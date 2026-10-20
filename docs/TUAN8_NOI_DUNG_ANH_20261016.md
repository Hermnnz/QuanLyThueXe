# Nội dung ảnh trong tài liệu tuần 8

Ngày chuyển thành văn bản: 16/10/2026.

Đây là bản chuyển nội dung 13 ảnh sang văn bản để đọc, tìm kiếm và đối chiếu nghiệp vụ. Các đoạn giải thích được diễn đạt lại; tên trường, giá trị, công thức và ví dụ được giữ theo ảnh. Đây không phải kết quả xác nhận mã nguồn đã thực hiện các yêu cầu.

Bản chữ có sẵn trong ba file Word và vị trí ảnh trong luồng tài liệu được lưu ở [TUAN8_VAN_BAN_GOC_20261016.md](TUAN8_VAN_BAN_GOC_20261016.md). Hai file cần được đọc cùng nhau. Nhãn `imageN.png` là tên ảnh bên trong DOCX, không phải số thứ tự xuất hiện. Số thứ tự bên dưới đã đối chiếu với XML của tài liệu.

## 1. Thực trạng

Nguồn: `D:\Document\Hoc\nam4ki1\TH ERP\Tuan8\thực trạng.docx`.

### Ảnh 1 — image1.png — Trùng lặp loại xe và quản lý tiền

- Contract có `rental_vehicle_type.brand` và `rental_vehicle_type.model` dạng text; Fleet đã có `fleet_vehicle_model_brand` và `fleet_vehicle_model`. Nhận xét trong ảnh: nhập lại hãng/dòng bằng text gây dư thừa; `rental_vehicle_type` thực chất đóng vai trò nhóm giá thuê theo hạng xe với `daily_rate`.
- Operations lưu các trường `total_rent_amount`, `is_rent_paid`, `total_incurred_cost`, `paid_incurred_cost`, `remaining_cost`, `is_incurred_cost_paid` trên `rental_operation_ticket`.
- Dòng xe vận hành lưu `delivery_fee`, `is_delivery_fee_paid`, `return_fee`, `is_return_fee_paid`.
- Sự cố lưu `cost`, `is_paid` trên `rental_operation_incident_log`.
- Finance có `motorbike_rental_charge` để ghi phí phát sinh/bồi thường và `motorbike_rental_payment` để ghi thực thu/chi, cọc, hoàn tiền.
- Nhận xét trong ảnh: Operations ghi nhận sự kiện giao nhận và hỏng hóc; Finance chịu trách nhiệm tính tiền, hóa đơn và thu/hoàn tiền. Các cờ thanh toán rời rạc ở Operations đang chồng chéo với Finance.

### Ảnh 2 — image3.png — Tham chiếu bằng chuỗi

- `rental_operation_ticket.rental_order_ref` lưu mã text thay vì khóa ngoại tới hợp đồng.
- `rental_operation_ticket_vehicle.vehicle_ref`, `rental_operation_incident_log.vehicle_ref`, `rental_operation_vehicle_replacement.old_vehicle_ref/new_vehicle_ref` lưu text thay vì liên kết tới `fleet_vehicle.id`.

### Ảnh 3 — image4.png — Luồng liên module từ 1 đến 4

1. Contract ↔ Fleet: `rental_contract_line.vehicle_id` → `fleet_vehicle.id`; mỗi dòng hợp đồng gắn một xe cụ thể khi chốt hoặc xếp xe.
2. Dùng chung `res_partner` cho tài liệu khách hàng, hợp đồng, khoản phí và thanh toán.
3. Dùng chung `res_currency` cho Contract, dòng hợp đồng, loại xe, bảng giá, khoản phí và thanh toán.
4. Operations ↔ Contract: thiết kế hiện trạng dùng `rental_operation_ticket.rental_order_ref` → `rental_contract.name` để gắn phiếu giao nhận/vận hành với hợp đồng.

### Ảnh 4 — image2.png — Luồng liên module từ 5 đến 6

- Giao nhận xe: `rental_operation_ticket_vehicle.vehicle_ref` → `fleet_vehicle.vehicle_code`.
- Sự cố trên đường: `rental_operation_incident_log.vehicle_ref` → `fleet_vehicle.vehicle_code`.
- Đổi xe: `rental_operation_vehicle_replacement.old_vehicle_ref/new_vehicle_ref` → `fleet_vehicle.vehicle_code`.
- Tiền cọc và tiền thuê của `rental_contract` được thu qua `motorbike_rental_payment`.
- Phí giao/nhận và phí sự cố được ánh xạ sang `motorbike_rental_charge`, đơn giá đối chiếu từ `motorbike_rental_price_catalog`.

