from odoo import models


class RentalOperationTicketVehicle(models.Model):
    _inherit = "rental.operation.ticket.vehicle"

    
    """Sau khi lưu thu hồi xe, gọi bên hóa đơn để tự tạo hóa đơn nháp nếu phiếu vận hành đã hoàn tất."""
    def write(self, vals):
        result = super().write(vals)
        if vals.get("status") == "returned":
            tickets = self.mapped("ticket_id").filtered(lambda ticket: ticket.state == "done")
            self.env["account.move"]._create_rental_invoice_after_return(tickets.mapped("contract_id"))
        return result
