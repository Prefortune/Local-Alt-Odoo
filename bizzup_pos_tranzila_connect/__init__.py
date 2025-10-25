#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
from . import models


def post_init(env):
    """Company write"""
    # env = api.Environment(cr, SUPERUSER_ID, {})

    # Search for the payment provider with code 'tranzila'
    provider = env["payment.provider"].search([("code", "=", "tranzila")])

    # Search for the POS payment method with name 'Tranzila POS Machine'
    pos_payment_method = env["pos.payment.method"].search(
        [("name", "=", "Tranzila POS Machine")]
    )

    pos_payment_method.write({"payment_limit": provider.payment_limit})

    # Check if both provider and POS payment method records are found
    if provider and pos_payment_method:
        # Iterate through the existing tranzila_terminal_ids in provider
        for rec in provider.tranzila_terminal_ids:
            # Use the write method to add new records
            pos_payment_method.write(
                {
                    "tranzila_terminal_ids": [
                        (
                            0,
                            0,
                            {
                                "pos_id": rec.pos_id,
                                "url": rec.url,
                                "provider_id": rec.provider_id.id,
                            },
                        )
                    ]
                }
            )
