from datetime import date
from unittest import mock

from django.core import mail
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.exceptions import CpfDoResponsavelIgualAoDoAluno, ResponsavelSomenteLeitura
from contas.models import HistoricoAlteracao, ResponsavelLegal, Usuario
from contas.services import CadastroService, DadosResponsavel, PerfilService

from .fabricas import CPF_VALIDO, CPF_VALIDO_2, criar_admin, dados_cadastro, dados_form_cadastro

HOJE = date(2026, 11, 24)
MENOR = date(2010, 3, 15)
CPF_RESPONSAVEL = "390.533.447-05"


def responsavel(**alteracoes) -> DadosResponsavel:
    valores = {
        "nome": "Ana Souza",
        "vinculo": "MAE",
        "cpf": CPF_RESPONSAVEL,
        "email": "ana@exemplo.com",
        "telefone": "(11) 97777-6666",
    }
    valores.update(alteracoes)
    return DadosResponsavel(**valores)


def form_responsavel(**alteracoes) -> dict:
    valores = {
        "responsavel_nome": "Ana Souza",
        "responsavel_vinculo": "MAE",
        "responsavel_cpf": "39053344705",
        "responsavel_email": "Ana@Exemplo.com",
        "responsavel_telefone": "11977776666",
        "aceite_responsavel": "on",
    }
    valores.update(alteracoes)
    return valores


@mock.patch("django.utils.timezone.localdate", return_value=HOJE)
class CadastroDeMenorTests(TestCase):
    def test_menor_e_cadastrado_com_o_responsavel_e_o_termo(self, _):
        with self.captureOnCommitCallbacks(execute=True):
            aluno = CadastroService.cadastrar(dados_cadastro(data_nascimento=MENOR), responsavel())

        registro = ResponsavelLegal.objects.get(aluno=aluno)
        self.assertEqual((registro.nome, registro.vinculo), ("Ana Souza", "MAE"))
        self.assertIsNotNone(registro.termo_aceito_em)

    def test_responsavel_recebe_o_email_sem_a_deficiencia(self, _):
        with self.captureOnCommitCallbacks(execute=True):
            CadastroService.cadastrar(
                dados_cadastro(data_nascimento=MENOR, deficiencia="AUDITIVA"), responsavel()
            )

        aviso = mail.outbox[0]
        self.assertEqual(aviso.to, ["ana@exemplo.com"])
        self.assertIn("Maria da Silva", aviso.body)
        self.assertIn("24/11/2026", aviso.body)
        self.assertNotIn("auditiva", aviso.body.lower())

    def test_cpf_do_responsavel_igual_ao_do_aluno_e_recusado(self, _):
        with self.assertRaises(CpfDoResponsavelIgualAoDoAluno):
            CadastroService.cadastrar(dados_cadastro(data_nascimento=MENOR), responsavel(cpf=CPF_VALIDO))

    def test_o_mesmo_responsavel_pode_ter_dois_alunos(self, _):
        CadastroService.cadastrar(dados_cadastro(data_nascimento=MENOR), responsavel())
        CadastroService.cadastrar(
            dados_cadastro(data_nascimento=MENOR, email="irmao@exemplo.com", cpf=CPF_VALIDO_2), responsavel()
        )

        self.assertEqual(ResponsavelLegal.objects.filter(cpf=CPF_RESPONSAVEL).count(), 2)

    def test_maior_de_idade_se_cadastra_sem_responsavel(self, _):
        aluno = CadastroService.cadastrar(dados_cadastro(), responsavel())

        self.assertFalse(ResponsavelLegal.objects.filter(aluno=aluno).exists())

    def test_banco_recusa_vinculo_e_cpf_fora_do_formato(self, _):
        aluno = CadastroService.cadastrar(dados_cadastro(data_nascimento=MENOR), responsavel())
        for campos in ({"vinculo": "AVO"}, {"cpf": "39053344705"}):
            with self.subTest(campos=campos), self.assertRaises(IntegrityError), transaction.atomic():
                ResponsavelLegal.objects.filter(aluno=aluno).update(**campos)


