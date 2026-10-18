"""Regras de negócio da comunicação por canais, com repositórios em memória.

Rodar na raiz do projeto:  python -m unittest discover -s tests -v
"""
import unittest

from tests.support import App

from application.exceptions.autorizacao_exceptions import (
    HierarquiaInsuficienteErro, NaoEMembroErro, PermissaoInvalidaErro, SemPermissaoErro,
)
from application.exceptions.canal_exceptions import CanalJaExisteErro, CanalNaoExisteErro
from application.exceptions.cargo_exceptions import CargoPadraoProtegidoErro
from application.exceptions.membro_gremio_exceptions import (
    FundadorProtegidoErro, MembroJaExisteErro, MembroNaoExisteErro,
)
from application.exceptions.mensagem_exceptions import (
    MensagemInvalidaErro, MensagemNaoExisteErro, NaoEAutorErro,
)
from domain.core.permissoes import TODAS, Permissao as P, de_nomes, para_nomes

VER, LER, ENVIAR, MOD = (int(P.VER_CANAL), int(P.LER_HISTORICO),
                         int(P.ENVIAR_MENSAGENS), int(P.GERENCIAR_MENSAGENS))


class Base(unittest.TestCase):
    def setUp(self):
        self.app = App()
        self.fundador = self.app.novo_usuario("fundador")
        self.ana = self.app.novo_usuario("ana")
        self.bia = self.app.novo_usuario("bia")
        self.carla = self.app.novo_usuario("carla")
        self.forasteiro = self.app.novo_usuario("forasteiro")

        g = self.app.gremios.criar_gremio("Elo", "Escola", "Médio", self.fundador)
        self.gremio = g["id"]
        for u in (self.ana, self.bia, self.carla):
            self.app.membros.adicionar_membro(self.gremio, self.fundador, u)

        self.geral = self.app.canais.listar_canais(self.gremio, self.fundador)[0]
        cargos = {c.nome: c for c in self.app.cargos.listar_cargos(self.gremio, self.fundador)}
        self.cargo_membro, self.cargo_admin = cargos["Membro"], cargos["Administrador"]

    # atalhos
    def criar_cargo(self, nome, prioridade, perms=(), ator=None):
        return self.app.cargos.criar_cargo(
            self.gremio, ator or self.fundador, nome, "#112233", prioridade, de_nomes(perms))

    def novo_canal(self, nome="privado", ator=None):
        return self.app.canais.criar_canal(self.gremio, ator or self.fundador, nome)

    def enviar(self, canal, usuario, texto="oi"):
        return self.app.mensagens.enviar(canal.id, usuario, texto)

    def ids_visiveis(self, usuario):
        return {c.id for c in self.app.canais.listar_canais(self.gremio, usuario)}


class CriacaoDoGremioTest(Base):
    def test_estrutura_inicial(self):
        cargos = {c.nome: c for c in self.app.cargos.listar_cargos(self.gremio, self.fundador)}
        self.assertTrue(cargos["Membro"].padrao)
        self.assertEqual(cargos["Administrador"].permissoes, int(P.ADMINISTRADOR))
        self.assertEqual(self.geral.nome, "geral")

    def test_fundador_e_membro_com_todas_as_permissoes(self):
        r = self.app.gremios.minhas_permissoes(self.gremio, self.fundador)
        self.assertTrue(r["fundador"])
        self.assertEqual(set(r["permissoes"]), set(para_nomes(TODAS)))

    def test_membro_comum_nao_gerencia_nada(self):
        r = self.app.gremios.minhas_permissoes(self.gremio, self.ana)
        self.assertEqual(set(r["permissoes"]), {"VER_CANAL", "LER_HISTORICO", "ENVIAR_MENSAGENS"})

    def test_gremio_so_aparece_para_membros(self):
        self.assertEqual(len(self.app.gremios.listar_do_usuario(self.ana)), 1)
        self.assertEqual(self.app.gremios.listar_do_usuario(self.forasteiro), [])
        with self.assertRaises(NaoEMembroErro):
            self.app.gremios.obter_do_membro(self.gremio, self.forasteiro)


