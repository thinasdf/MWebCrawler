# modificar a funcao cursos para pegar automaticamente o titulo da coluna
# departamentos
# criar objetos: disciplina, departamento, curso, curriculo, habilitacao
# montar grafo de dependencias das disciplinas
# mostrar de quantos cursos uma disciplina faz parte; disciplinas que estao em mais cursos



#  -*- coding: utf-8 -*-
#       @file: curso.py
#     @author: Guilherme N. Ramos (gnramos@unb.br)
#
# Funções de web-crawling para buscar informações da lista de cursos da UnB. O
# programa busca as informações com base em expressões regulares que, assume-se
# representam a estrutura de uma página do Matrícula Web. Caso esta estrutura
# seja alterada, as expressões aqui precisam ser atualizadas de acordo.
#
# Erros em requests são ignorados silenciosamente.

from RPA.Browser import Browser
from utils import *
import re


def cursos(nivel='graduacao', campus=DARCY_RIBEIRO):
    """Acessa o Matrícula Web e retorna um dicionário com a lista de cursos.
    Argumentos:
    nivel -- nível acadêmico dos cursos: graduacao ou posgraduacao.
             (default graduacao)
    campus -- o campus onde o curso é oferecido: DARCY_RIBEIRO, PLANALTINA,
              CEILANDIA ou GAMA
              (default DARCY_RIBEIRO)
    """

    url_cursos = url_mweb(nivel, 'curso_rel', campus)
    lib = Browser()
    #lib.open_chrome_browser(url_cursos)
    lib.open_headless_chrome_browser(url_cursos)

    list_cursos = {}
    try:
        locator_cursos = 'xpath:/html/body/section//table[@id="datatable"]/tbody/tr[position()>1]'
        for element in lib.find_elements(locator_cursos):
            row = [item.text for item in element.find_elements_by_tag_name('td')]
            modalidade, codigo, denominacao, turno = row
            list_cursos[codigo] = {}
            list_cursos[codigo]['Modalidade'] = modalidade
            list_cursos[codigo]['Denominação'] = denominacao
            list_cursos[codigo]['Turno'] = turno

    except: #RequestException as erro:
        print('erro em cursos')
        # print 'Erro ao buscar %s para %s em %d.\n%s' %
        #     (codigo, nivel, campus, erro)
    finally:
        lib.driver.close()

    return list_cursos


def disciplina(codigo, nivel='graduacao'):
    url_disciplinas = url_mweb(nivel, 'disciplina', codigo)
    #print(url_disciplinas)

    lib = Browser()
    #lib.open_chrome_browser(url_disciplinas)
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
    except: # RequestException as erro:
        print('erro em disciplina')
        # print 'Erro ao buscar %s para %s.\n%s' % (codigo, nivel, erro)
    finally:
        lib.driver.close()

    return disciplina


def habilitacao(codigo, nivel='graduacao'):
    """Acessa o Matrícula Web e retorna um dicionário com a lista de
    informações referentes a cada habilitação no curso.

    Argumentos:
    codigo -- o código do curso.
    nivel -- nível acadêmico do curso: graduacao ou posgraduacao.
             (default graduacao)
    """

    habilitacao_url = url_mweb(nivel, 'curso_dados', codigo)
    lib = Browser()
    #print(habilitacao_url)
    #lib.open_chrome_browser(habilitacao_url)
    lib.open_headless_chrome_browser(habilitacao_url)

    habilitacao = {}
    try:
        opcao_locator = 'xpath:/html/body/section//div[@class="body table-responsive"]//a'
        opcao_list = []
        for item in lib.find_elements(opcao_locator):
            opcao_url = item.get_property("href")
            opcao_match = re.search('=(\d+)$', opcao_url)
            opcao = opcao_match.group(1)
            #habilitacao[opcao] = {}
            opcao_list.append(opcao)

        table_locator = 'xpath:/html/body/section//table[@id="datatable"]'
        table_list = lib.find_elements(table_locator)

        for opcao, table in zip(opcao_list, table_list):
            habilitacao[opcao] = {}
            for line in table.find_elements_by_tag_name('tr'):
                th = line.find_element_by_tag_name('th')
                td = line.find_element_by_tag_name('td')
                title = th.text
                value = td.text
                habilitacao[opcao][title] = value
    except: # RequestException as erro:
        print('erro em habilitacao')
        #print 'Erro ao buscar %s para %s.\n%s' % (codigo, nivel, erro)
    finally:
       lib.driver.close()
    return habilitacao

def curriculo(codigo, nivel='graduacao'):
    """Acessa o Matrícula Web e retorna a lista de
    disciplinas definidas no curriculo do curso.

    Argumentos:
    codigo -- o código da habilitacao.
    nivel -- nível acadêmico do curso: graduacao ou posgraduacao.
             (default graduacao)
    """
    try:
        curriculo_url = url_mweb(nivel, 'curriculo', codigo)
        lib = Browser()
        #lib.open_chrome_browser(curriculo_url)
        lib.open_headless_chrome_browser(curriculo_url)
        main_locator = 'xpath://div[@class="body table-responsive"]'
        main_table = lib.find_element(main_locator)

        tipo_list = main_table.find_elements_by_xpath('//div[@class="panel panel-primary"]')
        tipo_list = [item.text for item in tipo_list]

        table_list = main_table.find_elements_by_class_name('table-responsive')[1:]

        curriculo = []
        for tipo, table in zip(tipo_list, table_list):
            lines = table.find_elements_by_tag_name('tr')
            titles = [item.text for item in lines[0].find_elements_by_tag_name('th')]
            for line_element in lines[1:]:
                line = [item.text for item in line_element.find_elements_by_tag_name('td')]
                disciplina = dict(zip(titles, line))
                disciplina['Tipo'] = tipo
                curriculo.append(disciplina)
    except:
        print('erro em curriculo')
    finally:
        lib.driver.close()
    return curriculo


# cursos_ = cursos()
# for c in cursos_:
#     print c, cursos_[c]

# d = disciplina(181196)
# for c in d:
#     print c, d[c]

# oferta = habilitacao(680)
# for h in oferta:
#     print h, oferta[h]

# periodos = fluxo(6912)  # 1856)
# for p in periodos:
#     print "Período ", p, periodos[p]
