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


from utils import *


def cursos(codigo='\d+', nivel='graduacao', campus=DARCY_RIBEIRO):
    """Acessa o Matrícula Web e retorna um dicionário com a lista de cursos.

    Argumentos:
    codigo -- o código do curso
            (default \d+) (todos)
    nivel -- nível acadêmico dos cursos: graduacao ou posgraduacao.
             (default graduacao)
    campus -- o campus onde o curso é oferecido: DARCY_RIBEIRO, PLANALTINA,
              CEILANDIA ou GAMA
              (default DARCY_RIBEIRO)

    O argumento 'codigo' deve ser uma expressão regular.
    """

    """CURSOS = '<tr CLASS=PadraoMenor bgcolor=.*?>'\
             '<td>(\w+)</td>' \
             '<td>\d+</td>' \
             '.*?aspx\?cod=(%s)>(.*?)</a></td>' \
             '<td>(.*?)</td></tr>' % codigo"""

    CURSOS = '<tr>' \
             '<td>(\w+)</td>' \
             '<td>(%s)</td>' \
             r'<td><a href=curso_dados\.aspx\?cod=\2>([^<]+)</a></td>' \
             '<td>(\w+)</td>' \
             '</tr>' % codigo

    lista = {}
    try:
        pagina_html = busca(url_mweb(nivel, 'curso_rel', campus))
        print(pagina_html.url)
        # print(pagina_html.content.decode('utf-8'))
        print(CURSOS)
        cursos_existentes = encontra_padrao(CURSOS, pagina_html.content.decode('utf-8'))
        for modalidade, codigo, denominacao, turno in cursos_existentes:
            lista[codigo] = {}
            lista[codigo]['Modalidade'] = modalidade
            lista[codigo]['Denominação'] = denominacao
            lista[codigo]['Turno'] = turno
    except RequestException as erro:
        pass
        # print 'Erro ao buscar %s para %s em %d.\n%s' %
        #     (codigo, nivel, campus, erro)

    return lista


def disciplina(codigo, nivel='graduacao'):
    """Acessa o Matrícula Web e retorna um dicionário com as informações da
    disciplina.

    Argumentos:
    codigo -- o código da disciplina.
    nivel -- nível acadêmico da disciplina: graduacao ou posgraduacao.
             (default graduacao)
    """

    disciplina_parse_info = {
        'Departamento':     {'pattern': '<tr><th class=[^>]*>Órgão</th><td class=[^>]*>([^<]*)</td></tr>'},
        'Denominação':      {'pattern': '<tr><th>Denominação</th><td>([^<]*)</td></tr>'},
        'Nivel':            {'pattern': '<tr><th>Nível</th><td>([^<]*)</td></tr>'},
        'Vigência':         {'pattern': '<tr><th>Início da Vigência em</th><td>([^<]*)</td></tr>'},
        'Pré-requisitos':   {'pattern': '<tr><th>Pré-requisitos</th><td>(.*?)</td></tr>',
                             'replace': [['<br>', ' ']]},
        'Ementa':           {'pattern':
                                 '<tr><th rowspan=[^>]*>Ementa</th><td>Início da Vigência em <b>[^<]+</b></td></tr>'
                                 '<tr><td><p align=\w+>(.*?)</td></tr>',
                             'replace': [['<br />', '\n']]},
        'Programa':         {'pattern': '<tr><th rowspan=[^>]*>Programa</th><td>Início da Vigência em <b>[^<]+</b>'
                                        '</td></tr><tr><td><p align=\w+>(.*?)</td></tr>',
                             'replace': [['<br />', '\n']]},
        'Bibliografia':     {'pattern':
                                 '<tr><th rowspan=[^>]*>Bibliografia</th><td>Início da Vigência em <b>[^<]+</b></td>'
                                 '</tr><tr><td><p align=\w+>(.*?)</td></tr>',
                             'replace': [['<br />', '\n']]}
    }

    disc = {}
    try:
        pagina_html = busca(url_mweb(nivel, 'disciplina', codigo))
        content = pagina_html.content.decode('utf-8')
        content = content.replace('\n', '')
        content = content.replace('\r', '')
        for item, info in disciplina_parse_info.items():
            pattern = info['pattern']
            text = encontra_padrao(pattern, content)[0]
            if 'replace' in info:
                for r in info['replace']:
                    text = text.replace(r[0], r[1])
            disc[item] = text
            # replace_tags
    except RequestException as erro:
        pass
        # print 'Erro ao buscar %s para %s.\n%s' % (codigo, nivel, erro)

    return disc


def habilitacao(codigo, nivel='graduacao'):
    """Acessa o Matrícula Web e retorna um dicionário com a lista de
    informações referentes a cada habilitação no curso.

    Argumentos:
    codigo -- o código do curso.
    nivel -- nível acadêmico do curso: graduacao ou posgraduacao.
             (default graduacao)
    """
    OPCAO = '<a href=curriculo.aspx\?cod=(\d+)>' \
            '.*?' \
            'Grau: </td><td .*?>(\w+)</td>' \
            '.*?' \
            'Limite mínimo de permanência: </td>' \
            '<td align=right>(\d+)</td>' \
            '.*?' \
            'Limite máximo de permanência: </td>' \
            '<td align=right>(\d+)</td>' \
            '.*?' \
            'Quantidade de Créditos para Formatura: </td>' \
            '<td align=right>(\d+)</td>' \
            '.*?' \
            'Quantidade mínima de Créditos Optativos ' \
            'na Área de Concentração: </td>' \
            '<td align=right>(\d+)</td>' \
            '.*?' \
            'Quantidade mínima de Créditos Optativos na Área Conexa: </td>' \
            '<td align=right>(\d+)</td>' \
            '.*?' \
            'Quantidade máxima de Créditos no Módulo Livre: </td>' \
            '<td align=right>(\d+)</td>'

    curso = {}
    try:
        pagina_html = busca(url_mweb(nivel, 'curso_dados', codigo))
        oferta = encontra_padrao(OPCAO, pagina_html.content.decode('utf-8'))
        for opcao, grau, min, max, formatura, obr, opt, livre in oferta:
            curso[opcao] = {}
            curso[opcao]['Grau'] = grau
            curso[opcao]['Limite mínimo de permanência'] = min
            curso[opcao]['Limite máximo de permanência'] = max
            curso[opcao]['Quantidade de Créditos para Formatura'] = formatura
            curso[opcao]['Quantidade mínima de Créditos Optativos na Área de Concentração'] = obr
            curso[opcao]['Quantidade mínima de Créditos Optativos na Área Conexa'] = opt
            curso[opcao]['Quantidade máxima de Créditos no Módulo Livre'] = livre
    except RequestException as erro:
        pass
        # print 'Erro ao buscar %s para %s.\n%s' % (codigo, nivel, erro)

    return oferta


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
