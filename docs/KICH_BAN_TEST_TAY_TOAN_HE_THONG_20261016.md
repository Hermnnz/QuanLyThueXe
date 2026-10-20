# Kịch bản kiểm thử bằng tay toàn hệ thống thuê xe điện

Ngày soạn: 16/10/2026. Địa chỉ người dùng cung cấp: http://localhost:8072/. Người thực hiện: bạn và các thành viên theo vai trò. Codex chỉ soạn tài liệu; không đăng nhập, bấm thử, tạo dữ liệu, chạy ca hay sửa mã nguồn trong đợt này.

## 1. Chuẩn kết luận đúng sai

**Tài liệu Word là chuẩn yêu cầu. Code đang chạy có thể sai. Không dùng hành vi hiện tại hoặc báo cáo kiểm thử AI làm đáp án.** Code chỉ được đọc để nhận diện điểm thao tác và rủi ro; một tính năng chưa có trong code không được tự bỏ khỏi yêu cầu Word.

Bộ này bao phủ yêu cầu đã đọc trong bốn file Word, các biên số/giờ, luồng lỗi, liên kết bốn phân hệ và rủi ro toàn vẹn dữ liệu. Đây là bộ kiểm có phạm vi xác định, không phải bảo đảm hết mọi lỗi hoặc mọi tổ hợp đầu vào. Chưa có ca nào được thực thi khi bàn giao tài liệu này.

### Nguồn yêu cầu

| Ký hiệu | Tài liệu nguồn | Cách dùng |
| --- | --- | --- |
| TT | `D:/Document/Hoc/nam4ki1/TH ERP/Tuan8/thực trạng.docx` | Nhận diện hiện trạng cũ và vấn đề liên module; không dùng thiết kế cũ để phủ định phương án sửa. |
| GQ | `D:/Document/Hoc/nam4ki1/TH ERP/Tuan8/giải quyết.docx` | DBML chuẩn hóa các liên kết và trường của cả bốn phân hệ; gồm một ảnh giải pháp. |
| BS1…BS8 | `D:/Document/Hoc/nam4ki1/TH ERP/Tuan8/giải quyết bổ sung.docx` | Ảnh số theo thứ tự xuất hiện trong Word: 1 đánh giá; 2 sơ đồ; 3 dòng tiền; 4 trường tối thiểu; 5 thu/hoàn; 6 ODO; 7 phạt trễ; 8 phân công. |
| NV1…NV15 | `D:/Document/Hoc/HeNam3/Video/nghiệp vụdocx.docx` | 15 nhóm nghiệp vụ Fleet và phần giới hạn; dùng như tài liệu người dùng cung cấp. Những chỗ khác bộ tuần 8 phải chốt, không tự suy diễn. |
| ĐK | Điều kiện để thực hiện và ghi kết quả | Chưa phải yêu cầu chức năng bổ sung. |
| RR | Ca kiểm tra rủi ro do người soạn đề xuất | Nếu Word chưa quy định, ghi quan sát/VẤN ĐỀ CẦN CHỐT; không tự gán một phương án thiết kế thành yêu cầu nhóm trưởng. |

Bản chuyển chữ để tìm nhanh: [nội dung 13 ảnh](TUAN8_NOI_DUNG_ANH_20261016.md) và [văn bản/DBML gốc](TUAN8_VAN_BAN_GOC_20261016.md). Khi có sai lệch chuyển chữ, mở Word/ảnh gốc làm chuẩn. Không lấy bản Markdown của Codex để sửa nghĩa Word.

### Những quyết định phải chốt trước khi đánh đạt

| Mã | Nội dung cần nhóm trưởng xác nhận | Điền quyết định và bằng chứng |
| --- | --- | --- |
| Q1 | BS6 minh họa trả thẳng `available`; NV7 mô tả Giang trả `pending_inspection`, Bắc kiểm tra rồi xác nhận. Chốt luồng trả bình thường, ai được kết luận đạt, xử lý lỗi/pin yếu. | CHƯA CHỐT: … |
| Q2 | BS1 đề nghị một hợp đồng một xe hoặc nhiều xe cùng giao/trả. Chốt phương án nhóm dùng; trả từng phần thuộc hay ngoài phạm vi. | CHƯA CHỐT: … |
| Q3 | Trạng thái hợp đồng nào giữ chỗ; nháp/hủy/done xử lý thế nào; hai hợp đồng tiếp giáp có cho phép không. Không mặc định khoảng của Fleet là quy tắc của Contract. | CHƯA CHỐT: … |
| Q4 | Cách tính ngày thuê/min/max, trường hợp lẻ ngày, cọc 0/âm; độ chính xác giây khi trễ 15 phút 1 giây. Quy tắc mẫu 10/15/16/60/65 phút thì đã có trong BS7. | CHƯA CHỐT: … |
| Q5 | ODO/pin có bắt buộc lúc giao/trả không; thiếu khác 0 ra sao; có cho sửa số đo đã xác nhận và ai được sửa. NV cho phép thiếu ODO ở API, BS yêu cầu snapshot; chốt yêu cầu màn hình. | CHƯA CHỐT: … |
| Q6 | Mã trễ `LATE_FEE` (BS3) hay `LATE_HOUR` (BS8); giá/đơn vị phạt pin; quy tắc bên gây lỗi/bồi thường, đổi xe và sửa sự cố sau kết thúc. | CHƯA CHỐT: … |
| Q7 | Khi nào thu cọc: ký hay giao; điều kiện chặn giao khi chưa thu; trạng thái Payment có hiệu lực; số dư 0, phí đã trả riêng, hủy sau thu, thời điểm Done sau hoàn tiền. | CHƯA CHỐT: … |
| Q8 | Quyền Contract/Operations/Finance; trạng thái Charge hiệu lực; sửa giá/Charge đã xác nhận, ngày áp dụng giá, precision, invoice, nhiều công ty và những trường NV có nhưng sơ đồ GQ không nêu. | CHƯA CHỐT: … |

Chỗ có đáp án Word rõ ràng thì kiểm theo Word ngay. Chỗ phụ thuộc Q chưa chốt: vẫn có thể làm bước chuẩn bị/quan sát, nhưng kết quả cuối ghi BLOCKED/CẦN CHỐT. Không chọn đáp án chỉ vì code đang chạy như vậy. Không tự coi một file mới hơn là quyết định hủy mọi quy tắc ở file khác.

## 2. Cách sử dụng

1. Mở ứng dụng tại http://localhost:8072/. Chỉ chạy các bước trong tài liệu bằng tay, trên dữ liệu TEST/bản thử đã được phép. Không chạy script validate/seed/upgrade để làm theo tài liệu này.
2. Điền môi trường và quyết định Q ở [sổ kết quả](KET_QUA_TEST_TAY_20261016.md). Địa chỉ 8072 chưa chứng minh đã có đủ bốn phân hệ. Nếu thiếu module/nút/trường bắt buộc, ghi FAIL khi đúng bản có nghĩa vụ cung cấp; ghi BLOCKED khi chưa có bản tích hợp để kiểm. Tuyệt đối không PASS vì không thử được.
3. Chuẩn bị các bộ dữ liệu bên dưới. Mỗi ca gây thay đổi dùng phiếu/chuyến riêng hoặc làm lại đúng điều kiện; không dùng trạng thái đầu ra của ca trước một cách vô thức.
4. Làm các bước theo thứ tự dấu chấm phẩy. Sau xác nhận, tải lại và mở cả bản ghi liên quan để kiểm dữ liệu thực sự đã lưu.
5. Ghi kết quả thực tế, mã xe/hợp đồng/phiếu/tiền, ảnh, ngày giờ, người thử. Một ca có nhiều biến thể chỉ PASS khi mọi biến thể đã thử và đúng; nếu chưa đủ ghi PARTIAL. Có thể tách dòng kết quả theo mã như `MNT-04.a/b/c`.
6. Không chỉnh code, xóa ràng buộc, đổi ngày giờ máy hoặc sửa SQL để ép đạt. Một số biên giờ cần trường nhập thời gian thực tế; nếu UI tự ghi giờ và không cho chỉnh, dùng lịch hẹn thích hợp trên bản thử hoặc nhờ người phụ trách chuẩn bị dữ liệu rồi bạn kiểm UI. Nếu chưa thể làm, ghi BLOCKED, không coi ca đã chạy.

### Trạng thái ghi nhận

| Trạng thái | Ý nghĩa |
| --- | --- |
| NOT_RUN | Chưa làm; mặc định toàn bộ bộ này. |
| PASS | Đã tự làm đủ bước/biến thể, kết quả khớp Word hoặc quyết định nhóm trưởng có bằng chứng. |
| FAIL | Kết quả thực tế khác yêu cầu đã xác định; ghi bước đầu sai và bằng chứng. |
| BLOCKED | Chưa chạy/kết luận được vì thiếu module, dữ liệu, quyền, màn hình, môi trường hoặc quyết định Q. |
| PARTIAL | Đã thử một phần; không tính là PASS. |
| N/A | Ngoài phạm vi được nhóm trưởng xác nhận, ghi lý do/người xác nhận; không dùng để che tính năng thiếu. |

P0: có thể làm sai xe, lịch, tiền, quyền hoặc chặn demo; chạy trước. P1: kiểm đủ nghiệp vụ và biên; vẫn cần xử lý trước khi nói đã bao phủ. P0/P1 là thứ tự thử, không phải kết luận rằng bỏ P1 vẫn đáp ứng toàn bộ yêu cầu.

### Đường đi trên UI

Fleet hiện có nhóm màn hình Phương tiện/Bảo dưỡng & Sửa chữa; ba phân hệ còn lại chưa có source trong thư mục đang đọc, nên tên menu/nút mô tả theo chức năng Word. Nếu tên thật khác, ghi tên thật vào sổ. Không giả định phải có một màn hình hay nút theo đúng tên Codex đặt.

Các ca lịch và API phải kiểm từ màn hình hợp đồng/giao nhận thật nếu đã nối Fleet. Không thấy nút `check_fleet_availability` là bình thường vì đó là hàm tích hợp, không phải menu người dùng. Nếu chỉ có Fleet độc lập thì các ca liên thông chưa kiểm được và phải ghi BLOCKED.

## 3. Dữ liệu thử dùng chung

Tất cả tên/mã có tiền tố `TEST-1710-` để tách với dữ liệu đem nộp. Chữ `TEST-X01`, `TEST-HD01` trong ca là tên rút gọn của tiền tố này. Không dùng thông tin cá nhân thật.

| Dữ liệu | Giá trị chuẩn bị |
| --- | --- |
| Người dùng | Nhân/Contract, Bắc/Fleet Officer, kỹ thuật viên thuần, Giang/Operations, Đức Anh/Finance, người thường, Fleet Administrator. Ghi nhóm quyền thực tế. |
| Khách | TEST-KH01 và TEST-KH02, tên/điện thoại/CCCD/bằng lái giả. |
| Danh mục | TEST-HANG, TEST-MODEL; TEST-GIA tham chiếu model_id của Fleet, giá 300.000đ/ngày, VND. |
| Xe | X01/X02 sẵn sàng, X03 chờ kiểm tra, X04 bảo dưỡng, X05 khóa chủ động, X06 lưu trữ. Xe đang thuê được tạo bằng giao thật trên chuyến TEST, không sửa tay trạng thái. |
| Chuẩn kỹ thuật | Dùng xe đã được kiểm tra, xác nhận đúng luồng; có lý do khi khóa; ODO ban đầu 1.000km nếu đã có cách nhập/chuẩn bị hợp lệ. |
| Mốc D | Ngày thử do bạn ghi: …; mọi thời gian trong kịch bản là giờ hiển thị Asia/Bangkok. `D+1`, `D+2` là ngày kế tiếp; nếu lịch nằm quá khứ bị chặn, chọn mốc khác và giữ khoảng cách/đáp án. |
| Hợp đồng chuẩn | D 10:00 đến D+2 10:00; giá 300.000đ/ngày; tiền thuê ví dụ 600.000đ khi quy tắc ngày đã chốt; cọc 2.000.000đ. Không tự đổi tiền thuê nếu Q4 chưa chốt. |
| Số đo | ODO đầu 1.000, cuối 1.080; pin đầu 90%, cuối bình thường 60%; pin thấp 19%, biên 20%. |
| Bảo dưỡng | Xe đủ điều kiện, lịch D 10:00–12:00; loại/chi phí/kết quả theo ca; tách xe này khỏi xe hợp đồng mẫu nếu không kiểm giao nhau. |
| Giá phụ phí để tính tay | Trễ 50.000đ/giờ theo ví dụ Word; pin TEST=150.000đ/lần và bồi thường TEST=200.000đ/lần chỉ là dữ liệu thử do nhóm cho phép cấu hình, không phải giá pin/bồi thường đã được Word ấn định. |
| Trạng thái tiền | Ghi rõ nháp/xác nhận/hủy và trạng thái nào Q7/Q8 quy định có hiệu lực. Chưa thu thật không đánh đã thu chỉ vì ticket có checkbox. |

Không coi việc khai báo ODO ban đầu 1.000 là một nút có sẵn trên form Fleet. Nếu form chỉ đọc, chuẩn bị qua luồng nhập có quyền hoặc nhờ người phụ trách tạo dữ liệu TEST hợp lệ; bạn vẫn chỉ dùng UI để chạy các bước được phép.

## 4. Đáp án tính tay

- Hai khoảng bảo dưỡng/thuê theo NV tiếp giáp không trùng: thuê kết thúc 10:00, sửa bắt đầu 10:00 thì không giao nhau. Hiệu lực hợp đồng và quy tắc tiếp giáp Contract xem Q3.
- Phạt trễ theo BS7: trễ ≤15 phút → 0; trễ >15 phút → `ceil(toàn bộ phút trễ / 60)`. Không trừ 15 phút khi đã vượt ngưỡng. 10 phút=0đ; 15 phút=0đ; 16 phút=50.000đ; 60 phút=50.000đ; 65 phút=100.000đ.
- Theo kịch bản BS5 đã thu đủ thuê và cọc: phụ phí C, cọc D; nếu C<D thì hoàn D-C; C>D thì thu thêm C-D; C=D xử lý số dư 0 theo Q7.
- Kiểm tra tiền khi đã quyết toán xong: `tổng mọi khoản thực thu - tổng mọi khoản thực hoàn = tiền thuê + toàn bộ phụ phí có hiệu lực`, với dữ liệu thử không có điều chỉnh khác. Tổng thực thu bao gồm tiền thuê, cọc, thu thêm và phụ phí đã trả riêng nếu có; không tính tiền nháp hoặc khoản chưa thu. Phụ phí đã trả riêng không được trừ cọc lần hai.
- Ví dụ chuẩn: thuê 600.000đ, cọc 2.000.000đ; phí 0 → hoàn 2.000.000đ; phí 250.000đ → hoàn 1.750.000đ; phí 3.500.000đ → thu thêm 1.500.000đ.
- Tiền sửa bảo dưỡng nội bộ không tự động là tiền khách phải bồi thường. Phải có sự cố, bên có lỗi/quyết định và Charge theo Q6.

