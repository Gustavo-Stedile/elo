import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np

from application.moderacao_mensagem import ModeradorMensagem
from tests.support import App


class ModeracaoMensagemTest(unittest.TestCase):
    def test_classifica_ameaca_e_ataque_a_identidade_com_limiares_proprios(self):
        moderador = ModeradorMensagem()
        moderador._tokenizer = Mock()
        moderador._tokenizer.encode.return_value = SimpleNamespace(ids=[1, 2])
        moderador._sessao = Mock()
        moderador._sessao.get_inputs.return_value = [
            SimpleNamespace(name="input_ids"),
            SimpleNamespace(name="attention_mask"),
        ]
        probabilidades = [0.1, 0.1, 0.1, 0.44, 0.1, 0.32, 0.1]
        logits = np.log(
            np.asarray(probabilidades) / (1 - np.asarray(probabilidades))
        )
        moderador._sessao.run.return_value = [np.asarray([logits])]

        resultado = moderador.avaliar("texto para classificar")

        self.assertEqual(set(resultado), {"ameaca", "ataque_a_identidade"})

    def test_registra_mensagem_sinalizada_em_json_lines(self):
        with tempfile.TemporaryDirectory() as diretorio:
            arquivo_log = Path(diretorio) / "log_mensagem_inadequada.txt"
            moderador = ModeradorMensagem(arquivo_log=arquivo_log)

            moderador.registrar_se_inadequada(
                "mensagem inadequada",
                autor_id=7,
                canal_id=12,
                categorias={"ameaca": 0.91},
            )

            registro = json.loads(arquivo_log.read_text(encoding="utf-8"))
            self.assertEqual(registro["mensagem"], "mensagem inadequada")
            self.assertEqual(registro["autor_id"], 7)
            self.assertEqual(registro["canal_id"], 12)
            self.assertEqual(registro["categorias"], {"ameaca": 0.91})

    def test_nao_cria_log_para_mensagem_sem_categoria_sinalizada(self):
        with tempfile.TemporaryDirectory() as diretorio:
            arquivo_log = Path(diretorio) / "log_mensagem_inadequada.txt"
            moderador = ModeradorMensagem(arquivo_log=arquivo_log)

            moderador.registrar_se_inadequada("mensagem adequada", 7, 12, {})

            self.assertFalse(arquivo_log.exists())

    def test_envio_classifica_e_registra_sem_bloquear_mensagem(self):
        app = App()
        fundador = app.novo_usuario("fundador")
        ana = app.novo_usuario("ana")
        gremio = app.gremios.criar_gremio(
            "Elo", "Escola", "Médio", fundador
        )
        canal = app.canais.listar_canais(gremio["id"], fundador)[0]
        moderador = Mock()
        moderador.avaliar.return_value = {"insulto": 0.84}
        app.mensagens.moderador = moderador

        mensagem = app.mensagens.enviar(canal.id, ana, "texto sinalizado")

        self.assertEqual(
            mensagem.conteudo, "[Mensagem ocultada para avaliação]"
        )
        self.assertTrue(mensagem.marcada_inapropriada_ia)
        moderador.avaliar.assert_called_once_with("texto sinalizado")
        moderador.registrar_se_inadequada.assert_called_once_with(
            "texto sinalizado", ana, canal.id, {"insulto": 0.84}
        )


if __name__ == "__main__":
    unittest.main()
