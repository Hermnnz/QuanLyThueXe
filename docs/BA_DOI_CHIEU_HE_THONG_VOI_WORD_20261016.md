# Báo cáo BA đối chiếu bản Fleet hiện có với tài liệu Word

Ngày: 16/10/2026. Phương pháp: đọc Word và 13 ảnh tuần 8, đọc source hiện tại, đối chiếu cấu trúc form và danh sách model của ứng dụng đang chạy qua các lệnh đọc. Không chạy workflow giao/trả, không tạo/xóa/sửa xe, phiếu hoặc tiền trong lượt rà này. Đăng nhập kỹ thuật chỉ để đọc thông tin.

## 1. Kết luận cần biết trước khi nộp

**Chưa đủ cơ sở xác nhận bản hiện có đúng hoàn toàn theo tài liệu hoặc đã là toàn bộ hệ thống của nhóm.**

- Địa chỉ `http://localhost:8072/` đang chạy **Odoo 19.0**, database `motorbike_fleet_simple_20261002`, module `motorbike_fleet_management` phiên bản **19.0.5.5.0**.
- Database này có Fleet; không có các model thuê xe, hợp đồng, vận hành, sự cố, khoản phí và thanh toán tùy biến trong Word tuần 8. `fleet.vehicle.log.contract` chuẩn Odoo không phải `rental.contract` của nhóm.
- Đã xác định ba điểm thiếu/khác so với file nghiệp vụ được cung cấp: trường quản lý người/đơn vị/loại sửa chữa trên UI; đường xem lịch sử ODO; đường cập nhật ODO trực tiếp không ghi lịch sử trong source.
- Có ba rủi ro bổ sung trong source cần tái hiện trên bản thử: mốc bảo dưỡng khi có phiếu lưu trữ, thay cờ xe điện làm mất khả năng xem hồ sơ cũ trên UI, và xóa xe đang thuê khi chưa có bản ghi liên quan ngăn xóa.
- Có hai quyết định tích hợp chưa thống nhất giữa tài liệu: trả xe về trạng thái nào và Operations có được dùng đoạn `write` trực tiếp như ví dụ Word hay phải gọi API Fleet.

Không tính việc thiếu Contract/Operations/Finance là lỗi của riêng module Bắc. Nhưng đây là lý do không thể dùng URL này để nghiệm thu toàn bộ hệ thống theo sơ đồ bốn phân hệ.

## 2. Chuẩn yêu cầu và mức bằng chứng

Word là chuẩn đối chiếu. Source và báo cáo Markdown do AI viết không được dùng để tự sửa nghĩa Word. Nếu hai file Word khác nhau thì ghi cần xác nhận, không chọn code làm đáp án.

| Ký hiệu | Nguồn |
| --- | --- |
| NV | [File nghiệp vụ](<D:/Document/Hoc/HeNam3/Video/nghiệp vụdocx.docx>), dùng số mục 1–15. File này mở đầu như một bản mô tả đã đối chiếu source; ở lượt rà này vẫn dùng làm tài liệu người dùng cung cấp, đồng thời nêu rõ nơi khác bộ tuần 8. |
| GQ | [Giải quyết](<D:/Document/Hoc/nam4ki1/TH ERP/Tuan8/giải quyết.docx>), phần DBML và ảnh chuẩn hóa. |
| BS | [Giải quyết bổ sung](<D:/Document/Hoc/nam4ki1/TH ERP/Tuan8/giải quyết bổ sung.docx>), 8 ảnh theo thứ tự xuất hiện trong Word. |
| TT | [Thực trạng](<D:/Document/Hoc/nam4ki1/TH ERP/Tuan8/thực trạng.docx>), mô tả hiện trạng cũ, không phải mọi chi tiết đều là thiết kế cần giữ. |

Mức bằng chứng:

- **Đã xác minh trên bản đang chạy:** đọc danh sách module/model, form kế thừa đã kết hợp, cấu hình trường/menu; chưa đồng nghĩa đã bấm hết UI hoặc chạy workflow.
- **Xác định từ source:** đường xử lý đọc được cho thấy thiếu/khác; chưa thực hiện thao tác ghi để tái hiện trên database.
- **Rủi ro cần tái hiện:** có điều kiện cụ thể trong code dẫn tới nghi vấn; chưa gọi là lỗi đã xảy ra với dữ liệu người dùng.
- **Cần chốt tài liệu:** hai mô tả chưa đồng nhất, không tự sửa thay nhóm.

