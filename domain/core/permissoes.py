"""Catálogo de permissões do sistema.

As permissões são armazenadas como bitmask (inteiro). Isso permite combinar,
negar e comparar conjuntos de permissões com operações bit a bit, e guardar
tudo em uma única coluna inteira.

Existem dois escopos:

* Escopo de CANAL: valem no grêmio inteiro (via cargos) e podem ser
  sobrescritas em cada canal, por cargo ou por usuário.
* Escopo de GRÊMIO: só fazem sentido no grêmio e não podem ser sobrescritas
  em canais.
"""
from enum import IntFlag
from functools import reduce
from operator import or_
from typing import Iterable


class Permissao(IntFlag):
    # --- Escopo de canal ---
    VER_CANAL = 1 << 0
    LER_HISTORICO = 1 << 1
    ENVIAR_MENSAGENS = 1 << 2
    GERENCIAR_MENSAGENS = 1 << 3  # apagar mensagens de outros usuários

    # --- Escopo de grêmio ---
    GERENCIAR_CANAIS = 1 << 8     # criar/editar/excluir canais e suas permissões
    GERENCIAR_CARGOS = 1 << 9     # criar/editar cargos, atribuí-los e dar permissões a usuários
    GERENCIAR_MEMBROS = 1 << 10   # adicionar/remover membros
    GERENCIAR_GREMIO = 1 << 11    # editar dados do grêmio

    # Ignora todas as verificações e sobrescritas de canal.
    ADMINISTRADOR = 1 << 15


NENHUMA = 0
TODAS = reduce(or_, (int(p) for p in Permissao), 0)

PERMISSOES_DE_CANAL = int(
    Permissao.VER_CANAL
    | Permissao.LER_HISTORICO
    | Permissao.ENVIAR_MENSAGENS
    | Permissao.GERENCIAR_MENSAGENS
)

# Permissões que todo membro recebe pelo cargo padrão de um grêmio novo.
PERMISSOES_PADRAO_MEMBRO = int(
    Permissao.VER_CANAL | Permissao.LER_HISTORICO | Permissao.ENVIAR_MENSAGENS
)


def nomes_validos() -> list[str]:
    return [p.name for p in Permissao]


def para_nomes(valor: int) -> list[str]:
    """Converte um bitmask na lista de nomes das permissões ativas."""
    return [p.name for p in Permissao if valor & int(p)]


def de_nomes(nomes: Iterable[str]) -> int:
    """Converte nomes de permissões em bitmask. Levanta ValueError se algum não existir."""
    valor = 0
    for nome in nomes:
        try:
            valor |= int(Permissao[nome])
        except KeyError:
            raise ValueError(f"Permissão desconhecida: {nome}")
    return valor


def e_valido(valor: int, mascara: int = TODAS) -> bool:
    """True se o bitmask só contém bits permitidos pela máscara."""
    return valor >= 0 and (valor & ~mascara) == 0
