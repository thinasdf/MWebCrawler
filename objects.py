import persistent
from utils import *
import datetime
from BTrees.IOBTree import IOBTree
import ZODB
import ZODB.FileStorage
import transaction
import os


"""
Todos os itens, exceto Departamento, tem códigos que poderiam ser armazenados como int.
Departamentos tem códigos do tipo 052, 19 e 383.
Por isso os códigos sao todos armazenados como str, exceto nas chaves das IOBTree,
onde são convertidos para str
"""


class UnB(persistent.Persistent):
    def __init__(self):
        self.campi = {}
        self.niveis = ['graduacao', 'posgraduacao']
        self.departamentos = None
        self.disciplinas = None
        self.cursos = None
        self.add_campi()

    def add_campi(self):
        value_map = {
            1: 'DARCY_RIBEIRO',
            2: 'PLANALTINA',
            3: 'CEILANDIA',
            4: 'GAMA'}

        for codigo, denominacao in value_map.items():
            campus = Campus()
            campus.codigo = codigo
            campus.denominacao = denominacao
            self.campi[codigo] = campus
        transaction.commit()


class Campus(persistent.Persistent):
    def __init__(self):
        self.codigo = None
        self.denominacao = None
        self.last_updated_in = None
        # TODO: Adicionar lista dos departamentos do campus? Departamentos sao da unb ou do campus?


class Departamentos(persistent.Persistent):
    def __init__(self):
        self.departamentos = IOBTree()

    def crawler(self, nivel, campus):
        """Acessa o Matrícula Web e retorna um dicionário com a lista de
        departamentos com ofertas.

        Parameters
        ----------
        nivel : str, optional
            Nível acadêmico do Departamento: graduacao ou posgraduacao (default is graduacao)
        campus : str
            O campus onde o curso é oferecido: DARCY_RIBEIRO,
            PLANALTINA, CEILANDIA ou GAMA (default is DARCY_RIBEIRO)

        Returns
        -------
        dict
            Um dicionário com os Departamentos. O código do Departamento é a chave.
            052 {'Sigla': 'CDT', 'Denominação': 'CENTRO DE APOIO AO DESENVOLVIMENTO TECNOLÓGICO'}
        """

        departamentos_url = url_mweb(nivel, 'oferta_dep', campus)
        table_lines_locator = 'xpath:/html/body/section//table[@id="datatable"]//tr'
        departamentos = table_to_dict(departamentos_url, table_lines_locator, key_index=0)
        return departamentos

    def add_departamentos(self, nivel, campus):
        """
        Cria objetos de Departamento() e respectivas Disciplina()
        a partir do dicionário retornado pelo crawler()

        Exemplo:
        052 {'Sigla': 'CDT', 'Denominação': 'CENTRO DE APOIO AO DESENVOLVIMENTO TECNOLÓGICO'}

        Parameters
        ----------
        nivel : str
            Graduação ('graduacao') ou Pós-graduação ('posgraduacao')
        campus : Campus()
            Campus
        """

        attribute_map = {
            'Código': 'codigo',
            'Sigla': 'sigla',
            'Denominação': 'denominacao'}

        # TODO: Pegar nome bonito do Departamento

        departamentos = self.crawler(nivel=nivel, campus=campus.codigo)
        for codigo in departamentos:
            if codigo not in self.departamentos:
                departamento = Departamento()

                for key, value in departamentos[codigo].items():
                    attribute = attribute_map[key]
                    setattr(departamento, attribute, value)
                departamento.last_updated_in = datetime.datetime.now()
                departamento.campus = campus
                departamento.disciplinas = self.get_disciplinas(departamento, nivel)
                print('\t', departamento.codigo, '-', departamento.denominacao)
                self.departamentos[int(departamento.codigo)] = departamento
            transaction.commit()

    def get_disciplinas(self, departamento, nivel):
        # TODO: receber obj depto
        """
        Acessa o Matrícula Web e retorna um dicionário com a lista de
        disciplinas ofertadas por um departamento.

        Parameters
        ----------
        departamento : Departamento()
            Departamento
        nivel : str, optional
            Nível acadêmico das disciplinas buscadas: graduacao ou
                 posgraduacao (default graduacao)

        Returns
        -------
        list
            lista de objetos do tipo Disciplina()

        """

        ofertadas_url = url_mweb(nivel, 'oferta_dis', departamento.codigo)
        table_lines_locator = 'xpath:/html/body/section//table[@id="datatable"]//tr'
        ofertadas = table_to_dict(ofertadas_url, table_lines_locator, key_index=0)

        disciplinas = IOBTree()
        # {int(k): v for k, v in ofertadas.items()}
        for codigo in ofertadas:
            ofertadas[codigo]['nivel'] = nivel
            disciplinas[int(codigo)] = ofertadas[codigo]

        return disciplinas

    def get_departamento_by_sigla(self, sigla):
        for departamento in self.departamentos.values():
            if departamento.sigla == sigla:
                return departamento
        return None

    def get_departamento_by_codigo(self, codigo):
        for departamento in self.departamentos.values():
            if departamento.codigo == codigo:
                return departamento
        return None


