from odoo import Command
from odoo.tests import Form, TransactionCase, tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestWeek6FleetCRUD(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Week 6 test'})
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'CRUD electric bike', 'brand_id': brand.id, 'vehicle_type': 'bike'})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id, 'is_electric_motorbike': True, 'vehicle_code': 'TEST-W6'})

    def user(self, login, group):
        return self.env['res.users'].create({'name': login, 'login': login,
            'group_ids': [Command.set([self.env.ref(group).id])]})

    def test_vehicle_form_crud(self):
        with Form(self.env['fleet.vehicle'].with_context(default_is_electric_motorbike=True)) as form:
            form.model_id = self.model
            form.vehicle_code = 'FORM-W6'
            form.license_plate = 'DEMO-W6'
            form.operational_status = 'available'
            form.technical_ready = True
        vehicle = form.record
        self.assertEqual(vehicle.read(['vehicle_code'])[0]['vehicle_code'], 'FORM-W6')
        with Form(vehicle) as form:
            form.operational_status = 'maintenance'
            form.technical_ready = False
            form.rental_blocked = True
            form.block_reason = 'Nhập liệu thử tuần 6'
            form.next_service_date = '2026-11-01'
        self.assertEqual(vehicle.operational_status, 'maintenance')
        self.assertFalse(vehicle.technical_ready)
        vehicle.unlink()
        self.assertFalse(vehicle.exists())

    def test_service_form_crud(self):
        with Form(self.env['fleet.vehicle.log.services'].with_context(motorbike_only=True)) as form:
            form.vehicle_id = self.vehicle
            form.maintenance_type = 'corrective'
            form.state = 'done'
            form.scheduled_start = '2026-09-10 02:00:00'
            form.scheduled_end = '2026-09-10 06:00:00'
            form.actual_start = '2026-09-10 02:30:00'
            form.actual_end = '2026-09-10 05:30:00'
            form.amount = 500000
            form.result = 'Sửa phanh'
        service = form.record
        self.assertIn(service, self.vehicle.log_services)
        self.assertEqual(service.read(['result'])[0]['result'], 'Sửa phanh')
        with Form(service) as form:
            form.amount = 650000
            form.result = 'Sửa phanh và kiểm tra lốp'
            form.state = 'scheduled'
            form.actual_end = '2026-09-10 06:00:00'
        self.assertEqual(service.cost, 650000)
        self.assertEqual(service.state, 'scheduled')
        service.unlink()
        self.assertFalse(service.exists())

    def test_maintenance_does_not_update_vehicle(self):
        self.vehicle.write({'operational_status': 'available', 'technical_ready': True,
                            'next_service_date': '2026-11-01'})
        service = self.env['fleet.vehicle.log.services'].create({
            'vehicle_id': self.vehicle.id, 'state': 'running', 'blocks_rental': True})
        self.assertFalse(service.actual_start)
        self.assertEqual(self.vehicle.operational_status, 'available')
        self.assertTrue(self.vehicle.technical_ready)
        service.write({'state': 'done', 'next_service_date': '2026-12-01'})
        self.assertFalse(service.actual_end)
        self.assertEqual(str(self.vehicle.next_service_date), '2026-11-01')
        self.assertEqual(self.vehicle.operational_status, 'available')

    def test_basic_permissions(self):
        officer = self.user('w6_officer', 'fleet.fleet_group_user')
        tech = self.user('w6_tech', 'motorbike_fleet_management.group_motorbike_technician')
        manager = self.user('w6_manager', 'fleet.fleet_group_manager')
        outsider = self.user('w6_outsider', 'base.group_user')
        self.vehicle.with_user(officer).write({'technical_ready': True, 'operational_status': 'available'})
        service = self.env['fleet.vehicle.log.services'].with_user(tech).create({
            'vehicle_id': self.vehicle.id, 'result': 'Tạo hồ sơ thử'})
        service.with_user(officer).read(['result'])
        with self.assertRaises(AccessError), self.cr.savepoint():
            service.with_user(officer).write({'result': 'Không có quyền sửa'})
        service.with_user(tech).write({'amount': 350000, 'result': 'Đã cập nhật'})
        with self.assertRaises(AccessError), self.cr.savepoint():
            service.with_user(tech).unlink()
        service.with_user(manager).unlink()
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.vehicle.with_user(outsider).read(['vehicle_code'])

    def test_native_company_rule(self):
        other = self.env['res.company'].create({'name': 'Other Week 6 company'})
        vehicle = self.env['fleet.vehicle'].create({'model_id': self.model.id, 'company_id': other.id})
        officer = self.user('w6_company_officer', 'fleet.fleet_group_user')
        with self.assertRaises(AccessError), self.cr.savepoint():
            vehicle.with_user(officer).read(['vehicle_code'])

    def test_week6_views_and_scope(self):
        for name in ['action_electric_motorbikes', 'action_motorbike_services']:
            action = self.env.ref('motorbike_fleet_management.' + name)
            self.assertEqual(action.view_mode, 'list,form')
            self.assertTrue(action.view_id)
        self.assertFalse(self.env.ref('motorbike_fleet_management.vehicle_search_electric', raise_if_not_found=False))
        for model in ['motorbike.battery', 'motorbike.battery.assignment', 'motorbike.maintenance.plan']:
            self.assertNotIn(model, self.env.registry)
        for method in ['check_availability', 'check_fleet_availability', 'action_mark_rented',
                       'action_confirm_technical_ready', 'action_return_for_inspection']:
            self.assertFalse(hasattr(self.vehicle, method))
