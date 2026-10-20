from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFleetRentalBridge(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({'name': 'Bridge customer'})
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Bridge brand'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'Bridge bike', 'brand_id': brand.id, 'vehicle_type': 'bike'})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id, 'is_electric_motorbike': True, 'odometer': 100,
            'technical_ready': True, 'operational_status': 'available'})
        cls.price = cls.env['rental.vehicle.type'].create({'name': 'Bridge price', 'model_id': model.id, 'daily_rate': 100})

    def contract(self, **values):
        return self.env['rental.contract'].create({
            'customer_id': self.customer.id, 'start_date': '2026-12-01 08:00:00',
            'end_date': '2026-12-03 08:00:00', 'line_ids': [(0, 0, {
                'vehicle_id': self.vehicle.id, 'vehicle_type_id': self.price.id})], **values})

    def operation(self, contract):
        return self.env['rental.operation.ticket'].create({
            'contract_id': contract.id, 'vehicle_detail_ids': [(0, 0, {'vehicle_id': self.vehicle.id})]
        }).vehicle_detail_ids

    def test_contract_rejects_blocked_unready_and_maintenance(self):
        contract = self.contract()
        self.vehicle.write({'rental_blocked': True, 'block_reason': 'Kiểm kê'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            contract.action_confirm()
        self.vehicle.write({'rental_blocked': False})
        service = self.env['fleet.vehicle.log.services'].create({
            'vehicle_id': self.vehicle.id, 'state': 'running'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            contract.action_confirm()
        service.action_cancel()
        self.vehicle.write({'operational_status': 'pending_inspection', 'technical_ready': False})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            contract.action_confirm()
        self.vehicle.action_confirm_technical_ready()
        contract.action_confirm()
        overlapping = self.contract()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            overlapping.action_confirm()

    def test_full_cycle_and_repair(self):
        contract = self.contract()
        contract.action_confirm()
        operation = self.operation(contract)
        operation.action_start_delivery()
        self.assertEqual(self.vehicle.operational_status, 'renting')
        operation.action_confirm_delivery()
        operation.odo_end = 150
        operation.action_confirm_return()
        self.assertEqual(self.vehicle.odometer, 150)
        self.assertEqual(self.vehicle.operational_status, 'pending_inspection')
        self.assertFalse(self.vehicle.technical_ready)
        self.assertEqual(operation.ticket_id.state, 'done')
        with self.assertRaises(UserError), self.cr.savepoint():
            operation.action_confirm_return()
        with self.assertRaises(UserError), self.cr.savepoint():
            operation.action_reset_waiting()
        with self.assertRaises(UserError), self.cr.savepoint():
            operation.ticket_id.unlink()
        service = self.env['fleet.vehicle.log.services'].create({'vehicle_id': self.vehicle.id, 'maintenance_type': 'corrective'})
        service.action_start()
        self.assertEqual(self.vehicle.operational_status, 'maintenance')
        service.result = 'Đã sửa và kiểm tra'
        service.action_done()
        self.assertEqual(self.vehicle.operational_status, 'available')
        self.vehicle.action_confirm_technical_ready()
        self.assertEqual(self.vehicle.operational_status, 'available')
        self.assertEqual(self.env['fleet.vehicle.odometer'].search_count([('vehicle_id', '=', self.vehicle.id)]), 2)

    def test_delivery_rechecks_conditions_after_reservation(self):
        contract = self.contract()
        contract.action_confirm()
        operation = self.operation(contract)
        self.vehicle.write({'rental_blocked': True, 'block_reason': 'Phát hiện lỗi'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            operation.action_confirm_delivery()
        self.assertEqual(operation.status, 'waiting')
        self.assertEqual(self.vehicle.operational_status, 'available')

    def test_return_rejects_decreasing_odo(self):
        contract = self.contract()
        contract.action_confirm()
        operation = self.operation(contract)
        operation.action_confirm_delivery()
        operation.odo_end = 90
        with self.assertRaises(ValidationError), self.cr.savepoint():
            operation.action_confirm_return()
        self.assertEqual(operation.status, 'renting')
        self.assertEqual(self.vehicle.operational_status, 'renting')

    def test_cannot_deliver_draft_contract(self):
        operation = self.operation(self.contract())
        with self.assertRaises(UserError), self.cr.savepoint():
            operation.action_confirm_delivery()

    def test_rental_user_can_complete_delivery_return(self):
        group = self.env.ref('motorbike_rental_core.group_rental_user')
        user = self.env['res.users'].create({'name': 'Bridge operator', 'login': 'bridge-operator', 'groups_id': [(6, 0, [group.id])]})
        contract = self.contract().with_user(user)
        contract.action_confirm()
        operation = self.operation(contract).with_user(user)
        operation.action_confirm_delivery()
        operation.action_confirm_return()
        self.assertEqual(operation.vehicle_id.operational_status, 'pending_inspection')
