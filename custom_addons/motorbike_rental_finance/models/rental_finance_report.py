# fields khai báo trường; models tạo model Odoo; tools cung cấp hàm quản lý SQL VIEW.
from odoo import fields, models, tools



"""
Class khai báo “cái khung”: dữ liệu có những trường nào, kiểu gì.
Hàm init() tạo SQL VIEW, quy định lấy dữ liệu từ đâu và ghép như thế nào.
Khi mở báo cáo, Odoo truy vấn VIEW rồi trả dữ liệu theo các trường của class.
"""
class RentalFinanceReport(models.Model):
    """Nguồn chỉ đọc cho các biểu đồ nghiệp vụ trong Dashboard gốc của Odoo."""

    # Tên kỹ thuật để Dashboard và quyền truy cập tìm đúng nguồn báo cáo này.
    _name = 'rental.finance.report'
    # Tên dễ đọc khi Odoo hiển thị thông tin về model.
    _description = 'Số liệu tổng quan nghiệp vụ thuê xe'
    # False ngăn Odoo tạo bảng lưu riêng; báo cáo đọc trực tiếp dữ liệu qua câu SQL ở dưới.
    _auto = False  # Đọc từ SQL VIEW; không tạo thêm phiếu tiền hoặc hóa đơn.
    # desc là giảm dần: hiện ngày mới nhất trước; cùng ngày thì hiện ID lớn hơn trước.
    _order = 'report_date desc, id desc'

    # Char là chuỗi ký tự; readonly=True nghĩa là chỉ đọc mã/tên chứng từ nguồn.
    name = fields.Char(string='Chứng từ', readonly=True)
    # Date chỉ lưu ngày để bộ lọc kỳ trên Dashboard biết phải lấy sự kiện nào.
    report_date = fields.Date(string='Ngày ghi nhận', readonly=True)
    # Many2one là liên kết tới một hợp đồng; báo cáo không nhân bản nội dung hợp đồng.
    contract_id = fields.Many2one('rental.contract', string='Hợp đồng', readonly=True)
    # Liên kết đồng tiền gốc; Dashboard lọc VND trước khi cộng, tránh cộng lẫn các đồng tiền.
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', readonly=True)
    # Liên kết dòng xe Fleet để nhóm lượt thuê theo Quantum, Evo200...; dòng tiền có thể để trống trường này.
    vehicle_model_id = fields.Many2one('fleet.vehicle.model', string='Dòng xe', readonly=True)
    # Selection là tập lựa chọn cố định: bên trái là mã lưu, bên phải là chữ người dùng đọc.
    contract_state = fields.Selection([
        # Hai trạng thái đầu: hợp đồng còn nháp hoặc đã ký/xác nhận.
        ('draft', 'Nháp'), ('confirmed', 'Đã xác nhận'),
        # Ba trạng thái còn lại: đang thuê, đã hoàn tất và đã hủy.
        ('in_progress', 'Đang thuê'), ('done', 'Hoàn tất'), ('cancelled', 'Đã hủy'),
    # Kết thúc danh sách trạng thái; chỉ hiển thị giá trị lấy từ hợp đồng.
    ], string='Trạng thái hợp đồng', readonly=True)
    # Trường phân loại doanh thu để biểu đồ tách tiền thuê, phí và bồi thường.
    category = fields.Selection([
        # rental là tiền thuê; service là dịch vụ; surcharge là phụ phí.
        ('rental', 'Tiền thuê'), ('service', 'Dịch vụ'), ('surcharge', 'Phụ phí'),
        # compensation là bồi thường; thiếu bảng giá thì dùng unclassified để không tự đoán loại phí.
        ('compensation', 'Bồi thường'), ('unclassified', 'Chưa phân loại'),
    # Kết thúc lựa chọn loại doanh thu và đặt nhãn tiếng Việt cho trường.
    ], string='Loại doanh thu', readonly=True)
    # metric là tên chỉ tiêu: mỗi dòng báo cáo chỉ thuộc một chỉ tiêu cụ thể.
    metric = fields.Selection([
        # revenue lấy từ hóa đơn đã xác nhận; deposit lấy từ phiếu thu cọc đã xác nhận.
        ('revenue', 'Doanh thu hóa đơn'), ('deposit', 'Cọc đã thu'),
        # held_deposit là cọc của hợp đồng chưa kết thúc; cash_in là tổng phiếu tiền thu vào.
        ('held_deposit', 'Cọc đang giữ'), ('cash_in', 'Tiền thực thu'),
        # cash_out là tiền hoàn ra; rental_count là lượt xe gốc đã giao thực tế.
        ('cash_out', 'Tiền đã hoàn'), ('rental_count', 'Lượt xe đã giao'),
        # contract_count dùng đếm hợp đồng; pending_fee dùng cộng phí còn nháp.
        ('contract_count', 'Số hợp đồng'), ('pending_fee', 'Phí chờ xác nhận'),
        # uninvoiced_fee dùng cộng phí đã duyệt nhưng chưa có hóa đơn đã xác nhận.
        ('uninvoiced_fee', 'Phí đã duyệt chưa quyết toán'),
    # Kết thúc lựa chọn chỉ tiêu; không cho người dùng sửa mã chỉ tiêu trên báo cáo.
    ], string='Chỉ tiêu', readonly=True)
    # Float là số; aggregator=sum bảo pivot cộng trường này. Với chỉ tiêu đếm, mỗi dòng có giá trị 1.
    amount = fields.Float(string='Giá trị', readonly=True, aggregator='sum')
    
    
    
    
    
    """
    tạo lại SQL VIEW cung cấp dữ liệu cho Dashboard tài chính khi Odoo khởi tạo model.

    Nó gom doanh thu hóa đơn, tiền thu/hoàn/cọc, lượt xe đã giao, 
    số hợp đồng và phí chờ xử lý vào một nguồn báo cáo chung.
    Chỉ đọc dữ liệu để thống kê, không sửa chứng từ gốc.
    """
    
    
    # Hàm init được Odoo gọi lúc khởi tạo/cập nhật model để dựng nguồn dữ liệu báo cáo.
    def init(self):  # Tạo lại bảng nhìn báo cáo khi cài/nâng cấp module Finance.
        # UNION ALL ghép các loại sự kiện; metric phân biệt tiền và số lượt.
        # Mỗi nhánh có khoảng ID riêng, tránh đếm trùng giữa hóa đơn và phiếu thu.
        # env.cr là kết nối thao tác database; _table là rental_finance_report. Chỉ bỏ VIEW cũ, không xóa bảng chứng từ.
        tools.drop_view_if_exists(self.env.cr, self._table)
        # execute gửi câu SQL nhiều dòng bên dưới đến PostgreSQL; ba dấu nháy mở một chuỗi nhiều dòng trong Python.
        self.env.cr.execute("""
            CREATE VIEW rental_finance_report AS
            SELECT 10000000000 + l.id AS id, m.name AS name,
                   m.invoice_date AS report_date, c.id AS contract_id,
                   m.currency_id, NULL::integer AS vehicle_model_id,
                   c.state AS contract_state,
                   CASE WHEN l.charge_id IS NULL AND l.price_catalog_id IS NULL
                        THEN 'rental' ELSE COALESCE(pc.category, 'unclassified') END AS category,
                   'revenue'::varchar AS metric,
                   l.price_subtotal * CASE WHEN m.move_type = 'out_refund' THEN -1 ELSE 1 END AS amount
              FROM account_move_line l
              JOIN account_move m ON m.id = l.move_id
              JOIN rental_contract c ON c.id = m.contract_id
              LEFT JOIN motorbike_rental_charge ch ON ch.id = l.charge_id
              LEFT JOIN motorbike_rental_price_catalog pc
                     ON pc.id = COALESCE(l.price_catalog_id, ch.price_catalog_id)
             WHERE m.state = 'posted' AND m.move_type IN ('out_invoice', 'out_refund')
               AND l.display_type = 'product'
            UNION ALL
            SELECT 20000000000 + p.id * 10 + event.n, p.name, p.payment_date,
                   c.id, p.currency_id, NULL::integer, c.state, NULL::varchar,
                   event.metric, p.amount
              FROM motorbike_rental_payment p
              JOIN rental_contract c ON c.id = p.contract_id
              CROSS JOIN LATERAL (VALUES
                  (1, 'cash_in', p.transaction_type IN ('deposit', 'rental_payment', 'additional_payment')),
                  (2, 'cash_out', p.transaction_type = 'refund'),
                  (3, 'deposit', p.transaction_type = 'deposit'),
                  (4, 'held_deposit', p.transaction_type = 'deposit' AND c.state NOT IN ('done', 'cancelled'))
              ) AS event(n, metric, include)
             WHERE p.state = 'confirmed' AND event.include
            UNION ALL
            SELECT 30000000000 + MIN(v.id), c.name,
                   (MIN(v.actual_delivery_date) AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Ho_Chi_Minh')::date,
                   c.id, c.currency_id, f.model_id, c.state, NULL::varchar,
                   'rental_count', 1::numeric
              FROM rental_operation_ticket_vehicle v
              JOIN rental_operation_ticket t ON t.id = v.ticket_id
              JOIN rental_contract c ON c.id = t.contract_id
              JOIN fleet_vehicle f ON f.id = v.vehicle_id
             WHERE v.status IN ('renting', 'returned') AND v.actual_delivery_date IS NOT NULL
               AND NOT COALESCE(v.subfleet, FALSE)
             GROUP BY c.id, c.name, c.currency_id, c.state, f.id, f.model_id
            UNION ALL
            SELECT 40000000000 + c.id, c.name,
                   (c.start_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Ho_Chi_Minh')::date,
                   c.id, c.currency_id, NULL::integer, c.state, NULL::varchar,
                   'contract_count', 1::numeric
              FROM rental_contract c
            UNION ALL
            SELECT 50000000000 + ch.id, ch.name, ch.charge_date,
                   c.id, ch.currency_id, NULL::integer, c.state,
                   COALESCE(pc.category, 'unclassified'),
                   CASE WHEN ch.state = 'draft' THEN 'pending_fee' ELSE 'uninvoiced_fee' END,
                   ch.amount
              FROM motorbike_rental_charge ch
              JOIN rental_contract c ON c.id = ch.contract_id
              LEFT JOIN motorbike_rental_price_catalog pc ON pc.id = ch.price_catalog_id
              LEFT JOIN account_move m ON m.id = ch.invoice_id
             WHERE c.state != 'cancelled' AND ch.amount > 0
               AND (ch.state = 'draft' OR (ch.state = 'confirmed' AND COALESCE(m.state, '') != 'posted'))
        """)
