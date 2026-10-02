"""Back up the existing minimal demo, then import a year of synthetic Fleet data."""
import configparser
from datetime import datetime
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, 'C:/odoo/venv/Lib/site-packages')
import psycopg2

folder = Path(os.environ['TEMP']) / 'codex-fleet-simple-20261002'
config = folder / 'odoo.conf'
cfg = configparser.ConfigParser()
cfg.read(config)
o = cfg['options']
assert o['db_name'] == 'motorbike_fleet_simple_20261002'
backup = folder / ('before-year-demo-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir()
pg_dump = Path('C:/Program Files/PostgreSQL/18/bin/pg_dump.exe')
process_env = os.environ.copy()
process_env['PGPASSWORD'] = o['db_password']
subprocess.run([str(pg_dump), '-h', o['db_host'], '-p', o['db_port'], '-U', o['db_user'],
                '-Fc', '-f', str(backup / 'database.dump'), o['db_name']], env=process_env, check=True)
filestore = Path(o['data_dir']) / 'filestore' / o['db_name']
if filestore.exists():
    shutil.copytree(filestore, backup / 'filestore' / o['db_name'])
print('Database and filestore backup:', backup, flush=True)
runner = Path(os.environ['TEMP']) / 'codex-fleet-week6-20261001/run_odoo.py'
script = Path('scripts/seed_year_demo.py').read_text(encoding='utf-8-sig')
result = subprocess.run([sys.executable, str(runner), 'shell', '-c', str(config), '--no-http',
                         '--logfile', str(folder / 'year-seed.log')], input=script, encoding='utf-8')
sys.exit(result.returncode)
