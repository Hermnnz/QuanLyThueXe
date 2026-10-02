# ERD Fleet — phạm vi tuần 6

Module `motorbike_fleet_management`, phiên bản `19.0.3.1.0`. Hai model nghiệp vụ, List/Form và CRUD cơ bản. Trạng thái, điều kiện kỹ thuật, thời gian và mốc bảo dưỡng do người dùng nhập.

```mermaid
erDiagram
    FLEET_VEHICLE ||--o{ FLEET_VEHICLE_LOG_SERVICES : maintenance_records
    FLEET_VEHICLE {
        int id PK
        string vehicle_code
        string license_plate
        int model_id FK
        boolean is_electric_motorbike
        string operational_status
        boolean technical_ready
        boolean rental_blocked
        text block_reason
        date next_service_date
        boolean active
    }
    FLEET_VEHICLE_LOG_SERVICES {
        int id PK
        int vehicle_id FK
        int service_type_id FK
        string maintenance_type
        datetime scheduled_start
        datetime scheduled_end
        datetime actual_start
        datetime actual_end
        string state
        string description
        text notes
        text result
        int technician_id FK
        int vendor_id FK
        decimal amount
        boolean blocks_rental
        date next_service_date
        boolean active
    }
```

Sơ đồ trình bày dữ liệu nghiệp vụ cần quan tâm; các cột chuẩn Odoo về công ty, tiền tệ, audit và thông số xe vẫn tồn tại. `cost` là alias ORM của `amount`, không phải cột riêng. `technician_id` và `vendor_id` tái sử dụng `res.partner`; danh mục xe/dịch vụ tái sử dụng Fleet chuẩn.

`operational_status`: available/rented/inspection/maintenance. `state` bảo dưỡng: new/scheduled/running/done/cancelled. Người dùng chọn trực tiếp trên Form. Hai field ngày bảo dưỡng tiếp theo ở xe và hồ sơ không tự đồng bộ. `rental_blocked` và `blocks_rental` chỉ ghi nhận thông tin; chưa có cơ chế chặn đặt thuê.

Không có pin asset/assignment, maintenance plan riêng, ODO tùy chỉnh, bảng availability, chi tiết chi phí hoặc kho phụ tùng trong phạm vi custom.

Rental và Inspection sẽ liên kết tới `fleet.vehicle` khi triển khai tuần tích hợp. Bản tuần 6 chưa tạo các quan hệ đó, chưa có availability API/hook, workflow giao–trả hoặc tự động chuyển trạng thái.

Nguồn phạm vi: `ERP_Odoo (1).xlsx`, `Ke hoach Sprint!F13:I13`. Các nhiệm vụ Search/validation/workflow thuộc hàng 17 và tích hợp thuộc hàng 21 được để lại cho tuần sau.
