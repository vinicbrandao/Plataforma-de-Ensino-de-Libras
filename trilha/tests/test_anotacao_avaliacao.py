from decimal import Decimal

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse

from contas.tests.fabricas import CPF_VALIDO_2, criar_admin, criar_aluno
from dicionario.tests.fabricas import MidiaTemporariaMixin
from trilha.exceptions import AcaoSomenteDoAluno, AulaNaoEncontrada, AulaNaoIniciada, AulaRestritaAVisitante
from trilha.models import AnotacaoAula, Aula, AvaliacaoAula, AvaliacoesDaAula
from trilha.services import AnotacaoService, AvaliacaoService, ProgressoService

from .fabricas import criar_aula, criar_modulo


class ParticipacaoMixin(MidiaTemporariaMixin):
    @classmethod
    def setUpTestData(cls):
        modulo = criar_modulo(1)
        cls.aula = criar_aula(modulo, 1)
        cls.segunda = criar_aula(modulo, 2)
        cls.aluno = criar_aluno()
        cls.outro = criar_aluno(email="joao@exemplo.com", cpf=CPF_VALIDO_2, nome_completo="João Souza")
        cls.admin = criar_admin()


class AnotacaoServiceTests(ParticipacaoMixin, TestCase):
    def test_salvar_cria_e_depois_atualiza_a_mesma_anotacao(self):
        primeira = AnotacaoService.salvar(self.aluno, self.aula.pk, "Primeira versão")
        segunda = AnotacaoService.salvar(self.aluno, self.aula.pk, "Segunda versão")

        self.assertEqual(primeira.pk, segunda.pk)
        self.assertEqual(AnotacaoAula.objects.get().texto, "Segunda versão")
        self.assertGreaterEqual(segunda.atualizada_em, primeira.atualizada_em)

    def test_recusa_aula_nao_publicada_restrita_e_administrador(self):
        Aula.objects.filter(pk=self.segunda.pk).update(publicada=False)
        casos = (
            (self.aluno, self.segunda.pk, AulaNaoEncontrada),
            (AnonymousUser(), self.segunda.pk, AulaNaoEncontrada),
            (self.admin, self.aula.pk, AcaoSomenteDoAluno),
        )
        for usuario, aula_id, excecao in casos:
            with self.subTest(excecao=excecao.__name__), self.assertRaises(excecao):
                AnotacaoService.salvar(usuario, aula_id, "Texto")

    def test_visitante_fora_da_primeira_aula_e_recusado(self):
        with self.assertRaises(AulaRestritaAVisitante):
            AnotacaoService.excluir(AnonymousUser(), self.segunda.pk)

    def test_excluir_apaga_de_forma_definitiva(self):
        AnotacaoService.salvar(self.aluno, self.aula.pk, "Texto")

        self.assertTrue(AnotacaoService.excluir(self.aluno, self.aula.pk))
        self.assertFalse(AnotacaoService.excluir(self.aluno, self.aula.pk))

    def test_anotacao_de_aula_despublicada_fica_gravada_e_volta(self):
        AnotacaoService.salvar(self.aluno, self.aula.pk, "Guardada")
        Aula.objects.filter(pk=self.aula.pk).update(publicada=False)
        self.assertEqual(AnotacaoAula.objects.count(), 1)

        Aula.objects.filter(pk=self.aula.pk).update(publicada=True)
        self.client.force_login(self.aluno)
        self.assertContains(self.client.get(reverse("trilha:aula", args=[self.aula.pk])), "Guardada")


