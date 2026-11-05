# fields khai báo trường; models tạo model Odoo; tools cung cấp hàm quản lý SQL VIEW.
from odoo import fields, models, tools


# Class này đăng ký một model báo cáo; model là đối tượng Odoo dùng để đọc dữ liệu theo trường.
# Quyền của model được đăng ký ở security/ir.model.access.csv cho nhóm Finance User.
# Dòng access_rental_finance_report_user có bốn cột quyền lần lượt là 1, 0, 0, 0:
# perm_read=1 cho đọc; perm_write/create/unlink=0 không cho sửa, tạo hoặc xóa dòng báo cáo.
# CSV quyền không nhận comment XML/Python, nên phần giải thích dòng quyền được đặt tại đây.
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

    # Hàm init được Odoo gọi lúc khởi tạo/cập nhật model để dựng nguồn dữ liệu báo cáo.
    def init(self):  # Tạo lại bảng nhìn báo cáo khi cài/nâng cấp module Finance.
        # UNION ALL ghép các loại sự kiện; metric phân biệt tiền và số lượt.
        # Mỗi nhánh có khoảng ID riêng, tránh đếm trùng giữa hóa đơn và phiếu thu.
        # env.cr là kết nối thao tác database; _table là rental_finance_report. Chỉ bỏ VIEW cũ, không xóa bảng chứng từ.
        tools.drop_view_if_exists(self.env.cr, self._table)
        # execute gửi câu SQL nhiều dòng bên dưới đến PostgreSQL; ba dấu nháy mở một chuỗi nhiều dòng trong Python.
        self.env.cr.execute("""
            -- VIEW là truy vấn được đặt tên: đọc báo cáo thì database đọc chứng từ hiện có, không lưu một bản tổng tiền riêng.
            CREATE VIEW rental_finance_report AS
            -- Nhánh 1 lấy dòng hóa đơn l; cộng một khoảng số lớn vào ID để không trùng ID của các nhánh khác.
            SELECT 10000000000 + l.id AS id, m.name AS name,
                   -- AS đặt tên cột kết quả: ngày hóa đơn thành report_date, ID hợp đồng thành contract_id.
                   m.invoice_date AS report_date, c.id AS contract_id,
                   -- Giữ tiền tệ hóa đơn; NULL là trống, ::integer quy định cột dòng xe thuộc kiểu số nguyên.
                   m.currency_id, NULL::integer AS vehicle_model_id,
                   -- Lấy trạng thái hiện tại của hợp đồng để có thể nhóm/lọc báo cáo theo trạng thái.
                   c.state AS contract_state,
                   -- CASE WHEN là nếu: một dòng không gắn khoản phí và không gắn bảng giá phí được xem là tiền thuê.
                   CASE WHEN l.charge_id IS NULL AND l.price_catalog_id IS NULL
                        -- THEN/ELSE là thì/ngược lại; COALESCE lấy giá trị đầu tiên không trống, thiếu loại phí thì hiện Chưa phân loại.
                        THEN 'rental' ELSE COALESCE(pc.category, 'unclassified') END AS category,
                   -- Gắn nhãn revenue cho mọi dòng của nhánh hóa đơn; ::varchar quy định đây là chuỗi.
                   'revenue'::varchar AS metric,
                   -- price_subtotal là tiền trước thuế; hóa đơn điều chỉnh giảm out_refund nhân -1 để giảm doanh thu.
                   l.price_subtotal * CASE WHEN m.move_type = 'out_refund' THEN -1 ELSE 1 END AS amount
              -- FROM chọn bảng nguồn; l là tên ngắn của bảng dòng hóa đơn account_move_line.
              FROM account_move_line l
              -- JOIN nối mỗi dòng với hóa đơn m qua move_id để biết loại, trạng thái và ngày hóa đơn.
              JOIN account_move m ON m.id = l.move_id
              -- Chỉ nối được hóa đơn có hợp đồng thuê c; hóa đơn ngoài nghiệp vụ thuê tự bị loại khỏi nhánh này.
              JOIN rental_contract c ON c.id = m.contract_id
              -- LEFT JOIN cho phép không có khoản phí ch; dòng tiền thuê vẫn được giữ lại.
              LEFT JOIN motorbike_rental_charge ch ON ch.id = l.charge_id
              -- Nối thêm bảng giá pc để biết khoản phí thuộc dịch vụ, phụ phí hay bồi thường.
              LEFT JOIN motorbike_rental_price_catalog pc
                     -- Ưu tiên bảng giá gắn trực tiếp vào dòng hóa đơn; nếu trống thì lấy bảng giá của khoản phí liên kết.
                     ON pc.id = COALESCE(l.price_catalog_id, ch.price_catalog_id)
             -- WHERE lọc dữ liệu: chỉ hóa đơn posted (đã xác nhận), thuộc loại bán hàng hoặc điều chỉnh giảm.
             WHERE m.state = 'posted' AND m.move_type IN ('out_invoice', 'out_refund')
               -- Chỉ lấy dòng tiền thực của hóa đơn; bỏ dòng tiêu đề, ghi chú và dòng kế toán khác.
               AND l.display_type = 'product'
            -- UNION ALL nối kết quả nhánh hóa đơn với nhánh phiếu tiền; chỉ cộng chung khi Dashboard lọc cùng metric.
            UNION ALL
            -- Nhánh 2: mỗi phiếu tiền có tối đa 4 sự kiện; nhân ID với 10 rồi cộng số thứ tự sự kiện để ID không trùng.
            SELECT 20000000000 + p.id * 10 + event.n, p.name, p.payment_date,
                   -- Các cột phải giữ đúng thứ tự nhánh đầu: hợp đồng, tiền tệ, dòng xe trống, trạng thái, loại doanh thu trống.
                   c.id, p.currency_id, NULL::integer, c.state, NULL::varchar,
                   -- Tên chỉ tiêu lấy từ sự kiện; số tiền lấy nguyên giá trị phiếu tiền, không cộng cọc vào metric doanh thu.
                   event.metric, p.amount
              -- p là tên ngắn của bảng phiếu tiền riêng của dự án.
              FROM motorbike_rental_payment p
              -- Chỉ nhận phiếu tiền có liên kết tới hợp đồng thuê.
              JOIN rental_contract c ON c.id = p.contract_id
              -- LATERAL cho phép VALUES đọc phiếu p hiện tại để tạo các dòng chỉ tiêu tương ứng với phiếu đó.
              CROSS JOIN LATERAL (VALUES
                  -- Sự kiện 1: tiền vào gồm cọc, tiền thuê và khoản thu thêm; điều kiện cuối dòng quyết định có giữ sự kiện không.
                  (1, 'cash_in', p.transaction_type IN ('deposit', 'rental_payment', 'additional_payment')),
                  -- Sự kiện 2: phiếu refund được đưa vào chỉ tiêu tiền đã hoàn.
                  (2, 'cash_out', p.transaction_type = 'refund'),
                  -- Sự kiện 3: chỉ phiếu deposit được đưa vào cọc đã thu, phục vụ thống kê theo ngày thu.
                  (3, 'deposit', p.transaction_type = 'deposit'),
                  -- Sự kiện 4: chỉ giữ cọc của hợp đồng chưa done/cancelled; phản ánh cọc đang giữ hiện tại.
                  (4, 'held_deposit', p.transaction_type = 'deposit' AND c.state NOT IN ('done', 'cancelled'))
              -- Đặt tên ba cột sự kiện: n là thứ tự, metric là chỉ tiêu, include là điều kiện đúng/sai.
              ) AS event(n, metric, include)
             -- Chỉ phiếu confirmed được tính; đồng thời include phải đúng. Phiếu nháp/hủy không vào dòng tiền.
             WHERE p.state = 'confirmed' AND event.include
            -- Nối tiếp nhánh đếm lượt xe gốc đã giao, tách biệt hoàn toàn với các chỉ tiêu tiền.
            UNION ALL
            -- Nhánh 3 dùng ID nhỏ nhất trong nhóm xe của hợp đồng để có ID báo cáo ổn định.
            SELECT 30000000000 + MIN(v.id), c.name,
                   -- Lấy lần giao sớm nhất; đổi giờ UTC trong database sang giờ Việt Nam trước khi cắt lấy ngày.
                   (MIN(v.actual_delivery_date) AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Ho_Chi_Minh')::date,
                   -- Giữ hợp đồng, tiền tệ và dòng xe thật của Fleet để nhóm bảng xếp hạng.
                   c.id, c.currency_id, f.model_id, c.state, NULL::varchar,
                   -- Một nhóm hợp đồng + chiếc xe gốc được gắn rental_count và giá trị 1 lượt.
                   'rental_count', 1::numeric
              -- Đọc v là dòng xe trong phiếu vận hành, không chỉ đọc xe đã được chọn trên hợp đồng nháp.
              FROM rental_operation_ticket_vehicle v
              -- Nối dòng xe với phiếu vận hành t để tìm hợp đồng của chuyến thuê.
              JOIN rental_operation_ticket t ON t.id = v.ticket_id
              -- Nối phiếu vận hành với hợp đồng c để lấy tiền tệ và trạng thái.
              JOIN rental_contract c ON c.id = t.contract_id
              -- Nối với xe Fleet f để biết chiếc xe này thuộc dòng xe nào.
              JOIN fleet_vehicle f ON f.id = v.vehicle_id
             -- Chỉ tính xe đang thuê/đã trả và có thời điểm giao thực tế; xe chờ giao không được tính lượt.
             WHERE v.status IN ('renting', 'returned') AND v.actual_delivery_date IS NOT NULL
               -- subfleet đánh dấu xe thay thế; NOT loại những xe đó để đổi A sang B không tăng lượt thuê.
               AND NOT COALESCE(v.subfleet, FALSE)
             -- GROUP BY gom theo hợp đồng và chiếc xe, tránh nhiều dòng vận hành của cùng chiếc xe làm tăng lượt.
             GROUP BY c.id, c.name, c.currency_id, c.state, f.id, f.model_id
            -- Nối thêm nguồn đếm hợp đồng hiện tại, không lấy số hợp đồng bằng cách đếm phiếu tiền.
            UNION ALL
            -- Nhánh 4 tạo một dòng riêng cho mỗi hợp đồng, với khoảng ID riêng.
            SELECT 40000000000 + c.id, c.name,
                   -- Ngày của dòng hợp đồng là ngày bắt đầu thuê theo giờ Việt Nam.
                   (c.start_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Ho_Chi_Minh')::date,
                   -- Giữ các thông tin hợp đồng; dòng xe và loại doanh thu không áp dụng nên để trống.
                   c.id, c.currency_id, NULL::integer, c.state, NULL::varchar,
                   -- Gắn metric đếm hợp đồng; 1::numeric nghĩa là số 1 ở kiểu số dùng cho phép cộng.
                   'contract_count', 1::numeric
              -- Lấy toàn bộ hợp đồng, gồm cả nháp/hủy; biểu đồ sẽ tách theo từng trạng thái.
              FROM rental_contract c
            -- Nối nguồn phí còn cần xử lý để Manager biết còn khoản nào chưa duyệt/chưa quyết toán.
            UNION ALL
            -- Nhánh 5 dùng ID khoản phí và ngày ghi nhận khoản phí; tên là tên khoản phát sinh.
            SELECT 50000000000 + ch.id, ch.name, ch.charge_date,
                   -- Giữ đúng hợp đồng, tiền tệ, trạng thái; không gán dòng xe cho một khoản phí chung.
                   c.id, ch.currency_id, NULL::integer, c.state,
                   -- Đọc loại phí từ bảng giá; thiếu bảng giá thì ghi Chưa phân loại.
                   COALESCE(pc.category, 'unclassified'),
                   -- Phí draft đưa vào pending_fee; nhánh confirmed chưa quyết toán đưa vào uninvoiced_fee.
                   CASE WHEN ch.state = 'draft' THEN 'pending_fee' ELSE 'uninvoiced_fee' END,
                   -- Dùng thành tiền quantity nhân unit_price đã được model khoản phí tính sẵn.
                   ch.amount
              -- ch là bảng các khoản phát sinh của Finance.
              FROM motorbike_rental_charge ch
              -- Chỉ đọc khoản phí có liên kết hợp đồng.
              JOIN rental_contract c ON c.id = ch.contract_id
              -- LEFT JOIN giữ được khoản phí ngay cả khi chưa chọn bảng giá.
              LEFT JOIN motorbike_rental_price_catalog pc ON pc.id = ch.price_catalog_id
              -- Nối hóa đơn nếu đã có, để phân biệt phí đã quyết toán với phí chỉ mới nằm trên hóa đơn nháp.
              LEFT JOIN account_move m ON m.id = ch.invoice_id
             -- Bỏ hợp đồng đã hủy và khoản phí không có tiền phải xử lý.
             WHERE c.state != 'cancelled' AND ch.amount > 0
               -- Giữ phí nháp hoặc phí confirmed chưa có hóa đơn posted; không cộng lại phí đã quyết toán.
               AND (ch.state = 'draft' OR (ch.state = 'confirmed' AND COALESCE(m.state, '') != 'posted'))
        -- Đóng chuỗi SQL và thực thi việc tạo VIEW. Không thay đổi tiền hoặc trạng thái chứng từ nguồn.
        """)
