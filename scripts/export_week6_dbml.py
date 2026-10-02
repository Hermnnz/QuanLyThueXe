"""Generate read-only DBML handoff from the current Week 6 schema snapshot."""
from pathlib import Path
import re

folder = Path('handoff/fleet_minimal')
sql = (folder/'Fleet_Minimal_Current.sql').read_text(encoding='utf-8')
tables = {}
for table, body in re.findall(r'CREATE TABLE "([^"]+)" \((.*?)\n\);', sql, re.S):
    cols = []
    for line in body.splitlines():
        match = re.match(r'\s*"([^"]+)"\s+(.+?)(,)?$', line)
        if not match:
            continue
        name, datatype = match.group(1), match.group(2)
        required = datatype.endswith(' NOT NULL')
        if required:
            datatype = datatype[:-9]
        cols.append((name, datatype, required))
    tables[table] = cols
assert set(tables) == {'fleet_vehicle', 'fleet_vehicle_log_services'}
refs = re.findall(r'ALTER TABLE "([^"]+)" ADD CONSTRAINT "([^"]+)" FOREIGN KEY \((\w+)\) REFERENCES (\w+)\((\w+)\) ON DELETE (SET NULL|RESTRICT);', sql)
indexes = re.findall(r'CREATE INDEX (\w+) ON (\w+) USING btree \((\w+)\);', sql)
shared = sorted({ref[3] for ref in refs} - set(tables))
notes = {
    'vehicle_code': 'Mã xe. Có index; hiện chưa có UNIQUE hoặc NOT NULL trong database.',
    'operational_status': 'available / rented / inspection / maintenance. Nhập tay; không phải PostgreSQL enum.',
    'technical_ready': 'Nhập tay ở tuần 6; chưa có workflow xác nhận kỹ thuật.',
    'rental_blocked': 'Ghi nhận khóa thuê; chưa có cơ chế chặn Rental.',
    'blocks_rental': 'Ghi nhận bảo dưỡng chặn thuê; chưa kiểm tra availability.',
    'maintenance_type': 'preventive / corrective / emergency. Selection Odoo lưu varchar.',
    'state': 'new / scheduled / running / done / cancelled. Trạng thái chuẩn Fleet mở rộng, nhập tay.',
    'amount': 'Chi phí chuẩn Odoo. cost là alias ORM, không có cột cost riêng.',
    'technician_id': 'FK tới res_partner, không phải res_users hoặc hr_employee.',
    'next_service_date': 'Nhập tay, không tự đồng bộ giữa xe và hồ sơ bảo dưỡng.',
    'actual_start': 'Thời gian thực tế nhập tay; timestamp UTC không timezone.',
    'actual_end': 'Thời gian thực tế nhập tay; timestamp UTC không timezone.',
    'active': 'Trường lưu trữ chuẩn Odoo.',
}

def column_type(datatype):
    if datatype == 'serial':
        return 'integer'
    if datatype == 'character varying':
        return 'varchar'
    return '"' + datatype + '"' if ' ' in datatype else datatype

def field_line(name, datatype, required):
    settings = []
    if name == 'id':
        settings += ['pk', 'increment']
    if required:
        settings.append('not null')
    if name in notes:
        settings.append("note: '" + notes[name].replace("'", "\\'") + "'")
    return '  ' + name + ' ' + column_type(datatype) + (' [' + ', '.join(settings) + ']' if settings else '')

