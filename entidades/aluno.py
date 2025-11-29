class Aluno:
    def __init__(self, codigo, preferencias_projetos: list, nota: int):
        self.codigo = codigo
        self.preferencias_projetos = preferencias_projetos
        self.nota = nota
        self.tipo = 'aluno'

    def getCodigo(self) -> str:
        return self.codigo

    def setCodigo(self, codigo: str):
        self.codigo = codigo

    def getPreferenciasProjetos(self) -> list:
        return self.preferencias_projetos

    def setPreferenciasProjetos(self, preferencias_projetos: list):
        self.preferencias_projetos = preferencias_projetos

    def getNota(self) -> int:
        return self.nota

    def setNota(self, nota: int):
        self.nota = nota

    def getTipo(self) -> str:
        return self.tipo

    def setTipo(self, tipo: str):
        self.tipo = tipo

    def __str__(self):
        return f"{self.getCodigo()} - {self.getPreferenciasProjetos()} - {self.getNota()}"