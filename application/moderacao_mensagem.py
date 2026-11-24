import hashlib
import json
import threading
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import onnxruntime
from tokenizers import Tokenizer


MODELO_ID = "Horizon-Labs/multilingual-toxicity-small"
REVISAO_MODELO = "a3c77222591af24ff81425c84146741c869f7835"
MAXIMO_TOKENS = 512
ROTULOS_E_LIMIARES = {
    "toxicidade": 0.5,
    "toxicidade_grave": 0.5,
    "obscenidade": 0.5,
    "ameaca": 0.4,
    "insulto": 0.5,
    "ataque_a_identidade": 0.3,
    "conteudo_sexual_explicito": 0.5,
}

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
DIRETORIO_MODELO = RAIZ_PROJETO / "modelos" / "multilingual-toxicity-small"
ARQUIVO_LOG = RAIZ_PROJETO / "log_mensagem_inadequada.txt"

_ARQUIVOS_MODELO = {
    "tokenizer.json": "4379fe7f4a7af10b1ac15ffc8ae90f446f92082393699e9dd54b8c3b5ec0abad",
    "onnx/model_quantized.onnx": "44d470dcb255c3b369dcfb2b0bab12610513e5cca635325ea86bf104a14f0080",
}
_LOCK_LOG = threading.Lock()


class ModeradorMensagem:
    """Classifica mensagens localmente e registra as que excedem o limiar."""

    def __init__(
        self,
        diretorio_modelo: Path = DIRETORIO_MODELO,
        arquivo_log: Path = ARQUIVO_LOG,
    ):
        self.diretorio_modelo = Path(diretorio_modelo)
        self.arquivo_log = Path(arquivo_log)
        self._sessao = None
        self._tokenizer = None
        self._lock_modelo = threading.Lock()

    def avaliar(self, texto: str) -> dict[str, float]:
        self._carregar_modelo()
        codificado = self._tokenizer.encode(texto, add_special_tokens=True)
        ids = codificado.ids[:MAXIMO_TOKENS]
        if not ids:
            return {}

        mascara = [1] * len(ids)
        preenchimento = MAXIMO_TOKENS - len(ids)
        ids.extend([0] * preenchimento)
        mascara.extend([0] * preenchimento)

        tensores = {
            "input_ids": np.asarray([ids], dtype=np.int64),
            "attention_mask": np.asarray([mascara], dtype=np.int64),
        }
        entradas = {}
        for entrada in self._sessao.get_inputs():
            if entrada.name not in tensores:
                raise RuntimeError(
                    f"Entrada ONNX não suportada pelo moderador: {entrada.name}"
                )
            entradas[entrada.name] = tensores[entrada.name]

        logits = self._sessao.run(None, entradas)[0][0]
        if len(logits) != len(ROTULOS_E_LIMIARES):
            raise RuntimeError(
                "O modelo retornou uma quantidade inesperada de categorias."
            )
        probabilidades = 1.0 / (1.0 + np.exp(-np.clip(logits, -80, 80)))
        return {
            rotulo: float(probabilidade)
            for (rotulo, limiar), probabilidade in zip(
                ROTULOS_E_LIMIARES.items(), probabilidades
            )
            if float(probabilidade) >= limiar
        }

    def registrar_se_inadequada(
        self,
        texto: str,
        autor_id: int,
        canal_id: int,
        categorias: dict[str, float],
    ) -> None:
        if not categorias:
            return

        registro = {
            "data_hora": datetime.now(timezone.utc).isoformat(),
            "autor_id": autor_id,
            "canal_id": canal_id,
            "modelo": MODELO_ID,
            "categorias": categorias,
            "mensagem": texto,
        }
        self.arquivo_log.parent.mkdir(parents=True, exist_ok=True)
        linha = json.dumps(registro, ensure_ascii=False) + "\n"
        with _LOCK_LOG:
            with self.arquivo_log.open("a", encoding="utf-8") as arquivo:
                arquivo.write(linha)

    def _carregar_modelo(self) -> None:
        if self._sessao is not None:
            return
        with self._lock_modelo:
            if self._sessao is not None:
                return

            for nome, sha256 in _ARQUIVOS_MODELO.items():
                caminho = self.diretorio_modelo / nome
                self._baixar_se_necessario(caminho, nome, sha256)

            tokenizer = Tokenizer.from_file(
                str(self.diretorio_modelo / "tokenizer.json")
            )
            tokenizer.enable_truncation(max_length=MAXIMO_TOKENS)
            sessao = onnxruntime.InferenceSession(
                str(self.diretorio_modelo / "onnx" / "model_quantized.onnx"),
                providers=["CPUExecutionProvider"],
            )
            self._tokenizer = tokenizer
            self._sessao = sessao

    def _baixar_se_necessario(
        self, destino: Path, nome: str, sha256_esperado: str
    ) -> None:
        if destino.is_file() and self._sha256(destino) == sha256_esperado:
            return

        destino.parent.mkdir(parents=True, exist_ok=True)
        url = (
            f"https://huggingface.co/{MODELO_ID}/resolve/"
            f"{REVISAO_MODELO}/{nome}"
        )
        temporario = destino.with_name(destino.name + ".download")
        try:
            with urllib.request.urlopen(url, timeout=60) as resposta:
                with temporario.open("wb") as arquivo:
                    while bloco := resposta.read(1024 * 1024):
                        arquivo.write(bloco)
            if self._sha256(temporario) != sha256_esperado:
                raise RuntimeError(f"Falha na verificação SHA-256 do modelo: {nome}")
            temporario.replace(destino)
        except (OSError, urllib.error.URLError, TimeoutError, RuntimeError) as erro:
            temporario.unlink(missing_ok=True)
            raise RuntimeError(
                f"Não foi possível baixar ou verificar {nome} do modelo "
                f"{MODELO_ID}."
            ) from erro

    @staticmethod
    def _sha256(caminho: Path) -> str:
        digest = hashlib.sha256()
        with caminho.open("rb") as arquivo:
            for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
                digest.update(bloco)
        return digest.hexdigest()