class MensagensTest(Base):
    def test_membro_envia_e_lista(self):
        m = self.enviar(self.geral, self.ana, "  olá  ")
        self.assertEqual(m.conteudo, "olá")
        self.assertEqual(m.autor_nome, "ana")
        lista = self.app.mensagens.listar(self.geral.id, self.bia)
        self.assertEqual([x.id for x in lista], [m.id])
        self.assertEqual(lista[0].autor_nome, "ana")

    def test_nao_membro_nao_ve_nem_envia(self):
        with self.assertRaises(CanalNaoExisteErro):
            self.enviar(self.geral, self.forasteiro)
        with self.assertRaises(CanalNaoExisteErro):
            self.app.mensagens.listar(self.geral.id, self.forasteiro)

    def test_mensagem_vazia_ou_gigante(self):
        with self.assertRaises(MensagemInvalidaErro):
            self.enviar(self.geral, self.ana, "   ")
        with self.assertRaises(MensagemInvalidaErro):
            self.enviar(self.geral, self.ana, "x" * 4001)

    def test_paginacao_e_polling(self):
        ids = [self.enviar(self.geral, self.ana, f"m{i}").id for i in range(5)]
        ultimas = self.app.mensagens.listar(self.geral.id, self.ana, limite=2)
        self.assertEqual([m.id for m in ultimas], ids[-2:])
        anteriores = self.app.mensagens.listar(self.geral.id, self.ana, limite=2, antes_de=ids[-2])
        self.assertEqual([m.id for m in anteriores], ids[1:3])
        novas = self.app.mensagens.listar(self.geral.id, self.ana, depois_de=ids[2])
        self.assertEqual([m.id for m in novas], ids[3:])

    def test_editar_somente_o_autor(self):
        m = self.enviar(self.geral, self.ana, "a")
        with self.assertRaises(NaoEAutorErro):
            self.app.mensagens.editar(self.geral.id, m.id, self.bia, "b")
        with self.assertRaises(NaoEAutorErro):  # nem o fundador edita texto alheio
            self.app.mensagens.editar(self.geral.id, m.id, self.fundador, "b")
        editada = self.app.mensagens.editar(self.geral.id, m.id, self.ana, "novo")
        self.assertEqual(editada.conteudo, "novo")
        self.assertIsNotNone(editada.editada_em)

    def test_apagar_autor_moderador_e_terceiro(self):
        m = self.enviar(self.geral, self.ana)
        with self.assertRaises(SemPermissaoErro):
            self.app.mensagens.apagar(self.geral.id, m.id, self.bia)
        self.app.mensagens.apagar(self.geral.id, m.id, self.ana)  # autor

        m2 = self.enviar(self.geral, self.ana)
        mod = self.criar_cargo("Mod", 10, ["GERENCIAR_MENSAGENS"])
        self.app.membros.atribuir_cargo(self.gremio, self.fundador, self.bia, mod.id)
        self.app.mensagens.apagar(self.geral.id, m2.id, self.bia)  # moderador
        self.assertEqual(self.app.mensagens.listar(self.geral.id, self.ana), [])

    def test_mensagem_de_outro_canal_e_inexistente(self):
        outro = self.novo_canal("outro")
        m = self.enviar(self.geral, self.ana)
        with self.assertRaises(MensagemNaoExisteErro):
            self.app.mensagens.apagar(outro.id, m.id, self.fundador)
        with self.assertRaises(MensagemNaoExisteErro):
            self.app.mensagens.editar(outro.id, m.id, self.ana, "x")