def generate(filename, selected=None):
    is_core = selected is not None
    chosen = {t: [c for c in cols if not is_core or c[0] in selected[t]] for t, cols in tables.items()}
    relationships = [r for r in refs if r[2] in {c[0] for c in chosen[r[0]]}]
    externals = sorted({r[3] for r in relationships} - set(tables))
    if 'fleet_vehicle_model' in externals and 'fleet_vehicle_model_brand' not in externals:
        externals.append('fleet_vehicle_model_brand')
        externals.sort()
    lines = [
        '// Fleet & Maintenance, Week 6 only, Odoo 19 / motorbike_fleet_management 19.0.3.1.0.',
        '// Core business tables: fleet_vehicle and fleet_vehicle_log_services.',
        '// Brand/model catalogs show relevant verified columns; other shared tables are ID-only placeholders.',
        '// When merging: retain the group definition of each shared table and remove duplicate placeholders.',
        '// No Rental/Inspection model, availability, workflow, custom battery or custom odometer.',
        '// No SQL defaults, ENUM, UNIQUE or CHECK added beyond the implemented schema.',
        '// ' + ('Business ERD: only selected relevant columns; use the Physical file for all stored columns.' if is_core
                  else 'Physical ERD: every stored column, FK and explicit index of the two Fleet tables in the SQL snapshot.'),
        *(['// Pending teacher review: company_id, vendor_id, service_type_id, technician_id and their shared tables are omitted from this business diagram only.'] if is_core else []),
        '',
        'Project Fleet_Week6 {',
        "  database_type: 'PostgreSQL'",
        "  Note: 'Phạm vi tuần 6: hai model, ACL cơ bản, menu/action, List/Form và CRUD thủ công. Không phải sơ đồ toàn bộ dự án.'",
        '}', '',
    ]
    for table, cols in chosen.items():
        lines += ['Table ' + table + ' {']
        lines += [field_line(*c) for c in cols]
        applicable = [i for i in indexes if i[1] == table and i[2] in {c[0] for c in cols}]
        if applicable:
            lines += ['', '  indexes {']
            for name, _, col in applicable:
                lines.append('    ' + col + " [name: '" + name + "', type: btree]")
            lines += ['  }']
        lines += ['', "  Note: '" + ('Hồ sơ xe: kế thừa fleet.vehicle. Các trạng thái và mốc bảo dưỡng nhập bằng tay.' if table == 'fleet_vehicle'
                   else 'Hồ sơ bảo dưỡng: kế thừa fleet.vehicle.log.services. Quan hệ 1:N với xe; nhập tay trạng thái, thời gian và kết quả.') + "'", '}', '']
    lines += ['// STANDARD ODOO CATALOGS AND SHARED REFERENCES — not newly created custom models.',
              '// Replace these with the shared tables owned by the group; do not create duplicate tables.', '']
    for table in externals:
        if table == 'fleet_vehicle_model_brand':
            lines += ['Table fleet_vehicle_model_brand {',
                      '  id integer [pk, increment, not null]',
                      '  name varchar [not null]', '  active boolean',
                      "  Note: 'Hãng xe chuẩn Odoo. Các cột cần thiết cho ERD; không phải schema đầy đủ.'", '}', '']
            continue
        if table == 'fleet_vehicle_model':
            lines += ['Table fleet_vehicle_model {',
                      '  id integer [pk, increment, not null]',
                      '  brand_id integer [not null]', '  name varchar [not null]',
                      '  vehicle_type varchar [not null]', '  active boolean',
                      "  Note: 'Dòng/mẫu xe chuẩn Odoo, thuộc một hãng. Các cột cần thiết cho ERD; không phải schema đầy đủ.'", '}', '']
            continue
        lines += ['Table ' + table + ' {', '  id integer [pk]',
                  "  Note: 'Bảng chuẩn Odoo dùng chung. Chỉ khai báo id để vẽ FK; đây không phải toàn bộ định nghĩa của bảng.'", '}', '']
    lines += ['// FOREIGN KEYS — preserved from the implemented schema.', '']
    for source, name, col, target, target_col, delete in relationships:
        assert col in {c[0] for c in chosen[source]}
        assert target in set(chosen) | set(externals)
        action = 'set null' if delete == 'SET NULL' else 'restrict'
        lines.append('Ref ' + name + ': ' + source + '.' + col + ' > ' + target + '.' + target_col + ' [delete: ' + action + ']')
    lines.append('Ref fleet_vehicle_model_brand_id_fkey: fleet_vehicle_model.brand_id > fleet_vehicle_model_brand.id [delete: restrict]')
    document = '\n'.join(lines) + '\n'
    (folder/filename).write_text(document, encoding='utf-8')
    print(filename, ':', sum(len(c) for c in chosen.values()), 'Fleet columns,', len(relationships) + 1, 'FKs,', len(externals), 'standard reference tables')
    return chosen

core_columns = {
    'fleet_vehicle': {'id', 'vehicle_code', 'license_plate', 'model_id', 'is_electric_motorbike',
                     'operational_status', 'technical_ready', 'rental_blocked', 'block_reason', 'next_service_date',
                     'active', 'acquisition_date'},
    'fleet_vehicle_log_services': {'id', 'vehicle_id', 'maintenance_type', 'date',
                     'scheduled_start', 'scheduled_end', 'actual_start', 'actual_end', 'state', 'description',
                     'notes', 'result', 'amount', 'blocks_rental',
                     'next_service_date', 'active'},
}
for table, names in core_columns.items():
    assert names <= {c[0] for c in tables[table]}
generate('Fleet_Week6.dbml', core_columns)
physical = generate('Fleet_Week6_Physical.dbml')
assert physical == tables
print('Verified: selected/physical columns, nullability, FK endpoints/delete rules and index names match the Week 6 SQL snapshot.')
