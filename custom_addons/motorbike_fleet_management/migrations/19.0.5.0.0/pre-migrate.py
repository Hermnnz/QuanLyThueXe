"""Rename vehicle state keys without rewriting any other vehicle or service data."""


def migrate(cr, version):
    cr.execute("""
        UPDATE fleet_vehicle
           SET operational_status = CASE operational_status
               WHEN 'rented' THEN 'renting'
               WHEN 'inspection' THEN 'pending_inspection'
           END
         WHERE operational_status IN ('rented', 'inspection')
    """)
