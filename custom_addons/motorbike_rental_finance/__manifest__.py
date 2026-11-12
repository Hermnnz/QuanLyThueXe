{
    "name": "Motorbike Rental Finance",

    "version": "1.0.0",

    "summary": "Finance management for motorbike rental",

    "author": "Nguyen Duc Anh",

    "category": "Services/Rental",

    "depends": [
        "base",
        "account",        
        "spreadsheet_dashboard_account",  # Kế thừa đúng Dashboard hóa đơn chuẩn Odoo.
        "motorbike_rental_operation",   # Thêm module Vận hành của Giang
    ],

    "data": [
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "views/rental_payment_views.xml",
        "views/rental_charge_views.xml",
        "views/rental_contract_views.xml",   
        "views/account_move_views.xml",
        "views/account_move_off.xml",  # Hạn chế giao diện kế toán gốc; nạp sau form hóa đơn Finance.
        "views/finance_actions.xml",
        "views/rental_finance_report_views.xml",  # Các màn hình chi tiết khi xem số liệu từ Dashboard.
        "data/rental_finance_dashboard.xml",  # Nạp trực tiếp bố cục Dashboard đã bỏ phần thừa, dùng trình hiển thị chuẩn Odoo.
        "views/finance_menu.xml",
        # Bộ cấp số cho các phiếu thanh toán.
        "data/rental_payment_sequence.xml",
    ],

    # Nạp kiểu chữ và viền ô tích cho hợp đồng, đồng thời làm nổi bật ô xác nhận hoàn tiền trên hóa đơn.
    "assets": {
        "web.assets_backend": [
            "motorbike_rental_finance/static/src/scss/rental_contract_payment.scss",
        ],
    },

    "installable": True,

    "application": True,

    "license": "LGPL-3",
}

