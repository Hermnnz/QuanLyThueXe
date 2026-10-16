"""Fresh Fleet integration test DB or backed-up upgrade with state-key migration.

Uses local Odoo credentials, never prints them. Tests roll back their records.
"""
import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, 'C:/odoo/venv/Lib/site-packages')
import psycopg2
from psycopg2 import sql

parser = argparse.ArgumentParser()
parser.add_argument('--upgrade', action='store_true')
parser.add_argument('--config', default='C:/odoo/odoo.conf')
parser.add_argument('--database', help='Fresh test DB only')
parser.add_argument('--report', default='FLEET_INTEGRATION_DATA_PRESERVATION.json', help='Preservation report filename in docs')
parser.add_argument('--clear-plate-id', type=int, action='append', default=[], help='Explicitly approved duplicate-plate record IDs to clear after backup')
args = parser.parse_args()
workspace = Path(__file__).resolve().parents[1]
folder = Path(os.environ['TEMP']) / 'codex-fleet-integration-20261012'
folder.mkdir(exist_ok=True)
config = configparser.ConfigParser()
if not config.read(args.config):
    raise SystemExit('Local Odoo config not found')
options = config['options']
demo = 'motorbike_fleet_simple_20261002'
database = demo if args.upgrade else (args.database or 'motorbike_fleet_integration_clean_20261012')
options['addons_path'] = 'C:/odoo/addons,' + str(workspace / 'custom_addons')
options['db_name'] = database
options['dbfilter'] = '^' + database + '$'
options['http_port'] = '8072'
options['data_dir'] = str(folder / 'data')
config_path = folder / ('demo.conf' if args.upgrade else database + '.conf')
with config_path.open('w', encoding='utf-8') as stream:
    config.write(stream)

credentials = dict(host=options['db_host'], port=options['db_port'],
                   user=options['db_user'], password=options['db_password'])
missing_code_ids = set()
approved_plate_changes = {}

def snapshot():
    with psycopg2.connect(dbname=demo, **credentials) as connection:
        with connection.cursor() as cursor:
            output = {}
            for table in ['fleet_vehicle', 'fleet_vehicle_log_services', 'fleet_vehicle_odometer']:
                cursor.execute(sql.SQL('SELECT row_to_json(t)::text FROM {} t ORDER BY id').format(sql.Identifier(table)))
                rows = [json.loads(r[0]) for r in cursor.fetchall()]
                if table == 'fleet_vehicle':
                    for row in rows:
                        # 19.0.5.4 adds the stored current ODO column. Check its
                        # initialization separately; preserve every existing column.
                        row.pop('odometer', None)
                        row.pop('license_plate_key', None)
                        row.pop('vehicle_code_key', None)
                        if row['id'] in missing_code_ids:
                            row['vehicle_code'] = None
                        if row['id'] in args.clear_plate_id:
                            row['license_plate'] = None
                            row['name'] = None  # Derived display name follows the approved plate change.
                        row['operational_status'] = {'rented': 'renting', 'inspection': 'pending_inspection'}.get(
                            row['operational_status'], row['operational_status'])
                encoded = json.dumps(rows, sort_keys=True, ensure_ascii=False)
                output[table] = {'count': len(rows), 'normalized_sha256': hashlib.sha256(encoded.encode()).hexdigest()}
            return output

def state_counts():
    with psycopg2.connect(dbname=demo, **credentials) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT operational_status, count(*) FROM fleet_vehicle GROUP BY operational_status')
            return dict(cursor.fetchall())

def current_odometer_snapshot():
    with psycopg2.connect(dbname=demo, **credentials) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                           "WHERE table_name='fleet_vehicle' AND column_name='odometer')")
            if cursor.fetchone()[0]:
                cursor.execute('SELECT id, COALESCE(odometer, 0) FROM fleet_vehicle ORDER BY id')
            else:
                cursor.execute('SELECT v.id, COALESCE(MAX(o.value), 0) FROM fleet_vehicle v '
                               'LEFT JOIN fleet_vehicle_odometer o ON o.vehicle_id=v.id '
                               'GROUP BY v.id ORDER BY v.id')
            return dict(cursor.fetchall())


