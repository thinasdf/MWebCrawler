class Departamento:
    def __init__(
        self,
        codigo
    ):
        self.codigo = codigo


class Disciplina:
    def __init__(
        self,
        codigo
    ):
        self.codigo = codigo
        self.denominacao = None
        self.departamento = None
        self.creditos = {'Teor':0, 'Prat':0, 'Ext':0, 'Est':0}
        self.nivel = None
        self.vigencia = None
        self.pre_requisitos = []
        self.ementa = None
        self.programa = None
        self.bibliografia = []


class Curso:
    def __init__(
        self,
        codigo
    ):
        self.codigo = codigo
        self.grau = None
        self.habilitacoes = []


class Habilitacao:
    def __init__(
        self,
        codigo
    ):
        self.codigo = codigo
        self.curriculo = None


class Curriculo:
    def __init__(
        self,
        codigo
    ):
        self.codigo = codigo
        self.disciplinas = []


class Campus:
    def __init__(self):
        pass
