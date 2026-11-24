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

// Mostra os dados do responsável somente para menores de 18 anos (RF002). Ao esconder,
// apaga o que foi digitado. Sem JavaScript, o grupo fica visível e o servidor decide pela idade.
(function () {
  const grupo = document.getElementById("dados-responsavel");
  const nascimento = document.getElementById("id_data_nascimento");
  if (!grupo || !nascimento) return;

  function idade(texto) {
    const partes = texto.split("-").map(Number);
    if (partes.length !== 3 || partes.some(isNaN)) return null;
    const hoje = new Date();
    let anos = hoje.getFullYear() - partes[0];
    const mes = hoje.getMonth() + 1;
    if (mes < partes[1] || (mes === partes[1] && hoje.getDate() < partes[2])) anos -= 1;
    return anos;
  }

  function atualizar() {
    const anos = idade(nascimento.value);
    const menor = anos !== null && anos < 18;
    grupo.hidden = !menor;
    if (menor) return;
    grupo.querySelectorAll("input").forEach(function (entrada) {
      if (entrada.type === "checkbox" || entrada.type === "radio") entrada.checked = false;
      else entrada.value = "";
    });
  }

  nascimento.addEventListener("change", atualizar);
  nascimento.addEventListener("input", atualizar);
  atualizar();
})();
