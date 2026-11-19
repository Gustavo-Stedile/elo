import unittest

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from infra.database_migrations import garantir_unicidade_gremio_instituicao_etapa


class GremioUniqueMigrationTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        with self.engine.begin() as connection:
            connection.execute(text(
                """
                CREATE TABLE gremios (
                    id INTEGER PRIMARY KEY,
                    instituicao VARCHAR(150) NOT NULL,
                    etapa_ensino INTEGER NOT NULL
                )
                """
            ))

    def tearDown(self):
        self.engine.dispose()

    def test_cria_indice_unico_em_tabela_existente(self):
        with self.engine.begin() as connection:
            garantir_unicidade_gremio_instituicao_etapa(connection)
            indexes = inspect(connection).get_indexes("gremios")
            self.assertTrue(any(
                index["name"] == "uq_gremio_instituicao_etapa"
                and index["unique"]
                and index["column_names"] == ["instituicao", "etapa_ensino"]
                for index in indexes
            ))
            connection.execute(text(
                "INSERT INTO gremios (instituicao, etapa_ensino) VALUES ('IFSP', 3)"
            ))
            with self.assertRaises(IntegrityError):
                connection.execute(text(
                    "INSERT INTO gremios (instituicao, etapa_ensino) VALUES ('IFSP', 3)"
                ))

    def test_informa_duplicados_preexistentes_sem_apaga_los(self):
        with self.engine.begin() as connection:
            connection.execute(text(
                """
                INSERT INTO gremios (instituicao, etapa_ensino)
                VALUES ('IFSP', 3), ('IFSP', 3)
                """
            ))
            with self.assertRaisesRegex(RuntimeError, "combinações duplicadas"):
                garantir_unicidade_gremio_instituicao_etapa(connection)
            self.assertEqual(
                connection.execute(text("SELECT COUNT(*) FROM gremios")).scalar_one(),
                2,
            )

    def test_migracao_pode_ser_executada_mais_de_uma_vez(self):
        with self.engine.begin() as connection:
            garantir_unicidade_gremio_instituicao_etapa(connection)
            garantir_unicidade_gremio_instituicao_etapa(connection)


if __name__ == "__main__":
    unittest.main()
