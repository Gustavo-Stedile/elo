"""Cálculo de permissões efetivas.

Funções puras (sem acesso a banco) para que as regras de autorização possam
ser testadas isoladamente.

Ordem de resolução, no estilo Discord:

Grêmio
    1. O fundador tem todas as permissões.
    2. Base = permissões do cargo padrão (todos os membros) + de todos os
       cargos do membro.
    3. Se a base contém ADMINISTRADOR, o membro tem todas as permissões.
    4. Sobrescritas do usuário no grêmio: remove as negadas e depois soma as
       permitidas.

Canal (parte das permissões do grêmio)
    1. ADMINISTRADOR ignora sobrescritas.
    2. Sobrescrita do cargo padrão.
    3. Sobrescritas dos cargos do membro (negações somadas, depois permissões
       somadas: se um cargo permite, vale).
    4. Sobrescrita do próprio usuário (a mais específica, vence as demais).
    5. Sem VER_CANAL, nenhuma outra permissão de canal vale.
"""
from typing import Iterable, Optional

from domain.core.cargo import Cargo
from domain.core.permissao_canal import PermissaoCanal
from domain.core.permissoes import (
    PERMISSOES_DE_CANAL,
    TODAS,
    Permissao,
)

_ADMIN = int(Permissao.ADMINISTRADOR)
_VER_CANAL = int(Permissao.VER_CANAL)


def _aplicar(base: int, permitir: int, negar: int) -> int:
    return (base & ~negar) | permitir


def calcular_permissoes_gremio(
    *,
    fundador: bool,
    cargo_padrao: Optional[Cargo],
    cargos: Iterable[Cargo],
    permitir_usuario: int = 0,
    negar_usuario: int = 0,
) -> int:
    if fundador:
        return TODAS

    base = cargo_padrao.permissoes if cargo_padrao else 0
    for cargo in cargos:
        base |= cargo.permissoes

    if base & _ADMIN:
        return TODAS

    base = _aplicar(base, permitir_usuario, negar_usuario)

    if base & _ADMIN:
        return TODAS

    return base & TODAS


def calcular_permissoes_canal(
    permissoes_gremio: int,
    *,
    ow_padrao: Optional[PermissaoCanal] = None,
    ow_cargos: Iterable[PermissaoCanal] = (),
    ow_usuario: Optional[PermissaoCanal] = None,
) -> int:
    if permissoes_gremio & _ADMIN:
        return TODAS

    permissoes = permissoes_gremio

    if ow_padrao:
        permissoes = _aplicar(permissoes, ow_padrao.permitir, ow_padrao.negar)

    permitir_cargos = 0
    negar_cargos = 0
    for ow in ow_cargos:
        permitir_cargos |= ow.permitir
        negar_cargos |= ow.negar
    permissoes = _aplicar(permissoes, permitir_cargos, negar_cargos)

    if ow_usuario:
        permissoes = _aplicar(permissoes, ow_usuario.permitir, ow_usuario.negar)

    if not permissoes & _VER_CANAL:
        permissoes &= ~PERMISSOES_DE_CANAL

    return permissoes & TODAS
