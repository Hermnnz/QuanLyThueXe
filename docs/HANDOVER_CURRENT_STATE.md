# BÀN GIAO TIẾN TRÌNH DỰ ÁN QUẢN LÝ THUÊ XE (QUANLYTHUEXE-FLEET)
*Thời điểm ghi nhận: 04:15 ngày 09/11/2026*

---

### 1. Thông tin Môi trường & Nhánh Git
* **Thư mục làm việc:** `C:\Users\bac\Documents\Codex\2026-09-25\too\outputs\QuanLyThueXe-fleet`
* **Nhánh Git:** `test/fleet-optimization`
* **Python Runtime:** `C:\Users\bac\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
* **Odoo Server Runtime:** `archive/odoo18-runtime/odoo-bin`
* **Thư mục phụ thuộc (Dependencies):** `C:\odoo\venv\Lib\site-packages` và `archive/odoo18-libs`
* **Cấu hình Odoo:** `archive/quanlythuexe/quanlythuexe.conf`
* **Cổng dịch vụ Web:** `http://localhost:8078` (Database: `quanlythuexe`, tài khoản `admin` / `admin`)
* **Lệnh khởi động chuẩn:**
  ```powershell
  python scripts/run_odoo_local.py -c archive/quanlythuexe/quanlythuexe.conf
  ```

---

### 2. Tình trạng hoàn thiện phân hệ Đội xe (`motorbike_fleet_management`) - ĐẠT 100%
1. **Form Phương tiện (`fleet_vehicle_views.xml`):**
   * Nút tím **"Lưu phương tiện"** (`action_save_and_view`): Lưu xe và giữ nguyên màn hình hồ sơ xe vừa tạo.
   * Tạo Dòng xe tại chỗ: Đã gỡ triệt để `no_create: True` trên `model_id`, có nút *"Tạo và chỉnh sửa..."*.
   * Form tạo mới xe tinh gọn: Ẩn các nút kỹ thuật và tab bảo dưỡng khi tạo mới (`invisible="not id"`).
   * Tab **Bảo dưỡng định kỳ**: Chia làm 2 khối phẳng khoa học:
     * Khối 1: *Chu kỳ định mức* (km, tháng) & *Hạn tiếp theo* (nhãn trạng thái màu, ngày dự kiến, ODO dự kiến).
     * Khối 2: *Cảnh báo trước* (km, ngày) & *Mốc bảo dưỡng* (mốc ban đầu, lần làm gần nhất).
   * Chuẩn hóa Biển số xe: Tự động format `29-E1 123.45`, chống trùng lặp khoảng trắng/gạch nối.
2. **Pop-up Dòng xe (`fleet_catalog_views.xml`):**
   * Chỉ hiện `Tên dòng xe` và `Hãng xe` bắt buộc.
   * Ẩn các trường thừa `active` và `vehicle_type` khi tạo nhanh từ pop-up (`invisible="not id"`).
3. **Phiếu bảo dưỡng & Nghiệp vụ Thợ (`fleet_service_views.xml`, `fleet_service.py`, `fleet_roles.py`):**
   * Nút **"Nhận việc"** (`action_claim_ticket`): Phân quyền cho `group_motorbike_technician` và `group_fleet_manager`.
   * Khi bấm Nhận việc: Tự động gán `technician_id` là thợ đang đăng nhập, chuyển trạng thái từ `new` sang `running`.
   * Khóa chỉ đọc trường `technician_id` khi phiếu đang ở `running`, `done`, `cancelled`.
4. **Phân quyền chuẩn Odoo (`security/groups.xml`):**
   * Danh mục hiển thị: *Quản lý Đội xe* (`module_category_motorbike_fleet`, sequence: 32).
   * 3 cấp bậc kế thừa: `Staff` $\rightarrow$ `Technician` $\rightarrow$ `Manager`.

---

### 3. Kết quả Kiểm thử Tự động (ĐÃ KIỂM ĐỊNH PASS 100%)
* `TestFleetDocsContract`: **PASS (0 failed, 0 error)**
* `TestFleetRoleBatch`: **PASS (0 failed, 0 error)**
* `TestFleetRentalBridge` (Cầu nối giữa Fleet & Operation): **PASS (0 failed, 0 error)**
* `motorbike_rental_core` (`test_rental_booking_request`, `test_rental_extension`): **PASS (0 failed, 0 error)**

---

### 4. Đồng bộ dữ liệu
* Thư mục sao lưu `restore_temp_00h49\custom_addons` đã được đồng bộ **hoàn toàn giống 100% từng file** với `QuanLyThueXe-fleet\custom_addons`.
* Tài khoản kỹ thuật viên mẫu: `tho01` (Tên: `Nguyễn Văn Nam (Kỹ thuật viên)`).

---

### 5. Hướng phát triển tiếp theo cho Chat mới
1. **Kiểm thử giao diện người dùng (E2E Manual Testing):** Đăng nhập trình duyệt thử tạo xe mới, duyệt đạt kỹ thuật, tạo phiếu và bấm nhận việc với tài khoản `tho01`.
2. **Liên thông Điều hành (Operation):** Kiểm tra xuất biên bản giao nhận xe khi hợp đồng thuê được duyệt.
3. **Nạp dữ liệu mẫu hoàn chỉnh (Demo Seeding):** Chạy `scripts/seed_demo.py` để tạo sẵn 10 xe mẫu với các trạng thái khác nhau.
