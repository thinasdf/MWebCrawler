"""
Todos os itens, exceto Departamento, tem códigos que poderiam ser armazenados como int.
No entanto, há Departamentos com códigos do tipo 052, 19 e 383.
Por isso os códigos sao todos armazenados como str, inclusive nas chaves das OOBTree.
"""
# TODO: implementar __repr__ nas classes
# TODO: montar grafo de dependencias das disciplinas
# TODO: mostrar de quantos cursos uma disciplina faz parte
# TODO: disciplinas que estao em mais cursos
# TODO: cursos que tem mais disciplinas em comum
# TODO: mensagens de evolução das etapas

from utils import *
import persistent
from BTrees.OOBTree import OOBTree
import ZODB
import transaction
import os
import re
from collections import OrderedDict


class UnB(persistent.Persistent):
    def __init__(self):
        self.campi = {}
        self.niveis = ['graduacao', 'posgraduacao']
        self.denominacao = 'Universidade de Brasília'

    def build(self):
        self.set_campi()
        transaction.commit()
        self.set_pre_requisitos()

    def set_campi(self):
        value_map = {
            # 1: 'Darcy Ribeiro',
            # 2: 'Planaltina',
            # 3: 'Ceilândia',
            4: 'Gama'}

        for codigo, denominacao in value_map.items():
            campus = Campus(codigo, denominacao)
            self.campi[codigo] = campus
        transaction.commit()

    def set_pre_requisitos(self):
        pass
        # TODO: Construir referências de pré-requisitos para cada disciplina

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
        Departamento

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
        Departamento

        """

        for campus in self.campi.values():
            return campus.get_departamento_by_sigla(sigla)

    def get_curso_by_codigo(self):
        pass

    def __repr__(self):
        return (f'<{self.__class__.__name__}'
                f'({self.denominacao})>')


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
        """Acessa a página Matrícula Web e retorna os cursos.

        Parameters
        ----------
        nivel : {'graduacao', 'posgraduacao'}
            Graduação ou Pós-Graduação.

        Returns
        -------
        Union[dict, None]
            Um dicionário contendo os cursos ou None, em caso de erro.
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
            if cursos:
                for codigo, attributes in cursos.items():
                    if codigo not in self.cursos:
                        curso = Curso(self, codigo)
                        write_attributes(mapping, curso, attributes)
                        self.cursos[codigo] = curso
                        transaction.commit()

    def crawler_departamentos(self, nivel):
        """
        Acessa a página Matrícula Web e retorna os departamentos do campus.

        Parameters
        ----------
        nivel : {'graduacao', 'posgraduacao'}
            Graduação ou Pós-Graduação.

        Returns
        -------
        Union[dict, None]
            Um dicionário contendo os departamentos ou None, caso ocorra erro.
            O código do departamento é a chave.
            '052': {'Sigla': 'CDT', 'Denominação': 'CENTRO DE APOIO AO DESENVOLVIMENTO TECNOLÓGICO'}
        """

        departamentos_url = url_mweb(nivel, 'oferta_dep', self.codigo)
        table_lines_locator = 'xpath:/html/body/section//table[@id="datatable"]//tr'
        departamentos = table_to_dict(departamentos_url, table_lines_locator, key_index=0)
        return departamentos

    @staticmethod
    def get_nome_departamento(nivel, codigo):
        """
        Busca nome do Departamento.

        Parameters
        ----------
        nivel : {'graduacao', 'posgraduacao'}
            Graduação ou Pós-Graduação.
        codigo : str
            Código do departamento.

        Returns
        -------
        str
            Nome do departamento.
        """
        url_oferta = url_mweb(nivel, 'oferta_dis', codigo)
        lib = Browser()
        try:
            lib.open_headless_chrome_browser(url_oferta)
            block_header = lib.find_element('xpath:/html/body/section//div[@class="block-header"]')
            nome = block_header.find_element_by_tag_name('small').text
            return nome
        except Exception as e:
            # FIXME: especificar erro da exceção
            print(f'Ao acessar a página {url_oferta} '
                  f'para buscar o nome do departamento {codigo}, '
                  f'foi encontrado o seguinte erro:\n{e}')
            return None
        finally:
            lib.driver.close()

    def set_departamentos(self):
        """
        Cria objetos de Departamento() a partir do dicionário retornado pela função crawler_departamentos()

        Exemplo:
        052 {'Sigla': 'CDT', 'Denominação': 'CENTRO DE APOIO AO DESENVOLVIMENTO TECNOLÓGICO'}
        """

        attr_mapping_rev = {
            # 'codigo': 'Código',
            'sigla': 'Sigla',
            'denominacao': 'Denominação'}

        for nivel in UnB().niveis:
            departamentos = self.crawler_departamentos(nivel)
            if departamentos:
                for codigo, attributes in departamentos.items():
                    if codigo not in self.departamentos:
                        sigla = attributes[attr_mapping_rev['sigla']]
                        # denominacao = attributes[attr_mapping_rev['denominacao']]
                        denominacao = self.get_nome_departamento(nivel, codigo)
                        departamento = Departamento(self, codigo, sigla, denominacao)
                        self.departamentos[codigo] = departamento
                        transaction.commit()
                        # transaction.begin # TODO: tenho que iniciar transacao???

    def get_departamento_by_sigla(self, sigla):
        """
        Seleciona departamento a partir da sigla

        Parameters
        ----------
        sigla : str
            Sigla do departamento

        Returns
        -------
        Departamento
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
        Departamento
        """
        if codigo in self.departamentos:
            return self.departamentos.get(codigo)
        else:
            return None

    def get_disciplina_by_codigo(self, codigo):
        for departamento in self.departamentos.values():
            return departamento.get_disciplina_by_codigo(codigo)

    def __repr__(self):
        return (f'<{self.__class__.__name__}'
                f'({self.denominacao})>')


