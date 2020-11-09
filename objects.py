# TODO: Usar IOBTree para todos, chave sendo sempre int e propriedade sendo str

import persistent
from utils import *
import datetime
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
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

    def build(self):
        self.set_campi()
        transaction.commit()

    def set_campi(self):
        value_map = {
            1: 'Darcy Ribeiro',
            2: 'Planaltina',
            3: 'Ceilândia',
            4: 'Gama'}

        for codigo, denominacao in value_map.items():
            campus = Campus(codigo, denominacao)
            self.campi[codigo] = campus
        transaction.commit()

    def iter_disciplinas(self):
        """
        Returns
        -------
        A generator of Disciplina()
        """
        for campus in self.campi.values():
            for departamento in campus.departamentos.departamentos.values():
                for disciplina in departamento.disciplinas.disciplinas.values():
                    yield disciplina

    def iter_departamentos(self):
        """
        Returns
        -------
        A generator of Departamentos()
        """
        for campus in self.campi.values():
            for departamento in campus.departamentos.values():
                yield departamento

    def get_disciplina_by_codigo(self, codigo):
        for campus in self.campi.values():
            campus.get_disciplina_by_codigo(codigo)

    def get_departamento_by_codigo(self, codigo):
        """

        Parameters
        ----------
        codigo : str

        Returns
        -------
        Departamento()

        """

        for campus in self.campi.values():
            return campus.get_departamento_by_codigo(codigo)

    def get_departamento_by_sigla(self, sigla):
        """

        Parameters
        ----------
        sigla : str

        Returns
        -------
        Departamento()

        """

        for campus in self.campi.values():
            return campus.get_departamento_by_sigla(sigla)

    def get_curso_by_codigo(self):
        pass



class Campus(persistent.Persistent):
    def __init__(self, codigo, denominacao):
        self.codigo = codigo
        self.denominacao = denominacao
        self.last_updated_in = None
        self.departamentos = OOBTree()
        self.cursos = IOBTree()
        self.set_departamentos()
        self.set_cursos()

    def crawler_cursos(self, nivel):
        """Acessa a página Matrícula Web e retorna um dicionário com a lista de cursos.

        Returns
        -------
        dict
            Um dicionário contendo os cursos.
            O código do curso é a chave.
            FIXME: exemplo do dicionário: 052 {'Sigla': 'CDT', 'Denominação': 'CENTRO DE APOIO AO DESENVOLVIMENTO TECNOLÓGICO'}
        """

        cursos_url = url_mweb(nivel, 'curso_rel', self.codigo)
        table_lines_locator = 'xpath:/html/body/section//table[@id="datatable"]//tr'
        cursos = table_to_dict(cursos_url, table_lines_locator, key_index=1)
        return cursos

    def set_cursos(self):
        """
        Cria objetos de Curso() a partir do dicionário retornado pela função crawler_cursos()

        Exemplo:
        052 {'Sigla': 'CDT', 'Denominação': 'CENTRO DE APOIO AO DESENVOLVIMENTO TECNOLÓGICO'}
        """

        mapping = {
            'Modalidade': 'modalidade',
            # 'Código': 'codigo',
            'Denominação': 'denominacao',
            'Turno': 'turno'}

        for nivel in UnB().niveis:
            cursos = self.crawler_departamentos(nivel)

            for codigo, attributes in cursos.items():
                codigo = int(codigo) # FIXME: remover quando tipificar saída do table_to_dict
                if codigo not in self.cursos:
                    curso = Curso(self, codigo)
                    write_attributes(mapping, curso, attributes)
                    self.cursos[codigo] = curso
                    transaction.commit()

    def crawler_departamentos(self, nivel):
        """Acessa a página Matrícula Web e retorna um dicionário com a lista de departamentos.

        Returns
        -------
        dict
            Um dicionário contendo os departamentos.
            O código do departamento é a chave.
            052 {'Sigla': 'CDT', 'Denominação': 'CENTRO DE APOIO AO DESENVOLVIMENTO TECNOLÓGICO'}
        """

        departamentos_url = url_mweb(nivel, 'oferta_dep', self.codigo)
        table_lines_locator = 'xpath:/html/body/section//table[@id="datatable"]//tr'
        departamentos = table_to_dict(departamentos_url, table_lines_locator, key_index=0)
        return departamentos

    def set_departamentos(self):
        """
        Cria objetos de Departamento() a partir do dicionário retornado pela função crawler_departamentos()

        Exemplo:
        052 {'Sigla': 'CDT', 'Denominação': 'CENTRO DE APOIO AO DESENVOLVIMENTO TECNOLÓGICO'}
        """

        # TODO: pegar nome bonito do Departamento. Onde???

        attr_mapping_rev = {
            # 'codigo': 'Código',
            'sigla': 'Sigla',
            'denominacao': 'Denominação'}

        for nivel in UnB().niveis:
            departamentos = self.crawler_departamentos(nivel)
            for codigo, attributes in departamentos:
                if codigo not in self.departamentos:
                    sigla = attributes[attr_mapping_rev['sigla']]
                    denominacao = attributes[attr_mapping_rev['denominacao']]
                    departamento = Departamento(self, codigo, sigla, denominacao)
                    self.departamentos[departamento.codigo] = departamento
                    transaction.commit()

    def get_departamento_by_sigla(self, sigla):
        """
        Seleciona departamento a partir da sigla

        Parameters
        ----------
        sigla : str
            Sigla do departamento

        Returns
        -------
        Departamento()
        """

        for departamento in self.departamentos.values():
            if departamento.sigla == sigla:
                return departamento
        return None

    def get_departamento_by_codigo(self, codigo):
        """
        Seleciona departamento a partir do código

        Parameters
        ----------
        codigo : str
            Código do departamento

        Returns
        -------
        Departamento()
        """
        if codigo in self.departamentos:
            return self.departamentos.get(codigo)
        else:
            return None

    def get_disciplina_by_codigo(self, codigo):
        for departamento in self.departamentos.values():
            return departamento.get_disciplina_by_codigo(codigo)


