# Motorbike Rental Core - Hướng dẫn cho người mới bắt đầu với Odoo

> Phần dưới đây mô tả code hiện đang có trong folder `Thue_xe`, phiên bản addon `19.0.1.0.4`, chạy trên Odoo 19.

## Phần đã làm

### 1. Phạm vi

Addon hiện có các chức năng:

- Mở rộng hồ sơ khách hàng thuê xe trên Contacts của Odoo.
- Lưu nhiều PDF trong hồ sơ khách hàng.
- Tạo hợp đồng thuê, gắn một hoặc nhiều xe, theo dõi trạng thái hợp đồng.
- Lưu tiền cọc và giới hạn ngày thuê ngay trên hợp đồng.
- Quản lý giá thuê/ngày theo dòng xe; giá không nhập riêng theo biển số.

Danh mục xe vật lý/biển số thuộc nhóm Xe và không được tạo lại trong addon này. Dòng hợp đồng lưu `vehicle_id` dạng số nguyên làm external ID tạm thời; khi nhóm Xe cung cấp technical model chính thức, field này sẽ chuyển thành Many2one để chọn xe trực tiếp.

### 2. Các model và bảng dữ liệu

Tên model Odoo có dấu chấm được chuyển thành tên bảng SQL bằng dấu gạch dưới.

| Model Odoo                 | Bảng SQL                   | Dùng để                                                      |
| -------------------------- | -------------------------- | ------------------------------------------------------------ |
| `res.partner`              | `res_partner`              | Hồ sơ khách hàng chuẩn Odoo, được bổ sung thông tin thuê xe. |
| `rental.customer.document` | `rental_customer_document` | Thông tin mô tả từng PDF gắn với khách hàng.                 |
| `rental.contract`          | `rental_contract`          | Hợp đồng, thời hạn, tiền cọc, trạng thái và tổng tiền.       |
| `rental.contract.line`     | `rental_contract_line`     | Mỗi dòng nối hợp đồng, external vehicle ID và dòng giá.      |
| `rental.vehicle.type`      | `rental_vehicle_type`      | Dòng xe và giá thuê/ngày dùng chung cho dòng đó.             |

### 3. Thuộc tính chính

**Khách hàng — `res.partner`**

- `is_rental_customer`: đánh dấu khách thuê xe.
- `rental_id_number`: số CCCD/CMND.
- `rental_driver_license`: số giấy phép lái xe.
- `rental_notes`: ghi chú thuê xe.
- `rental_contract_ids`, `rental_document_ids`: quan hệ một khách hàng có nhiều hợp đồng/PDF; đây là One2many nên không tạo cột riêng.

**Hồ sơ PDF — `rental.customer.document`**

- `customer_id`: khách hàng sở hữu hồ sơ.
- `name`, `filename`, `document_date`, `notes`: thông tin để nhận biết và tra cứu file.
- `file`: nội dung PDF do Odoo lưu qua `ir_attachment`, không nằm trực tiếp trong bảng `rental_customer_document`.
- File được kiểm tra phần mở rộng `.pdf` và chữ ký nội dung `%PDF-`.

**Hợp đồng — `rental.contract`**

- `name`: mã hợp đồng tự sinh theo sequence `RC/YYYY/00001`.
- `customer_id`: khách thuê; `start_date`, `end_date`: thời hạn.
- `deposit_amount`: tiền cọc; `currency_id`: tiền tệ.
- `min_rental_days`, `max_rental_days`: giới hạn ngày thuê; `max_rental_days = 0` nghĩa là không giới hạn.
- `rental_days`: số ngày được tính từ ngày kết thúc trừ ngày bắt đầu.
- `total_amount`: tổng tiền được tính từ số ngày thuê và giá/ngày của các dòng xe.
- `state`: trạng thái hợp đồng; `notes`: ghi chú.

Tiền cọc và giới hạn ngày được lưu trực tiếp trên từng hợp đồng. Module không còn bảng cấu hình thuê riêng.

**Dòng xe và giá — `rental.vehicle.type`**

- `name`, `brand`, `model`: tên dòng xe và thông tin nhận biết.
- `daily_rate`: giá thuê/ngày dùng chung cho các xe cùng dòng.
- `currency_id`: tiền tệ của giá; `active`: có cho phép chọn dòng giá mới hay không.

