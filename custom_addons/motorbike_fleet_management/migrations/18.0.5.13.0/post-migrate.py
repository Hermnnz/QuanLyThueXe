def migrate(cr, version):
    # Existing archived electric vehicles become visible in their dedicated column.
    cr.execute("UPDATE fleet_vehicle SET operational_status='inactive', technical_ready=false WHERE active=false AND is_electric_motorbike=true")
