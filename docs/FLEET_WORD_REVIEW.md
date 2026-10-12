> Đã xử lý sau rà soát, phiên bản 19.0.5.1.0: bổ sung UNIQUE(vehicle_code) ở database và khóa sửa tay operational_status/technical_ready trên form. Mã duy nhất kể cả xe lưu trữ; xe chưa cấp mã và bản sao có thể để NULL. Phương thức giao/trả/bảo dưỡng vẫn cập nhật qua ORM với validation hiện có. Bảng đối chiếu bên dưới ghi nhận hiện trạng trước khi sửa; hai mục mã trùng/sửa tay trên form đã được xử lý. Các phần cần Operations/Rental nối vẫn giữ đúng phạm vi. Kiểm thử sửa: 34/34 trên database thử và demo nâng cấp, RPC đạt; đối chiếu `FLEET_WORD_FIX_DATA_PRESERVATION.json`.

# Đối chiếu Fleet với tài liệu nhóm trưởng

Rà soát ngày 12/10/2026, module `motorbike_fleet_management` phiên bản `19.0.5.0.0`. Đã đọc lại nội dung và hình nhúng trong ba file Word: `thực trạng.docx`, `giải quyết.docx`, `giải quyết bổ sung.docx` tại `D:/Document/Hoc/nam4ki1/TH ERP/Tuan8`.

Kết luận: phần Fleet đáp ứng các nhiệm vụ chính trong bảng phân công cho Bắc. Chưa khớp hoàn toàn ERD về tính duy nhất của mã xe; các luồng xuyên module chưa được kiểm chứng vì repo/database demo chỉ có Fleet. Đây là lần kiểm tra và ghi nhận, không thay đổi code hoặc dữ liệu nghiệp vụ.

| Nội dung Word | Hiện trạng | Kết luận |
| --- | --- | --- |
| Hai model lõi Xe/Bảo dưỡng, danh mục hãng/dòng xe | Kế thừa Fleet chuẩn; không tạo danh mục trùng | Khớp |
| Bốn trạng thái available/renting/maintenance/pending_inspection | Selection, bộ lọc, Kanban và migration đã thống nhất | Khớp |
| rental_blocked kiểu Boolean | Có, cần lý do; kiểm tra điều kiện Fleet/giao xe chặn khi khóa | Khớp |
| ODO hiện tại trên fleet.vehicle | Có sẵn field odometer chuẩn Odoo, compute/inverse dựa trên lịch sử chuẩn | Đạt mục tiêu; chủ động không khai báo đè Float trong ví dụ Word |
| Giao xe cập nhật renting | action_deliver_vehicle kiểm tra điều kiện rồi chuyển renting | Fleet đã có; Giang cần gọi từ thao tác xác nhận giao |
| Nhận trả cập nhật ODO và trạng thái | action_return_vehicle ghi ODO theo ngày và xử lý kết quả kiểm tra bắt buộc | Fleet đã có; không dùng đoạn mẫu luôn ghi available |
| Kiểm tra lỗi/pin yếu trước khi đổi trạng thái | Fleet nhận kết luận passed/failed/pending/maintenance; không có field hoặc tham số pin trên xe | Operations kiểm tra pin và gửi kết luận phù hợp; hiện chưa nối |
| model_id/vehicle_id Many2one nối Rental/Operations tới Fleet | Các model đích Fleet có sẵn | Khóa ngoại phía Rental/Operations do thành viên phụ trách thêm |
| Giữ chỗ và chống trùng lịch thuê | Fleet kiểm tra kỹ thuật/khóa thuê/lịch bảo dưỡng; không có hợp đồng trong repo | Rental phải kiểm tra các hợp đồng có hiệu lực và xử lý yêu cầu đồng thời |
| Đổi xe trên đường | Fleet có phương thức trả xe cũ và giao xe mới; chưa có thao tác đổi xe xuyên module | Operations/Rental phải nối cùng giao dịch |
| vehicle_code [unique] trong cả hai bản DBML Word | Code chỉ index=True; database chỉ có index thường | Chưa khớp: cần bổ sung ràng buộc duy nhất nếu chốt theo ERD này |

## Hai khác biệt có chủ đích