**Dòng hợp đồng — `rental.contract.line`**

- `contract_id`: hợp đồng cha; xóa hợp đồng sẽ xóa các dòng chi tiết.
- `vehicle_id`: số ID xe nhận từ module Quản lý xe; hiện chưa có dropdown vì technical model chưa được cung cấp.
- `vehicle_type_id`: dòng giá được chọn trực tiếp từ `rental.vehicle.type`.
- `daily_rate`: bản chụp giá/ngày lúc thêm xe vào hợp đồng, để lịch sử không đổi khi cập nhật bảng giá.
- `subtotal`: số ngày thuê nhân với giá/ngày của dòng đó.

### 4. Quy trình sử dụng

1. Tạo khách hàng trong **Khách hàng thuê xe**, bổ sung CCCD/CMND và giấy phép nếu cần.
2. Tải giấy tờ PDF lên tab **Thuê xe** trong hồ sơ khách hàng.
3. Rental Manager vào **Cấu hình → Bảng giá thuê theo dòng xe**, tạo dòng xe và nhập giá/ngày.
4. Chọn dòng giá và nhập external vehicle ID do nhóm Quản lý xe cung cấp. Sau khi tích hợp technical model, trường ID sẽ đổi thành dropdown chọn xe.
5. Tạo **Hợp đồng thuê xe**, chọn khách hàng, thời hạn, tiền cọc, giới hạn ngày và thêm một hoặc nhiều xe.
6. Xác nhận hợp đồng để giữ lịch xe; lần lượt chuyển sang đang thuê và hoàn tất khi phù hợp.

### 5. State machine và kiểm tra dữ liệu

```text
Nháp --Xác nhận--> Đã xác nhận --Bắt đầu thuê--> Đang thuê --Hoàn tất--> Hoàn tất
  |                     |                    |
  +-------- Hủy --------+-------- Hủy --------+----------------------> Đã hủy
```

- Chỉ tạo hợp đồng ở trạng thái nháp; chuyển trạng thái phải đi qua action hợp lệ, không ghi state tùy ý.
- Chỉ hợp đồng nháp được xác nhận; chỉ hợp đồng đã xác nhận được bắt đầu thuê.
- Chỉ hợp đồng đang thuê được hoàn tất; có thể hủy hợp đồng nháp/đã xác nhận/đang thuê.
- Hợp đồng đã hoàn tất hoặc đã hủy là trạng thái kết thúc và không thể chuyển tiếp.
- Ngày kết thúc phải sau ngày bắt đầu; thời hạn phải đạt `min_rental_days` và không vượt `max_rental_days` nếu có giới hạn.
- Tiền đặt cọc và giá thuê mỗi ngày không được âm.
- Hợp đồng phải có ít nhất một xe trước khi xác nhận.
- Không cho trùng cùng một xe trong hợp đồng hoặc trùng lịch xe với hợp đồng đang xác nhận/đang thuê.
- Giá ngày không được âm; external vehicle ID không được trùng trên cùng hợp đồng hoặc trùng lịch với hợp đồng đang hiệu lực.

Các quy tắc trên chạy qua Odoo ORM. Vì vậy thao tác ghi nên thực hiện qua giao diện/ORM/API, không `INSERT` trực tiếp vào PostgreSQL.

### 6. Menu và quyền

- **Quản lý thuê xe → Khách hàng thuê xe**: danh sách, tìm kiếm và hồ sơ khách thuê.
- **Quản lý thuê xe → Hợp đồng thuê xe**: danh sách, tìm kiếm và state machine.
- **Cấu hình → Bảng giá thuê theo dòng xe**: quản lý giá chung theo dòng; dành cho Rental Manager.
- **Danh mục xe vật lý**: do nhóm Xe quản lý; không có bảng, menu hay CRUD xe vật lý trong addon này.
- Rental User tạo/sửa hợp đồng và thêm PDF; Rental Manager có quyền quản lý bảng giá, hợp đồng và PDF theo ACL hiện tại.

### 7. Chạy trên máy local

Từ folder `D:\Odoo_data`:

```powershell
docker compose up -d
```

Mở `http://localhost:8069`, chọn database `odoo_db` nếu được hỏi và đăng nhập bằng tài khoản Odoo hiện có. Module đã nằm trong `addons-path`; khi code thay đổi, dùng **Apps → Motorbike Rental Core → Upgrade**.

