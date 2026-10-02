"""Existing optional one-year fixture, compatible with Week 6 manual CRUD.

Execute through Odoo shell. Historical dates are imported directly; no workflow,
clock simulation, availability or Rental/Inspection integration is required.
The existing one-year data is retained and reruns do not create duplicates.
"""
from collections import Counter
from datetime import date, datetime, time, timedelta
import json
from pathlib import Path
import random

from odoo import fields

DATABASE = 'motorbike_fleet_simple_20261002'
MODULE = 'fleet_year_demo'
BEGIN = date(2025, 10, 2)
END = date(2026, 10, 2)
assert env.cr.dbname == DATABASE, 'Only the minimal demo database may be seeded'
ctx = dict(env.context, tracking_disable=True, mail_create_nosubscribe=True, mail_notrack=True)
E = env(context=ctx)
rng = random.Random(20261002)


def bind(name, record):
    E['ir.model.data'].create({'module': MODULE, 'name': name, 'model': record._name,
                               'res_id': record.id, 'noupdate': True})
    return record


def references(model):
    return E['ir.model.data'].search([('module', '=', MODULE), ('model', '=', model)])


def at_local(day, hour=9, minute=0):
    # Odoo stores naive UTC; business time is UTC+7.
    return datetime.combine(day, time(hour, minute)) - timedelta(hours=7)


