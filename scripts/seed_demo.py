"""Optional small Week 6 CRUD fixture; existing records are preserved."""
from datetime import timedelta
from odoo import fields

assert env.cr.dbname == 'motorbike_fleet_simple_20261002'
if not env['fleet.vehicle'].with_context(active_test=False).search_count([('vehicle_code', '=', 'XE001')]):
    brand = env['fleet.vehicle.model.brand'].create({'name': 'Demo tuần 6'})
    model = env['fleet.vehicle.model'].create({'name': 'Xe điện demo', 'brand_id': brand.id, 'vehicle_type': 'bike'})
    vehicles = env['fleet.vehicle'].create([
        {'model_id': model.id, 'is_electric_motorbike': True, 'fuel_type': 'electric',
         'vehicle_code': 'XE00' + str(i), 'license_plate': 'MIN-EV-00' + str(i),
         'operational_status': ['available', 'inspection', 'maintenance'][i-1],
         'technical_ready': i == 1} for i in range(1, 4)])
    start = fields.Datetime.now() + timedelta(days=2)
    env['fleet.vehicle.log.services'].create({
        'vehicle_id': vehicles[0].id, 'maintenance_type': 'preventive',
        'description': 'Bảo dưỡng đã lên lịch — nhập tay',
        'scheduled_start': start, 'scheduled_end': start + timedelta(hours=3), 'state': 'scheduled'})
    env['fleet.vehicle.log.services'].create({
        'vehicle_id': vehicles[2].id, 'maintenance_type': 'corrective',
        'description': 'Sửa phanh — nhập tay', 'amount': 250000,
        'state': 'running', 'actual_start': fields.Datetime.now(),
        'result': 'Đang kiểm tra hệ thống phanh'})
    env.cr.commit()
print('Week 6 sample records available; existing data preserved.')
