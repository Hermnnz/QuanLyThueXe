def migrate(cr, version):
    cr.execute("SELECT to_regclass('public.rental_contract'), to_regclass('public.rental_config')")
    contract_table, config_table = cr.fetchone()
    if not contract_table or not config_table:
        return

    cr.execute(
        """
        SELECT EXISTS (
            SELECT 1
              FROM information_schema.columns
             WHERE table_schema = 'public'
               AND table_name = 'rental_contract'
               AND column_name = 'rental_config_id'
        )
        """
    )
    has_config_field, = cr.fetchone()
    if not has_config_field:
        return

    cr.execute('ALTER TABLE rental_contract ADD COLUMN IF NOT EXISTS min_rental_days integer')
    cr.execute('ALTER TABLE rental_contract ADD COLUMN IF NOT EXISTS max_rental_days integer')
    cr.execute(
        """
        UPDATE rental_contract AS contract
           SET min_rental_days = COALESCE(config.min_rental_days, 1),
               max_rental_days = COALESCE(config.max_rental_days, 0)
          FROM rental_config AS config
         WHERE contract.rental_config_id = config.id
        """
    )
    cr.execute(
        """
        UPDATE rental_contract
           SET min_rental_days = COALESCE(min_rental_days, 1),
               max_rental_days = COALESCE(max_rental_days, 0)
         WHERE min_rental_days IS NULL OR max_rental_days IS NULL
        """
    )