ODO chuẩn tồn tại ngay trên `fleet.vehicle`: giá trị hiện tại lấy từ `fleet.vehicle.odometer`. Việc không thêm field Float mới vẫn cho phép Giang đọc `vehicle.odometer`; giao/trả qua phương thức Fleet ghi vào lịch sử chuẩn. Không có cột SQL `odometer` trên bảng xe nên ERD vật lý phải thể hiện đúng điều này. Số đo ODO trong giao diện Fleet hiện là tùy chọn; nếu nhóm bắt buộc đo mỗi chuyến, Operations phải yêu cầu nhập trước khi gọi.

Đoạn code minh họa Word ghi `operational_status='available'` sau mọi lần trả xe. Code hiện tại chỉ làm vậy khi kết quả `passed`; lỗi/chưa kết luận → `pending_inspection`, cần sửa hoặc còn bảo dưỡng chạy → `maintenance`. Cách này phù hợp yêu cầu kiểm tra lỗi trước khi cập nhật trạng thái và thống nhất trước đó với người dùng. Khóa thuê chủ động vẫn giữ.

## Điểm cần hoàn thiện khi nhóm nối module

1. Mã xe: database hiện không có mã trùng, nhưng vẫn cho phép tạo trùng trong tương lai. Khóa ngoại Many2one dùng ID nên không bị hỏng ngay; tính duy nhất vẫn cần chốt để code và ERD thống nhất.
2. Giang cần gọi phương thức Fleet đã bàn giao, thay vì chỉ sao chép đoạn write trong Word. Operations lưu ODO/pin đầu–cuối, kiểm tra ODO cuối ≥ đầu của chuyến, ngăn xác nhận lặp và cập nhật dòng giao/trả cùng transaction. Pin dưới ngưỡng tính phí thuộc Operations/Finance; phí đã tạo không tự chứng minh xe đủ pin để giao lượt sau.
3. Đổi xe không chỉ đổi vehicle_id: phải xử lý xe cũ về chờ kiểm tra/bảo dưỡng, kiểm tra và giao xe mới sang renting, cập nhật liên kết hợp đồng/phiếu và giữ dữ liệu sự cố. Nếu bỏ cập nhật trạng thái, xe cũ có thể vẫn renting còn xe mới vẫn available. Fleet cung cấp các phương thức thành phần, chưa có orchestration đổi xe.
4. Các trường trạng thái và technical_ready vẫn sửa được trên form. Constraints chặn một số tổ hợp sai, nhưng chưa ngăn mọi thao tác đổi tay bỏ qua luồng giao/trả. Đây là đề xuất củng cố workflow, không phải yêu cầu mới được ghi rõ trong bảng phân công Word. Không nên tuyên bố hệ thống đã bắt buộc mọi thay đổi đi qua Operations.

ODO/pin snapshot, ngày giờ hợp đồng, actual_return_date, incident_id, phí phạt, Monetary, chống tạo Charge trùng và quyết toán thuộc các module khác. Không bổ sung những bảng này vào Fleet. Ràng buộc duy nhất cặp contract_id/vehicle_id trong cùng hợp đồng cũng không thay thế kiểm tra xe trùng thời gian giữa hai hợp đồng.

## Bằng chứng kiểm tra

- Demo đang cài `19.0.5.0.0`; 21 available, 8 renting, 6 pending_inspection, 4 maintenance, tổng 39 xe gồm xe lưu trữ. Không còn khóa trạng thái cũ.
- Index thực tế: `CREATE INDEX fleet_vehicle__vehicle_code_index ... (vehicle_code)`, không UNIQUE; truy vấn hiện không tìm thấy mã trùng.
- Repo chỉ có một manifest Fleet; database chưa có các model hợp đồng/vận hành/tài chính của nhóm. Vì vậy các xe đang thuê trong bộ dữ liệu một năm vẫn là trạng thái giả lập, không phải hợp đồng thuê thật.
- Bộ kiểm thử gần nhất: 31/31 đạt trên cài mới và nâng cấp, RPC giao/trả/ODO/lịch bảo dưỡng đạt. Lần rà soát này không sửa code nên không chạy lại toàn bộ test.
- Bảo toàn dữ liệu: `docs/FLEET_INTEGRATION_DATA_PRESERVATION.json`; hướng dẫn gọi: `handoff/Fleet_Integration_Week8.md`.
