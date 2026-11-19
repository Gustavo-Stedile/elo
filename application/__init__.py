from importlib import import_module


_EXPORTS = {
    "AutorizacaoService": (".autorizacao_service", "AutorizacaoService"),
    "GremioService": (".gremio_service", "GremioService"),
    "UsuarioService": (".usuario_service", "UsuarioService"),
    "AuthService": (".auth_service", "AuthService"),
    "MembroService": (".membro_service", "MembroService"),
    "CargoService": (".cargo_service", "CargoService"),
    "CanalService": (".canal_service", "CanalService"),
    "MensagemService": (".mensagem_service", "MensagemService"),
    "EnqueteService": (".enquete_comunicado_service", "EnqueteService"),
    "ComunicadoService": (".enquete_comunicado_service", "ComunicadoService"),
    "PermissaoRelacionalService": (
        ".permissao_relacional_service",
        "PermissaoRelacionalService",
    ),
    "PermissaoGlobalService": (
        ".permissao_global_service",
        "PermissaoGlobalService",
    ),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = _EXPORTS[name]
    attribute = getattr(import_module(module_name, __name__), attribute_name)
    globals()[name] = attribute
    return attribute
