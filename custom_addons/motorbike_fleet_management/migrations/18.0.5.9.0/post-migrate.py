from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    # One-time copy, including archived vehicles. Subsequent upgrades must not
    # overwrite each vehicle's independent settings.
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.flush_all()
    cr.execute("""UPDATE fleet_vehicle v SET
        service_interval_km = COALESCE(m.service_interval_km, 0),
        service_interval_months = COALESCE(m.service_interval_months, 0),
        service_warning_km = COALESCE(m.service_warning_km, 200),
        service_warning_days = COALESCE(m.service_warning_days, 7)
        FROM fleet_vehicle_model m WHERE v.model_id = m.id""")
    env.invalidate_all(flush=False)
    vehicles = env['fleet.vehicle'].with_context(active_test=False).search([])
    vehicles._compute_service_schedule()
    vehicles._compute_service_alert()
    old_view = env.ref('motorbike_fleet_management.service_policy_form', raise_if_not_found=False)
    if old_view:
        old_view.active = False
