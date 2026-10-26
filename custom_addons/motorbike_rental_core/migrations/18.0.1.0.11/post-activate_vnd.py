def migrate(cr, version):
    cr.execute("UPDATE res_currency SET active = TRUE WHERE name = 'VND'")
    if cr.rowcount != 1:
        raise RuntimeError('Expected exactly one VND currency to activate.')
