import curso

# Testa Cursos
# cursos = curso.cursos()
# for item in cursos:
#     print(item, cursos[item])


# # Testa Disciplina
# disciplina = curso.disciplina(100854)
# for item in disciplina:
#     print(item + ':', '\t', disciplina[item][:200] + '...')


# Testa Habilitação
habilitacao = curso.habilitacao(264)
for opcao, items in habilitacao.items():
    print('Habilitação:', opcao)
    for item in items:
        print('\t' + item + ':', '\t', items[item])
