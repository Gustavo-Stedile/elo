"""Teste ponta a ponta via HTTP (FastAPI + SQLAlchemy + SQLite temporário).

Requer: pip install pytest httpx   (além das dependências do projeto)
Rodar na raiz do projeto:  python -m unittest tests.test_api_e2e -v
É ignorado automaticamente se fastapi/httpx não estiverem instalados.
"""
import importlib.util
import os
import tempfile
import unittest

_DEPS = all(importlib.util.find_spec(m) for m in ("fastapi", "httpx", "sqlalchemy", "bcrypt"))


@unittest.skipUnless(_DEPS, "fastapi/httpx/sqlalchemy/bcrypt não instalados")
class FluxoCompletoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        os.environ["ELO_DATABASE_URL"] = f"sqlite:///{cls._tmp.name}/teste.db"
        os.environ["ELO_RESET_DB"] = "1"

        from fastapi.testclient import TestClient
        import main  # cria as tabelas no banco temporário

        cls.client = TestClient(main.app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls._tmp.cleanup()

    # ---- helpers ----
    def _cadastrar(self, nome, n):
        r = self.client.post("/usuario/", json={
            "nome": nome, "senha": "SenhaSegura123",
            "cpf": f"0000000000{n}", "email": f"{nome}@exemplo.com",
        })
        self.assertEqual(r.status_code, 201, r.text)
        uid = r.json()["usuario"]["id"]
        r = self.client.post("/auth/", json={"email": f"{nome}@exemplo.com", "senha": "SenhaSegura123"})
        self.assertEqual(r.status_code, 200, r.text)
        return uid, {"Authorization": f"Bearer {r.json()['access_token']}"}

    def test_fluxo(self):
        c = self.client
        fund_id, fund = self._cadastrar("fundador", 1)
        ana_id, ana = self._cadastrar("ana", 2)
        _, fora = self._cadastrar("forasteiro", 3)

        # grêmio + estrutura inicial
        r = c.post("/gremio/", json={"nome_gremio": "Grêmio Teste"}, headers=fund)
        self.assertEqual(r.status_code, 201, r.text)
        g = r.json()["gremio"]["id"]

        canais = c.get(f"/gremio/{g}/canais/", headers=fund).json()
        self.assertEqual([x["nome"] for x in canais], ["geral"])
        geral = canais[0]["id"]

        # forasteiro não vê nada; ana ainda não é membro
        self.assertEqual(c.get(f"/canal/{geral}/mensagens/", headers=fora).status_code, 404)
        self.assertEqual(c.get(f"/gremio/{g}/canais/", headers=ana).status_code, 403)

        # fundador adiciona ana; ana conversa
        r = c.post(f"/gremio/{g}/membros/", json={"usuario_id": ana_id}, headers=fund)
        self.assertEqual(r.status_code, 201, r.text)
        r = c.post(f"/canal/{geral}/mensagens/", json={"conteudo": "olá!"}, headers=ana)
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["autor_nome"], "ana")
        msgs = c.get(f"/canal/{geral}/mensagens/", headers=fund).json()
        self.assertEqual([m["conteudo"] for m in msgs], ["olá!"])

        # ana não administra nada
        r = c.post(f"/gremio/{g}/canais/", json={"nome": "x"}, headers=ana)
        self.assertEqual(r.status_code, 403)

        # silenciar ana no canal (permissão por usuário no canal)
        url = f"/canal/{geral}/permissoes/usuarios/{ana_id}"
        r = c.put(url, json={"negar": ["ENVIAR_MENSAGENS"]}, headers=fund)
        self.assertEqual(r.status_code, 200, r.text)
        r = c.post(f"/canal/{geral}/mensagens/", json={"conteudo": "..."}, headers=ana)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(c.delete(url, headers=fund).status_code, 204)
        r = c.post(f"/canal/{geral}/mensagens/", json={"conteudo": "voltei"}, headers=ana)
        self.assertEqual(r.status_code, 201, r.text)

        # canal privado: some da listagem de quem não tem acesso
        r = c.post(f"/gremio/{g}/canais/", json={"nome": "diretoria"}, headers=fund)
        privado = r.json()["id"]
        cargos = c.get(f"/gremio/{g}/cargos/", headers=fund).json()
        padrao = next(x["id"] for x in cargos if x["padrao"])
        r = c.put(f"/canal/{privado}/permissoes/cargos/{padrao}", json={"negar": ["VER_CANAL"]}, headers=fund)
        self.assertEqual(r.status_code, 200, r.text)
        nomes = [x["nome"] for x in c.get(f"/gremio/{g}/canais/", headers=ana).json()]
        self.assertEqual(nomes, ["geral"])
        self.assertEqual(c.get(f"/canal/{privado}", headers=ana).status_code, 404)

        # liberar só a ana (permissão por usuário no canal)
        r = c.put(f"/canal/{privado}/permissoes/usuarios/{ana_id}",
                  json={"permitir": ["VER_CANAL", "LER_HISTORICO", "ENVIAR_MENSAGENS"]}, headers=fund)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(c.post(f"/canal/{privado}/mensagens/", json={"conteudo": "psiu"}, headers=ana).status_code, 201)

        # permissão individual no grêmio
        r = c.put(f"/gremio/{g}/membros/{ana_id}/permissoes",
                  json={"permitir": ["GERENCIAR_CANAIS"]}, headers=fund)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(c.post(f"/gremio/{g}/canais/", json={"nome": "da-ana"}, headers=ana).status_code, 201)

        # validação
        r = c.put(f"/canal/{geral}/permissoes/usuarios/{ana_id}", json={"negar": ["VOAR"]}, headers=fund)
        self.assertEqual(r.status_code, 422)
        r = c.put(f"/canal/{geral}/permissoes/usuarios/{ana_id}", json={"negar": ["GERENCIAR_CARGOS"]}, headers=fund)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(c.get(f"/gremio/{g}/canais/").status_code, 401)  # sem token


if __name__ == "__main__":
    unittest.main()
