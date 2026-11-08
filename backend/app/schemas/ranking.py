from pydantic import BaseModel


class ItemRanking(BaseModel):
    posicion: int
    apodo: str
    total: int
    exactos: int
    aciertos: int
    racha_actual: int
    mejor_racha: int


class RankingSalida(BaseModel):
    pagina: int
    tamano: int
    total_usuarios: int
    items: list[ItemRanking]
