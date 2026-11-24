from datetime import date
from unittest import mock

from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from contas.exceptions import CpfJaCadastrado, EmailJaCadastrado, ResponsavelObrigatorio
from contas.forms import CadastroForm
from contas.models import RegistroAuditoria, Usuario
from contas.services import CadastroService

from .fabricas import CPF_VALIDO_2, criar_aluno, dados_cadastro, dados_form_cadastro

HOJE = date(2026, 11, 22)


class CalcularIdadeTests(SimpleTestCase):
    def test_idade_completa_no_dia_do_aniversario(self):
        self.assertEqual(CadastroService.calcular_idade(date(2008, 11, 22), HOJE), 18)
        self.assertEqual(CadastroService.calcular_idade(date(2008, 11, 23), HOJE), 17)

    def test_nascido_em_29_de_fevereiro_completa_anos_em_1_de_marco(self):
        nascimento = date(2008, 2, 29)
        self.assertEqual(CadastroService.calcular_idade(nascimento, date(2026, 2, 28)), 17)
        self.assertEqual(CadastroService.calcular_idade(nascimento, date(2026, 3, 1)), 18)


@mock.patch("contas.services.cadastro.timezone.localdate", return_value=HOJE)
class CadastroServiceTests(TestCase):
    def test_cria_aluno_e_registra_aceite_dos_termos(self, _):
        usuario = CadastroService.cadastrar(dados_cadastro())

        self.assertFalse(usuario.is_staff)
        self.assertIsNotNone(usuario.termos_aceitos_em)
        self.assertTrue(usuario.check_password("SenhaTeste123"))

    def test_recusa_email_repetido_com_maiusculas_diferentes(self, _):
        criar_aluno()

        with self.assertRaises(EmailJaCadastrado):
            CadastroService.cadastrar(dados_cadastro(email="MARIA@exemplo.com", cpf=CPF_VALIDO_2))

    def test_recusa_cpf_repetido(self, _):
        criar_aluno()

        with self.assertRaises(CpfJaCadastrado):
            CadastroService.cadastrar(dados_cadastro(email="outra@exemplo.com"))

    def test_quem_tem_17_anos_precisa_do_responsavel(self, _):
        with self.assertRaises(ResponsavelObrigatorio):
            CadastroService.cadastrar(dados_cadastro(data_nascimento=date(2008, 11, 23)))

    def test_aceita_quem_completa_18_hoje(self, _):
        usuario = CadastroService.cadastrar(dados_cadastro(data_nascimento=date(2008, 11, 22)))

        self.assertEqual(usuario.data_nascimento, date(2008, 11, 22))


