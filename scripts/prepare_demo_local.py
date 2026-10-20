"""Load the optional small demo using the committed runner and current local config."""
import argparse
import configparser
import os
from pathlib import Path
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
if cfg['options'].get('db_name') != 'motorbike_fleet_simple_20261002':
    raise SystemExit('This fixture is restricted to the named Fleet demo database')
script = (workspace / 'scripts/seed_demo.py').read_text(encoding='utf-8-sig')
result = subprocess.run([sys.executable, str(workspace / 'scripts/run_odoo_local.py'),
                         'shell', '-c', str(config), '--no-http'],
                        input=script, encoding='utf-8', cwd=workspace)
sys.exit(result.returncode)
