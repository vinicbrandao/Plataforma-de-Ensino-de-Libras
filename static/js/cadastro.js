// Mostra "Qual deficiência" somente com "Sim, outra" (RF001). Sem JavaScript, o campo
// fica sempre visível e o servidor aplica a mesma regra.
(function () {
  const campo = document.getElementById("campo-qual_deficiencia");
  const opcoes = document.querySelectorAll('input[name="deficiencia"]');
  if (!campo || opcoes.length === 0) return;
  const entrada = campo.querySelector("input");

  function atualizar() {
    const marcada = document.querySelector('input[name="deficiencia"]:checked');
    const outra = marcada !== null && marcada.value === "OUTRA";
    campo.hidden = !outra;
    if (!outra && entrada) entrada.value = "";
  }

  opcoes.forEach(function (opcao) { opcao.addEventListener("change", atualizar); });
  atualizar();
})();
