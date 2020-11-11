#  -*- coding: utf-8 -*-
#       @file: utils.py
#     @author: Guilherme N. Ramos (gnramos@unb.br)
#     @author: Thiago S. Nascimento
#
# Utilidades.

from RPA.Browser import Browser


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

    url = f'https://matriculaweb.unb.br/{nivel}/{pagina}.aspx?cod={cod}'

    return url


def lines_to_dict(lines, key_index):
    titles = [item.text for item in lines[0].find_elements_by_tag_name('th')]
    dict_object = {}
    for element in lines[1:]:  # skip title row
        line = [item.text for item in element.find_elements_by_tag_name('td')]
        key = line[key_index]
        dict_object[key] = dict(zip(titles, line))
        # TODO: remover a coluna que será usada como chave dos values (key_index)
    return dict_object


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
    try:
        lib.open_headless_chrome_browser(web_url)
        lines = lib.find_elements(table_lines_locator)
        dict_object = lines_to_dict(lines, key_index)
        return dict_object
    except Exception as e:
        # FIXME: Especificar exceção
        print(f'Ao buscar a expressão {table_lines_locator} na página {web_url}, '
              'ocorreu o seguinte erro: \n {e}')
        return None
    finally:
        lib.driver.close()


def write_attributes(attr_mapping, obj_instance, attributes):
    """

    Parameters
    ----------
    attr_mapping : dict
        A dictionary relating column names (as returned by the crawler) and the object properties names.
    obj_instance : Object
        An instance of an Object
    attributes : dict
        The dictionary returned by the crawler.
    -------
    """
    for column_name, attribute_value in attributes.items():
        property_name = attr_mapping[column_name]
        setattr(obj_instance, property_name, attribute_value)
