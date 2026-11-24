from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.urls import reverse

from contas.tests.fabricas import CPF_VALIDO_2, criar_admin, criar_aluno
from dicionario.tests.fabricas import MidiaTemporariaMixin
from questionarios.exceptions import PeriodoInvalido
from questionarios.models import Tentativa
from questionarios.services import FiltrosHistorico, HistoricoService
from trilha.models import Aula
from trilha.tests.fabricas import criar_aula, criar_modulo

FUSO = ZoneInfo("America/Sao_Paulo")
URL = reverse("questionarios:historico")


def quando(dia: int, hora: int = 10, minuto: int = 0) -> datetime:
    return datetime(2026, 11, dia, hora, minuto, tzinfo=FUSO)


def registrar(aluno, aula, momento: datetime, acertos: int = 3, total: int = 3) -> Tentativa:
    aprovada = acertos * 10 >= total * 7
    return Tentativa.objects.create(
        aluno=aluno,
        aula=aula,
        acertos=acertos,
        total=total,
        percentual=round(100 * acertos / total),
        aprovada=aprovada,
        realizada_em=momento,
    )


class HistoricoMixin(MidiaTemporariaMixin):
    @classmethod
    def setUpTestData(cls):
        cls.modulo = criar_modulo(1, "Alfabeto")
        cls.outro_modulo = criar_modulo(2, "Saudações")
        cls.aula = criar_aula(cls.modulo, 1, titulo="Letras A a E")
        cls.segunda = criar_aula(cls.modulo, 2, titulo="Letras F a J")
        cls.aula_saudacoes = criar_aula(cls.outro_modulo, 1, titulo="Bom dia")
        cls.aluno = criar_aluno()
        cls.outro = criar_aluno(email="joao@exemplo.com", cpf=CPF_VALIDO_2, nome_completo="João Souza")


class ConsultarTests(HistoricoMixin, TestCase):
    def test_mostra_so_as_tentativas_do_aluno_da_mais_recente_para_a_mais_antiga(self):
        antiga = registrar(self.aluno, self.aula, quando(10))
        recente = registrar(self.aluno, self.segunda, quando(12))
        registrar(self.outro, self.aula, quando(11))

        pagina = HistoricoService.consultar(self.aluno).pagina

        self.assertEqual(list(pagina), [recente, antiga])

    def test_pagina_com_20_tentativas(self):
        for minuto in range(25):
            registrar(self.aluno, self.aula, quando(10, minuto=minuto))

        primeira = HistoricoService.consultar(self.aluno).pagina
        segunda = HistoricoService.consultar(self.aluno, pagina=2).pagina

        self.assertEqual(len(primeira), 20)
        self.assertEqual(len(segunda), 5)
        self.assertEqual(primeira[0].realizada_em, quando(10, minuto=24))

    def test_filtra_por_modulo(self):
        registrar(self.aluno, self.aula, quando(10))
        saudacao = registrar(self.aluno, self.aula_saudacoes, quando(11))

        pagina = HistoricoService.consultar(
            self.aluno, FiltrosHistorico(modulo_id=self.outro_modulo.pk)
        ).pagina

        self.assertEqual(list(pagina), [saudacao])

    def test_filtra_por_aula(self):
        da_aula = registrar(self.aluno, self.aula, quando(10))
        registrar(self.aluno, self.segunda, quando(11))

        pagina = HistoricoService.consultar(self.aluno, FiltrosHistorico(aula_id=self.aula.pk)).pagina

        self.assertEqual(list(pagina), [da_aula])

    def test_filtra_por_resultado(self):
        aprovada = registrar(self.aluno, self.aula, quando(10), acertos=3)
        reprovada = registrar(self.aluno, self.aula, quando(11), acertos=1)

        aprovadas = HistoricoService.consultar(self.aluno, FiltrosHistorico(aprovada=True)).pagina
        reprovadas = HistoricoService.consultar(self.aluno, FiltrosHistorico(aprovada=False)).pagina

        self.assertEqual(list(aprovadas), [aprovada])
        self.assertEqual(list(reprovadas), [reprovada])

    def test_periodo_inclui_os_dois_dias_no_fuso_local(self):
        registrar(self.aluno, self.aula, quando(19, 23, 59))
        # 23h30 em Brasília já é dia 21 em UTC, mas conta como dia 20.
        primeira = registrar(self.aluno, self.aula, quando(20, 0, 0))
        ultima = registrar(self.aluno, self.aula, quando(21, 23, 30))
        registrar(self.aluno, self.aula, quando(22, 0, 0))

        pagina = HistoricoService.consultar(
            self.aluno, FiltrosHistorico(data_inicial=date(2026, 11, 20), data_final=date(2026, 11, 21))
        ).pagina

        self.assertEqual(list(pagina), [ultima, primeira])

    def test_filtros_combinados(self):
        alvo = registrar(self.aluno, self.aula, quando(10), acertos=1)
        registrar(self.aluno, self.aula, quando(11), acertos=3)
        registrar(self.aluno, self.segunda, quando(10), acertos=1)

        pagina = HistoricoService.consultar(
            self.aluno,
            FiltrosHistorico(modulo_id=self.modulo.pk, aula_id=self.aula.pk, aprovada=False),
        ).pagina

        self.assertEqual(list(pagina), [alvo])

    def test_recusa_data_final_anterior_a_inicial(self):
        with self.assertRaises(PeriodoInvalido):
            HistoricoService.consultar(
                self.aluno,
                FiltrosHistorico(data_inicial=date(2026, 11, 21), data_final=date(2026, 11, 20)),
            )

    def test_aceita_periodo_de_um_dia(self):
        tentativa = registrar(self.aluno, self.aula, quando(20))

        pagina = HistoricoService.consultar(
            self.aluno, FiltrosHistorico(data_inicial=date(2026, 11, 20), data_final=date(2026, 11, 20))
        ).pagina

        self.assertEqual(list(pagina), [tentativa])


