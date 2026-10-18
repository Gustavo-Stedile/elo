from application.exceptions.gremio_exceptions import GremioNaoExisteErro
from domain.core import Gremio, MembroGremio
from infra.core.repositories import GremioRepository, MembroGremioRepository


class GremioService:
    def __init__(
        self, 
        gremio_repository: GremioRepository, 
        membro_gremio_repository: MembroGremioRepository
    ):
        self.gremio_repository = gremio_repository
        self.membro_gremio_repository = membro_gremio_repository

    def criar_gremio(
        self, 
        nome: str, 
        instituicao: str, 
        etapa_ensino: str, 
        fundador_id: int
    ) -> Gremio:
        """Cria um grêmio e automaticamente vincula o usuário criador como fundador."""
        
        novo_gremio = Gremio(
            id=None,
            nome=nome,
            instituicao=instituicao,
            etapa_ensino=etapa_ensino,
            legitimado=False
        )

        # 2. Salva o grêmio no banco via repositório
        gremio_salvo = self.gremio_repository.create(novo_gremio)

        # 3. Regra de Negócio: Cria o vínculo associativo colocando o criador como fundador
        novo_membro = MembroGremio(
            id=None,
            usuario_id=fundador_id,
            gremio_id=gremio_salvo.id,
            cargo="fundador"
        )
        self.membro_gremio_repository.create(novo_membro)

        # 4. Retorna a entidade de domínio do grêmio (a camada de rota formata o JSON)
        return {
            "id": gremio_salvo.id,
            "nome": gremio_salvo.nome,
            "instituicao": gremio_salvo.instituicao,
            "etapa_ensino": gremio_salvo.etapa_ensino,
            "legitimado": gremio_salvo.legitimado,
        }

    def buscar_por_id(self, id: int) -> Gremio:
        """Busca um grêmio pelo ID. Lança exceção se não encontrar."""
        gremio = self.gremio_repository.get_by_id(id)

        if not gremio:
            raise GremioNaoExisteErro()
        
        return {
            "id": gremio.id,
            "nome": gremio.nome,
            "instituicao": gremio.instituicao,
            "etapa_ensino": gremio.etapa_ensino,
            "legitimado": gremio.legitimado,
        }