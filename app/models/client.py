from typing import Any


class Client:
    """
    Modelo do Cliente para o GlobalSIM (Etapa 2 - Árvore B).
    Armazena o identificador único (ID), nome, e-mail, código eSIM,
    pacote de dados contratado e status da linha.
    """

    def __init__(
        self,
        id: int,
        name: str,
        email: str,
        esim: str,
        pacote: int | str,
        status: str = "ativo",
    ):
        self.id: int = id
        self.name: str = name
        self.email: str = email
        self.esim: str = esim
        self.pacote: int | str = pacote
        self.status: str = status

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Client):
            return self.id < other.id
        return self.id < other

    def __le__(self, other: Any) -> bool:
        if isinstance(other, Client):
            return self.id <= other.id
        return self.id <= other

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, Client):
            return self.id > other.id
        return self.id > other

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, Client):
            return self.id >= other.id
        return self.id >= other

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Client):
            return self.id == other.id
        return self.id == other

    def __repr__(self) -> str:
        return (
            f"Client(id={self.id}, name='{self.name}', "
            f"esim='{self.esim}', pacote='{self.pacote}', status='{self.status}')"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "esim": self.esim,
            "pacote": self.pacote,
            "status": self.status,
        }
