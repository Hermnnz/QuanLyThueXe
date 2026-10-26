from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.flush_all()
    for table in ['fleet_vehicle', 'fleet_vehicle_model', 'fleet_vehicle_log_services']:
        cr.execute('UPDATE ' + table + ' t SET write_uid=b.write_uid, write_date=b.write_date FROM periodic_audit_' + table + ' b WHERE t.id=b.id')
    env.invalidate_all(flush=False)
