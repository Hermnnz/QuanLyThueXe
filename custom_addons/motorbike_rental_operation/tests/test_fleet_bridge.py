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
        vals = {
            'customer_id': self.customer.id,
            'start_date': '2026-12-01 08:00:00',
            'end_date': '2026-12-03 08:00:00',
            'line_ids': [(0, 0, {
                'vehicle_id': self.vehicle.id,
                'vehicle_type_id': self.price.id,
            })],
        }
        if 'motorbike.rental.payment' in self.env.registry:
            vals['deposit_amount'] = values.get('deposit_amount', 50)
            vals['upfront_received_check'] = True
            vals['upfront_payment_method'] = 'cash'
        vals.update(values)
        contract = self.env['rental.contract'].create(vals)
        if 'motorbike.rental.payment' in self.env.registry:
            contract.write({
                'upfront_received_check': True,
                'upfront_payment_method': 'cash',
            })
        return contract

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
        self.assertEqual(contract.state, 'in_progress')
        operation.odo_end = 150
        operation.action_confirm_return()
        self.assertEqual(self.vehicle.odometer, 150)
        self.assertEqual(self.vehicle.operational_status, 'pending_inspection')
        self.assertFalse(self.vehicle.technical_ready)
        self.assertEqual(operation.ticket_id.state, 'done')
        self.assertEqual(contract.state, 'in_progress')
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

    def test_contract_moves_to_in_progress_when_vehicle_delivered(self):
        contract = self.contract()
        contract.action_confirm()
        self.assertEqual(contract.state, 'confirmed')
        operation = self.operation(contract)
        operation.action_confirm_delivery()
        self.assertEqual(contract.state, 'in_progress')

    def test_contract_moves_to_in_progress_when_one_of_multiple_vehicles_delivered(self):
        model = self.env['fleet.vehicle.model'].search([], limit=1)
        veh2 = self.env['fleet.vehicle'].create({
            'model_id': model.id, 'odometer': 200,
            'technical_ready': True, 'operational_status': 'available'})
        contract = self.contract(line_ids=[
            (0, 0, {'vehicle_id': self.vehicle.id, 'vehicle_type_id': self.price.id}),
            (0, 0, {'vehicle_id': veh2.id, 'vehicle_type_id': self.price.id}),
        ])
        contract.action_confirm()
        ticket = self.env['rental.operation.ticket'].create({
            'contract_id': contract.id,
            'vehicle_detail_ids': [
                (0, 0, {'vehicle_id': self.vehicle.id}),
                (0, 0, {'vehicle_id': veh2.id}),
            ]
        })
        v1 = ticket.vehicle_detail_ids.filtered(lambda v: v.vehicle_id.id == self.vehicle.id)
        v2 = ticket.vehicle_detail_ids.filtered(lambda v: v.vehicle_id.id == veh2.id)
        # Chỉ giao 1 trong 2 xe
        v1.action_confirm_delivery()
        self.assertEqual(v1.status, 'renting')
        self.assertEqual(v2.status, 'waiting')
        self.assertEqual(contract.state, 'in_progress')
        self.assertEqual(ticket.state, 'in_progress')

    def test_incident_quantity_and_penalty_calculation(self):
        catalog = self.env['motorbike.rental.price.catalog'].create({
            'name': 'Trễ giờ thử nghiệm',
            'code': 'TEST-TRE-GIO',
            'category': 'surcharge',
            'unit_price': 50000,
            'unit': 'hour',
        })
        contract = self.contract()
        contract.action_confirm()
        operation = self.operation(contract)
        incident = self.env['rental.operation.incident.log'].create({
            'ticket_id': operation.ticket_id.id,
            'vehicle_id': self.vehicle.id,
            'price_catalog_id': catalog.id,
            'quantity': 5,
        })
        self.assertEqual(incident.quantity, 5)
        self.assertEqual(incident.unit_price, 50000)
        self.assertEqual(incident.penalty_amount, 250000)

    def test_available_contracts_only_shows_confirmed(self):
        brand = self.env['fleet.vehicle.model.brand'].create({'name': 'Brand Extra'})
        model = self.env['fleet.vehicle.model'].create({'name': 'Bike Extra', 'brand_id': brand.id, 'vehicle_type': 'bike'})
        veh2 = self.env['fleet.vehicle'].create({
            'model_id': model.id, 'odometer': 50,
            'technical_ready': True, 'operational_status': 'available'})
        price2 = self.env['rental.vehicle.type'].create({'name': 'Price Extra', 'model_id': model.id, 'daily_rate': 120})
        cust2 = self.env['res.partner'].create({'name': 'Customer Extra'})
        
        draft_contract = self.env['rental.contract'].create({
            'customer_id': cust2.id, 'start_date': '2026-12-10 08:00:00',
            'end_date': '2026-12-12 08:00:00', 'line_ids': [(0, 0, {
                'vehicle_id': veh2.id, 'vehicle_type_id': price2.id})]})
        
        ticket = self.env['rental.operation.ticket'].new()
        ticket._compute_available_contract_ids()
        self.assertNotIn(draft_contract.id, ticket.available_contract_ids.ids)

        draft_contract.action_confirm()
        ticket._compute_available_contract_ids()
        self.assertIn(draft_contract.id, ticket.available_contract_ids.ids)

    def test_incident_needs_repair_syncs_to_fleet_service(self):
        contract = self.contract()
        contract.action_confirm()
        operation = self.operation(contract)
        incident = self.env['rental.operation.incident.log'].create({
            'ticket_id': operation.ticket_id.id,
            'vehicle_id': self.vehicle.id,
            'damage_description': 'Gãy gương bên trái',
            'needs_repair': True,
            'penalty_amount': 150000,
        })
        # Khi mới tạo: chưa bấm đồng bộ nên chưa đẩy sang Fleet
        self.assertFalse(incident.service_id)
        self.assertEqual(incident.needs_repair_display, 'yes')

        # Bấm Lưu thay đổi từ phiếu
        operation.ticket_id.action_bulk_sync_incidents_to_fleet()
        self.assertTrue(incident.service_id)
        self.assertEqual(incident.service_id.vehicle_id.id, self.vehicle.id)
        self.assertEqual(incident.service_id.maintenance_type, 'corrective')
        self.assertEqual(incident.service_id.customer_name, self.customer.name)
        self.assertEqual(incident.service_id.amount, 150000)
        self.assertEqual(incident.status, 'processing')

        # Dữ liệu đã bấm đồng bộ thì KHÔNG cho xóa
        with self.assertRaises(UserError):
            incident.unlink()

        # Thử đổi sự cố đã đồng bộ sang 'Không cần sửa chữa' phải bị chặn
        with self.assertRaises(UserError):
            incident.write({'needs_repair_display': 'no'})

        # Tạo sự cố chọn 'Không cần sửa chữa' qua needs_repair_display
        incident_no_repair = self.env['rental.operation.incident.log'].create({
            'ticket_id': operation.ticket_id.id,
            'vehicle_id': self.vehicle.id,
            'damage_description': 'Trầy xước nhẹ (Không sửa)',
            'needs_repair_display': 'no',
        })
        self.assertFalse(incident_no_repair.needs_repair)
        self.assertEqual(incident_no_repair.needs_repair_display, 'no')
        self.assertFalse(incident_no_repair.service_id)

        # Bấm Lưu thay đổi: sự cố 'Không cần sửa chữa' TUYỆT ĐỐI không bị ép thành 'Cần sửa chữa', không bị đẩy đi và lưu ở trạng thái Hoàn tất
        operation.ticket_id.action_bulk_sync_incidents_to_fleet()
        self.assertFalse(incident_no_repair.needs_repair)
        self.assertEqual(incident_no_repair.needs_repair_display, 'no')
        self.assertFalse(incident_no_repair.service_id)
        self.assertEqual(incident_no_repair.status, 'resolved')

        # Chỉnh sửa từ 'no' sang 'yes' và ngược lại
        incident_no_repair.write({'needs_repair_display': 'yes'})
        self.assertTrue(incident_no_repair.needs_repair)
        self.assertEqual(incident_no_repair.needs_repair_display, 'yes')

        incident_no_repair.write({'needs_repair_display': 'no'})
        self.assertFalse(incident_no_repair.needs_repair)
        self.assertEqual(incident_no_repair.needs_repair_display, 'no')

        incident_unsynced = self.env['rental.operation.incident.log'].create({
            'ticket_id': operation.ticket_id.id,
            'vehicle_id': self.vehicle.id,
            'damage_description': 'Trầy xước nhẹ',
            'needs_repair': False,
        })
        self.assertEqual(incident_unsynced.needs_repair_display, 'no')
        self.assertFalse(incident_unsynced.service_id)
        # Dữ liệu chưa đồng bộ thì cho phép xóa bình thường
        incident_unsynced.unlink()
        incident_no_repair.unlink()

    def test_contract_filter_same_customer_vehicle_time_overlap(self):
        # Hợp đồng 1 đã tạo phiếu giao xe
        contract1 = self.env['rental.contract'].create({
            'customer_id': self.customer.id,
            'start_date': '2026-11-01 08:00:00',
            'end_date': '2026-11-05 18:00:00',
            'line_ids': [(0, 0, {'vehicle_id': self.vehicle.id, 'vehicle_type_id': self.price.id})],
        })
        contract1.action_confirm()
        self.env['rental.operation.ticket'].create({
            'contract_id': contract1.id,
            'vehicle_detail_ids': [(0, 0, {
                'vehicle_id': self.vehicle.id,
                'date_checkout': '2026-11-01 08:00:00',
                'date_checkin': '2026-11-05 18:00:00',
            })],
        })

        # Hợp đồng 2: Cùng khách hàng, cùng xe trùng thời gian nhưng chưa có phiếu giao xe
        contract_overlap = self.env['rental.contract'].create({
            'customer_id': self.customer.id,
            'start_date': '2026-11-03 08:00:00',
            'end_date': '2026-11-07 18:00:00',
            'line_ids': [(0, 0, {'vehicle_id': self.vehicle.id, 'vehicle_type_id': self.price.id})],
        })
        contract_overlap.action_confirm()

        # Hợp đồng 3: Cùng khách hàng, cùng xe khác thời gian
        contract_diff_time = self.env['rental.contract'].create({
            'customer_id': self.customer.id,
            'start_date': '2026-11-10 08:00:00',
            'end_date': '2026-11-15 18:00:00',
            'line_ids': [(0, 0, {'vehicle_id': self.vehicle.id, 'vehicle_type_id': self.price.id})],
        })
        contract_diff_time.action_confirm()

        # Kiểm tra danh sách hợp đồng khả dụng khi tạo phiếu mới:
        new_ticket = self.env['rental.operation.ticket'].new()
        new_ticket._compute_available_contract_ids()

        # Hợp đồng 1 đã có phiếu -> KHÔNG cho hiển thị
        self.assertNotIn(contract1.id, new_ticket.available_contract_ids.ids)
        # Hợp đồng 2 & 3 chưa có phiếu và đã confirmed -> ĐỀU ĐƯỢC PHÉP hiển thị (đã bỏ tiêu chí 3)
        self.assertIn(contract_overlap.id, new_ticket.available_contract_ids.ids)
        self.assertIn(contract_diff_time.id, new_ticket.available_contract_ids.ids)

    def test_vehicle_condition_from_fleet_description(self):
        # Thiết lập mô tả tình trạng trên xe fleet.vehicle
        self.vehicle.description = '<p>Xước nhẹ yếm trước, phanh tốt</p>'

        # Test lấy trực tiếp qua hàm helper
        cond = self.env['rental.operation.ticket.vehicle']._get_vehicle_exterior_condition(self.vehicle)
        self.assertEqual(cond, 'Xước nhẹ yếm trước, phanh tốt')

        # Test tự động nạp khi tạo dòng xe trong phiếu vận hành
        contract = self.contract()
        contract.action_confirm()
        ticket = self.env['rental.operation.ticket'].create({
            'contract_id': contract.id,
            'vehicle_detail_ids': [(0, 0, {
                'vehicle_id': self.vehicle.id,
                'vehicle_price': 100000,
            })]
        })
        self.assertEqual(ticket.vehicle_detail_ids[0].delivery_visual_note, 'Xước nhẹ yếm trước, phanh tốt')
        self.assertEqual(ticket.vehicle_detail_ids[0]._get_display_visual_note(), 'Xước nhẹ yếm trước, phanh tốt')

        # Trường hợp dòng xe bị gán lại giá trị mặc định, _get_display_visual_note vẫn ưu tiên lấy từ xe
        ticket.vehicle_detail_ids[0].delivery_visual_note = 'Ngoại quan của xe không có vấn đề'
        self.assertEqual(ticket.vehicle_detail_ids[0]._get_display_visual_note(), 'Xước nhẹ yếm trước, phanh tốt')

        # Test biên lai giao xe khi in PDF sẽ đồng bộ lại mô tả tình trạng
        receipt = self.env['rental.delivery.receipt'].create({
            'ticket_id': ticket.id,
            'customer_id': self.customer.id,
            'vehicle_ids': [(6, 0, ticket.vehicle_detail_ids.ids)],
        })
        receipt.action_print_receipt()
        self.assertEqual(ticket.vehicle_detail_ids[0].delivery_visual_note, 'Xước nhẹ yếm trước, phanh tốt')

    def test_ticket_prevent_unlink(self):
        """Kiểm tra ngăn chặn việc xóa phiếu vận hành"""
        contract = self.contract()
        contract.action_confirm()
        ticket = self.env['rental.operation.ticket'].create({
            'contract_id': contract.id,
            'vehicle_detail_ids': [(0, 0, {
                'vehicle_id': self.vehicle.id,
                'vehicle_price': 100000,
            })]
        })

        # Ngăn chặn việc xóa phiếu vận hành
        with self.assertRaises(UserError):
            ticket.unlink()

    def test_ticket_contract_cancelled_and_locks(self):
        """Kiểm tra khi Hợp đồng bị hủy:
        - Phiếu vận hành chuyển trạng thái 'contract_cancelled'
        - Không được chỉnh sửa gì ở phiếu giao xe (phiếu và chi tiết xe)
        - Không được tạo hoặc liên kết sự cố tới phiếu này
        """
        contract = self.contract()
        contract.action_confirm()
        ticket = self.env['rental.operation.ticket'].create({
            'contract_id': contract.id,
            'vehicle_detail_ids': [(0, 0, {'vehicle_id': self.vehicle.id})],
        })
        veh_detail = ticket.vehicle_detail_ids[0]

        # Bắt đầu giao xe để xe chuyển sang renting
        veh_detail.action_start_delivery()
        self.assertEqual(veh_detail.status, 'delivering')
        self.assertEqual(self.vehicle.operational_status, 'renting')

        # Hủy hợp đồng
        if hasattr(contract, 'action_cancel'):
            contract.action_cancel()
        else:
            contract.write({'state': 'cancelled'})

        # 1. Phiếu chuyển sang 'contract_cancelled'
        self.assertEqual(ticket.state, 'contract_cancelled')

        # 2. Không cho phép chỉnh sửa phiếu
        with self.assertRaises(UserError):
            ticket.write({'quick_delivery_location': 'Hà Nội'})

        # 3. Không cho phép xóa phiếu
        with self.assertRaises(UserError):
            ticket.unlink()

        # 4. Không cho phép chỉnh sửa xe con
        with self.assertRaises(UserError):
            veh_detail.write({'delivery_location': 'Đà Nẵng'})

        # 5. Không cho phép xóa xe con
        with self.assertRaises(UserError):
            veh_detail.unlink()

        # 6. Không cho phép thêm xe con mới
        with self.assertRaises(UserError):
            self.env['rental.operation.ticket.vehicle'].create({
                'ticket_id': ticket.id,
                'vehicle_id': self.vehicle.id,
            })

        # 7. Không cho phép thực hiện action giao xe
        with self.assertRaises(UserError):
            veh_detail.action_confirm_delivery()
        with self.assertRaises(UserError):
            ticket.action_bulk_start_delivery()

        # 8. Sự cố không được gọi/liên kết tới mã bản ghi phiếu này
        catalog = self.env['motorbike.rental.price.catalog'].create({
            'name': 'Hỏng còi',
            'catalog_type': 'damage',
            'unit_price': 30000,
        })
        with self.assertRaises(UserError):
            self.env['rental.operation.incident.log'].create({
                'ticket_id': ticket.id,
                'vehicle_id': self.vehicle.id,
                'price_catalog_id': catalog.id,
            })

        # Tạo sự cố không có ticket_id, sau đó thử gắn ticket_id cũng phải bị chặn
        incident_independent = self.env['rental.operation.incident.log'].create({
            'vehicle_id': self.vehicle.id,
            'price_catalog_id': catalog.id,
        })
        with self.assertRaises(UserError):
            incident_independent.write({'ticket_id': ticket.id})

    def test_return_receipt_only_delivered_vehicles_can_be_returned(self):
        """Kiểm tra Biên lai thu hồi xe chỉ có 2 trạng thái (pending, returned)
        và chỉ được phép xác nhận thu hồi khi xe đã ở trạng thái đã bàn giao ('renting').
        """
        contract = self.contract()
        contract.action_confirm()
        veh_detail = self.operation(contract)
        ticket = veh_detail.ticket_id

        return_receipt = self.env['rental.return.receipt'].create({
            'ticket_id': ticket.id,
            'customer_id': contract.partner_id.id,
            'vehicle_ids': [(6, 0, [veh_detail.id])],
        })
        # Trạng thái ban đầu là 'pending' (Chưa thực hiện)
        self.assertEqual(return_receipt.state, 'pending')

        # 1. Xe đang ở trạng thái 'waiting' (chưa bàn giao) -> Không được phép xác nhận thu hồi
        self.assertEqual(veh_detail.status, 'waiting')
        with self.assertRaises(UserError):
            return_receipt.action_confirm_return()
        self.assertEqual(return_receipt.state, 'pending')

        # 2. Không cho phép ghi đè trực tiếp state='returned' khi xe chưa bàn giao
        with self.assertRaises(UserError):
            return_receipt.write({'state': 'returned'})
        self.assertEqual(return_receipt.state, 'pending')

        # 3. Bàn giao xe cho khách hàng thành công (status -> 'renting')
        veh_detail.action_confirm_delivery()
        self.assertEqual(veh_detail.status, 'renting')

        # 4. Khi xe đã bàn giao -> Xác nhận thu hồi thành công, chuyển sang 'returned'
        return_receipt.action_confirm_return()
        self.assertEqual(return_receipt.state, 'returned')
        self.assertEqual(veh_detail.status, 'returned')



