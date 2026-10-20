from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("SELECT id FROM fleet_vehicle WHERE vehicle_code IS NULL OR BTRIM(vehicle_code)='' ORDER BY id")
    for (vehicle_id,) in cr.fetchall():
        while True:
            code = env['ir.sequence'].next_by_code('motorbike.fleet.vehicle')
            cr.execute('SELECT 1 FROM fleet_vehicle WHERE vehicle_code_key=%s', (code,))
            if not cr.fetchone():
                break
        # Add missing identifiers without rewriting unrelated historical audit fields.
        cr.execute('UPDATE fleet_vehicle SET vehicle_code=%s, vehicle_code_key=%s WHERE id=%s',
                   (code, code, vehicle_id))
    # SQL duplicate-plate corrections happen before schema loading; refresh only
    # the derived display names, without changing source fields or audit timestamps.
    env['fleet.vehicle'].with_context(active_test=False).search([
        ('license_plate', '=', False)])._compute_vehicle_name()
    env.flush_all()
    cr.execute('UPDATE fleet_vehicle v SET write_uid=b.write_uid, write_date=b.write_date '
               'FROM fleet_audit_before_1955 b WHERE v.id=b.id')
    env.invalidate_all(flush=False)
