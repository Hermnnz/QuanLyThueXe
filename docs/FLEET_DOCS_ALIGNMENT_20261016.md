# Đối chiếu Fleet với Word nhóm trưởng

Nguồn: `giải quyết.docx` và `giải quyết bổ sung.docx` trong `D:/Document/Hoc/nam4ki1/TH ERP/Tuan8`. Đọc cả SQL/DBML và 8 ảnh trong file bổ sung. Phạm vi: Fleet–Maintenance, không sửa thay các module thành viên khác.

| Nội dung Word | Áp dụng |
| --- | --- |
| Hãng xe: id, name, active | Dùng model chuẩn fleet.vehicle.model.brand |
| Dòng xe: id, brand_id, name, vehicle_type, active | Form/danh sách dùng tên, hãng, loại phương tiện; hỗ trợ lưu trữ |
| Không có category_id/bảng nhóm phương tiện trong Fleet | Ẩn menu nhóm, trường category_id trên dòng xe và bộ lọc nhóm category |
| Xe: model_id, license_plate, acquisition_date, active và các trường trạng thái/khóa/kỹ thuật/ngày bảo dưỡng | Hiển thị trên form xe; active qua thao tác lưu trữ chuẩn |
| Bổ sung odometer Float lưu trên fleet.vehicle | Bản 19.0.5.4.0: compute=None, inverse=None, store=True; Operations write trực tiếp được; API giao/trả cập nhật giá trị |
| Bảo dưỡng: vehicle_id, description, state, date, notes, amount, active, maintenance_type, next_service_date, result, blocks_rental, scheduled_start/end, actual_start/end | Giữ đủ trên hồ sơ bảo dưỡng, active qua thao tác lưu trữ |
| Không có technician_id/vendor_id/service_type_id trong sơ đồ Fleet | Ẩn khỏi giao diện nghiệp vụ; giữ cột/model nền và loại dịch vụ mặc định do Odoo yêu cầu |
| Operations giữ ODO/pin đầu–cuối và biên bản sự cố | Không tạo bảng tương tự trong Fleet |

## Rà lại hiển thị toàn bộ trường lúc 18:03 ngày 16/10/2026

- Đưa ô `is_electric_motorbike` vào nhóm Thông tin phương tiện theo yêu cầu người dùng; không có nhóm Phân loại phương tiện riêng. Hiển thị cả khi True và False, không giấu theo chính giá trị của nó. Đã có kiểm thử trên view sau kế thừa.
- `id` là khóa hệ thống, không cần ô nhập. `active` được quản lý qua Lưu trữ/Khôi phục, không bị xóa khỏi model. Kiểu dữ liệu, liên kết, required và unique giữ như đối chiếu/model Odoo; không tự thêm nhóm phương tiện.
- Các trường còn lại trong danh sách Word được kiểm tra hiện trên form đúng phạm vi, gồm trường lý do khóa khi đã bật khóa; trạng thái và kỹ thuật chỉ đọc nhưng vẫn hiển thị.
- Kiểm thử `test_docs_contract.py` kiểm tra form xe điện, khả năng hiện checkbox khi bỏ chọn, form dòng xe/bảo dưỡng, menu ngoài phạm vi và cột ODO lưu trực tiếp.

### Những lựa chọn triển khai không được Word quy định cụ thể

Đây là phần mô tả hiện trạng, không coi là yêu cầu nguyên văn của nhóm trưởng:

