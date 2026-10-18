from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session
from domain.core import Usuario

from application.exceptions.usuario_exceptions import (
    CPFJaCadastradoErro, EmailJaCadastradoErro, RAJaCadastradoErro,
    UsuarioNaoExisteErro
)

from infra.core.orm import UsuarioORM
from infra.core.mappers.usuario_mappers import (
    usuario_to_domain, usuario_to_orm
)

class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Usuario | None:
        orm_user = self.db.get(UsuarioORM, id)
        return usuario_to_domain(orm_user)

    def get_many(self, ids: list[int]) -> dict[int, Usuario]:
        """Busca vários usuários de uma vez. Retorna um mapa id -> Usuario."""
        if not ids:
            return {}
        orm_users = self.db.query(UsuarioORM).filter(UsuarioORM.id.in_(set(ids))).all()
        return {u.id: usuario_to_domain(u) for u in orm_users}

    def get_by_email(self, email: str) -> Usuario | None:
        orm_user = self.db.query(UsuarioORM).filter(UsuarioORM.email == email).first()
        return usuario_to_domain(orm_user)

    def get_by_cpf(self, cpf: str) -> Usuario | None:
        orm_user = self.db.query(UsuarioORM).filter(UsuarioORM.cpf == cpf).first()
        return usuario_to_domain(orm_user)

    def get_by_ra(self, ra: str) -> Usuario | None:
        orm_user = self.db.query(UsuarioORM).filter(UsuarioORM.ra == ra).first()
        return usuario_to_domain(orm_user)

    def create(self, usuario: Usuario) -> Usuario:
        """Cria um novo usuário na base de dados."""
        try:
            orm_user = usuario_to_orm(usuario)
            self.db.add(orm_user)
            self.db.commit()
            self.db.refresh(orm_user)
            return usuario_to_domain(orm_user)
            
        except IntegrityError as e:
            self.db.rollback()
            self._tratar_erro_integridade(e)

    def update(self, usuario: Usuario) -> Usuario:
        """Atualiza um usuário existente na base de dados."""
        try:
            orm_user = self.db.get(UsuarioORM, usuario.id)
            if not orm_user:
                raise UsuarioNaoExisteErro()

            orm_user.nome = usuario.nome
            orm_user.cpf = usuario.cpf
            orm_user.email = usuario.email
            orm_user.ra = usuario.ra
            orm_user.senha = usuario.senha

            self.db.commit()
            self.db.refresh(orm_user)
            return usuario_to_domain(orm_user)
            
        except IntegrityError as e:
            self.db.rollback()
            self._tratar_erro_integridade(e)

    def _tratar_erro_integridade(self, e: IntegrityError):
        """Valida se o IntegrityError é uma violação de Unique Constraint e dispara a exceção correta."""
        erro_msg = str(e.orig).lower()
        
        # Garante que o erro é estritamente de restrição única (SQLite ou Postgres)
        is_unique_violation = "unique" in erro_msg or "duplicate" in erro_msg or "23505" in erro_msg
        
        if is_unique_violation:
            if "email" in erro_msg:
                raise EmailJaCadastradoErro()
            elif "cpf" in erro_msg:
                raise CPFJaCadastradoErro()
            elif "ra" in erro_msg:
                raise RAJaCadastradoErro()
                
        raise e