class PermissoesDeCanalTest(Base):
    def test_canal_privado_por_cargo(self):
        privado = self.novo_canal("diretoria")
        diretoria = self.criar_cargo("Diretoria", 50)
        self.app.membros.atribuir_cargo(self.gremio, self.fundador, self.ana, diretoria.id)

        self.app.canais.definir_permissao_cargo(
            privado.id, self.fundador, self.cargo_membro.id, 0, VER)            # todos: sem acesso
        self.app.canais.definir_permissao_cargo(
            privado.id, self.fundador, diretoria.id, VER | LER | ENVIAR, 0)     # diretoria: acesso

        self.assertIn(privado.id, self.ids_visiveis(self.ana))
        self.assertNotIn(privado.id, self.ids_visiveis(self.bia))
        self.assertIn(self.geral.id, self.ids_visiveis(self.bia))

        self.enviar(privado, self.ana, "reunião às 10h")
        with self.assertRaises(CanalNaoExisteErro):   # nem revela que existe
            self.app.canais.obter_canal(privado.id, self.bia)
        with self.assertRaises(CanalNaoExisteErro):
            self.enviar(privado, self.bia)
        with self.assertRaises(CanalNaoExisteErro):
            self.app.mensagens.listar(privado.id, self.bia)

    def test_canal_somente_leitura(self):
        avisos = self.novo_canal("avisos")
        self.app.canais.definir_permissao_cargo(
            avisos.id, self.fundador, self.cargo_membro.id, 0, ENVIAR)
        with self.assertRaises(SemPermissaoErro):
            self.enviar(avisos, self.ana)
        self.assertEqual(self.app.mensagens.listar(avisos.id, self.ana), [])  # ainda lê
        self.enviar(avisos, self.fundador, "aviso")  # quem administra continua enviando

    def test_silenciar_um_usuario_em_um_canal(self):
        self.app.canais.definir_permissao_usuario(self.geral.id, self.fundador, self.ana, 0, ENVIAR)
        with self.assertRaises(SemPermissaoErro):
            self.enviar(self.geral, self.ana)
        self.enviar(self.geral, self.bia)                    # os demais seguem normais
        outro = self.novo_canal("outro")
        self.enviar(outro, self.ana)                         # e a restrição é só neste canal

    def test_liberar_um_usuario_em_canal_privado(self):
        privado = self.novo_canal("secreto")
        self.app.canais.definir_permissao_cargo(privado.id, self.fundador, self.cargo_membro.id, 0, VER)
        self.app.canais.definir_permissao_usuario(privado.id, self.fundador, self.carla, VER | LER | ENVIAR, 0)
        self.enviar(privado, self.carla)
        self.assertNotIn(privado.id, self.ids_visiveis(self.ana))

    def test_remover_sobrescrita_restaura_acesso(self):
        self.app.canais.definir_permissao_usuario(self.geral.id, self.fundador, self.ana, 0, ENVIAR)
        self.app.canais.remover_permissao_usuario(self.geral.id, self.fundador, self.ana)
        self.enviar(self.geral, self.ana)
        self.assertEqual(self.app.canais.listar_permissoes(self.geral.id, self.fundador), [])

    def test_enviar_zero_zero_remove_sobrescrita(self):
        self.app.canais.definir_permissao_usuario(self.geral.id, self.fundador, self.ana, 0, ENVIAR)
        r = self.app.canais.definir_permissao_usuario(self.geral.id, self.fundador, self.ana, 0, 0)
        self.assertIsNone(r)

    def test_minhas_permissoes_no_canal(self):
        self.app.canais.definir_permissao_cargo(self.geral.id, self.fundador, self.cargo_membro.id, 0, ENVIAR)
        acesso = self.app.canais.obter_canal(self.geral.id, self.ana)
        self.assertEqual(set(para_nomes(acesso.permissoes)), {"VER_CANAL", "LER_HISTORICO"})

    def test_gerenciar_canais_nao_burla_leitura_de_canal_privado(self):
        privado = self.novo_canal("secreto")
        self.app.canais.definir_permissao_cargo(privado.id, self.fundador, self.cargo_membro.id, 0, VER)
        gestor = self.criar_cargo("Gestor", 10, ["GERENCIAR_CANAIS"])
        self.app.membros.atribuir_cargo(self.gremio, self.fundador, self.ana, gestor.id)
        # Gerente encontra o canal para poder consertar permissões...
        self.app.canais.listar_permissoes(privado.id, self.ana)
        # ...mas não lê o conteúdo.
        with self.assertRaises(SemPermissaoErro):
            self.app.mensagens.listar(privado.id, self.ana)

    def test_validacao_das_mascaras(self):
        with self.assertRaises(PermissaoInvalidaErro):  # permissão de grêmio em canal
            self.app.canais.definir_permissao_usuario(
                self.geral.id, self.fundador, self.ana, int(P.GERENCIAR_CARGOS), 0)
        with self.assertRaises(PermissaoInvalidaErro):  # permitir e negar a mesma
            self.app.canais.definir_permissao_usuario(
                self.geral.id, self.fundador, self.ana, ENVIAR, ENVIAR)

    def test_sem_gerenciar_canais_nao_mexe_em_permissoes(self):
        with self.assertRaises(SemPermissaoErro):
            self.app.canais.definir_permissao_usuario(self.geral.id, self.ana, self.bia, 0, ENVIAR)
        with self.assertRaises(SemPermissaoErro):
            self.app.canais.listar_permissoes(self.geral.id, self.ana)

    def test_excluir_canal_apaga_mensagens(self):
        c = self.novo_canal("temp")
        self.enviar(c, self.ana)
        self.app.canais.excluir_canal(c.id, self.fundador)
        self.assertEqual(self.app.store.mensagens.get(c.id), None)
        self.assertNotIn(c.id, self.ids_visiveis(self.ana))

    def test_nome_de_canal_unico_no_gremio(self):
        with self.assertRaises(CanalJaExisteErro):
            self.novo_canal("geral")


