from pathlib import Path
from xml.etree import ElementTree as ET
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    # Existing demo models are noupdate. Refresh ONLY the explicitly approved
    # maintenance policy fields, never replay trip workflow or historical logs.
    env = api.Environment(cr, SUPERUSER_ID, {})
    path = Path(__file__).resolve().parents[2] / 'data' / 'periodic_demo.xml'
    for node in ET.parse(path).findall(".//record[@model='fleet.vehicle.model']"):
        model = env.ref('motorbike_rental_demo.' + node.get('id'))
        values = {f.get('name'): float(f.text) if f.get('name') in ('service_interval_km', 'service_warning_km') else int(f.text)
                  for f in node.findall('field') if f.get('name') in (
                      'service_interval_km', 'service_interval_months', 'service_warning_km', 'service_warning_days')}
        model.write(values)
