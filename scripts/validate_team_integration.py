"""Install all team modules and run bridge/regression tests in a NEW Odoo 18 DB.

ODOO_ROOT selects the separate source runtime. Credentials are read from the
existing local configuration and written only to ignored archive files.
Never upgrades or resets the user's demonstration database.
"""
import argparse
import configparser
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, 'C:/odoo/venv/Lib/site-packages')
import psycopg2
from psycopg2 import sql

parser = argparse.ArgumentParser()
parser.add_argument('--database', required=True)
parser.add_argument('--upgrade-test-database', action='store_true')
parser.add_argument('--addons-directory', type=Path)
parser.add_argument('--install-only', action='store_true')
args = parser.parse_args()
if not args.database.startswith('fleet_team_test_'):
    raise SystemExit('Only dedicated fleet_team_test_* databases are allowed')
workspace = Path(__file__).resolve().parents[1]
config = configparser.ConfigParser()
config.read('C:/odoo/odoo.conf')
options = config['options']
credentials = {key: options['db_' + key] for key in ['host', 'port', 'user', 'password']}
connection = psycopg2.connect(dbname='postgres', **credentials)
connection.autocommit = True
with connection.cursor() as cursor:
    cursor.execute('SELECT 1 FROM pg_database WHERE datname=%s', (args.database,))
    exists = bool(cursor.fetchone())
    if exists and not args.upgrade_test_database:
        raise SystemExit('Test database exists; use a new name')
    if not exists:
        cursor.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C'").format(sql.Identifier(args.database)))
connection.close()
runtime = Path(os.environ['ODOO_ROOT'])
folder = workspace / 'archive' / args.database
folder.mkdir(exist_ok=True)
options.update({'addons_path': str(runtime / 'addons') + ',' + str(args.addons_directory or workspace / 'custom_addons'),
                'db_name': args.database, 'dbfilter': '^' + args.database + '$',
                'data_dir': str(folder / 'data'), 'http_port': '8078', 'gevent_port': '8079',
                'workers': '0', 'max_cron_threads': '0', 'logfile': str(folder / 'test.log')})
with (folder / 'test.conf').open('w', encoding='utf-8') as stream:
    config.write(stream)
modules = 'motorbike_fleet_management,motorbike_rental_core,motorbike_rental_operation,motorbike_rental_finance'
command = [sys.executable, '-X', 'utf8', str(workspace / 'scripts/run_odoo_local.py'),
           '-c', str(folder / 'test.conf'), '-d', args.database,
           '-i', modules, *(['-u', modules] if exists else []), '--without-demo=all',
           *(['--no-http'] if args.install_only else ['--test-enable', '--test-tags',
               '/motorbike_fleet_management,/motorbike_rental_core,/motorbike_rental_operation,/motorbike_rental_finance']),
           '--stop-after-init']
print('Testing all four modules on isolated database:', args.database, flush=True)
result = subprocess.run(command)
print('Test log:', folder / 'test.log', flush=True)
raise SystemExit(result.returncode)
