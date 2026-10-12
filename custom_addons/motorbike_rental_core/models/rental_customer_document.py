import base64
import binascii

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RentalCustomerDocument(models.Model):
    _name = 'rental.customer.document'
    _description = 'Tài liệu khách hàng'
    _order = 'document_date desc, id desc'

    name = fields.Char(string='Tên tài liệu', required=True)
    customer_id = fields.Many2one(
        'res.partner', string='Khách hàng', required=True, ondelete='cascade', index=True
    )
    document_date = fields.Date(
        string='Ngày lưu', required=True, default=fields.Date.context_today
    )
    file = fields.Binary(string='Tệp PDF', required=True, attachment=True)
    filename = fields.Char(string='Tên tệp', required=True)
    notes = fields.Char(string='Ghi chú')

    @api.constrains('file', 'filename')
    def _check_pdf_file(self):
        for document in self:
            if not document.file:
                continue
            if not document.filename or not document.filename.lower().endswith('.pdf'):
                raise ValidationError(_('Vui lòng chọn tệp có phần mở rộng .pdf.'))
            try:
                content = base64.b64decode(document.file)
            except (binascii.Error, TypeError, ValueError):
                raise ValidationError(_('Tệp tải lên không phải là PDF hợp lệ.')) from None
            if not content.startswith(b'%PDF-'):
                raise ValidationError(_('Tệp tải lên không phải là PDF hợp lệ.'))