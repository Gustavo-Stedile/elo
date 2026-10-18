from infra.database import SessionLocal


def get_db():
    """Uma sessão por requisição, compartilhada por todas as dependências
    daquela requisição e sempre fechada ao final (antes, cada dependência
    abria uma sessão que nunca era fechada)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
