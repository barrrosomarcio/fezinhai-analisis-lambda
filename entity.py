from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class Premiacao:
    vencedores: int
    premio: float

@dataclass
class LotofacilPremiacao:
    quinze: Premiacao
    quatorze: Premiacao
    treze: Premiacao
    doze: Premiacao
    onze: Premiacao

@dataclass
class LotofacilResultEntity:
    concurso: int
    data: datetime
    dezenas: List[str]
    premiacoes: LotofacilPremiacao
    acumulou: bool
    acumuladaProxConcurso: float
    dataProxConcurso: str
    proxConcurso: int
    timeCoracao: str
    mesSorte: str

@dataclass
class LotofacilResultsListEntity:
    results: List[LotofacilResultEntity] 