Database local dùng PostgreSQL 16, tên `odoo_db`, schema `public`; thông tin host/user/password được khai báo trong `docker-compose.yml`. Đây là cấu hình phát triển, không dùng nguyên trạng trên môi trường production.

---

<details>
<summary>Giải thích thêm về Odoo cho người mới</summary>

## 1. Odoo là gì?

Odoo là một nền tảng quản trị doanh nghiệp. Nói đơn giản, Odoo cho phép bạn:

- quản lý khách hàng
- quản lý đơn hàng
- quản lý nhân sự
- quản lý kho hàng
- quản lý tài chính
- và tùy chỉnh theo nhu cầu riêng của doanh nghiệp

Odoo hoạt động theo kiểu module (addon). Mỗi module là một phần chức năng riêng.

Ví dụ:

- module khách hàng: `contacts`
- module đơn hàng: `sale`
- module của bạn: `motorbike_rental_core`

---

## 2. Module là gì?

Trong Odoo, module là một gói code chứa chức năng riêng.

Ví dụ trong dự án của bạn:

- `motorbike_rental_core` là module chính
- nó chứa các model dữ liệu, view, quyền truy cập, menu

Một module Odoo thường có các phần sau:

- `__manifest__.py`: khai báo thông tin module
- `models/`: chứa dữ liệu
- `views/`: chứa giao diện người dùng
- `security/`: chứa quyền truy cập
- `data/`: chứa dữ liệu khởi tạo

---

## 3. Dự án của bạn đang làm gì?

Bạn đang xây một module cho hệ thống thuê xe máy.

Nó có 4 phần cốt lõi:

1. Khách hàng thuê xe
2. Điều kiện thuê trên hợp đồng
3. Bảng giá thuê theo dòng xe
4. Hợp đồng thuê xe

Nói đơn giản:

- ai thuê xe
- thời hạn và tiền cọc của hợp đồng
- giá thuê theo dòng xe
- hợp đồng thuê như thế nào

---

## 4. Tại sao phải có model?

Trong Odoo, model tương đương với bảng dữ liệu.

Ví dụ:

- `res.partner`: bảng khách hàng
- `rental.contract`: bảng hợp đồng thuê
- `rental.vehicle.type`: dòng xe và giá thuê/ngày dùng chung

Nếu bạn chưa từng làm database, hãy hình dung như sau:

- model = bảng
- field = cột trong bảng
- record = dòng dữ liệu

Ví dụ:

- `res.partner` có các cột như tên, email, số điện thoại
- `rental.contract` có các cột như khách hàng, ngày bắt đầu, ngày kết thúc, trạng thái

---

## 5. Mô tả từng file trong project

### 5.1 `__manifest__.py`

Đây là file quan trọng nhất để Odoo nhận diện module.

Nó giống như "thẻ giới thiệu" của module.

Nó chứa:

- tên module
- version
- module phụ thuộc
- file dữ liệu cần load

Ví dụ:

```python
{
    'name': 'Motorbike Rental Core',
    'version': '1.0.0',
    'depends': ['base', 'contacts'],
    'data': [...],
}
```

Nếu file này sai, module sẽ không cài được.

---

### 5.2 `models/__init__.py`

File này dùng để import các model vào module.

Ví dụ:

```python
from . import res_partner
from . import rental_contract
```

Nghĩa là Odoo nạp các model Customer & Rental Order của addon khi cài module.

---

### 5.3 `models/res_partner.py`

Đây là file mở rộng khách hàng.

Trong Odoo, `res.partner` là model khách hàng chuẩn.

Bạn thêm các field mới để lưu thêm thông tin thuê xe, ví dụ:

- `is_rental_customer`
- `rental_id_number`
- `rental_driver_license`
- `rental_notes`
- hồ sơ PDF đính kèm (có thể lưu nhiều tài liệu cho mỗi khách hàng)

Cách hiểu đơn giản:

- trước đây partner chỉ là người liên hệ
- bây giờ partner còn có thêm thông tin liệu họ có thuê xe hay không

---

### 5.4 `models/rental_contract.py`

Đây là bảng hợp đồng thuê xe.

Nó chứa:

