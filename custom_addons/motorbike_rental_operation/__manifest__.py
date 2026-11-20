# -*- coding: utf-8 -*-
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# FILE KHAI BÁO CẤU HÌNH MODULE VẬN HÀNH THUÊ XE MÁY
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
{
    'name': 'Vận Hành Thuê Xe Máy',
    'version': '1.0',
    'summary': 'Quản lý Giao nhận, Hậu kiểm và Sự cố',
    'author': 'Giang',
    'license': 'LGPL-3',
    'depends': ['base', 'fleet', 'motorbike_rental_core'], # Phụ thuộc 3 module: nhân Odoo, Quản lý đội xe (Fleet) và Hợp đồng lõi (Core)
    'data': [ # Thứ tự load rất quan trọng: phân quyền -> dữ liệu nền -> báo cáo PDF -> giao diện -> menu cuối cùng
        'security/ir.model.access.csv', # Cấp quyền đọc/ghi/tạo/xóa cho các Model và Wizard
        'data/sequence.xml', # Bộ sinh mã tự động (OP-, BLGX-, BLTH-, DX-, SC-...)
        'data/price_catalog_data.xml', # Dữ liệu mẫu bảng giá phụ phí và bồi thường
        'report/delivery_receipt_report.xml', # Mẫu in PDF Biên lai giao xe
        'report/return_receipt_report.xml', # Mẫu in PDF Biên lai thu hồi xe
        'views/price_catalog_views.xml', # Giao diện Bảng giá sự cố
        'views/confirm_wizard_views.xml', # Popup xác nhận thao tác hàng loạt
        'views/vehicle_schedule_wizard_views.xml', # Popup đổi lịch giao/thu hồi nhanh
        'views/delivery_receipt_views.xml', # Giao diện Biên lai giao xe
        'views/delivery_receipt_wizard_views.xml', # Popup tạo & xuất Biên lai giao xe
        'views/return_receipt_views.xml', # Giao diện Biên lai thu hồi xe
        'views/return_receipt_wizard_views.xml', # Popup tạo & xuất Biên lai thu hồi xe
        'views/ticket_views.xml', # Màn hình chính Phiếu vận hành tổng
        'views/incident_views.xml', # Giao diện Nhật ký sự cố
        'views/menu_views.xml', # Cây menu chính trên thanh điều hướng
    'views/vehicle_exchange_views.xml', # Giao diện Phiếu đổi xe
    ],
    'assets': {
        'web.assets_backend': [ # Nạp file CSS tùy biến giao diện vào backend của Odoo
            'motorbike_rental_operation/static/src/css/operation.css',
        ],
    },
    'installable': True,
    'application': True, # Hiển thị như 1 ứng dụng độc lập ngoài màn hình chính Apps của Odoo
    'category': 'Quản trị',
}