class Departamento(persistent.Persistent):
    def __init__(self, campus, codigo, sigla, denominacao):
        """

        Parameters
        ----------
            campus : Campus
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
        """
        Acessa a página Matrícula Web e retorna as disciplinas ofertadas pelo departamento.

        Parameters
        ----------
        nivel : {'graduacao', 'posgraduacao'}
            Graduação ou Pós-Graduação.

        Returns
        -------

        """
        oferta_url = url_mweb(nivel, 'oferta_dis', self.codigo)
        table_lines_locator = 'xpath:/html/body/section//table[@id="datatable"]//tr'
        oferta = table_to_dict(oferta_url, table_lines_locator, key_index=0)
        return oferta

    def set_disciplinas(self):
        """
        Acessa a página Matrícula Web, extrai as disciplinas ofertadas pelo departamento,
        cria objetos Disciplina() e adiciona na OOBTree
        """
        for nivel in UnB().niveis:
            oferta = self.crawler_oferta(nivel)
            if oferta:
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

    def __repr__(self):
        return (f'<{self.__class__.__name__}'
                f'([{self.codigo}] '
                f'{self.sigla}-, '
                f'{self.denominacao}, '
                f'{self.campus!r})>')


class Disciplina(persistent.Persistent):
    def __init__(self, departamento, nivel, codigo):
        """
        Constrói objeto Disciplina().

        Parameters
        ----------
        codigo : str
            Código da disciplina.
        nivel : {'graduacao', 'posgraduacao'}
            Graduação ou Pós-Graduação.
        departamento : Departamento
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
        """Acessa a página Matrícula Web e retorna as informações da disciplina.

        Returns
        -------
        Union[dict, None]
            Dicionário com os atributos da disciplina ou None, caso ocorra erro.
        """

        url_disciplinas = url_mweb(self.nivel, 'disciplina', self.codigo)
        lib = Browser()
        try:
            lib.open_headless_chrome_browser(url_disciplinas)
            disciplina = {}

            locator_disciplinas = 'xpath:/html/body/section//table[@id="datatable"]/tbody/tr'
            for element in lib.find_elements(locator_disciplinas):
                th = element.find_elements_by_tag_name('th')
                td = element.find_element_by_tag_name('td')
                value = td.text
                if len(th) > 0:
                    title = th[0].text
                    disciplina[title] = value
                else:
                    # caso a tag th tenha o rowspan > 1, na próxima linha vem vazia.
                    # então repete o título e adiciona o conteúdo
                    # assume que no início do loop encontra um th
                    disciplina[title] += '\n' + value
            return disciplina
        except Exception as e:
            # FIXME: especificar erro da exceção
            print(f'Ao acessar a página {url_disciplinas} para buscar informações sobre a disciplina, '
                  f'foi encontrado o seguinte erro:\n{e}')
            return None
        finally:
            lib.driver.close()

    def set_disciplina(self):
        """
        Preenche os atributos da disciplina.

        """

        disciplina = self.crawler_disciplina()
        if disciplina:
            attr_mapping = {
                # 'Órgão': 'departamento',
                # 'Código': 'codigo',
                'Denominação': 'denominacao',
                # 'Nível': 'nivel',
                'Início da Vigência em': 'vigencia',
                'Pré-requisitos': 'pre_requisitos',
                'Bibliografia': 'bibliografia',
                'Ementa': 'ementa',
                'Programa': 'programa'}

            write_attributes(attr_mapping, self, disciplina)

            transaction.commit()

    def __repr__(self):
        return (f'<{self.__class__.__name__}'
                f'({self.nivel} '
                f'[{self.codigo}] '
                f'{self.departamento.sigla} - '
                f'{self.denominacao})>')


