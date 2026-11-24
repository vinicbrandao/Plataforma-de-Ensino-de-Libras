// Mostra a mensagem de falha e o botão de nova tentativa quando o vídeo não carrega (RF007).
(function () {
  const video = document.getElementById("video-aula");
  const erro = document.getElementById("erro-video");
  const tentar = document.getElementById("tentar-video");
  if (!video || !erro || !tentar) return;
  const fonte = video.querySelector("source");

  function mostrarErro() { erro.hidden = false; }

  video.addEventListener("error", mostrarErro);
  if (fonte) fonte.addEventListener("error", mostrarErro);
  tentar.addEventListener("click", function () {
    erro.hidden = true;
    video.load();
  });
})();

// Contador de caracteres restantes da anotação (RF019).
(function () {
  const campo = document.getElementById("id_texto");
  const contador = document.getElementById("contador-anotacao");
  if (!campo || !contador) return;
  const limite = Number(campo.getAttribute("maxlength")) || 2000;

  function atualizar() {
    const restantes = limite - campo.value.length;
    contador.textContent = restantes === 1 ? "1 caractere restante" : restantes + " caracteres restantes";
  }

  contador.hidden = false;
  campo.addEventListener("input", atualizar);
  atualizar();
})();

// Confirmação antes de excluir a anotação (RF019).
(function () {
  document.querySelectorAll("form[data-confirmacao]").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      if (!window.confirm(form.dataset.confirmacao)) evento.preventDefault();
    });
  });
})();
