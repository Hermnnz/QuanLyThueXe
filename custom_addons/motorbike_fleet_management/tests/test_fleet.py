from odoo import Command
from odoo.tests import Form, TransactionCase, tagged
from odoo.exceptions import AccessError, ValidationError


@tagged('post_install', '-at_install')
class TestElectricFleet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test electric'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'Test bike', 'brand_id': brand.id, 'vehicle_type': 'bike'})
        cls.vehicle = cls.env['fleet.vehicle'].create({'model_id': model.id, 'is_electric_motorbike': True, 'battery_capacity_kwh': 3.5})
        cls.service_type = cls.env['fleet.service.type'].create({'name': 'Test maintenance', 'category': 'service'})
        cls.service = cls.env['fleet.vehicle.log.services'].create({'vehicle_id': cls.vehicle.id, 'service_type_id': cls.service_type.id, 'date': '2026-09-25', 'maintenance_component': 'battery'})

    def test_invalid_battery(self):
        for values in ({'battery_capacity_kwh': -1}, {'battery_voltage': -1}, {'charging_time_hours': -1}, {'battery_health': 101}, {'battery_health': -1}):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.vehicle.write(values)
        self.vehicle.write({'battery_health': 0})
        self.vehicle.write({'battery_health': 100})

    def test_service_dates_and_relation(self):
        self.assertTrue(self.service.is_electric_motorbike)
        self.assertIn(self.service, self.vehicle.log_services)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.service.next_maintenance_date = '2026-09-24'
        self.service.write({'next_maintenance_date': '2026-10-25', 'state': 'done'})
        self.assertEqual(self.service.state, 'done')

    def test_permissions(self):
        def user(login, group):
            return self.env['res.users'].create({'name': login, 'login': login, 'group_ids': [Command.set([self.env.ref(group).id])]})
        officer = user('test_fleet_officer', 'fleet.fleet_group_user')
        technician = user('test_fleet_technician', 'motorbike_fleet_management.group_motorbike_technician')
        manager = user('test_fleet_manager', 'fleet.fleet_group_manager')
        outsider = user('test_fleet_outsider', 'base.group_user')
        self.service.with_user(officer).read(['maintenance_component'])
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.service.with_user(officer).write({'maintenance_result': 'Forbidden'})
        self.service.with_user(technician).write({'maintenance_result': 'Checked'})
        created = self.env['fleet.vehicle.log.services'].with_user(technician).create({'vehicle_id': self.vehicle.id, 'service_type_id': self.service_type.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            created.with_user(technician).unlink()
        created.with_user(manager).unlink()
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.vehicle.with_user(outsider).read(['battery_capacity_kwh'])

    def test_company_isolation(self):
        other = self.env['res.company'].create({'name': 'Other Fleet Company'})
        vehicle = self.vehicle.copy({'company_id': other.id})
        user = self.env['res.users'].create({'name': 'Company officer', 'login': 'test_company_officer', 'company_id': self.env.company.id, 'company_ids': [Command.set([self.env.company.id])], 'group_ids': [Command.set([self.env.ref('fleet.fleet_group_user').id])]})
        with self.assertRaises(AccessError), self.cr.savepoint():
            vehicle.with_user(user).read(['battery_capacity_kwh'])

    def test_v2_crud_and_battery_history(self):
        battery = self.env['motorbike.battery'].create({
            'battery_code': 'TEST-BAT-001', 'soc': 86, 'soh': 95,
        })
        assignment = self.env['motorbike.battery.assignment'].create({
            'battery_id': battery.id, 'vehicle_id': self.vehicle.id,
            'installed_at': '2026-10-01 08:00:00', 'install_odo': 100,
        })
        self.assertEqual(self.vehicle.current_battery_id, battery)
        self.assertEqual(battery.current_vehicle_id, self.vehicle)
        self.assertEqual(self.vehicle.current_soc, 86)
        battery.soc = 90
        self.assertEqual(self.vehicle.current_soc, 90)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            battery.soc = 101
        assignment.write({'removed_at': '2026-10-02 08:00:00', 'remove_odo': 110})
        self.assertFalse(self.vehicle.current_battery_id)
        self.assertFalse(battery.current_vehicle_id)
        replacement = self.env['motorbike.battery'].create({'battery_code': 'TEST-BAT-002'})
        installed = assignment.copy({
            'battery_id': replacement.id, 'installed_at': '2026-10-02 08:00:00',
            'removed_at': False, 'install_odo': 110, 'remove_odo': 0,
        })
        self.assertEqual(self.vehicle.current_battery_id, replacement)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            assignment.write({'removed_at': '2026-10-03 08:00:00'})
        installed.unlink()
        self.assertFalse(self.vehicle.current_battery_id)
        plan = self.env['motorbike.maintenance.plan'].create({
            'name': 'Bảo dưỡng tổng quát', 'vehicle_id': self.vehicle.id,
            'interval_km': 5000, 'interval_days': 180,
        })
        plan.write({'next_service_odo': 15000})
        self.assertIn(plan, self.vehicle.maintenance_plan_ids)
        plan.unlink()
        self.service.write({'cost': 500000, 'result': 'Kiểm tra phanh', 'state': 'scheduled'})
        self.service.cost = 650000
        self.assertEqual(self.service.amount, 650000)
        self.assertEqual(self.service.maintenance_result, 'Kiểm tra phanh')
        odo = self.env['fleet.vehicle.odometer'].create({
            'vehicle_id': self.vehicle.id, 'value': 12680, 'source_type': 'maintenance',
            'service_id': self.service.id,
        })
        odo.note = 'Đã đối chiếu'
        self.assertEqual(odo.service_id, self.service)

    def test_v2_custom_permissions(self):
        def user(login, group):
            return self.env['res.users'].create({'name': login, 'login': login,
                'group_ids': [Command.set([self.env.ref(group).id])]})
        manager = user('v2_manager', 'fleet.fleet_group_manager')
        tech = user('v2_tech', 'motorbike_fleet_management.group_motorbike_technician')
        outsider = user('v2_outsider', 'base.group_user')
        battery = self.env['motorbike.battery'].with_user(manager).create({'battery_code': 'ACL-BAT'})
        plan = self.env['motorbike.maintenance.plan'].with_user(manager).create({
            'name': 'ACL Plan', 'vehicle_id': self.vehicle.id,
        })
        assignment = self.env['motorbike.battery.assignment'].with_user(manager).create({
            'battery_id': battery.id, 'vehicle_id': self.vehicle.id,
        })
        for record in [battery, plan, assignment]:
            record.with_user(tech).read()
            with self.assertRaises(AccessError), self.cr.savepoint():
                record.with_user(tech).unlink()
            with self.assertRaises(AccessError), self.cr.savepoint():
                record.with_user(outsider).read()
        with self.assertRaises(AccessError), self.cr.savepoint():
            battery.with_user(tech).soc = 50
        assignment.with_user(manager).unlink()
        battery.with_user(manager).unlink()
        plan.with_user(manager).unlink()

    def test_week6_forms(self):
        with Form(self.env['motorbike.battery']) as form:
            form.battery_code = 'FORM-BAT'
            form.soc = 86
        battery = form.record
        with Form(self.vehicle) as form:
            form.vehicle_code = 'FORM-XE'
            with form.battery_assignment_ids.new() as line:
                line.battery_id = battery
        self.assertEqual(self.vehicle.current_battery_id, battery)
        with Form(self.env['motorbike.maintenance.plan']) as form:
            form.name = 'Form plan'
            form.vehicle_id = self.vehicle
            form.interval_km = 5000
            form.interval_days = 180
        self.assertEqual(form.record.interval_days, 180)
        with Form(self.service.with_context(motorbike_only=True)) as form:
            form.amount = 650000
            form.result = 'Đã kiểm tra'
        self.assertEqual(self.service.cost, 650000)
        self.assertEqual(self.service.result, 'Đã kiểm tra')
        with Form(self.env['fleet.vehicle.odometer']) as form:
            form.vehicle_id = self.vehicle
            form.value = 12680
            form.source_type = 'manual'
            form.note = 'Form ODO tuần 6'
        self.assertEqual(form.record.value, 12680)
