from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UsuarioCadastroSchema(BaseModel):
    nome: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Nome completo do usuário",
        examples=["Ana Silva"]
    )
    senha: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Senha de acesso (mínimo 8 caracteres)",
        examples=["SenhaSegura123"]
    )
    cpf: str = Field(
        ...,
        # pattern=r"^\d{11}$|^\d{3}\.\d{3}\.\d{3}-\d{2}$",
        description="CPF com 11 dígitos numéricos ou formatado (000.000.000-00)",
        examples=["12345678901"]
    )
    email: EmailStr = Field(
        ...,
        description="Endereço de e-mail válido",
        examples=["ana.silva@exemplo.com"]
    )
    ra: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=30,
        # pattern=r"^[a-zA-Z0-9]+$",
        description="Registro Acadêmico (opcional)",
        examples=["202612345"]
    )