from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPeriodicDemoData(TransactionCase):
    def vehicle(self, key):
        return self.env.ref('motorbike_rental_demo.periodic_vehicle_' + key)

    def test_milestones_and_identity(self):
        for key, odo in [('routine_ok', 6240), ('soon_km', 9850), ('due_km', 12000),
                         ('overdue_km', 15280), ('soon_date', 7420), ('overdue_date', 4350),
                         ('missing_baseline', 8320), ('in_progress', 18760)]:
            vehicle = self.vehicle(key)
            self.assertEqual(vehicle.odometer, odo)
            self.assertTrue(vehicle.vehicle_code)
            self.assertTrue(vehicle.license_plate)
        self.assertEqual(self.vehicle('due_km').service_next_odo, 12000)
        self.assertEqual(self.vehicle('soon_km').service_next_odo, 10000)
        self.assertEqual(self.vehicle('missing_baseline').service_schedule_state, 'missing_baseline')
        self.assertFalse(self.vehicle('missing_baseline').service_last_date)

    def test_open_jobs_and_completed_history(self):
        running = self.env.ref('motorbike_rental_demo.periodic_service_running')
        scheduled = self.env.ref('motorbike_rental_demo.periodic_service_scheduled')
        self.assertEqual(running.state, 'running')
        self.assertEqual(running.vehicle_id.operational_status, 'maintenance')
        self.assertEqual(scheduled.state, 'scheduled')
        self.assertEqual(scheduled.vehicle_id.operational_status, 'available')
        self.assertEqual(scheduled.vehicle_id.action_preventive_service()['res_id'], scheduled.id)
        for key in ['routine_ok', 'overdue_km']:
            service = self.env.ref('motorbike_rental_demo.periodic_history_' + key)
            self.assertEqual(service.state, 'done')
            self.assertTrue(service.service_odometer_recorded)
            self.assertEqual(service.service_odometer, service.vehicle_id.service_last_odo)

    def test_old_rental_links_are_unchanged(self):
        vehicle = self.env.ref('motorbike_rental_demo.demo_w8_vehicle_3')
        self.assertEqual(vehicle.operational_status, 'renting')
        self.assertEqual(vehicle.odometer, 1000)
        self.assertEqual(self.env.ref('motorbike_rental_demo.demo_w8_vehicle_4').odometer, 2080)
