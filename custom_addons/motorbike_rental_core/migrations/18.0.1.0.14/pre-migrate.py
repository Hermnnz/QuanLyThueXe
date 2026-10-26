def migrate(cr, version):
    cr.execute(
        """
        UPDATE rental_booking_request
           SET state = CASE WHEN state = 'contacted' THEN 'new' ELSE state END,
               name = replace(name, '/', '-')
         WHERE state = 'contacted'
            OR name LIKE 'RR/%'
        """
    )