class ResumoTests(HistoricoMixin, TestCase):
    def test_total_e_primeira_aprovacao_por_aula_sem_os_filtros(self):
        registrar(self.aluno, self.aula, quando(10), acertos=1)
        registrar(self.aluno, self.aula, quando(11), acertos=3)
        registrar(self.aluno, self.aula, quando(12), acertos=3)
        registrar(self.aluno, self.segunda, quando(13), acertos=1)
        registrar(self.outro, self.aula, quando(9), acertos=3)

        historico = HistoricoService.consultar(self.aluno, FiltrosHistorico(aprovada=False))
        resumo = {linha.aula: linha for linha in historico.resumo}

        self.assertEqual([linha.aula for linha in historico.resumo], ["Letras A a E", "Letras F a J"])
        self.assertEqual(resumo["Letras A a E"].tentativas, 3)
        self.assertEqual(resumo["Letras A a E"].primeira_aprovacao, quando(11))
        self.assertEqual(resumo["Letras F a J"].tentativas, 1)
        self.assertIsNone(resumo["Letras F a J"].primeira_aprovacao)

    def test_historico_vazio_sem_tentativas(self):
        registrar(self.outro, self.aula, quando(10))

        self.assertTrue(HistoricoService.consultar(self.aluno).vazio)


class AulaDespublicadaTests(HistoricoMixin, TestCase):
    def test_tentativa_de_aula_despublicada_continua_no_historico_e_nas_opcoes(self):
        tentativa = registrar(self.aluno, self.aula, quando(10))
        Aula.objects.filter(pk=self.aula.pk).update(publicada=False)

        historico = HistoricoService.consultar(self.aluno)
        opcoes = HistoricoService.opcoes(self.aluno)

        self.assertEqual(list(historico.pagina), [tentativa])
        self.assertEqual(opcoes.aulas, [("Alfabeto", [(self.aula.pk, "Letras A a E")])])


class OpcoesTests(HistoricoMixin, TestCase):
    def test_oferece_so_modulos_e_aulas_respondidos_pelo_aluno_em_ordem(self):
        registrar(self.aluno, self.aula_saudacoes, quando(10))
        registrar(self.aluno, self.segunda, quando(11))
        registrar(self.aluno, self.segunda, quando(12))
        registrar(self.outro, self.aula, quando(10))

        opcoes = HistoricoService.opcoes(self.aluno)

        self.assertEqual(
            opcoes.modulos, [(self.modulo.pk, "Alfabeto"), (self.outro_modulo.pk, "Saudações")]
        )
        self.assertEqual(
            opcoes.aulas,
            [
                ("Alfabeto", [(self.segunda.pk, "Letras F a J")]),
                ("Saudações", [(self.aula_saudacoes.pk, "Bom dia")]),
            ],
        )