Mức độ: P1 là ảnh hưởng lớn đến khai thác/tích hợp hoặc tính toàn vẹn; P2 là thiếu chức năng/khả năng truy vết hoặc ảnh hưởng có điều kiện. Không phát hiện lỗi P0 đã được tái hiện trong lượt chỉ đọc này; điều đó không chứng minh không có P0.

## 3. Các điểm thiếu và khác đã có bằng chứng

### BA-01 — P2 — Không nhập được kỹ thuật viên, đơn vị sửa và loại dịch vụ trên form xe điện

**Chuẩn tài liệu:** NV mục 8 liệt kê khả năng lưu `technician_id`, `vendor_id`, `service_type_id`; mục 13 nêu danh mục/liên hệ dùng cho kỹ thuật viên và nhà cung cấp.

**Hiện trạng:** form bảo dưỡng đang chạy không có trường `technician_id`. `vendor_id` và `service_type_id` có trong cấu trúc form nhưng có điều kiện `invisible="is_electric_motorbike"`, nên bị ẩn đúng với xe thuộc nghiệp vụ đang làm. Model có trường không có nghĩa người dùng nhập được trên màn hình.

**Bằng chứng:** [fleet_service.py](../custom_addons/motorbike_fleet_management/models/fleet_service.py) khai báo kỹ thuật viên; [fleet_views.xml](../custom_addons/motorbike_fleet_management/views/fleet_views.xml) dòng 168 và 180 ẩn loại dịch vụ/đơn vị. Bản `get_view` của server xác nhận cùng tình trạng; `technician_id` không xuất hiện.

**Ảnh hưởng:** nhân viên không phân công hoặc ghi nhận đầy đủ ai sửa, sửa ở đâu, dịch vụ gì bằng luồng thông thường. Loại dịch vụ mặc định không thay thế được lựa chọn của từng phiếu nếu yêu cầu cho phép chọn.

**Cách kiểm bằng tay:** mở một phiếu bảo dưỡng xe điện mới, tìm ba ô trên. Không có/không thể chọn thì ghi thiếu so với NV8.

**Khuyến nghị:** cho nhập ba trường nếu NV8 vẫn là phạm vi phải đáp ứng. GQ không liệt kê chúng trong sơ đồ; việc không có trong sơ đồ chưa tự chứng minh nhóm trưởng yêu cầu cấm hiển thị. Nếu nhóm đã chính thức bỏ chúng, cần bổ sung quyết định vào phạm vi trước khi loại lỗi này.

**Trạng thái:** đã xác minh thiếu đường nhập trên form đang chạy; việc có giữ yêu cầu NV8 khi nộp cần nhóm xác nhận nếu chỉ dùng sơ đồ GQ làm phạm vi.

### BA-02 — P2 — Người dùng không có đường thông thường để xem lịch sử ODO của xe

**Chuẩn tài liệu:** NV1 yêu cầu xem lịch sử bảo dưỡng và ODO liên quan từng xe; NV12 yêu cầu lịch sử số đo theo xe/ngày.

**Hiện trạng:** phần `button_box` chuẩn trên form bị thay bằng nút bảo dưỡng duy nhất. Nút mở ODO chuẩn không còn. Menu ODO còn bản ghi nhưng nằm dưới các nhánh chuẩn/báo cáo đang bị ẩn. Không thấy đường thay thế từ form xe điện.

**Bằng chứng:** [fleet_views.xml](../custom_addons/motorbike_fleet_management/views/fleet_views.xml) dòng 36–42 thay toàn bộ hộp nút; cùng file ẩn `fleet.fleet_vehicles` và `fleet.menu_fleet_reporting`. Cấu trúc form/menu đọc từ server xác nhận điều này.

**Ảnh hưởng:** nhìn được số km hiện tại nhưng không tra được các lần đo theo ngày bằng luồng UI được cung cấp. Việc action ODO vẫn tồn tại hoặc biết URL kỹ thuật không thay thế một chức năng tra cứu cho người dùng.