class Curso(persistent.Persistent):
    def __init__(self, campus, codigo):
        """

        Parameters
        ----------
        campus : Campus
        codigo : str
            Código do curso.
        """

        self.campus = campus
        self.codigo = codigo
        self.denominacao = None
        self.grau = None
        self.modalidade = None
        self.habilitacoes = {}
        self.last_updated_in = None

        self.set_habilitacoes()

    def crawler_habilitacoes(self, nivel):
        """
        Acessa a página Matrícula Web e retorna as habilitações do curso.

        Parameters
        ----------
        nivel : {'graduacao', 'posgraduacao'}
            Graduação ou Pós-Graduação.

        Returns
        -------
        Union[dict, None]
            Dicionário contendo as habilitações do curso ou None, caso ocorra erro.
        """
        habilitacoes_url = url_mweb(nivel, 'curso_dados', self.codigo)
        lib = Browser()
        try:
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
        except Exception as e:
            # FIXME: especificar erro da exceção
            print(f'Ao acessar a página {habilitacoes_url} para buscar habilitações '
                  f'do curso de {self.denominacao}, '
                  f'foi encontrado o seguinte erro:\n{e}')
            return None
        finally:
            lib.driver.close()

    def set_habilitacoes(self):
        # TODO: Verificar problema de habilitacoes na posgraduacao sem curriculo, ex: Geografia
        # FIXME: Armazenar informações no currículo ao invés da habilitação.
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
            if habilitacoes:
                for codigo, attributes in habilitacoes:
                    habilitacao = Habilitacao(self, nivel, codigo)
                    write_attributes(attr_mapping, habilitacao, attributes)
                    self.habilitacoes[codigo] = habilitacao
                    self.set_curriculo(nivel, habilitacao)
                    transaction.commit()

    def crawler_tables(self, nivel, codigo):
        """
        Acessa a página Matrícula Web e retorna as tabelas da habilitação.

        Parameters
        ----------
        nivel : {'graduacao', 'posgraduacao'}
            Graduação ou Pós-Graduação.
        codigo : str
            Código da habilitação.

        Returns
        -------
        Union[list, None]
            Lista de dicionários das tabelas da habilitação ou None, caso ocorra erro.
        """

        curriculo_url = url_mweb(nivel, 'curriculo', codigo)
        lib = Browser()
        cadeias = []
        try:
            lib.open_headless_chrome_browser(curriculo_url)
            tables_locator = 'xpath:/html/body/section//table[@id="datatable"]'
            tables = lib.find_elements(tables_locator)
            for table in tables:
                lines = table.find_elements_by_tag_name('tr')
                cadeia = lines_to_dict(lines, key_index=0)
                cadeias.append(cadeia)
            return cadeias
        except Exception as e:
            # FIXME: especificar erro da exceção
            print(f'Ao acessar a página {curriculo_url} '
                  f'para buscar o curriculo do curso {self.denominacao}, '
                  f'foi encontrado o seguinte erro:\n{e}')
            return None
        finally:
            lib.driver.close()

    def set_curriculo(self, nivel, habilitacao):
        """

        Parameters
        ----------
        nivel : {'graduacao', 'posgraduacao'}
            Graduação ou Pós-Graduação.
        habilitacao : Habilitacao

        """

        tables = self.crawler_tables(nivel, habilitacao.codigo)

        table_mapping = [
            {'tipo': 'curriculo', 'pos': 0},
            {'tipo': 'obrigatoria', 'pos': 1},
            {'tipo': 'obrigatoria_seletiva', 'pos': 2},
            {'tipo': 'optativa', 'pos': 3}]

        attr_mapping = {
            'codigo': 'Código',
            'disciplina': 'Disciplina',
            'creditos': 'Créditos',
            'area': 'Área'}

        curriculo = Curriculo(habilitacao)

        for mapping in table_mapping:
            tipo = mapping['tipo']
            pos = mapping['pos']
            table = tables[pos]
            if pos == 0:
                pass
                # TODO: pegar informações complementares sobre o currículo da habilitação
            else:
                cadeia = Cadeia(curriculo, tipo)
                for line in table:
                    codigo = line[attr_mapping['codigo']]
                    creditos = line[attr_mapping['creditos']]
                    cadeia.add_disciplina(codigo, creditos)
                curriculo.cadeias.append(cadeia)
            transaction.commit()

    def __repr__(self):
        return (f'<{self.__class__.__name__}'
                f'({self.nivel}: '
                f'[{self.codigo}] '
                f'{self.denominacao}, '
                f'{self.campus!r})>')


