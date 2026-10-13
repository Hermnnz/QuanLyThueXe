"""Execute demo seed via the locally configured Odoo shell, without logging credentials."""
import configparser
import os
from pathlib import Path
import subprocess
import sys

folder = Path(os.environ['TEMP']) / 'codex-fleet-simple-20261002'
runner = Path(os.environ['TEMP']) / 'codex-fleet-week6-20261001' / 'run_odoo.py'
script = Path('scripts/seed_demo.py').read_text(encoding='utf-8-sig')
result = subprocess.run([sys.executable, str(runner), 'shell', '-c', str(folder / 'odoo.conf'),
                         '--no-http'], input=script, encoding='utf-8')
sys.exit(result.returncode)