class HistoricoViewTests(HistoricoMixin, TestCase):
    def test_visitante_vai_ao_login(self):
        resposta = self.client.get(URL)

        self.assertRedirects(resposta, f"{reverse('contas:entrar')}?next={URL}")

    def test_sem_tentativas_mostra_a_mensagem(self):
        self.client.force_login(self.aluno)

        resposta = self.client.get(URL)

        self.assertContains(resposta, "Nenhuma tentativa registrada até o momento")
        self.assertNotContains(resposta, "Resumo por aula")

    def test_lista_tentativas_e_resumo(self):
        registrar(self.aluno, self.aula, quando(20, 14, 5), acertos=1)
        registrar(self.aluno, self.aula, quando(21, 9, 30), acertos=3)
        self.client.force_login(self.aluno)

        resposta = self.client.get(URL)

        self.assertContains(resposta, "21/11/2026 09:30")
        self.assertContains(resposta, "1 de 3 (33%)")
        self.assertContains(resposta, "Reprovado")
        self.assertContains(resposta, "Aprovado")
        self.assertContains(resposta, "Resumo por aula")

    def test_nao_mostra_tentativas_de_outro_aluno(self):
        registrar(self.aluno, self.aula, quando(10))
        registrar(self.outro, self.aula_saudacoes, quando(11))
        self.client.force_login(self.aluno)

        resposta = self.client.get(URL)

        self.assertNotContains(resposta, "Bom dia")

    def test_aula_de_outro_aluno_e_recusada_como_escolha_invalida(self):
        registrar(self.aluno, self.aula, quando(10))
        registrar(self.outro, self.aula_saudacoes, quando(11))
        self.client.force_login(self.aluno)

        resposta = self.client.get(URL, {"aula": self.aula_saudacoes.pk})

        self.assertIsNone(resposta.context["historico"])
        self.assertTrue(resposta.context["form"].errors["aula"])
        self.assertNotContains(resposta, "Bom dia")

    def test_data_final_anterior_mostra_erro_no_campo_e_mantem_os_filtros(self):
        registrar(self.aluno, self.aula, quando(10))
        self.client.force_login(self.aluno)

        resposta = self.client.get(URL, {"data_inicial": "2026-11-21", "data_final": "2026-11-20"})

        self.assertContains(resposta, "A data final não pode ser anterior à data inicial")
        self.assertContains(resposta, 'id="id_data_final_error"')
        self.assertContains(resposta, 'value="2026-11-21"')
        self.assertContains(resposta, "Resumo por aula")

    def test_filtro_sem_resultado_mostra_a_mensagem(self):
        registrar(self.aluno, self.aula, quando(10), acertos=3)
        self.client.force_login(self.aluno)

        resposta = self.client.get(URL, {"resultado": "reprovado"})

        self.assertContains(resposta, "Nenhum registro encontrado para os filtros informados")

    def test_paginacao_mantem_os_filtros(self):
        for minuto in range(21):
            registrar(self.aluno, self.aula, quando(10, minuto=minuto), acertos=1)
        self.client.force_login(self.aluno)

        resposta = self.client.get(URL, {"resultado": "reprovado"})

        self.assertContains(resposta, "?resultado=reprovado&amp;pagina=2")

    def test_numero_fixo_de_consultas(self):
        for minuto in range(5):
            registrar(self.aluno, self.aula, quando(10, minuto=minuto))
            registrar(self.aluno, self.aula_saudacoes, quando(11, minuto=minuto))
        self.client.force_login(self.aluno)
        self.client.get(URL)  # aquece sessão e usuário

        # Sessão e usuário (2), opções, contagem, página e resumo (4) e a sessão
        # gravada a cada requisição, com savepoint (3). Não cresce com as tentativas.
        with self.assertNumQueries(9):
            self.client.get(URL)

    def test_menu_mostra_historico_so_ao_aluno(self):
        self.client.force_login(self.aluno)
        self.assertContains(self.client.get(reverse("inicio")), f'href="{URL}"')

        self.client.force_login(criar_admin())
        self.assertNotContains(self.client.get(reverse("inicio")), f'href="{URL}"')

        self.client.logout()
        self.assertNotContains(self.client.get(reverse("inicio")), f'href="{URL}"')
