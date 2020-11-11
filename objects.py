"""
Todos os itens, exceto Departamento, tem códigos que poderiam ser armazenados como int.
No entanto, há Departamentos com códigos do tipo 052, 19 e 383.
Por isso os códigos sao todos armazenados como str, inclusive nas chaves das OOBTree.
"""

import persistent
from utils import *
import datetime
from BTrees.OOBTree import OOBTree
import ZODB
import ZODB.FileStorage
import transaction
import os
import re
from collections import OrderedDict


class UnB(persistent.Persistent):
    def __init__(self):
        self.campi = {}
        self.niveis = ['graduacao', 'posgraduacao']

    def build(self):
        self.set_campi()
        transaction.commit()
        self.set_pre_requisitos()

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

    def set_pre_requisitos(self):
        pass  # TODO: Construir referências de pré-requisitos para cada disciplina

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
        self.cursos = OOBTree()
        self.set_departamentos()
        self.set_cursos()

    def crawler_cursos(self, nivel):
        """Acessa a página Matrícula Web e retorna um dicionário com a lista de cursos.

        Returns
        -------
        dict
            Um dicionário contendo os cursos.
            O código do curso é a chave.
            FIXME: exemplo do dicionário:
            052 {'Sigla': 'CDT', 'Denominação': 'CENTRO DE APOIO AO DESENVOLVIMENTO TECNOLÓGICO'}
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
                    self.departamentos[codigo] = departamento
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

        self.disciplinas = OOBTree()
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
        cria objetos Disciplina() e adiciona na OOBTree
        """
        for nivel in UnB().niveis:
            oferta = self.crawler_oferta(nivel)
            for codigo in oferta:
                disciplina = Disciplina(self, nivel, codigo)
                disciplina.set_disciplina()
                self.disciplinas[codigo] = disciplina
        transaction.commit()

    def get_disciplina_by_codigo(self, codigo):
        if codigo in self.disciplinas:
            return self.disciplinas.get(codigo)
        else:
            return None


