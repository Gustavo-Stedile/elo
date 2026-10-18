from pydantic import Field, BaseModel, EmailStr


class AuthSchema(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Endereço de e-mail válido",
        examples=["ana.silva@exemplo.com"]
    )

    senha: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Senha de acesso (mínimo 8 caracteres)",
        examples=["SenhaSegura123"]
    )