class Departamento(persistent.Persistent):
    def __init__(self):
        self.codigo = None
        self.sigla = None
        self.denominacao = None
        self.disciplinas = IOBTree()
        self.campus = None
        self.last_updated_in = None


class Disciplinas(persistent.Persistent):
    def __init__(self):
        self.disciplinas = IOBTree()

    def crawler(self, codigo, nivel):
        """Acessa o Matrícula Web e retorna um dicionário com as informações da
        disciplina.

        Parameters
        ----------
        codigo : str
            o código da disciplina.
        nivel : str
            nível acadêmico da disciplina: graduacao ou posgraduacao
        """

        url_disciplinas = url_mweb(nivel, 'disciplina', codigo)
        lib = Browser()
        lib.open_headless_chrome_browser(url_disciplinas)

        disciplina = {}
        try:
            locator_disciplinas = 'xpath:/html/body/section//table[@id="datatable"]/tbody/tr'
            for element in lib.find_elements(locator_disciplinas):
                th = element.find_elements_by_tag_name('th')
                td = element.find_element_by_tag_name('td')
                value = td.text
                if len(th) > 0:
                    title = th[0].text
                    disciplina[title] = value
                else:
                    # no caso de o th tiver o rowspan > 1, na proxima linha vem vazio.
                    # entao repete o titulo e adicona o conteudo
                    # assume que no inicio do loop encontra um th
                    disciplina[title] += '\n' + value
        except Exception as e:
            # FIXME: especificar erro da exceção
            print('erro em disciplina:', e)
            transaction.abort()
        finally:
            lib.driver.close()
        return disciplina

    def add_disciplina(self, codigo, nivel):
        """
        Usa o dicionário retornado pelo crawler() para cria um objeto Disciplina()

        Exemplo:


        """

        # TODO: Verifica se a disciplina já existe no banco antes de adicionar (usar flag overwrite)
        disciplina_dict = self.crawler(codigo, nivel)
        disciplina = Disciplina()

        attribute_map = {
            'Órgão': 'departamento',
            'Código': 'codigo',
            'Denominação': 'denominacao',
            'Nível': 'nivel',
            'Início da Vigência em': 'vigencia',
            'Pré-requisitos': 'pre_requisitos',
            'Bibliografia': 'bibliografia',
            'Ementa': 'ementa',
            'Programa': 'programa'}

        for key, value in disciplina_dict.items():
            attribute = attribute_map[key]
            setattr(disciplina, attribute, value)
        disciplina.last_updated_in = datetime.datetime.now()
        # TODO: Adicionar o objeto departamento ao inves da string
        self.disciplinas[int(disciplina.codigo)] = disciplina
        return disciplina

    def __repr__(self):
        representation = \
            f'{self.codigo} - '\
            f'{self.sigla} - '\
            f'{self.denominacao} '\
            f'({self.campus.denominacao})'
        return representation


