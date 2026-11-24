// Confirmação do botão Cancelar do perfil, como no RF001 (RF005).
(function () {
  document.querySelectorAll("a[data-confirmacao]").forEach(function (link) {
    link.addEventListener("click", function (evento) {
      if (!window.confirm(link.dataset.confirmacao)) evento.preventDefault();
    });
  });
})();