| Lựa chọn hiện tại | Căn cứ/giới hạn |
| --- | --- |
| Xe mới mặc định pending_inspection và technical_ready=False | Lựa chọn triển khai trước đây, Word không quy định mặc định |
| Nút xác nhận đạt kỹ thuật | Thao tác triển khai để cập nhật các trường Word, không phải nút được Word chỉ định |
| Không kéo Kanban; status/technical_ready chỉ đọc | Cơ chế giao diện đã triển khai, Word không quy định |
| Tạo từ menu Phương tiện mặc định is_electric_motorbike=True; menu lọc xe điện | Phạm vi/menu đã triển khai; checkbox nay hiện rõ và sửa được. Bỏ chọn sẽ khiến bản ghi không còn trong danh sách chỉ lọc xe điện sau khi lưu |
| ODO mặc định 0 | Có trong ảnh bổ sung |
| Ngày đưa vào sử dụng mặc định hôm nay | Mặc định chuẩn Odoo, Word không quy định ngày mặc định |
| blocks_rental=True và maintenance_type=preventive khi tạo phiếu | Mặc định triển khai, Word chỉ liệt kê các trường |
| Ràng buộc thời gian, kết quả hoàn tất, khóa có lý do, ODO/chi phí hợp lệ | Kiểm soát dữ liệu đã có; không coi từng chi tiết là quy tắc được Word mô tả đầy đủ |

Không tự đổi những hành vi này chỉ vì Word im lặng; cũng không tuyên bố chúng là yêu cầu của Word. Yêu cầu trực tiếp của người dùng có ưu tiên nếu khác ví dụ trong Word. Phần Rental/Operations/Finance nằm ngoài working tree, không thể xác nhận tích hợp toàn dự án chỉ bằng kiểm tra Fleet.

## Bảo toàn và giới hạn

- Không xóa bảng/cột chuẩn Odoo hoặc dữ liệu khi ẩn giao diện. Đây là đối chiếu nghiệp vụ, không tuyên bố physical schema Odoo chỉ có các cột trong Word.
- Migration ODO giữ lịch sử chuẩn, khởi tạo số hiện tại từ MAX(value) như cách Odoo cũ đọc ODO. Báo cáo nâng cấp kiểm tra riêng ODO trước/sau ngoài hash các cột cũ.
- API Fleet tiếp tục ghi log ODO để giữ khả năng tra cứu, không tạo phân hệ ODO mới.
- Ngoại lệ có yêu cầu trực tiếp của người dùng: nhận trả về pending_inspection để Fleet kiểm tra, thay vì tự available như đoạn ví dụ ảnh bổ sung. API passed chỉ dùng khi đã có kết luận đạt.
- Mô tả tình trạng chung trên xe giữ theo trao đổi trực tiếp trước đó; không phải snapshot ngoại quan/phụ kiện từng chuyến.
- Chưa xác nhận toàn bộ tích hợp trên dev hoặc Odoo 18. Không tự đổi phiên bản runtime hoặc push GitHub.

## Kiểm tra

Đợt rà hiển thị toàn bộ sau cùng: 43/43 kiểm thử đạt, không failed/error. Web RPC giao/trả/ODO/lịch bảo dưỡng/unique/trạng thái đạt. Báo cáo `FLEET_DOCS_VISIBILITY_DATA_PRESERVATION.json` xác nhận dữ liệu trước/sau giữ nguyên; 42 xe, 300 phiếu, 0 log ODO có sẵn được giữ nguyên qua kiểm tra web. Số xe tăng so với báo cáo cũ do có bản ghi người dùng tạo trong lúc kiểm tra giao diện, không nạp lại dữ liệu mẫu.

Báo cáo dữ liệu: `FLEET_DOCS_ALIGNMENT_DATA_PRESERVATION.json`. Kiểm thử bao gồm việc Operations ghi ODO trực tiếp vào cột SQL rồi giao/trả qua API. Kết quả thực tế ghi ở cuối đợt thực hiện, không suy diễn thành bảo đảm mọi tình huống.

Kết quả: nâng cấp demo thành công; 39/39 kiểm thử đạt (0 failed, 0 errors). Báo cáo dữ liệu xác nhận các cột cũ và ODO trước/sau không đổi. Web xác nhận menu nhóm phương tiện bị ẩn, form/list/search dòng xe không còn category_id; form xe hiển thị acquisition_date.
