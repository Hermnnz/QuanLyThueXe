from psycopg2.errors import UniqueViolation
from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestFleetBusinessHardening(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Hardening'})
        cls.model = cls.env['fleet.vehicle.model'].create({'name': 'EV', 'brand_id': cls.brand.id, 'vehicle_type': 'bike'})

    def vehicle(self, **values):
        return self.env['fleet.vehicle'].create({'model_id': self.model.id, 'is_electric_motorbike': True, **values})

    def ready(self):
        return self.vehicle(operational_status='available', technical_ready=True)

    def test_sequence_and_copy(self):
        first, second = self.vehicle(), self.vehicle()
        self.assertTrue(first.vehicle_code.startswith('XE'))
        self.assertNotEqual(first.vehicle_code, second.vehicle_code)
        first.license_plate = 'TEST-COPY-123'
        copied = first.copy()
        self.assertNotEqual(copied.vehicle_code, first.vehicle_code)
        self.assertFalse(copied.license_plate)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            first.vehicle_code = False

    @mute_logger('odoo.sql_db')
    def test_normalized_plate_unique_create_write_and_archived(self):
        first = self.vehicle(license_plate='59-A1 123.45')
        for plate in ['59a112345', '59 A1-12345']:
            with self.assertRaises(UniqueViolation), self.cr.savepoint():
                self.vehicle(license_plate=plate)
        other = self.vehicle()
        with self.assertRaises(UniqueViolation), self.cr.savepoint():
            other.license_plate = '59A112345'
        first.active = False
        with self.assertRaises(UniqueViolation), self.cr.savepoint():
            self.vehicle(license_plate='59-A1-12345')
        self.vehicle(license_plate=False)
        self.vehicle(license_plate=False)

    @mute_logger('odoo.sql_db')
    def test_normalized_code_unique(self):
        self.vehicle(vehicle_code=' xx 100 ')
        with self.assertRaises(UniqueViolation), self.cr.savepoint():
            self.vehicle(vehicle_code='XX100')

    def test_cannot_archive_delete_or_force_release_renting_vehicle(self):
        vehicle = self.ready()
        vehicle.action_deliver_vehicle('2027-01-01 00:00:00', '2027-01-02 00:00:00')
        for values in [{'active': False}, {'operational_status': 'available'}, {'is_electric_motorbike': False}]:
            with self.assertRaises(UserError), self.cr.savepoint():
                vehicle.write(values)
        with self.assertRaises(UserError), self.cr.savepoint():
            vehicle.unlink()
        vehicle.action_return_vehicle('passed')
        self.assertEqual(vehicle.operational_status, 'available')

    def test_cannot_reclassify_scheduled_or_running_service(self):
        vehicle = self.ready()
        service = self.env['fleet.vehicle.log.services'].create({'vehicle_id': vehicle.id, 'state': 'scheduled',
            'scheduled_start': '2027-01-01 00:00:00', 'scheduled_end': '2027-01-02 00:00:00'})
        with self.assertRaises(UserError), self.cr.savepoint():
            vehicle.is_electric_motorbike = False
        service.action_start()
        with self.assertRaises(UserError), self.cr.savepoint():
            vehicle.is_electric_motorbike = False

    def test_completed_service_frozen_but_note_allowed(self):
        vehicle = self.ready()
        service = self.env['fleet.vehicle.log.services'].create({'vehicle_id': vehicle.id, 'result': 'Đã sửa'})
        service.action_start()
        service.action_done()
        for values in [{'result': False}, {'amount': 123}, {'next_service_date': '2027-01-01'}, {'actual_end': False}]:
            with self.assertRaises(UserError), self.cr.savepoint():
                service.write(values)
        service.notes = 'Ghi chú bổ sung'
        self.assertEqual(service.result, 'Đã sửa')
        with self.assertRaises(UserError), self.cr.savepoint():
            vehicle.is_electric_motorbike = False
        with self.assertRaises(UserError), self.cr.savepoint():
            vehicle.unlink()

    def test_history_requires_manager_result_and_timestamps(self):
        vehicle = self.ready()
        services = self.env['fleet.vehicle.log.services']
        with self.assertRaises(ValidationError), self.cr.savepoint():
            services.create({'vehicle_id': vehicle.id, 'state': 'done'})
        tech = self.env['res.users'].create({'name': 'Tech history', 'login': 'hardening_tech',
            ('group_ids' if 'group_ids' in self.env['res.users']._fields else 'groups_id'): [Command.set([self.env.ref('motorbike_fleet_management.group_motorbike_technician').id])]})
        with self.assertRaises(UserError), self.cr.savepoint():
            services.with_user(tech).create({'vehicle_id': vehicle.id, 'state': 'done', 'result': 'Đã sửa',
                'actual_start': '2026-01-01 00:00:00', 'actual_end': '2026-01-01 01:00:00'})

    def test_cannot_force_ready_after_pending(self):
        vehicle = self.vehicle()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            vehicle.write({'operational_status': 'available', 'technical_ready': True})
        vehicle.action_confirm_technical_ready()
        self.assertEqual(vehicle.operational_status, 'available')

    def test_delete_latest_milestone_recomputes_vehicle(self):
        vehicle = self.ready()
        previous = self.env['fleet.vehicle.log.services'].create({'vehicle_id': vehicle.id, 'state': 'done',
            'date': '2026-01-01', 'next_service_date': '2026-05-01', 'result': 'Lịch sử',
            'actual_start': '2026-01-01 00:00:00', 'actual_end': '2026-01-01 01:00:00'})
        latest = self.env['fleet.vehicle.log.services'].create({'vehicle_id': vehicle.id, 'date': '2026-02-01',
            'next_service_date': '2026-06-01', 'result': 'Đã sửa'})
        latest.action_start()
        latest.action_done()
        latest.unlink()
        self.assertEqual(vehicle.next_service_date, previous.next_service_date)

    def test_archived_catalog_blocks_selection_and_delivery(self):
        vehicle = self.ready()
        self.brand.active = False
        self.assertIn('inactive_catalog', vehicle.check_fleet_availability('2027-01-01 00:00:00', '2027-01-02 00:00:00')[0]['reasons'])
        with self.assertRaises(UserError), self.cr.savepoint():
            self.vehicle()
        self.brand.active = True
        self.model.active = False
        with self.assertRaises(UserError), self.cr.savepoint():
            self.vehicle()

    def test_archived_newer_service_keeps_latest_milestone(self):
        vehicle = self.ready()
        services = self.env['fleet.vehicle.log.services']
        newer = services.create({'vehicle_id': vehicle.id, 'date': '2026-02-01',
            'next_service_date': '2027-06-01', 'result': 'Đã sửa'})
        newer.action_start()
        newer.action_done()
        newer.active = False
        older = services.create({'vehicle_id': vehicle.id, 'date': '2026-01-01',
            'next_service_date': '2027-05-01', 'result': 'Bổ sung công việc trước đó'})
        older.action_start()
        older.action_done()
        self.assertEqual(str(vehicle.next_service_date), '2027-06-01')
        newer.unlink()
        self.assertEqual(str(vehicle.next_service_date), '2027-05-01')

    def test_archived_history_cannot_be_bypassed_by_reclassification(self):
        vehicle = self.ready()
        service = self.env['fleet.vehicle.log.services'].create({'vehicle_id': vehicle.id, 'result': 'Đã sửa'})
        service.action_start()
        service.action_done()
        service.active = False
        with self.assertRaises(UserError), self.cr.savepoint():
            vehicle.is_electric_motorbike = False
        with self.assertRaises(UserError), self.cr.savepoint():
            vehicle.unlink()

    def test_active_fields_have_visible_form_controls(self):
        for xmlid in ['fleet.fleet_vehicle_model_brand_view_form', 'fleet.fleet_vehicle_model_view_form',
                      'fleet.fleet_vehicle_view_form', 'fleet.fleet_vehicle_log_services_view_form']:
            arch = self.env.ref(xmlid)._get_combined_arch()
            self.assertTrue(arch.xpath('.//field[@name="active" and not(@invisible)]'), xmlid)
        self.assertEqual(self.env.ref('fleet.fleet_vehicle_model_brand_action').context, '{}')

    def test_vehicle_cannot_be_deleted_even_without_history_or_with_sudo(self):
        vehicle = self.ready()
        for record in [vehicle, vehicle.sudo()]:
            with self.assertRaises(UserError), self.cr.savepoint():
                record.unlink()
        vehicle.active = False
        self.assertTrue(vehicle.exists())
        self.assertFalse(vehicle.active)
        with self.assertRaises(UserError), self.cr.savepoint():
            vehicle.sudo().unlink()
        vehicle.active = True
        self.assertTrue(vehicle.active)

    def test_batch_vehicle_delete_does_not_remove_any_vehicle(self):
        vehicles = self.ready() | self.ready()
        with self.assertRaises(UserError), self.cr.savepoint():
            vehicles.sudo().unlink()
        self.assertEqual(len(vehicles.exists()), 2)
