/** @odoo-module **/

// Dùng autocomplete và ô thẻ xe chuẩn của Odoo, chỉ thêm một lựa chọn thao tác "Tất cả".
import { _t } from "@web/core/l10n/translation"; // Hàm dịch nhãn giao diện.
import { registry } from "@web/core/registry"; // Nơi đăng ký widget để XML gọi bằng tên.
import { Many2XAutocomplete } from "@web/views/fields/relational_utils"; // Danh sách đổ xuống có sẵn.
import { Many2ManyTagsFieldColorEditable, many2ManyTagsFieldColorEditable } from "@web/views/fields/many2many_tags/many2many_tags_field"; // Giữ chức năng chọn nhiều thẻ xe chuẩn.

class ExtensionVehicleAutocomplete extends Many2XAutocomplete { // Chỉ dùng danh sách tùy chỉnh cho ô xe gia hạn.
    async loadOptionsSource(request) { // Hàm này lấy các lựa chọn khi người dùng mở hoặc tìm kiếm trong dropdown.
        const options = await super.loadOptionsSource(request); // Giữ nguyên danh sách xe và chức năng tìm kiếm chuẩn.
        if (!request.trim()) { // Chỉ gợi ý tất cả khi mở danh sách; tìm biển số thì ưu tiên đúng xe đang tìm.
            options.unshift({ // Đặt lựa chọn tất cả ở đầu danh sách, không tạo bản ghi xe giả.
                label: _t("Tất cả xe đang thuê"), // Nội dung người dùng nhìn thấy trong dropdown.
                classList: "o_m2o_dropdown_option", // Dùng cách trình bày lựa chọn thao tác chuẩn của Odoo.
                action: () => this.props.update([], { rentalSelectAll: true }), // Báo cho widget chọn tất cả; không truyền ID xe không tồn tại.
            });
        }
        return options; // Trả danh sách cho autocomplete hiển thị.
    }
}

export class ExtensionVehicleSelection extends Many2ManyTagsFieldColorEditable { // Kế thừa đầy đủ ô chọn nhiều xe, không ảnh hưởng ô chọn khác.
    static components = { // Chỉ thay thành phần dropdown của widget này.
        ...Many2ManyTagsFieldColorEditable.components, // Giữ thẻ xe, nút xóa và các thành phần Odoo còn lại.
        Many2XAutocomplete: ExtensionVehicleAutocomplete, // Bổ sung lựa chọn tất cả ngay trong dropdown.
    };

    setup() { // Hàm khởi tạo widget và cách cập nhật nhóm xe được chọn.
        super.setup(); // Khởi tạo các hành vi chuẩn trước.
        this.update = async (records, params = {}) => { // Được gọi khi chọn một xe, nhiều xe từ tìm kiếm hoặc chọn tất cả.
            if (params.rentalSelectAll) { // Người dùng bấm dòng "Tất cả xe đang thuê".
                return this.props.record.update({ select_all: true }); // Onchange Python sẽ lấy toàn bộ xe đủ điều kiện và cập nhật tiền.
            }
            const current = this.props.record.data[this.props.name].records; // Các xe đang hiện dưới dạng thẻ.
            const ids = this.props.record.data.select_all ? [] : current.map((record) => record.resId); // Đang chọn tất cả mà chọn riêng thì bắt đầu lại từ xe vừa chọn.
            const selected = [...new Set([...ids, ...(records || []).map((record) => record.id)])]; // Có thể chọn tiếp nhiều xe riêng, không thêm xe trùng.
            return this.props.record.update({ // Cập nhật nhóm xe và chế độ chọn trong cùng một lần để không chồng onchange.
                select_all: false, // Nội bộ chuyển sang chọn riêng; không cần ô tích trên giao diện.
                [this.props.name]: [[6, 0, selected]], // Lệnh số 6 của Odoo thay toàn bộ liên kết bằng đúng danh sách ID này.
            });
        };
    }

    async deleteTag(id) { // Hàm này xử lý khi người dùng bấm dấu x để bỏ một xe khỏi nhóm đã chọn.
        const records = this.props.record.data[this.props.name].records; // Đọc danh sách thẻ hiện tại.
        const ids = records.filter((record) => record.id !== id).map((record) => record.resId); // Bỏ đúng thẻ được bấm, giữ các xe còn lại.
        return this.props.record.update({ select_all: false, [this.props.name]: [[6, 0, ids]] }); // Chuyển sang chọn riêng để lúc lưu không tự thêm xe vừa bỏ.
    }
}

registry.category("fields").add("extension_vehicle_selection", { // Tên được dùng ở field line_ids trong view gia hạn.
    ...many2ManyTagsFieldColorEditable, // Giữ cách đọc domain, options và kiểu dữ liệu many2many chuẩn.
    component: ExtensionVehicleSelection, // Chỉ thay component cho ô chọn gia hạn này.
});
