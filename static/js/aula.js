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