**Cách kiểm bằng tay:** mở xe → tìm nút/tab lịch sử ODO; tìm trong các menu đang được cung cấp. Phải xem được các dòng theo xe và ngày, không chỉ số hiện tại.

**Khuyến nghị:** bổ sung đường mở lịch sử ODO chuẩn có domain đúng xe; không cần xây một phân hệ ODO mới.

**Trạng thái:** đã xác minh từ form/menu đang chạy; chưa kiểm bấm một action ẩn bằng URL kỹ thuật.

### BA-03 — P2 — Sửa ODO trực tiếp trên form không có đường ghi lịch sử trong source

**Chuẩn tài liệu:** NV12 yêu cầu lưu lịch sử số đo theo xe/ngày; BS ảnh 6 yêu cầu có số ODO hiện tại lưu trên xe. Hai yêu cầu có thể cùng đáp ứng, không cần bỏ một yêu cầu.

**Hiện trạng:** field `odometer` được đổi thành `store=True, compute=None, inverse=None`. Form hiện cho nhập khi xe không `renting/maintenance`. `write()` của module không tạo bản ghi `fleet.vehicle.odometer` cho lần sửa trực tiếp. Hàm ghi log chỉ được gọi trong API giao/trả.

**Bằng chứng:** [fleet_vehicle.py](../custom_addons/motorbike_fleet_management/models/fleet_vehicle.py) dòng 12–14, 59–81, 186–208; [fleet_views.xml](../custom_addons/motorbike_fleet_management/views/fleet_views.xml) dòng 63. Trong Odoo gốc, inverse `_set_odometer` tạo lịch sử; source custom đã bỏ inverse này.

**Ảnh hưởng:** có đường cập nhật số hiện tại không để lại số đo theo ngày. Nếu chỉ tích hợp bằng `vehicle.write({'odometer': ...})` như ví dụ BS thì cũng đi qua đường này. Chỉ việc giao/trả qua API Fleet mới có ghi log trong source đang đọc.

**Cách tái hiện trên dữ liệu TEST:** ghi số log ban đầu; sửa ODO một xe đang ở bãi từ 1.000 lên 1.080 bằng form; lưu/tải lại; kiểm xem có log đúng xe/ngày/1.080 không. Lượt rà này chưa thực hiện bước ghi đó.

**Khuyến nghị:** phân biệt nhập số đầu kỳ với cập nhật số đo mới và có một cơ chế ghi lịch sử thống nhất; tránh tạo log hai lần khi API đã ghi. Kiểm cả đường Operations ghi trực tiếp.

**Trạng thái:** đường thiếu ghi log xác định từ source; quyền sửa và field lưu trực tiếp đã xác minh ở cấu trúc form/metadata server. Chưa tái hiện bằng ghi dữ liệu thật. Số log hiện có bằng 0 không được dùng riêng để kết luận đã mất lịch sử, vì chưa biết các lần nhập trước đi qua đường nào.

## 4. Rủi ro code cần tái hiện trước khi coi là đã sửa

### R-01 — P2 — Mốc bảo dưỡng có thể bị phiếu cũ ghi đè khi phiếu mới hơn được lưu trữ

**Căn cứ:** NV11 mô tả cập nhật từ hồ sơ hoàn tất phù hợp mới nhất.

**Đường code:** khi hoàn tất, [fleet_service.py](../custom_addons/motorbike_fleet_management/models/fleet_service.py) dòng 155 tìm `latest` bằng context mặc định, bỏ qua phiếu đã lưu trữ. Trong khi khi xóa ở dòng 172 lại dùng `active_test=False`, bao gồm phiếu lưu trữ. Hai cách xác định “mới nhất” không nhất quán.

**Kịch bản cần thử:** phiếu A ngày mới hơn, đã hoàn tất, mốc 01/06/2027, sau đó lưu trữ; hoàn tất phiếu B ngày cũ hơn với mốc 01/05/2027. Xem mốc xe có lùi từ tháng 6 về tháng 5 không.

**Điểm phải chốt:** phiếu lưu trữ có còn được tính là nguồn mốc mới nhất hay không. Nếu có, cần tìm bao gồm lưu trữ và thử lại. Nếu không, tài liệu cần ghi rõ quy tắc đó. Không tự gán “đã lưu trữ = chưa từng hoàn tất”.

