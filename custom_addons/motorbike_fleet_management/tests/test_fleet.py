from odoo import Command
from odoo.tests import TransactionCase, tagged
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
