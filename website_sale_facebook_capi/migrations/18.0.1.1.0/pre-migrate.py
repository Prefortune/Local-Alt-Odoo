def migrate(cr, version):

    cr.execute("UPDATE website_tracking_service SET api_is_active = TRUE where fb_capi_is_active = TRUE;")
    cr.execute("ALTER TABLE website_tracking_service DROP COLUMN fb_capi_is_active;")

    # Select Facebook API services
    cr.execute("SELECT id, fb_capi_access_token FROM website_tracking_service "
               "WHERE type='fbp' AND fb_capi_access_token IS NOT NULL;")
    service_ids = cr.fetchall()

    # Save token from the old field to the new one
    for rec in service_ids:
        cr.execute(
            "UPDATE website_tracking_service SET api_token = %(token)s where id = %(id)s;",
            {'id': rec[0], 'token': rec[1]},
        )
    cr.execute("ALTER TABLE website_tracking_service DROP COLUMN fb_capi_access_token;")

    cr.execute("UPDATE website_tracking_service SET api_deactivate_pixel=TRUE where fb_capi_deactivate_pixel=TRUE;")
    cr.execute("ALTER TABLE website_tracking_service DROP COLUMN fb_capi_deactivate_pixel;")

    # Select Facebook API services
    cr.execute("SELECT id, fb_capi_test_event_code FROM website_tracking_service "
               "WHERE type='fbp' AND fb_capi_test_event_code IS NOT NULL;")
    service_ids = cr.fetchall()

    # Save a test code from the old field to the new one
    for rec in service_ids:
        cr.execute(
            "UPDATE website_tracking_service SET api_test_code = %(code)s where id = %(id)s;",
            {'id': rec[0], 'code': rec[1]},
        )
    cr.execute("ALTER TABLE website_tracking_service DROP COLUMN fb_capi_test_event_code;")