## 5. Lượt kiểm ưu tiên trước khi nộp

Lượt ngắn này giúp phát hiện lỗi lớn trước; không thay thế toàn bộ ca bên dưới. Dừng và ghi lỗi ngay khi dữ liệu tiền/xe sai; không nối tiếp bằng sửa trạng thái tay.

1. ENV-01…ENV-06: đúng bản, backup, đủ module/quyền và quyết định còn thiếu.
2. REF-01…REF-02, FLT-01…FLT-03, FLT-06, FLT-09…FLT-10: danh mục, xe, trùng mã, kỹ thuật, khóa.
3. MNT-03, MNT-08, MNT-11…MNT-14: lịch, bắt đầu, thiếu kết quả, hoàn tất/hủy và hai phiếu.
4. AVL-04, AVL-09…AVL-11, AVL-15: giao nhau, tiếp giáp, running quá giờ và tab cũ.
5. CON-02…CON-06, OPS-02, OPS-05, OPS-07…OPS-11, ODO-03…ODO-04: ngày giờ, giá snapshot, giữ chỗ, giao/trả/lặp, số đo.
6. FIN-07…FIN-10, FIN-14…FIN-20, INC-02…INC-04: ngưỡng trễ, pin, tính tiền, hoàn/thu thêm, chống phí trùng.
7. E2E-01…E2E-04, ACL-05, REP-01…REP-04: cả hệ thống, tài khoản thật, hai phiên và thao tác cũ.
8. Chạy mọi ca còn lại và ghi mọi biến thể trước khi kết luận đã kiểm theo toàn bộ tài liệu.

## 6. Ma trận yêu cầu và nơi kiểm

| Nhóm yêu cầu Word | Nhóm ca |
| --- | --- |
| NV1 hồ sơ, NV2 trạng thái, NV3 xác nhận, NV4 khóa | FLT; ACL; E2E |
| NV5 khả dụng và lịch | AVL; CON; REP |
| NV6 giao, NV7 trả | OPS; ODO; E2E |
| NV8 hồ sơ sửa, NV9 workflow, NV10 đồng bộ, NV11 kỳ tiếp | MNT; AVL; FLT |
| NV12 ODO | ODO; OPS; E2E |
| NV13 danh mục, NV14 tra cứu, NV15 quyền | REF; UI; ACL |
| GQ khách và tài liệu khách | REF |
| GQ loại xe/model, hợp đồng/dòng, tiền tệ | REF; CON; FIN |
| GQ ticket, dòng xe, sự cố, thay xe và các FK | OPS; INC; CON; E2E |
| GQ bảng giá, khoản phí, thanh toán, invoice liên kết | REF; FIN; UI |
| BS1 chín vấn đề, BS2 sơ đồ | CON; OPS; INC; FIN; E2E |
| BS3 dòng tiền, BS4 trường tối thiểu, BS5 quyết toán | ODO; OPS; FIN; INC |
| BS6 code minh họa ODO, BS7 phạt, BS8 phân công | ODO; FIN; FLT; CON; INC |
| Bấm lặp, đồng thời, lỗi giữa chừng | INC; FIN; REP; E2E — một phần RR, không giả là nguyên văn Word |
| Phạm vi không có pin asset/kho/checklist phức tạp | SCP |

Các kịch bản bao phủ hành vi UI và liên kết truy vết. Kiểm tay không chứng minh loại dữ liệu SQL, UNIQUE thực ở database, an toàn mọi RPC/import hay mọi giao dịch đồng thời. Nếu cần chứng minh các thuộc tính kỹ thuật đó, ghi riêng việc phải có bằng chứng kỹ thuật; không ghi đạt chỉ từ nhãn trên form. Đợt này không chạy thêm công cụ kiểm hệ thống.

## 7. Danh sách chi tiết


Tổng số: **207 ca**; P0: **141**; P1: **66**. Các biến thể bên trong ca cần ghi riêng nếu kết quả khác nhau.

| Nhóm | Nội dung | Số ca |
| --- | --- | ---: |
| ENV | Xác định đúng bản và chuẩn bị | 8 |
| REF | Danh mục và khách hàng | 10 |
| FLT | Hồ sơ xe và điều kiện kỹ thuật | 16 |
| ODO | ODO và số đo chuyến | 12 |
| MNT | Bảo dưỡng và sửa chữa | 26 |
| AVL | Khoảng thuê và lịch bảo dưỡng | 16 |
| CON | Hợp đồng và giữ chỗ | 18 |
| OPS | Giao xe và nhận trả | 21 |
| INC | Sự cố và thay xe | 10 |
| FIN | Khoản phí, thanh toán và quyết toán | 27 |
| E2E | Luồng xuyên cả bốn phân hệ | 12 |
| ACL | Phân quyền bằng tài khoản thực | 10 |
| REP | Thao tác lặp, dữ liệu cũ và gián đoạn | 8 |
| UI | Tra cứu và trình bày để demo | 7 |
| SCP | Biên phạm vi và chuẩn bị nộp | 6 |

### ENV — Xác định đúng bản và chuẩn bị

Nguồn: ĐK.

Nơi thao tác: Trình duyệt và thông tin môi trường.

#### ENV-01 · P0 · Mở đúng địa chỉ

- **Chuẩn bị:** Chưa đăng nhập.
- **Thao tác:** Mở http://localhost:8072/; đăng nhập tài khoản thử; chụp thanh địa chỉ và tên người dùng.
- **Mong đợi theo tài liệu:** Trang tải được; ghi lại đúng địa chỉ và database, không suy ra đủ bốn phân hệ chỉ từ cổng 8072.
- **Ghi kết quả:** dòng `ENV-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ENV-02 · P0 · Xác định module có thể kiểm

- **Chuẩn bị:** Tài khoản quản trị của bản thử.
- **Thao tác:** Mở danh sách ứng dụng đã cài và menu; tìm Đội xe, Hợp đồng, Vận hành, Tài chính.
- **Mong đợi theo tài liệu:** Ghi Có/Không cho từng phân hệ. Phân hệ thiếu được ghi BLOCKED ở các ca tương ứng, không ghi PASS.
- **Ghi kết quả:** dòng `ENV-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ENV-03 · P0 · Chốt bản đem nộp

- **Chuẩn bị:** Ứng dụng đang dùng.
- **Thao tác:** Ghi phiên bản Odoo, database, phiên bản từng module nếu xem được; ghi thời điểm bắt đầu; chụp thông tin.
- **Mong đợi theo tài liệu:** Xác định được bản đang kiểm. Nếu không xem được, ghi CHƯA XÁC ĐỊNH; không đoán là Odoo 18/19.
- **Ghi kết quả:** dòng `ENV-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ENV-04 · P0 · Bảo vệ dữ liệu trước test

- **Chuẩn bị:** Có người quản lý database.
- **Thao tác:** Xác nhận đã có bản sao/backup và cách khôi phục được người phụ trách kiểm tra; chỉ đặt mã TEST cho dữ liệu mới.
- **Mong đợi theo tài liệu:** Có tên bản sao, ngày và người giữ; không thử xóa hoặc phát sinh thanh toán trên dữ liệu cần giữ.
- **Ghi kết quả:** dòng `ENV-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ENV-05 · P0 · Chuẩn bị người dùng theo vai trò

- **Chuẩn bị:** Có quyền cấu hình người dùng trong bản thử.
- **Thao tác:** Tạo/chọn tài khoản Nhân, Bắc, Giang, Đức Anh, kỹ thuật viên và người thường; ghi nhóm quyền thực tế.
- **Mong đợi theo tài liệu:** Có tài khoản riêng theo vai trò; tài khoản dùng chung admin không thay thế kiểm quyền.
- **Ghi kết quả:** dòng `ENV-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ENV-06 · P0 · Chốt các điểm mâu thuẫn tài liệu

- **Chuẩn bị:** Có bảng câu hỏi ở đầu bộ test.
- **Thao tác:** Điền quyết định nhóm trưởng cho Q1–Q8; lưu ngày và bằng chứng trả lời.
- **Mong đợi theo tài liệu:** Chỉ đánh PASS các ca phụ thuộc sau khi có quyết định; chưa chốt thì BLOCKED, không lấy code làm chuẩn.
- **Ghi kết quả:** dòng `ENV-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ENV-07 · P1 · Múi giờ và tiền tệ

- **Chuẩn bị:** Hai người dùng trong bản thử.
- **Thao tác:** Kiểm tra múi giờ Asia/Bangkok và VND; mở cùng lịch thuê ở hai tài khoản.
- **Mong đợi theo tài liệu:** Giờ nghiệp vụ thống nhất; tiền VND; nếu thiết lập khác phải ghi rõ trước khi so sánh.
- **Ghi kết quả:** dòng `ENV-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ENV-08 · P0 · Kiểm tra lại sau đóng/mở trình duyệt

- **Chuẩn bị:** Có bản ghi TEST đã lưu.
- **Thao tác:** Đăng xuất; đóng tab; mở lại 8072; tìm mã TEST.
- **Mong đợi theo tài liệu:** Đọc được dữ liệu đã lưu; không phụ thuộc tab còn mở hoặc dữ liệu nháp.
- **Ghi kết quả:** dòng `ENV-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### REF — Danh mục và khách hàng

Nguồn: TT, GQ, BS1, BS8.

Nơi thao tác: Danh mục Fleet, khách hàng và bảng giá thuê của Contract.

#### REF-01 · P0 · Tạo hãng và dòng xe dùng chung

- **Chuẩn bị:** Bắc có quyền danh mục.
- **Thao tác:** Tạo hãng TEST-HANG; tạo TEST-MODEL gắn hãng và loại phương tiện; mở lại.
- **Mong đợi theo tài liệu:** Lưu đúng tên/hãng/loại; xe và Contract có thể tham chiếu cùng dòng xe.
- **Ghi kết quả:** dòng `REF-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REF-02 · P0 · Loại xe thuê liên kết mẫu Fleet

- **Chuẩn bị:** TEST-MODEL đã có.
- **Thao tác:** Nhân tạo nhóm giá TEST-GIA; chọn model_id TEST-MODEL; mở lại.
- **Mong đợi theo tài liệu:** Liên kết tới mẫu Fleet thật; không chỉ nhập lại hãng/dòng bằng text rời.
- **Ghi kết quả:** dòng `REF-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REF-03 · P1 · Cập nhật tên mẫu dùng chung

- **Chuẩn bị:** Một mẫu TEST đang được xe và loại thuê tham chiếu.
- **Thao tác:** Đổi tên mẫu; tải lại cả hai màn hình.
- **Mong đợi theo tài liệu:** Vẫn tham chiếu cùng bản ghi, không phát sinh mẫu mới hay mất liên kết.
- **Ghi kết quả:** dòng `REF-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REF-04 · P1 · Lưu trữ hãng/dòng đang tham chiếu

- **Chuẩn bị:** Chỉ dùng danh mục TEST.
- **Thao tác:** Lưu trữ dòng; mở xe/hợp đồng cũ; tìm trong lựa chọn mới; khôi phục.
- **Mong đợi theo tài liệu:** Lịch sử không mất; hành vi chọn mới theo quy ước lưu trữ đã chốt, không phá bản ghi cũ.
- **Ghi kết quả:** dòng `REF-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REF-05 · P0 · Tạo khách thuê

- **Chuẩn bị:** Nhân đăng nhập.
- **Thao tác:** Tạo TEST-KH01 với tên, điện thoại, email, CCCD, bằng lái và ghi chú; bật khách thuê; lưu/mở lại.
- **Mong đợi theo tài liệu:** Các thông tin của khách được giữ đúng và gắn cùng res_partner.
- **Ghi kết quả:** dòng `REF-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REF-06 · P0 · Dùng chung khách giữa các phân hệ

- **Chuẩn bị:** TEST-KH01 đã có.
- **Thao tác:** Chọn khách trên hợp đồng, phiếu tiền và khoản phí; mở liên kết khách từng nơi.
- **Mong đợi theo tài liệu:** Cùng khách hàng; không tạo ba khách trùng chỉ vì khác module.
- **Ghi kết quả:** dòng `REF-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REF-07 · P1 · Tài liệu khách hàng

- **Chuẩn bị:** Khách TEST có file giả, không dùng CCCD thật.
- **Thao tác:** Thêm tên, tên file, ngày và ghi chú theo màn hình; tải lại file nếu chức năng có.
- **Mong đợi theo tài liệu:** Liên kết đúng khách; thông tin và file đọc lại đúng; thiếu chức năng theo Word ghi FAIL/BLOCKED theo nguyên nhân.
- **Ghi kết quả:** dòng `REF-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REF-08 · P1 · Thiếu dữ liệu bắt buộc khách/tài liệu

- **Chuẩn bị:** Bản nháp TEST.
- **Thao tác:** Lần lượt bỏ tên khách; bỏ tên/tên file/ngày của tài liệu; bấm lưu.
- **Mong đợi theo tài liệu:** Các trường [not null] theo GQ được kiểm soát; báo rõ, không tạo bản ghi rỗng.
- **Ghi kết quả:** dòng `REF-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REF-09 · P0 · Danh mục giá tiền

- **Chuẩn bị:** Đức Anh đăng nhập.
- **Thao tác:** Tạo các mã trễ giờ đã chốt, BATTERY_CHARGE, COMPENSATION; nhập VND, đơn vị, ngày hiệu lực, giá.
- **Mong đợi theo tài liệu:** Có mã/loại/đơn vị/giá đúng quyết định; ví dụ trễ 50.000đ/giờ; không dùng đồng thời hai mã cho một khoản.
- **Ghi kết quả:** dòng `REF-09` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REF-10 · P1 · Không phá lịch sử khi sửa danh mục

- **Chuẩn bị:** Có dòng hợp đồng đã chốt và Charge TEST.
- **Thao tác:** Đổi tên hoặc giá danh mục; mở lại chứng từ cũ.
- **Mong đợi theo tài liệu:** Giá snapshot hợp đồng cũ không tự đổi; chính sách giá Charge cũ theo Q8; lịch sử còn truy vết được.
- **Ghi kết quả:** dòng `REF-10` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### FLT — Hồ sơ xe và điều kiện kỹ thuật

Nguồn: NV1–4, NV13–15; GQ Fleet; BS8.

Nơi thao tác: Đội xe → Phương tiện và form xe.

#### FLT-01 · P0 · Tạo xe mới

- **Chuẩn bị:** TEST-MODEL có sẵn.
- **Thao tác:** Tạo TEST-X01, biển số giả, chọn dòng, ngày đưa vào dùng, mô tả; lưu rồi mở lại.
- **Mong đợi theo tài liệu:** Thông tin đúng; xe mới Chờ kiểm tra, chưa đạt kỹ thuật theo NV; chưa được tự coi là cho thuê được.
- **Ghi kết quả:** dòng `FLT-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-02 · P0 · Mã xe trùng đang hoạt động

- **Chuẩn bị:** Đã có TEST-X01.
- **Thao tác:** Tạo xe thứ hai cùng mã TEST-X01; lưu.
- **Mong đợi theo tài liệu:** Bị từ chối; không có hai xe cùng mã đã cấp.
- **Ghi kết quả:** dòng `FLT-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-03 · P0 · Mã xe trùng xe lưu trữ

