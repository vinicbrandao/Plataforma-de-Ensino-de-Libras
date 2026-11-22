from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.test import TestCase
from django.urls import reverse

from contas.models import RegistroAuditoria, Usuario

from .fabricas import CPF_VALIDO_2, SENHA, criar_admin, criar_aluno


class UsuarioAdminTests(TestCase):
    lista = reverse("admin:contas_usuario_changelist")

    @classmethod
    def setUpTestData(cls):
        cls.admin = criar_admin()
        cls.aluno = criar_aluno(deficiencia=Usuario.Deficiencia.OUTRA, qual_deficiencia="Dislexia")
        cls.outro = criar_aluno(
            nome_completo="João Souza", email="joao@exemplo.com", cpf=CPF_VALIDO_2
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_lista_so_alunos_com_cpf_parcial(self):
        resposta = self.client.get(self.lista)

        self.assertContains(resposta, "Maria da Silva")
        self.assertContains(resposta, "***.982.247-**")
        self.assertNotContains(resposta, "529.982.247-25")
        self.assertNotContains(resposta, '<td class="field-email">admin@exemplo.com</td>')

    def test_detalhe_nao_mostra_deficiencia_nem_botoes_de_salvar(self):
        resposta = self.client.get(reverse("admin:contas_usuario_change", args=[self.aluno.pk]))

        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, "Dislexia")
        self.assertNotContains(resposta, "deficiência")
        self.assertNotContains(resposta, 'name="_save"')

    def test_nao_permite_incluir_nem_excluir(self):
        self.assertEqual(self.client.get(reverse("admin:contas_usuario_add")).status_code, 403)
        url_excluir = reverse("admin:contas_usuario_delete", args=[self.aluno.pk])
        self.assertEqual(self.client.get(url_excluir).status_code, 403)

    def test_pesquisa_por_cpf_completo_com_e_sem_pontuacao(self):
        for termo in ("529.982.247-25", "52998224725"):
            with self.subTest(termo=termo):
                resposta = self.client.get(self.lista, {"q": termo})
                self.assertContains(resposta, "Maria da Silva")
                self.assertNotContains(resposta, "João Souza")

    def test_pesquisa_por_parte_do_nome(self):
        resposta = self.client.get(self.lista, {"q": "souza"})

        self.assertContains(resposta, "João Souza")
        self.assertNotContains(resposta, "Maria da Silva")

    def test_abrir_detalhe_registra_consulta(self):
        self.client.get(reverse("admin:contas_usuario_change", args=[self.aluno.pk]))

        registro = RegistroAuditoria.objects.get(acao=RegistroAuditoria.Acao.CONSULTA_ALUNO)
        self.assertEqual((registro.autor, registro.alvo), (self.admin, self.aluno))

    def _acao(self, acao: str, **extra):
        dados = {"action": acao, ACTION_CHECKBOX_NAME: [self.aluno.pk], **extra}
        return self.client.post(self.lista, dados, follow=True)

    def test_desativacao_pede_confirmacao_antes(self):
        resposta = self._acao("desativar_selecionados")

        self.assertContains(resposta, "Deseja realmente desativar este usuário?")
        self.aluno.refresh_from_db()
        self.assertTrue(self.aluno.is_active)

    def test_desativacao_confirmada_desativa_registra_e_encerra_a_sessao(self):
        cliente_aluno = self.client_class()
        cliente_aluno.force_login(self.aluno)

        resposta = self._acao("desativar_selecionados", confirmacao="sim")

        self.assertContains(resposta, "Usuário desativado com sucesso")
        self.aluno.refresh_from_db()
        self.assertFalse(self.aluno.is_active)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                acao=RegistroAuditoria.Acao.DESATIVACAO, alvo=self.aluno
            ).exists()
        )
        self.assertFalse(cliente_aluno.get(reverse("inicio")).wsgi_request.user.is_authenticated)

    def test_reativacao_registra(self):
        self.aluno.is_active = False
        self.aluno.save()

        resposta = self._acao("reativar_selecionados")

        self.assertContains(resposta, "Usuário reativado com sucesso")
        self.aluno.refresh_from_db()
        self.assertTrue(self.aluno.is_active)
        self.assertTrue(
            RegistroAuditoria.objects.filter(acao=RegistroAuditoria.Acao.REATIVACAO).exists()
        )

    def test_aluno_nao_acessa_o_admin(self):
        self.client.force_login(self.aluno)

        resposta = self.client.get(self.lista)

        self.assertEqual(resposta.status_code, 302)


class RegistroLoginAdminTests(TestCase):
    def test_login_e_logout_de_administrador_sao_registrados(self):
        admin = criar_admin()

        self.client.post(reverse("contas:entrar"), {"login": admin.email, "senha": SENHA})
        self.client.post(reverse("contas:sair"))

        acoes = list(
            RegistroAuditoria.objects.filter(autor=admin).values_list("acao", flat=True)
        )
        self.assertCountEqual(
            acoes, [RegistroAuditoria.Acao.LOGIN_ADMIN, RegistroAuditoria.Acao.LOGOUT_ADMIN]
        )

    def test_login_de_aluno_nao_e_registrado(self):
        aluno = criar_aluno()

        self.client.post(reverse("contas:entrar"), {"login": aluno.email, "senha": SENHA})

        self.assertFalse(RegistroAuditoria.objects.exists())