**Trạng thái:** rủi ro xác định từ source, chưa ghi dữ liệu để tái hiện.

### R-02 — P2 — Đổi phân loại xe có thể làm hồ sơ bảo dưỡng đã xong không còn truy cập được qua UI chính

**Căn cứ:** NV1/NV8 yêu cầu xem và giữ hồ sơ phương tiện, bảo dưỡng.

**Đường code:** [fleet_vehicle.py](../custom_addons/motorbike_fleet_management/models/fleet_vehicle.py) dòng 70–74 chỉ chặn bỏ cờ xe điện khi đang thuê/bảo dưỡng hoặc có phiếu `scheduled/running`. Phiếu `done/cancelled`, và phiếu lưu trữ do search mặc định, không thuộc kiểm tra này. Action bảo dưỡng lại lọc `vehicle_id.is_electric_motorbike=True`; nút bảo dưỡng trên xe cũng ẩn khi cờ False.

**Kịch bản cần thử:** xe điện có một phiếu done, không có lịch/công việc đang mở → bỏ Xe máy điện → lưu → tìm phiếu cũ và đường mở từ form xe.

**Ảnh hưởng có thể có:** dữ liệu không bị xóa nhưng người dùng tưởng mất lịch sử, hoặc lịch sử không còn trong luồng nghiệp vụ được cung cấp. Báo cáo sửa cũ nói đã chặn khi có mọi hồ sơ, nhưng source hiện đọc chưa thể hiện điều kiện rộng như vậy.

**Trạng thái:** rủi ro từ source; chưa bấm đổi phân loại trên bản đang chạy. Quy tắc có cho đổi phân loại sau khi có lịch sử cần được nhóm chốt.

### R-03 — P1 có điều kiện — Không thấy guard xóa xe đang thuê trong source custom

**Căn cứ:** đây là rủi ro toàn vẹn nghiệp vụ, không khẳng định Word có câu cấm xóa mọi xe đang thuê. NV1 cho xóa theo quyền và ràng buộc liên quan; NV6 có đường giao không bắt buộc ODO.

**Đường code:** source `fleet_vehicle.py` có chặn `active=False` khi đang thuê, nhưng không có override `unlink()` hay `@api.ondelete` cho trạng thái thuê. ACL Fleet chuẩn cho nhóm Fleet User quyền xóa. Với xe có quan hệ bảo dưỡng/hợp đồng, khóa ngoại hoặc module khác có thể ngăn xóa; không thể dựa vào điều đó cho một xe không có các quan hệ này.

**Kịch bản cần thử trên database riêng:** tạo xe đủ điều kiện, giao qua API/Operations mà không nhập ODO và không có hồ sơ phụ; thử xóa bằng tài khoản có quyền. Không thử trên xe/chuyến dùng để demo hoặc dữ liệu cần giữ.

**Ảnh hưởng nếu tái hiện được:** xe đang ngoài đường biến mất khỏi danh mục. Đây là điểm phải kiểm trước khi tin báo cáo “đã chặn xóa xe đang thuê”.

**Trạng thái:** guard thiếu trong source đã đọc; chưa thực hiện xóa nên chưa gọi là lỗi đã tái hiện trên bản chạy.

## 5. Hai điểm cần chốt với nhóm trưởng và Giang

### Q-01 — Trả xe về available hay pending_inspection

- BS ảnh 6 minh họa khi nhận trả thì ghi `operational_status='available'`.
- NV7 mô tả Giang nhận về Chờ kiểm tra, Fleet xác nhận; API hỗ trợ cả `pending/failed/passed/maintenance`.
- API Fleet hiện có thể đáp ứng cả hai kết luận nếu bên gọi truyền đúng kết quả. Chỉ nhìn API chưa chứng minh Operations chọn đúng luồng nhóm chốt.

**Kết luận BA:** đây là khác biệt giữa tài liệu, chưa được phép gọi một trong hai là lỗi chỉ vì code chọn khác. Cần lưu quyết định cuối và kiểm ở màn hình Giang.

### Q-02 — Đoạn write trực tiếp trong Word không tương thích với guard hiện tại