- **Chuẩn bị:** Có xe TEST-ARCH đã lưu trữ.
- **Thao tác:** Tạo xe mới mã TEST-ARCH.
- **Mong đợi theo tài liệu:** Bị từ chối; mã của xe lưu trữ vẫn được giữ duy nhất theo NV.
- **Ghi kết quả:** dòng `FLT-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-04 · P1 · Sao chép hồ sơ xe

- **Chuẩn bị:** TEST-X01 đã xác nhận kỹ thuật.
- **Thao tác:** Sao chép xe; xem mã và điều kiện kỹ thuật trước/sau lưu.
- **Mong đợi theo tài liệu:** Không mang nguyên mã và trạng thái đạt kỹ thuật sang xe mới; phải kiểm tra xe mới riêng.
- **Ghi kết quả:** dòng `FLT-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-05 · P1 · Sửa hồ sơ và mô tả chung

- **Chuẩn bị:** Xe TEST chưa có chuyến.
- **Thao tác:** Đổi biển số/mô tả/ngày sử dụng; lưu; tải lại.
- **Mong đợi theo tài liệu:** Thông tin mới đúng; không tự đổi trạng thái thuê hoặc tạo phiếu sự cố.
- **Ghi kết quả:** dòng `FLT-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-06 · P0 · Xác nhận đạt kỹ thuật

- **Chuẩn bị:** Xe TEST đang Chờ kiểm tra, hoạt động, không bảo dưỡng chạy.
- **Thao tác:** Bấm Xác nhận đạt kỹ thuật; mở lại form và Kanban.
- **Mong đợi theo tài liệu:** Xe Sẵn sàng/available, technical_ready=True.
- **Ghi kết quả:** dòng `FLT-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-07 · P0 · Không xác nhận khi đang thuê

- **Chuẩn bị:** Xe đã giao qua ca OPS.
- **Thao tác:** Mở xe; thử tìm/bấm xác nhận kỹ thuật nếu có.
- **Mong đợi theo tài liệu:** Không được chuyển xe đang thuê thành Sẵn sàng; nút ẩn hoặc bị từ chối.
- **Ghi kết quả:** dòng `FLT-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-08 · P0 · Không xác nhận khi đang sửa chặn thuê

- **Chuẩn bị:** Xe có phiếu running, blocks_rental=True.
- **Thao tác:** Thử xác nhận kỹ thuật.
- **Mong đợi theo tài liệu:** Từ chối; xe vẫn Bảo dưỡng và chưa đạt kỹ thuật.
- **Ghi kết quả:** dòng `FLT-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-09 · P0 · Khóa thuê phải có lý do

- **Chuẩn bị:** Xe TEST đang sẵn sàng.
- **Thao tác:** Bật Khóa thuê; để trống rồi chỉ nhập khoảng trắng ở lý do; thử lưu từng lần.
- **Mong đợi theo tài liệu:** Đều bị từ chối; sau nhập lý do hợp lệ mới lưu được.
- **Ghi kết quả:** dòng `FLT-09` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-10 · P0 · Khóa thuê khác kỹ thuật

- **Chuẩn bị:** Xe sẵn sàng.
- **Thao tác:** Khóa với lý do Kiểm kê; lưu; thử chọn/giao trong hệ thống.
- **Mong đợi theo tài liệu:** Vẫn thể hiện đạt kỹ thuật nhưng không được giao/cho thuê theo điều kiện Fleet.
- **Ghi kết quả:** dòng `FLT-10` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-11 · P0 · Xác nhận kỹ thuật không xóa khóa

- **Chuẩn bị:** Xe khóa chủ động và đủ điều kiện kiểm tra.
- **Thao tác:** Xác nhận đạt kỹ thuật; mở lại lý do khóa.
- **Mong đợi theo tài liệu:** Giữ rental_blocked và lý do; không tự mở khóa.
- **Ghi kết quả:** dòng `FLT-11` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-12 · P0 · Mở khóa chủ động

- **Chuẩn bị:** Xe khóa, sẵn sàng, không lịch chặn.
- **Thao tác:** Bỏ Khóa thuê; lưu; kiểm tra điều kiện thuê lại.
- **Mong đợi theo tài liệu:** Xe được xét thuê lại; lịch bảo dưỡng/điều kiện khác vẫn phải kiểm tra độc lập.
- **Ghi kết quả:** dòng `FLT-12` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-13 · P1 · Lưu trữ và khôi phục xe

- **Chuẩn bị:** Xe TEST không thuộc chuyến đang diễn ra.
- **Thao tác:** Lưu trữ; tìm bộ lọc lưu trữ; khôi phục.
- **Mong đợi theo tài liệu:** Ẩn khỏi lựa chọn hoạt động; lịch sử vẫn có; khôi phục đúng xe, không tạo bản sao.
- **Ghi kết quả:** dòng `FLT-13` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-14 · P0 · Không khai thác xe lưu trữ

- **Chuẩn bị:** Xe TEST đã lưu trữ.
- **Thao tác:** Thử chọn trên hợp đồng/giao xe/xác nhận kỹ thuật.
- **Mong đợi theo tài liệu:** Không cho khai thác xe lưu trữ; không mất dữ liệu liên quan.
- **Ghi kết quả:** dòng `FLT-14` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-15 · P0 · Trạng thái không sửa bằng kéo thả

- **Chuẩn bị:** Kanban có xe TEST.
- **Thao tác:** Thử kéo thẻ qua cột khác; thử sửa trực tiếp trạng thái/cờ kỹ thuật trên form.
- **Mong đợi theo tài liệu:** Không đổi trực tiếp trên UI theo NV; dùng thao tác nghiệp vụ. Chỉ đọc trên UI không đủ chứng minh server an toàn.
- **Ghi kết quả:** dòng `FLT-15` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FLT-16 · P1 · Xem bảo dưỡng đúng xe

- **Chuẩn bị:** Hai xe TEST, mỗi xe có phiếu riêng.
- **Thao tác:** Từ form TEST-X01 mở lịch sử bảo dưỡng.
- **Mong đợi theo tài liệu:** Chỉ phiếu đúng xe; tạo mới từ đây gắn đúng xe, không lẫn TEST-X02.
- **Ghi kết quả:** dòng `FLT-16` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### ODO — ODO và số đo chuyến

Nguồn: NV6–7, NV12; BS6, BS8.

Nơi thao tác: Form xe, dòng giao/trả Operations; lịch sử ODO nếu có màn hình.

#### ODO-01 · P0 · Ghi ODO lúc giao

- **Chuẩn bị:** Xe có ODO 1.000, chuyến hợp lệ.
- **Thao tác:** Nhập ODO giao 1.000; xác nhận giao; mở lại xe và dòng chuyến.
- **Mong đợi theo tài liệu:** Dòng giữ 1.000; xe không giảm ODO; không làm mất lịch sử đã có.
- **Ghi kết quả:** dòng `ODO-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ODO-02 · P0 · Ghi ODO lúc trả

- **Chuẩn bị:** Chuyến giao ODO 1.000 đang diễn ra.
- **Thao tác:** Trả với ODO 1.080; mở lại dòng trả và xe.
- **Mong đợi theo tài liệu:** Xe có ODO hiện tại 1.080; đầu chuyến vẫn 1.000; dữ liệu còn sau tải lại.
- **Ghi kết quả:** dòng `ODO-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ODO-03 · P0 · Chặn ODO giao thấp hơn xe

- **Chuẩn bị:** Xe ODO 1.000.
- **Thao tác:** Nhập ODO giao 999; xác nhận.
- **Mong đợi theo tài liệu:** Từ chối; xe chưa chuyển Đang thuê; ODO và phiếu không cập nhật dở dang.
- **Ghi kết quả:** dòng `ODO-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ODO-04 · P0 · Chặn ODO trả thấp hơn đầu chuyến

- **Chuẩn bị:** Chuyến bắt đầu 1.000.
- **Thao tác:** Nhập ODO trả 999; xác nhận.
- **Mong đợi theo tài liệu:** Từ chối; không hoàn tất phiếu; xe và tiền không cập nhật một phần.
- **Ghi kết quả:** dòng `ODO-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ODO-05 · P0 · Chặn ODO trả thấp hơn ODO hiện tại

- **Chuẩn bị:** Xe/chuyến đang thử có mốc hiện tại 1.080.
- **Thao tác:** Thử trả 1.050, bằng dữ liệu TEST chuẩn bị riêng.
- **Mong đợi theo tài liệu:** Từ chối theo NV; không làm giảm số hiện tại.
- **Ghi kết quả:** dòng `ODO-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ODO-06 · P1 · ODO đầu bằng cuối

- **Chuẩn bị:** Chuyến đầu 1.000.
- **Thao tác:** Nhập cuối 1.000; xác nhận trả.
- **Mong đợi theo tài liệu:** Cho phép không phát sinh quãng đường; không bắt buộc cuối phải lớn hơn đầu.
- **Ghi kết quả:** dòng `ODO-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ODO-07 · P0 · ODO âm

- **Chuẩn bị:** Xe/chuyến TEST.
- **Thao tác:** Nhập -1 ở ODO giao rồi ở ODO trả; thử lưu/xác nhận từng lần.
- **Mong đợi theo tài liệu:** Từ chối cả hai; không lưu số âm.
- **Ghi kết quả:** dòng `ODO-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ODO-08 · P1 · ODO bằng 0 khác thiếu số đo

- **Chuẩn bị:** Xe mới ODO 0, chưa chạy.
- **Thao tác:** Giao/trả với 0 nếu màn hình cho phép; ở chuyến khác để trống theo Q5.
- **Mong đợi theo tài liệu:** 0 hợp lệ, không coi là thiếu; việc bắt buộc đo theo Q5; không ghi 0 đè số cũ khi thiếu.
- **Ghi kết quả:** dòng `ODO-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ODO-09 · P1 · ODO thập phân

- **Chuẩn bị:** Xe/chuyến TEST.
- **Thao tác:** Giao 1.000,5; trả 1.001,5; tải lại.
- **Mong đợi theo tài liệu:** Số được giữ theo độ chính xác đã cấu hình; không nhầm dấu phân cách thành 10.005/10.015.
- **Ghi kết quả:** dòng `ODO-09` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ODO-10 · P1 · Giữ snapshot đầu cuối

- **Chuẩn bị:** Hai chuyến liên tiếp cùng xe.
- **Thao tác:** Hoàn tất chuyến A 1.000→1.080 rồi B 1.080→1.150; mở lại A.
- **Mong đợi theo tài liệu:** A vẫn 1.000/1.080; xe hiện tại 1.150; trường chuyến không phải related trực tiếp làm đổi lịch sử.
- **Ghi kết quả:** dòng `ODO-10` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ODO-11 · P1 · Lịch sử ODO giảm theo ngày

- **Chuẩn bị:** Có màn hình lịch sử chuẩn; chỉ dùng dữ liệu TEST.
- **Thao tác:** Tạo mốc D=1.000, D+2=1.100; nhập D+1=1.050 rồi thử D+1=1.200.
- **Mong đợi theo tài liệu:** 1.050 hợp lệ; 1.200 bị từ chối theo NV vì vượt mốc sau. Nếu không có UI ghi BLOCKED, không sửa code để test.
- **Ghi kết quả:** dòng `ODO-11` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ODO-12 · P1 · ODO và trạng thái không cập nhật nửa chừng

- **Chuẩn bị:** Chuyến chuẩn bị trả, ODO không hợp lệ.
- **Thao tác:** Bấm xác nhận trả với ODO âm/thấp; tải lại toàn bộ xe và phiếu.
- **Mong đợi theo tài liệu:** Lỗi không để xe đã trả nhưng phiếu còn thuê, hoặc ODO đã tăng nhưng thao tác thất bại.
- **Ghi kết quả:** dòng `ODO-12` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### MNT — Bảo dưỡng và sửa chữa

Nguồn: NV8–11; GQ Fleet.

Nơi thao tác: Đội xe → Bảo dưỡng & Sửa chữa.

#### MNT-01 · P0 · Lập phiếu đầy đủ

- **Chuẩn bị:** Xe TEST hoạt động.
- **Thao tác:** Tạo phiếu với xe, ngày, nội dung, loại, ghi chú, chi phí, lịch, chặn thuê, mốc tiếp theo; lưu/mở lại.
- **Mong đợi theo tài liệu:** Giữ đầy đủ thông tin theo Word; phiếu Mới; không tự đổi xe sang Bảo dưỡng chỉ vì tạo nháp.
- **Ghi kết quả:** dòng `MNT-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-02 · P1 · Ba loại bảo dưỡng

- **Chuẩn bị:** Ba phiếu TEST riêng.
- **Thao tác:** Lần lượt chọn Định kỳ, Sửa chữa, Khẩn cấp; lưu và lọc lại.
- **Mong đợi theo tài liệu:** Lưu đúng cả ba loại; hiển thị đúng khi tra cứu.
- **Ghi kết quả:** dòng `MNT-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-03 · P0 · Lên lịch hợp lệ

- **Chuẩn bị:** Phiếu Mới, lịch D 10:00–12:00.
- **Thao tác:** Bấm Lên lịch.
- **Mong đợi theo tài liệu:** Phiếu Đã lên lịch; giữ khoảng giờ; chưa đổi trạng thái hiện tại của xe.
- **Ghi kết quả:** dòng `MNT-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-04 · P0 · Thiếu giờ khi lên lịch

- **Chuẩn bị:** Phiếu Mới.
- **Thao tác:** Thử không có giờ; chỉ đầu; chỉ cuối; bấm Lên lịch mỗi biến thể.
- **Mong đợi theo tài liệu:** Đều không lên lịch được khi thiếu đầu/cuối; không phát sinh lịch chặn sai.
- **Ghi kết quả:** dòng `MNT-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-05 · P0 · Kết thúc dự kiến trước bắt đầu

- **Chuẩn bị:** Phiếu TEST.
- **Thao tác:** Nhập D 12:00→10:00; lưu/lên lịch.
- **Mong đợi theo tài liệu:** Từ chối; không đảo giờ tự động.
- **Ghi kết quả:** dòng `MNT-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-06 · P0 · Lịch chặn thuê thời lượng 0

- **Chuẩn bị:** Phiếu Mới, chặn thuê=True.
- **Thao tác:** Nhập D 10:00→10:00; lên lịch.
- **Mong đợi theo tài liệu:** Từ chối theo NV; lịch chặn phải có thời lượng dương.
- **Ghi kết quả:** dòng `MNT-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-07 · P0 · Bắt đầu từ phiếu Mới

- **Chuẩn bị:** Xe sẵn sàng, phiếu Mới chặn thuê.
- **Thao tác:** Bấm Bắt đầu.
- **Mong đợi theo tài liệu:** Phiếu Đang thực hiện; có actual_start; xe Bảo dưỡng, chưa đạt kỹ thuật.
- **Ghi kết quả:** dòng `MNT-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-08 · P0 · Bắt đầu phiếu đã lên lịch

- **Chuẩn bị:** Xe sẵn sàng, phiếu scheduled chặn thuê.
- **Thao tác:** Bấm Bắt đầu; mở lại xe.
- **Mong đợi theo tài liệu:** Phiếu running; xe maintenance/False; thời gian thực tế được ghi khi thiếu.
- **Ghi kết quả:** dòng `MNT-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-09 · P0 · Không sửa chặn thuê khi xe đang thuê

