from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_rental_customer = fields.Boolean(string='Khách thuê xe')
    rental_id_number = fields.Char(string='Số CCCD/CMND')
    rental_driver_license = fields.Char(string='Số giấy phép lái xe')
    rental_notes = fields.Text(string='Ghi chú thuê xe')
    rental_document_ids = fields.One2many(
        'rental.customer.document', 'customer_id', string='Tài liệu PDF'
    )
    rental_contract_ids = fields.One2many(
        'rental.contract', 'customer_id', string='Hợp đồng thuê xe'
    )