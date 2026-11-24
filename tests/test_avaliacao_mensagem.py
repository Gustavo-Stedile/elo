import unittest
from unittest.mock import Mock

from application.exceptions.autorizacao_exceptions import SemPermissaoErro
from domain.core.permissoes import de_nomes
from tests.support import App


class AvaliacaoMensagemTest(unittest.TestCase):
    def setUp(self):
        self.app = App()
        self.fundador = self.app.novo_usuario("fundador")
        self.ana = self.app.novo_usuario("ana")
        self.bia = self.app.novo_usuario("bia")
        gremio = self.app.gremios.criar_gremio(
            "Elo", "Escola", "Médio", self.fundador
        )
        self.gremio_id = gremio["id"]
        self.canal = self.app.canais.listar_canais(
            self.gremio_id, self.fundador
        )[0]
        self.moderador_ia = Mock()
        self.moderador_ia.avaliar.return_value = {"insulto": 0.9}
        self.app.mensagens.moderador = self.moderador_ia

    def test_ia_oculta_mensagem_ate_aprovacao_e_admin_pode_revisar(self):
        enviada = self.app.mensagens.enviar(
            self.canal.id, self.ana, "mensagem sinalizada"
        )
        self.assertTrue(enviada.marcada_inapropriada_ia)
        self.assertIsNone(enviada.avaliacao_admin)
        self.assertEqual(enviada.conteudo, "[Mensagem ocultada para avaliação]")

        listada_para_ana = self.app.mensagens.listar(
            self.canal.id, self.ana
        )[0]
        listada_para_fundador = self.app.mensagens.listar(
            self.canal.id, self.fundador
        )[0]
        self.assertEqual(
            listada_para_ana.conteudo, "[Mensagem ocultada para avaliação]"
        )
        self.assertEqual(listada_para_fundador.conteudo, "mensagem sinalizada")

        with self.assertRaises(SemPermissaoErro):
            self.app.mensagens.avaliar(
                self.canal.id, enviada.id, self.ana, True
            )

        aprovada = self.app.mensagens.avaliar(
            self.canal.id, enviada.id, self.fundador, True
        )
        self.assertTrue(aprovada.avaliacao_admin)
        self.assertEqual(aprovada.conteudo, "mensagem sinalizada")
        self.assertEqual(
            self.app.mensagens.listar(self.canal.id, self.ana)[0].conteudo,
            "mensagem sinalizada",
        )

        reprovada = self.app.mensagens.avaliar(
            self.canal.id, enviada.id, self.fundador, False
        )
        self.assertFalse(reprovada.avaliacao_admin)
        self.assertEqual(
            self.app.mensagens.listar(self.canal.id, self.ana)[0].conteudo,
            "[Mensagem ocultada para avaliação]",
        )

    def test_cargo_com_permissao_pode_avaliar_mensagem(self):
        mensagem = self.app.mensagens.enviar(
            self.canal.id, self.ana, "mensagem sinalizada"
        )
        cargo = self.app.cargos.criar_cargo(
            self.gremio_id,
            self.fundador,
            "Moderador de mensagens",
            "#123456",
            10,
            de_nomes(["AVALIAR_MENSAGENS"]),
        )
        self.app.membros.atribuir_cargo(
            self.gremio_id, self.fundador, self.bia, cargo.id
        )

        resultado = self.app.mensagens.avaliar(
            self.canal.id, mensagem.id, self.bia, True
        )

        self.assertTrue(resultado.avaliacao_admin)
        self.assertEqual(resultado.conteudo, "mensagem sinalizada")


if __name__ == "__main__":
    unittest.main()