Các liên kết bằng text ở mục này mô tả hiện trạng; tài liệu “giải quyết” đề xuất đổi sang khóa ngoại ID.

## 2. Giải quyết

Nguồn: `D:\Document\Hoc\nam4ki1\TH ERP\Tuan8\giải quyết.docx`.

### Ảnh 1 — image1.png — Ba hướng chuẩn hóa

1. Chuẩn hóa khóa ngoại:
   - `rental_operation_ticket.rental_order_ref` → `contract_id integer`, trỏ tới `rental_contract.id`.
   - `vehicle_ref`, `old_vehicle_ref`, `new_vehicle_ref` → `vehicle_id`, `old_vehicle_id`, `new_vehicle_id integer`, trỏ tới `fleet_vehicle.id`.
2. Bỏ trùng lặp loại xe:
   - Bỏ cột text `brand`, `model` của `rental_vehicle_type`.
   - Thay bằng `model_id integer` → `fleet_vehicle_model.id`; mẫu xe đã có hãng qua `brand_id`.
3. Kết nối tiền với nghiệp vụ:
   - Thêm `contract_id` vào `motorbike_rental_payment`.
   - Thêm `contract_id`, `ticket_id` vào `motorbike_rental_charge`.
   - Các cờ `is_paid`, `is_rent_paid`… ở Operations được tính từ Finance thay vì nhập tay.

Phần DBML đầy đủ của tài liệu nằm trong bản văn bản gốc đi kèm.

## 3. Giải quyết bổ sung

Nguồn: `D:\Document\Hoc\nam4ki1\TH ERP\Tuan8\giải quyết bổ sung.docx`.

### Ảnh 1 — image4.png — Đánh giá chín vấn đề

| Vấn đề trong ảnh | Đánh giá trong ảnh | Nội dung giải pháp |
| --- | --- | --- |
| Thiếu ODO và pin | Đúng 70%, cần làm gọn | Cần phần trăm pin lúc giao/trả, nhất là nếu phạt khi pin trả dưới 20%. Không cần mở rộng sang dung lượng kWh, lịch sử sạc, SOC/SOH. |
| Hợp đồng dùng Date nhưng phạt theo giờ | Đúng 100%, bắt buộc sửa | Đổi `rental_contract.start_date/end_date` sang Datetime hoặc timestamp. |
| Charge thiếu `incident_id` | Đúng 100%, quan trọng cho Finance | Thêm Many2one từ `motorbike_rental_charge` tới `rental_operation_incident_log` để truy vết từng sự cố. |
| Kiểu tiền Float và numeric/decimal khác nhau | Đúng 100% | Dùng `fields.Monetary` hoặc `digits=(16, 2)`; ảnh minh họa sai số `50000.00000001`. |
| Đổi xe chưa cập nhật hợp đồng | Đúng về nghiệp vụ, là lỗi code | Khi xác nhận đổi xe, cập nhật `vehicle_id` ở dòng hợp đồng/dòng ticket; không cần bảng mới chỉ để giải quyết việc này. |
| Thiếu checklist phụ kiện | Không cần thiết cho phạm vi đề xuất | Dùng `notes` hoặc checkbox `has_charger` trên biên bản giao nhận. |
| Hợp đồng nhiều xe, phiếu vận hành | Nên đơn giản hóa | Quy ước một hợp đồng giao và trả cùng lúc, hoặc một hợp đồng cho một xe; tránh xử lý trả từng phần trong giai đoạn này. |
| Bấm tạo phụ phí nhiều lần | Nhận xét chính xác | Thêm `is_charge_created` hoặc `charge_id` vào sự cố; khi tạo Charge thì ẩn/vô hiệu hóa nút. |
| Chưa khép kín quyết toán | Đúng 100% | Cần kịch bản cấn trừ cọc khi trả xe; tiền cọc ở Contract, phụ phí ở Charge, thực thu ở Payment. |

### Ảnh 2 — image1.png — Sơ đồ toàn bộ luồng

Các bên: khách hàng; Hợp đồng (Nhân); Đội xe (Bắc); Vận hành (Giang); Tài chính (Đức Anh).

