"""Verify Week 6 demo CRUD via authenticated web RPC; remove only our temporary records."""
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'C:/odoo/venv/Lib/site-packages')
import requests

base = 'http://127.0.0.1:8072'
for attempt in range(20):
    try:
        requests.get(base + '/web/login', timeout=2).raise_for_status()
        break
    except requests.RequestException:
        time.sleep(1)
else:
    raise SystemExit('Demo did not start')
session = requests.Session()

def rpc(path, params):
    response = session.post(base + path, json={'jsonrpc': '2.0', 'method': 'call', 'params': params, 'id': 1}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if 'error' in payload:
        error = payload['error']
        raise RuntimeError(error.get('data', {}).get('message', error.get('message')))
    return payload['result']

def call(model, method, args, kwargs=None):
    return rpc('/web/dataset/call_kw/' + model + '/' + method,
               {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}})

def one(result):
    if isinstance(result, list):
        assert len(result) == 1
        return result[0]
    return result

auth = rpc('/web/session/authenticate', {'db': 'motorbike_fleet_simple_20261002', 'login': 'admin', 'password': 'admin'})
assert auth['uid']
context = {'context': {'active_test': False}}
assert call('fleet.vehicle', 'search_count', [[]], context) == 39
assert call('fleet.vehicle.log.services', 'search_count', [[]], context) == 300
vehicle_id = service_id = None
try:
    model = call('fleet.vehicle.model', 'search_read', [[]], {'fields': ['id'], 'limit': 1})[0]['id']
    vehicle_id = one(call('fleet.vehicle', 'create', [{'model_id': model, 'is_electric_motorbike': True,
        'vehicle_code': 'TEMP-W6-WEB-CHECK', 'operational_status': 'available', 'technical_ready': True}]))
    row = call('fleet.vehicle', 'read', [[vehicle_id], ['vehicle_code', 'operational_status']])[0]
    assert row['vehicle_code'] == 'TEMP-W6-WEB-CHECK'
    call('fleet.vehicle', 'write', [[vehicle_id], {'operational_status': 'rented', 'block_reason': 'Nhập liệu thử'}])
    service_id = one(call('fleet.vehicle.log.services', 'create', [{'vehicle_id': vehicle_id, 'state': 'done',
        'actual_start': '2026-09-01 02:00:00', 'actual_end': '2026-09-01 05:00:00',
        'amount': 500000, 'result': 'CRUD web'}]))
    call('fleet.vehicle.log.services', 'write', [[service_id], {'state': 'running',
        'actual_end': '2026-09-01 06:00:00', 'amount': 650000}])
    service = call('fleet.vehicle.log.services', 'read', [[service_id], ['amount', 'state', 'actual_end']])[0]
    assert service['amount'] == 650000 and service['state'] == 'running'
    assert service['actual_end'] == '2026-09-01 06:00:00'
    vehicle = call('fleet.vehicle', 'read', [[vehicle_id], ['operational_status']])[0]
    assert vehicle['operational_status'] == 'rented'
    for xmlid, forbidden in [
            ('vehicle_form_electric', ['action_confirm_technical_ready', 'action_return_for_inspection']),
            ('service_form_motorbike', ['action_schedule', 'action_start', 'action_done'])]:
        record = call('ir.model.data', 'search_read', [[['module', '=', 'motorbike_fleet_management'],
            ['name', '=', xmlid]]], {'fields': ['res_id']})[0]
        arch = call('ir.ui.view', 'read', [[record['res_id']], ['arch_db']])[0]['arch_db']
        assert all(name not in arch for name in forbidden)
finally:
    if service_id:
        call('fleet.vehicle.log.services', 'unlink', [[service_id]])
    if vehicle_id:
        call('fleet.vehicle', 'unlink', [[vehicle_id]])
assert call('fleet.vehicle', 'search_count', [[]], context) == 39
assert call('fleet.vehicle.log.services', 'search_count', [[]], context) == 300
print('Web CRUD passed: editable status/dates/cost; no automatic vehicle updates; temporary records removed.')
print('Demo data retained: 39 vehicles / 300 services. Admin login works on port 8072.')
