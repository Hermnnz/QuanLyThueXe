# MẪU THIẾT KẾ THẺ KANBAN PHƯƠNG TIỆN XE ĐIỆN (BẢN ĐẸP & CHUẨN ODOO 18)

> **Mục đích:** Lưu trữ bản thiết kế thẻ xe máy điện đã tối ưu giao diện (tích hợp ảnh xe 64x64px, thay dải ruy-băng vỡ bằng Smart Status Badges góc trên, chân thẻ chia mốc ODO/hạn định kỳ tinh tế).  
> **Phiên bản tương thích:** Odoo 18 (OWL Framework) & các bản Odoo kế thừa.

---

## 1. Đoạn mã XML View (`fleet_vehicle_views.xml`)

Thay thế toàn bộ record `vehicle_kanban_electric` trong file:  
`custom_addons/motorbike_fleet_management/views/fleet_vehicle_views.xml`:

```xml
  <record id="vehicle_kanban_electric" model="ir.ui.view">
    <field name="name">vehicle_kanban_electric</field>
    <field name="model">fleet.vehicle</field>
    <field name="arch" type="xml">
      <kanban class="o_fleet_vehicle_kanban" delete="false" default_group_by="operational_status" records_draggable="false" quick_create="false" group_create="false" group_delete="false" group_edit="false">
        <field name="id"/>
        <field name="image_128"/>
        <field name="operational_status"/>
        <field name="technical_ready"/>
        <field name="rental_blocked"/>
        <field name="service_schedule_state"/>
        <templates>
          <t t-name="card">
            <!-- 1. Header: Mã xe, Biển số bên trái - Huy hiệu cảnh báo (Smart Badges) bên phải -->
            <div class="d-flex justify-content-between align-items-start mb-2">
              <div>
                <div class="fw-bold fs-5 text-primary"><field name="vehicle_code"/></div>
                <div class="fw-semibold text-dark"><field name="license_plate"/></div>
              </div>
              <div class="d-flex flex-column align-items-end gap-1">
                <span t-if="record.service_schedule_state.raw_value === 'overdue'" class="badge rounded-pill text-bg-danger">
                  <i class="fa fa-exclamation-triangle me-1"/>Quá hạn BD
                </span>
                <span t-elif="record.service_schedule_state.raw_value === 'due'" class="badge rounded-pill text-bg-danger">
                  <i class="fa fa-wrench me-1"/>Đến hạn BD
                </span>
                <span t-elif="record.service_schedule_state.raw_value === 'soon'" class="badge rounded-pill text-bg-warning text-dark">
                  <i class="fa fa-clock-o me-1"/>Sắp đến hạn
                </span>
                <span t-if="record.rental_blocked.raw_value" class="badge rounded-pill text-bg-danger">
                  <i class="fa fa-ban me-1"/>Khóa thuê
                </span>
              </div>
            </div>

            <!-- 2. Body: Thumbnail ảnh xe (Chuẩn REST Odoo 18) + Dòng xe, ODO, Trạng thái kỹ thuật -->
            <div class="d-flex gap-2 align-items-center mb-2">
              <img t-attf-src="/web/image/fleet.vehicle/#{record.id.raw_value}/image_128" 
                   class="rounded border bg-light flex-shrink-0" 
                   alt="Vehicle" 
                   style="width: 64px; height: 64px; object-fit: contain;"/>
              <div class="flex-grow-1 overflow-hidden">
                <div class="fw-semibold text-truncate"><field name="model_id"/></div>
                <div class="small text-muted">ODO: <span class="fw-bold text-dark"><field name="odometer"/></span> km</div>
                <div class="mt-1">
                  <span t-if="record.operational_status.raw_value === 'inactive'" class="badge text-bg-secondary">Ngừng hoạt động</span>
                  <span t-elif="record.technical_ready.raw_value" class="badge text-bg-success"><i class="fa fa-check-circle me-1"/>Đạt kỹ thuật</span>
                  <span t-else="" class="badge text-bg-warning text-dark"><i class="fa fa-hourglass-half me-1"/>Chờ xác nhận KT</span>
                </div>
              </div>
            </div>

            <!-- 3. Footer: Hạn bảo dưỡng định kỳ & Mốc ODO & Lịch hẹn kiểm tra -->
            <div class="small border-top pt-2 mt-auto text-muted">
              <div t-if="record.service_next_date.raw_value" class="d-flex justify-content-between">
                <span>Hạn định kỳ:</span>
                <span class="fw-bold text-dark"><field name="service_next_date"/></span>
              </div>
              <div t-if="record.service_next_odo.raw_value &gt; 0" class="d-flex justify-content-between">
                <span>Mốc ODO:</span>
                <span class="fw-bold text-dark"><field name="service_next_odo"/> km</span>
              </div>
              <div t-if="record.next_service_date.raw_value" class="d-flex justify-content-between mt-1 text-info">
                <span>Lịch hẹn kiểm tra:</span>
                <span class="fw-bold"><field name="next_service_date"/></span>
              </div>
            </div>
          </t>
        </templates>
      </kanban>
    </field>
  </record>
```

---

## 2. Ưu điểm nổi bật của bản thiết kế này:

1. **Chuẩn Odoo 18 OWL:** Dùng URL `/web/image/fleet.vehicle/#{record.id.raw_value}/image_128` tương thích 100%, không bị lỗi `TypeError: ctx.kanban_image is not a function`.
2. **Không phụ thuộc file SCSS ruy-băng:** Ruy-băng chéo cũ dễ bị vỡ thành chữ thô khi chuyển sang dạng lưới phẳng (ungrouped). Smart Badges dùng hoàn toàn Bootstrap pills nên luôn hiển thị ngay ngắn, có icon trực quan.
3. **Hiển thị hình ảnh xe thực tế:** Có khung ảnh 64x64px nằm cạnh Model và ODO giúp nhận diện xe nhanh chóng.
4. **Bố cục phân tầng 3 phần:** Header (Mã + Cảnh báo) - Body (Ảnh + Thông tin xe) - Footer (Lịch hẹn kiểm tra & Mốc bảo dưỡng định kỳ).

---

## 3. Cách kích hoạt lại khi bạn muốn áp dụng:

1. Mở file `custom_addons/motorbike_fleet_management/views/fleet_vehicle_views.xml`.
2. Dán đoạn XML ở **Mục 1** đè lên record `vehicle_kanban_electric`.
3. Chạy lệnh nâng cấp module để nạp lại vào database:
   ```powershell
   python scripts/run_odoo_local.py -c archive/quanlythuexe/quanlythuexe.conf -u motorbike_fleet_management --stop-after-init
   ```
4. Khởi động lại Odoo và nhấn `Ctrl + F5` trên trình duyệt.