1. Khách ký hợp đồng thuê xe máy điện.
2. Contract gửi Finance tạo Payment thu cọc (`deposit`).
3. Contract khóa lịch xe/giữ chỗ với Fleet.
4. Giao xe: Operations kiểm tra `technical_ready`, `rental_blocked` với Fleet; ghi ODO và pin lúc giao (`ODO_start`, `Pin_start` trong sơ đồ).
5. Nếu có sự cố trên đường: lập Incident, ví dụ vỡ gương/hỏng đèn; chuyển Finance tạo Charge bồi thường theo Price Catalog.
6. Trả xe: ghi pin cuối (`Pin_end`), ví dụ dưới 20% tạo phí sạc pin; ghi giờ trả so với Datetime hợp đồng để tạo phí trễ giờ.
7. Finance quyết toán: tổng phải thu = tiền thuê + các Charge; khoản đã thu minh họa là tiền cọc; bù trừ để hoàn cọc (`Refund`) hoặc thu thêm (`Additional`).

Lưu ý đối chiếu: sơ đồ này chưa thể hiện rõ khoản tiền thuê đã thu; ảnh 5 bên dưới mô tả thu cả tiền thuê gốc và tiền cọc khi nhận xe.

### Ảnh 3 — image7.png — Quy tắc dòng tiền

- Khi ký hợp đồng: tạo `motorbike_rental_payment` với `transaction_type='deposit'`, số tiền bằng `rental_contract.deposit_amount`.
- Khi phát sinh phí: tạo `motorbike_rental_charge`.
  - Trễ giờ: đơn giá từ Price Catalog, mã `LATE_FEE`.
  - Pin dưới 20%: mã `BATTERY_CHARGE`.
  - Hỏng hóc: mã `COMPENSATION`, lưu `incident_id`.
- Quyết toán: `số tiền chênh lệch = tiền cọc - tổng phụ phí phát sinh`.
  - Nếu số dư > 0: tạo Payment loại `refund`, hoàn cọc thừa; hợp đồng `state='done'`.
  - Nếu số dư < 0: tạo Payment loại `additional_payment`, thu thêm; thu xong mới đóng hợp đồng.
- Ảnh không nêu riêng nhánh số dư = 0.

### Ảnh 4 — image2.png — Trường tối thiểu cần cập nhật

- Contract (Nhân): đổi `rental_contract.start_date/end_date` sang Datetime.
- Operations (Giang):
  - Thêm `battery_start`, `battery_end` (Float) vào `rental_operation_ticket_vehicle` để ghi % pin giao/trả.
  - Thêm `odometer_start`, `odometer_end` (numeric).
  - Thêm `rental_operation_incident_log.is_charge_created` (Boolean, mặc định False) để chống sinh phụ phí trùng.
  - Chuẩn hóa `delivery_fee`, `return_fee`, `cost` từ Float sang Monetary.
- Finance (Đức Anh): thêm `motorbike_rental_charge.incident_id` (Many2one tới `rental_operation_incident_log`); giữ Price Catalog để lấy giá phạt sạc pin, trễ giờ và bồi thường.

### Ảnh 5 — image5.png — Thu tiền thuê và quyết toán cọc

Quy tắc trong ảnh: khách đóng tiền thuê gốc và cọc khi nhận xe; khi trả chỉ quyết toán cọc với phụ phí.

Khi giao xe:

- Tiền thuê gốc `total_amount` → Payment `transaction_type='rental_payment'`.
- Tiền cọc `deposit_amount` → Payment `transaction_type='deposit'`.
- Xe xuất bãi, trạng thái `renting`.

Khi trả xe:

- Tổng Charge = trễ giờ + sạc pin + sự cố hỏng hóc.
- Nếu phụ phí ≤ cọc: cấn trừ cọc, tiền hoàn = cọc - phụ phí; ảnh dùng Payment `type='refund'`.
- Nếu phụ phí > cọc: giữ toàn bộ cọc, thu thêm = phụ phí - cọc; ảnh dùng Payment `type='additional_payment'`.

| Ví dụ trong ảnh | Tiền cọc | Tiền thuê gốc đã đóng | Phụ phí | Quyết toán | Kết quả |
| --- | ---: | ---: | ---: | --- | --- |
| Trả xe chuẩn | 2.000.000đ | 600.000đ | 0đ | Hoàn 2.000.000đ | Done |
| Trễ giờ và thiếu pin | 2.000.000đ | 600.000đ | 250.000đ | Hoàn 1.750.000đ | Done |
| Đâm va vỡ yếm | 2.000.000đ | 600.000đ | 3.500.000đ | Giữ cọc, thu thêm 1.500.000đ | Thu xong → Done |

