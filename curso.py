# modificar a funcao cursos para pegar automaticamente o titulo da coluna
# montar grafo de dependencias das disciplinas





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
# precisa modificar para reconhecer mais de uma habilitacao
    habilitacao_url = url_mweb(nivel, 'curso_dados', codigo)
    lib = Browser()
    #print(habilitacao_url)
    #lib.open_chrome_browser(habilitacao_url)
    lib.open_headless_chrome_browser(habilitacao_url)

    habilitacao = {}
    # try:
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
    # except: # RequestException as erro:
    #     print('erro em habilitacao')
    #     #print 'Erro ao buscar %s para %s.\n%s' % (codigo, nivel, erro)
    # finally:
    #    lib.driver.close()
    return habilitacao


def fluxo(codigo, nivel='graduacao'):
    """Acessa o Matrícula Web e retorna um dicionário com a lista de
    disciplinas por período definidas no fluxo do curso.

    Argumentos:
    codigo -- o código do curso.
    nivel -- nível acadêmico do curso: graduacao ou posgraduacao.
             (default graduacao)
    """
    PERIODO = '<b>PERÍODO: (\d+).*?CRÉDITOS:</b> (\d+)</td>(.*?)</tr></table>'
    DISCIPLINA = 'disciplina.aspx\?cod=\d+>(\d+)</a>'

    curso = {}
    try:
        pagina_html = busca(url_mweb(nivel, 'fluxo', codigo))
        oferta = encontra_padrao(PERIODO, pagina_html.content.decode('utf-8'))
        for periodo, creditos, dados in oferta:
            curso[periodo] = {}
            curso[periodo]['Créditos'] = creditos
            curso[periodo]['Disciplinas'] = encontra_padrao(DISCIPLINA, dados)
    except RequestException as erro:
        pass
        # print 'Erro ao buscar %s para %s.\n%s' % (codigo, nivel, erro)

    return curso

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
