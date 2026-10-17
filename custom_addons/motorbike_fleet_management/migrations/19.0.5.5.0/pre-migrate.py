def migrate(cr, version):
    # Adding stored identity keys makes Odoo recompute all vehicle rows. Preserve
    # the original author/time metadata for this mechanical schema migration.
    cr.execute('CREATE TEMP TABLE fleet_audit_before_1955 ON COMMIT DROP AS '
               'SELECT id, write_uid, write_date FROM fleet_vehicle')