- **Chuẩn bị:** Xe renting và phiếu TEST chưa bắt đầu.
- **Thao tác:** Thử Bắt đầu phiếu chặn thuê.
- **Mong đợi theo tài liệu:** Từ chối; xe vẫn đang thuê; phiếu không running một phần.
- **Ghi kết quả:** dòng `MNT-09` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-10 · P0 · Phiếu không chặn thuê

- **Chuẩn bị:** Xe sẵn sàng, phiếu blocks_rental=False.
- **Thao tác:** Bắt đầu rồi hoàn tất với kết quả.
- **Mong đợi theo tài liệu:** Phiếu đổi trạng thái; xe không tự mất sẵn sàng chỉ do phiếu không chặn.
- **Ghi kết quả:** dòng `MNT-10` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-11 · P0 · Hoàn tất thiếu kết quả

- **Chuẩn bị:** Phiếu running.
- **Thao tác:** Để result trống rồi chỉ khoảng trắng; bấm Hoàn tất.
- **Mong đợi theo tài liệu:** Từ chối; xe chưa được giải phóng; nhập kết quả rõ ràng mới hoàn tất.
- **Ghi kết quả:** dòng `MNT-11` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-12 · P0 · Hoàn tất phiếu chặn cuối cùng

- **Chuẩn bị:** Chỉ một phiếu running chặn thuê.
- **Thao tác:** Nhập kết quả; Hoàn tất; xem xe.
- **Mong đợi theo tài liệu:** Phiếu done, có actual_end; xe Chờ kiểm tra/False, chưa tự Sẵn sàng.
- **Ghi kết quả:** dòng `MNT-12` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-13 · P0 · Hai phiếu chặn cùng xe

- **Chuẩn bị:** Xe có hai phiếu running chặn thuê.
- **Thao tác:** Hoàn tất phiếu thứ nhất; xem xe; hoàn tất phiếu còn lại.
- **Mong đợi theo tài liệu:** Sau phiếu đầu vẫn maintenance/False; sau phiếu cuối pending_inspection/False.
- **Ghi kết quả:** dòng `MNT-13` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-14 · P0 · Hủy phiếu đang chạy

- **Chuẩn bị:** Xe có một phiếu running chặn thuê.
- **Thao tác:** Bấm Hủy; xem xe.
- **Mong đợi theo tài liệu:** Phiếu cancelled; xe Chờ kiểm tra, chưa đạt kỹ thuật; cần kiểm tra lại.
- **Ghi kết quả:** dòng `MNT-14` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-15 · P1 · Hủy phiếu mới hoặc lịch tương lai

- **Chuẩn bị:** Xe sẵn sàng, phiếu new/scheduled riêng.
- **Thao tác:** Hủy từng phiếu; xem xe và thử kiểm tra lịch thuê.
- **Mong đợi theo tài liệu:** Không đổi trạng thái xe; lịch đã hủy không còn chặn thuê.
- **Ghi kết quả:** dòng `MNT-15` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-16 · P0 · Không chuyển ngược phiếu kết thúc

- **Chuẩn bị:** Phiếu done và cancelled TEST.
- **Thao tác:** Thử quay về Mới/Lên lịch/Bắt đầu bằng thao tác UI nếu có.
- **Mong đợi theo tài liệu:** Không cho quay ngược; UI không có đường làm sai hoặc báo từ chối.
- **Ghi kết quả:** dòng `MNT-16` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-17 · P0 · Khóa sửa cấu trúc phiếu running

- **Chuẩn bị:** Phiếu running chặn thuê.
- **Thao tác:** Thử đổi xe, đổi chặn thuê, lưu trữ và xóa từng biến thể.
- **Mong đợi theo tài liệu:** Đều bị chặn; không chuyển phiếu đang chạy sang xe khác.
- **Ghi kết quả:** dòng `MNT-17` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-18 · P1 · Không đổi xe phiếu đã kết thúc

- **Chuẩn bị:** Phiếu done/cancelled.
- **Thao tác:** Thử sửa vehicle_id qua form nếu có.
- **Mong đợi theo tài liệu:** Không được đổi xe của lịch sử đã kết thúc.
- **Ghi kết quả:** dòng `MNT-18` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-19 · P0 · Chi phí âm và miễn phí

- **Chuẩn bị:** Hai phiếu TEST.
- **Thao tác:** Nhập -1 rồi lưu; phiếu khác nhập 0 và lưu.
- **Mong đợi theo tài liệu:** Âm bị chặn; 0 hợp lệ; tiền hiển thị đúng tiền tệ.
- **Ghi kết quả:** dòng `MNT-19` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-20 · P1 · Thời gian thực tế sai

- **Chuẩn bị:** Phiếu TEST riêng.
- **Thao tác:** Nhập actual_end nhưng thiếu actual_start; rồi nhập cuối trước đầu.
- **Mong đợi theo tài liệu:** Từ chối cả hai; không lưu thời gian vô lý.
- **Ghi kết quả:** dòng `MNT-20` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-21 · P1 · Mốc tiếp theo phải sau ngày phiếu

- **Chuẩn bị:** Phiếu ngày D.
- **Thao tác:** Thử next_service_date=D-1, D, D+1.
- **Mong đợi theo tài liệu:** Hai giá trị đầu bị chặn; D+1 được nhận.
- **Ghi kết quả:** dòng `MNT-21` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-22 · P1 · Cập nhật mốc xe từ phiếu mới nhất

- **Chuẩn bị:** Hai phiếu khác ngày cho cùng xe.
- **Thao tác:** Hoàn tất phiếu ngày mới hơn có mốc A; rồi phiếu ngày cũ hơn có mốc B.
- **Mong đợi theo tài liệu:** Mốc trên xe theo phiếu hoàn tất phù hợp mới nhất, không bị phiếu lịch sử cũ ghi đè.
- **Ghi kết quả:** dòng `MNT-22` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-23 · P1 · Sao chép phiếu bảo dưỡng

- **Chuẩn bị:** Phiếu done có result và giờ thực tế.
- **Thao tác:** Sao chép; xem phiếu mới; thử đi workflow.
- **Mong đợi theo tài liệu:** Không mang result/giờ thực tế cũ; phiếu mới cần kết quả mới.
- **Ghi kết quả:** dòng `MNT-23` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-24 · P1 · Không bắt đầu phiếu hoặc xe lưu trữ

- **Chuẩn bị:** Phiếu TEST/xe TEST đã lưu trữ.
- **Thao tác:** Thử mở và Bắt đầu.
- **Mong đợi theo tài liệu:** Từ chối; không tự kích hoạt lại đối tượng lưu trữ.
- **Ghi kết quả:** dòng `MNT-24` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-25 · P1 · Đến hạn chưa tự động chặn xe

- **Chuẩn bị:** Xe sẵn sàng, next_service_date hôm nay/hôm qua.
- **Thao tác:** Lọc Đến hạn; mở xe và kiểm tra có phiếu tự sinh không.
- **Mong đợi theo tài liệu:** Được lọc đúng; theo NV không tự tạo phiếu/khóa xe chỉ vì đến ngày.
- **Ghi kết quả:** dòng `MNT-25` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### MNT-26 · P1 · Sửa ghi chú lịch sử không đổi hiện tại

- **Chuẩn bị:** Xe đang ở trạng thái xác định, có phiếu done cũ.
- **Thao tác:** Sửa notes của phiếu cũ; tải lại xe.
- **Mong đợi theo tài liệu:** Giữ trạng thái/ODO/mốc xe; không kích hoạt lại bảo dưỡng.
- **Ghi kết quả:** dòng `MNT-26` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### AVL — Khoảng thuê và lịch bảo dưỡng

Nguồn: NV5; BS1–2; GQ Contract.

Nơi thao tác: Chọn xe/xác nhận hợp đồng; ghi BLOCKED nếu hệ thống chưa nối kiểm tra Fleet.

#### AVL-01 · P0 · Xe đủ điều kiện

- **Chuẩn bị:** Xe sẵn sàng, đạt kỹ thuật, hoạt động, không khóa/lịch/hợp đồng trùng.
- **Thao tác:** Chọn cho khoảng D 10:00–D+2 10:00; xác nhận theo workflow.
- **Mong đợi theo tài liệu:** Qua kiểm tra Fleet; vẫn phải đủ điều kiện hợp đồng và thanh toán khác.
- **Ghi kết quả:** dòng `AVL-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-02 · P0 · Xe chưa đạt kỹ thuật

- **Chuẩn bị:** Xe pending_inspection/False.
- **Thao tác:** Thử chọn và xác nhận hợp đồng/giao.
- **Mong đợi theo tài liệu:** Bị loại hoặc bị chặn xác nhận/giao; không chỉ cảnh báo rồi vẫn cho giao.
- **Ghi kết quả:** dòng `AVL-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-03 · P0 · Xe bị khóa chủ động

- **Chuẩn bị:** Xe available/True, rental_blocked=True.
- **Thao tác:** Thử đặt/giao.
- **Mong đợi theo tài liệu:** Bị chặn vì khóa dù đạt kỹ thuật.
- **Ghi kết quả:** dòng `AVL-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-04 · P0 · Lịch bảo dưỡng trùng một phần đầu

- **Chuẩn bị:** Bảo dưỡng scheduled D 09:00–11:00 chặn thuê.
- **Thao tác:** Thử thuê D 10:00–12:00.
- **Mong đợi theo tài liệu:** Bị chặn do giao nhau 10:00–11:00.
- **Ghi kết quả:** dòng `AVL-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-05 · P0 · Lịch bảo dưỡng trùng một phần cuối

- **Chuẩn bị:** Bảo dưỡng D 11:00–13:00.
- **Thao tác:** Thử thuê D 10:00–12:00.
- **Mong đợi theo tài liệu:** Bị chặn do giao nhau 11:00–12:00.
- **Ghi kết quả:** dòng `AVL-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-06 · P0 · Thuê bao trùm bảo dưỡng

- **Chuẩn bị:** Bảo dưỡng D 10:00–12:00.
- **Thao tác:** Thử thuê D 09:00–13:00.
- **Mong đợi theo tài liệu:** Bị chặn.
- **Ghi kết quả:** dòng `AVL-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-07 · P0 · Bảo dưỡng bao trùm thuê

- **Chuẩn bị:** Bảo dưỡng D 09:00–13:00.
- **Thao tác:** Thử thuê D 10:00–12:00.
- **Mong đợi theo tài liệu:** Bị chặn.
- **Ghi kết quả:** dòng `AVL-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-08 · P0 · Khoảng trùng hoàn toàn

- **Chuẩn bị:** Bảo dưỡng D 10:00–12:00.
- **Thao tác:** Thử thuê đúng D 10:00–12:00.
- **Mong đợi theo tài liệu:** Bị chặn.
- **Ghi kết quả:** dòng `AVL-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-09 · P1 · Tiếp giáp đầu lịch bảo dưỡng

- **Chuẩn bị:** Bảo dưỡng D 10:00–12:00.
- **Thao tác:** Thử thuê D 08:00–10:00.
- **Mong đợi theo tài liệu:** Theo NV hai khoảng tiếp giáp không trùng; không bị chặn chỉ do lịch này.
- **Ghi kết quả:** dòng `AVL-09` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-10 · P1 · Tiếp giáp cuối lịch bảo dưỡng

- **Chuẩn bị:** Bảo dưỡng D 10:00–12:00.
- **Thao tác:** Thử thuê D 12:00–14:00.
- **Mong đợi theo tài liệu:** Theo NV không trùng; điều kiện khác vẫn kiểm tra.
- **Ghi kết quả:** dòng `AVL-10` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-11 · P0 · Running quá giờ dự kiến vẫn chặn

- **Chuẩn bị:** Phiếu running có giờ dự kiến kết thúc trong quá khứ.
- **Thao tác:** Thử đặt/giao sau giờ dự kiến, chưa hoàn tất phiếu.
- **Mong đợi theo tài liệu:** Vẫn chặn; giờ dự kiến không tự coi là sửa xong.
- **Ghi kết quả:** dòng `AVL-11` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-12 · P1 · Không chặn bởi nháp/hủy/hoàn tất

- **Chuẩn bị:** Xe đủ điều kiện; mỗi biến thể phiếu new/cancelled/done.
- **Thao tác:** Kiểm tra khoảng thuê trùng giờ phiếu, xác nhận kỹ thuật lại khi cần.
- **Mong đợi theo tài liệu:** Không bị chặn chỉ bởi lịch của ba trạng thái này.
- **Ghi kết quả:** dòng `AVL-12` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-13 · P1 · Không chặn bởi phiếu không chặn thuê

- **Chuẩn bị:** Phiếu scheduled blocks_rental=False.
- **Thao tác:** Thử thuê giao nhau.
- **Mong đợi theo tài liệu:** Không bị loại chỉ vì phiếu này.
- **Ghi kết quả:** dòng `AVL-13` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-14 · P0 · Khoảng thuê rỗng hoặc đảo

- **Chuẩn bị:** Xe đủ điều kiện.
- **Thao tác:** Thử đầu=cuối; đầu>sau cuối; thiếu đầu/cuối từng biến thể.
- **Mong đợi theo tài liệu:** Từ chối dữ liệu thời gian không hợp lệ; không giữ chỗ.
- **Ghi kết quả:** dòng `AVL-14` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-15 · P0 · Kiểm tra lại sau khi xe đổi điều kiện

- **Chuẩn bị:** Tab hợp đồng đã chọn xe; Bắc khóa hoặc bắt đầu bảo dưỡng ở tab khác.
- **Thao tác:** Quay lại tab cũ; xác nhận/giao.
- **Mong đợi theo tài liệu:** Kiểm tra điều kiện mới; không giao dựa vào dữ liệu cũ trên màn hình.
- **Ghi kết quả:** dòng `AVL-15` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### AVL-16 · P1 · Đang thuê không cấm mọi lịch tương lai

- **Chuẩn bị:** Xe có hợp đồng hiện tại kết thúc D 10:00.
- **Thao tác:** Thử đặt sau D 12:00 rồi thử trùng lịch hiện tại.
- **Mong đợi theo tài liệu:** Lịch tương lai không bị cấm chỉ vì hiện đang renting; lịch trùng do Contract chặn; điều kiện kỹ thuật hiện tại vẫn phải xét.
- **Ghi kết quả:** dòng `AVL-16` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### CON — Hợp đồng và giữ chỗ

Nguồn: GQ Contract; BS1, BS4, BS8.

Nơi thao tác: Hợp đồng → khách, dòng xe, xác nhận và hủy theo màn hình thực tế.

#### CON-01 · P0 · Hợp đồng đầy đủ

