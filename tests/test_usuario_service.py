import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from application.usuario_service import UsuarioService


class UsuarioServiceTest(unittest.TestCase):
    @patch("application.usuario_service.bcrypt")
    def test_confirma_cadastro_com_ra_sem_gremio_correspondente(self, bcrypt):
        bcrypt.hashpw.return_value = b"hash"
        usuario = SimpleNamespace(
            id=1,
            nome="Ana Silva",
            cpf="12345678901",
            email="ana@example.com",
            ra="202612345",
        )
        usuarios = Mock()
        usuarios.create.return_value = usuario
        gremios = Mock()
        gremios.get_by_instituicao_etapa.return_value = None
        membros = Mock()
        uow = Mock()
        service = UsuarioService(usuarios, gremios, membros, uow)

        resultado = service.criar_usuario(
            nome=usuario.nome,
            cpf=usuario.cpf,
            email=usuario.email,
            ra=usuario.ra,
            senha="senha-segura",
        )

        self.assertEqual(resultado["id"], usuario.id)
        gremios.get_by_instituicao_etapa.assert_called_once_with("IFSP", 3)
        membros.create.assert_not_called()
        uow.commit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
