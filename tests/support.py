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
        "EnqueteRepository", "ComunicadoRepository", "PermissaoObjetoRepository",
        "PermissaoGlobalRepository",
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
    GremioService, MembroService, MensagemService, PermissaoRelacionalService,
    PermissaoGlobalService,
)
from application.exceptions.canal_exceptions import CanalJaExisteErro  # noqa: E402
from application.exceptions.cargo_exceptions import CargoJaExisteErro  # noqa: E402
from application.exceptions.membro_gremio_exceptions import MembroJaExisteErro  # noqa: E402
from domain.core import (  # noqa: E402
    Canal, Cargo, ConcessaoPermissao, Gremio, MembroGremio, Mensagem,
    PermissaoCanal, PermissaoObjeto, PermissaoGlobal, Usuario,
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
        self.permissoes_objeto, self.concessoes_permissao = {}, set()
        self.permissoes_globais, self.concessoes_globais = {}, set()

    def proximo(self):
        self.seq += 1
        return self.seq


class FakeUsuarios:
    def __init__(self, s): self.s = s
    def get_by_id(self, id): return self.s.usuarios.get(id)
    def get_many(self, ids): return {i: self.s.usuarios[i] for i in set(ids) if i in self.s.usuarios}
    def listar_com_ra(self):
        return [u for u in self.s.usuarios.values() if u.ra and u.ra.strip()]


class FakeGremios:
    def __init__(self, s): self.s = s
    def get_by_id(self, id): return _copia(self.s.gremios.get(id)) if id in self.s.gremios else None
    def get_by_instituicao_etapa(self, instituicao, etapa_ensino):
        return next(
            (_copia(g) for g in self.s.gremios.values()
             if g.instituicao == instituicao and g.etapa_ensino == etapa_ensino),
            None,
        )
    def create(self, g):
        g = _copia(g); g.id = self.s.proximo(); self.s.gremios[g.id] = g; return _copia(g)
    def update(self, g):
        self.s.gremios[g.id] = _copia(g)
        return _copia(g)
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
    def contar_ocupantes(self, cargo_id):
        return sum(1 for _, atribuido in self.s.atribuicoes if atribuido == cargo_id)


class FakePermissaoObjetoRepository:
    def __init__(self, s): self.s = s
    def obter_ou_criar(self, gremio_id, recurso_tipo, recurso_id, codigo, nome, descricao=None):
        key = (recurso_tipo, recurso_id, codigo)
        if key not in self.s.permissoes_objeto:
            p = PermissaoObjeto(self.s.proximo(), gremio_id, recurso_tipo, recurso_id, codigo, nome, descricao)
            self.s.permissoes_objeto[key] = p
        return _copia(self.s.permissoes_objeto[key])
    def obter(self, permissao_id):
        return next((_copia(p) for p in self.s.permissoes_objeto.values() if p.id == permissao_id), None)
    def obter_por_recurso(self, gremio_id, recurso_tipo, recurso_id, codigo):
        p = self.s.permissoes_objeto.get((recurso_tipo, recurso_id, codigo))
        return _copia(p) if p and p.gremio_id == gremio_id else None
    def listar_do_gremio(self, gremio_id):
        return [_copia(p) for p in self.s.permissoes_objeto.values() if p.gremio_id == gremio_id]
    def listar_do_recurso(self, gremio_id, recurso_tipo, recurso_id):
        return [
            _copia(p) for p in self.s.permissoes_objeto.values()
            if p.gremio_id == gremio_id
            and p.recurso_tipo == recurso_tipo
            and p.recurso_id == recurso_id
        ]
    def listar_do_gremio_por_ids(self, ids):
        return [_copia(p) for p in self.s.permissoes_objeto.values() if p.id in ids]
    def listar_do_cargo(self, cargo_id):
        ids = {p for (p, cargo, membro) in self.s.concessoes_permissao if cargo == cargo_id and membro is None}
        return self.listar_do_gremio_por_ids(ids)
    def listar_ids_concedidos_ao_membro(self, membro_id):
        ids = {p for (p, cargo, membro) in self.s.concessoes_permissao if membro == membro_id and cargo is None}
        cargos = {c for (m, c) in self.s.atribuicoes if m == membro_id}
        membro = self.s.membros.get(membro_id)
        if membro:
            cargos.update(
                c.id for c in self.s.cargos.values()
                if c.gremio_id == membro.gremio_id and c.padrao
            )
        ids.update(p for (p, cargo, membro) in self.s.concessoes_permissao if cargo in cargos and membro is None)
        return {
            p.id for p in self.s.permissoes_objeto.values()
            if p.id in ids and membro and p.gremio_id == membro.gremio_id
        }
    def membro_possui(self, membro_id, permissao_id):
        permissao = next(
            (p for p in self.s.permissoes_objeto.values() if p.id == permissao_id),
            None,
        )
        membro = self.s.membros.get(membro_id)
        if not membro or not permissao or permissao.gremio_id != membro.gremio_id:
            return False
        if permissao_id in self.listar_ids_concedidos_ao_membro(membro_id):
            return True
        cargo_ids = {c for (m, c) in self.s.atribuicoes if m == membro_id}
        cargo_ids.update(
            c.id for c in self.s.cargos.values()
            if c.gremio_id == membro.gremio_id and c.padrao
        )
        return any(
            self.s.cargos[cid].gremio_id == membro.gremio_id
            and self.s.cargos[cid].permissoes & (1 << 15)
            for cid in cargo_ids
        )
    def conceder_a_cargo(self, permissao_id, cargo_id):
        key = (permissao_id, cargo_id, None)
        self.s.concessoes_permissao.add(key)
        return ConcessaoPermissao(0, permissao_id, cargo_id=cargo_id)
    def conceder_a_membro(self, permissao_id, membro_id):
        key = (permissao_id, None, membro_id)
        self.s.concessoes_permissao.add(key)
        return ConcessaoPermissao(0, permissao_id, membro_id=membro_id)
    def revogar_de_cargo(self, permissao_id, cargo_id):
        self.s.concessoes_permissao.discard((permissao_id, cargo_id, None))
    def revogar_de_membro(self, permissao_id, membro_id):
        self.s.concessoes_permissao.discard((permissao_id, None, membro_id))
    def excluir_do_recurso(self, gremio_id, recurso_tipo, recurso_id):
        ids = {
            p.id for p in self.s.permissoes_objeto.values()
            if p.gremio_id == gremio_id
            and p.recurso_tipo == recurso_tipo
            and p.recurso_id == recurso_id
        }
        self.s.permissoes_objeto = {
            key: p for key, p in self.s.permissoes_objeto.items()
            if p.id not in ids
        }
        self.s.concessoes_permissao = {
            concessao for concessao in self.s.concessoes_permissao
            if concessao[0] not in ids
        }


class FakePermissaoGlobalRepository:
    def __init__(self, s): self.s = s
    def obter_ou_criar(self, codigo, nome, descricao=None):
        if codigo not in self.s.permissoes_globais:
            p = PermissaoGlobal(
                self.s.proximo(), codigo, nome, descricao
            )
            self.s.permissoes_globais[codigo] = p
        return _copia(self.s.permissoes_globais[codigo])
    def obter_por_codigo(self, codigo):
        p = self.s.permissoes_globais.get(codigo)
        return _copia(p) if p else None
    def usuario_possui(self, usuario_id, permissao_id):
        return (permissao_id, usuario_id) in self.s.concessoes_globais
    def conceder_a_usuario(self, permissao_id, usuario_id):
        self.s.concessoes_globais.add((permissao_id, usuario_id))


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
        self.permissoes_relacionais = PermissaoRelacionalService(
            FakePermissaoObjetoRepository(s)
        )
        self.permissoes_globais = PermissaoGlobalService(
            FakePermissaoGlobalRepository(s)
        )
        self.permissoes_globais.criar_catalogo()
        self.autorizacao = AutorizacaoService(
            gremios, membros, cargos, canais, sobre, self.permissoes_relacionais
        )
        self.gremios = GremioService(
            gremios, membros, cargos, canais, usuarios, self.autorizacao, uow,
            self.permissoes_relacionais,
            self.permissoes_globais,
        )
        self.membros = MembroService(
            gremios, membros, cargos, sobre, usuarios, self.autorizacao, uow,
            self.permissoes_relacionais,
        )
        self.cargos = CargoService(
            cargos, self.autorizacao, uow, self.permissoes_relacionais
        )
        self.canais = CanalService(
            canais, sobre, cargos, membros, self.autorizacao, uow,
            self.permissoes_relacionais,
        )
        self.mensagens = MensagemService(msgs, usuarios, self.autorizacao, uow)

    def novo_usuario(self, nome):
        uid = self.store.proximo()
        self.store.usuarios[uid] = Usuario(uid, nome, f"cpf{uid}", f"{nome}@x.com", f"RA{uid}", "hash")
        return uid