class AnotacaoViewTests(ParticipacaoMixin, TestCase):
    def url(self, nome="trilha:salvar_anotacao", aula=None):
        return reverse(nome, args=[(aula or self.aula).pk])

    def test_salvar_mostra_a_mensagem_e_volta_para_a_aula(self):
        self.client.force_login(self.aluno)

        resposta = self.client.post(self.url(), {"texto": "Mão aberta no peito"}, follow=True)

        self.assertContains(resposta, "Anotação salva")
        self.assertContains(resposta, "Mão aberta no peito")
        self.assertEqual(resposta.redirect_chain[0][0], f"{reverse('trilha:aula', args=[self.aula.pk])}#anotacoes")

    def test_texto_acima_do_limite_mostra_erro_e_mantem_o_texto(self):
        self.client.force_login(self.aluno)
        texto = "a" * 2001

        resposta = self.client.post(self.url(), {"texto": texto})

        self.assertContains(resposta, "A anotação deve ter até 2.000 caracteres")
        self.assertContains(resposta, texto)
        self.assertFalse(AnotacaoAula.objects.exists())

    def test_texto_so_com_espacos_e_recusado(self):
        self.client.force_login(self.aluno)

        resposta = self.client.post(self.url(), {"texto": "   "})

        self.assertContains(resposta, "Campo obrigatório não preenchido")

    def test_excluir_mostra_a_mensagem(self):
        AnotacaoService.salvar(self.aluno, self.aula.pk, "Texto")
        self.client.force_login(self.aluno)

        resposta = self.client.post(self.url("trilha:excluir_anotacao"), follow=True)

        self.assertContains(resposta, "Anotação excluída")
        self.assertFalse(AnotacaoAula.objects.exists())

    def test_um_aluno_nao_ve_nem_altera_a_anotacao_de_outro(self):
        AnotacaoService.salvar(self.outro, self.aula.pk, "Segredo do João")
        self.client.force_login(self.aluno)

        self.assertNotContains(self.client.get(reverse("trilha:aula", args=[self.aula.pk])), "Segredo do João")
        self.client.post(self.url("trilha:excluir_anotacao"))
        self.assertTrue(AnotacaoAula.objects.filter(aluno=self.outro).exists())

    def test_visitante_ve_o_aviso_e_administrador_nao_ve_a_area(self):
        aula_url = reverse("trilha:aula", args=[self.aula.pk])

        self.assertContains(self.client.get(aula_url), "Faça login para salvar anotações")

        self.client.force_login(self.admin)
        resposta = self.client.get(aula_url)
        self.assertNotContains(resposta, "Minhas anotações")
        self.assertEqual(self.client.post(self.url(), {"texto": "x"}).status_code, 403)

    def test_visitante_que_posta_vai_ao_login(self):
        resposta = self.client.post(self.url(), {"texto": "x"})

        self.assertRedirects(resposta, f"{reverse('contas:entrar')}?next={self.url()}", fetch_redirect_response=False)

    def test_texto_com_script_aparece_escapado(self):
        AnotacaoService.salvar(self.aluno, self.aula.pk, "<script>alert(1)</script>")
        self.client.force_login(self.aluno)

        resposta = self.client.get(reverse("trilha:aula", args=[self.aula.pk]))

        self.assertNotContains(resposta, "<script>alert(1)</script>")
        self.assertContains(resposta, "&lt;script&gt;alert(1)&lt;/script&gt;")


class AvaliacaoServiceTests(ParticipacaoMixin, TestCase):
    def setUp(self):
        ProgressoService.registrar_acesso(self.aluno, self.aula)

    def test_avaliar_cria_e_depois_substitui(self):
        _, criada = AvaliacaoService.avaliar(self.aluno, self.aula.pk, 3, "  Boa  ")
        avaliacao, criada_de_novo = AvaliacaoService.avaliar(self.aluno, self.aula.pk, 5)

        self.assertTrue(criada)
        self.assertFalse(criada_de_novo)
        self.assertEqual((avaliacao.nota, AvaliacaoAula.objects.count()), (5, 1))

    def test_comentario_sem_espacos_nas_pontas(self):
        avaliacao, _ = AvaliacaoService.avaliar(self.aluno, self.aula.pk, 4, "  Muito clara  ")

        self.assertEqual(avaliacao.comentario, "Muito clara")

    def test_recusa_administrador_e_aula_nunca_aberta(self):
        with self.assertRaises(AcaoSomenteDoAluno):
            AvaliacaoService.avaliar(self.admin, self.aula.pk, 4)
        with self.assertRaises(AulaNaoIniciada):
            AvaliacaoService.avaliar(self.aluno, self.segunda.pk, 4)

    def test_resumo_com_media_de_uma_casa_quantidade_e_comentarios_sem_dados_do_aluno(self):
        ProgressoService.registrar_acesso(self.outro, self.aula)
        AvaliacaoService.avaliar(self.aluno, self.aula.pk, 4, "Clara")
        AvaliacaoService.avaliar(self.outro, self.aula.pk, 5)

        resumo = AvaliacaoService.resumo(self.aula)

        self.assertEqual(resumo.media, Decimal("4.5"))
        self.assertEqual(resumo.quantidade, 2)
        self.assertEqual([(nota, texto) for _, nota, texto in resumo.comentarios], [(4, "Clara")])

    def test_resumo_arredonda_para_uma_casa(self):
        ProgressoService.registrar_acesso(self.outro, self.aula)
        terceiro = criar_aluno(email="ana@exemplo.com", cpf="390.533.447-05", nome_completo="Ana Lima")
        ProgressoService.registrar_acesso(terceiro, self.aula)
        for aluno, nota in ((self.aluno, 4), (self.outro, 4), (terceiro, 5)):
            AvaliacaoService.avaliar(aluno, self.aula.pk, nota)

        self.assertEqual(AvaliacaoService.resumo(self.aula).media, Decimal("4.3"))


