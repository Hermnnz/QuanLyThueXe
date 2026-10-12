# Customer & Rental Core

## Tài liệu database và thuộc tính

Tài liệu này mô tả phần **Khách hàng, Hợp đồng thuê và Bảng giá theo dòng xe** trong addon `motorbike_rental_core`. Schema được đối chiếu với PostgreSQL local.

## Đọc nhanh

### Luồng dữ liệu

```text
Khách hàng (res_partner)
├── Hợp đồng thuê (rental_contract)
│   └── Dòng xe thuê (rental_contract_line)
│       ├── ID xe ngoài (module Quản lý xe; chưa có FK chính thức)
│       └── Giá/ngày chụp từ dòng xe (rental_vehicle_type)
└── Hồ sơ PDF (rental_customer_document → ir_attachment)
```

### Vai trò các bảng

| Bảng                       | Lưu gì?                                               | Ghi chú                                                  |
| -------------------------- | ----------------------------------------------------- | -------------------------------------------------------- |
| `res_partner`              | Khách hàng và thông tin thuê                          | Bảng Contacts chuẩn được addon mở rộng.                  |
| `rental_customer_document` | Tên, ngày, ghi chú của PDF                            | Nội dung file được Odoo lưu qua `ir_attachment`.         |
| `rental_contract`          | Khách, ngày thuê, tiền cọc, giới hạn ngày, trạng thái | Điều kiện thuê nằm trực tiếp trên hợp đồng.              |
| `rental_contract_line`     | Xe của hợp đồng và giá đã chốt                        | Một hợp đồng có thể có nhiều dòng; mỗi dòng chọn một xe. |
| `rental_vehicle_type`      | Dòng xe và giá thuê/ngày                              | Một giá dùng chung cho các xe cùng dòng.                 |

Danh mục xe vật lý/biển số do nhóm Xe quản lý và không tạo bảng trong addon này. Dòng hợp đồng tạm lưu ID xe dạng số nguyên; khi có technical model chính thức, field sẽ chuyển thành Many2one.

### Quy tắc dễ nhớ

- Giá được nhập theo **dòng xe**, không nhập theo từng biển số.
- Khi thêm xe vào hợp đồng, giá/ngày được chụp vào dòng hợp đồng để giữ lịch sử.
- Hợp đồng lưu trực tiếp tiền cọc và số ngày thuê tối thiểu/tối đa; không có bảng cấu hình thuê riêng.
- PDF gắn với khách hàng; một khách hàng có thể lưu nhiều file.

<details>
<summary>Mở chi tiết schema, thuộc tính, kết nối và câu lệnh SQL</summary>

Phần dưới đây là tra cứu kỹ thuật đầy đủ; các bảng được giữ nguyên để xem kiểu PostgreSQL, field, quan hệ và ví dụ truy vấn.

## 1. Phạm vi

Phần này quản lý:

- Hồ sơ khách hàng thuê xe và thông tin định danh.
- Nhiều file PDF đính kèm trên hồ sơ khách hàng.
- Tiền cọc và giới hạn ngày thuê lưu trực tiếp trên hợp đồng.
- Bảng giá thuê/ngày dùng chung theo dòng xe.
- Hợp đồng thuê, trạng thái, thời hạn và liên kết tới một hoặc nhiều xe.

**Ngoài phạm vi phụ trách:** danh mục xe vật lý và biển số do nhóm khác quản lý. Customer & Rental quản lý bảng giá theo dòng xe trong `rental.vehicle.type`.

Model Odoo có dấu chấm được ánh xạ thành tên bảng SQL bằng dấu gạch dưới. Ví dụ: `rental.contract.line` → `rental_contract_line`.

## 2. Kết nối database local

| Tham số     | Từ máy Windows   | Từ container Docker |
| ----------- | ---------------- | ------------------- |
| Hệ quản trị | PostgreSQL 16.15 | PostgreSQL 16.15    |
| Host        | `localhost`      | `db`                |
| Port        | `5432`           | `5432`              |
| Database    | `odoo_db`        | `odoo_db`           |
| Schema      | `public`         | `public`            |
| Username    | `odoo`           | `odoo`              |
| Credentials | Cấu hình riêng   | Cấu hình riêng      |

Không lưu thông tin xác thực trong tài liệu hoặc Git; cấu hình riêng cho môi trường local. Chỉ dùng SQL trực tiếp để đọc/báo cáo; dùng Odoo ORM/API để thêm, sửa hoặc xóa dữ liệu nghiệp vụ.

## 3. Quan hệ giữa các bảng

