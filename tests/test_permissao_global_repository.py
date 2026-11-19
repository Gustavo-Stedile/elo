import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from application.exceptions.autorizacao_exceptions import SemPermissaoErro
from application.permissao_global_service import PermissaoGlobalService
from infra.core.orm import UsuarioORM
from infra.core.repositories.permissao_global_repo import (
    PermissaoGlobalRepository,
)
from infra.database import Base


class PermissaoGlobalRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.usuario = UsuarioORM(
            nome="Sistema",
            cpf="000.000.000-01",
            email="sistema@example.com",
            senha="hash",
        )
        self.db.add(self.usuario)
        self.db.commit()
        self.repository = PermissaoGlobalRepository(self.db)
        self.service = PermissaoGlobalService(self.repository)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_catalogo_global_existe_mas_nao_concede_permissao(self):
        permissao, = self.service.criar_catalogo()

        self.assertEqual(permissao.codigo, "LEGITIMAR_GREMIO")
        self.assertFalse(
            self.repository.usuario_possui(self.usuario.id, permissao.id)
        )

        with self.assertRaises(SemPermissaoErro):
            self.service.exigir(self.usuario.id, "LEGITIMAR_GREMIO")

    def test_usuario_com_concessao_global_efetiva_acesso(self):
        permissao, = self.service.criar_catalogo()
        self.repository.conceder_a_usuario(permissao.id, self.usuario.id)

        self.service.exigir(self.usuario.id, "LEGITIMAR_GREMIO")


if __name__ == "__main__":
    unittest.main()
