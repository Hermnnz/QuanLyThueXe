from odoo import Command
from odoo.tests import Form, TransactionCase, tagged
from odoo.exceptions import AccessError, UserError, ValidationError


@tagged('post_install', '-at_install')
class TestWeek7Fleet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Week 7 test'})
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'Electric bike', 'brand_id': brand.id, 'vehicle_type': 'bike'})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id, 'is_electric_motorbike': True, 'vehicle_code': 'TEST-W7'})

    def service(self, **values):
        return self.env['fleet.vehicle.log.services'].create({
            'vehicle_id': self.vehicle.id, 'date': '2026-10-09',
            'scheduled_start': '2026-10-09 02:00:00',
            'scheduled_end': '2026-10-09 06:00:00', **values})

    def user(self, login, group):
        return self.env['res.users'].create({'name': login, 'login': login,
            'group_ids': [Command.set([self.env.ref(group).id])]})

    def test_vehicle_form_crud(self):
        with Form(self.env['fleet.vehicle'].with_context(default_is_electric_motorbike=True)) as form:
            form.model_id = self.model
            form.vehicle_code = 'FORM-W7'
            form.license_plate = 'DEMO-W7'
        vehicle = form.record
        vehicle.action_confirm_technical_ready()
        with Form(vehicle) as form:
            form.rental_blocked = True
            form.block_reason = 'Kiểm kê'
        self.assertEqual(vehicle.operational_status, 'available')
        self.assertTrue(vehicle.technical_ready)
        vehicle.unlink()

    def test_service_form_crud(self):
        with Form(self.env['fleet.vehicle.log.services'].with_context(motorbike_only=True)) as form:
            form.vehicle_id = self.vehicle
            form.maintenance_type = 'corrective'
            form.amount = 500000
            form.result = 'Sửa phanh'
        service = form.record
        service.action_start()
        self.assertEqual(service.cost, 500000)
        service.action_done()
        self.assertEqual(service.state, 'done')
        service.unlink()

    def test_vehicle_validation(self):
        for values in [{'operational_status': 'available'}, {'rental_blocked': True},
                       {'rental_blocked': True, 'block_reason': '   '}]:
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.vehicle.write(values)
        self.vehicle.write({'rental_blocked': True, 'block_reason': 'Kiểm kê'})
        self.vehicle.action_confirm_technical_ready()
        self.assertTrue(self.vehicle.rental_blocked)

    def test_service_validation(self):
        for values in [{'amount': -1}, {'scheduled_end': '2026-10-08 06:00:00'},
                       {'scheduled_start': False}, {'actual_end': '2026-10-09 06:00:00'},
                       {'actual_start': '2026-10-09 06:00:00', 'actual_end': '2026-10-09 02:00:00'},
                       {'next_service_date': '2026-10-09'}]:
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.service(**values)
        self.assertEqual(self.service(amount=0).cost, 0)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['fleet.vehicle.log.services'].create({'vehicle_id': self.vehicle.id, 'state': 'scheduled'})

    def test_workflow_and_next_date(self):
        self.vehicle.action_confirm_technical_ready()
        service = self.service(result='Đã sửa', next_service_date='2026-12-01')
        service.action_schedule()
        self.assertEqual(self.vehicle.operational_status, 'available')
        service.action_start()
        self.assertTrue(service.actual_start)
        self.assertFalse(self.vehicle.technical_ready)
        self.assertEqual(self.vehicle.operational_status, 'maintenance')
        with self.assertRaises(UserError), self.cr.savepoint():
            self.vehicle.action_confirm_technical_ready()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.vehicle.write({'technical_ready': True, 'operational_status': 'available'})
        service.action_done()
        self.assertTrue(service.actual_end)
        self.assertEqual(self.vehicle.operational_status, 'inspection')
        self.assertFalse(self.vehicle.technical_ready)
        self.assertEqual(str(self.vehicle.next_service_date), '2026-12-01')
        self.vehicle.action_confirm_technical_ready()
        self.assertEqual(self.vehicle.operational_status, 'available')

    def test_multiple_blocking_services(self):
        first, second = self.service(result='Xong'), self.service(result='Xong')
        (first | second).action_start()
        first.action_done()
        self.assertEqual(self.vehicle.operational_status, 'maintenance')
        with self.assertRaises(UserError), self.cr.savepoint():
            self.vehicle.action_confirm_technical_ready()
        second.action_cancel()
        self.assertEqual(self.vehicle.operational_status, 'inspection')

    def test_nonblocking_and_cancel_scheduled(self):
        self.vehicle.action_confirm_technical_ready()
        service = self.service(blocks_rental=False, result='Kiểm tra')
        service.action_start()
        service.action_done()
        self.assertEqual(self.vehicle.operational_status, 'available')
        self.assertTrue(self.vehicle.technical_ready)
        planned = self.service()
        planned.action_schedule()
        planned.action_cancel()
        self.assertFalse(planned.actual_start)
        self.assertFalse(planned.actual_end)

    def test_invalid_transition_and_result(self):
        service = self.service()
        with self.assertRaises(UserError), self.cr.savepoint():
            service.write({'state': 'done'})
        service.action_start()
        with self.assertRaises(UserError), self.cr.savepoint():
            service.action_done()
        service.result = 'Đã sửa'
        service.action_done()
        with self.assertRaises(UserError), self.cr.savepoint():
            service.action_start()

    def test_running_record_cannot_be_hidden_or_reassigned(self):
        service = self.service(state='running')
        for values in [{'active': False}, {'blocks_rental': False}, {'vehicle_id': self.vehicle.id}]:
            with self.assertRaises(UserError), self.cr.savepoint():
                service.write(values)
        with self.assertRaises(UserError), self.cr.savepoint():
            service.unlink()

    def test_rented_or_archived_vehicle(self):
        self.vehicle.operational_status = 'rented'
        service = self.service()
        with self.assertRaises(UserError), self.cr.savepoint():
            service.action_start()
        with self.assertRaises(UserError), self.cr.savepoint():
            self.vehicle.action_confirm_technical_ready()
        self.vehicle.write({'operational_status': 'inspection', 'active': False})
        with self.assertRaises(UserError), self.cr.savepoint():
            self.vehicle.action_confirm_technical_ready()
        with self.assertRaises(UserError), self.cr.savepoint():
            service.action_start()

    def test_history_does_not_rewrite_current_state(self):
        self.vehicle.action_confirm_technical_ready()
        self.vehicle.next_service_date = '2027-01-01'
        service = self.service(state='done', date='2025-10-09', next_service_date='2025-12-01',
                               actual_start='2025-10-09 02:00:00', actual_end='2025-10-09 06:00:00')
        service.result = 'Bổ sung ghi chú lịch sử'
        self.assertEqual(self.vehicle.operational_status, 'available')
        self.assertEqual(str(self.vehicle.next_service_date), '2027-01-01')

    def test_old_completion_does_not_overwrite_newer_milestone(self):
        self.service(state='done', date='2026-10-09', next_service_date='2027-02-01')
        self.vehicle.next_service_date = '2027-02-01'
        older = self.service(date='2026-10-08', next_service_date='2026-12-01', result='Xong')
        older.action_start()
        older.action_done()
        self.assertEqual(str(self.vehicle.next_service_date), '2027-02-01')

    def test_native_odometer_validation(self):
        logs = self.env['fleet.vehicle.odometer']
        first = logs.create({'vehicle_id': self.vehicle.id, 'date': '2026-10-01', 'value': 100})
        logs.create({'vehicle_id': self.vehicle.id, 'date': '2026-10-09', 'value': 200})
        for values in [{'date': '2026-10-02', 'value': -1}, {'date': '2026-10-02', 'value': 99},
                       {'date': '2026-10-02', 'value': 201}]:
            with self.assertRaises(ValidationError), self.cr.savepoint():
                logs.create({'vehicle_id': self.vehicle.id, **values})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            first.value = 201
        with self.assertRaises(UserError), self.cr.savepoint():
            self.vehicle.odometer = -1

    def test_basic_permissions(self):
        officer = self.user('w7_officer', 'fleet.fleet_group_user')
        tech = self.user('w7_tech', 'motorbike_fleet_management.group_motorbike_technician')
        manager = self.user('w7_manager', 'fleet.fleet_group_manager')
        outsider = self.user('w7_outsider', 'base.group_user')
        self.vehicle.with_user(officer).action_confirm_technical_ready()
        service = self.env['fleet.vehicle.log.services'].with_user(tech).create({
            'vehicle_id': self.vehicle.id, 'result': 'Đã sửa'})
        with self.assertRaises(AccessError), self.cr.savepoint():
            service.with_user(officer).action_start()
        service.action_start()
        service.action_done()
        with self.assertRaises(AccessError), self.cr.savepoint():
            service.unlink()
        service.with_user(manager).unlink()
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.vehicle.with_user(outsider).action_confirm_technical_ready()

    def test_native_company_rule(self):
        other = self.env['res.company'].create({'name': 'Other Week 7 company'})
        vehicle = self.env['fleet.vehicle'].create({'model_id': self.model.id, 'company_id': other.id})
        officer = self.user('w7_company_officer', 'fleet.fleet_group_user')
        with self.assertRaises(AccessError), self.cr.savepoint():
            vehicle.with_user(officer).read(['vehicle_code'])

    def test_native_vehicle_scope_and_reassignment(self):
        ordinary = self.env['fleet.vehicle'].create({'model_id': self.model.id})
        service = self.env['fleet.vehicle.log.services'].create({'vehicle_id': ordinary.id})
        service.write({'state': 'done'})
        service.write({'state': 'new'})
        self.vehicle.operational_status = 'rented'
        with self.assertRaises(UserError), self.cr.savepoint():
            service.write({'vehicle_id': self.vehicle.id, 'state': 'running'})
        self.assertEqual(service.vehicle_id, ordinary)

    def test_preserve_actual_timestamps_and_alias_validation(self):
        service = self.service(actual_start='2026-10-09 02:00:00',
                               actual_end='2026-10-09 06:00:00', result='Xong')
        service.action_start()
        service.action_done()
        self.assertEqual(str(service.actual_start), '2026-10-09 02:00:00')
        self.assertEqual(str(service.actual_end), '2026-10-09 06:00:00')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            service.cost = -1

    def test_week7_views_and_scope(self):
        prefix = 'motorbike_fleet_management.'
        action = self.env.ref(prefix + 'action_electric_motorbikes')
        self.assertEqual(action.view_mode, 'list,kanban,form')
        self.assertEqual(action.search_view_id, self.env.ref(prefix + 'vehicle_search_electric'))
        self.assertIn((self.env.ref(prefix + 'vehicle_kanban_electric').id, 'kanban'), action.views)
        services = self.env.ref(prefix + 'action_motorbike_services')
        self.assertEqual(services.view_mode, 'list,form')
        self.assertEqual(services.search_view_id, self.env.ref(prefix + 'service_search_motorbike'))
        groups = self.env['fleet.vehicle'].with_context(read_group_expand=True).formatted_read_group([('id', '=', self.vehicle.id)],
                                                               ['operational_status'], ['__count'])
        self.assertEqual({g['operational_status'] for g in groups},
                         {'available', 'rented', 'inspection', 'maintenance'})
        for model in ['motorbike.battery', 'motorbike.battery.assignment', 'motorbike.maintenance.plan']:
            self.assertNotIn(model, self.env.registry)
        for method in ['check_availability', 'check_fleet_availability', 'action_mark_rented', 'action_return_for_inspection']:
            self.assertFalse(hasattr(self.vehicle, method))