if not E.ref(MODULE + '.seed_complete', raise_if_not_found=False):
    assert not references('fleet.vehicle'), 'Unexpected incomplete seed; inspect before retrying'
    currency = E['res.currency'].with_context(active_test=False).search([('name', '=', 'VND')], limit=1)
    assert currency, 'VND currency must exist'
    currency.active = True
    E.company.currency_id = currency

    brand = bind('brand', E['fleet.vehicle.model.brand'].create({'name': 'Demo E-Motion'}))
    models = []
    for idx, (name, price) in enumerate([
            ('City Eco — demo', 22000000), ('Urban Flex — demo', 28000000),
            ('Tour Plus — demo', 35000000), ('Cargo Mini — demo', 31000000)]):
        models.append((bind('model_' + str(idx), E['fleet.vehicle.model'].create({
            'name': name, 'brand_id': brand.id, 'vehicle_type': 'bike'})), price))

    vendors = []
    for idx, name in enumerate(['Garage Ánh Dương — demo', 'Trạm dịch vụ Bình Minh — demo',
                               'Xưởng xe điện Đông Nam — demo']):
        vendors.append(bind('vendor_' + str(idx), E['res.partner'].create({
            'name': name, 'is_company': True, 'street': 'Địa chỉ giả lập phục vụ đồ án',
            'email': 'vendor' + str(idx + 1) + '@example.invalid',
            'comment': 'Dữ liệu giả lập, không phải doanh nghiệp có thật.'})))
    technicians = []
    for idx, name in enumerate(['Minh', 'Lan', 'Huy', 'Thảo']):
        technicians.append(bind('technician_' + str(idx), E['res.partner'].create({
            'name': 'Kỹ thuật viên ' + name + ' — demo',
            'email': 'technician' + str(idx + 1) + '@example.invalid',
            'employee': True, 'comment': 'Nhân sự giả lập; không tạo tài khoản đăng nhập.'})))

    types = {}
    for key, label in [('periodic', 'Kiểm tra định kỳ'), ('brakes', 'Phanh và lốp'),
                       ('electric', 'Hệ thống điện và bộ sạc'), ('emergency', 'Sửa chữa khẩn cấp')]:
        types[key] = bind('service_type_' + key, E['fleet.service.type'].create({
            'name': label + ' — demo', 'category': 'service'}))

    vehicles = []
    colors = ['Trắng', 'Đen', 'Xanh dương', 'Đỏ', 'Xám', 'Xanh lá']
    for idx in range(36):
        acquired = BEGIN if idx < 24 else date(2026, 1, 5) if idx < 30 else date(2026, 5, 4)
        model, price = models[idx % len(models)]
        vehicle = bind('vehicle_' + str(idx), E['fleet.vehicle'].create({
            'model_id': model.id, 'is_electric_motorbike': True, 'fuel_type': 'electric',
            'vehicle_code': 'XE' + str(101 + idx), 'license_plate': 'DEMO-EV-' + str(101 + idx),
            'acquisition_date': acquired, 'car_value': price, 'color': colors[idx % len(colors)],
            'location': 'Cửa hàng demo', 'company_id': E.company.id,
            'description': 'Dữ liệu giả lập 1 năm. Biển số/model/giá đều là số liệu minh họa. '
                           'Trạng thái đang thuê chỉ là tình huống Fleet; chưa có hợp đồng Rental.'}))
        vehicles.append(vehicle)
        vehicle.write({'operational_status': 'available', 'technical_ready': True})
        # Growing fleet, staggered periodic work, random corrective/emergency work.
        events = []
        day = acquired + timedelta(days=35 + idx % 19)
        while day < END:
            events.append((day, 'preventive', 'periodic', False))
            day += timedelta(days=rng.randint(42, 62))
        span = (END - acquired).days
        for fault in range(1 + idx % 3):
            day = acquired + timedelta(days=rng.randint(15, span - 3))
            emergency = fault == 1 and idx % 4 == 0
            events.append((day, 'emergency' if emergency else 'corrective',
                           'emergency' if emergency else 'brakes' if idx % 2 else 'electric', False))
        # Cancelled appointments provide realistic cancelled history without costs.
        if idx % 6 == 0:
            events.append((acquired + timedelta(days=min(80, span - 5)), 'preventive', 'periodic', True))
        # One visit per vehicle/day; combine scenarios across distinct visits.
        occupied_days = set()
        normalized = []
        for day, kind, category, cancelled in sorted(events):
            while day in occupied_days and day < END:
                day += timedelta(days=1)
            if day >= END:
                day = END - timedelta(days=1)
                while day in occupied_days:
                    day -= timedelta(days=1)
            occupied_days.add(day)
            normalized.append((day, kind, category, cancelled))
        for number, (day, kind, category, cancelled) in enumerate(sorted(normalized)):
            scheduled = at_local(day, 8 + (number % 3))
            duration = rng.choice([1, 2, 3]) if kind == 'preventive' else rng.choice([3, 4, 6])
            costs = {'preventive': [150000, 180000, 220000, 280000, 320000],
                     'corrective': [350000, 480000, 650000, 850000, 1100000],
                     'emergency': [700000, 950000, 1300000, 1650000]}
            result = {
                'periodic': 'Kiểm tra phanh/lốp, siết đầu nối, vệ sinh xe; chạy thử đạt yêu cầu.',
                'brakes': 'Điều chỉnh phanh, thay chi tiết mòn theo tình trạng; chạy thử đạt yêu cầu.',
                'electric': 'Kiểm tra giắc nối, dây điện và bộ sạc; khắc phục lỗi, chạy thử đạt yêu cầu.',
                'emergency': 'Khắc phục sự cố phát sinh, kiểm tra an toàn và chạy thử trước khi khai thác lại.',
            }[category]
            service = E['fleet.vehicle.log.services'].create({
                'vehicle_id': vehicle.id, 'company_id': E.company.id,
                'service_type_id': types[category].id, 'maintenance_type': kind,
                'date': day, 'description': '[' + vehicle.vehicle_code + '] ' + types[category].name,
                'notes': 'Lịch sử giả lập 12 tháng; nhập liệu CRUD, không có chứng từ thanh toán.',
                'vendor_id': vendors[(idx + number) % len(vendors)].id,
                'technician_id': technicians[(idx + number) % len(technicians)].id,
                'scheduled_start': scheduled, 'scheduled_end': scheduled + timedelta(hours=duration),
                'amount': 0 if cancelled else rng.choice(costs[kind]), 'blocks_rental': True,
                'next_service_date': day + timedelta(days=60) if kind == 'preventive' and not cancelled else False,
            })
            bind('history_' + str(idx) + '_' + str(number), service)
            service.state = 'scheduled'
            if cancelled:
                service.state = 'cancelled'
                service.notes = 'Lịch giả lập bị hủy do đổi kế hoạch; không phát sinh chi phí.'
            else:
                actual_start = scheduled + timedelta(minutes=rng.choice([0, 15, 30]))
                actual_end = actual_start + timedelta(hours=duration, minutes=rng.choice([0, 15, 45]))
                service.write({'state': 'running', 'actual_start': actual_start})
                service.result = result
                service.write({'state': 'done', 'actual_end': actual_end})
                vehicle.write({'operational_status': 'available', 'technical_ready': True})
                if service.next_service_date:
                    vehicle.next_service_date = service.next_service_date

    snapshot = fields.Datetime.now()
    # 20 available (two administratively blocked), 8 rented, 3 inspection,
    # 3 running maintenance, 2 archived; all are synthetic current snapshots.
    for idx, vehicle in enumerate(vehicles):
        if idx < 20:
            vehicle.write({'operational_status': 'available', 'technical_ready': True})
            if idx in (18, 19):
                vehicle.write({'rental_blocked': True, 'block_reason':
                    'Giữ xe cho kiểm kê tài sản — tình huống demo' if idx == 18 else
                    'Tạm giữ xe phục vụ đào tạo nhân viên — tình huống demo'})
        elif idx < 28:
            vehicle.write({'operational_status': 'available', 'technical_ready': True})
            vehicle.operational_status = 'rented'
            vehicle.location = 'Đang giao khách — trạng thái demo, chưa có đơn Rental'
        elif idx < 31:
            vehicle.write({'operational_status': 'available', 'technical_ready': True})
            vehicle.operational_status = 'rented'
            vehicle.write({'operational_status': 'inspection', 'technical_ready': False})
            vehicle.location = 'Khu vực chờ kiểm tra sau trả xe — demo'
        elif idx < 34:
            start = snapshot - timedelta(hours=3 + idx % 3)
            repair = E['fleet.vehicle.log.services'].create({
                'vehicle_id': vehicle.id, 'company_id': E.company.id,
                'service_type_id': types['brakes' if idx % 2 else 'electric'].id,
                'maintenance_type': 'corrective', 'date': END,
                'description': 'Đang sửa chữa để đưa xe trở lại khai thác — demo',
                'scheduled_start': start, 'scheduled_end': snapshot + timedelta(days=1, hours=idx % 3),
                'vendor_id': vendors[idx % 3].id, 'technician_id': technicians[idx % 4].id,
                'amount': [450000, 650000, 900000][idx % 3],
                'notes': 'Chi phí dự kiến cho hồ sơ đang thực hiện; dữ liệu giả lập.'})
            bind('current_repair_' + str(idx), repair)
            repair.write({'state': 'running', 'actual_start': start})
            vehicle.write({'operational_status': 'maintenance', 'technical_ready': False})
            vehicle.location = 'Xưởng sửa chữa — demo'
        else:
            vehicle.write({'operational_status': 'available', 'technical_ready': True})
            vehicle.operational_status = 'rented'
            vehicle.write({'operational_status': 'inspection', 'technical_ready': False})
            vehicle.write({'active': False, 'rental_blocked': True,
                'block_reason': 'Ngừng khai thác phục vụ đối chiếu tài sản — demo',
                'location': 'Khu vực xe đã ngừng khai thác'})

    # Future bookings are kept away from running/inspection/archived vehicles.
    for idx in range(12):
        vehicle = vehicles[idx]
        day = END + timedelta(days=3 + idx * 2)
        start = at_local(day, 9 + idx % 3)
        scheduled = E['fleet.vehicle.log.services'].create({
            'vehicle_id': vehicle.id, 'company_id': E.company.id,
            'service_type_id': types['periodic'].id, 'maintenance_type': 'preventive',
            'date': day, 'description': 'Lịch bảo dưỡng sắp tới — demo',
            'scheduled_start': start, 'scheduled_end': start + timedelta(hours=2),
            'technician_id': technicians[idx % 4].id, 'vendor_id': vendors[idx % 3].id,
            'amount': 0, 'notes': 'Chưa phát sinh chi phí; sẽ nhập chi phí thực tế khi thực hiện.'})
        scheduled.state = 'scheduled'
        vehicle.next_service_date = day
        bind('future_' + str(idx), scheduled)
    for idx in range(2):
        draft = E['fleet.vehicle.log.services'].create({
            'vehicle_id': vehicles[14 + idx].id, 'company_id': E.company.id,
            'service_type_id': types['electric'].id, 'maintenance_type': 'preventive',
            'date': END, 'description': 'Đề xuất kiểm tra bộ sạc — chưa chốt lịch demo',
            'blocks_rental': False, 'amount': 0})
        bind('draft_' + str(idx), draft)
    bind('seed_complete', E.company)

