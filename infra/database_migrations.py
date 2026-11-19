from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection


_GREMIO_UNIQUE_COLUMNS = ["instituicao", "etapa_ensino"]
_GREMIO_UNIQUE_INDEX = "uq_gremio_instituicao_etapa"


def garantir_unicidade_gremio_instituicao_etapa(connection: Connection) -> None:
    """Aplica em bancos SQLite existentes a unicidade definida no modelo."""
    inspector = inspect(connection)
    constraints = inspector.get_unique_constraints("gremios")
    indexes = inspector.get_indexes("gremios")

    restricao_existente = any(
        constraint.get("column_names") == _GREMIO_UNIQUE_COLUMNS
        for constraint in constraints
    )
    indice_existente = any(
        index.get("unique")
        and index.get("column_names") == _GREMIO_UNIQUE_COLUMNS
        for index in indexes
    )
    if restricao_existente or indice_existente:
        return

    duplicados = connection.execute(text(
        """
        SELECT instituicao, etapa_ensino, COUNT(*) AS quantidade
        FROM gremios
        GROUP BY instituicao, etapa_ensino
        HAVING COUNT(*) > 1
        """
    )).all()
    if duplicados:
        pares = ", ".join(
            f"({instituicao!r}, {etapa!r}) x{quantidade}"
            for instituicao, etapa, quantidade in duplicados[:5]
        )
        raise RuntimeError(
            "Não foi possível aplicar a unicidade de grêmio por instituição "
            f"e etapa: existem combinações duplicadas em gremios: {pares}. "
            "Resolva os duplicados e reinicie a aplicação."
        )

    connection.execute(text(
        f'CREATE UNIQUE INDEX "{_GREMIO_UNIQUE_INDEX}" '
        'ON gremios (instituicao, etapa_ensino)'
    ))
