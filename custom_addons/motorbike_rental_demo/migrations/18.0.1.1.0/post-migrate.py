"""Refresh only the approved demo catalog labels; keep trips and negotiated prices."""
from pathlib import Path
from xml.etree import ElementTree as ET
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    catalog = Path(__file__).resolve().parents[2] / 'data' / 'catalog.xml'
    for node in ET.parse(catalog).findall('.//record'):
        label = node.find("field[@name='name']")
        record = env.ref('motorbike_rental_demo.' + node.get('id'), raise_if_not_found=False)
        if label is not None and record:
            record.write({'name': label.text})
    brands = env.ref('motorbike_rental_demo.demo_w8_brand_vinfast') | env.ref('motorbike_rental_demo.demo_w8_brand_datbike')
    env['fleet.vehicle.model.brand'].search([('id', 'not in', brands.ids), ('model_ids', '=', False)]).write({'active': False})
