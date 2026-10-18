"""Repositórios em memória para testar a camada de aplicação sem banco.

Reproduzem o contrato dos repositórios reais (incluindo cascatas e
restrições de unicidade). Se SQLAlchemy/bcrypt não estiverem instalados,
módulos vazios são registrados só para permitir o import dos serviços,
que usam os repositórios apenas por duck typing.
"""
import sys
import types
from datetime import datetime, timezone


def _instalar_stubs_se_necessario():
    try:
        import infra.core.repositories  # noqa: F401
        import bcrypt  # noqa: F401
        return
    except ImportError:
        pass

    nomes = [
        "UsuarioRepository", "GremioRepository", "MembroGremioRepository",
        "CargoRepository", "CanalRepository", "PermissaoCanalRepository",
        "MensagemRepository",
    ]
    repos = types.ModuleType("infra.core.repositories")
    for n in nomes:
        setattr(repos, n, type(n, (), {}))
    sys.modules["infra.core.repositories"] = repos

    uow = types.ModuleType("infra.unit_of_work")
    uow.UnitOfWork = type("UnitOfWork", (), {})
    sys.modules["infra.unit_of_work"] = uow

    if "bcrypt" not in sys.modules:
        try:
            import bcrypt  # noqa: F401
        except ImportError:
            sys.modules["bcrypt"] = types.ModuleType("bcrypt")

    for pacote in ("infra", "infra.core"):
        if pacote not in sys.modules:
            m = types.ModuleType(pacote)
            m.__path__ = []
            sys.modules[pacote] = m


_instalar_stubs_se_necessario()

from application import (  # noqa: E402
    AutorizacaoService, CanalService, CargoService,
    GremioService, MembroService, MensagemService,
)
from application.exceptions.canal_exceptions import CanalJaExisteErro  # noqa: E402
from application.exceptions.cargo_exceptions import CargoJaExisteErro  # noqa: E402
from application.exceptions.membro_gremio_exceptions import MembroJaExisteErro  # noqa: E402
from domain.core import (  # noqa: E402
    Canal, Cargo, Gremio, MembroGremio, Mensagem, PermissaoCanal, Usuario,
)


def _copia(obj):
    import copy
    return copy.copy(obj)


class Store:
    def __init__(self):
        self.seq = 0
        self.usuarios, self.gremios, self.membros = {}, {}, {}
        self.cargos, self.atribuicoes = {}, set()   # atribuicoes: (membro_id, cargo_id)
        self.canais, self.sobrescritas, self.mensagens = {}, {}, {}

    def proximo(self):
        self.seq += 1
        return self.seq


class FakeUsuarios:
    def __init__(self, s): self.s = s
    def get_by_id(self, id): return self.s.usuarios.get(id)
    def get_many(self, ids): return {i: self.s.usuarios[i] for i in set(ids) if i in self.s.usuarios}


class FakeGremios:
    def __init__(self, s): self.s = s
    def get_by_id(self, id): return _copia(self.s.gremios.get(id)) if id in self.s.gremios else None
    def create(self, g):
        g = _copia(g); g.id = self.s.proximo(); self.s.gremios[g.id] = g; return _copia(g)
    def listar_por_usuario(self, uid):
        ids = {m.gremio_id for m in self.s.membros.values() if m.usuario_id == uid}
        return [_copia(g) for g in self.s.gremios.values() if g.id in ids]


class FakeMembros:
    def __init__(self, s): self.s = s
    def create(self, m):
        if self.get(m.gremio_id, m.usuario_id):
            raise MembroJaExisteErro()
        m = _copia(m); m.id = self.s.proximo(); self.s.membros[m.id] = m; return _copia(m)
    def get(self, gremio_id, usuario_id):
        for m in self.s.membros.values():
            if m.gremio_id == gremio_id and m.usuario_id == usuario_id:
                return _copia(m)
    def listar_por_gremio(self, gremio_id):
        return [_copia(m) for m in self.s.membros.values() if m.gremio_id == gremio_id]
    def atualizar_permissoes(self, m):
        o = self.s.membros[m.id]
        o.permissoes_permitidas, o.permissoes_negadas = m.permissoes_permitidas, m.permissoes_negadas
        return _copia(o)
    def remover(self, membro_id):
        self.s.membros.pop(membro_id, None)
        self.s.atribuicoes = {a for a in self.s.atribuicoes if a[0] != membro_id}


class FakeCargos:
    def __init__(self, s): self.s = s
    def create(self, c):
        if any(x.gremio_id == c.gremio_id and x.nome == c.nome for x in self.s.cargos.values()):
            raise CargoJaExisteErro()
        c = _copia(c); c.id = self.s.proximo(); self.s.cargos[c.id] = c; return _copia(c)
    def get_by_id(self, id): return _copia(self.s.cargos[id]) if id in self.s.cargos else None
    def get_padrao(self, gremio_id):
        return next((_copia(c) for c in self.s.cargos.values() if c.gremio_id == gremio_id and c.padrao), None)
    def listar_por_gremio(self, gremio_id):
        return sorted((_copia(c) for c in self.s.cargos.values() if c.gremio_id == gremio_id),
                      key=lambda c: (-c.prioridade, c.id))
    def update(self, c):
        self.s.cargos[c.id] = _copia(c); return _copia(c)
    def delete(self, cargo_id):
        self.s.cargos.pop(cargo_id, None)
        self.s.atribuicoes = {a for a in self.s.atribuicoes if a[1] != cargo_id}
        self.s.sobrescritas = {k: v for k, v in self.s.sobrescritas.items() if v.cargo_id != cargo_id}
    def listar_do_membro(self, membro_id):
        return [_copia(self.s.cargos[c]) for (m, c) in self.s.atribuicoes if m == membro_id]
    def listar_atribuicoes_do_gremio(self, gremio_id):
        r = {}
        for (m, c) in self.s.atribuicoes:
            if self.s.membros[m].gremio_id == gremio_id:
                r.setdefault(m, []).append(c)
        return r
    def atribuir(self, membro_id, cargo_id): self.s.atribuicoes.add((membro_id, cargo_id))
    def desatribuir(self, membro_id, cargo_id): self.s.atribuicoes.discard((membro_id, cargo_id))


