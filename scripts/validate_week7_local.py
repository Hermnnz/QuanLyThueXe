"""Compatibility entry point: validate the current Fleet code, not a historical snapshot."""
from pathlib import Path
import runpy

print('Historical entry point: using the current backed-up Fleet validator.', flush=True)
runpy.run_path(str(Path(__file__).with_name('validate_fleet_integration_local.py')), run_name='__main__')