class PermissoesDeGremioPorUsuarioTest(Base):
    def test_permissao_individual_no_gremio(self):
        with self.assertRaises(SemPermissaoErro):
            self.novo_canal("x", ator=self.ana)
        self.app.membros.definir_permissoes_usuario(
            self.gremio, self.fundador, self.ana, de_nomes(["GERENCIAR_CANAIS"]), 0)
        self.novo_canal("x", ator=self.ana)

    def test_negacao_individual_vale_em_todos_os_canais(self):
        outro = self.novo_canal("outro")
        self.app.membros.definir_permissoes_usuario(
            self.gremio, self.fundador, self.ana, 0, ENVIAR)
        for canal in (self.geral, outro):
            with self.assertRaises(SemPermissaoErro):
                self.enviar(canal, self.ana)
        self.enviar(self.geral, self.bia)

    def test_override_de_canal_pode_liberar_o_que_o_gremio_negou(self):
        self.app.membros.definir_permissoes_usuario(self.gremio, self.fundador, self.ana, 0, ENVIAR)
        self.app.canais.definir_permissao_usuario(self.geral.id, self.fundador, self.ana, ENVIAR, 0)
        self.enviar(self.geral, self.ana)

    def test_fundador_e_intocavel(self):
        with self.assertRaises(FundadorProtegidoErro):
            self.app.membros.definir_permissoes_usuario(self.gremio, self.fundador, self.fundador, 0, ENVIAR)
        with self.assertRaises(FundadorProtegidoErro):
            self.app.membros.remover_membro(self.gremio, self.fundador, self.fundador)
        with self.assertRaises(FundadorProtegidoErro):
            self.app.canais.definir_permissao_usuario(self.geral.id, self.fundador, self.fundador, 0, ENVIAR)


