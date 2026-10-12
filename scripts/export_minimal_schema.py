"""Export and validate two-table schema from the minimal demo, without business data."""
import configparser
import argparse
import os
from pathlib import Path
import sys
sys.path.insert(0, 'C:/odoo/venv/Lib/site-packages')
import psycopg2
from psycopg2 import sql

parser = argparse.ArgumentParser()
parser.add_argument('--config', default=str(Path(os.environ['TEMP']) / 'codex-fleet-integration-20261012/demo.conf'))
args = parser.parse_args()
cfg = configparser.ConfigParser()
if not cfg.read(args.config):
    raise SystemExit('Local Odoo configuration not found')
o = cfg['options']
conn = psycopg2.connect(dbname=o['db_name'], host=o['db_host'], port=o['db_port'],
                        user=o['db_user'], password=o['db_password'])
tables = ['fleet_vehicle', 'fleet_vehicle_log_services']
parts = ['-- Fleet integration 19.0.5.1.0, snapshot 2026-10-12.',
         '-- Schema-only, includes Odoo core fields; NOT an Odoo installer or migration.',
         '-- Use only an isolated schema with shared Odoo reference tables available.',
         '-- Fleet methods and workflow live in ORM, not in this schema export.',
         '-- UTC timestamps; ORM defaults/ACL are not represented as SQL logic.', 'BEGIN;']
with conn.cursor() as cr:
    for table in tables:
        cr.execute('''SELECT a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull,
                             pg_get_expr(d.adbin, d.adrelid)
                      FROM pg_attribute a LEFT JOIN pg_attrdef d
                        ON d.adrelid=a.attrelid AND d.adnum=a.attnum
                      WHERE a.attrelid=%s::regclass AND a.attnum>0 AND NOT a.attisdropped
                      ORDER BY a.attnum''', ('public.' + table,))
        columns = []
        for name, datatype, required, default in cr.fetchall():
            definition = '    "' + name + '" ' + ('serial' if name == 'id' else datatype)
            if required:
                definition += ' NOT NULL'
            if default and name != 'id':
                definition += ' DEFAULT ' + default
            columns.append(definition)
        parts.append('CREATE TABLE "' + table + '" (\n' + ',\n'.join(columns) + '\n);')
    for table in tables:
        cr.execute('''SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint
                      WHERE conrelid=%s::regclass AND contype != 'n' ORDER BY conname''', ('public.' + table,))
        for name, definition in cr.fetchall():
            parts.append('ALTER TABLE "' + table + '" ADD CONSTRAINT "' + name + '" ' + definition + ';')
        cr.execute('''SELECT indexdef FROM pg_indexes i WHERE schemaname='public' AND tablename=%s
                      AND NOT EXISTS (SELECT 1 FROM pg_constraint c
                                      WHERE c.conindid=to_regclass('public.' || i.indexname))
                      ORDER BY indexname''', (table,))
        for (definition,) in cr.fetchall():
            parts.append(definition.replace(' ON public.', ' ON ') + ';')
    parts.append('COMMIT;')
    document = '\n\n'.join(parts) + '\n'
    # Roll back all verification objects; public is used only for shared FK targets.
    cr.execute('CREATE SCHEMA fleet_minimal_ddl_validation')
    cr.execute('SET LOCAL search_path TO fleet_minimal_ddl_validation, public')
    cr.execute('\n\n'.join(parts[6:-1]))
    for table in tables:
        cr.execute('''SELECT column_name, data_type, is_nullable FROM information_schema.columns
                      WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position''', ('public', table))
        original = cr.fetchall()
        cr.execute('''SELECT column_name, data_type, is_nullable FROM information_schema.columns
                      WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position''', ('fleet_minimal_ddl_validation', table))
        assert original == cr.fetchall(), table
conn.rollback()
conn.close()
output = Path('handoff/fleet_minimal/Fleet_Minimal_Current.sql')
output.write_text(document, encoding='utf-8')
print('Exported and transactionally verified both Fleet tables:', output)