- **Chuẩn bị:** TEST-KH01, TEST-GIA và xe đủ điều kiện.
- **Thao tác:** Tạo TEST-HD01; chọn khách, đầu/cuối có giờ, cọc 2.000.000đ; thêm xe và giá; lưu.
- **Mong đợi theo tài liệu:** Đúng khách, xe, model, tiền tệ, giờ và giá; quan hệ là bản ghi thật, không chỉ text rời.
- **Ghi kết quả:** dòng `CON-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-02 · P0 · Giờ không bị mất khi lưu

- **Chuẩn bị:** Hai hợp đồng nháp TEST.
- **Thao tác:** Nhập đầu 08:30 và cuối 11:45; lưu, tải lại ở form và Operations.
- **Mong đợi theo tài liệu:** Giữ cả ngày và giờ; không chuyển thành 00:00 hoặc Date vì cần tính trễ giờ.
- **Ghi kết quả:** dòng `CON-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-03 · P0 · Giá thuê chụp tại lúc chọn

- **Chuẩn bị:** Nhóm giá 300.000đ/ngày.
- **Thao tác:** Chọn loại xe ở dòng hợp đồng; lưu; đổi giá danh mục thành 350.000đ; mở lại hợp đồng cũ và tạo hợp đồng mới.
- **Mong đợi theo tài liệu:** Hợp đồng cũ giữ giá snapshot 300.000đ; dòng mới dùng giá hiệu lực theo chính sách đã chốt.
- **Ghi kết quả:** dòng `CON-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-04 · P0 · Tiền thuê mẫu hai ngày

- **Chuẩn bị:** Q4 đã chốt, xe TEST.
- **Thao tác:** Tạo thuê D 10:00→D+2 10:00, giá 300.000đ/ngày, không giảm/thuế/phí thêm.
- **Mong đợi theo tài liệu:** Nếu Q4 quy định đúng hai ngày thì rental_days=2, subtotal/total=600.000đ; cọc không cộng thành tiền thuê 2.600.000đ.
- **Ghi kết quả:** dòng `CON-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-05 · P0 · Không lặp cùng xe trong một hợp đồng

- **Chuẩn bị:** Một hợp đồng nháp có TEST-X01.
- **Thao tác:** Thêm dòng thứ hai cùng TEST-X01; lưu/xác nhận.
- **Mong đợi theo tài liệu:** Từ chối trùng cặp contract_id, vehicle_id theo BS8; không thu hai lần cho một xe.
- **Ghi kết quả:** dòng `CON-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-06 · P0 · Không giữ chỗ hai hợp đồng trùng

- **Chuẩn bị:** Hợp đồng A đã giữ xe D 10:00–D+2 10:00 theo trạng thái hiệu lực Q3.
- **Thao tác:** Tạo B cùng xe nằm trong khoảng đó; xác nhận.
- **Mong đợi theo tài liệu:** B bị chặn; không chỉ kiểm tra xe đang available.
- **Ghi kết quả:** dòng `CON-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-07 · P0 · Hai hợp đồng trùng một phần

- **Chuẩn bị:** A có hiệu lực D 10:00–D+2 10:00.
- **Thao tác:** Tạo B D+1 10:00–D+3 10:00 cùng xe.
- **Mong đợi theo tài liệu:** B bị chặn do giao nhau.
- **Ghi kết quả:** dòng `CON-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-08 · P0 · Hai hợp đồng bao trùm hoặc bằng nhau

- **Chuẩn bị:** A giữ xe D 10:00–D+2 10:00.
- **Thao tác:** Thử B D-1→D+3; thử B trùng hoàn toàn bằng hợp đồng mới riêng.
- **Mong đợi theo tài liệu:** Đều bị chặn theo quy tắc hiệu lực Q3.
- **Ghi kết quả:** dòng `CON-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-09 · P1 · Hai hợp đồng tiếp giáp

- **Chuẩn bị:** A kết thúc D+2 10:00.
- **Thao tác:** Tạo B cùng xe bắt đầu đúng D+2 10:00.
- **Mong đợi theo tài liệu:** Kết quả theo quy tắc tiếp giáp Contract do Q3 chốt; không lấy quy tắc Fleet tự suy ra Contract đã triển khai.
- **Ghi kết quả:** dòng `CON-09` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-10 · P0 · Nháp và hủy có giữ chỗ không

- **Chuẩn bị:** Hợp đồng nháp A; hợp đồng B cùng xe/cùng giờ.
- **Thao tác:** Thử xác nhận B; sau đó xác nhận A ở ca riêng; hủy A rồi đặt B.
- **Mong đợi theo tài liệu:** Theo trạng thái hiệu lực Q3; hủy phải giải phóng giữ chỗ nếu đó là chính sách đã chốt; không để hai hợp đồng hiệu lực trùng.
- **Ghi kết quả:** dòng `CON-10` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-11 · P0 · Không sửa xe/giờ để né trùng

- **Chuẩn bị:** A và B đã có hiệu lực không trùng.
- **Thao tác:** Sửa B sang xe/giờ của A; lưu/xác nhận lại.
- **Mong đợi theo tài liệu:** Chặn xung đột mới; không chỉ kiểm lúc tạo ban đầu.
- **Ghi kết quả:** dòng `CON-11` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-12 · P1 · Ràng buộc ngày thuê tối thiểu/tối đa

- **Chuẩn bị:** Q4 có min=1, max=3 để test.
- **Thao tác:** Thử 0, đúng 1, đúng 3 và 4 ngày theo cách tính đã chốt.
- **Mong đợi theo tài liệu:** Các biên theo Q4; không tự mặc định quy tắc làm tròn ngày chưa có trong Word.
- **Ghi kết quả:** dòng `CON-12` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-13 · P1 · Hợp đồng nhiều xe

- **Chuẩn bị:** Q2 cho phép nhiều xe cùng giao/trả.
- **Thao tác:** Thêm hai xe khác nhau, hai đơn giá; xem tổng và tạo phiếu vận hành.
- **Mong đợi theo tài liệu:** Tổng là tổng dòng đúng; cả hai xe được liên kết, không mất dòng; nếu Q2 chỉ một xe thì ca này phải bị chặn theo quy ước.
- **Ghi kết quả:** dòng `CON-13` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-14 · P0 · Dữ liệu bắt buộc hợp đồng

- **Chuẩn bị:** Hợp đồng TEST nháp.
- **Thao tác:** Lần lượt bỏ khách, tiền tệ, đầu/cuối, xe/loại xe của dòng; lưu.
- **Mong đợi theo tài liệu:** Các trường bắt buộc theo GQ được kiểm soát; không tạo hợp đồng không thể truy vết.
- **Ghi kết quả:** dòng `CON-14` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-15 · P1 · Mã hợp đồng và tiền cọc

- **Chuẩn bị:** Có hợp đồng TEST-HD01.
- **Thao tác:** Thử mã trùng nếu được nhập; thử cọc âm và cọc 0.
- **Mong đợi theo tài liệu:** Mã hợp đồng duy nhất theo GQ; cọc âm/0 theo chính sách Q4 đã chốt, không coi mặc định code là chuẩn.
- **Ghi kết quả:** dòng `CON-15` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-16 · P0 · Đổi xe cập nhật hợp đồng

- **Chuẩn bị:** Chuyến TEST có xe cũ, xe thay hợp lệ.
- **Thao tác:** Thực hiện đổi xe ở Operations; mở hợp đồng và dòng ticket.
- **Mong đợi theo tài liệu:** Xe đang thực hiện được cập nhật nhất quán theo BS1; không chỉ đổi dòng ticket và để hợp đồng còn xe cũ.
- **Ghi kết quả:** dòng `CON-16` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-17 · P1 · Xem hợp đồng lịch sử

- **Chuẩn bị:** Hợp đồng TEST đã xong.
- **Thao tác:** Tìm theo mã, khách, xe; mở các phiếu vận hành, tiền, phí liên quan.
- **Mong đợi theo tài liệu:** Truy vết đúng cùng hợp đồng; không trộn chứng từ khách khác.
- **Ghi kết quả:** dòng `CON-17` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### CON-18 · P0 · Hủy hợp đồng đã thu tiền

- **Chuẩn bị:** Q7 quy định hủy/hoàn cọc; dữ liệu TEST.
- **Thao tác:** Thu cọc rồi thử hủy; kiểm tra giữ chỗ, xe và Payment.
- **Mong đợi theo tài liệu:** Không mất chứng từ hoặc tự hoàn tiền chưa ghi nhận; xử lý đúng Q7. Chưa chốt thì BLOCKED.
- **Ghi kết quả:** dòng `CON-18` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### OPS — Giao xe và nhận trả

Nguồn: GQ Operations; BS2, BS5–6, BS8; NV6–7.

Nơi thao tác: Vận hành → phiếu hợp đồng, dòng xe và xác nhận giao/trả.

#### OPS-01 · P0 · Phiếu vận hành liên kết hợp đồng

- **Chuẩn bị:** Hợp đồng TEST hợp lệ.
- **Thao tác:** Tạo phiếu; chọn contract_id; chọn xe trên dòng; mở các liên kết.
- **Mong đợi theo tài liệu:** Đúng hợp đồng và fleet.vehicle; không chỉ nhập rental_order_ref/vehicle_ref text.
- **Ghi kết quả:** dòng `OPS-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-02 · P0 · Giao xe thông thường

- **Chuẩn bị:** Xe available/True, không khóa/lịch; đã ghi tiền thuê và cọc theo Q7.
- **Thao tác:** Nhập địa điểm/phí giao, ODO=1.000, pin=90; xác nhận giao.
- **Mong đợi theo tài liệu:** Xe chuyển renting trên form/Kanban; dòng có giờ giao và snapshot; chứng từ liên quan đúng hợp đồng.
- **Ghi kết quả:** dòng `OPS-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-03 · P0 · Giao xe thiếu điều kiện tiền

- **Chuẩn bị:** Chưa thu tiền thuê hoặc cọc theo quy tắc BS5/Q7.
- **Thao tác:** Thử xác nhận giao.
- **Mong đợi theo tài liệu:** Xử lý theo điều kiện nhóm chốt; không báo đã thu khi chưa có Payment hợp lệ; chưa chốt mức chặn thì BLOCKED.
- **Ghi kết quả:** dòng `OPS-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-04 · P0 · Không giao khi xe không sẵn sàng

- **Chuẩn bị:** Ba xe TEST pending, maintenance, renting.
- **Thao tác:** Thử giao từng xe qua phiếu mới.
- **Mong đợi theo tài liệu:** Đều không được giao lại; không ghi thêm tiền/trạng thái một phần.
- **Ghi kết quả:** dòng `OPS-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-05 · P0 · Xác nhận giao lặp

- **Chuẩn bị:** Phiếu vừa giao thành công.
- **Thao tác:** Bấm lại nếu có; tải lại rồi thử lại; kiểm tra ODO/tiền/lịch sử.
- **Mong đợi theo tài liệu:** Không ghi giao hai lần; không nhân đôi Payment/Charge/log do lặp thao tác.
- **Ghi kết quả:** dòng `OPS-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-06 · P0 · Chưa giao không được nhận trả

- **Chuẩn bị:** Dòng chưa checkout.
- **Thao tác:** Thử bấm nhận trả.
- **Mong đợi theo tài liệu:** Từ chối hoặc không có thao tác; không biến xe trong bãi thành xe đã hoàn tất chuyến.
- **Ghi kết quả:** dòng `OPS-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-07 · P0 · Nhận trả thông thường

- **Chuẩn bị:** Xe renting, ODO đầu 1.000, pin đầu 90.
- **Thao tác:** Nhập trả 1.080, pin 60, giờ trả đúng hạn và kết luận theo Q1; xác nhận.
- **Mong đợi theo tài liệu:** Dòng có thời gian và snapshot đúng; xe cập nhật theo Q1; không mặc định lấy hành vi code làm quy trình đúng.
- **Ghi kết quả:** dòng `OPS-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-08 · P0 · Nhận trả chưa kiểm tra

- **Chuẩn bị:** Q1 chốt quy trình pending; xe renting.
- **Thao tác:** Nhận xe và chọn chưa kết luận/chờ kiểm tra nếu có.
- **Mong đợi theo tài liệu:** Xe pending_inspection/False; không xuất thuê tiếp trước xác nhận Fleet. Nếu Q1 chọn quy trình khác, điều chỉnh đáp án theo quyết định lưu lại.
- **Ghi kết quả:** dòng `OPS-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-09 · P0 · Trả xe có lỗi

- **Chuẩn bị:** Xe đang thuê, có lỗi ghi nhận.
- **Thao tác:** Chọn không đạt; ghi mô tả; xác nhận trả.
- **Mong đợi theo tài liệu:** Xe không sẵn sàng; có thông tin chuyển Fleet theo Q1; không tự xóa lỗi vì đã thu phí.
- **Ghi kết quả:** dòng `OPS-09` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-10 · P0 · Trả xe cần sửa

- **Chuẩn bị:** Xe đang thuê.
- **Thao tác:** Ghi cần sửa chữa, xác nhận; kiểm tra xe và phiếu sửa.
- **Mong đợi theo tài liệu:** Xe Bảo dưỡng/chưa đạt theo NV; tạo hồ sơ sửa theo quy trình, không đánh sẵn sàng khi chưa sửa.
- **Ghi kết quả:** dòng `OPS-10` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-11 · P0 · Nhận trả lặp

- **Chuẩn bị:** Dòng chuyến đã nhận trả.
- **Thao tác:** Bấm trả lần hai hoặc mở tab cũ và xác nhận lại.
- **Mong đợi theo tài liệu:** Không cập nhật lặp ODO/giờ trả/Charge/hoàn cọc; không nhận trả lại một chuyến cũ sau khi xe đã sang chuyến mới.
- **Ghi kết quả:** dòng `OPS-11` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-12 · P0 · Giữ khóa thuê khi trả

- **Chuẩn bị:** Bắc khóa xe đang thuê vì lý do quản lý.
- **Thao tác:** Nhận trả, kiểm tra kỹ thuật và xác nhận theo Q1.
- **Mong đợi theo tài liệu:** Giữ khóa và lý do; trả đạt kỹ thuật không tự cho phép thuê.
- **Ghi kết quả:** dòng `OPS-12` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-13 · P0 · Pin giao/trả được giữ riêng

- **Chuẩn bị:** Chuyến TEST pin đầu 90, cuối 19.
- **Thao tác:** Lưu/xác nhận; mở lại chuyến cũ sau một chuyến mới.
- **Mong đợi theo tài liệu:** Giữ đúng 90/19 của chuyến; không lấy giá trị pin hiện tại đè lịch sử.
- **Ghi kết quả:** dòng `OPS-13` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-14 · P0 · Biên pin dưới 20 phần trăm

- **Chuẩn bị:** Các chuyến độc lập, bảng giá pin xác định.
- **Thao tác:** Trả lần lượt 19,99; 20; 20,01 phần trăm.
- **Mong đợi theo tài liệu:** Phụ phí thiếu pin chỉ phát sinh khi <20% theo BS; 20 và 20,01 không có phí này. Kết luận kỹ thuật theo Q1, không suy ra từ việc nộp phí.
- **Ghi kết quả:** dòng `OPS-14` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-15 · P1 · Pin âm hoặc hơn 100

