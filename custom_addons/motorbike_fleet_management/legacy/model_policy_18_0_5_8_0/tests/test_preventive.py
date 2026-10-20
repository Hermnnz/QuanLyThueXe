from datetime import timedelta
from unittest.mock import patch
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPeriodicMaintenance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Periodic test'})
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'Periodic bike', 'brand_id': brand.id, 'vehicle_type': 'bike',
            'service_interval_km': 1000, 'service_interval_months': 3,
            'service_warning_km': 100, 'service_warning_days': 7})

    def vehicle(self, **values):
        return self.env['fleet.vehicle'].create({
            'model_id': self.model.id, 'is_electric_motorbike': True,
            'odometer': 500, 'operational_status': 'available', 'technical_ready': True, **values})

    def anchored(self):
        return self.vehicle(service_reference_date=fields.Date.today(), service_reference_odo=100)

    def complete(self, vehicle, kind='preventive'):
        service = self.env['fleet.vehicle.log.services'].create({
            'vehicle_id': vehicle.id, 'maintenance_type': kind, 'result': 'Đã kiểm tra hoàn tất'})
        service.action_start()
        service.action_done()
        return service

    def test_missing_baseline_does_not_invent_history(self):
        vehicle = self.vehicle()
        self.assertEqual(vehicle.service_schedule_state, 'missing_baseline')
        self.assertFalse(vehicle.service_last_date)
        self.assertFalse(vehicle.service_next_date)
        self.assertEqual(vehicle.service_next_odo, 0)

    def test_kilometer_boundaries_do_not_block_rental(self):
        vehicle = self.anchored()
        self.assertEqual(vehicle.service_next_odo, 1100)
        self.assertEqual(vehicle.service_schedule_state, 'ok')
        for odo, state in [(1000, 'soon'), (1100, 'due'), (1101, 'overdue')]:
            vehicle.odometer = odo
            self.assertEqual(vehicle.service_schedule_state, state)
            self.assertEqual(vehicle.operational_status, 'available')
            self.assertFalse(vehicle.rental_blocked)
            self.assertTrue(vehicle.check_fleet_availability('2027-01-01 00:00:00', '2027-01-02 00:00:00')[0]['fleet_ok'])

    def test_calendar_boundaries_and_daily_refresh(self):
        vehicle = self.anchored()
        deadline = vehicle.service_next_date
        for days, state in [(8, 'ok'), (7, 'soon'), (0, 'due'), (-1, 'overdue')]:
            with patch.object(type(vehicle), '_maintenance_today', return_value=deadline - timedelta(days=days)):
                self.env['fleet.vehicle']._cron_refresh_service_alerts()
                self.assertEqual(vehicle.service_schedule_state, state)

    def test_month_end_and_single_criterion(self):
        vehicle = self.vehicle(service_reference_date='2026-01-31', service_reference_odo=0)
        self.assertEqual(str(vehicle.service_next_date), '2026-04-30')
        self.model.service_interval_months = 0
        self.assertFalse(vehicle.service_next_date)
        self.assertEqual(vehicle.service_next_odo, 1000)
        self.model.service_interval_km = 0
        self.assertEqual(vehicle.service_schedule_state, 'unconfigured')

    def test_completion_resets_periodic_milestones_only(self):
        vehicle = self.anchored()
        old_date, old_odo = vehicle.service_next_date, vehicle.service_next_odo
        self.complete(vehicle, 'corrective')
        self.assertEqual(vehicle.service_next_date, old_date)
        self.assertEqual(vehicle.service_next_odo, old_odo)
        vehicle.action_confirm_technical_ready()
        service = self.complete(vehicle)
        self.assertTrue(service.service_odometer_recorded)
        self.assertEqual(service.service_odometer, 500)
        self.assertEqual(vehicle.service_next_odo, 1500)
        self.assertEqual(vehicle.operational_status, 'pending_inspection')
        service.active = False
        self.assertEqual(vehicle.service_next_odo, 1500)

    def test_old_historical_service_without_snapshot_is_not_assumed(self):
        vehicle = self.vehicle()
        self.env['fleet.vehicle.log.services'].create({
            'vehicle_id': vehicle.id, 'state': 'done', 'result': 'Lịch sử cũ',
            'actual_start': '2026-01-01 01:00:00', 'actual_end': '2026-01-01 02:00:00'})
        self.assertEqual(vehicle.service_schedule_state, 'missing_baseline')

    def test_create_button_is_idempotent_and_does_not_start_work(self):
        vehicle = self.anchored()
        first = vehicle.action_preventive_service()
        second = vehicle.action_preventive_service()
        self.assertEqual(first['res_id'], second['res_id'])
        self.assertEqual(vehicle.open_preventive_count, 1)
        self.assertEqual(vehicle.operational_status, 'available')
        self.env['fleet.vehicle.log.services'].browse(first['res_id']).action_cancel()
        self.assertNotEqual(vehicle.action_preventive_service()['res_id'], first['res_id'])

    def test_existing_manual_appointment_still_warns(self):
        vehicle = self.vehicle(next_service_date=fields.Date.today())
        self.assertEqual(vehicle.service_schedule_state, 'due')
        self.complete(vehicle)
        self.assertFalse(vehicle.next_service_date)
        self.assertEqual(vehicle.service_next_odo, 1500)

    def test_deleting_latest_service_restores_initial_milestone(self):
        vehicle = self.anchored()
        service = self.complete(vehicle)
        self.assertEqual(vehicle.service_next_odo, 1500)
        service.unlink()
        self.assertEqual(vehicle.service_next_odo, 1100)

    def test_model_policy_change_updates_all_vehicles(self):
        first, second = self.anchored(), self.anchored()
        self.model.service_interval_km = 2000
        self.assertEqual(first.service_next_odo, 2100)
        self.assertEqual(second.service_next_odo, 2100)

    def test_invalid_policy_and_baseline_rejected(self):
        for vals in [{'service_interval_km': -1}, {'service_warning_days': -1},
                     {'service_warning_km': 1000}]:
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.model.write(vals)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.vehicle(service_reference_date=fields.Date.today(), service_reference_odo=501)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.vehicle(service_reference_date=fields.Date.today() + timedelta(days=1))
