function naviguj(target) {
  window.location = jQuery(target).attr("href");
  return false;
  };

function zmen_barvu(elem, barva) {
  jQuery(elem).animate({"background-color": barva});
  };

$(document).ready(
  function () {
    jQuery(".initsel").hover(
      function () {jQuery(this).css('cursor', 'pointer'); zmen_barvu(this, "#ccccdd");},
      function () {zmen_barvu(this, "#e8e8e8");});

    jQuery("#initsel_login").click(function() {naviguj("#a_login")});
    jQuery("#initsel_mail").click(function() {naviguj("#a_mail")});
    jQuery("#initsel_register").click(function() {naviguj("#a_register")});
    });
