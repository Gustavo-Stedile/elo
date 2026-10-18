from application.autorizacao_service import AutorizacaoService
from application.exceptions.gremio_exceptions import GremioNaoExisteErro
from application.exceptions.usuario_exceptions import UsuarioNaoExisteErro
from domain.core import Cargo, Canal, Gremio, MembroGremio
from domain.core.permissoes import (
    PERMISSOES_PADRAO_MEMBRO,
    Permissao,
    para_nomes,
)
from infra.core.repositories import (
    CanalRepository,
    CargoRepository,
    GremioRepository,
    MembroGremioRepository,
    UsuarioRepository,
)
from infra.unit_of_work import UnitOfWork


class GremioService:
    def __init__(
        self,
        gremio_repository: GremioRepository,
        membro_gremio_repository: MembroGremioRepository,
        cargo_repository: CargoRepository,
        canal_repository: CanalRepository,
        usuario_repository: UsuarioRepository,
        autorizacao: AutorizacaoService,
        uow: UnitOfWork,
    ):
        self.gremio_repository = gremio_repository
        self.membro_gremio_repository = membro_gremio_repository
        self.cargo_repository = cargo_repository
        self.canal_repository = canal_repository
        self.usuario_repository = usuario_repository
        self.autorizacao = autorizacao
        self.uow = uow

    @staticmethod
    def _para_dict(gremio: Gremio) -> dict:
        return {
            "id": gremio.id,
            "nome": gremio.nome,
            "instituicao": gremio.instituicao,
            "etapa_ensino": gremio.etapa_ensino,
            "legitimado": gremio.legitimado,
            "fundador_id": gremio.fundador_id,
        }

    def criar_gremio(
        self, 
        nome: str, 
        instituicao: str, 
        etapa_ensino: str, 
        fundador_id: int
    ) -> dict:
        """Cria um grêmio com a estrutura inicial de comunicação.

        Em uma única transação cria: o grêmio, o cargo padrão "Membro" (todos
        os membros), o cargo "Administrador", o vínculo do fundador e o canal
        "geral".
        """
        if not self.usuario_repository.get_by_id(fundador_id):
            raise UsuarioNaoExisteErro()

        gremio_salvo = self.gremio_repository.create(Gremio(
            id=None,
            nome=nome,
            instituicao=instituicao,
            etapa_ensino=etapa_ensino,
            legitimado=False,
            fundador_id=fundador_id,
        ))

        self.cargo_repository.create(Cargo(
            id=None,
            gremio_id=gremio_salvo.id,
            nome="Membro",
            cor="#99AAB5",
            prioridade=0,
            permissoes=PERMISSOES_PADRAO_MEMBRO,
            padrao=True,
        ))
        self.cargo_repository.create(Cargo(
            id=None,
            gremio_id=gremio_salvo.id,
            nome="Administrador",
            cor="#E67E22",
            prioridade=100,
            permissoes=int(Permissao.ADMINISTRADOR),
        ))

        self.membro_gremio_repository.create(MembroGremio(
            id=None,
            usuario_id=fundador_id,
            gremio_id=gremio_salvo.id,
        ))

        self.canal_repository.create(Canal(
            id=None,
            gremio_id=gremio_salvo.id,
            nome="geral",
            descricao="Canal geral do grêmio",
        ))

        self.uow.commit()
        return self._para_dict(gremio_salvo)

    def buscar_por_id(self, id: int) -> dict:
        """Busca um grêmio pelo ID. Lança exceção se não encontrar."""
        gremio = self.gremio_repository.get_by_id(id)

        if not gremio:
            raise GremioNaoExisteErro()
        
        return self._para_dict(gremio)

    def obter_do_membro(self, gremio_id: int, usuario_id: int) -> dict:
        """Dados do grêmio, visíveis apenas para seus membros."""
        ctx = self.autorizacao.contexto(gremio_id, usuario_id)
        return self._para_dict(ctx.gremio)

    def listar_do_usuario(self, usuario_id: int) -> list[dict]:
        return [
            self._para_dict(g)
            for g in self.gremio_repository.listar_por_usuario(usuario_id)
        ]

    def minhas_permissoes(self, gremio_id: int, usuario_id: int) -> dict:
        ctx = self.autorizacao.contexto(gremio_id, usuario_id)
        return {
            "fundador": ctx.fundador,
            "cargos": [c.id for c in ctx.cargos],
            "permissoes": para_nomes(ctx.permissoes),
        }
