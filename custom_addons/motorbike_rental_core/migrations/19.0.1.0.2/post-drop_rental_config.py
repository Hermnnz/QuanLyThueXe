def migrate(cr, version):
    cr.execute('DROP TABLE IF EXISTS rental_config')