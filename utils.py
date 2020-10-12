#  -*- coding: utf-8 -*-
#       @file: utils.py
#     @author: Guilherme N. Ramos (gnramos@unb.br)
#     @author: Thiago S. Nascimento
#
# Utilidades.

from RPA.Browser import Browser
from objects import *


# Códigos dos campi
DARCY_RIBEIRO = 1
PLANALTINA = 2
CEILANDIA = 3
GAMA = 4


def url_mweb(nivel, pagina, cod):
    """
    Constrói links para o Matrícula Web

    Parameters
    ----------
    nivel : str
        Nível do ensino: graduacao ou posgraduacao
    pagina : str
        Nome da pagina, p. ex. : disciplina, oferta_dep, oferta_dis, curso_dados, curriculo
    cod : str
        Código do item

    Returns
    -------
    str
        URL
    """

    url = f'https://matriculaweb.unb.br/{nivel}/{pagina}.aspx?cod={str(cod)}'

    return url


def table_to_dict(web_url, table_lines_locator, key_index=0):
    """Acessa uma página, localiza uma tabela e a retorna como um dicionário.

    Parameters
    ----------
    web_url : str
        Endereço da página que contém a tabela
    table_lines_locator : str
        XPath Locator da tabela
    key_index : int, optional
        Índice da coluna que será usada como chave do dicionário (default is 0)

    Returns
    -------
    dict
        Um dicionário contendo as linhas da tabela
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