```text
res_partner 1 ─── N rental_contract
res_partner 1 ─── N rental_customer_document
rental_contract 1 ─── N rental_contract_line
rental_vehicle_type 1 ─── N rental_contract_line
rental_contract_line N ─── 1 [vehicle_id bên module Quản lý xe; chưa có FK]
rental_customer_document ─── ir_attachment (file PDF)
```

- Một khách hàng có thể có nhiều hợp đồng và nhiều tài liệu PDF.
- Một hợp đồng có thể liên kết tới một hoặc nhiều xe qua các dòng hợp đồng.
- Giá thuê được cấu hình một lần theo dòng xe; từng dòng hợp đồng lưu giá áp dụng tại thời điểm tạo.
- `vehicle_id` hiện trỏ tới prototype `rental.vehicle`; khi tích hợp chính thức, model đích sẽ theo addon của nhóm Xe.

## 4. Thuộc tính theo bảng

Các bảng model Odoo có `id` làm khóa chính và các trường audit tự sinh: `create_uid`, `create_date`, `write_uid`, `write_date`. `Many2one` được lưu dưới dạng cột integer chứa ID của record được tham chiếu. Mặc định của Odoo được áp dụng khi tạo qua ORM và có thể không xuất hiện ở `column_default` của PostgreSQL. Trong các bảng dưới đây, **Field kỹ thuật** dùng trong code/SQL; **Nhãn Odoo** là tên người dùng nhìn thấy trên form; **Chú thích** giải thích cách dùng field.

### 4.1 Khách hàng — `res_partner`

Đây là bảng Contacts chuẩn của Odoo được addon mở rộng, không phải bảng khách hàng riêng. Các trường chuẩn thường dùng gồm `name`, `phone`, `email`; addon bổ sung:

| Field kỹ thuật          | Nhãn Odoo           | Kiểu PostgreSQL         | Bắt buộc / mặc định           | Chú thích                                                          |
| ----------------------- | ------------------- | ----------------------- | ----------------------------- | ------------------------------------------------------------------ |
| `name`                  | Tên                 | varchar                 | Chuẩn Odoo; có thể NULL ở SQL | Tên cá nhân hoặc tên công ty thuê xe.                              |
| `phone`                 | Điện thoại          | varchar                 | Không bắt buộc                | Số liên hệ chính của khách.                                        |
| `email`                 | Email               | varchar                 | Không bắt buộc                | Email liên hệ.                                                     |
| `is_rental_customer`    | Khách thuê xe       | boolean                 | Mặc định ORM: False           | Bật để đưa khách vào danh sách khách thuê.                         |
| `rental_id_number`      | Số CCCD/CMND        | varchar                 | Không bắt buộc                | Số giấy tờ định danh; nên giới hạn người được quyền xem.           |
| `rental_driver_license` | Số giấy phép lái xe | varchar                 | Không bắt buộc                | Lưu số giấy phép dùng khi xác minh điều kiện thuê.                 |
| `rental_notes`          | Ghi chú thuê xe     | text                    | Không bắt buộc                | Thông tin bổ sung của khách liên quan việc thuê.                   |
| `rental_contract_ids`   | Hợp đồng thuê xe    | One2many, không tạo cột | —                             | Danh sách hợp đồng liên kết qua `rental_contract.customer_id`.     |
| `rental_document_ids`   | Tài liệu PDF        | One2many, không tạo cột | —                             | Danh sách PDF liên kết qua `rental_customer_document.customer_id`. |

### 4.2 Hồ sơ PDF khách hàng — `rental_customer_document`

| Field kỹ thuật  | Nhãn Odoo    | Kiểu PostgreSQL     | Bắt buộc / mặc định        | Chú thích                                                                     |
| --------------- | ------------ | ------------------- | -------------------------- | ----------------------------------------------------------------------------- |
| `name`          | Tên tài liệu | varchar             | Bắt buộc                   | Tên dễ nhận biết, ví dụ “CCCD mặt trước”.                                     |
| `customer_id`   | Khách hàng   | integer             | Bắt buộc                   | FK → `res_partner.id`; xóa khách hàng thì hồ sơ bị xóa theo.                  |
| `document_date` | Ngày lưu     | date                | Bắt buộc; mặc định hôm nay | Ngày ghi nhận tài liệu trong hệ thống.                                        |
| `filename`      | Tên tệp      | varchar             | Bắt buộc                   | Tên file tải lên; phải có phần mở rộng `.pdf`.                                |
| `notes`         | Ghi chú      | varchar             | Không bắt buộc             | Mô tả ngắn về file hoặc giấy tờ.                                              |
| `file`          | Tệp PDF      | Attachment của Odoo | Bắt buộc ở ORM             | Nội dung được quản lý qua `ir_attachment`, không phải cột bytea của bảng này. |