class Disciplina(persistent.Persistent):
    def __init__(self, departamento, nivel, codigo):
        """
        Constrói objeto Disciplina()

        Parameters
        ----------
        codigo : str
            Código da disciplina
        nivel : str
            Graduação ('graduacao') ou Pós-graduação ('posgraduacao')
        departamento : Departamento()
        """
        self.codigo = codigo
        self.nivel = nivel
        self.departamento = departamento
        self.denominacao = None
        self.creditos = OrderedDict({'teoria': 0, 'pratica': 0, 'extensao': 0, 'estudos': 0})
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
                    # caso a tag th tenha o rowspan > 1, na próxima linha vem vazio.
                    # então repete o título e adiciona o conteúdo
                    # assume que no início do loop encontra um th
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
        codigo : str
        """

        self.campus = campus
        self.codigo = codigo
        self.grau = None
        self.modalidade = None
        self.habilitacoes = {}
        self.last_updated_in = None

        self.set_habilitacoes()

    def crawler_habilitacoes(self, nivel):
        # TODO: Try, Except, Finally
        lib = Browser()
        habilitacoes_url = url_mweb(nivel, 'curso_dados', self.codigo)
        lib.open_headless_chrome_browser(habilitacoes_url)

        main_table_locator = 'xpath:/html/body/section//div[@class="body table-responsive"]'
        main_table_we = lib.find_element(main_table_locator)

        curriculos_we = main_table_we.find_elements_by_partial_link_text('curriculo.aspx?cod=')
        tables_we = main_table_we.find_elements_by_tag_name('table')
        habilitacoes_we = dict(zip(curriculos_we, tables_we))

        habilitacoes = {}
        for curriculo_we, table_we in habilitacoes_we:
            # Codigo
            match = re.match(r'\D+(\d+)$', curriculo_we.url)
            codigo = match.group(1)

            # Table
            titles = [th.text for th in table_we.find_elements_by_tag_name('th')]
            values = [td.text for td in table_we.find_elements_by_tag_name('td')]

            habilitacoes[codigo] = dict(zip(titles, values))

        return habilitacoes

    def set_habilitacoes(self):
        attr_mapping = {
            'Grau': 'grau',
            'Limite mínimo de permanência': 'permanencia_min',
            'Limite máximo de permanência': 'permanencia_max',
            'Quantidade de créditos para formatura': 'cred_formatura',
            'Quantidade mínima de créditos optativos na área de concentração': 'cred_min_opt_concentr',
            'Quantidade mínima de créditos optativos na área conexa': 'cred_min_opt_conexa',
            'Quantidade máxima de créditos no módulo livre': 'cred_max_opt_concentr',
            'Quantidade mínima de Horas em Atividade Complementar': 'horas_min_ativ_compl',
            'Quantidade máxima integralizada de Horas em Atividade Complementar': 'horas_max_ativ_compl',
            'Quantidade mínima de Horas em Atividade de Extensão': 'horas_min_ativ_ext',
            'Quantidade máxima integralizada de Horas em Atividade de Extensão': 'horas_max_ativ_ext'}

        for nivel in UnB().niveis:
            habilitacoes = self.crawler_habilitacoes(nivel)
            for codigo, attributes in habilitacoes:
                habilitacao = Habilitacao(self, nivel, codigo)
                write_attributes(attr_mapping, habilitacao, attributes)
                self.habilitacoes[codigo] = habilitacao
                self.set_curriculo(nivel, habilitacao)
                transaction.commit()

    def crawler_curriculo(self, nivel, codigo):
        # TODO: Try, Except, Finally
        lib = Browser()
        curriculo_url = url_mweb(nivel, 'curriculo', codigo)
        lib.open_headless_chrome_browser(curriculo_url)

        tables_locator = 'xpath:/html/body/section//table[@id="datatable"]'
        tables_we = lib.find_elements(tables_locator)
        # TODO: pegar disciplinas das diferentes cadeias: tables_we[1:]
        #
        # curriculos_we = main_table_we.find_elements_by_partial_link_text('curriculo.aspx?cod=')
        # tables_we = main_table_we.find_elements_by_tag_name('table')
        # habilitacoes_we = dict(zip(curriculos_we, tables_we))



        curriculo = {}

        return curriculo

    def set_curriculo(self, nivel, habilitacao):
        curriculo = Curriculo(habilitacao)
        attributes = self.crawler_curriculo(nivel, habilitacao.codigo)
        attr_mapping = {}  # TODO: Mapa de atributos
        write_attributes(attr_mapping, curriculo, attributes)
        # transaction.commit()


class Habilitacao(persistent.Persistent):
    def __init__(self, curso, nivel, codigo):
        self.curso = curso
        self.nivel = nivel
        self.codigo = codigo
        self.curriculo = None  # Curriculo()
        self.grau = None

    def crawler_curriculo(self):
        pass

    def set_curriculo(self):
        pass


class Curriculo(persistent.Persistent):
    def __init__(self, habilitacao):
        self.habilitacao = habilitacao  # Habilitacao()
        self.disciplinas = []
        self.permanencia_min = None
        self.permanencia_max = None
        self.cred_formatura = None
        self.cred_min_opt_concentr = None
        self.cred_min_opt_conexa = None
        self.cred_max_opt_concentr = None
        self.horas_min_ativ_compl = None
        self.horas_max_ativ_compl = None
        self.horas_min_ativ_ext = None
        self.horas_max_ativ_ext = None
        self.last_updated_in = None
        self.last_updated_in = None

    def crawler_disciplinas(self):
        pass

    def set_disciplinas(self):
        pass

    # TODO: adicionar créditos da disciplina ao ler curriculo da habilitacao


class Cadeia(persistent.Persistent):
    def __init__(self, curriculo, tipo):
        """

        Parameters
        ----------
        curriculo : Curriculo()
        tipo : {'obrigatoria', 'obrigatoria_seletiva', 'optativa'}
            Tipo das disciplinas na cadeia.
        """
        self.curriculo = curriculo
        self.tipo = tipo
        self.disciplinas = OOBTree()

    def add_disciplina(self, codigo, creditos):
        """

        Parameters
        ----------
        codigo : str
        creditos : str

        Returns
        -------

        """
        campus = self.curriculo.habilitacao.curso.campus
        disciplina = campus.get_disciplina_by_codigo(codigo)

        keys = disciplina.creditos.keys()
        values = creditos.split(' ')
        creditos = dict(zip(keys, values))
        disciplina.creditos.update(creditos)

        self.disciplinas[codigo] = disciplina

    def get_disciplina_by_codigo(self):
        pass

    def iter_disciplinas(self):
        pass

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
        pass

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
