from odoo import Command
from odoo.tests import Form, TransactionCase, tagged
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import mute_logger
from psycopg2.errors import UniqueViolation


@tagged('post_install', '-at_install')
class TestFleetIntegration(TransactionCase):
    start = '2026-12-01 02:00:00'
    end = '2026-12-03 02:00:00'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Integration test'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'Bike', 'brand_id': brand.id, 'vehicle_type': 'bike'})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id, 'is_electric_motorbike': True,
            'technical_ready': True, 'operational_status': 'available'})

    def eligibility(self, start=None, end=None):
        return self.vehicle.check_fleet_availability(start or self.start, end or self.end)[0]

    def deliver(self, **values):
        return self.vehicle.action_deliver_vehicle(self.start, self.end, **values)

    def service(self, **values):
        return self.env['fleet.vehicle.log.services'].create({
            'vehicle_id': self.vehicle.id, 'state': 'new', **values})

    def test_delivery_and_passed_return(self):
        self.deliver(odometer_start=100, checkout_at=self.start)
        self.assertEqual(self.vehicle.operational_status, 'renting')
        self.assertEqual(self.vehicle.odometer, 100)
        self.vehicle.action_return_vehicle('passed', odometer_end=150, checkin_at=self.end)
        self.assertEqual(self.vehicle.odometer, 150)
        self.assertEqual(self.vehicle.operational_status, 'available')
        self.assertTrue(self.vehicle.technical_ready)
        logs = self.env['fleet.vehicle.odometer'].search([('vehicle_id', '=', self.vehicle.id)])
        self.assertEqual(len(logs), 2)
        self.assertEqual({str(log.date) for log in logs}, {'2026-12-01', '2026-12-03'})

    def test_return_results_and_reinspection(self):
        for result in ['failed', 'pending', 'maintenance']:
            self.vehicle.action_confirm_technical_ready()
            self.deliver()
            self.vehicle.action_return_vehicle(result)
            self.assertFalse(self.vehicle.technical_ready)
            self.assertEqual(self.vehicle.operational_status,
                             'maintenance' if result == 'maintenance' else 'pending_inspection')
        self.vehicle.action_confirm_technical_ready()
        self.assertEqual(self.vehicle.operational_status, 'available')

    def test_passed_return_reconfirms_technical_condition_and_retains_block(self):
        self.deliver()
        self.vehicle.write({'technical_ready': False, 'rental_blocked': True, 'block_reason': 'Kiểm kê'})
        self.vehicle.action_return_vehicle('passed')
        self.assertTrue(self.vehicle.technical_ready)
        self.assertTrue(self.vehicle.rental_blocked)
        self.assertEqual(self.vehicle.block_reason, 'Kiểm kê')
        with self.assertRaises(UserError), self.cr.savepoint():
            self.deliver()

    def test_return_preserves_running_maintenance(self):
        self.deliver()
        self.vehicle.write({'operational_status': 'maintenance', 'technical_ready': False})
        self.service(state='running', actual_start=self.start)
        self.vehicle.action_return_vehicle('passed', odometer_end=10, checkin_at=self.end)
        self.assertEqual(self.vehicle.operational_status, 'maintenance')
        self.assertFalse(self.vehicle.technical_ready)

    def test_explicit_return_result_and_duplicate_return(self):
        self.deliver()
        for result in [None, '', 'available', True]:
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.vehicle.action_return_vehicle(result)
        self.vehicle.action_return_vehicle('passed')
        with self.assertRaises(UserError), self.cr.savepoint():
            self.vehicle.action_return_vehicle('passed')

    def test_odometer_values_and_transaction_rollback(self):
        self.deliver(odometer_start=100, checkout_at=self.start)
        for value in [-1, 99, float('nan'), float('inf'), True, '200']:
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.vehicle.action_return_vehicle('passed', odometer_end=value, checkin_at=self.end)
            self.assertEqual(self.vehicle.operational_status, 'renting')
            self.assertEqual(self.vehicle.odometer, 100)
        self.vehicle.action_return_vehicle('passed', odometer_end=100, checkin_at=self.start)
        self.assertEqual(self.env['fleet.vehicle.odometer'].search_count([('vehicle_id', '=', self.vehicle.id)]), 1)

    def test_zero_odometer_and_optional_odometer(self):
        self.deliver(odometer_start=0, checkout_at=self.start)
        self.vehicle.action_return_vehicle('pending', odometer_end=0, checkin_at=self.end)
        self.assertEqual(self.vehicle.odometer, 0)
        self.assertEqual(self.env['fleet.vehicle.odometer'].search_count([('vehicle_id', '=', self.vehicle.id)]), 2)

    def test_draft_does_not_reserve_dates_but_running_blocks(self):
        service = self.service()
        self.assertTrue(self.eligibility()['fleet_ok'])
        service.action_start()
        self.assertFalse(self.eligibility()['fleet_ok'])
        self.assertIn('blocking_maintenance', self.eligibility()['reasons'])
        with self.assertRaises(UserError), self.cr.savepoint():
            self.deliver(odometer_start=10)
        service.action_cancel()
        self.vehicle.action_confirm_technical_ready()
        self.assertTrue(self.eligibility()['fleet_ok'])

    def test_nonblocking_archived_and_new_maintenance(self):
        service = self.service(blocks_rental=False)
        self.assertTrue(self.eligibility()['fleet_ok'])
        service.write({'blocks_rental': True, 'active': False})
        self.assertTrue(self.eligibility()['fleet_ok'])
        self.service(state='new')
        self.assertTrue(self.eligibility()['fleet_ok'])

    def test_running_maintenance_has_no_guaranteed_end(self):
        service = self.service(state='running', actual_start=self.start)
        result = self.eligibility('2027-01-01 02:00:00', '2027-01-02 02:00:00')
        self.assertIn('blocking_maintenance', result['reasons'])
        service.write({'result': 'Xong', 'actual_end': self.end})
        service.action_done()
        self.vehicle.action_confirm_technical_ready()
        self.assertTrue(self.eligibility()['fleet_ok'])

    def test_static_conditions_and_current_renting_is_not_a_future_reservation(self):
        self.deliver()
        # Rental must independently reject a conflicting contract. Fleet has no Rental dependency.
        self.assertTrue(self.eligibility()['fleet_ok'])
        with self.assertRaises(UserError), self.cr.savepoint():
            self.deliver()
        self.vehicle.action_return_vehicle('passed')
        self.vehicle.active = False
        self.assertIn('archived', self.eligibility()['reasons'])
        self.vehicle.write({'active': True, 'operational_status': 'pending_inspection', 'technical_ready': False})
        self.assertIn('not_technical_ready', self.eligibility()['reasons'])

    def test_invalid_rental_period(self):
        for start, end in [(None, self.end), (self.start, self.start), (self.end, self.start), ('bad', self.end)]:
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.vehicle.check_fleet_availability(start, end)

    def test_integration_access(self):
        outsider = self.env['res.users'].create({'name': 'No Fleet', 'login': 'w8_no_fleet',
            ('group_ids' if 'group_ids' in self.env['res.users']._fields else 'groups_id'): [Command.set([self.env.ref('base.group_user').id])]})
        for method, args in [('check_fleet_availability', (self.start, self.end)),
                             ('action_deliver_vehicle', (self.start, self.end)),
                             ('action_return_vehicle', ('passed',))]:
            with self.assertRaises(AccessError), self.cr.savepoint():
                getattr(self.vehicle.with_user(outsider), method)(*args)
        officer = self.env['res.users'].create({'name': 'Fleet', 'login': 'w8_fleet',
            ('group_ids' if 'group_ids' in self.env['res.users']._fields else 'groups_id'): [Command.set([self.env.ref('fleet.fleet_group_user').id])]})
        vehicle = self.vehicle.with_user(officer)
        vehicle.action_deliver_vehicle(self.start, self.end, odometer_start=10, checkout_at=self.start)
        vehicle.action_return_vehicle('passed', odometer_end=20, checkin_at=self.end)
        self.assertEqual(vehicle.operational_status, 'available')

    @mute_logger('odoo.sql_db')
    def test_vehicle_code_unique_create_write_and_archived(self):
        self.vehicle.vehicle_code = 'UNIQUE-W8'
        values = {'model_id': self.vehicle.model_id.id, 'is_electric_motorbike': True}
        with self.assertRaises(UniqueViolation), self.cr.savepoint():
            self.env['fleet.vehicle'].create({**values, 'vehicle_code': 'UNIQUE-W8'})
        other = self.env['fleet.vehicle'].create({**values, 'vehicle_code': 'OTHER-W8'})
        with self.assertRaises(UniqueViolation), self.cr.savepoint():
            other.write({'vehicle_code': 'UNIQUE-W8'})
            self.env.flush_all()
        self.vehicle.active = False
        with self.assertRaises(UniqueViolation), self.cr.savepoint():
            self.env['fleet.vehicle'].create({**values, 'vehicle_code': 'UNIQUE-W8'})
        self.cr.execute("SELECT 1 FROM pg_constraint WHERE conrelid='fleet_vehicle'::regclass "
                        "AND contype='u' AND pg_get_constraintdef(oid)='UNIQUE (vehicle_code)'")
        self.assertTrue(self.cr.fetchone(), 'Vehicle code must also be unique at the database level')

    def test_optional_vehicle_code_and_copy(self):
        values = {'model_id': self.vehicle.model_id.id, 'is_electric_motorbike': True}
        blank = self.env['fleet.vehicle'].create([values, values])
        self.assertEqual(len(set(blank.mapped('vehicle_code'))), 2)
        self.assertTrue(all(blank.mapped('vehicle_code')))
        self.vehicle.vehicle_code = 'COPY-W8'
        copied = self.vehicle.copy()
        self.assertTrue(copied.vehicle_code)
        self.assertNotEqual(copied.vehicle_code, self.vehicle.vehicle_code)

    def test_vehicle_form_state_is_readonly_but_workflow_works(self):
        with Form(self.vehicle) as form:
            with self.assertRaises(AssertionError):
                form.operational_status = 'renting'
            with self.assertRaises(AssertionError):
                form.technical_ready = False
            form.rental_blocked = True
            form.block_reason = 'Kiểm kê'
        self.assertTrue(self.vehicle.rental_blocked)
        self.vehicle.write({'rental_blocked': False})
        self.deliver()
        self.vehicle.action_return_vehicle('pending')
        self.vehicle.action_confirm_technical_ready()
        self.assertEqual(self.vehicle.operational_status, 'available')
