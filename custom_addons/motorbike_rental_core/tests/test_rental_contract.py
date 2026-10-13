from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRentalContract(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({'name': 'Rental Test Customer'})
        cls.currency = cls.env.company.currency_id
        cls.vehicle_type = cls.env['rental.vehicle.type'].create({
            'name': 'Rental Test Type',
            'currency_id': cls.currency.id,
            'daily_rate': 100,
        })

    def _create_contract(self, **overrides):
        values = {
            'customer_id': self.customer.id,
            'start_date': '2026-10-01',
            'end_date': '2026-10-04',
            'currency_id': self.currency.id,
        }
        values.update(overrides)
        return self.env['rental.contract'].create(values)

    def _add_vehicle(self, contract, vehicle_id, daily_rate=None):
        values = {
            'contract_id': contract.id,
            'vehicle_id': vehicle_id,
            'vehicle_type_id': self.vehicle_type.id,
        }
        if daily_rate is not None:
            values['daily_rate'] = daily_rate
        return self.env['rental.contract.line'].create(values)

    def test_compute_rental_days_and_amounts(self):
        contract = self._create_contract()
        first_line = self._add_vehicle(contract, 101)
        second_line = self._add_vehicle(contract, 102, daily_rate=50)

        self.assertEqual(contract.rental_days, 3)
        self.assertEqual(first_line.subtotal, 300)
        self.assertEqual(second_line.subtotal, 150)
        self.assertEqual(contract.total_amount, 450)

    def test_state_machine_actions(self):
        contract = self._create_contract()
        self._add_vehicle(contract, 101)

        with self.assertRaises(UserError):
            contract.write({'state': 'in_progress'})

        contract.action_confirm()
        self.assertEqual(contract.state, 'confirmed')
        contract.action_start()
        self.assertEqual(contract.state, 'in_progress')
        contract.action_done()
        self.assertEqual(contract.state, 'done')

        with self.assertRaises(UserError):
            contract.action_cancel()

    def test_cannot_confirm_without_vehicle(self):
        contract = self._create_contract()

        with self.assertRaises(ValidationError), self.cr.savepoint():
            contract.action_confirm()

        self.assertEqual(contract.state, 'draft')

    def test_cannot_create_outside_draft_state(self):
        with self.assertRaises(UserError):
            self._create_contract(state='confirmed')

    def test_cancel_from_active_states(self):
        draft_contract = self._create_contract()
        draft_contract.action_cancel()
        self.assertEqual(draft_contract.state, 'cancelled')

        confirmed_contract = self._create_contract()
        self._add_vehicle(confirmed_contract, 101)
        confirmed_contract.action_confirm()
        confirmed_contract.action_cancel()
        self.assertEqual(confirmed_contract.state, 'cancelled')

    def test_rejects_overlapping_vehicle_reservation(self):
        first_contract = self._create_contract()
        self._add_vehicle(first_contract, 101)
        first_contract.action_confirm()

        overlapping_contract = self._create_contract(
            start_date='2026-10-03',
            end_date='2026-10-06',
        )
        self._add_vehicle(overlapping_contract, 101)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            overlapping_contract.action_confirm()

        self.assertEqual(overlapping_contract.state, 'draft')

    def test_rejects_invalid_rental_period_and_negative_deposit(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self._create_contract(
                min_rental_days=4,
            )

        with self.assertRaises(ValidationError), self.cr.savepoint():
            self._create_contract(
                deposit_amount=-1,
            )