class HierarquiaTest(Base):
    def setUp(self):
        super().setUp()
        self.mod = self.criar_cargo("Moderador", 10, ["GERENCIAR_CARGOS", "GERENCIAR_CANAIS", "GERENCIAR_MEMBROS"])
        self.app.membros.atribuir_cargo(self.gremio, self.fundador, self.ana, self.mod.id)   # ana = moderadora

    def test_nao_cria_cargo_igual_ou_acima(self):
        for prioridade in (10, 11, 100):
            with self.assertRaises(HierarquiaInsuficienteErro):
                self.criar_cargo(f"c{prioridade}", prioridade, ator=self.ana)
        self.criar_cargo("Auxiliar", 5, ["VER_CANAL"], ator=self.ana)

    def test_nao_concede_permissao_que_nao_tem(self):
        with self.assertRaises(SemPermissaoErro):
            self.criar_cargo("Golpe", 5, ["ADMINISTRADOR"], ator=self.ana)
        with self.assertRaises(SemPermissaoErro):
            self.criar_cargo("Golpe2", 5, ["GERENCIAR_GREMIO"], ator=self.ana)

    def test_nao_edita_nem_exclui_cargo_superior(self):
        with self.assertRaises(HierarquiaInsuficienteErro):
            self.app.cargos.atualizar_cargo(self.gremio, self.cargo_admin.id, self.ana, nome="X")
        with self.assertRaises(HierarquiaInsuficienteErro):
            self.app.cargos.excluir_cargo(self.gremio, self.cargo_admin.id, self.ana)

    def test_nao_se_autopromove_editando_o_proprio_cargo(self):
        with self.assertRaises(HierarquiaInsuficienteErro):
            self.app.cargos.atualizar_cargo(self.gremio, self.mod.id, self.ana, prioridade=11)
        with self.assertRaises(HierarquiaInsuficienteErro):
            self.app.cargos.atualizar_cargo(self.gremio, self.mod.id, self.ana, permissoes=int(P.ADMINISTRADOR))

    def test_nao_se_atribui_cargo_superior(self):
        with self.assertRaises(HierarquiaInsuficienteErro):
            self.app.membros.atribuir_cargo(self.gremio, self.ana, self.ana, self.cargo_admin.id)
        with self.assertRaises(HierarquiaInsuficienteErro):
            self.app.membros.atribuir_cargo(self.gremio, self.ana, self.bia, self.mod.id)  # igual ao seu

    def test_atribui_cargo_inferior(self):
        aux = self.criar_cargo("Auxiliar", 5, ["ENVIAR_MENSAGENS"], ator=self.ana)
        self.app.membros.atribuir_cargo(self.gremio, self.ana, self.bia, aux.id)
        det = {m.usuario_id: m for m in self.app.membros.listar_membros(self.gremio, self.ana)}
        self.assertEqual(det[self.bia].cargos_ids, [aux.id])

    def test_nao_remove_nem_altera_membro_de_cargo_superior_ou_igual(self):
        admin = self.app.novo_usuario("admin")
        self.app.membros.adicionar_membro(self.gremio, self.fundador, admin)
        self.app.membros.atribuir_cargo(self.gremio, self.fundador, admin, self.cargo_admin.id)
        with self.assertRaises(HierarquiaInsuficienteErro):
            self.app.membros.remover_membro(self.gremio, self.ana, admin)
        with self.assertRaises(HierarquiaInsuficienteErro):
            self.app.membros.definir_permissoes_usuario(self.gremio, self.ana, admin, 0, ENVIAR)
        with self.assertRaises(HierarquiaInsuficienteErro):
            self.app.canais.definir_permissao_usuario(self.geral.id, self.ana, admin, 0, ENVIAR)
        # mas modera quem está abaixo
        self.app.membros.remover_membro(self.gremio, self.ana, self.carla)

    def test_moderador_nao_concede_individualmente_o_que_nao_tem(self):
        with self.assertRaises(SemPermissaoErro):
            self.app.membros.definir_permissoes_usuario(
                self.gremio, self.ana, self.bia, de_nomes(["GERENCIAR_GREMIO"]), 0)

    def test_moderador_nao_concede_em_canal_o_que_nao_tem_no_canal(self):
        self.app.canais.definir_permissao_usuario(self.geral.id, self.fundador, self.ana, 0, ENVIAR)
        with self.assertRaises(SemPermissaoErro):
            self.app.canais.definir_permissao_usuario(self.geral.id, self.ana, self.bia, ENVIAR, 0)

    def test_cargo_padrao_e_protegido(self):
        with self.assertRaises(CargoPadraoProtegidoErro):
            self.app.cargos.excluir_cargo(self.gremio, self.cargo_membro.id, self.ana)
        with self.assertRaises(CargoPadraoProtegidoErro):
            self.app.cargos.atualizar_cargo(self.gremio, self.cargo_membro.id, self.ana, permissoes=int(P.ADMINISTRADOR))
        with self.assertRaises(CargoPadraoProtegidoErro):
            self.app.membros.atribuir_cargo(self.gremio, self.ana, self.bia, self.cargo_membro.id)

    def test_moderador_edita_o_cargo_padrao_dentro_do_que_possui(self):
        # Ana não tem ENVIAR... ela tem: removê-lo de todos é permitido; adicionar algo que não tem, não.
        novo = self.cargo_membro.permissoes & ~ENVIAR
        self.app.cargos.atualizar_cargo(self.gremio, self.cargo_membro.id, self.ana, permissoes=novo)
        with self.assertRaises(SemPermissaoErro):
            self.app.cargos.atualizar_cargo(
                self.gremio, self.cargo_membro.id, self.ana, permissoes=novo | MOD | int(P.GERENCIAR_GREMIO))

    def test_excluir_cargo_remove_atribuicoes_e_sobrescritas(self):
        aux = self.criar_cargo("Aux", 5, ["VER_CANAL"], ator=self.ana)
        self.app.membros.atribuir_cargo(self.gremio, self.ana, self.bia, aux.id)
        self.app.canais.definir_permissao_cargo(self.geral.id, self.fundador, aux.id, VER, 0)
        self.app.cargos.excluir_cargo(self.gremio, aux.id, self.ana)
        self.assertEqual(self.app.canais.listar_permissoes(self.geral.id, self.fundador), [])
        det = {m.usuario_id: m for m in self.app.membros.listar_membros(self.gremio, self.ana)}
        self.assertEqual(det[self.bia].cargos_ids, [])


