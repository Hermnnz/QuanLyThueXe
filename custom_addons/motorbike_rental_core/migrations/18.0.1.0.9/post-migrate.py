def migrate(cr, version):
    cr.execute(
        'ALTER TABLE rental_contract '
        'DROP CONSTRAINT IF EXISTS rental_contract_valid_rental_day_limits'
    )
    cr.execute(
        'ALTER TABLE rental_contract '
        'DROP COLUMN IF EXISTS min_rental_days'
    )
    cr.execute(
        'ALTER TABLE rental_contract '
        'DROP COLUMN IF EXISTS max_rental_days'
    )
