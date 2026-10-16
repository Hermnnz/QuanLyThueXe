import re


def migrate(cr, version):
    # Refuse an ambiguous upgrade rather than silently failing to add uniqueness.
    cr.execute('SELECT id, license_plate, vehicle_code FROM fleet_vehicle ORDER BY id')
    plates, codes = {}, {}
    for record_id, plate, code in cr.fetchall():
        for seen, value, label in [
                (plates, re.sub(r'[\W_]+', '', plate or '').upper(), 'biển số'),
                (codes, ''.join((code or '').split()).upper(), 'mã xe')]:
            if value and value in seen:
                raise RuntimeError('Cần xử lý trùng %s ở xe ID %s và %s trước khi nâng cấp Fleet.' % (
                    label, seen[value], record_id))
            if value:
                seen[value] = record_id
    # Adding stored identity keys makes Odoo recompute all vehicle rows. Preserve
    # the original author/time metadata for this mechanical schema migration.
    cr.execute('CREATE TEMP TABLE fleet_audit_before_1955 ON COMMIT DROP AS '
               'SELECT id, write_uid, write_date FROM fleet_vehicle')

    cr.execute("UPDATE fleet_vehicle SET operational_status = CASE operational_status WHEN 'rented' THEN 'renting' WHEN 'inspection' THEN 'pending_inspection' END WHERE operational_status IN ('rented', 'inspection')")
