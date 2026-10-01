from odoo import api, SUPERUSER_ID
from odoo.exceptions import ValidationError


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    vehicles = env['fleet.vehicle'].with_context(active_test=False).search([
        ('is_electric_motorbike', '=', True),
    ])
    for vehicle in vehicles:
        if vehicle.current_battery_id or not (
            vehicle.battery_serial or vehicle.battery_capacity_kwh or vehicle.battery_voltage
            or vehicle.battery_warranty_until or vehicle.battery_health != 100
        ):
            continue
        if vehicle.battery_serial and env['motorbike.battery'].with_context(active_test=False).search_count([
            ('serial_number', '=', vehicle.battery_serial),
        ]):
            raise ValidationError('Serial pin cũ bị trùng: %s. Cần đối chiếu dữ liệu trước khi nâng cấp.' % vehicle.battery_serial)
        battery = env['motorbike.battery'].create({
            'battery_code': 'LEGACY-VEH-%s' % vehicle.id,
            'serial_number': vehicle.battery_serial,
            'capacity_kwh': vehicle.battery_capacity_kwh,
            'voltage': vehicle.battery_voltage,
            'soh': vehicle.battery_health,
            'warranty_expiry': vehicle.battery_warranty_until,
            'status': 'installed',
            # SOC is unknown in Week 5. Do not assume a charged battery.
        })
        env['motorbike.battery.assignment'].create({
            'vehicle_id': vehicle.id, 'battery_id': battery.id,
            'install_odo': vehicle.odometer,
            'reason': 'Chuyển dữ liệu tuần 5 sang V2; thời điểm gắn thực tế chưa được ghi nhận.',
        })
