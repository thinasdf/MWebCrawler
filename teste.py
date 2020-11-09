import curso
import oferta
from utils import *

#Testa Cursos
# cursos = curso.cursos()
# for item in cursos:
#     print(item, cursos[item])


# # Testa Disciplina
# disciplina = curso.disciplina(100854)
# for item in disciplina:
#     print(item + ':', '\t', disciplina[item][:200] + '...')
#
#
# # Testa Habilitação
# habilitacao = curso.habilitacao(264)
# for opcao, items in habilitacao.items():
#     print('Habilitação:', opcao)
#     for item in items:
#         print('\t' + item + ':', '\t', items[item])


# # Testa Curriculo
# curriculo = curso.curriculo(3841)
# for disciplina in curriculo:
#     print(disciplina)


# # Testa Departamentos
# departamentos = oferta.departamentos()
# for codigo in departamentos:
#     print(codigo)
#     print('\t', departamentos[codigo])


# # Testa disciplinas do departamento
# disciplinas = oferta.disciplinas('383')
# for d in disciplinas:
#     print(d)
#     print('\t', disciplinas[d])


nivel = 'graduacao'
campus = DARCY_RIBEIRO
url = url_mweb(nivel, 'oferta_dep', campus)
print(url)