- **Chuẩn bị:** Phiếu TEST.
- **Thao tác:** Nhập -1 và 101 ở đầu/cuối; lưu/xác nhận.
- **Mong đợi theo tài liệu:** Đây là ca suy ra từ đơn vị % (RR): phải được kiểm soát hoặc ghi vấn đề cần chốt; không dùng giá vô lý để tính phí.
- **Ghi kết quả:** dòng `OPS-15` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-16 · P1 · Thiếu pin hoặc ODO

- **Chuẩn bị:** Phiếu TEST.
- **Thao tác:** Để trống từng số đo, còn dữ liệu khác hợp lệ; xác nhận.
- **Mong đợi theo tài liệu:** Theo Q5; không coi trống là pin 0% rồi tự phạt, không ghi ODO 0 đè số hiện tại.
- **Ghi kết quả:** dòng `OPS-16` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-17 · P1 · Địa điểm và phí giao nhận

- **Chuẩn bị:** Phiếu TEST có giao/nhận khác điểm.
- **Thao tác:** Ghi địa điểm, phí giao 30.000đ, phí nhận 40.000đ; kiểm tra Charge và thanh toán.
- **Mong đợi theo tài liệu:** Địa điểm đúng; khoản phí liên kết đúng hợp đồng/ticket theo GQ; không thu hai lần cùng khoản ở Operations và Finance.
- **Ghi kết quả:** dòng `OPS-17` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-18 · P1 · Ghi phụ kiện và ngoại quan

- **Chuẩn bị:** Có notes hoặc has_charger theo BS1.
- **Thao tác:** Ghi Có sạc, xước trái lúc giao; lúc trả ghi Thiếu sạc nếu có nơi ghi; mở lại.
- **Mong đợi theo tài liệu:** Thông tin đủ truy lại theo phạm vi Word; không bắt buộc có bảng checklist/phụ kiện riêng.
- **Ghi kết quả:** dòng `OPS-18` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-19 · P0 · Đổi xe trong chuyến

- **Chuẩn bị:** Xe cũ đang thuê, xe mới đủ điều kiện.
- **Thao tác:** Lập sự cố và đề nghị thay; xác nhận; xem hai xe, hợp đồng và ticket.
- **Mong đợi theo tài liệu:** Xe mới chuyển renting; xe cũ được xử lý đúng tình trạng; hợp đồng/ticket cùng xe mới; lưu được dấu vết xe cũ/sự cố.
- **Ghi kết quả:** dòng `OPS-19` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-20 · P0 · Đổi sang xe không đủ điều kiện

- **Chuẩn bị:** Xe thay đang khóa/đang thuê/đang sửa, từng biến thể.
- **Thao tác:** Thử xác nhận đổi.
- **Mong đợi theo tài liệu:** Từ chối; xe cũ/hợp đồng/ticket giữ nguyên; không đổi được nửa chừng.
- **Ghi kết quả:** dòng `OPS-20` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### OPS-21 · P0 · Một hợp đồng nhiều xe trả cùng lúc

- **Chuẩn bị:** Q2 chốt cùng giao/trả, hai xe đã giao.
- **Thao tác:** Thử trả một dòng riêng; sau đó thử quy trình trả cả hai theo Q2.
- **Mong đợi theo tài liệu:** Tuân theo phạm vi đơn giản hóa đã chốt; không đóng hợp đồng khi còn xe chưa trả. Nếu Q2 một xe/hợp đồng thì không tạo được trường hợp này.
- **Ghi kết quả:** dòng `OPS-21` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### INC — Sự cố và thay xe

Nguồn: GQ Operations; BS1, BS3–4, BS8.

Nơi thao tác: Vận hành → sự cố, thay xe; Finance → khoản phí.

#### INC-01 · P0 · Ghi sự cố đúng xe đúng chuyến

- **Chuẩn bị:** Phiếu thuê TEST đang diễn ra.
- **Thao tác:** Tạo sự cố với ticket, xe, thời điểm, mô tả Vỡ gương, người có lỗi/quyết định khách nếu có.
- **Mong đợi theo tài liệu:** Sự cố liên kết đúng fleet.vehicle và ticket; không chỉ text mã xe.
- **Ghi kết quả:** dòng `INC-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### INC-02 · P0 · Một chuyến hai sự cố

- **Chuẩn bị:** Cùng ticket TEST.
- **Thao tác:** Tạo Vỡ gương và Hỏng đèn; tạo Charge từ từng sự cố.
- **Mong đợi theo tài liệu:** Hai Charge truy vết được hai incident_id khác nhau; không gộp mất nguồn.
- **Ghi kết quả:** dòng `INC-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### INC-03 · P0 · Tạo Charge bồi thường

- **Chuẩn bị:** Danh mục COMPENSATION=200.000đ/lần.
- **Thao tác:** Từ sự cố tạo một khoản phí số lượng 1.
- **Mong đợi theo tài liệu:** Đúng danh mục, khách, hợp đồng, ticket, incident; amount_total=200.000đ theo đơn giá mẫu.
- **Ghi kết quả:** dòng `INC-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### INC-04 · P0 · Chống tạo Charge lặp

- **Chuẩn bị:** Một sự cố đã có Charge.
- **Thao tác:** Bấm tạo lại; tải lại; thử từ tab cũ.
- **Mong đợi theo tài liệu:** Chỉ một khoản phí cho cùng thao tác được phép; có is_charge_created/charge_id hoặc cơ chế tương đương bảo vệ nghiệp vụ.
- **Ghi kết quả:** dòng `INC-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### INC-05 · P1 · Phân biệt phí hai sự cố

- **Chuẩn bị:** Hai sự cố cùng xe, cùng số tiền.
- **Thao tác:** Tạo phí từng sự cố; mở từ Finance về nguồn.
- **Mong đợi theo tài liệu:** Mỗi khoản về đúng sự cố; không chống trùng quá mức làm mất phí của sự cố thứ hai.
- **Ghi kết quả:** dòng `INC-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### INC-06 · P1 · Bên có lỗi và quyết định khách

- **Chuẩn bị:** Có chính sách Q6.
- **Thao tác:** Thử khách có lỗi, đơn vị có lỗi, chưa kết luận; chọn sửa/đổi xe nếu có.
- **Mong đợi theo tài liệu:** Ghi nhận đúng; nghĩa vụ bồi thường theo Q6, không tự tính mọi sự cố là lỗi khách khi Word chưa chốt.
- **Ghi kết quả:** dòng `INC-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### INC-07 · P0 · Liên kết thay xe

- **Chuẩn bị:** Có sự cố và hai xe TEST.
- **Thao tác:** Lập replacement; chọn incident, xe cũ/mới; xác nhận.
- **Mong đợi theo tài liệu:** incident_id, old_vehicle_id, new_vehicle_id là liên kết ID; có ngày và trạng thái; đúng hai xe.
- **Ghi kết quả:** dòng `INC-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### INC-08 · P1 · Không thay xe bằng chính nó

- **Chuẩn bị:** Xe TEST đang thuê.
- **Thao tác:** Chọn xe cũ=xe mới; xác nhận.
- **Mong đợi theo tài liệu:** RR: thao tác vô nghĩa phải bị chặn hoặc ghi yêu cầu cần chốt; không phát sinh chuyến/tiền trùng.
- **Ghi kết quả:** dòng `INC-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### INC-09 · P0 · Xác nhận thay xe lặp

- **Chuẩn bị:** Replacement đã xác nhận.
- **Thao tác:** Bấm lại/tab cũ; kiểm tra trạng thái xe và hợp đồng.
- **Mong đợi theo tài liệu:** Không giao xe mới/nhận xe cũ lần hai; không sinh phí trùng.
- **Ghi kết quả:** dòng `INC-09` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### INC-10 · P1 · Sự cố sau khi đã quyết toán

- **Chuẩn bị:** Hợp đồng TEST đã xong.
- **Thao tác:** Thử thêm phí/sửa chi phí sự cố.
- **Mong đợi theo tài liệu:** Theo Q6/Q8; không âm thầm thay đổi số đã hoàn/thu; phải có dấu vết điều chỉnh theo quy trình đã chốt.
- **Ghi kết quả:** dòng `INC-10` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### FIN — Khoản phí, thanh toán và quyết toán

Nguồn: GQ Finance; BS1–5, BS7–8.

Nơi thao tác: Tài chính → Price Catalog, Charge, Payment, quyết toán.

#### FIN-01 · P0 · Thu tiền thuê gốc

- **Chuẩn bị:** Hợp đồng mẫu 600.000đ.
- **Thao tác:** Tạo/xác nhận Payment rental_payment=600.000đ; mở lại.
- **Mong đợi theo tài liệu:** Đúng khách/contract, loại, tiền tệ, số tiền và ngày; không nhầm thành deposit hay phụ phí.
- **Ghi kết quả:** dòng `FIN-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-02 · P0 · Thu cọc

- **Chuẩn bị:** Hợp đồng cọc 2.000.000đ.
- **Thao tác:** Tạo/xác nhận Payment deposit=2.000.000đ.
- **Mong đợi theo tài liệu:** Đúng hợp đồng; không tăng tiền thuê gốc; khoản đã thu được nhận diện đúng trạng thái hiệu lực Q7.
- **Ghi kết quả:** dòng `FIN-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-03 · P0 · Chưa xác nhận Payment chưa coi là đã thu

- **Chuẩn bị:** Một Payment nháp 600.000đ.
- **Thao tác:** Kiểm tra trạng thái thu tiền trên Operations; xác nhận Payment rồi tải lại.
- **Mong đợi theo tài liệu:** Cờ/số đã thu theo Finance thực tế; nháp không làm báo đã thu nếu Q7 quy định chỉ Payment xác nhận có hiệu lực.
- **Ghi kết quả:** dòng `FIN-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-04 · P0 · Tiền ở Operations lấy từ Finance

- **Chuẩn bị:** Có Payment/Charge TEST.
- **Thao tác:** Xác nhận tiền bên Finance rồi tải lại ticket; thử chỉ thay cờ thanh toán tay nếu UI cho phép.
- **Mong đợi theo tài liệu:** Cờ và tổng theo dữ liệu Finance theo GQ; không cho khai đã trả bằng cờ rời trái chứng từ.
- **Ghi kết quả:** dòng `FIN-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-05 · P0 · Charge số lượng nhân đơn giá

- **Chuẩn bị:** Danh mục 50.000đ/giờ.
- **Thao tác:** Tạo Charge 2 giờ; mở lại và kiểm tra tổng.
- **Mong đợi theo tài liệu:** amount_total=100.000đ; không cộng nhầm thành 50.002đ hoặc bỏ số lượng.
- **Ghi kết quả:** dòng `FIN-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-06 · P0 · Miễn trễ 10 phút

- **Chuẩn bị:** Hẹn D 10:00, giờ trả D 10:10.
- **Thao tác:** Xác nhận trả và tính phí.
- **Mong đợi theo tài liệu:** late_hours=0, phí trễ=0đ theo BS7.
- **Ghi kết quả:** dòng `FIN-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-07 · P0 · Miễn trễ đúng 15 phút

- **Chuẩn bị:** Hẹn D 10:00, trả 10:15.
- **Thao tác:** Tính phí theo quy trình UI.
- **Mong đợi theo tài liệu:** late_hours=0, phí=0đ.
- **Ghi kết quả:** dòng `FIN-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-08 · P0 · Trễ 16 phút

- **Chuẩn bị:** Hẹn D 10:00, trả 10:16.
- **Thao tác:** Tính phí.
- **Mong đợi theo tài liệu:** ceil(16/60)=1 giờ, 50.000đ với bảng giá mẫu.
- **Ghi kết quả:** dòng `FIN-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-09 · P0 · Trễ đúng 60 phút

- **Chuẩn bị:** Hẹn 10:00, trả 11:00.
- **Thao tác:** Tính phí.
- **Mong đợi theo tài liệu:** 1 giờ, 50.000đ.
- **Ghi kết quả:** dòng `FIN-09` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-10 · P0 · Trễ 65 phút

- **Chuẩn bị:** Hẹn 10:00, trả 11:05.
- **Thao tác:** Tính phí.
- **Mong đợi theo tài liệu:** 2 giờ, 100.000đ; không trừ 15 phút rồi chỉ tính 1 giờ.
- **Ghi kết quả:** dòng `FIN-10` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-11 · P1 · Trả sớm và qua nửa đêm

- **Chuẩn bị:** Hai chuyến: trả trước hẹn; hẹn D 23:50 trả D+1 00:06.
- **Thao tác:** Tính phí từng chuyến.
- **Mong đợi theo tài liệu:** Sớm không có phí trễ âm; qua ngày trễ 16 phút → 1 giờ/50.000đ.
- **Ghi kết quả:** dòng `FIN-11` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-12 · P1 · Biên 15 phút và 1 giây

- **Chuẩn bị:** Hẹn 10:00, trả 10:15:01; có UI nhập giây hoặc người phụ trách chuẩn bị dữ liệu.
- **Thao tác:** Tính phí, ghi chính xác thời gian và quyết định Q4.
- **Mong đợi theo tài liệu:** Theo độ chính xác nhóm chốt; chưa chốt cách làm tròn phút/giây thì BLOCKED, không đoán.
- **Ghi kết quả:** dòng `FIN-12` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-13 · P0 · Giá pin từ danh mục

- **Chuẩn bị:** BATTERY_CHARGE=150.000đ theo Q6.
- **Thao tác:** Trả pin 19%; tạo/tính phí.
- **Mong đợi theo tài liệu:** Một Charge thiếu pin 150.000đ theo đơn vị và quy tắc Q6, không hardcode giá ngoài danh mục.
- **Ghi kết quả:** dòng `FIN-13` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-14 · P0 · Không phí pin đúng 20 phần trăm

- **Chuẩn bị:** Chuyến trả pin 20%.
- **Thao tác:** Tính phí.
- **Mong đợi theo tài liệu:** Không có BATTERY_CHARGE chỉ vì bằng 20%.
- **Ghi kết quả:** dòng `FIN-14` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-15 · P0 · Quyết toán không phụ phí

- **Chuẩn bị:** Đã thu thuê 600.000đ và cọc 2.000.000đ; trả đúng hạn/pin đủ.
- **Thao tác:** Thực hiện quyết toán rồi hoàn tiền theo UI.
- **Mong đợi theo tài liệu:** Refund=2.000.000đ; không trừ thêm 600.000đ đã thu; tổng thực giữ=600.000đ; chỉ đóng theo Q7.
- **Ghi kết quả:** dòng `FIN-15` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-16 · P0 · Quyết toán phụ phí nhỏ hơn cọc

- **Chuẩn bị:** Đã thu thuê/cọc; tổng Charge có hiệu lực 250.000đ.
- **Thao tác:** Quyết toán và hoàn theo UI.
- **Mong đợi theo tài liệu:** Refund=1.750.000đ; tổng thực giữ=850.000đ; liên kết đúng hợp đồng.
- **Ghi kết quả:** dòng `FIN-16` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-17 · P0 · Quyết toán phụ phí lớn hơn cọc

