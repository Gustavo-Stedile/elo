import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from infra.core.orm import (
    CargoORM,
    ConcessaoPermissaoORM,
    GremioORM,
    MembroCargoORM,
    MembroGremioORM,
    PermissaoObjetoORM,
    UsuarioORM,
)
from infra.core.repositories.permissao_objeto_repo import PermissaoObjetoRepository
from infra.database import Base


class PermissaoObjetoRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

        usuarios = [
            UsuarioORM(
                nome=f"usuario-{n}",
                cpf=f"000.000.000-0{n}",
                email=f"usuario-{n}@example.com",
                senha="hash",
            )
            for n in (1, 2)
        ]
        self.db.add_all(usuarios)
        self.db.flush()

        gremios = [
            GremioORM(
                nome=f"Gremio-{n}",
                instituicao=f"Instituicao-{n}",
                etapa_ensino=3,
                legitimado=False,
                fundador_id=usuarios[n - 1].id,
            )
            for n in (1, 2)
        ]
        self.db.add_all(gremios)
        self.db.flush()

        self.membro_1 = MembroGremioORM(
            usuario_id=usuarios[0].id, gremio_id=gremios[0].id
        )
        self.membro_2 = MembroGremioORM(
            usuario_id=usuarios[1].id, gremio_id=gremios[1].id
        )
        self.admin_1 = CargoORM(
            gremio_id=gremios[0].id,
            nome="Administrador",
            prioridade=100,
            permissoes=1 << 15,
        )
        self.permissao_1 = PermissaoObjetoORM(
            gremio_id=gremios[0].id,
            recurso_tipo="GREMIO",
            recurso_id=gremios[0].id,
            codigo="GREMIO_EDITAR_NOME",
            nome="Editar nome",
        )
        self.permissao_2 = PermissaoObjetoORM(
            gremio_id=gremios[1].id,
            recurso_tipo="GREMIO",
            recurso_id=gremios[1].id,
            codigo="GREMIO_EDITAR_NOME",
            nome="Editar nome",
        )
        self.db.add_all(
            [
                self.membro_1,
                self.membro_2,
                self.admin_1,
                self.permissao_1,
                self.permissao_2,
            ]
        )
        self.db.flush()
        self.db.add_all(
            [
                MembroCargoORM(
                    membro_id=self.membro_1.id, cargo_id=self.admin_1.id
                ),
                # Deliberately malformed cross-guild assignment and grant.
                MembroCargoORM(
                    membro_id=self.membro_2.id, cargo_id=self.admin_1.id
                ),
                ConcessaoPermissaoORM(
                    permissao_id=self.permissao_2.id,
                    membro_id=self.membro_1.id,
                ),
            ]
        )
        self.db.commit()
        self.repository = PermissaoObjetoRepository(self.db)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_grants_and_administrator_bypass_are_scoped_to_guild(self):
        self.assertTrue(
            self.repository.membro_possui(
                self.membro_1.id, self.permissao_1.id
            )
        )
        self.assertFalse(
            self.repository.membro_possui(
                self.membro_2.id, self.permissao_2.id
            )
        )
        self.assertNotIn(
            self.permissao_2.id,
            self.repository.listar_ids_concedidos_ao_membro(self.membro_1.id),
        )

        self.repository.conceder_a_membro(
            self.permissao_2.id, self.membro_2.id
        )
        self.assertTrue(
            self.repository.membro_possui(
                self.membro_2.id, self.permissao_2.id
            )
        )


if __name__ == "__main__":
    unittest.main()
