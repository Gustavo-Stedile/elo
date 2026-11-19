import bcrypt

from application.exceptions.usuario_exceptions import (
    UsuarioNaoExisteErro,
)
from domain.core import Usuario
from domain.core import MembroGremio
from application.ra_resolver import resolvedor_ra
from infra.core.repositories import (
    GremioRepository,
    MembroGremioRepository,
    UsuarioRepository,
)
from infra.unit_of_work import UnitOfWork

class UsuarioService:
    def __init__(
        self,
        usuario_repository: UsuarioRepository,
        gremio_repository: GremioRepository | None = None,
        membro_gremio_repository: MembroGremioRepository | None = None,
        uow: UnitOfWork | None = None,
    ):
        self.usuario_repository = usuario_repository
        self.gremio_repository = gremio_repository
        self.membro_gremio_repository = membro_gremio_repository
        self.uow = uow

    def criar_usuario(
        self, nome: str, cpf: str, email: str, 
        ra: str | None = None, senha: str = ""
    ) -> dict:
        """Regista um novo usuário aplicando regras de negócio se necessário."""

        # 2. Criptografa a senha com bcrypt
        senha_bytes = senha.encode("utf-8")
        salt = bcrypt.gensalt()
        senha_hash = bcrypt.hashpw(senha_bytes, salt).decode("utf-8")

        novo_usuario = Usuario(
            id=None,
            nome=nome,
            cpf=cpf,
            email=email,
            ra=ra,
            senha=senha_hash,  # Dica: em produção, aplique hash na senha aqui ou no domínio
        )

        res = self.usuario_repository.create(novo_usuario)

        dados_ra = None
        if ra:
            dados_ra = resolvedor_ra.resolve(ra)
            if (
                dados_ra
                and self.gremio_repository
                and self.membro_gremio_repository
                and self.uow
            ):
                gremio = self.gremio_repository.get_by_instituicao_etapa(
                    dados_ra.instituicao,
                    dados_ra.etapa_ensino,
                )
                if gremio:
                    self.membro_gremio_repository.create(MembroGremio(
                        id=None,
                        usuario_id=res.id,
                        gremio_id=gremio.id,
                    ))
        if self.uow:
            self.uow.commit()
        
        return {
            "id": res.id,
            "nome": res.nome,
            "cpf": res.cpf,
            "email": res.email, 
            "ra": res.ra, 
            "instituicao": dados_ra.instituicao if dados_ra else None,
            "etapa_ensino": dados_ra.etapa_ensino if dados_ra else None,
        }

    def buscar_por_id(self, id: int) -> Usuario:
        res = self.usuario_repository.get_by_id(id)

        if not res:
            raise UsuarioNaoExisteErro()

        dados_ra = resolvedor_ra.resolve(res.ra) if res.ra else None
        
        return {
            "id": res.id,
            "nome": res.nome,
            "cpf": res.cpf,
            "email": res.email, 
            "ra": res.ra, 
            "instituicao": dados_ra.instituicao if dados_ra else None,
            "etapa_ensino": dados_ra.etapa_ensino if dados_ra else None,
        }