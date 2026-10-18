from sqlalchemy.orm import Session


class UnitOfWork:
    """Controla a transação de uma requisição.

    Os repositórios apenas fazem flush; quem decide confirmar a operação é a
    camada de aplicação, chamando commit() quando o caso de uso termina.
    Assim, operações com vários passos (ex.: criar grêmio + cargos + canal)
    são atômicas.
    """

    def __init__(self, db: Session):
        self.db = db

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
