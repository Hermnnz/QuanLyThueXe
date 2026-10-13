"""Verify Fleet's public integration methods through authenticated Odoo RPC.

Creates and deletes only isolated TEMP-W8 records; never changes existing vehicles.
"""
import sys
import time
from xml.etree import ElementTree

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'C:/odoo/venv/Lib/site-packages')
import requests

base = 'http://127.0.0.1:8072'
session = requests.Session()
for attempt in range(20):
    try:
        session.get(base + '/web/login', timeout=2).raise_for_status()
        break
    except requests.RequestException:
        time.sleep(1)
else:
    raise SystemExit('Demo server not ready')


def rpc(path, params):
    response = session.post(base + path, json={
        'jsonrpc': '2.0', 'method': 'call', 'params': params, 'id': 1}, timeout=30)
    response.raise_for_status()
    data = response.json()
    if 'error' in data:
        raise RuntimeError(data['error'].get('data', {}).get('message', data['error']['message']))
    return data['result']


def call(model, method, args, kwargs=None):
    return rpc('/web/dataset/call_kw/' + model + '/' + method,
               {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}})


def one(value):
    return value[0] if isinstance(value, list) else value


def rejected(model, method, args):
    try:
        call(model, method, args)
    except RuntimeError:
        return
    raise AssertionError('Expected rejected operation: ' + method)


auth = rpc('/web/session/authenticate', {
    'db': 'motorbike_fleet_simple_20261002', 'login': 'admin', 'password': 'admin'})
assert auth['uid']
all_rows = {'context': {'active_test': False}}
models = ['fleet.vehicle', 'fleet.vehicle.log.services', 'fleet.vehicle.odometer']
before = {m: call(m, 'search_count', [[]], all_rows) for m in models}
vehicle = service = None
start, end = '2026-12-01 02:00:00', '2026-12-03 02:00:00'
try:
    model = call('fleet.vehicle.model', 'search_read', [[]], {'fields': ['id'], 'limit': 1})[0]['id']
    vehicle = one(call('fleet.vehicle', 'create', [{
        'model_id': model, 'is_electric_motorbike': True, 'vehicle_code': 'TEMP-W8-WEB-CHECK',
        'license_plate': 'TEMP-W8', 'operational_status': 'available', 'technical_ready': True}]))
    rejected('fleet.vehicle', 'create', [{'model_id': model, 'vehicle_code': 'TEMP-W8-WEB-CHECK'}])
    eligibility = lambda: call('fleet.vehicle', 'check_fleet_availability', [[vehicle], start, end])[0]
    assert eligibility()['fleet_ok']
    call('fleet.vehicle', 'action_deliver_vehicle', [[vehicle], start, end], {
        'odometer_start': 100, 'checkout_at': start})
    # Invalid result and decreasing ODO must be rejected without changing rental state.
    rejected('fleet.vehicle', 'action_return_vehicle', [[vehicle], 'available'])
    try:
        call('fleet.vehicle', 'action_return_vehicle', [[vehicle], 'passed'], {
            'odometer_end': 99, 'checkin_at': end})
    except RuntimeError:
        pass
    else:
        raise AssertionError('Decreasing ODO accepted')
    call('fleet.vehicle', 'action_return_vehicle', [[vehicle], 'passed'], {
        'odometer_end': 150, 'checkin_at': end})
    row = call('fleet.vehicle', 'read', [[vehicle], ['operational_status', 'technical_ready', 'odometer']])[0]
    assert row['operational_status'] == 'available' and row['technical_ready'] and row['odometer'] == 150
    rejected('fleet.vehicle', 'action_return_vehicle', [[vehicle], 'passed'])
    call('fleet.vehicle', 'action_deliver_vehicle', [[vehicle], start, end])
    call('fleet.vehicle', 'action_return_vehicle', [[vehicle], 'failed'])
    assert not eligibility()['fleet_ok']
    call('fleet.vehicle', 'action_confirm_technical_ready', [[vehicle]])
    service = one(call('fleet.vehicle.log.services', 'create', [{
        'vehicle_id': vehicle, 'scheduled_start': start, 'scheduled_end': end}]))
    call('fleet.vehicle.log.services', 'action_schedule', [[service]])
    assert 'blocking_maintenance' in eligibility()['reasons']
    rejected('fleet.vehicle', 'action_deliver_vehicle', [[vehicle], start, end])
    boundary = call('fleet.vehicle', 'check_fleet_availability', [[vehicle], end, '2026-12-04 02:00:00'])[0]
    assert boundary['fleet_ok']
    call('fleet.vehicle.log.services', 'action_cancel', [[service]])
    assert eligibility()['fleet_ok']
    groups = call('fleet.vehicle', 'formatted_read_group', [
        [['id', '=', vehicle]], ['operational_status'], ['__count']], {'context': {'read_group_expand': True}})
    assert {r['operational_status'] for r in groups} == {
        'available', 'renting', 'pending_inspection', 'maintenance'}
    views = call('fleet.vehicle', 'get_views', [[(False, 'list'), (False, 'form'), (False, 'kanban'), (False, 'search')]])
    assert {'list', 'form', 'kanban', 'search'} <= views['views'].keys()
    form = ElementTree.fromstring(views['views']['form']['arch'])
    for field in ['operational_status', 'technical_ready']:
        nodes = form.findall(".//field[@name='" + field + "']")
        assert nodes and all(node.get('readonly') in ('1', 'True', 'true') for node in nodes)
    call('fleet.vehicle', 'write', [[vehicle], {'active': False}])
    rejected('fleet.vehicle', 'create', [{'model_id': model, 'vehicle_code': 'TEMP-W8-WEB-CHECK'}])
finally:
    if service:
        call('fleet.vehicle.log.services', 'unlink', [[service]])
    if vehicle:
        logs = call('fleet.vehicle.odometer', 'search', [[('vehicle_id', '=', vehicle)]])
        if logs:
            call('fleet.vehicle.odometer', 'unlink', [logs])
        call('fleet.vehicle', 'unlink', [[vehicle]])

after = {m: call(m, 'search_count', [[]], all_rows) for m in models}
assert before == after
print('Web RPC PASS: delivery, explicit return, native ODO, maintenance intervals, unique codes, readonly form and four states.')
print('Existing record counts retained:', after)