# Audit before committing; also used on reruns without creating duplicate records.
vehicle_ids = references('fleet.vehicle').mapped('res_id')
service_ids = references('fleet.vehicle.log.services').mapped('res_id')
vehicles = E['fleet.vehicle'].with_context(active_test=False).browse(vehicle_ids).exists()
services = E['fleet.vehicle.log.services'].with_context(active_test=False).browse(service_ids).exists()
assert len(vehicles) == 36
assert all(v.company_id == E.company for v in vehicles)
assert all(s.vehicle_id in vehicles and s.company_id == E.company for s in services)
assert all(v.technical_ready for v in vehicles if v.operational_status in ('available', 'rented'))
assert all((v.block_reason or '').strip() for v in vehicles if v.rental_blocked)
completed = services.filtered(lambda s: s.state == 'done')
assert all(s.result and s.actual_start and s.actual_end >= s.actual_start for s in completed)
assert all(s.vehicle_id.acquisition_date <= s.date < END for s in completed)
assert all(s.date >= BEGIN for s in services)
assert all(not s.actual_start for s in services if s.state in ('new', 'scheduled', 'cancelled'))
assert all(not s.vehicle_id.technical_ready for s in services if s.state == 'running' and s.blocks_rental)
monthly = Counter(s.date.strftime('%Y-%m') for s in completed)
expected_months = {(BEGIN + timedelta(days=offset)).strftime('%Y-%m')
                   for offset in range((END - BEGIN).days)}