- BS ảnh 6 đưa ví dụ `vehicle.write({'odometer': ..., 'operational_status': 'available'})`.
- [fleet_vehicle.py](../custom_addons/motorbike_fleet_management/models/fleet_vehicle.py) dòng 75–76 từ chối ghi thẳng từ `renting` về `available`.
- Handoff hiện yêu cầu gọi `action_return_vehicle(...)`; đó là hợp đồng tích hợp khác đoạn ví dụ Word. Không coi handoff AI là quyết định tự động thay Word.

**Ảnh hưởng:** nếu Giang áp dụng đúng đoạn minh họa Word vào xe đang thuê, đường code hiện tại sẽ từ chối; nếu Giang gọi API đúng thì có thể tránh xung đột. Database hiện không có Operations nên chưa xác nhận cách Giang đang gọi.

**Kết luận BA:** rủi ro tích hợp P1 có điều kiện. Nhóm phải chốt API chính thức và sửa thống nhất hướng dẫn hoặc cách gọi; không tự gỡ guard kỹ thuật để khớp ví dụ khi chưa rõ luồng trả xe.

## 6. Đánh giá mức đáp ứng của phần Fleet

Đây là đối chiếu theo **15 nhóm nghiệp vụ NV**, không phải tỷ lệ ca test đã chạy hay xác suất hệ thống đúng. “Có cơ chế phù hợp” nghĩa source thể hiện phần cốt lõi; không xác nhận mọi biên hoặc quyền người dùng thật đã được thực thi thành công.

| Mục NV | Nhóm nghiệp vụ | Đánh giá hiện tại | Bằng chứng/giới hạn |
| --- | --- | --- | --- |
| 1 | Hồ sơ xe | Có cơ chế cơ bản phù hợp; lịch sử ODO xem mục 12 | Model kế thừa, mã unique, copy mã/trạng thái không giữ nguyên, active và mô tả. Chưa thử CRUD ghi trong lượt này. |
| 2 | Trạng thái vận hành | Có cơ chế phù hợp | Bốn khóa trạng thái, mặc định, constraints, tracking và UI chỉ đọc. |
| 3 | Xác nhận kỹ thuật | Có cơ chế phù hợp | Kiểm xe điện/active/renting/phiếu running; ghi available/True. |
| 4 | Khóa thuê | Có cơ chế phù hợp | Bắt buộc lý do, độc lập kỹ thuật, API trả không xóa khóa. |
| 5 | Kiểm tra khoảng thuê | Có cơ chế phù hợp ở API | Kiểm static và lịch; tiếp giáp không trùng; Rental vẫn phải nối và kiểm hợp đồng. |
| 6 | API giao xe | Có cơ chế phù hợp ở API | Quyền, Fleet eligibility, chỉ available, ODO tùy chọn, đổi renting; chưa có Operations để chứng minh toàn luồng. |
| 7 | API nhận trả | Cần chốt tài liệu/tích hợp | Đủ bốn kết quả nhưng Q-01/Q-02 chưa xác nhận bên gọi. |
| 8 | Hồ sơ bảo dưỡng | Thiếu đường thao tác theo NV | BA-01: kỹ thuật viên/đơn vị/loại dịch vụ trên form. |
| 9 | Workflow bảo dưỡng | Có cơ chế phù hợp | Chuyển trạng thái, kết quả, giờ, chi phí, bảo vệ phiếu running, copy kết quả/giờ. |
| 10 | Đồng bộ bảo dưỡng và xe | Có cơ chế phù hợp | Bắt đầu/hủy/hoàn tất, nhiều phiếu chặn, vẫn cần xác nhận kỹ thuật. |
| 11 | Kỳ bảo dưỡng tiếp | Có phần cơ bản; cần kiểm biên lưu trữ | Có field, bộ lọc, cập nhật latest; R-01 chưa được loại trừ. |
| 12 | ODO hiện tại và lịch sử | Chưa đầy đủ theo đường thao tác được cung cấp | Có số hiện tại và log qua API; BA-02, BA-03. |
| 13 | Danh mục dùng chung | Có model/liên kết nền | Hãng/model và các model chuẩn được giữ; việc quản lý liên hệ sửa chữa trên UI chịu BA-01. |
| 14 | Tra cứu và giao diện | Có cơ chế cơ bản phù hợp | Kanban/list/form, tìm/lọc/nhóm trong XML; chưa bấm hết bộ lọc trong lượt này. |
| 15 | Phân quyền | Cấu hình cơ bản phù hợp | ACL chuẩn, kỹ thuật viên thêm/sửa/đọc, không tự cấp xóa; method có check_access. Chưa đăng nhập từng vai trò để nghiệm thu. |

