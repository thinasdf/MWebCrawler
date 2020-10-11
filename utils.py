#  -*- coding: utf-8 -*-
#       @file: utils.py
#     @author: Guilherme N. Ramos (gnramos@unb.br)
#
# Utilidades.

#from requests import get as busca
#from requests.exceptions import RequestException as RequestException
#from re import findall as encontra_padrao
#from re import match
from RPA.Browser import Browser

# Construção de links para o Matrícula Web.
mweb = lambda nivel: 'https://matriculaweb.unb.br/' + str(nivel)
link = lambda pagina, cod: str(pagina) + '.aspx?cod=' + str(cod)
url_mweb = lambda nivel, pagina, cod: mweb(nivel) + '/' + link(pagina, cod)


def table_to_dict(web_url, table_lines_locator, key_index=0):
    """Acessa uma página, localiza uma tabela e a retorna como um dicionário.

    Argumentos:
    web_url -- o código do Departamento que oferece as disciplinas.
    table_lines_locator -- XPath Locator string.
    key_index -- índice da coluna que será usada como chave do dicionário.
                 (default 0)
    """

    lib = Browser()
    dict_object = {}
    try:
        lib.open_headless_chrome_browser(web_url)

        lines = lib.find_elements(table_lines_locator)

        titles = [item.text for item in lines[0].find_elements_by_tag_name('th')]
        del titles[key_index]  # remove key element

        for element in lines[1:]:  # skip title row
            line = [item.text for item in element.find_elements_by_tag_name('td')]
            key = line.pop(key_index)  # remove key element
            dict_object[key] = dict(zip(titles, line))
    except:
        print('erro em table_to_dict')
    finally:
        lib.driver.close()
    return dict_object


# Códigos dos campi
DARCY_RIBEIRO = 1
PLANALTINA = 2
CEILANDIA = 3
GAMA = 4