Odoo liên kết file qua `ir_attachment.res_model = 'rental.customer.document'`, `res_id = ID hồ sơ`, `res_field = 'file'`. Nội dung có thể nằm trong filestore (`store_fname`) hoặc trong database (`db_datas`) tùy cấu hình.

### 4.3 Hợp đồng thuê — `rental_contract`

| Field kỹ thuật    | Nhãn Odoo              | Kiểu PostgreSQL         | Bắt buộc / mặc định             | Chú thích                                                                     |
| ----------------- | ---------------------- | ----------------------- | ------------------------------- | ----------------------------------------------------------------------------- |
| `name`            | Mã hợp đồng            | varchar                 | Bắt buộc; tự sinh               | Sequence `RC/YYYY/00001`; không nhập tay trên form.                           |
| `customer_id`     | Khách hàng             | integer                 | Bắt buộc                        | FK → `res_partner.id`; không xóa khách đang có hợp đồng.                      |
| `start_date`      | Ngày bắt đầu           | date                    | Bắt buộc; mặc định hôm nay      | Ngày bắt đầu tính tiền thuê.                                                  |
| `end_date`        | Ngày kết thúc          | date                    | Bắt buộc; mặc định ngày kế tiếp | Phải sau ngày bắt đầu; thời hạn được kiểm tra theo cấu hình.                  |
| `rental_days`     | Số ngày thuê           | integer                 | Tự tính, lưu trữ                | Chênh lệch ngày kết thúc trừ ngày bắt đầu.                                    |
| `currency_id`     | Tiền tệ                | integer                 | Bắt buộc; mặc định tiền công ty | FK → `res_currency.id`; dùng cho tiền cọc và tổng tiền hợp đồng.              |
| `deposit_amount`  | Tiền đặt cọc           | numeric                 | Bắt buộc; mặc định 0            | Tiền cọc của hợp đồng.                                                        |
| `min_rental_days` | Số ngày thuê tối thiểu | integer                 | Bắt buộc; mặc định 1            | Ngày thuê phải đạt mức tối thiểu này.                                         |
| `max_rental_days` | Số ngày thuê tối đa    | integer                 | Mặc định 0                      | 0 là không giới hạn; nếu có giá trị thì không được nhỏ hơn min.               |
| `total_amount`    | Tổng tiền thuê         | numeric                 | Tự tính, lưu trữ                | Tổng thành tiền của các dòng xe.                                              |
| `state`           | Trạng thái             | varchar                 | Bắt buộc; mặc định `draft`      | Luồng: nháp → xác nhận → đang thuê → hoàn tất; có thể hủy trước khi hoàn tất. |
| `notes`           | Ghi chú                | text                    | Không bắt buộc                  | Thông tin bổ sung cho hợp đồng.                                               |
| `line_ids`        | Xe thuê                | One2many, không tạo cột | —                               | Danh sách xe nằm trong hợp đồng.                                              |

### 4.4 Bảng giá thuê theo dòng xe — `rental_vehicle_type`

`daily_rate` là giá chung theo dòng xe, không nhập riêng cho từng xe/biển số. Danh mục xe vật lý vẫn do nhóm xe quản lý.

| Field kỹ thuật | Nhãn Odoo         | Kiểu PostgreSQL | Bắt buộc / mặc định             | Chú thích                                                |
| -------------- | ----------------- | --------------- | ------------------------------- | -------------------------------------------------------- |
| `name`         | Tên dòng xe       | varchar         | Bắt buộc                        | Tên nhóm giá, ví dụ dòng xe điện tương ứng.              |
| `brand`        | Hãng xe           | varchar         | Không bắt buộc                  | Hãng sản xuất.                                           |
| `model`        | Mẫu xe            | varchar         | Không bắt buộc                  | Tên mẫu/dòng xe.                                         |
| `currency_id`  | Tiền tệ           | integer         | Bắt buộc; mặc định tiền công ty | FK → `res_currency.id`.                                  |
| `daily_rate`   | Giá thuê mỗi ngày | numeric         | Bắt buộc; mặc định 0            | Mức giá/ngày dùng chung cho toàn dòng xe; không được âm. |
| `active`       | Đang hoạt động    | boolean         | Mặc định True                   | Tắt để ngừng sử dụng dòng giá mới, giữ dữ liệu lịch sử.  |

### 4.5 Chi tiết xe trong hợp đồng — `rental_contract_line`

