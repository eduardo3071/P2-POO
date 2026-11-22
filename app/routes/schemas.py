from pydantic import BaseModel, Field


class ChamadoCriar(BaseModel):
    tipo: str = Field(examples=["rede"])
    titulo: str = Field(examples=["Wi-Fi caiu no bloco B"])
    descricao: str = Field(examples=["Sem sinal nas salas 201 a 205."])
    solicitante_id: int = Field(examples=[1])
    tecnico_id: int | None = Field(default=None, examples=[1])


class ChamadoAlterar(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    tecnico_id: int | None = None


class ChamadoFechar(BaseModel):
    solucao: str = Field(examples=["Roteador reiniciado e firmware atualizado."])


class SolicitanteCriar(BaseModel):
    nome: str = Field(examples=["Ana Souza"])
    email: str = Field(examples=["ana@fatec.sp.gov.br"])


class TecnicoCriar(BaseModel):
    nome: str = Field(examples=["Carlos Lima"])