### Ảnh 6 — image8.png — ODO giữa Fleet và Operations

Ảnh đề xuất Fleet có trường số km hiện tại:

```python
odometer = fields.Float(
    string="Số ODO hiện tại (km)",
    default=0.0,
    help="Tổng số km xe đã chạy, tự động cập nhật sau mỗi chuyến thuê."
)
```

Operations có:

```python
odometer_start = fields.Float(string="ODO lúc giao xe (km)")
odometer_end = fields.Float(string="ODO lúc trả xe (km)")

@api.constrains('odometer_start', 'odometer_end')
def _check_odometer(self):
    for rec in self:
        if rec.odometer_start < rec.vehicle_id.odometer:
            raise ValidationError(
                f"ODO giao xe ({rec.odometer_start} km) không được nhỏ hơn "
                f"ODO hiện tại của xe ({rec.vehicle_id.odometer} km)!"
            )
        if rec.odometer_end and rec.odometer_end < rec.odometer_start:
            raise ValidationError("ODO lúc trả xe không được nhỏ hơn ODO lúc giao xe!")
```

Ảnh minh họa cập nhật khi xác nhận trả xe:

```python
def action_return_vehicle(self):
    """Khi hoàn tất nhận lại xe, cập nhật ODO mới nhất sang đội xe của Bắc"""
    for rec in self:
        if rec.odometer_end:
            rec.vehicle_id.write({
                'odometer': rec.odometer_end,
                'operational_status': 'available',
            })
```

Các đoạn code trên chép lại nội dung minh họa của ảnh, có xuống dòng lại cho dễ đọc. Chưa phải bản vá được kiểm chứng, cũng chưa xác nhận cần khai báo lại trường ODO đã có trong Odoo hay không.

### Ảnh 7 — image3.png — Làm tròn phạt trễ giờ

Quy tắc: miễn phí 15 phút đầu; nếu trễ quá 15 phút thì làm tròn lên theo giờ bằng `math.ceil`.

Các ví dụ dùng **toàn bộ số phút trễ** khi đã vượt ngưỡng, không trừ 15 phút trước khi làm tròn:

```text
Nếu phút_trễ <= 15: giờ_phạt = 0
Nếu phút_trễ > 15:  giờ_phạt = ceil(phút_trễ / 60)
```

| Hẹn trả | Thực trả | Số phút trễ | Giờ phạt | Phí ví dụ 50.000đ/giờ |
| --- | --- | ---: | ---: | ---: |
| 10:00 | 10:10 | 10 | 0 | 0đ |
| 10:00 | 10:15 | 15 | 0 | 0đ |
| 10:00 | 10:16 | 16 | 1 | 50.000đ |
| 10:00 | 11:00 | 60 | 1 | 50.000đ |
| 10:00 | 11:05 | 65 | 2 | 100.000đ |

### Ảnh 8 — image6.png — Phân công cập nhật

**Bắc — Fleet & Maintenance**

- Ảnh yêu cầu thêm `odometer = fields.Float(string="Số ODO hiện tại", default=0.0)` trên `fleet_vehicle`.
- Chuẩn trạng thái `operational_status`: `available`, `renting`, `maintenance`, `pending_inspection`.
- Chuẩn hóa khóa xe `rental_blocked` (Boolean).

**Nhân — Customer & Rental Core**

- Đổi ngày bắt đầu/kết thúc hợp đồng từ Date sang Datetime.
- Thêm `_sql_constraints` cho cặp `(contract_id, vehicle_id)` trên `rental_contract_line` để chống trùng xe trong cùng hợp đồng.
- Gán giá cố định (snapshot) từ bảng giá sang dòng hợp đồng khi chọn loại xe.

**Giang — Rental Operations**

- Thêm `actual_return_date = fields.Datetime(string="Giờ trả thực tế")` trên header `rental_operation_ticket`.
- Thêm `odometer_start`, `odometer_end` (Float), `battery_start`, `battery_end` (Float) trên dòng xe.
- Thêm `is_charge_created = fields.Boolean(default=False)` trên sự cố để chống nhân đôi phụ phí.
- Viết hàm trả xe cập nhật ODO và kiểm tra lỗi/pin yếu trước khi chuyển trạng thái xe sang Fleet.

**Đức Anh — Finance & Accounting**

