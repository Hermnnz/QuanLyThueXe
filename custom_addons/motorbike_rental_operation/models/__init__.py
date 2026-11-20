# -*- coding: utf-8 -*-
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# KHAI BÁO NẠP TOÀN BỘ 12 FILE MODEL & WIZARD CỦA MODULE VẬN HÀNH
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
from . import rental_operation_ticket # Phiếu vận hành tổng (Model cha trung tâm)
from . import rental_operation_ticket_vehicle # Chi tiết từng xe vận hành & đồng bộ sang Fleet
from . import rental_incident_log # Nhật ký sự cố & đồng bộ sửa chữa sang Fleet
from . import price_catalog # Bảng giá phụ phí & bồi thường sự cố
from . import rental_operation_confirm_wizard # Wizard popup xác nhận thao tác hàng loạt
from . import rental_delivery_receipt # Biên lai giao xe (BLGX)
from . import rental_delivery_receipt_wizard # Wizard kiểm đếm & xuất Biên lai giao xe
from . import rental_return_receipt # Biên lai thu hồi xe (BLTH)
from . import rental_return_receipt_wizard # Wizard kiểm đếm & xuất Biên lai thu hồi xe
from . import rental_vehicle_schedule_wizard # Wizard cập nhật nhanh địa điểm/giờ giao nhận
from . import rental_contract # Kế thừa mở rộng Hợp đồng (rental.contract) từ module Core
from . import rental_vehicle_exchange # Phiếu đổi xe A -> B trong quá trình thuê