class Habilitacao(persistent.Persistent):
    def __init__(self, curso, nivel, codigo):
        self.curso = curso
        self.nivel = nivel
        self.codigo = codigo
        self.curriculo = None  # Curriculo()
        self.grau = None

    def crawler_curriculo(self):
        pass
        # TODO: trazer código da função Curso().crawler_tables para cá

    def set_curriculo(self):
        pass
        # TODO: trazer código da função Curso().set_curriculo para cá

    def __repr__(self):
        return (f'<{self.__class__.__name__}'
                f'({self.grau}, '
                f'{self.curso.denominacao})>')


class Curriculo(persistent.Persistent):
    def __init__(self, habilitacao):
        self.habilitacao = habilitacao  # Habilitacao()
        self.cadeias = []
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
        # TODO: trazer código da função Curso().crawler_tables para cá

    def set_disciplinas(self):
        pass
        # TODO: trazer código da função Curso().crawler_tables para cá

    def __repr__(self):
        return (f'<{self.__class__.__name__}'
                f'{self.cred_formatura} créditos)>')


class Cadeia(persistent.Persistent):
    def __init__(self, curriculo, tipo):
        """

        Parameters
        ----------
        curriculo : Curriculo
        tipo : {'obrigatorias', 'obrigatorias_seletivas', 'optativas'}
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
            Código da disciplina.
        creditos : str
            Créditos dividos em quatro áreas: '002 004 000 006'

        """
        campus = self.curriculo.habilitacao.curso.campus
        disciplina = campus.get_disciplina_by_codigo(codigo)

        keys = disciplina.creditos.keys()
        values = creditos.split(' ')
        values = list(map(int, values))
        creditos_dict = dict(zip(keys, values))
        disciplina.creditos.update(creditos_dict)

        self.disciplinas[codigo] = disciplina

    def get_disciplina_by_codigo(self, codigo):
        return self.disciplinas.get(codigo)

    def iter_disciplinas(self):
        for disciplina in self.disciplinas.values():
            yield disciplina

    def __len__(self):
        count = 0
        for disciplina in self.iter_disciplinas():
            count += 1
        return count

    def __repr__(self):
        return (f'<{self.__class__.__name__}'
                f'({self.tipo}: '
                f'{len(self)} disciplinas)>')


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
            print(f'Finished building database in {clock.get_duration()} minutes')

        transaction.commit()
        connection.close()


def test():
    pass
    # TODO: Buscar atributos e objetos que ficaram vazios


if __name__ == '__main__':
    main = Main()
    db_location = 'data/data_v1.fs'
    main.build_database(db_location, overwrite=True)
