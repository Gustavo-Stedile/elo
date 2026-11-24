from datetime import datetime, timezone

from application.autorizacao_service import AutorizacaoService
from application.exceptions.autorizacao_exceptions import SemPermissaoErro
from application.exceptions.mensagem_exceptions import (
    MensagemInvalidaErro,
    MensagemNaoExisteErro,
    NaoEAutorErro,
)
from application.moderacao_mensagem import ModeradorMensagem
from domain.core import Mensagem
from domain.core.permissoes import Permissao
from infra.core.repositories import MensagemRepository, UsuarioRepository
from infra.unit_of_work import UnitOfWork

TAMANHO_MAXIMO = 4000
LIMITE_MAXIMO_POR_PAGINA = 100


class MensagemService:
    """Comunicação nos canais, sempre sujeita às permissões efetivas do canal.

    * enviar / editar: VER_CANAL + ENVIAR_MENSAGENS (editar: só o autor)
    * listar: VER_CANAL + LER_HISTORICO
    * apagar: o autor (com VER_CANAL) ou quem tem GERENCIAR_MENSAGENS
    """

    def __init__(
        self,
        mensagem_repository: MensagemRepository,
        usuario_repository: UsuarioRepository,
        autorizacao: AutorizacaoService,
        uow: UnitOfWork,
        moderador: ModeradorMensagem | None = None,
    ):
        self.mensagem_repository = mensagem_repository
        self.usuario_repository = usuario_repository
        self.autorizacao = autorizacao
        self.uow = uow
        self.moderador = moderador

    def enviar(self, canal_id: int, autor_id: int, conteudo: str) -> Mensagem:
        acesso = self.autorizacao.acessar_canal(
            canal_id, autor_id, Permissao.VER_CANAL | Permissao.ENVIAR_MENSAGENS
        )
        texto = self._normalizar(conteudo)

        categorias = {}
        if self.moderador:
            categorias = self.moderador.avaliar(texto)
            self.moderador.registrar_se_inadequada(
                texto, autor_id, canal_id, categorias
            )

        mensagem = self.mensagem_repository.create(Mensagem(
            id=None,
            canal_id=canal_id,
            autor_id=autor_id,
            conteudo=texto,
            criada_em=datetime.now(timezone.utc),
            marcada_inapropriada_ia=bool(categorias),
        ))
        self.uow.commit()

        autor = self.usuario_repository.get_by_id(autor_id)
        mensagem.autor_nome = autor.nome if autor else None
        self._ocultar_conteudo_se_necessario(mensagem, acesso.contexto.permissoes)
        return mensagem

    def listar(
        self,
        canal_id: int,
        usuario_id: int,
        limite: int = 50,
        antes_de: int | None = None,
        depois_de: int | None = None,
    ) -> list[Mensagem]:
        acesso = self.autorizacao.acessar_canal(
            canal_id, usuario_id, Permissao.VER_CANAL | Permissao.LER_HISTORICO
        )
        limite = max(1, min(limite, LIMITE_MAXIMO_POR_PAGINA))

        mensagens = self.mensagem_repository.listar(
            canal_id, limite, antes_de=antes_de, depois_de=depois_de
        )

        autores = self.usuario_repository.get_many([m.autor_id for m in mensagens])
        for m in mensagens:
            autor = autores.get(m.autor_id)
            m.autor_nome = autor.nome if autor else None
            self._ocultar_conteudo_se_necessario(
                m, acesso.contexto.permissoes
            )
        return mensagens

    def editar(
        self, canal_id: int, mensagem_id: int, ator_id: int, conteudo: str
    ) -> Mensagem:
        acesso = self.autorizacao.acessar_canal(
            canal_id, ator_id, Permissao.VER_CANAL | Permissao.ENVIAR_MENSAGENS
        )
        mensagem = self._obter(canal_id, mensagem_id)

        if mensagem.autor_id != ator_id:
            raise NaoEAutorErro()

        texto = self._normalizar(conteudo)
        categorias = {}
        if self.moderador:
            categorias = self.moderador.avaliar(texto)
            self.moderador.registrar_se_inadequada(
                texto, ator_id, canal_id, categorias
            )
        mensagem = self.mensagem_repository.atualizar_conteudo(
            mensagem.id,
            texto,
            datetime.now(timezone.utc),
            marcada_inapropriada_ia=bool(categorias),
            avaliacao_admin=None,
        )
        self.uow.commit()

        autor = self.usuario_repository.get_by_id(ator_id)
        mensagem.autor_nome = autor.nome if autor else None
        self._ocultar_conteudo_se_necessario(mensagem, acesso.contexto.permissoes)
        return mensagem

    def avaliar(
        self,
        canal_id: int,
        mensagem_id: int,
        avaliador_id: int,
        apropriada: bool,
    ) -> Mensagem:
        acesso = self.autorizacao.acessar_canal(
            canal_id, avaliador_id, Permissao.VER_CANAL
        )
        if not acesso.contexto.permissoes & int(
            Permissao.AVALIAR_MENSAGENS | Permissao.ADMINISTRADOR
        ):
            raise SemPermissaoErro(["AVALIAR_MENSAGENS"])

        mensagem = self._obter(canal_id, mensagem_id)
        mensagem = self.mensagem_repository.avaliar(
            mensagem.id, apropriada
        )
        if not mensagem:
            raise MensagemNaoExisteErro()
        self.uow.commit()

        autor = self.usuario_repository.get_by_id(mensagem.autor_id)
        mensagem.autor_nome = autor.nome if autor else None
        self._ocultar_conteudo_se_necessario(
            mensagem, acesso.contexto.permissoes
        )
        return mensagem

    @staticmethod
    def _ocultar_conteudo_se_necessario(
        mensagem: Mensagem, permissoes: int
    ) -> None:
        if (
            (mensagem.marcada_inapropriada_ia or mensagem.avaliacao_admin is False)
            and mensagem.avaliacao_admin is not True
            and not permissoes
            & int(Permissao.AVALIAR_MENSAGENS | Permissao.ADMINISTRADOR)
        ):
            mensagem.conteudo = "[Mensagem ocultada para avaliação]"

    def apagar(self, canal_id: int, mensagem_id: int, ator_id: int) -> None:
        acesso = self.autorizacao.acessar_canal(canal_id, ator_id, Permissao.VER_CANAL)
        mensagem = self._obter(canal_id, mensagem_id)

        if mensagem.autor_id != ator_id:
            if not acesso.permissoes & int(Permissao.GERENCIAR_MENSAGENS):
                raise SemPermissaoErro(["GERENCIAR_MENSAGENS"])

        self.mensagem_repository.delete(mensagem.id)
        self.uow.commit()

    # ------------------------------------------------------------------
    def _obter(self, canal_id: int, mensagem_id: int) -> Mensagem:
        mensagem = self.mensagem_repository.get_by_id(mensagem_id)
        # Mensagem de outro canal é tratada como inexistente: a permissão
        # conferida foi a deste canal, não a do canal dono da mensagem.
        if not mensagem or mensagem.canal_id != canal_id:
            raise MensagemNaoExisteErro()
        return mensagem

    @staticmethod
    def _normalizar(conteudo: str) -> str:
        texto = (conteudo or "").strip()
        if not texto:
            raise MensagemInvalidaErro()
        if len(texto) > TAMANHO_MAXIMO:
            raise MensagemInvalidaErro(
                f"A mensagem excede {TAMANHO_MAXIMO} caracteres."
            )
        return texto
