from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestServiceNotifications(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = cls.env['res.users'].create({'name': 'Fleet notification test',
            'login': 'fleet.notification.test', 'company_id': cls.env.company.id,
            'company_ids': [Command.set(cls.env.company.ids)],
            'groups_id': [Command.set(cls.env.ref('fleet.fleet_group_manager').ids)]})
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Notification'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'EV', 'brand_id': brand.id, 'vehicle_type': 'bike'})
        cls.vehicle = cls.env['fleet.vehicle'].create({'model_id': model.id, 'is_electric_motorbike': True,
            'manager_id': cls.manager.id, 'operational_status': 'available', 'technical_ready': True})
        cls.activity_type = cls.env.ref('motorbike_fleet_management.activity_service_created')

    def activities(self, service):
        return service.activity_ids.filtered(lambda a: a.activity_type_id == self.activity_type)

    def service(self, **values):
        return self.env['fleet.vehicle.log.services'].create({'vehicle_id': self.vehicle.id,
            'description': 'Kiểm tra phanh <script>unsafe</script>', **values})

    def test_new_service_notifies_manager_once_and_finishes_when_started(self):
        service = self.service()
        activities = self.activities(service)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.user_id, self.manager)
        self.assertIn(str(service.id), activities.summary)
        self.assertIn(self.vehicle.vehicle_code, activities.summary)
        self.assertNotIn('<script>', str(activities.note))
        service._notify_new_service()
        self.assertEqual(self.activities(service), activities)
        service.action_start()
        self.assertFalse(self.activities(service))

    def test_automatic_due_draft_notifies_too(self):
        self.vehicle.write({'service_reference_date': fields.Date.today(), 'service_reference_odo': 0,
                            'service_interval_km': 1000, 'odometer': 1000})
        service = self.vehicle._open_preventive_services()
        self.assertEqual(len(service), 1)
        self.assertEqual(self.activities(service).user_id, self.manager)
        self.vehicle._auto_create_due_services()
        self.assertEqual(len(self.activities(service)), 1)

    def test_no_manager_falls_back_to_fleet_managers(self):
        self.vehicle.manager_id = False
        service = self.service()
        self.assertIn(self.manager, self.activities(service).user_id)
        self.assertNotIn(self.env.ref('base.user_root'), self.activities(service).user_id)
        service.action_cancel()
        self.assertFalse(self.activities(service))

    def test_history_and_install_do_not_notify(self):
        service = self.env['fleet.vehicle.log.services'].with_context(install_mode=True).create({
            'vehicle_id': self.vehicle.id})
        self.assertFalse(self.activities(service))
        history = self.service(state='done', result='Lịch sử',
            actual_start='2026-01-01 01:00:00', actual_end='2026-01-01 02:00:00')
        self.assertFalse(self.activities(history))