class Departamento(persistent.Persistent):
    def __init__(self, campus, codigo, sigla, denominacao):
        """
        Parameters
        ----------
            campus : Campus()
            codigo : str
                string porque há departamentos com e sem 0 (zero) na frente
            sigla : str
            denominacao : str
        """

        self.campus = campus
        self.codigo = codigo
        self.sigla = sigla
        self.denominacao = denominacao

        self.disciplinas = IOBTree()
        self.set_disciplinas()
        self.last_updated_in = datetime.datetime.now()

    def crawler_oferta(self, nivel):
        oferta_url = url_mweb(nivel, 'oferta_dis', self.codigo)
        table_lines_locator = 'xpath:/html/body/section//table[@id="datatable"]//tr'
        oferta = table_to_dict(oferta_url, table_lines_locator, key_index=0)
        return oferta

    def set_disciplinas(self):
        """
        Acessa a página do Matrícula Web, extrai as disciplinas ofertadas pelo departamento,
        cria objetos Disciplina() e adiciona na IOBTree
        """
        for nivel in UnB().niveis:
            oferta = self.crawler_oferta(nivel)
            for codigo in oferta:
                codigo = int(codigo) # FIXME: remover quando tipificar saída do table_to_dict
                disciplina = Disciplina(codigo, nivel)
                disciplina.set_disciplina()
                self.disciplinas[codigo] = disciplina
        transaction.commit()

    def get_disciplina_by_codigo(self, codigo):
        if codigo in self.disciplinas:
            return self.disciplinas.get(codigo)
        else:
            return None

