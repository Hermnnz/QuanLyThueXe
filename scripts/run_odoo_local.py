"""Run the existing Windows Odoo installation with the selected Python runtime."""
import os
import site
import sys

root = os.environ.get('ODOO_ROOT', 'C:/odoo')
dependency_path = os.environ.get('ODOO_DEPENDENCIES')
if dependency_path:
    site.addsitedir(dependency_path)
site.addsitedir(root + '/venv/Lib/site-packages')
sys.path.insert(0, root + '/venv/Lib/site-packages')
sys.path.insert(0, root)
import odoo.cli

odoo.cli.main()
