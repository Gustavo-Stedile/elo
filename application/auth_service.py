import bcrypt
from domain.core import Usuario
from infra.core.repositories import UsuarioRepository

from application.exceptions.auth_exceptions import CredenciaisInvalidasErro

class AuthService:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    def autenticar(self, email: str, senha_fornecida: str) -> Usuario:
        """Valida as credenciais e retorna o usuário se tudo estiver correto."""
        
        usuario = self.usuario_repository.get_by_email(email)

        if not usuario:
            raise CredenciaisInvalidasErro()

        senha_valida = bcrypt.checkpw(
            senha_fornecida.encode('utf-8'), 
            usuario.senha.encode('utf-8')
        )
        
        if not senha_valida:
            raise CredenciaisInvalidasErro()

        return usuario.id