class Disciplina(persistent.Persistent):
    def __init__(self, codigo, nivel, departamento):
        """
        Constrói objeto Disciplina()

        Parameters
        ----------
        codigo : int
            Código da disciplina
        nivel : str
            Graduação ('graduacao') ou Pós-graduação ('posgraduacao')
        departamento : Departamento()
        """
        self.codigo = codigo
        self.nivel = nivel
        self.departamento = departamento
        self.denominacao = None
        self.creditos = {'Teor': 0, 'Prat': 0, 'Ext': 0, 'Est': 0}
        self.vigencia = None
        self.pre_requisitos = []
        self.ementa = None
        self.programa = None
        self.bibliografia = []
        self.last_updated_in = None
        self.set_disciplina()
        self.last_updated_in = datetime.datetime.now()

    def crawler_disciplina(self):
        """Acessa a página Matrícula Web e retorna um dicionário com as informações da disciplina.

        Returns
        -------
        dict
            Dicionario com os atributos da disciplina
        """

        url_disciplinas = url_mweb(self.nivel, 'disciplina', self.codigo)
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

    def set_disciplina(self):
        """
        Usa o dicionário retornado pelo crawler() para preencher os atributos da disciplina
        """

        disciplinas = self.crawler_disciplina()

        attr_mapping = {
            'Órgão': 'departamento',
            # 'Código': 'codigo',
            # 'Denominação': 'denominacao',
            'Nível': 'nivel',
            'Início da Vigência em': 'vigencia',
            'Pré-requisitos': 'pre_requisitos',
            'Bibliografia': 'bibliografia',
            'Ementa': 'ementa',
            'Programa': 'programa'}

        write_attributes(attr_mapping, self, disciplinas)

        transaction.commit()

    def __repr__(self):
        representation = \
            f'{self.codigo} - '\
            f'{self.sigla} - '\
            f'{self.denominacao} '\
            f'({self.campus.denominacao})'
        return representation


class Curso(persistent.Persistent):
    def __init__(self, campus, codigo):
        """

        Parameters
        ----------
        campus : Campus()
        codigo : int
        """

        self.campus = campus
        self.codigo = codigo
        self.grau = None
        self.modalidade = None
        self.habilitacoes = {}
        self.last_updated_in = None

    def crawler_habilitacoes(self):
        # habilitacoes_url = url_mweb(nivel, 'curso_rel', self.codigo)
        # table_lines_locator = 'xpath:/html/body/section//table[@id="datatable"]//tr'
        # habilitacoes = table_to_dict(habilitacoes_url, table_lines_locator, key_index=1)
        return habilitacoes

    def set_habilitacoes(self):
        pass


class Habilitacao(persistent.Persistent):
    def __init__(self):
        self.codigo = None
        self.curriculo = None
        self.last_updated_in = None

    def crawler_curriculo(self):
        pass

    def set_curriculo(self):
        pass

class Curriculo(persistent.Persistent):
    def __init__(self):
        self.codigo = None
        self.disciplinas = []
        self.last_updated_in = None

    def crawler_disciplinas(self):
        pass

    def set_disciplinas(self):
        pass

    # TODO: adicionar créditos da disciplina ao ler curriculo da habilitacao


# TODO: mensagens de evolução das etapas

class Clock:
    def __init__(self):
        self.start_time = datetime.datetime.now()

    def get_duration(self):
        now = datetime.datetime.now()
        duration = now - self.start_time
        return duration.total_seconds()/60


class Main:
    def __init__(self):

    @staticmethod
    def build_database(db_location, overwrite=False):
        clock = Clock()
        exists = os.path.isfile(db_location)

        # Create connection
        connection = ZODB.connection(db_location)
        root = connection.root

        if overwrite or not exists:
            root.Unb = UnB()
            root.Unb.build()
            duration = None
            print(f'Finished building database in {clock.get_duration()} minutes')

        transaction.commit()
        connection.close()


def test():
    pass
    # TODO: Buscar atributos e objetos que ficaram vazios


if __name__ == '__main__':
    main = Main()
    db_location = 'data/data_v10.fs'
    main.build_database(db_location, overwrite=True)

