import bcrypt

from application.exceptions.usuario_exceptions import (
    UsuarioNaoExisteErro,
)
from domain.core import Usuario
from infra.core.repositories import UsuarioRepository

class UsuarioService:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

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
        
        return {
            "id": res.id,
            "nome": res.nome,
            "cpf": res.cpf,
            "email": res.email, 
            "ra": res.ra, 
        }

    def buscar_por_id(self, id: int) -> Usuario:
        res = self.usuario_repository.get_by_id(id)

        if not res:
            raise UsuarioNaoExisteErro()
        
        return {
            "id": res.id,
            "nome": res.nome,
            "cpf": res.cpf,
            "email": res.email, 
            "ra": res.ra, 
        }