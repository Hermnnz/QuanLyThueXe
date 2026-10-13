"""Verify Week 7 over authenticated Odoo RPC, cleaning up only our test records."""
import sys
import time
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
    response = session.post(base + path, json={'jsonrpc': '2.0', 'method': 'call', 'params': params, 'id': 1}, timeout=30)
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

auth = rpc('/web/session/authenticate', {'db': 'motorbike_fleet_simple_20261002', 'login': 'admin', 'password': 'admin'})
assert auth['uid']
all_rows = {'context': {'active_test': False}}
before = {m: call(m, 'search_count', [[]], all_rows) for m in ['fleet.vehicle', 'fleet.vehicle.log.services']}
vehicle = service = None
try:
    model = call('fleet.vehicle.model', 'search_read', [[]], {'fields': ['id'], 'limit': 1})[0]['id']
    vehicle = one(call('fleet.vehicle', 'create', [{'model_id': model, 'is_electric_motorbike': True,
        'vehicle_code': 'TEMP-W7-WEB-CHECK', 'license_plate': 'TEMP-W7'}]))
    rejected('fleet.vehicle', 'write', [[vehicle], {'operational_status': 'available'}])
    call('fleet.vehicle', 'action_confirm_technical_ready', [[vehicle]])
    service = one(call('fleet.vehicle.log.services', 'create', [{'vehicle_id': vehicle,
        'scheduled_start': '2026-10-09 02:00:00', 'scheduled_end': '2026-10-09 06:00:00',
        'date': '2026-10-09', 'next_service_date': '2026-12-01', 'result': 'Kiểm thử tuần 7'}]))
    call('fleet.vehicle.log.services', 'action_schedule', [[service]])
    call('fleet.vehicle.log.services', 'action_start', [[service]])
    row = call('fleet.vehicle', 'read', [[vehicle], ['operational_status', 'technical_ready']])[0]
    assert row['operational_status'] == 'maintenance' and not row['technical_ready']
    rejected('fleet.vehicle', 'action_confirm_technical_ready', [[vehicle]])
    call('fleet.vehicle.log.services', 'action_done', [[service]])
    row = call('fleet.vehicle', 'read', [[vehicle], ['operational_status', 'technical_ready', 'next_service_date']])[0]
    assert row['operational_status'] == 'pending_inspection' and not row['technical_ready']
    assert row['next_service_date'] == '2026-12-01'
    call('fleet.vehicle', 'action_confirm_technical_ready', [[vehicle]])
    groups = call('fleet.vehicle', 'formatted_read_group', [[['id', '=', vehicle]], ['operational_status'], ['__count']],
                  {'context': {'read_group_expand': True}})
    assert {r['operational_status'] for r in groups} == {'available', 'renting', 'pending_inspection', 'maintenance'}
    results = call('fleet.vehicle', 'search_read', [[['vehicle_code', 'ilike', 'TEMP-W7'], ['operational_status', '=', 'available']]],
                   {'fields': ['id']})
    assert [r['id'] for r in results] == [vehicle]
    xmlids = call('ir.model.data', 'search_read', [[['module', '=', 'motorbike_fleet_management'],
        ['name', 'in', ['vehicle_kanban_electric', 'vehicle_search_electric', 'service_search_motorbike']]]],
        {'fields': ['name', 'res_id']})
    assert len(xmlids) == 3
    views = call('fleet.vehicle', 'get_views', [[(r['res_id'], 'kanban' if 'kanban' in r['name'] else 'search')
                                               for r in xmlids if r['name'] != 'service_search_motorbike']])
    assert 'kanban' in views['views'] and 'search' in views['views']
finally:
    if service:
        state = call('fleet.vehicle.log.services', 'read', [[service], ['state']])[0]['state']
        if state == 'running':
            call('fleet.vehicle.log.services', 'action_cancel', [[service]])
        call('fleet.vehicle.log.services', 'unlink', [[service]])
    if vehicle:
        call('fleet.vehicle', 'unlink', [[vehicle]])
after = {m: call(m, 'search_count', [[]], all_rows) for m in before}
assert before == after
print('Web RPC PASS: workflow, validation, search, four Kanban groups and view loading.')
print('Existing record counts retained:', after)