class AvaliacaoViewTests(ParticipacaoMixin, TestCase):
    def setUp(self):
        self.url = reverse("trilha:avaliar", args=[self.aula.pk])
        self.client.force_login(self.aluno)
        self.client.get(reverse("trilha:aula", args=[self.aula.pk]))

    def test_primeira_avaliacao_e_atualizacao_mostram_as_mensagens(self):
        primeira = self.client.post(self.url, {"nota": "4"}, follow=True)
        segunda = self.client.post(self.url, {"nota": "5", "comentario": "Ótima"}, follow=True)

        self.assertContains(primeira, "Obrigado pela sua avaliação!")
        self.assertContains(segunda, "Avaliação atualizada")
        self.assertContains(segunda, "Atualizar avaliação")

    def test_sem_nota_mostra_a_mensagem_e_mantem_o_comentario(self):
        resposta = self.client.post(self.url, {"comentario": "Faltou exemplo"})

        self.assertContains(resposta, "Selecione uma nota de 1 a 5")
        self.assertContains(resposta, "Faltou exemplo")
        self.assertFalse(AvaliacaoAula.objects.exists())

    def test_estrelas_tem_texto_equivalente(self):
        resposta = self.client.get(reverse("trilha:aula", args=[self.aula.pk]))

        for nota in range(1, 6):
            self.assertContains(resposta, f"{nota} de 5")

    def test_visitante_e_administrador_nao_veem_a_area(self):
        self.client.logout()
        self.assertNotContains(self.client.get(reverse("trilha:aula", args=[self.aula.pk])), "Avalie esta aula")

        self.client.force_login(self.admin)
        self.assertNotContains(self.client.get(reverse("trilha:aula", args=[self.aula.pk])), "Avalie esta aula")


class AvaliacoesAdminTests(ParticipacaoMixin, TestCase):
    def setUp(self):
        self.client.force_login(self.admin)

    def test_lista_media_e_quantidade(self):
        ProgressoService.registrar_acesso(self.aluno, self.aula)
        AvaliacaoService.avaliar(self.aluno, self.aula.pk, 4, "<b>clara</b>")

        lista = self.client.get(reverse("admin:trilha_avaliacoesdaaula_changelist"))
        detalhe = self.client.get(reverse("admin:trilha_avaliacoesdaaula_change", args=[self.aula.pk]))

        self.assertContains(lista, "4,0")
        self.assertContains(detalhe, "&lt;b&gt;clara&lt;/b&gt;")
        self.assertNotContains(detalhe, self.aluno.email)
        self.assertNotContains(detalhe, self.aluno.nome_completo)

    def test_aula_sem_avaliacoes_mostra_a_mensagem_e_nao_permite_editar(self):
        detalhe = self.client.get(reverse("admin:trilha_avaliacoesdaaula_change", args=[self.segunda.pk]))

        self.assertContains(detalhe, "Esta aula ainda não possui avaliações")
        self.assertNotContains(detalhe, 'name="_save"')
        self.assertEqual(self.client.get(reverse("admin:trilha_avaliacoesdaaula_add")).status_code, 403)
        self.assertTrue(AvaliacoesDaAula._meta.proxy)


class SugestaoAoConcluirTests(ParticipacaoMixin, TestCase):
    def test_resultado_aprovado_mostra_o_link_para_avaliar(self):
        from questionarios.tests.fabricas import criar_questao, respostas

        questao = criar_questao(self.aula, 1)
        self.client.force_login(self.aluno)
        dados = {f"questao_{questao.pk}": respostas([questao], 1)[questao.pk]}

        resposta = self.client.post(reverse("questionarios:responder", args=[self.aula.pk]), dados)

        self.assertContains(resposta, "Avalie esta aula")
        self.assertContains(resposta, f"{reverse('trilha:aula', args=[self.aula.pk])}#avaliacao")