class MembrosTest(Base):
    def test_so_quem_gerencia_membros_adiciona(self):
        with self.assertRaises(SemPermissaoErro):
            self.app.membros.adicionar_membro(self.gremio, self.ana, self.forasteiro)
        self.app.membros.adicionar_membro(self.gremio, self.fundador, self.forasteiro)
        with self.assertRaises(MembroJaExisteErro):
            self.app.membros.adicionar_membro(self.gremio, self.fundador, self.forasteiro)

    def test_sair_do_gremio_limpa_cargos_e_sobrescritas(self):
        cargo = self.criar_cargo("X", 5)
        self.app.membros.atribuir_cargo(self.gremio, self.fundador, self.ana, cargo.id)
        self.app.canais.definir_permissao_usuario(self.geral.id, self.fundador, self.ana, 0, ENVIAR)

        self.app.membros.remover_membro(self.gremio, self.ana, self.ana)   # saiu

        self.assertEqual(self.app.canais.listar_permissoes(self.geral.id, self.fundador), [])
        with self.assertRaises(CanalNaoExisteErro):
            self.enviar(self.geral, self.ana)
        # ao voltar, começa do zero
        self.app.membros.adicionar_membro(self.gremio, self.fundador, self.ana)
        self.enviar(self.geral, self.ana)

    def test_remocao_por_quem_gerencia(self):
        with self.assertRaises(SemPermissaoErro):
            self.app.membros.remover_membro(self.gremio, self.ana, self.bia)
        self.app.membros.remover_membro(self.gremio, self.fundador, self.bia)
        with self.assertRaises(MembroNaoExisteErro):
            self.app.membros.remover_membro(self.gremio, self.fundador, self.bia)

    def test_nao_membro_nao_lista_membros(self):
        with self.assertRaises(NaoEMembroErro):
            self.app.membros.listar_membros(self.gremio, self.forasteiro)

    def test_listagem_traz_nome_e_fundador(self):
        det = self.app.membros.listar_membros(self.gremio, self.ana)
        self.assertEqual({m.nome for m in det}, {"fundador", "ana", "bia", "carla"})
        self.assertEqual([m.nome for m in det if m.fundador], ["fundador"])


class IsolamentoEntreGremiosTest(Base):
    def test_cargo_e_canal_de_outro_gremio_sao_inexistentes(self):
        outro_dono = self.app.novo_usuario("dono2")
        g2 = self.app.gremios.criar_gremio("Outro", "Escola", "Médio", outro_dono)["id"]
        canal2 = self.app.canais.listar_canais(g2, outro_dono)[0]

        # fundador do grêmio 1 não é membro do 2
        with self.assertRaises(CanalNaoExisteErro):
            self.app.mensagens.listar(canal2.id, self.fundador)
        with self.assertRaises(CanalNaoExisteErro):
            self.app.canais.excluir_canal(canal2.id, self.fundador)

        # cargo do grêmio 2 não pode ser usado em canal do grêmio 1
        cargo2 = self.app.cargos.listar_cargos(g2, outro_dono)[0]
        from application.exceptions.cargo_exceptions import CargoNaoExisteErro
        with self.assertRaises(CargoNaoExisteErro):
            self.app.canais.definir_permissao_cargo(self.geral.id, self.fundador, cargo2.id, VER, 0)
        with self.assertRaises(CargoNaoExisteErro):
            self.app.membros.atribuir_cargo(self.gremio, self.fundador, self.ana, cargo2.id)


if __name__ == "__main__":
    unittest.main()