- Thêm `motorbike_rental_charge.incident_id = fields.Many2one('rental_operation_incident_log')`.
- Thêm `amount_total = fields.Monetary(compute='_compute_amount_total', store=True)` trên Charge.
- Cấu hình Price Catalog: `LATE_HOUR` (phạt trễ 50.000đ/giờ), `BATTERY_CHARGE`, `COMPENSATION`.
- Viết `action_settlement` tính tiền hoàn cọc/thu thêm từ tiền cọc trừ tổng phụ phí.

### Phần chữ ngoài ảnh của tài liệu bổ sung

Tài liệu nhắc Giang cập nhật trạng thái xe khi `action_deliver_vehicle` bàn giao xuất bãi, nếu thiếu thì khách đã lấy xe nhưng Kanban của Bắc vẫn hiện `available`. Giá trị trạng thái sau giao thể hiện ở ảnh 5 là `renting`. Toàn bộ phần chữ ngoài ảnh được giữ trong bản văn bản gốc đi kèm.

## 4. Ghi chú đối chiếu của người chuyển bản

Phần này là nhận xét của Codex khi đối chiếu tài liệu, không phải nguyên văn hay quyết định của nhóm trưởng.

| Điểm cần xác nhận | Bằng chứng và giới hạn |
| --- | --- |
| Trạng thái sau trả xe | Ảnh bổ sung `image8.png` ghi thẳng `available`; file `D:\Document\Hoc\HeNam3\Video\nghiệp vụdocx.docx` đã đọc trước đó mô tả quy trình Giang trả về Chờ kiểm tra, Fleet kiểm tra rồi xác nhận sẵn sàng. Cần xác định quy trình nhóm chốt. |
| Trường ODO của Fleet | Ảnh đề xuất thêm Float; tài liệu nghiệp vụ trước đó mô tả dùng ODO chuẩn Odoo. Cần kiểm tra trường kế thừa hiện có trước khi sửa; không mặc định phải tạo trường mới. |
| Thời điểm thu tiền | Sơ đồ tổng chỉ nêu thu cọc; ảnh kịch bản chi tiết nêu thu cả tiền thuê gốc và cọc khi nhận xe. Cần dùng một luồng nhất quán để tránh tính trùng tiền thuê khi quyết toán. |
| Mã bảng giá trễ giờ | `image7.png` dùng `LATE_FEE`; `image6.png` dùng `LATE_HOUR`. Chưa có căn cứ chọn một mã là mã đã thống nhất. |
| Tên trường loại thanh toán | Ảnh dùng cả `transaction_type` và ký hiệu `Payment: type`. Cần kiểm tra tên trường thực tế, không tự coi đây là hai trường riêng. |
| Số dư quyết toán bằng 0 | Quy tắc chữ trong `image7.png` chỉ ghi > 0 và < 0; `image5.png` ghi nhánh phụ phí ≤ cọc nhưng chưa mô tả có tạo phiếu hoàn giá trị 0 hay không. |
| Kiểu dữ liệu tiền | Ảnh đề nghị Monetary hoặc precision; DBML trong tài liệu vẫn có các cột Float. DBML là bản mô tả đề xuất, chưa chứng minh source đã đổi kiểu. |
| Cơ chế chống Charge trùng | Cờ và việc ẩn nút là đề xuất trong ảnh. Tài liệu không chứng minh đã ngăn được gọi lặp hoặc đồng thời ở server. |
| Phạm vi tài liệu | Bộ tuần 8 bao gồm cả bốn phân hệ; danh sách 15 nhóm chức năng trong file nghiệp vụ trước đó tập trung Fleet. Không dùng danh sách Fleet để kết luận toàn hệ thống đã đáp ứng tuần 8. |

## 5. Cách dùng làm căn cứ kiểm tra

- Dùng phần “thực trạng” để hiểu lỗi cũ, phần “giải quyết” để đọc hướng chuẩn hóa, phần “bổ sung” để đọc quy tắc và phân công thêm. Những điểm khác nhau vẫn phải được xác nhận; thứ tự trình bày không tự chứng minh quyết định cuối cùng.
- Khi đối chiếu code, ghi riêng: yêu cầu tài liệu; vị trí triển khai; kiểm thử/bằng chứng; kết luận đạt/chưa đạt/chưa xác minh.
- Những đoạn code, quy tắc và phân công trong tài liệu là dữ liệu nguồn để xem xét. Bản chuyển này không tự cho phép sửa, commit, push hoặc triển khai dự án.
- File Markdown chỉ được tạo để lưu nội dung và tra cứu. Đợt chuyển bản này chưa kiểm tra lại code hay chạy kiểm thử nghiệp vụ.