- khách hàng thuê
- tiền cọc và giới hạn ngày thuê ngay trên hợp đồng
- một hoặc nhiều xe qua các dòng chi tiết hợp đồng
- ngày bắt đầu
- ngày kết thúc
- trạng thái hợp đồng
- ghi chú

Các trạng thái hợp đồng cơ bản:

- Draft
- Confirmed
- In Progress
- Done
- Cancelled

Nói đơn giản:

- khi khách thuê xe, bạn tạo hợp đồng
- hợp đồng đó sẽ đi qua các trạng thái khác nhau

### 5.5 Bảng giá thuê theo dòng xe

Model `rental.vehicle.type` lưu `daily_rate` dùng chung cho các xe cùng dòng. Rental Manager cập nhật giá tại menu **Configuration → Bảng giá thuê theo dòng xe**. Danh sách xe vật lý và biển số do nhóm xe quản lý.

---

## 6. Relation là gì?

Trong Odoo, relation là mối quan hệ giữa các model.

Bạn có 2 mối quan hệ chính trong module này:

### 6.1 Khách hàng với hợp đồng

```text
res.partner 1 ---- N rental.contract
```

Tức là:

- 1 khách hàng có thể có nhiều hợp đồng
- mỗi hợp đồng thuộc về 1 khách hàng

Trong code, điều này được biểu diễn bằng field:

```python
customer_id = fields.Many2one('res.partner')
```

Và ngược lại:

```python
rental_contract_ids = fields.One2many('rental.contract', 'customer_id')
```

---

### 6.2 Điều kiện thuê trên hợp đồng

Tiền cọc, số ngày thuê tối thiểu và tối đa được lưu trực tiếp trên `rental.contract`. Mỗi hợp đồng giữ lại điều kiện áp dụng cho chính nó, không cần chọn record cấu hình dùng chung.

---

## 7. View là gì?

View là giao diện của Odoo.

Trong Odoo, view có 3 dạng phổ biến:

- form: hiển thị chi tiết một bản ghi
- tree: hiển thị danh sách bản ghi
- search: tìm kiếm

Ví dụ trong dự án:

- form khách hàng: hiển thị thông tin khách hàng thuê xe
- tree hợp đồng: hiển thị danh sách hợp đồng
- form hợp đồng: hiển thị tiền cọc và giới hạn ngày thuê

Nếu không có view thì người dùng sẽ không thấy dữ liệu trên màn hình.

---

## 8. Menu là gì?

Menu là đường dẫn trong Odoo để người dùng vào chức năng.

Trong dự án bạn, menu có dạng như:

- Motorbike Rental
  - Rental Management
    - Rental Contracts
  - Rental Customers
  - Configuration
    - Bảng giá thuê theo dòng xe
  - Danh mục xe được mở từ module Quản lý xe; không thuộc menu addon này

Tức là:

- người dùng vào menu này để thấy hợp đồng
- vào menu kia để thấy khách hàng thuê
- nhập điều kiện thuê ngay trên hợp đồng

---

## 9. Security và ACL là gì?

Đây là phần quyền truy cập.

Giả sử bạn có nhiều người dùng trong dự án, không phải ai cũng được sửa tất cả dữ liệu.

Odoo có 2 khái niệm cơ bản:

- group: nhóm người dùng
- rule: quy tắc quyền

Ví dụ:

- `Rental User`: người dùng bình thường
- `Rental Manager`: người quản lý có quyền cao hơn

`ir.model.access.csv` định nghĩa ai được đọc, tạo, sửa, xóa model nào.

Nói đơn giản:

- Rental User được xem bảng giá, tạo/sửa hợp đồng và thêm PDF nhưng không được xóa tài liệu.
- Rental Manager có toàn quyền với bảng giá, hợp đồng và tài liệu PDF; danh mục xe vật lý thuộc phân hệ xe.

---

## 10. Dữ liệu khởi tạo là gì?

File sequence khởi tạo mã hợp đồng để module có thể tự sinh số hợp đồng.

---

## 11. Lưu ý về phiên bản

Khi phát triển module Odoo, các phiên bản khác nhau có thể có sự khác biệt về API và kiểm tra cú pháp. Luôn kiểm tra trường `depends` trong `__manifest__.py` và thử cài module trên phiên bản Odoo mục tiêu.

Một số lỗi thường gặp khi chuyển giữa các bản Odoo hoặc khi dùng code cũ:

