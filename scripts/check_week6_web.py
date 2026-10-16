"""Compatibility entry point for the current Fleet web verification."""
from pathlib import Path
import runpy

print('Week 6 editable-state CRUD is historical; checking the current Fleet workflow.', flush=True)
runpy.run_path(str(Path(__file__).with_name('check_fleet_integration_web.py')), run_name='__main__')
