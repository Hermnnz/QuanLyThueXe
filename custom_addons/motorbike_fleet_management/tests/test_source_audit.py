from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFleetSourceAudit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Source audit'})
        model = cls.env['fleet.vehicle.model'].create({
            'name': 'Audit bike', 'brand_id': brand.id, 'vehicle_type': 'bike'})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id, 'is_electric_motorbike': True,
            'operational_status': 'available', 'technical_ready': True})

    def service(self, **values):
        return self.env['fleet.vehicle.log.services'].create({
            'vehicle_id': self.vehicle.id, **values})

    def test_docs_stored_odometer_accepts_operations_update(self):
        field = self.env['fleet.vehicle']._fields['odometer']
        self.assertTrue(field.store)
        self.assertFalse(field.compute)
        self.vehicle.write({'odometer': 120})
        self.env.flush_all()
        self.env.cr.execute('SELECT odometer FROM fleet_vehicle WHERE id=%s', (self.vehicle.id,))
        self.assertEqual(self.env.cr.fetchone()[0], 120)
        self.vehicle.action_deliver_vehicle('2027-01-01 00:00:00', '2027-01-02 00:00:00', odometer_start=120)
        self.vehicle.action_return_vehicle('pending', odometer_end=150)
        self.assertEqual(self.vehicle.odometer, 150)

    def test_nonfinite_repair_cost_is_rejected(self):
        for value in [float('nan'), float('inf'), -float('inf')]:
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.service(amount=value)
        service = self.service(amount=0)
        for value in [float('nan'), float('inf')]:
            with self.assertRaises(ValidationError), self.cr.savepoint():
                service.cost = value
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['fleet.vehicle.log.services'].with_context(
                default_vehicle_id=self.vehicle.id, default_amount=float('inf')).create({})

    def test_waiting_or_maintenance_vehicle_cannot_be_technical_ready(self):
        for status in ['pending_inspection', 'maintenance']:
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.vehicle.write({'operational_status': status, 'technical_ready': True})
        self.vehicle.write({'operational_status': 'pending_inspection', 'technical_ready': False})
        self.assertFalse(self.vehicle.check_fleet_availability(
            '2026-12-01 02:00:00', '2026-12-02 02:00:00')[0]['fleet_ok'])
        self.vehicle.action_confirm_technical_ready()
        self.assertEqual(self.vehicle.operational_status, 'available')

    def test_copied_service_needs_its_own_work_result(self):
        original = self.service(state='done', result='Đã thay gương cho lần sửa trước',
                                actual_start='2026-10-01 00:00:00', actual_end='2026-10-01 01:00:00')
        copied = original.copy()
        self.assertEqual(copied.state, 'new')
        self.assertFalse(copied.result)
        copied.action_start()
        with self.assertRaises(UserError), self.cr.savepoint():
            copied.action_done()

    def test_planned_fields_and_scheduled_state_removed(self):
        Service = self.env['fleet.vehicle.log.services']
        self.assertNotIn('scheduled_start', Service._fields)
        self.assertNotIn('scheduled_end', Service._fields)
        self.assertNotIn('scheduled', dict(Service._fields['state']._description_selection(self.env)))
        self.assertFalse(hasattr(Service, 'action_schedule'))
        self.assertEqual(Service._fields['actual_start'].string, 'Ngày bắt đầu')
        self.assertEqual(Service._fields['actual_end'].string, 'Ngày kết thúc')
