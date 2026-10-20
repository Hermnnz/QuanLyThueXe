"""Initialize stored current ODO from the standard history without deleting logs."""


def migrate(cr, version):
    cr.execute('''
        UPDATE fleet_vehicle v
           SET odometer = COALESCE((SELECT MAX(o.value)
                                      FROM fleet_vehicle_odometer o
                                     WHERE o.vehicle_id = v.id), 0)
         WHERE v.odometer IS NULL OR v.odometer = 0
    ''')