| Field kỹ thuật    | Nhãn Odoo          | Kiểu PostgreSQL | Bắt buộc / mặc định | Chú thích                                                                                   |
| ----------------- | ------------------ | --------------- | ------------------- | ------------------------------------------------------------------------------------------- |
| `contract_id`     | Hợp đồng           | integer         | Bắt buộc            | FK → `rental_contract.id`; gom xe vào hợp đồng; xóa hợp đồng thì xóa dòng này.              |
| `vehicle_id`      | ID xe ngoài        | integer         | Bắt buộc            | ID xe do module Quản lý xe cung cấp; hiện chưa có FK/Many2one vì technical model chưa chốt. |
| `vehicle_type_id` | Dòng xe / bảng giá | integer         | Bắt buộc; FK        | Liên kết trực tiếp tới `rental_vehicle_type.id` để lấy giá thuê/ngày.                       |
| `currency_id`     | Tiền tệ            | integer         | Related, lưu trữ    | Tiền tệ lấy từ hợp đồng.                                                                    |
| `daily_rate`      | Giá thuê mỗi ngày  | numeric         | Bắt buộc            | Bản chụp giá/ngày theo dòng xe tại lúc lập hợp đồng.                                        |
| `subtotal`        | Thành tiền         | numeric         | Tự tính, lưu trữ    | Số ngày thuê × giá/ngày của dòng hợp đồng.                                                  |

## 5. Quy tắc thuê xe

- Hợp đồng có thể chứa nhiều xe, nhưng không được thêm cùng một xe hai lần.
- Hợp đồng mới phải bắt đầu ở trạng thái `draft`; state chỉ chuyển theo action hợp lệ: `draft → confirmed → in_progress → done`, hoặc hủy từ `draft`, `confirmed`, `in_progress`.
- Trạng thái `done` và `cancelled` là trạng thái kết thúc; không cho chuyển tiếp hoặc hủy lại.
- Khi xác nhận, hợp đồng phải có ít nhất một xe.
- Xe không được nằm trong hai hợp đồng `confirmed`/`in_progress` có khoảng ngày giao nhau; hợp đồng liền kề ngày được phép.
- Thời hạn thuê phải đạt `min_rental_days`/`max_rental_days` trên hợp đồng; ngày kết thúc phải sau ngày bắt đầu.
- Giá từ dòng xe được chụp vào hợp đồng để thay đổi bảng giá không sửa lịch sử hợp đồng cũ.
- Tiền đặt cọc và giá thuê mỗi ngày không được âm.
- ID xe được kiểm tra không trùng và trùng lịch; trạng thái sẵn sàng của xe sẽ cần tích hợp sau.
- File khách hàng chỉ chấp nhận tên có đuôi `.pdf` và nội dung có header `%PDF-`.

Các kiểm tra trên được thực hiện bởi Odoo ORM; không phải tất cả đều là constraint trong PostgreSQL. Khi kết nối để ghi dữ liệu, gọi ORM/API thay vì INSERT/UPDATE trực tiếp.

## 6. Truy vấn mẫu chỉ đọc

### Danh sách hợp đồng và khách hàng

```sql
SELECT c.id, c.name AS contract_no, p.name AS customer,
       c.start_date, c.end_date, c.rental_days, c.state
FROM rental_contract AS c
JOIN res_partner AS p ON p.id = c.customer_id
ORDER BY c.start_date DESC, c.id DESC;
```

### Giá và xe đã chọn trên hợp đồng

```sql
SELECT c.name AS contract_no, line.vehicle_id, t.name AS vehicle_type,
       line.daily_rate, line.subtotal
FROM rental_contract_line AS line
JOIN rental_contract AS c ON c.id = line.contract_id
JOIN rental_vehicle_type AS t ON t.id = line.vehicle_type_id
ORDER BY c.id, line.id;
```

`vehicle_id` hiện là ID ngoài nên truy vấn này chưa thể lấy biển số. Sau khi có model chính thức, nối field này với bảng xe của nhóm Quản lý xe.

### Metadata PDF gắn với khách hàng

```sql
SELECT d.id, d.customer_id, d.name, d.filename, d.document_date,
       a.mimetype, a.store_fname, a.file_size
FROM rental_customer_document AS d
LEFT JOIN ir_attachment AS a
  ON a.res_model = 'rental.customer.document'
 AND a.res_id = d.id
 AND a.res_field = 'file';
```

Truy vấn cuối chỉ đọc metadata. Để tải nội dung PDF, nên dùng Odoo UI/API vì file có thể được lưu trong filestore.

</details>
