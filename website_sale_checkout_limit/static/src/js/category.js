/** @odoo-module **/
import wSaleUtils from "@website_sale/js/website_sale_utils";


wSaleUtils.updateCartNavBar = function updateCartNavBar(data) {
   sessionStorage.setItem('website_sale_cart_quantity', data.cart_quantity);
   $(".my_cart_quantity")
      .parents('li.o_wsale_my_cart').removeClass('d-none').end()
      .toggleClass('d-none', data.cart_quantity === 0)
      .addClass('o_mycart_zoom_animation').delay(300)
      .queue(function () {
         $(this)
            .toggleClass('fa fa-warning', !data.cart_quantity)
            .attr('title', data.warning)
            .text(data.cart_quantity || '')
            .removeClass('o_mycart_zoom_animation')
            .dequeue();
      });

   $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();
   $("#cart_total").replaceWith(data['website_sale.total']);
   if (data.cart_ready) {
      document.querySelector("a[name='website_sale_main_button']")?.classList.remove('disabled');
   } else {
      document.querySelector("a[name='website_sale_main_button']")?.classList.add('disabled');
   }


   //***** Custom Data*****
   var res = data['website_sale.check']
   if (res) {
      $('.checkout_one').removeClass("disabled")
      $('#message').addClass("d-none")
   }
   else {
      $('.checkout_one').addClass("disabled")
      $('#message').removeClass("d-none")
   }
   // *******
}