Tổng hợp cách phân loại trên: **11/15 nhóm có cơ chế cốt lõi phù hợp theo đọc code; 3/15 nhóm có thiếu sót hoặc biên chưa giải quyết (8, 11, 12); 1/15 cần chốt quy trình (7)**. Các nhóm có thể liên quan cùng một lỗi, nên không dùng tỷ lệ này để ước lượng phần trăm chức năng chạy đúng.

**Đánh giá BA:** phần Fleet đã có nền nghiệp vụ tương đối đầy đủ, nhưng chưa đạt điều kiện xác nhận đúng hoàn toàn theo toàn bộ tài liệu đã giao. Riêng toàn hệ thống bốn phân hệ: **chưa đủ dữ liệu để chấm phần trăm chính xác** vì bản đang chạy không chứa ba phân hệ còn lại và chưa có kết quả kiểm liên thông. Số kiểm thử AI cũ đạt 54/54 không thay thế việc đối chiếu này.

## 7. Thứ tự xử lý trước khi nộp

1. Xác định bản nộp là module Fleet hay bản tích hợp cả nhóm. Nếu là bản tích hợp, phải có địa chỉ/database/source chứa đủ ba module còn lại rồi mới kiểm liên thông.
2. Chốt Q-01/Q-02 với nhóm trưởng và Giang; thử một lượt giao → trả → kiểm tra kỹ thuật bằng tài khoản thật trên bản tích hợp.
3. Xác nhận BA-01 còn thuộc yêu cầu nộp; nếu có thì phải có đường nhập ba trường theo NV8.
4. Bổ sung/kiểm lại lịch sử ODO: xem theo xe/ngày, ghi khi cập nhật số đo, không log trùng.
5. Tái hiện R-01/R-02/R-03 trên bản thử, ghi đúng bằng chứng rồi mới sửa; không gán các rủi ro thành lỗi chắc chắn trên dữ liệu hiện tại.
6. Sau sửa, chạy lại các ca bị ảnh hưởng trong [bộ kiểm phần Bắc](TEST_TAY_PHAN_BAC.md), bổ sung ca ODO/lưu trữ như báo cáo; giữ nguyên kết quả Chưa kiểm được nếu chưa có bản tích hợp.

Lượt này chỉ báo cáo, không sửa source hay thay đổi dữ liệu nghiệp vụ.

## 8. Bằng chứng lưu cùng dự án

- [Metadata/form/module trên bản chạy](../archive/ba-audit-20261016/runtime_readonly.json): ghi thời điểm UTC, Odoo, database, module, model, cấu trúc form, thông tin copy và menu.
- [Snapshot source](../archive/ba-audit-20261016/source/custom_addons/motorbike_fleet_management/models/fleet_vehicle.py): source đã đọc, có SHA-256 trong JSON bằng chứng; không phải một bản dự án chính mới.
- [Văn bản NV trích để tra cứu](../archive/ba-audit-20261016/nghiep_vu_text.txt).
- [Kiểm tra chỉ đọc dữ liệu dự kiến sao chép](../archive/ba-audit-20261016/copy_preview_readonly.json): không gọi `copy/create`; kết quả không mang biển số cũ trong preview. Vì vậy lượt này **không kết luận lỗi sao chép biển số**, dù metadata `copied=True` ban đầu làm phát sinh nghi vấn. Không dùng một tín hiệu riêng lẻ để báo lỗi chắc chắn.

Tại lần đọc metadata, database có 42 xe, 302 phiếu bảo dưỡng, 0 log ODO; đây là số chụp tại thời điểm đọc, không phải kết quả kiểm bảo toàn dữ liệu hoặc bằng chứng người dùng đã làm mất log. Người dùng có thể vẫn đang test song song.