class CadastroDeMenorViewTests(TestCase):
    def setUp(self):
        hoje = timezone.localdate()
        self.nascimento = hoje.replace(year=hoje.year - 15).isoformat()

    def test_menor_com_responsavel_e_cadastrado(self):
        with self.captureOnCommitCallbacks(execute=True):
            resposta = self.client.post(
                reverse("contas:cadastro"),
                {**dados_form_cadastro(data_nascimento=self.nascimento), **form_responsavel()},
                follow=True,
            )

        self.assertContains(resposta, "Cadastro realizado com sucesso")
        registro = ResponsavelLegal.objects.get()
        self.assertEqual((registro.cpf, registro.email), (CPF_RESPONSAVEL, "ana@exemplo.com"))

    def test_cpf_do_responsavel_invalido_ou_igual_ao_do_aluno(self):
        url = reverse("contas:cadastro")
        base = dados_form_cadastro(data_nascimento=self.nascimento)

        invalido = self.client.post(url, {**base, **form_responsavel(responsavel_cpf="12345678900")})
        igual = self.client.post(url, {**base, **form_responsavel(responsavel_cpf="52998224725")})

        self.assertContains(invalido, "CPF do responsável inválido")
        self.assertContains(igual, "O CPF do responsável deve ser diferente do CPF do aluno")
        self.assertFalse(Usuario.objects.exists())

    def test_maior_de_idade_tem_os_dados_do_responsavel_descartados(self):
        self.client.post(reverse("contas:cadastro"), {**dados_form_cadastro(), **form_responsavel()})

        self.assertTrue(Usuario.objects.exists())
        self.assertFalse(ResponsavelLegal.objects.exists())

    def test_tela_agrupa_os_campos_do_responsavel(self):
        resposta = self.client.get(reverse("contas:cadastro"))

        self.assertContains(resposta, 'id="dados-responsavel"')
        self.assertContains(resposta, "Ler o termo de autorização e consentimento")


class ResponsavelNoPerfilTests(TestCase):
    def setUp(self):
        hoje = timezone.localdate()
        self.aluno = CadastroService.cadastrar(
            dados_cadastro(data_nascimento=hoje.replace(year=hoje.year - 15)), responsavel()
        )

    def test_menor_altera_o_responsavel_com_historico_e_emails_ao_anterior_e_ao_novo(self):
        with self.captureOnCommitCallbacks(execute=True):
            PerfilService.atualizar_responsavel(self.aluno, responsavel(email="ana.nova@exemplo.com"))

        linha = HistoricoAlteracao.objects.get(campo="responsavel.email")
        self.assertEqual((linha.valor_anterior, linha.valor_novo), ("ana@exemplo.com", "ana.nova@exemplo.com"))
        self.assertEqual(mail.outbox[-1].to, ["ana@exemplo.com", "ana.nova@exemplo.com"])

    def test_sem_alteracao_nao_envia_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            PerfilService.atualizar_responsavel(self.aluno, responsavel())

        self.assertEqual(len(mail.outbox), 0)

    def test_quem_fez_18_anos_ve_so_para_leitura_e_nao_altera(self):
        Usuario.objects.filter(pk=self.aluno.pk).update(data_nascimento=date(2000, 1, 1))
        self.aluno.refresh_from_db()

        with self.assertRaises(ResponsavelSomenteLeitura):
            PerfilService.atualizar_responsavel(self.aluno, responsavel(nome="Outro Nome"))

        self.client.force_login(self.aluno)
        tela = self.client.get(reverse("contas:perfil"))
        self.assertContains(tela, "estes dados ficam só para consulta")
        self.assertNotContains(tela, 'action="/perfil/responsavel/"')
        post = self.client.post(reverse("contas:responsavel"), {
            "nome": "Outro Nome", "vinculo": "MAE", "cpf": "39053344705",
            "email": "ana@exemplo.com", "telefone": "11977776666",
        })
        self.assertEqual(post.status_code, 403)

    def test_menor_altera_pela_tela(self):
        self.client.force_login(self.aluno)

        resposta = self.client.post(reverse("contas:responsavel"), {
            "nome": "Ana Souza Lima", "vinculo": "MAE", "cpf": "39053344705",
            "email": "ana@exemplo.com", "telefone": "11977776666",
        }, follow=True)

        self.assertContains(resposta, "Dados atualizados com sucesso")
        self.assertEqual(ResponsavelLegal.objects.get().nome, "Ana Souza Lima")

    def test_admin_ve_o_responsavel_sem_poder_alterar(self):
        self.client.force_login(criar_admin())

        resposta = self.client.get(reverse("admin:contas_usuario_change", args=[self.aluno.pk]))

        self.assertContains(resposta, "Ana Souza")
        self.assertContains(resposta, "***.533.447-**")
        self.assertNotContains(resposta, 'name="responsavel-0-nome"')