before = None
if args.upgrade:
    with psycopg2.connect(dbname=demo, **credentials) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM fleet_vehicle WHERE vehicle_code IS NULL OR BTRIM(vehicle_code)='' ")
            missing_code_ids = {r[0] for r in cursor.fetchall()}
            if args.clear_plate_id:
                cursor.execute('SELECT id, license_plate FROM fleet_vehicle WHERE id=ANY(%s)', (args.clear_plate_id,))
                approved_plate_changes = dict(cursor.fetchall())
                if set(approved_plate_changes) != set(args.clear_plate_id):
                    raise SystemExit('Approved plate ID not found; no changes applied')
    before = snapshot()
    odometer_before = current_odometer_snapshot()
    states_before = state_counts()
    with psycopg2.connect(dbname=demo, **credentials) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT vehicle_code FROM fleet_vehicle WHERE vehicle_code IS NOT NULL '
                           'GROUP BY vehicle_code HAVING count(*) > 1')
            if cursor.fetchall():
                raise SystemExit('Duplicate vehicle codes: resolve explicitly before upgrade; no data renamed')
    backup = workspace / 'archive' / ('before-fleet-integration-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True)
    process_env = os.environ.copy()
    process_env['PGPASSWORD'] = options['db_password']
    subprocess.run(['C:/Program Files/PostgreSQL/18/bin/pg_dump.exe',
                    '-h', options['db_host'], '-p', options['db_port'], '-U', options['db_user'],
                    '-Fc', '-f', str(backup / 'database.dump'), demo], env=process_env, check=True)
    previous = Path(os.environ['TEMP']) / 'codex-fleet-week7-20261009/data/filestore' / demo
    current = folder / 'data/filestore' / demo
    available = current if current.exists() else previous if previous.exists() else workspace / 'archive/year-demo-20261002/filestore' / demo
    if available.exists():
        shutil.copytree(available, backup / 'filestore' / demo)
    if available.exists() and not (folder / 'data/filestore' / demo).exists():
        shutil.copytree(available, folder / 'data/filestore' / demo)
    print('Pre-upgrade backup:', backup, flush=True)
    if args.clear_plate_id:
        with psycopg2.connect(dbname=demo, **credentials) as connection:
            with connection.cursor() as cursor:
                cursor.execute('UPDATE fleet_vehicle SET license_plate=NULL WHERE id=ANY(%s)', (args.clear_plate_id,))
        print('Cleared only explicitly approved duplicate plates:', sorted(args.clear_plate_id), flush=True)
else:
    connection = psycopg2.connect(dbname='postgres', **credentials)
    connection.autocommit = True
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', (database,))
        if cursor.fetchone():
            raise SystemExit('Fresh database already exists; choose a new --database name')
        cursor.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C'").format(sql.Identifier(database)))
    connection.close()

logfile = folder / ('upgrade.log' if args.upgrade else database + '.log')
result = subprocess.run([sys.executable, '-X', 'utf8', str(workspace / 'scripts/run_odoo_local.py'),
                         '-c', str(config_path), '-d', database,
                         '-u' if args.upgrade else '-i', 'motorbike_fleet_management',
                         '--without-demo=all', '--test-enable', '--test-tags', '/motorbike_fleet_management',
                         # Odoo test mode can start HTTP despite --no-http. A private
                         # ephemeral port prevents open demo tabs attaching websocket
                         # requests to this short-lived upgrade/test process.
                         '--stop-after-init', '--no-http', '--http-port=0', '--logfile', str(logfile)])
print('Database:', database, '\nExit:', result.returncode, '\nLog:', logfile, flush=True)
if args.upgrade:
    after = snapshot()
    states_after = state_counts()
    expected_states = {}
    for state, count in states_before.items():
        renamed = {'rented': 'renting', 'inspection': 'pending_inspection'}.get(state, state)
        expected_states[renamed] = expected_states.get(renamed, 0) + count
    odometer_after = current_odometer_snapshot()
    preserved = before == after and odometer_before == odometer_after and states_after == expected_states and not (
        {'rented', 'inspection'} & states_after.keys())
    report = {'database': demo, 'expected_state_renames': {'rented': 'renting', 'inspection': 'pending_inspection'},
              'approved_plate_changes_before': approved_plate_changes,
              'generated_missing_code_ids': sorted(missing_code_ids),
              'current_odometer_before': odometer_before, 'current_odometer_after': odometer_after,
              'states_before': states_before, 'states_after': states_after,
              'before_normalized': before, 'after_normalized': after, 'only_expected_changes': preserved}
    (workspace / 'docs' / Path(args.report).name).write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Only expected state-key changes:', preserved)
    if not preserved:
        raise SystemExit('Unexpected existing data change; inspect preservation report and backup')
sys.exit(result.returncode)
