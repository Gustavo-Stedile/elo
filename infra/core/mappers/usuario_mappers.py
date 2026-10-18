from domain.core import Usuario
from infra.core.orm import UsuarioORM

def usuario_to_domain(orm: UsuarioORM | None) -> Usuario | None:
    if not orm:
        return None
    
    return Usuario(
        id=orm.id,
        nome=orm.nome,
        cpf=orm.cpf,
        email=orm.email,
        ra=orm.ra,
        senha=orm.senha,
    )

def usuario_to_orm(domain: Usuario) -> UsuarioORM:
    return UsuarioORM(
        id=domain.id,
        nome=domain.nome,
        cpf=domain.cpf,
        email=domain.email,
        ra=domain.ra,
        senha=domain.senha,
    )