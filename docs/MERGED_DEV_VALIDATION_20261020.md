# Kết quả kiểm tra bản gộp trước khi đẩy hai nhánh — 20/10/2026

Fleet: 18.0.5.13.2. Đã gộp các commit dev `5495c5c` và `62647b9` vào bản Fleet, không có xung đột Git. Không thay đổi database demo đang chạy cổng 8078.

Nâng cấp đủ 5 module trên database kiểm thử riêng thành công. Bộ kiểm tra chạy 144 ca: **2 thất bại, 10 lỗi**. Không có lỗi được ghi nhận trong các ca Fleet và Demo; không được dùng kết quả kiểm tra Fleet trước đó để khẳng định toàn bộ bản gộp đạt.

Các điểm cần phối hợp với nhóm:

- Sáu ca Core xác nhận hợp đồng bị chặn bởi quy tắc Finance mới yêu cầu thu đủ tiền thuê/cọc; dữ liệu kiểm thử Core chưa đáp ứng quy tắc này.
- Core mới bỏ lời gọi kiểm tra điều kiện Fleet khỏi `_check_vehicle_availability`; ca Vận hành về xe khóa thuê/chưa đạt kỹ thuật/bảo dưỡng không còn bị chặn khi xác nhận hợp đồng. Khi giao xe, Fleet vẫn chặn xe không đủ điều kiện.
- Một ca giao xe mong đợi `ValidationError`, trong khi Fleet trả `UserError` khi xe bị khóa thuê.
- Bốn ca Finance chưa đạt liên quan lập hóa đơn sau trả xe và tạo giao dịch thanh toán. Cần rà soát với tác giả Core/Finance; chưa tự thay đổi nghiệp vụ của các module đó trong lần đẩy này.

Danh sách ca chưa đạt:

- `motorbike_rental_core.tests.test_rental_contract` — ERROR: `TestRentalContract.test_allows_adjacent_reservations_for_same_vehicle`
- `motorbike_rental_core.tests.test_rental_contract` — ERROR: `TestRentalContract.test_cancel_from_active_states`
- `motorbike_rental_core.tests.test_rental_contract` — ERROR: `TestRentalContract.test_confirmed_contract_and_vehicle_lines_are_immutable`
- `motorbike_rental_core.tests.test_rental_contract` — ERROR: `TestRentalContract.test_rejects_overlapping_vehicle_reservation`
- `motorbike_rental_core.tests.test_rental_contract` — ERROR: `TestRentalContract.test_rejects_rescheduling_confirmed_contract`
- `motorbike_rental_core.tests.test_rental_contract` — ERROR: `TestRentalContract.test_state_machine_actions`
- `motorbike_rental_operation.tests.test_fleet_bridge` — FAIL: `TestFleetRentalBridge.test_contract_rejects_blocked_unready_and_maintenance`
- `motorbike_rental_operation.tests.test_fleet_bridge` — ERROR: `TestFleetRentalBridge.test_delivery_rechecks_conditions_after_reservation`
- `motorbike_rental_finance.tests.test_invoice_return` — FAIL: `TestInvoiceReturn.test_charge_button_obeys_return_rule`
- `motorbike_rental_finance.tests.test_invoice_return` — ERROR: `TestInvoiceReturn.test_partial_return_blocks_then_full_return_allows_invoice`
- `motorbike_rental_finance.tests.test_upfront_payments` — ERROR: `TestUpfrontPayments.test_partial_receipts_allow_signing_only_when_both_are_fully_paid`
- `motorbike_rental_finance.tests.test_upfront_payments` — ERROR: `TestUpfrontPayments.test_partial_rent_and_other_transaction_types_do_not_cover_rent`

Log đầy đủ nằm tại `archive/dev-merge-validation/pre-push-merged-20261020.log` trên máy kiểm tra (không đưa log/database lên GitHub).
