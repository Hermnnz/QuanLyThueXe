def migrate(cr, version):
    for table in ['fleet_vehicle', 'fleet_vehicle_model', 'fleet_vehicle_log_services']:
        cr.execute('CREATE TEMP TABLE periodic_audit_' + table + ' ON COMMIT DROP AS SELECT id, write_uid, write_date FROM ' + table)
