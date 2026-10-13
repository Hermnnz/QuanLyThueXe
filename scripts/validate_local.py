"""Check Week 6: clean installation, or upgrade the existing demo with its data intact."""
import configparser
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, 'C:/odoo/venv/Lib/site-packages')
import psycopg2
from psycopg2 import sql

folder = Path(os.environ['TEMP']) / 'codex-fleet-simple-20261002'
source = Path(os.environ['TEMP']) / 'codex-fleet-week6-20261001'
cfg = configparser.ConfigParser()
cfg.read(folder / 'odoo.conf')
o = cfg['options']
upgrade = '--upgrade' in sys.argv
database = 'motorbike_fleet_simple_20261002' if upgrade else 'motorbike_fleet_week6_crud_clean_20261002'
assert o['db_name'] == 'motorbike_fleet_simple_20261002'
if not upgrade:
    connection = psycopg2.connect(dbname='postgres', host=o['db_host'], port=o['db_port'],
                                 user=o['db_user'], password=o['db_password'])
    connection.autocommit = True
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', (database,))
        if cursor.fetchone():
            raise SystemExit('Clean test database already exists; do not overwrite it.')
        cursor.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C'").format(sql.Identifier(database)))
    connection.close()
    o['db_name'] = database
    o['dbfilter'] = '^' + database + '$'
    config_path = folder / 'week6_clean.conf'
    with config_path.open('w', encoding='utf-8') as stream:
        cfg.write(stream)
else:
    config_path = folder / 'odoo.conf'
logfile = folder / ('week6_upgrade.log' if upgrade else 'week6_clean.log')
command = [sys.executable, str(source / 'run_odoo.py'), '-c', str(config_path), '-d', database,
           '-u' if upgrade else '-i', 'motorbike_fleet_management', '--without-demo=all',
           '--test-enable', '--test-tags', '/motorbike_fleet_management', '--stop-after-init',
           '--no-http', '--logfile', str(logfile)]
result = subprocess.run(command)
print('Verification database:', database)
print('Exit status:', result.returncode)
print('Log:', logfile)
sys.exit(result.returncode)