- **Chuẩn bị:** Đã thu thuê/cọc; Charge=3.500.000đ.
- **Thao tác:** Quyết toán, tạo additional_payment và ghi thu.
- **Mong đợi theo tài liệu:** Giữ cọc, thu thêm 1.500.000đ; thực giữ=4.100.000đ; thu xong mới Done, không hoàn số âm.
- **Ghi kết quả:** dòng `FIN-17` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-18 · P0 · Phụ phí bằng cọc

- **Chuẩn bị:** Đã thu thuê/cọc; Charge=2.000.000đ.
- **Thao tác:** Quyết toán.
- **Mong đợi theo tài liệu:** Chênh lệch=0; không có hoàn/thu thêm âm; cách đóng hoặc phiếu 0 theo Q7.
- **Ghi kết quả:** dòng `FIN-18` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-19 · P0 · Nhiều loại phí cộng đúng

- **Chuẩn bị:** Trễ 65 phút=100.000đ; pin=150.000đ; bồi thường=200.000đ.
- **Thao tác:** Tính toàn bộ rồi quyết toán cọc 2.000.000đ.
- **Mong đợi theo tài liệu:** Phụ phí=450.000đ; hoàn=1.550.000đ; không cộng trùng tiền thuê hoặc cùng Charge hai lần.
- **Ghi kết quả:** dòng `FIN-19` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-20 · P0 · Quyết toán lặp

- **Chuẩn bị:** Hợp đồng đã quyết toán/hoàn thành.
- **Thao tác:** Bấm quyết toán/hoàn tiền lần hai, cả sau tải lại.
- **Mong đợi theo tài liệu:** Không tạo Refund/Additional lần hai; số tiền và số chứng từ không tăng sai.
- **Ghi kết quả:** dòng `FIN-20` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-21 · P0 · Thu tiền/hoàn tiền nhấn lặp

- **Chuẩn bị:** Một Payment TEST nháp cần xác nhận.
- **Thao tác:** Bấm liên tiếp rồi mở lại; kiểm tra các bản ghi cùng tham chiếu.
- **Mong đợi theo tài liệu:** Một giao dịch nghiệp vụ không bị hạch toán/ghi nhận thu chi hai lần.
- **Ghi kết quả:** dòng `FIN-21` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-22 · P0 · Charge nháp/hủy không bị cộng sai

- **Chuẩn bị:** Có Charge 100.000đ nháp và 200.000đ hủy; Q8 đã chốt trạng thái hiệu lực.
- **Thao tác:** Tính quyết toán, xác nhận Charge hợp lệ rồi tính lại.
- **Mong đợi theo tài liệu:** Tổng chỉ lấy trạng thái Q8 cho phép; số trên ticket khớp Finance, không chỉ nhìn cờ tay.
- **Ghi kết quả:** dòng `FIN-22` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-23 · P1 · Giá và tiền tệ không sai dấu

- **Chuẩn bị:** Charge thử 50.000đ × 3; thử nhập 12.345,67 theo ngôn ngữ giao diện.
- **Thao tác:** Lưu, tải lại, đối chiếu giá trị hiển thị.
- **Mong đợi theo tài liệu:** 150.000đ cho ví dụ đầu; giá trị thứ hai đúng quy tắc precision VND Q8; không biến thành số khác do dấu phẩy/chấm.
- **Ghi kết quả:** dòng `FIN-23` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-24 · P1 · Giá theo ngày hiệu lực

- **Chuẩn bị:** Hai giá TEST cho hai giai đoạn, Q8 có quy tắc.
- **Thao tác:** Tạo khoản phí trước/đúng/sau ngày đổi giá.
- **Mong đợi theo tài liệu:** Áp dụng đúng Q8; không tự đoán dùng giá ngày trả hay ngày lập; chưa có quy tắc thì BLOCKED.
- **Ghi kết quả:** dòng `FIN-24` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-25 · P0 · Không lẫn hợp đồng cùng khách

- **Chuẩn bị:** TEST-KH01 có hai hợp đồng A/B.
- **Thao tác:** Thu cọc A, tạo phí B; xem quyết toán mỗi hợp đồng.
- **Mong đợi theo tài liệu:** A không bị trừ phí B; Payment/Charge có contract_id đúng, không tổng hợp chỉ theo khách.
- **Ghi kết quả:** dòng `FIN-25` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-26 · P1 · Phụ phí đã được trả riêng

- **Chuẩn bị:** Có Charge 250.000đ đã thu ngoài cọc theo chính sách Q7.
- **Thao tác:** Quyết toán hợp đồng.
- **Mong đợi theo tài liệu:** Không trừ 250.000đ lần hai khỏi cọc; cách ghi thanh toán riêng cần Q7 chốt trước khi PASS.
- **Ghi kết quả:** dòng `FIN-26` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### FIN-27 · P1 · Liên kết hóa đơn nếu thuộc phạm vi

- **Chuẩn bị:** Q8 yêu cầu invoice_id và bản thử có hóa đơn.
- **Thao tác:** Mở invoice từ Payment/Charge và mở ngược chứng từ nguồn.
- **Mong đợi theo tài liệu:** Đúng invoice, khách, tiền tệ; nếu chỉ có trường liên kết, không tự yêu cầu phân hệ hóa đơn đầy đủ ngoài phạm vi nhóm chốt.
- **Ghi kết quả:** dòng `FIN-27` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### E2E — Luồng xuyên cả bốn phân hệ

Nguồn: GQ và BS; NV; Q1–Q8 khi có mâu thuẫn.

Nơi thao tác: Làm tuần tự bằng tài khoản Nhân → Đức Anh → Giang → Bắc.

#### E2E-01 · P0 · Chuyến chuẩn trọn vòng

- **Chuẩn bị:** Khách mới, xe available, thuê 600.000đ, cọc 2.000.000đ, Q1/Q7 đã chốt.
- **Thao tác:** Nhân lập/chốt hợp đồng; Đức Anh thu thuê+cọc; Giang giao 1.000/90%; trả đúng hẹn 1.080/60%; Bắc xử lý kỹ thuật theo Q1; Đức Anh quyết toán.
- **Mong đợi theo tài liệu:** Đúng xe/hợp đồng suốt luồng; ODO=1.080; không phụ phí; hoàn 2.000.000đ; tiền giữ 600.000đ; xe sẵn sàng chỉ sau bước Q1 yêu cầu.
- **Ghi kết quả:** dòng `E2E-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### E2E-02 · P0 · Chuyến trễ giờ và thiếu pin

- **Chuẩn bị:** Mẫu giá; thuê/cọc đã thu.
- **Thao tác:** Giao xe; trả trễ 65 phút, pin 19%; tạo Charge và quyết toán; kiểm tra kỹ thuật.
- **Mong đợi theo tài liệu:** Phí trễ=100.000đ, pin=150.000đ; tổng 250.000đ; hoàn 1.750.000đ; trạng thái xe và hợp đồng độc lập với việc đã đóng tiền.
- **Ghi kết quả:** dòng `E2E-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### E2E-03 · P0 · Chuyến hỏng vượt cọc

- **Chuẩn bị:** Thuê/cọc đã thu, Charge bồi thường 3.500.000đ.
- **Thao tác:** Ghi sự cố, nhận trả cần sửa, lập sửa; quyết toán và thu thêm; hoàn tất sửa rồi kiểm tra kỹ thuật.
- **Mong đợi theo tài liệu:** Thu thêm 1.500.000đ; xe không tự sẵn sàng chỉ vì hợp đồng Done; chỉ sẵn sàng sau sửa và xác nhận.
- **Ghi kết quả:** dòng `E2E-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### E2E-04 · P0 · Đổi xe giữa chuyến

- **Chuẩn bị:** Xe A renting, B available, có sự cố.
- **Thao tác:** Lập Incident A, xác nhận đổi sang B; xem hợp đồng/ticket; trả B và quyết toán.
- **Mong đợi theo tài liệu:** A xử lý kỹ thuật đúng; B renting rồi trả theo Q1; lịch sử hai xe còn; phí sự cố về đúng incident; không thu lại tiền thuê/cọc vô cớ.
- **Ghi kết quả:** dòng `E2E-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### E2E-05 · P0 · Bảo dưỡng tương lai ngăn đặt nhầm

- **Chuẩn bị:** Xe hiện sẵn sàng, lịch sửa D+1 10:00–12:00.
- **Thao tác:** Tạo hợp đồng D→D+2; thử xác nhận; đổi sang xe khác hợp lệ rồi tiếp tục.
- **Mong đợi theo tài liệu:** Xe có lịch bị chặn; xe thay hợp lệ chạy được; không xóa lịch bảo dưỡng để ép ca PASS.
- **Ghi kết quả:** dòng `E2E-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### E2E-06 · P0 · Hai khách tranh cùng xe

- **Chuẩn bị:** Hai tài khoản Nhân hoặc hai phiên độc lập.
- **Thao tác:** Hai người chọn cùng xe/cùng giờ; lần lượt hoặc gần đồng thời xác nhận; xem cả hai hợp đồng.
- **Mong đợi theo tài liệu:** Chỉ một hợp đồng hiệu lực giữ xe; hợp đồng còn lại bị từ chối; không tạo hai nghĩa vụ thuê hợp lệ.
- **Ghi kết quả:** dòng `E2E-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### E2E-07 · P0 · Khóa thuê giữa lúc chuẩn bị giao

- **Chuẩn bị:** Đã lập hợp đồng và thu theo quy tắc; Giang mở phiếu giao.
- **Thao tác:** Bắc khóa xe; Giang xác nhận từ tab cũ.
- **Mong đợi theo tài liệu:** Giao bị chặn; xe chưa renting; tiền thu trước vẫn truy vết được; xử lý đổi/hủy theo Q7, không tự xóa tiền.
- **Ghi kết quả:** dòng `E2E-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### E2E-08 · P0 · Không sử dụng tiền của chuyến khác

- **Chuẩn bị:** Cùng khách, A đã cọc và B chưa cọc.
- **Thao tác:** Thử giao/quyết toán B; kiểm tra liên kết tiền A.
- **Mong đợi theo tài liệu:** B không được coi đã cọc vì A đã trả; mọi tổng theo contract_id đúng.
- **Ghi kết quả:** dòng `E2E-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### E2E-09 · P0 · Bảo dưỡng xong rồi thuê lại

- **Chuẩn bị:** Xe trả cần sửa, có phiếu running.
- **Thao tác:** Hoàn tất sửa; thử thuê/giao trước xác nhận kỹ thuật; sau đó xác nhận và thử lại.
- **Mong đợi theo tài liệu:** Trước xác nhận bị chặn; sau xác nhận và đủ lịch/khóa/tiền mới đi tiếp.
- **Ghi kết quả:** dòng `E2E-09` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### E2E-10 · P0 · Hoàn tiền không giải phóng xe chưa trả

- **Chuẩn bị:** Xe vẫn đang ngoài đường.
- **Thao tác:** Thử quyết toán/đóng hợp đồng trước nhận xe theo quy trình Q7.
- **Mong đợi theo tài liệu:** Không để hệ thống vừa báo hoàn tất vừa còn xe chưa trả; chặn hoặc quy trình rõ được nhóm trưởng chấp thuận.
- **Ghi kết quả:** dòng `E2E-10` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### E2E-11 · P1 · Hai chuyến kế tiếp giữ đúng lịch sử

- **Chuẩn bị:** Một xe hoàn tất A rồi B.
- **Thao tác:** Chạy A với giá cũ/ODO 1.000→1.080; B giá mới/1.080→1.150; mở lại cả hai.
- **Mong đợi theo tài liệu:** Giá, ODO, pin, phí, tiền của A giữ nguyên; xe hiện tại 1.150; không trộn tiền B.
- **Ghi kết quả:** dòng `E2E-11` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### E2E-12 · P0 · Tất cả màn hình khớp sau tải lại

- **Chuẩn bị:** Một chuyến vừa hoàn tất và một chuyến đang thuê.
- **Thao tác:** Mở lại từ Nhân/Bắc/Giang/Đức Anh; đối chiếu bảng tổng hợp theo mã hợp đồng và mã xe.
- **Mong đợi theo tài liệu:** Hợp đồng, ticket, xe, Charge và Payment cùng phản ánh sự kiện đã xác nhận; không chỉ tab vừa bấm có số đúng.
- **Ghi kết quả:** dòng `E2E-12` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### ACL — Phân quyền bằng tài khoản thực

Nguồn: NV15; GQ nguyên tắc Finance; RR cho quyền khác chờ Q6/Q8.

Nơi thao tác: Đăng xuất hoặc dùng các hồ sơ trình duyệt độc lập.

#### ACL-01 · P0 · Bắc quản lý xe

- **Chuẩn bị:** Tài khoản Fleet Officer, không admin.
- **Thao tác:** Tạo/sửa xe TEST, đọc phiếu bảo dưỡng.
- **Mong đợi theo tài liệu:** Được đúng quyền xe/đọc bảo dưỡng theo NV; không cần dùng admin để vượt lỗi.
- **Ghi kết quả:** dòng `ACL-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ACL-02 · P0 · Kỹ thuật viên quản lý bảo dưỡng

- **Chuẩn bị:** Chỉ nhóm kỹ thuật viên và nhóm kế thừa cần thiết.
- **Thao tác:** Tạo, đọc, sửa phiếu TEST; thử xóa phiếu chưa chạy.
- **Mong đợi theo tài liệu:** Tạo/đọc/sửa được; nhóm kỹ thuật viên không tự cấp quyền xóa; không trộn thêm nhóm quản trị khi kết luận.
- **Ghi kết quả:** dòng `ACL-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ACL-03 · P0 · Quản trị Fleet không vượt workflow

- **Chuẩn bị:** Fleet Administrator.
- **Thao tác:** Thử xóa phiếu running, xác nhận kỹ thuật xe đang thuê.
- **Mong đợi theo tài liệu:** Quyền rộng không cho phá ràng buộc nghiệp vụ theo NV.
- **Ghi kết quả:** dòng `ACL-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ACL-04 · P0 · Người ngoài Fleet

- **Chuẩn bị:** Người thường không có nhóm Fleet.
- **Thao tác:** Tìm menu và thử mở URL bản ghi TEST do người có quyền cung cấp.
- **Mong đợi theo tài liệu:** Không được cấp quyền xe/bảo dưỡng trái phép; ẩn menu riêng chưa đủ để PASS.
- **Ghi kết quả:** dòng `ACL-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ACL-05 · P0 · Giang giao/trả bằng quyền thật

- **Chuẩn bị:** Tài khoản Operations theo cấu hình nhóm.
- **Thao tác:** Thực hiện chuyến hợp lệ không bằng admin.
- **Mong đợi theo tài liệu:** Đủ quyền tích hợp được nhóm cấp; nếu Access Error thì FAIL/BLOCKED cấu hình, không coi admin làm được là xong.
- **Ghi kết quả:** dòng `ACL-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ACL-06 · P0 · Nhân không tự nhận đã thu tiền

- **Chuẩn bị:** Tài khoản Contract không quyền Finance ngoài vai trò đã chốt.
- **Thao tác:** Thử sửa cờ đã thu/Payment/Refund.
- **Mong đợi theo tài liệu:** Không được làm trái phân công Finance; quyền cụ thể theo Q8, chưa chốt thì BLOCKED.
- **Ghi kết quả:** dòng `ACL-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ACL-07 · P0 · Giang không tự thay khoản thu đã xác nhận

