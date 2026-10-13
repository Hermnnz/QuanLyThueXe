def migrate(cr, version):
    cr.execute("SELECT to_regclass('public.rental_vehicle')")
    if not cr.fetchone()[0]:
        return

    cr.execute('SELECT count(*) FROM rental_vehicle')
    vehicle_count = cr.fetchone()[0]
    cr.execute('SELECT count(*) FROM rental_contract_line')
    contract_line_count = cr.fetchone()[0]
    if vehicle_count or contract_line_count:
        raise RuntimeError(
            'Cannot remove rental_vehicle prototype while vehicles or contract lines exist. '
            'Map existing vehicle IDs to the official vehicle module before upgrading.'
        )

    cr.execute(
        'ALTER TABLE rental_contract_line '
        'DROP CONSTRAINT IF EXISTS rental_contract_line_vehicle_id_fkey'
    )