class ConstraintsTests(TestCase):
    def test_banco_recusa_aluno_sem_cpf(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.create(email="sem@exemplo.com", nome_completo="Sem CPF")

    def test_banco_recusa_email_com_maiusculas(self):
        aluno = criar_aluno()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.filter(pk=aluno.pk).update(email="Maria@Exemplo.com")

    def test_administrador_pode_ficar_sem_cpf(self):
        admin = Usuario.objects.create_superuser(
            email="Admin@Exemplo.com", password="x1", nome_completo="Admin"
        )

        self.assertIsNone(admin.cpf)
        self.assertEqual(admin.email, "admin@exemplo.com")

    def test_banco_recusa_deficiencia_fora_das_opcoes(self):
        aluno = criar_aluno()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.filter(pk=aluno.pk).update(deficiencia="MOTORA")

    def test_banco_recusa_contato_libras_fora_das_opcoes(self):
        aluno = criar_aluno()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.filter(pk=aluno.pk).update(contato_libras="FLUENTE")

    def test_administrador_pode_ficar_sem_deficiencia_e_contato(self):
        admin = Usuario.objects.create_superuser(
            email="admin@exemplo.com", password="x1", nome_completo="Admin"
        )

        self.assertEqual((admin.deficiencia, admin.contato_libras), ("", ""))

    def test_banco_recusa_acao_de_auditoria_fora_das_opcoes(self):
        admin = Usuario.objects.create_superuser(
            email="admin@exemplo.com", password="x1", nome_completo="Admin"
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            RegistroAuditoria.objects.create(autor=admin, acao="EXCLUSAO")


class CadastroFormTests(SimpleTestCase):
    def test_normaliza_os_dados_validos(self):
        form = CadastroForm(dados_form_cadastro())

        self.assertTrue(form.is_valid(), form.errors)
        dados = form.dados()
        self.assertEqual(dados.nome_completo, "Maria da Silva")
        self.assertEqual(dados.email, "maria@exemplo.com")
        self.assertEqual(dados.cpf, "529.982.247-25")
        self.assertEqual(dados.telefone, "(11) 91234-5678")

    def test_mostra_a_mensagem_de_cada_campo_invalido(self):
        casos = {
            "nome_completo": ("Ma", "Nome inválido"),
            "email": ("maria@exemplo", "E-mail inválido"),
            "cpf": ("529.982.247-26", "CPF inválido"),
            "telefone": ("1132345678", "Telefone inválido"),
            "data_nascimento": ("2999-01-01", "Data de nascimento inválida"),
        }
        for campo, (valor, mensagem) in casos.items():
            with self.subTest(campo=campo):
                form = CadastroForm(dados_form_cadastro(**{campo: valor}))
                self.assertFalse(form.is_valid())
                self.assertIn(mensagem, form.errors[campo])

    def test_nome_com_numero_e_invalido(self):
        form = CadastroForm(dados_form_cadastro(nome_completo="Maria 2"))

        self.assertIn("Nome inválido", form.errors["nome_completo"])

    def test_campo_vazio_usa_mensagem_de_obrigatorio(self):
        form = CadastroForm(dados_form_cadastro(cpf=""))

        self.assertIn("Campo obrigatório não preenchido", form.errors["cpf"])

    def test_exige_qual_deficiencia_somente_com_sim_outra(self):
        com_outra = CadastroForm(dados_form_cadastro(deficiencia="OUTRA"))
        self.assertIn("Campo obrigatório não preenchido", com_outra.errors["qual_deficiencia"])

        sem_outra = CadastroForm(dados_form_cadastro(deficiencia="NAO", qual_deficiencia="Algo"))
        self.assertTrue(sem_outra.is_valid(), sem_outra.errors)
        self.assertEqual(sem_outra.cleaned_data["qual_deficiencia"], "")

    def test_recusa_senha_sem_numero(self):
        form = CadastroForm(
            dados_form_cadastro(senha="SomenteLetras", confirmacao_senha="SomenteLetras")
        )

        self.assertIn(
            "A senha deve ter ao menos 8 caracteres, com letras e números", form.errors["senha"]
        )

    def test_recusa_senhas_diferentes(self):
        form = CadastroForm(dados_form_cadastro(confirmacao_senha="OutraSenha123"))

        self.assertIn("As senhas informadas não coincidem", form.errors["confirmacao_senha"])

    def test_exige_aceite_dos_termos(self):
        dados = dados_form_cadastro()
        del dados["aceite_termos"]

        form = CadastroForm(dados)

        self.assertIn(
            "É necessário aceitar os termos de uso e a política de privacidade",
            form.errors["aceite_termos"],
        )


class CadastroViewTests(TestCase):
    url = reverse("contas:cadastro")

    def test_post_valido_cria_conta_autentica_e_redireciona(self):
        resposta = self.client.post(self.url, dados_form_cadastro())

        self.assertRedirects(resposta, reverse("inicio"))
        usuario = Usuario.objects.get(email="maria@exemplo.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)

    def test_email_repetido_mostra_erro_no_campo_e_mantem_dados(self):
        criar_aluno()

        resposta = self.client.post(
            self.url, dados_form_cadastro(cpf=CPF_VALIDO_2.replace(".", "").replace("-", ""))
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "E-mail já cadastrado")
        self.assertContains(resposta, 'value="Maria@Exemplo.com"')
        self.assertContains(resposta, 'aria-describedby="id_email_error"')
        self.assertContains(resposta, 'id="id_email_error"')

    def test_menor_sem_responsavel_recebe_as_mensagens(self):
        hoje = timezone.localdate()
        nascimento = hoje.replace(year=hoje.year - 17).isoformat()

        resposta = self.client.post(self.url, dados_form_cadastro(data_nascimento=nascimento))

        self.assertContains(resposta, "Campo obrigatório não preenchido")
        self.assertContains(resposta, "É necessário confirmar a autorização do responsável")
        self.assertFalse(Usuario.objects.exists())

    def test_usuario_autenticado_e_redirecionado(self):
        self.client.force_login(criar_aluno())

        self.assertRedirects(self.client.get(self.url), reverse("inicio"))
