from odoo import fields, models 

# Lấy 2 thứ từ odoo 
# models → dùng để tạo Model
# fields → dùng để tạo các trường dữ liệu



class MotorbikeRentalPriceCatalog(models.Model):        #Tạo class mới (model mới) kế thừa từ hệ thống model của odoo 
    _name = "motorbike.rental.price.catalog"             #tên(model) trong hệ thống odoo, sinh bảng tương ứng
    _description = "Motorbike Rental Price Catalog"      #Mô tả  (model) trong hệ thống odoo

    name = fields.Char(   #Thuộc tính của đối tượng
        string="Tên khoản giá",
        required=True,
    )

    code = fields.Char(
        string="Mã bảng giá",
        required=True,
    )

    category=fields.Selection(
        string="Loại bảng giá",
        selection=[("service", "Dịch vụ"), ("surcharge", "Phụ phí"), ("compensation", "Bồi thường")],
        required=True,
    )
    
    currency_id = fields.Many2one(
        "res.currency",                 # Liên kết đến model cso sẵn trong odoo, Nhiều dòng bảng giá có thể sử dụng cùng một loại tiền tệ
        string="Loại tiền",
        required=True,
        default=lambda self: self.env.company.currency_id,  # Mặc định lấy loại tiền của công ty hiện tại
    )
    
    unit_price=fields.Monetary(
        string="Đơn giá",
        required=True,
        currency_field="currency_id"
    )
    
    unit=fields.Selection(
        string="Đơn vị",
        selection=[("time", "Lần"), ("hour", "Giờ"),("day", "Ngày"),("item", "Cái"),("set", "Bộ") ],
        required=True,
    )   
    
    effective_from=fields.Date(
        string="Ngày bắt đầu áp dụng",
        required=False,
    )
    
    effective_to=fields.Date(
        string="Ngày kết thúc áp dụng", 
    )
    
    active = fields.Boolean(
        string="Trạng thái",
        default=True,
    )
    
    note=fields.Text(
        string="Ghi chú",
    )
    