class FakeCanais:
    def __init__(self, s): self.s = s
    def create(self, c):
        if any(x.gremio_id == c.gremio_id and x.nome == c.nome for x in self.s.canais.values()):
            raise CanalJaExisteErro()
        c = _copia(c); c.id = self.s.proximo(); self.s.canais[c.id] = c; return _copia(c)
    def get_by_id(self, id): return _copia(self.s.canais[id]) if id in self.s.canais else None
    def listar_por_gremio(self, gremio_id):
        return [_copia(c) for c in self.s.canais.values() if c.gremio_id == gremio_id]
    def update(self, c): self.s.canais[c.id] = _copia(c); return _copia(c)
    def delete(self, canal_id):
        self.s.canais.pop(canal_id, None)
        self.s.mensagens = {k: v for k, v in self.s.mensagens.items() if v.canal_id != canal_id}
        self.s.sobrescritas = {k: v for k, v in self.s.sobrescritas.items() if v.canal_id != canal_id}


class FakeSobrescritas:
    def __init__(self, s): self.s = s
    def _achar(self, canal_id, cargo_id=None, usuario_id=None):
        for k, v in self.s.sobrescritas.items():
            if v.canal_id == canal_id and v.cargo_id == cargo_id and v.usuario_id == usuario_id:
                return k
    def listar_por_canal(self, canal_id):
        return [_copia(v) for v in self.s.sobrescritas.values() if v.canal_id == canal_id]
    def listar_por_canais(self, ids):
        return {i: self.listar_por_canal(i) for i in ids}
    def _definir(self, canal_id, permitir, negar, cargo_id=None, usuario_id=None):
        k = self._achar(canal_id, cargo_id, usuario_id)
        if k is None:
            k = self.s.proximo()
            self.s.sobrescritas[k] = PermissaoCanal(k, canal_id, cargo_id=cargo_id, usuario_id=usuario_id)
        self.s.sobrescritas[k].permitir, self.s.sobrescritas[k].negar = permitir, negar
        return _copia(self.s.sobrescritas[k])
    def definir_cargo(self, canal_id, cargo_id, permitir, negar):
        return self._definir(canal_id, permitir, negar, cargo_id=cargo_id)
    def definir_usuario(self, canal_id, usuario_id, permitir, negar):
        return self._definir(canal_id, permitir, negar, usuario_id=usuario_id)
    def remover_cargo(self, canal_id, cargo_id):
        self.s.sobrescritas.pop(self._achar(canal_id, cargo_id=cargo_id), None)
    def remover_usuario(self, canal_id, usuario_id):
        self.s.sobrescritas.pop(self._achar(canal_id, usuario_id=usuario_id), None)
    def remover_do_usuario_no_gremio(self, gremio_id, usuario_id):
        canais = {c.id for c in self.s.canais.values() if c.gremio_id == gremio_id}
        self.s.sobrescritas = {k: v for k, v in self.s.sobrescritas.items()
                               if not (v.usuario_id == usuario_id and v.canal_id in canais)}


class FakeMensagens:
    def __init__(self, s): self.s = s
    def create(self, m):
        m = _copia(m); m.id = self.s.proximo(); self.s.mensagens[m.id] = m; return _copia(m)
    def get_by_id(self, id): return _copia(self.s.mensagens[id]) if id in self.s.mensagens else None
    def listar(self, canal_id, limite, antes_de=None, depois_de=None):
        ms = sorted((m for m in self.s.mensagens.values() if m.canal_id == canal_id), key=lambda m: m.id)
        if depois_de is not None:
            return [_copia(m) for m in ms if m.id > depois_de][:limite]
        if antes_de is not None:
            ms = [m for m in ms if m.id < antes_de]
        return [_copia(m) for m in ms][-limite:]
    def atualizar_conteudo(self, mensagem_id, conteudo, editada_em):
        m = self.s.mensagens[mensagem_id]; m.conteudo, m.editada_em = conteudo, editada_em; return _copia(m)
    def delete(self, mensagem_id): self.s.mensagens.pop(mensagem_id, None)


class FakeUow:
    def commit(self): pass
    def rollback(self): pass


class App:
    """Monta todos os serviços sobre o mesmo repositório em memória."""

    def __init__(self):
        s = self.store = Store()
        usuarios, gremios, membros = FakeUsuarios(s), FakeGremios(s), FakeMembros(s)
        cargos, canais, sobre, msgs = FakeCargos(s), FakeCanais(s), FakeSobrescritas(s), FakeMensagens(s)
        uow = FakeUow()
        self.autorizacao = AutorizacaoService(gremios, membros, cargos, canais, sobre)
        self.gremios = GremioService(gremios, membros, cargos, canais, usuarios, self.autorizacao, uow)
        self.membros = MembroService(gremios, membros, cargos, sobre, usuarios, self.autorizacao, uow)
        self.cargos = CargoService(cargos, self.autorizacao, uow)
        self.canais = CanalService(canais, sobre, cargos, membros, self.autorizacao, uow)
        self.mensagens = MensagemService(msgs, usuarios, self.autorizacao, uow)

    def novo_usuario(self, nome):
        uid = self.store.proximo()
        self.store.usuarios[uid] = Usuario(uid, nome, f"cpf{uid}", f"{nome}@x.com", None, "hash")
        return uid