assert set(monthly) == expected_months, monthly
for vehicle in vehicles:
    history = completed.filtered(lambda s: s.vehicle_id == vehicle).sorted('actual_start')
    assert all(first.actual_end <= second.actual_start for first, second in zip(history, history[1:]))
assert E.company.currency_id.name == 'VND'
# Verify saved dates and manually entered current states.
for service in services.filtered(lambda s: s.state == 'scheduled'):
    assert service.scheduled_start and service.scheduled_end > service.scheduled_start
for service in services.filtered(lambda s: s.state == 'running'):
    assert service.vehicle_id.operational_status == 'maintenance'

status = Counter(v.operational_status if v.active else 'archived' for v in vehicles)
monthly_costs = {month: int(sum(s.amount for s in completed if s.date.strftime('%Y-%m') == month))
                 for month in sorted(monthly)}
summary = {
    'database': DATABASE, 'period_start': str(BEGIN), 'period_end_exclusive': str(END),
    'synthetic': True, 'currency': 'VND', 'new_vehicles': len(vehicles),
    'vehicles_total_including_initial_demo': E['fleet.vehicle'].with_context(active_test=False).search_count([]),
    'new_models': len(references('fleet.vehicle.model')),
    'new_vendors': 3, 'new_technicians': 4, 'services': len(services),
    'service_states': dict(Counter(services.mapped('state'))), 'vehicle_states': dict(status),
    'blocked_active_vehicles': len(vehicles.filtered(lambda v: v.active and v.rental_blocked)),
    'completed_maintenance_cost_vnd': int(sum(completed.mapped('amount'))),
    'monthly_completed_services': dict(sorted(monthly.items())), 'monthly_cost_vnd': monthly_costs,
    'rental_contracts_created': 0, 'inspection_records_created': 0,
}
E.cr.commit()
Path('docs/FLEET_YEAR_DEMO_SUMMARY.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