- thiếu dependency (module cần chưa được khai báo trong `depends`)
- tham chiếu XML sai hoặc thiếu trường
- tham số field đã được deprecated hoặc thay đổi tên

Nếu cần, mình có thể kiểm tra và chỉnh sửa module để tương thích với phiên bản Odoo mà nhóm bạn đang sử dụng.

---

## 12. Cách các file kết nối với nhau

Mình mô tả kiểu dễ tưởng tượng như sau:

### Bước 1: Khách hàng

`res.partner` lưu thông tin khách hàng thuê xe.

### Bước 2: Hợp đồng

`rental.contract` lưu khách hàng, thời hạn, tiền cọc và điều kiện số ngày thuê; các xe được gắn qua các dòng chi tiết hợp đồng.

### Bước 3: Odoo hiển thị bằng view

View cho mỗi model hiển thị trên form/tree/menu.

### Bước 4: Odoo kiểm soát quyền

ACL và security giới hạn người dùng được quyền gì.

Như vậy, module mới trọn vẹn.

---

## 13. Chạy module trong Odoo như thế nào?

### Bước 1: Khởi động Docker

```bash
docker-compose up -d
```

### Bước 2: Mở Odoo

```text
http://localhost:8069
```

### Bước 3: Vào Apps

- chọn `Update Apps List`
- tìm `Motorbike Rental Core`
- nhấn `Install`

### Bước 4: Vào menu

- `Motorbike Rental`
- xem khách hàng
- cập nhật bảng giá theo dòng xe trong Configuration
- nhập điều kiện thuê ở hợp đồng
- tạo hợp đồng thuê

---

## 14. Nếu mới học Odoo, hãy nhớ 3 điều này

### 1. Học model trước

Model là nền tảng của Odoo.

Nếu model đúng, phần còn lại dễ làm.

### 2. Học relation trước

Bạn phải biết:

- 1-1
- 1-N
- N-N

Trong module của bạn, bạn dùng 1-N rất rõ.

### 3. Học view + menu sau

Sau khi model đã xong, bạn mới làm giao diện và menu.

---

## 15. Tóm tắt rất ngắn

Project của bạn có nghĩa là:

- Khách hàng thuê xe được lưu trong `res.partner`
- Giá thuê/ngày dùng chung theo dòng xe được lưu trong `rental.vehicle.type`
- Điều kiện tiền cọc và giới hạn ngày thuê được lưu trong `rental.contract`
- Hợp đồng thuê được lưu trong `rental.contract`
- Hợp đồng liên kết tới khách hàng và các dòng xe
- Odoo hiển thị bằng form/tree/menu
- quyền truy cập được kiểm soát bằng ACL

Đây là một module Odoo cơ bản nhưng đúng kiểu nền tảng cho hệ thống thuê xe.

---

## 16. Kết luận

Nếu bạn mới làm quen với Odoo, hãy hiểu theo cách này:

- Odoo làm việc theo module
- module là tập hợp các model, view, security, data
- model là dữ liệu chính
- view là giao diện
- ACL là quyền
- relation là cách nối các dữ liệu với nhau

Và module `motorbike_rental_core` của bạn chính là một ví dụ rất tốt để bắt đầu học Odoo.

Nếu bạn muốn, mình có thể làm tiếp cho bạn:

1. phiên bản README cực ngắn cho thuyết trình
2. phiên bản README theo kiểu báo cáo dự án nhóm
3. phiên bản README có hình ảnh sơ đồ mối quan hệ dễ đọc hơn
4. hướng dẫn từng file code thao tác từ đầu đến cuối

### Module đã triển khai trong workspace

Addon nằm tại `motorbike_rental_core/` và được Docker đưa vào `addons-path` từ folder `Thue_xe`. Hợp đồng lưu tiền cọc, giới hạn ngày và trạng thái trực tiếp; một hợp đồng có thể có nhiều dòng xe. Giá/ngày được quản lý theo dòng xe trong `rental.vehicle.type` và được chụp trên dòng hợp đồng. Hồ sơ khách hàng cho phép lưu nhiều PDF; danh mục xe vật lý/biển số thuộc nhóm khác.

Số ngày thuê tối thiểu/tối đa và ngày bắt đầu/kết thúc được kiểm tra khi tạo hoặc cập nhật hợp đồng.

</details>