- **Chuẩn bị:** Tài khoản Operations không quyền Finance ngoài vai trò đã chốt.
- **Thao tác:** Mở Charge/Payment đã xác nhận; thử sửa số tiền, đánh đã thu.
- **Mong đợi theo tài liệu:** Thẩm quyền theo Q8; không cho cờ tay trái chứng từ Finance làm thay đổi số quyết toán.
- **Ghi kết quả:** dòng `ACL-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ACL-08 · P1 · Quyền cộng dồn

- **Chuẩn bị:** Một người kỹ thuật viên được thêm Fleet Administrator trong bản thử.
- **Thao tác:** So sánh quyền với tài khoản kỹ thuật viên thuần.
- **Mong đợi theo tài liệu:** Ghi rõ quyền cộng dồn theo NV; không báo lỗi xóa được do nhóm khác rồi quy cho nhóm kỹ thuật viên.
- **Ghi kết quả:** dòng `ACL-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ACL-09 · P1 · Hai công ty nếu sử dụng

- **Chuẩn bị:** Nhóm có bật nhiều công ty, Q8 có quy tắc.
- **Thao tác:** Tài khoản công ty A mở xe/chứng từ B bằng URL và tìm kiếm.
- **Mong đợi theo tài liệu:** Theo phạm vi quyền đã chốt; không lộ/chỉnh dữ liệu trái quyền. Không dùng nhiều công ty ghi N/A có lý do.
- **Ghi kết quả:** dòng `ACL-09` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### ACL-10 · P1 · Đổi người dùng trên cùng trình duyệt

- **Chuẩn bị:** Một người quyền cao vừa đăng xuất.
- **Thao tác:** Đăng nhập người thường, mở lại URL và Back.
- **Mong đợi theo tài liệu:** Không giữ quyền phiên trước; thao tác ghi trái quyền bị từ chối.
- **Ghi kết quả:** dòng `ACL-10` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### REP — Thao tác lặp, dữ liệu cũ và gián đoạn

Nguồn: RR — tiêu chí toàn vẹn suy ra từ giao dịch; BS chống Charge trùng.

Nơi thao tác: Chỉ trên dữ liệu TEST; không đổi giờ máy hay làm hỏng dịch vụ.

#### REP-01 · P0 · Hai phiên xác nhận giao cùng xe

- **Chuẩn bị:** Hai người mở hai phiếu cùng xe hợp lệ.
- **Thao tác:** Đếm 3-2-1 rồi cùng bấm giao; tải lại hai phiếu và xe.
- **Mong đợi theo tài liệu:** Không có hai giao xe hiệu lực cho cùng chiếc xe; ghi thời điểm và ảnh cả hai phía. Thử tay không chứng minh tuyệt đối mọi race condition.
- **Ghi kết quả:** dòng `REP-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REP-02 · P0 · Hai phiên tạo phí cùng sự cố

- **Chuẩn bị:** Cùng incident mở trên hai phiên Finance/Operations đúng quyền.
- **Thao tác:** Cùng bấm tạo Charge; tìm tất cả Charge theo incident_id.
- **Mong đợi theo tài liệu:** Không có hai khoản trùng cùng một lần phát sinh.
- **Ghi kết quả:** dòng `REP-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REP-03 · P0 · Hai phiên quyết toán cùng hợp đồng

- **Chuẩn bị:** Hợp đồng đủ điều kiện hoàn 1.750.000đ.
- **Thao tác:** Cùng bấm quyết toán/hoàn; mở danh sách Payment.
- **Mong đợi theo tài liệu:** Không có hai Refund cùng nghĩa vụ; tổng tiền không tăng gấp đôi.
- **Ghi kết quả:** dòng `REP-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REP-04 · P0 · Tab nhận trả cũ sau chuyến mới

- **Chuẩn bị:** A đã trả, xe sau đó giao B; vẫn giữ tab trả A.
- **Thao tác:** Bấm xác nhận lại từ A; tải lại xe, B và Payment.
- **Mong đợi theo tài liệu:** Không kéo xe của B về bãi, không ghi lại ODO/giờ/tiền của A.
- **Ghi kết quả:** dòng `REP-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REP-05 · P1 · Refresh ngay sau xác nhận

- **Chuẩn bị:** Bản ghi TEST chuẩn bị xác nhận.
- **Thao tác:** Bấm xác nhận rồi tải lại trang; kiểm tra cả danh sách lẫn bản ghi.
- **Mong đợi theo tài liệu:** Có một kết quả xác định; không tự phát sinh bản ghi thứ hai do tải trang.
- **Ghi kết quả:** dòng `REP-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REP-06 · P1 · Mất mạng ở phía trình duyệt

- **Chuẩn bị:** Bản TEST, có thể bật Offline trong công cụ trình duyệt.
- **Thao tác:** Ngắt mạng phía trình duyệt, thử lưu; bật lại; tìm bản ghi trước khi bấm lại.
- **Mong đợi theo tài liệu:** Không báo thành công giả; xác định đã lưu hay chưa rồi xử lý; không mất liên kết hoặc sinh trùng. Không dừng server/database.
- **Ghi kết quả:** dòng `REP-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REP-07 · P0 · Lỗi ở bước cuối không để cập nhật dở

- **Chuẩn bị:** Phiếu nhận trả có ODO không hợp lệ, các trường khác hợp lệ.
- **Thao tác:** Thử xác nhận; sau báo lỗi tải lại xe, phiếu, tiền.
- **Mong đợi theo tài liệu:** Không có phần giao dịch đã commit riêng khi toàn thao tác bị từ chối.
- **Ghi kết quả:** dòng `REP-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### REP-08 · P1 · Hủy sửa form

- **Chuẩn bị:** Bản ghi TEST đã lưu.
- **Thao tác:** Sửa nhưng bấm Hủy/Discard; mở lại.
- **Mong đợi theo tài liệu:** Giá trị đã lưu giữ nguyên; không đổi xe, tiền, lịch do nháp chưa xác nhận.
- **Ghi kết quả:** dòng `REP-08` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### UI — Tra cứu và trình bày để demo

Nguồn: NV14; GQ; BS8.

Nơi thao tác: Các màn hình nghiệp vụ thực tế; nhãn có thể khác theo phiên bản.

#### UI-01 · P1 · Kanban đủ bốn trạng thái

- **Chuẩn bị:** Có dữ liệu hoặc cột rỗng.
- **Thao tác:** Mở Phương tiện; kiểm tra Sẵn sàng, Đang thuê, Chờ kiểm tra, Bảo dưỡng; mở thẻ.
- **Mong đợi theo tài liệu:** Cột/thẻ phản ánh trạng thái nghiệp vụ, không nhầm trạng thái mua/đăng ký chuẩn Odoo.
- **Ghi kết quả:** dòng `UI-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### UI-02 · P1 · Tìm xe theo ba tiêu chí

- **Chuẩn bị:** Xe TEST có mã, biển, dòng.
- **Thao tác:** Tìm lần lượt mã, biển số, dòng xe; xóa bộ lọc giữa lần thử.
- **Mong đợi theo tài liệu:** Tìm được đúng xe; không còn bộ lọc ẩn làm tưởng mất dữ liệu.
- **Ghi kết quả:** dòng `UI-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### UI-03 · P1 · Bộ lọc xe

- **Chuẩn bị:** Chuẩn bị xe sẵn sàng/thuê/chờ/sửa/khóa/đến hạn/lưu trữ.
- **Thao tác:** Chạy từng bộ lọc; so với form bản ghi.
- **Mong đợi theo tài liệu:** Đúng các nhóm theo NV; bản lưu trữ tìm được qua bộ lọc tương ứng.
- **Ghi kết quả:** dòng `UI-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### UI-04 · P1 · Tìm và nhóm bảo dưỡng

- **Chuẩn bị:** Phiếu các loại/trạng thái/xe khác nhau.
- **Thao tác:** Tìm mô tả/xe/loại; lọc trạng thái/lịch/chặn/lưu trữ; nhóm theo xe/trạng thái/loại.
- **Mong đợi theo tài liệu:** Kết quả đúng; tổng đếm khớp, không trộn xe ngoài phạm vi.
- **Ghi kết quả:** dòng `UI-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### UI-05 · P1 · Tra cứu chứng từ xuyên phân hệ

- **Chuẩn bị:** Hợp đồng E2E có ticket, incident, tiền.
- **Thao tác:** Tìm theo mã; mở các Many2one từ hợp đồng đến xe/khách và phí về sự cố.
- **Mong đợi theo tài liệu:** Mỗi liên kết mở đúng bản ghi; không liên kết rỗng hoặc nhầm người khác.
- **Ghi kết quả:** dòng `UI-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### UI-06 · P1 · Tiếng Việt, số và giờ

- **Chuẩn bị:** Một bộ chứng từ TEST.
- **Thao tác:** Kiểm tra dấu tiếng Việt, VND, km, %, giờ giao/trả và tổng tiền trên form/list.
- **Mong đợi theo tài liệu:** Không mất chữ, cắt số quan trọng, nhầm đơn vị; cùng dữ liệu hiển thị nhất quán.
- **Ghi kết quả:** dòng `UI-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### UI-07 · P1 · Tải lại và đếm số bản ghi

- **Chuẩn bị:** Ghi số xe/ticket/Charge/Payment TEST trước một thao tác.
- **Thao tác:** Thực hiện một chuyến/Charge; xóa lọc và đếm lại đúng phạm vi TEST.
- **Mong đợi theo tài liệu:** Mức tăng đúng số dự kiến; không có bản trùng bị lọc che khuất.
- **Ghi kết quả:** dòng `UI-07` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

### SCP — Biên phạm vi và chuẩn bị nộp

Nguồn: NV phần chưa thực hiện; BS1; RR cho bàn giao.

Nơi thao tác: Đọc đối chiếu và chạy lại các luồng đã chọn.

#### SCP-01 · P1 · Không yêu cầu pin asset ngoài phạm vi

- **Chuẩn bị:** Tài liệu NV và BS1.
- **Thao tác:** Xem phần pin đang lưu.
- **Mong đợi theo tài liệu:** Có snapshot % đầu/cuối ở Operations theo Word; không đánh FAIL vì thiếu kho pin, SOC/SOH hoặc lịch sử sạc chuyên sâu.
- **Ghi kết quả:** dòng `SCP-01` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### SCP-02 · P1 · Phụ kiện đúng mức đơn giản

- **Chuẩn bị:** BS1 chốt notes hoặc has_charger.
- **Thao tác:** Kiểm tra nơi ghi sạc/ghi chú giao nhận.
- **Mong đợi theo tài liệu:** Không bắt buộc bảng checklist riêng nếu thông tin cần thiết đã ghi theo quy ước nhóm.
- **Ghi kết quả:** dòng `SCP-02` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### SCP-03 · P0 · Đối chiếu dữ liệu thật trước/sau test

- **Chuẩn bị:** Có thống kê ban đầu và chỉ thêm TEST.
- **Thao tác:** So sánh số xe/chuyến/tiền cần giữ; xem các bản ghi gốc quan trọng.
- **Mong đợi theo tài liệu:** Không thay/xóa dữ liệu ngoài các ca được phép; phân biệt dữ liệu TEST với dữ liệu đem demo.
- **Ghi kết quả:** dòng `SCP-03` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### SCP-04 · P0 · Chạy lại lỗi sau sửa

- **Chuẩn bị:** Có FAIL được người phụ trách sửa, đã ghi phiên bản mới.
- **Thao tác:** Chạy lại đúng bước ca FAIL; chạy các ca E2E và ca liên quan tiền/trạng thái.
- **Mong đợi theo tài liệu:** Chỉ đổi FAIL→PASS khi có kết quả mới và bằng chứng; không dựa vào lời báo đã sửa.
- **Ghi kết quả:** dòng `SCP-04` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### SCP-05 · P0 · Đóng băng bản đã kiểm

- **Chuẩn bị:** Tất cả ca bắt buộc đã có kết quả.
- **Thao tác:** Ghi database/phiên bản/thời điểm kết thúc, backup đã xác nhận, danh sách lỗi còn; sau đó không cập nhật code trước nộp nếu chưa kiểm lại.
- **Mong đợi theo tài liệu:** Bản đem nộp chính là bản đã kiểm; mọi sửa tiếp phải ghi và kiểm lại phạm vi ảnh hưởng.
- **Ghi kết quả:** dòng `SCP-05` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

#### SCP-06 · P0 · Buổi demo thử từ đăng nhập

- **Chuẩn bị:** Có dữ liệu sạch dành riêng demo.
- **Thao tác:** Đăng xuất; đăng nhập vai trò thật; chạy E2E-01 và một luồng phí, một luồng bảo dưỡng.
- **Mong đợi theo tài liệu:** Có thể lặp lại bằng thao tác người dùng, không cần shell/sửa DB để vượt lỗi; tiền và xe đúng đáp án tài liệu.
- **Ghi kết quả:** dòng `SCP-06` trong sổ kết quả; kèm bản ghi/ảnh và mọi biến thể.

## 8. Khi nào có thể kết luận để nộp

Tất cả ca áp dụng phải có kết quả; mọi P0 FAIL phải được sửa và thử lại, hoặc được nhóm trưởng ghi nhận rõ là lỗi còn tồn tại. BLOCKED/PARTIAL/NOT_RUN không phải PASS; chưa chốt quy trình thì chưa thể kết luận quy trình đó đúng. N/A cần lý do và người xác nhận phạm vi.

Bản báo cáo cuối cần nêu số ca đã làm/đạt/lỗi/chưa kiểm được, tám quyết định Q đã chốt chưa, lỗi còn lại và ảnh hưởng demo. Chỉ nộp đúng bản đã kiểm; nếu code hoặc cấu hình thay đổi sau đó, phải kiểm lại các ca bị ảnh hưởng.

## 9. Dấu nhận diện nguồn lúc soạn

Hash chỉ giúp nhận biết file nguồn thay đổi, không quyết định tài liệu nào đúng hơn.

- `D:\Document\Hoc\nam4ki1\TH ERP\Tuan8\thực trạng.docx` — SHA-256: `0eba9f8444dd88594120a5d58ec07c5436b1bc261e0ded7a579422954e2a82a8`.

- `D:\Document\Hoc\nam4ki1\TH ERP\Tuan8\giải quyết.docx` — SHA-256: `cfedb219b4d0d68996285d5b634477db8995a1301ffffc9ec568b23897c2b76f`.

- `D:\Document\Hoc\nam4ki1\TH ERP\Tuan8\giải quyết bổ sung.docx` — SHA-256: `b0723b917e450020e428f28ba1d0a6e9ef1696c6d7be1e54afc88696e9650037`.

- `D:\Document\Hoc\HeNam3\Video\nghiệp vụdocx.docx` — SHA-256: `0854322b94ce0a145d0695feacefa7f714e515c6873fa269661aea3b2d534e5e`.
