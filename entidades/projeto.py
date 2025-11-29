class Projeto:
    def __init__(self, codigo: str, numero_vagas: int, requisito_notas: int):
        self.codigo = codigo
        self.numero_vagas = numero_vagas
        self.requisito_notas = requisito_notas
        self.tipo = 'projeto'

    def getCodigo(self) -> str:
        return self.codigo

    def setCodigo(self, codigo: str):
        self.codigo = codigo

    def getNumeroVagas(self) -> int:
        return self.numero_vagas

    def setNumeroVagas(self, numero_vagas: int):
        self.numero_vagas = numero_vagas

    def getRequisitoNotas(self) -> int:
        return self.requisito_notas

    def setRequisitoNotas(self, requisito_notas: int):
        self.requisito_notas = requisito_notas

    def getTipo(self) -> str:
        return self.tipo

    def setTipo(self, tipo: str):
        self.tipo = tipo

    def __str__(self):
        return f"{self.getCodigo()} - {self.getNumeroVagas()} - {self.getRequisitoNotas()}"