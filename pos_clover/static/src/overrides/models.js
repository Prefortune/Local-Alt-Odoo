/** @odoo-module */

import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { PaymentClover } from "@pos_clover/app/payment_clover";

register_payment_method("clover", PaymentClover);