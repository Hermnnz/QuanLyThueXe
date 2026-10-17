"""Back up the named Fleet demo and load its idempotent one-year fixture."""
import argparse
import configparser
from datetime import datetime
import os
from pathlib import Path
import shutil
import subprocess
import sys

workspace = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--config', default=str(Path(os.environ['TEMP']) / 'codex-fleet-integration-20261012/demo.conf'))
args = parser.parse_args()
config = Path(args.config).expanduser().resolve()
cfg = configparser.ConfigParser()
if not cfg.read(config):
    raise SystemExit('Local demo config not found; configure the current demo first or pass --config')
o = cfg['options']
if o.get('db_name') != 'motorbike_fleet_simple_20261002':
    raise SystemExit('This fixture is restricted to the named Fleet demo database')
backup = workspace / 'archive' / ('before-year-demo-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(parents=True)
process_env = os.environ.copy()
process_env['PGPASSWORD'] = o['db_password']
subprocess.run(['C:/Program Files/PostgreSQL/18/bin/pg_dump.exe',
                '-h', o['db_host'], '-p', o['db_port'], '-U', o['db_user'],
                '-Fc', '-f', str(backup / 'database.dump'), o['db_name']],
               env=process_env, check=True)
filestore = Path(o['data_dir']) / 'filestore' / o['db_name']
if filestore.exists():
    shutil.copytree(filestore, backup / 'filestore' / o['db_name'])
print('Database and filestore backup:', backup, flush=True)
script = (workspace / 'scripts/seed_year_demo.py').read_text(encoding='utf-8-sig')
result = subprocess.run([sys.executable, str(workspace / 'scripts/run_odoo_local.py'),
                         'shell', '-c', str(config), '--no-http',
                         '--logfile', str(config.parent / 'year-seed.log')],
                        input=script, encoding='utf-8', cwd=workspace)
sys.exit(result.returncode)