class Disciplina(persistent.Persistent):
    def __init__(
        self
    ):
        self.codigo = None
        self.denominacao = None
        self.departamento = None
        self.creditos = {'Teor': 0, 'Prat': 0, 'Ext': 0, 'Est': 0}
        self.nivel = None
        self.vigencia = None
        self.pre_requisitos = []
        self.ementa = None
        self.programa = None
        self.bibliografia = []
        self.last_updated_in = None


class Cursos(persistent.Persistent):
    def __init__(self):
        self.cursos = IOBTree()


class Curso(persistent.Persistent):
    def __init__(self):
        self.codigo = None
        self.grau = None
        self.habilitacoes = []
        self.last_updated_in = None


class Habilitacao(persistent.Persistent):
    def __init__(self):
        self.codigo = None
        self.curriculo = None
        self.last_updated_in = None


class Curriculo(persistent.Persistent):
    def __init__(self):
        self.codigo = None
        self.disciplinas = []
        self.last_updated_in = None

    # TODO: adicionar creditos da disciplina ao ler curriculo da habilitacao


# TODO: mensagens de evolução das etapas


def build_database(db_location):
    # Create Database
    connection = ZODB.connection(db_location)
    root = connection.root

    # Initialize
    root.Unb = UnB()
    root.Unb.disciplinas = Disciplinas()
    root.Unb.cursos = Cursos()
    root.Unb.departamentos = Departamentos()

    # Finish
    transaction.commit()
    connection.close()

    print('Database created at', db_location)


def fill_database(db_location):
    if not os.path.isfile(db_location):
        build_database(db_location)

    connection = ZODB.connection(db_location)
    root = connection.root

    # Cria os departamentos
    print()
    for nivel in root.Unb.niveis:
        for campus in root.Unb.campi.values():
            print('Criando departamentos de', nivel, 'do campus', campus.denominacao)
            root.Unb.departamentos.add_departamentos(nivel, campus)
            transaction.commit()

    # Cria as disciplinas no banco
    # Reaponta as listas dos departamentos para os objetos de disciplina criados em banco
    print('Criando disciplinas de cada departamento')
    for departamento in root.Unb.departamentos.departamentos.values():
        for key, disciplina in departamento.disciplinas.items():
            nova_disciplina = root.Unb.disciplinas.add_disciplina(disciplina['Código'],
                                                                  disciplina['nivel'])
            departamento.disciplinas[key] = nova_disciplina
            transaction.commit()
        # print('\t Departamento', departamento.codigo, 'tem', len(departamento.disciplinas), 'disciplinas')
        print('\t', len(departamento.disciplinas), 'disciplinas criadas em', departamento.denominacao)

    connection.close()


def test():
    pass
    # TODO: Buscar atributos e objetos que ficaram vazios


def corrige(db_location):
    connection = ZODB.connection(db_location)
    root = connection.root

    # Cria as disciplinas no banco
    # Reaponta as listas dos departamentos para os objetos de disciplina criados em banco
    print('Criando disciplinas...')
    for departamento in root.Unb.Departamentos.departamentos.values():
        for key, disciplina in departamento.disciplinas.items():
            nova_disciplina = root.Unb.Disciplinas.add_disciplina(disciplina['Código'],
                                                                  disciplina['nivel'])
            departamento.disciplinas[key] = nova_disciplina
            transaction.commit()
        print('\t Departamento', departamento.codigo, 'tem', len(departamento.disciplinas), 'disciplinas')
    connection.close()


def main():
    # db_location = 'data/data.fs'
    db_location = 'data/data_v10.fs'
    fill_database(db_location)
    # corrige(db_location)


if __name__ == '__main__':
    main()


import ZODB
db_location = 'data/data_v10.fs'
connection = ZODB.connection(db_location)
root = connection.root
deptos = {depto.departamento: depto for depto in root.Unb.departamentos.departamentos.values()}
for k, disciplina in root.Unb.disciplinas.disciplinas.items():
    sigla = disciplina.departamento.split(' ')[0]
    disciplina.departamento = deptos[sigla]
transaction.commit()