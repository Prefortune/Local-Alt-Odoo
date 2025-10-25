//
// odoo.define('pos_custom_button.CustomButton', function (require) {
//     "use strict";
//
//     const PosComponent = require('point_of_sale.PosComponent');
//     const Registries = require('point_of_sale.Registries');
//
//     class CustomButton extends PosComponent {
//         async onClick() {
//             this.showPopup('ConfirmPopup', {
//                 title: 'Custom Button',
//                 body: 'This is a custom button action!',
//             });
//         }
//     }
//     CustomButton.template = 'CustomButton';
//     Registries.Component.add(CustomButton);
//     return CustomButton;
// });

// import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
// import { patch } from "@web/core/utils/patch";
//
// patch(PaymentScreen.prototype, {
//
//   patch(PaymentScreen.prototype, {
//     async onClick() {
//         this.showPopup('ConfirmPopup', {
//             title: 'Custom Button',
//             body: 'This is a custom button action!',
//         });
//     }
//   });
//
// });


import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
  async onClick() {
      this.showPopup('ConfirmPopup', {
          title: 'Custom Button',
          body: 'This is a custom button action!',
      });
  },
});
