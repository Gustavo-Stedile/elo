"""Testes do motor de permissões (domínio puro, sem banco).

Rodar na raiz do projeto:  python -m unittest discover -s tests -v
"""
import unittest

from domain.core import Cargo, PermissaoCanal
from domain.core.autorizacao import (
    calcular_permissoes_canal,
    calcular_permissoes_gremio,
)
from domain.core.permissoes import (
    PERMISSOES_DE_CANAL,
    PERMISSOES_PADRAO_MEMBRO,
    TODAS,
    Permissao as P,
    de_nomes,
    e_valido,
    para_nomes,
)

VER, LER, ENVIAR, MOD = (
    int(P.VER_CANAL), int(P.LER_HISTORICO),
    int(P.ENVIAR_MENSAGENS), int(P.GERENCIAR_MENSAGENS),
)


def cargo(id, permissoes, padrao=False, prioridade=0):
    return Cargo(id, 1, f"c{id}", permissoes=permissoes, padrao=padrao, prioridade=prioridade)


def ow(permitir=0, negar=0, cargo_id=None, usuario_id=None):
    return PermissaoCanal(None, 1, permitir=permitir, negar=negar,
                          cargo_id=cargo_id, usuario_id=usuario_id)


PADRAO = cargo(1, PERMISSOES_PADRAO_MEMBRO, padrao=True)


class PermissoesGremioTest(unittest.TestCase):
    def test_membro_comum_recebe_apenas_o_cargo_padrao(self):
        r = calcular_permissoes_gremio(fundador=False, cargo_padrao=PADRAO, cargos=[])
        self.assertEqual(r, PERMISSOES_PADRAO_MEMBRO)

    def test_cargos_somam_permissoes(self):
        mod = cargo(2, MOD)
        r = calcular_permissoes_gremio(fundador=False, cargo_padrao=PADRAO, cargos=[mod])
        self.assertEqual(r, PERMISSOES_PADRAO_MEMBRO | MOD)

    def test_fundador_tem_tudo(self):
        r = calcular_permissoes_gremio(fundador=True, cargo_padrao=None, cargos=[])
        self.assertEqual(r, TODAS)

    def test_administrador_tem_tudo(self):
        adm = cargo(2, int(P.ADMINISTRADOR))
        r = calcular_permissoes_gremio(fundador=False, cargo_padrao=PADRAO, cargos=[adm])
        self.assertEqual(r, TODAS)

    def test_usuario_pode_ter_permissao_extra(self):
        r = calcular_permissoes_gremio(
            fundador=False, cargo_padrao=PADRAO, cargos=[],
            permitir_usuario=int(P.GERENCIAR_CANAIS))
        self.assertTrue(r & int(P.GERENCIAR_CANAIS))

    def test_negacao_individual_vence_o_cargo(self):
        r = calcular_permissoes_gremio(
            fundador=False, cargo_padrao=PADRAO, cargos=[], negar_usuario=ENVIAR)
        self.assertFalse(r & ENVIAR)
        self.assertTrue(r & VER)

    def test_negacao_individual_nao_remove_administrador(self):
        adm = cargo(2, int(P.ADMINISTRADOR))
        r = calcular_permissoes_gremio(
            fundador=False, cargo_padrao=PADRAO, cargos=[adm], negar_usuario=TODAS)
        self.assertEqual(r, TODAS)


class PermissoesCanalTest(unittest.TestCase):
    BASE = PERMISSOES_PADRAO_MEMBRO

    def test_sem_sobrescritas_herda_do_gremio(self):
        self.assertEqual(calcular_permissoes_canal(self.BASE), self.BASE)

    def test_canal_privado_esconde_tudo_do_cargo_padrao(self):
        r = calcular_permissoes_canal(self.BASE, ow_padrao=ow(negar=VER, cargo_id=1))
        self.assertEqual(r & PERMISSOES_DE_CANAL, 0)

    def test_cargo_libera_canal_privado(self):
        r = calcular_permissoes_canal(
            self.BASE | MOD,
            ow_padrao=ow(negar=VER, cargo_id=1),
            ow_cargos=[ow(permitir=VER, cargo_id=2)])
        self.assertTrue(r & VER)
        self.assertTrue(r & ENVIAR)

    def test_canal_somente_leitura(self):
        r = calcular_permissoes_canal(self.BASE, ow_padrao=ow(negar=ENVIAR, cargo_id=1))
        self.assertTrue(r & VER and r & LER)
        self.assertFalse(r & ENVIAR)

    def test_cargo_que_permite_vence_cargo_que_nega(self):
        r = calcular_permissoes_canal(
            self.BASE,
            ow_cargos=[ow(negar=ENVIAR, cargo_id=2), ow(permitir=ENVIAR, cargo_id=3)])
        self.assertTrue(r & ENVIAR)

    def test_usuario_vence_cargos(self):
        silenciado = calcular_permissoes_canal(
            self.BASE,
            ow_cargos=[ow(permitir=ENVIAR, cargo_id=2)],
            ow_usuario=ow(negar=ENVIAR, usuario_id=9))
        self.assertFalse(silenciado & ENVIAR)

        liberado = calcular_permissoes_canal(
            self.BASE,
            ow_padrao=ow(negar=VER | ENVIAR, cargo_id=1),
            ow_usuario=ow(permitir=VER | ENVIAR, usuario_id=9))
        self.assertTrue(liberado & VER and liberado & ENVIAR)

    def test_sem_ver_canal_nada_de_canal_vale(self):
        r = calcular_permissoes_canal(
            self.BASE,
            ow_padrao=ow(negar=VER, cargo_id=1),
            ow_usuario=ow(permitir=ENVIAR, usuario_id=9))
        self.assertEqual(r & PERMISSOES_DE_CANAL, 0)

    def test_permissoes_de_gremio_passam_intactas(self):
        base = self.BASE | int(P.GERENCIAR_CANAIS)
        r = calcular_permissoes_canal(base, ow_padrao=ow(negar=VER, cargo_id=1))
        self.assertTrue(r & int(P.GERENCIAR_CANAIS))

    def test_administrador_ignora_sobrescritas(self):
        r = calcular_permissoes_canal(
            TODAS, ow_padrao=ow(negar=VER), ow_usuario=ow(negar=TODAS, usuario_id=9))
        self.assertEqual(r, TODAS)


class CatalogoTest(unittest.TestCase):
    def test_ida_e_volta_de_nomes(self):
        nomes = ["VER_CANAL", "ENVIAR_MENSAGENS"]
        self.assertEqual(sorted(para_nomes(de_nomes(nomes))), sorted(nomes))

    def test_nome_desconhecido(self):
        with self.assertRaises(ValueError):
            de_nomes(["VOAR"])

    def test_validacao_de_mascara(self):
        self.assertTrue(e_valido(VER | ENVIAR, PERMISSOES_DE_CANAL))
        self.assertFalse(e_valido(int(P.GERENCIAR_CARGOS), PERMISSOES_DE_CANAL))
        self.assertFalse(e_valido(-1))
        self.assertFalse(e_valido(1 << 20))


if __name__ == "__main__":
    unittest.main()
