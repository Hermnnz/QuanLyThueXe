# Command cung cấp lệnh tạo/liên kết/xóa quan hệ Odoo khi chuẩn bị dữ liệu kiểm thử.
from odoo import Command
# Lớp kiểm thử kế toán chuẩn cung cấp khách, tài khoản doanh thu và nhật ký thử hợp lệ.
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
# tagged gắn nhãn để có thể chỉ chạy đúng nhóm kiểm thử báo cáo này.
from odoo.tests import tagged


# post_install chạy sau khi cài xong module; -at_install bỏ thời điểm đang cài để đủ dữ liệu phụ thuộc.
@tagged('post_install', '-at_install')
# Lớp kiểm thử kế thừa bộ dữ liệu kế toán thử; dữ liệu test nằm trong transaction được rollback sau ca thử.
class TestFinanceDashboard(AccountTestInvoicingCommon):
    # classmethod cho phép phương thức chuẩn bị dùng cls, tức chính lớp kiểm thử.
    @classmethod
    # Hàm setUpClass tạo dữ liệu chung cho các ca kiểm thử báo cáo bên dưới.
    def setUpClass(cls):  # Chuẩn bị chứng từ thử để kiểm tra phép tổng hợp, không kiểm thử lại luồng ký/giao xe.
        # Gọi phần chuẩn bị của lớp cha trước để có khách, công ty, tài khoản và nhật ký thử.
        super().setUpClass()
        # Chỉ nâng quyền ở bước cấp nhóm cho tài khoản test; sudo không được thêm vào báo cáo chạy thật.
        cls.env.user.sudo().write({'groups_id': [
            # Command.link thêm nhóm quản lý thuê xe để test được tạo hợp đồng, xe và bảng giá.
            Command.link(cls.env.ref('motorbike_rental_core.group_rental_manager').id),
            # Thêm nhóm Finance để tài khoản test được đọc báo cáo và tạo chứng từ tài chính thử.
            Command.link(cls.env.ref('motorbike_rental_finance.group_motorbike_finance_user').id),
        # Kết thúc danh sách nhóm và lưu quyền của tài khoản kiểm thử.
        ]})
        # Lấy bản ghi VND chuẩn, không dùng ID tiền tệ cố định của database.
        cls.vnd = cls.env.ref('base.VND')
        # Tạo hãng xe riêng cho test để không phụ thuộc tên hoặc số lượng xe demo.
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Dashboard test'})
        # Tạo một dòng xe thuộc hãng vừa tạo; vehicle_type=bike xác định loại xe trong Fleet.
        cls.model = cls.env['fleet.vehicle.model'].create({'name': 'Dashboard bike', 'brand_id': brand.id, 'vehicle_type': 'bike'})
        # Tạo chiếc xe mẫu để nối với hợp đồng và dòng vận hành thử.
        cls.vehicle = cls.env['fleet.vehicle'].create({
            # Chọn dòng xe vừa tạo và đánh dấu đây là xe máy điện.
            'model_id': cls.model.id, 'is_electric_motorbike': True,
            # Đặt xe Sẵn sàng và đạt kỹ thuật để dữ liệu thử hợp lệ với ràng buộc Fleet.
            'operational_status': 'available', 'technical_ready': True,
        # Kết thúc tạo xe thử.
        })
        # Tạo bảng giá thuê riêng cho dòng xe thử.
        price = cls.env['rental.vehicle.type'].create({
            # Giá một ngày là 600.000đ, dùng VND, gắn đúng dòng xe mà test vừa tạo.
            'name': 'Dashboard price', 'model_id': cls.model.id, 'daily_rate': 600000, 'currency_id': cls.vnd.id,
        # Kết thúc tạo bảng giá thử.
        })
        # Tạo hợp đồng thử làm phạm vi riêng cho mọi phép tổng hợp trong các ca test.
        cls.contract = cls.env['rental.contract'].create({
            # Dùng khách partner_a do lớp cha tạo và tiền tệ VND.
            'customer_id': cls.partner_a.id, 'currency_id': cls.vnd.id,
            # Khoảng thời gian này dài đúng một ngày, giúp tiền thuê dự kiến đúng 600.000đ.
            'start_date': '2026-11-01 03:00:00', 'end_date': '2026-11-02 03:00:00',
            # Đặt tiền cọc 500.000đ; tổng hai khoản thu ban đầu cần kiểm tra là 1.100.000đ.
            'deposit_amount': 500000,
            # Command.create tạo dòng xe thuê con, gắn chiếc xe và bảng giá tương ứng.
            'line_ids': [Command.create({'vehicle_id': cls.vehicle.id, 'vehicle_type_id': price.id})],
        # Kết thúc tạo hợp đồng; Finance tự tạo hai phiếu tiền ban đầu ở trạng thái nháp.
        })
        # Giữ model báo cáo trong cls.report để các ca test truy vấn thuận tiện.
        cls.report = cls.env['rental.finance.report']

    # Hàm total cộng một chỉ tiêu của riêng hợp đồng thử; extra cho phép truyền thêm điều kiện phân loại.
    def total(self, metric, extra=None):  # Cộng chỉ số của riêng hợp đồng thử, không phụ thuộc dữ liệu demo.
        # Bỏ cache giá trị report vì các lệnh SQL thử làm nguồn VIEW đổi ngay, ngoài cơ chế ghi ORM.
        self.report.invalidate_model()  # SQL VIEW thay đổi theo nguồn; bỏ giá trị cũ trong bộ nhớ của lần đọc trước.
        # search tìm các dòng báo cáo phù hợp; sum cộng các giá trị lấy được.
        return sum(self.report.search([
            # Chỉ lấy hợp đồng thử và metric được truyền vào hàm, tránh lẫn dữ liệu có sẵn trong database.
            ('contract_id', '=', self.contract.id), ('metric', '=', metric),
        # extra or [] dùng danh sách rỗng khi không có lọc thêm; mapped lấy trường amount của các dòng tìm được.
        ] + (extra or [])).mapped('amount'))

    # Ca này kiểm tra phiếu nháp/hủy, tiền cọc và tiền thu thật được báo cáo đúng, độc lập với doanh thu hóa đơn.
    def test_confirmed_cash_and_current_deposit(self):  # Nháp không tạo dòng tiền; cọc không biến thành doanh thu.
        # assertEqual báo lỗi test nếu hai số khác nhau; phiếu cọc còn nháp phải cho tổng cọc bằng 0.
        self.assertEqual(self.total('deposit'), 0)
        # flush_all ghi các giá trị ORM đang chờ xuống database trước khi dùng SQL đọc/cập nhật.
        self.env.flush_all()
        # SQL chỉ chuẩn bị trạng thái đầu vào cho báo cáo trong transaction kiểm thử.
        # Chỉ trong test, đặt phiếu tiền sang confirmed để chuẩn bị đầu vào; %s là tham số SQL an toàn, không ghép ID vào chuỗi.
        self.env.cr.execute("UPDATE motorbike_rental_payment SET state='confirmed' WHERE contract_id=%s", [self.contract.id])
        # Đặt hợp đồng thử sang đang thuê để mô phỏng tiền cọc hiện còn giữ.
        self.env.cr.execute("UPDATE rental_contract SET state='in_progress' WHERE id=%s", [self.contract.id])
        # Tiền thực thu phải là 600.000đ thuê cộng 500.000đ cọc.
        self.assertEqual(self.total('cash_in'), 1100000)
        # Cọc đã thu phải đúng 500.000đ, không gồm tiền thuê.
        self.assertEqual(self.total('deposit'), 500000)
        # Hợp đồng đang thuê nên toàn bộ cọc 500.000đ vẫn thuộc cọc đang giữ.
        self.assertEqual(self.total('held_deposit'), 500000)
        # Chưa có hóa đơn xác nhận thì tiền đã thu không tự biến thành doanh thu hóa đơn.
        self.assertEqual(self.total('revenue'), 0)
        # Mô phỏng hợp đồng đã hoàn tất để kiểm tra cọc hiện tại được loại khỏi số đang giữ.
        self.env.cr.execute("UPDATE rental_contract SET state='done' WHERE id=%s", [self.contract.id])
        # Cọc đang giữ phải về 0 khi hợp đồng hoàn tất.
        self.assertEqual(self.total('held_deposit'), 0)
        # Lịch sử cọc đã thu vẫn là 500.000đ dù hợp đồng không còn giữ cọc.
        self.assertEqual(self.total('deposit'), 500000)
        # Mô phỏng phiếu tiền bị hủy để kiểm tra bộ lọc trạng thái nguồn.
        self.env.cr.execute("UPDATE motorbike_rental_payment SET state='cancelled' WHERE contract_id=%s", [self.contract.id])
        # Phiếu hủy không được cộng vào tổng thực thu.
        self.assertEqual(self.total('cash_in'), 0)

    # Ca này kiểm tra doanh thu nháp/đã xác nhận, phân loại thuê/bồi thường và dấu âm của hóa đơn điều chỉnh giảm.
    def test_invoice_revenue_category_and_draft(self):  # Hóa đơn nháp bị loại; tiền thuê và bồi thường tách đúng loại.
        # Tạo bảng giá bồi thường riêng để kiểm tra việc phân loại dựa trên dữ liệu thật của bảng giá.
        catalog = self.env['motorbike.rental.price.catalog'].create({
            # category=compensation là mã bồi thường mà nhánh SQL cần nhận diện.
            'name': 'Dashboard compensation', 'category': 'compensation',
            # Đơn giá thử là 200.000đ, cùng VND với hợp đồng.
            'currency_id': self.vnd.id, 'unit_price': 200000,
        # Kết thúc tạo bảng giá bồi thường.
        })
        # Tạo hóa đơn nháp để chuẩn bị đầu vào báo cáo; chưa gắn hợp đồng ở bước ORM này.
        invoice = self.env['account.move'].create({
            # out_invoice là hóa đơn khách hàng; dùng khách thử của lớp cha.
            'move_type': 'out_invoice', 'partner_id': self.partner_a.id,
            # Đặt VND và ngày hóa đơn cụ thể để kết quả test ổn định.
            'currency_id': self.vnd.id, 'invoice_date': '2026-11-02',
            # Lấy nhật ký bán hàng thử hợp lệ do bộ kiểm thử kế toán Odoo chuẩn bị.
            'journal_id': self.company_data['default_journal_sale'].id,
            # Tạo các dòng hóa đơn bằng danh sách Command.create.
            'invoice_line_ids': [Command.create({
                # Mỗi dòng có tên, số lượng 1 và giá từ tuple ở vòng lặp bên dưới.
                'name': name, 'quantity': 1, 'price_unit': amount,
                # Dòng bồi thường được gắn bảng giá; dòng tiền thuê không gắn bảng giá phí.
                'price_catalog_id': catalog_id,
                # Dùng tài khoản doanh thu thử để dòng hóa đơn hợp lệ với model kế toán.
                'account_id': self.company_data['default_account_revenue'].id,
                # Command.clear bỏ thuế khỏi dòng thử để tổng chỉ gồm đúng hai khoản 600.000đ và 200.000đ.
                'tax_ids': [Command.clear()],
            # List comprehension lặp qua hai tuple để tạo hai dòng: Thuê và Bồi thường.
            }) for name, amount, catalog_id in [('Thuê', 600000, False), ('Bồi thường', 200000, catalog.id)]],
        # Kết thúc tạo hóa đơn nháp phục vụ ca thử.
        })
        # Đẩy các thay đổi ORM xuống database trước khi chuyển sang kiểm tra báo cáo bằng SQL.
        self.env.flush_all()
        # Gắn hóa đơn với hợp đồng bằng SQL trong test để tập trung vào báo cáo, không chạy lại toàn bộ kiểm tra thu hồi.
        self.env.cr.execute('UPDATE account_move SET contract_id=%s WHERE id=%s', [self.contract.id, invoice.id])
        # Hóa đơn vẫn nháp nên tổng doanh thu phải bằng 0.
        self.assertEqual(self.total('revenue'), 0)
        # Mô phỏng hóa đơn đã xác nhận, là điều kiện nguồn để doanh thu được ghi vào VIEW.
        self.env.cr.execute("UPDATE account_move SET state='posted' WHERE id=%s", [invoice.id])
        # Tổng doanh thu phải là 600.000đ thuê cộng 200.000đ bồi thường.
        self.assertEqual(self.total('revenue'), 800000)
        # Thêm lọc category=rental để xác nhận tiền thuê được tách riêng đúng 600.000đ.
        self.assertEqual(self.total('revenue', [('category', '=', 'rental')]), 600000)
        # Thêm lọc compensation để xác nhận bồi thường được tách riêng đúng 200.000đ.
        self.assertEqual(self.total('revenue', [('category', '=', 'compensation')]), 200000)
        # Mô phỏng chứng từ điều chỉnh giảm; đây là đầu vào kiểm thử cách tính dấu của doanh thu.
        self.env.cr.execute("UPDATE account_move SET move_type='out_refund' WHERE id=%s", [invoice.id])
        # Toàn bộ 800.000đ phải đổi sang số âm để giảm doanh thu thay vì tăng doanh thu lần nữa.
        self.assertEqual(self.total('revenue'), -800000)

    # Ca này xác nhận xe gốc có lượt thuê, còn dòng mang cờ xe thay thế không làm tăng bảng xếp hạng.
    def test_replacement_does_not_increase_rental_count(self):  # Đổi A sang B không tạo lượt thuê mới trong bảng xếp hạng.
        # Ghi dữ liệu đang chờ xuống database trước khi chuẩn bị trạng thái hợp đồng thử.
        self.env.flush_all()
        # Trạng thái thử được đặt bằng SQL để không kích hoạt luồng vận hành hoặc sinh hóa đơn tự động.
        # Mô phỏng hợp đồng đang thuê bằng SQL; không chạy tác dụng phụ của các nút nghiệp vụ trong ca báo cáo này.
        self.env.cr.execute("UPDATE rental_contract SET state='in_progress' WHERE id=%s", [self.contract.id])
        # Bỏ cache state của hợp đồng để lần tạo phiếu vận hành đọc được giá trị đang thuê vừa đặt bằng SQL.
        self.contract.invalidate_recordset(['state'])
        # Tạo phiếu vận hành thử có đúng một dòng xe.
        ticket = self.env['rental.operation.ticket'].create({
            # Phiếu vận hành thuộc hợp đồng thử, không dùng hợp đồng demo.
            'contract_id': self.contract.id,
            # Tạo dòng vận hành con chứa chiếc xe thử đã chuẩn bị.
            'vehicle_detail_ids': [Command.create({'vehicle_id': self.vehicle.id})],
        # Kết thúc tạo phiếu vận hành thử.
        })
        # [:1] lấy tối đa dòng xe đầu tiên để chuẩn bị thời điểm giao và trạng thái nguồn.
        line = ticket.vehicle_detail_ids[:1]
        # Ghi dòng vận hành xuống database trước khi cập nhật các trường bằng SQL.
        self.env.flush_all()
        # Đặt dòng xe Đang thuê và có giờ giao thực tế; đây là hai điều kiện để báo cáo công nhận lượt thuê.
        self.env.cr.execute("UPDATE rental_operation_ticket_vehicle SET status='renting', actual_delivery_date='2026-11-01 03:00:00' WHERE id=%s", [line.id])
        # Xe gốc vừa giao phải được đếm đúng một lượt.
        self.assertEqual(self.total('rental_count'), 1)
        # Chuyển chính dòng thử sang cờ xe thay thế để kiểm tra điều kiện loại subfleet của VIEW.
        self.env.cr.execute('UPDATE rental_operation_ticket_vehicle SET subfleet=TRUE WHERE id=%s', [line.id])
        # Dòng xe thay thế phải đóng góp 0 lượt vào bảng xếp hạng xe thuê.
        self.assertEqual(self.total('rental_count'), 0)

    # Ca này kiểm tra Dashboard vẫn dùng bản gốc Odoo, có đúng phần mới và model báo cáo chỉ được đọc.
    def test_native_snapshot_and_readonly_report(self):  # Giữ Dashboard gốc, thêm đúng 12 thẻ và không dùng dữ liệu mẫu.
        # Tìm Dashboard hóa đơn chuẩn bằng mã XML mà phần kế thừa đang sử dụng.
        dashboard = self.env.ref('spreadsheet_dashboard_account.dashboard_invoicing')
        # Gọi hàm thật trả cấu hình Dashboard, bao gồm phần mở rộng Finance.
        result = dashboard.get_readonly_dashboard()
        # Bốn bảng xếp hạng chung không còn xuất hiện trên trang tổng quan thuê xe.
        contents = '\n'.join(cell.get('content', '') for cell in result['snapshot']['sheets'][0]['cells'].values())
        # Duyệt đủ bốn tiêu đề của mẫu gốc để kiểm tra việc loại bỏ không bị thiếu bảng.
        for title in ('Top Countries', 'Top Categories', 'Top Products', 'Top Salespeople'):
            # assertNotIn báo lỗi nếu nội dung tiêu đề cũ vẫn còn trong trang.
            self.assertNotIn(f'[{title}]', contents)
        # Gom mọi công thức, gồm sheet ẩn, để kiểm tra không còn gọi số dư kế toán cho DSO.
        formulas = '\n'.join(cell.get('content', '') for page in result['snapshot']['sheets']
                             for cell in page.get('cells', {}).values())
        # Các thẻ đã bỏ không được để lại truy vấn ODOO.BALANCE chạy ngầm.
        self.assertNotIn('ODOO.BALANCE(', formulas)
        # Kiểm tra cả nguồn pivot của bốn bảng cũ và khoản chưa đối soát đã được dọn.
        obsolete = {'Top Countries', 'Top Categories', 'Top Products', 'Top Salespeople', 'KPI - Unpaid Invoices'}
        # Tập tên các pivot còn lại chỉ được gồm các nguồn đang cần cho Dashboard.
        self.assertFalse(obsolete.intersection(source['name'] for source in result['snapshot']['pivots'].values()))
        # Không được trả bộ dữ liệu mẫu is_sample thay cho số liệu thật.
        self.assertFalse(result.get('is_sample'))
        # Lấy danh sách thành phần hiển thị của trang đầu tiên.
        figures = result['snapshot']['sheets'][0]['figures']
        # Lọc ID thẻ có tiền tố rental-kpi- rồi kiểm tra phải có đủ 12 thẻ.
        self.assertEqual(len([f for f in figures if f['id'].startswith('rental-kpi-')]), 12)
        # Lọc ID biểu đồ có tiền tố rental-chart- rồi kiểm tra phải có đủ 4 biểu đồ.
        self.assertEqual(len([f for f in figures if f['id'].startswith('rental-chart-')]), 4)
        # has_access kiểm tra quyền; tài khoản Finance không được tạo dòng báo cáo thủ công.
        self.assertFalse(self.report.has_access('create'))
        # Tài khoản Finance không được sửa trực tiếp giá trị tổng hợp.
        self.assertFalse(self.report.has_access('write'))
        # Tài khoản Finance không được xóa dòng báo cáo hoặc chứng từ nguồn qua model báo cáo.
        self.assertFalse(self.report.has_access('unlink'))
