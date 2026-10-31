import uuid

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRentalExtension(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        suffix = uuid.uuid4().hex[:8]
        cls.customer = cls.env['res.partner'].create({
            'name': 'Extension customer %s' % suffix,
            'phone': '0901%s' % suffix[:6],
            'email': 'extension-%s@example.com' % suffix,
            'rental_id_number': 'ID-%s' % suffix,
            'is_rental_customer': True,
        })
        cls.customer.rental_document_ids.create({
            'name': 'Identity document',
            'customer_id': cls.customer.id,
            'file': 'dGVzdA==',
            'filename': 'identity.txt',
        })
        brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Extension brand %s' % suffix,
        })
        model = cls.env['fleet.vehicle.model'].create({
            'name': 'Extension bike %s' % suffix,
            'brand_id': brand.id,
            'vehicle_type': 'bike',
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'is_electric_motorbike': True,
            'odometer': 100,
            'technical_ready': True,
            'operational_status': 'available',
        })
        cls.vehicle_type = cls.env['rental.vehicle.type'].create({
            'name': 'Extension rate %s' % suffix,
            'model_id': model.id,
            'daily_rate': 100000,
        })
        cls.employee = cls.env['res.users'].create({
            'name': 'Extension employee %s' % suffix,
            'login': 'extension-employee-%s' % suffix,
            'groups_id': [(6, 0, [
                cls.env.ref('motorbike_rental_core.group_rental_user').id,
            ])],
        })
        cls.manager = cls.env['res.users'].create({
            'name': 'Extension manager %s' % suffix,
            'login': 'extension-manager-%s' % suffix,
            'groups_id': [(6, 0, [
                cls.env.ref('motorbike_rental_core.group_rental_manager').id,
            ])],
        })

    def _create_active_contract(
        self,
        start_date='2026-12-01 08:00:00',
        end_date='2026-12-03 08:00:00',
    ):
        contract = self.env['rental.contract'].create({
            'customer_id': self.customer.id,
            'start_date': start_date,
            'end_date': end_date,
            'line_ids': [(0, 0, {
                'vehicle_id': self.vehicle.id,
                'vehicle_type_id': self.vehicle_type.id,
            })],
        })
        if (
            'motorbike.rental.payment' in self.env.registry
            and 'upfront_received_check' in contract._fields
        ):
            contract.write({
                'upfront_received_check': True,
                'upfront_payment_method': 'cash',
            })
        contract.action_confirm()
        contract.action_start()
        return contract

    def _create_extension(self, contract, requested_end_date):
        return self.env['rental.extension'].with_user(self.employee).create({
            'contract_id': contract.id,
            'requested_end_date': requested_end_date,
            'reason': 'Khách cần thêm thời gian thuê.',
        })

    def test_extension_form_defaults_show_current_and_next_return_time(self):
        contract = self._create_active_contract()

        defaults = self.env['rental.extension'].with_context(
            default_contract_id=contract.id,
        ).default_get([
            'state',
            'contract_id',
            'original_end_date',
            'original_rental_days',
            'requested_end_date',
        ])

        self.assertEqual(defaults['state'], 'pending')
        self.assertEqual(defaults['contract_id'], contract.id)
        self.assertEqual(defaults['original_end_date'], contract.end_date)
        self.assertEqual(defaults['original_rental_days'], contract.rental_days)
        self.assertEqual(
            defaults['requested_end_date'],
            fields.Datetime.add(contract.end_date, days=1),
        )
        extension_form = self.env['rental.extension'].new(defaults)
        self.assertEqual(extension_form.additional_days, 1)
        self.assertEqual(extension_form.additional_amount, 100000)

    def test_create_uses_contract_from_action_context(self):
        contract = self._create_active_contract()

        extension = self.env['rental.extension'].with_user(
            self.employee
        ).with_context(default_contract_id=contract.id).create({
            'requested_end_date': '2026-12-04 08:00:00',
            'reason': 'Khách cần thêm thời gian thuê.',
        })

        self.assertEqual(extension.contract_id, contract)
        self.assertEqual(extension.original_end_date, contract.end_date)

    def test_rental_user_can_check_and_extend_contract(self):
        contract = self._create_active_contract()
        extension = self._create_extension(
            contract, '2026-12-05 08:00:00'
        )

        self.assertEqual(extension.additional_days, 2)
        self.assertEqual(extension.additional_amount, 200000)

        extension.with_user(self.employee).action_check_and_extend()

        self.assertEqual(extension.state, 'approved')
        self.assertEqual(extension.reviewed_by, self.employee)
        self.assertEqual(contract.end_date, fields.Datetime.to_datetime(
            '2026-12-05 08:00:00'
        ))
        self.assertEqual(contract.rental_days, 4)
        self.assertEqual(contract.total_amount, 400000)

    def test_check_does_not_extend_when_next_booking_conflicts(self):
        contract = self._create_active_contract()
        self._create_active_contract(
            start_date='2026-12-03 08:00:00',
            end_date='2026-12-05 08:00:00'
        )
        extension = self._create_extension(
            contract, '2026-12-04 08:00:00'
        )

        with self.assertRaises(ValidationError), self.cr.savepoint():
            extension.with_user(self.employee).action_check_and_extend()

        self.assertEqual(extension.state, 'pending')
        self.assertEqual(contract.end_date, fields.Datetime.to_datetime(
            '2026-12-03 08:00:00'
        ))

    def test_rejection_requires_a_reason(self):
        contract = self._create_active_contract()
        extension = self._create_extension(
            contract, '2026-12-04 08:00:00'
        )

        with self.assertRaises(UserError), self.cr.savepoint():
            extension.with_user(self.manager).action_reject()

        extension.with_user(self.manager).write({
            'rejection_reason': 'Xe đã có lịch thuê tiếp theo.',
        })
        extension.with_user(self.manager).action_reject()

        self.assertEqual(extension.state, 'rejected')
        self.assertEqual(extension.reviewed_by, self.manager)

    def test_requester_can_cancel_pending_extension(self):
        contract = self._create_active_contract()
        extension = self._create_extension(
            contract, '2026-12-04 08:00:00'
        )

        extension.with_user(self.employee).action_cancel()

        self.assertEqual(extension.state, 'cancelled')

    def test_only_one_pending_extension_per_contract(self):
        contract = self._create_active_contract()
        self._create_extension(contract, '2026-12-04 08:00:00')

        with self.assertRaises(UserError), self.cr.savepoint():
            self._create_extension(contract, '2026-12-05 08:00:00')
