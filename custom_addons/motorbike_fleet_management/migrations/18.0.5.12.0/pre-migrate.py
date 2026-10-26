def migrate(cr, version):
    # Preserve old date columns and a readable trace before removing selection.
    cr.execute("""UPDATE fleet_vehicle_log_services SET
        notes = COALESCE(notes, '') || E'\n[Lịch dự kiến cũ: ' ||
                COALESCE(scheduled_start::text, 'chưa nhập') || ' → ' ||
                COALESCE(scheduled_end::text, 'chưa nhập') ||
                '; chuyển về Mới khi bỏ chức năng lên lịch]',
        state = 'new'
        WHERE state = 'scheduled'""")
