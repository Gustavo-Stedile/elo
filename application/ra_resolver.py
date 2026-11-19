from dataclasses import dataclass


@dataclass(frozen=True)
class DadosInstitucionaisRA:
    instituicao: str
    etapa_ensino: int


class ResolvedorRA:
    """Componente temporário que associa todos os RA ao mesmo cadastro."""

    def resolve(self, ra: str | None) -> DadosInstitucionaisRA | None:
        if ra is None:
            return None

        valor = ra.strip()
        if not valor:
            return None

        return DadosInstitucionaisRA(
            instituicao="IFSP",
            etapa_ensino=3,
        )


resolvedor_ra = ResolvedorRA()
