"""Dados do conteúdo inicial de demonstração (spec 0005).

As questões são conceituais e não descrevem a execução de sinais: a descrição de cada
sinal fica para a equipe completar pelo Admin.
"""

CATEGORIAS = {
    "Saudações": ("OUTROS", ["Oi", "Tchau", "Bom dia", "Obrigado", "Por favor"]),
    "Família": ("SUBSTANTIVO", ["Mãe", "Pai", "Irmão", "Avó", "Filho"]),
    "Cores": ("ADJETIVO", ["Azul", "Vermelho", "Verde", "Amarelo", "Branco"]),
}

MODULOS = [
    {
        "titulo": "Primeiros passos",
        "descricao": "O que é Libras, o alfabeto manual e as primeiras saudações.",
        "aulas": [
            {
                "titulo": "O que é Libras",
                "descricao": "A Língua Brasileira de Sinais, seu reconhecimento e sua gramática própria.",
                "questoes": [
                    ("O que significa a sigla Libras?", [
                        ("Língua Brasileira de Sinais", True),
                        ("Linguagem Brasileira de Símbolos", False),
                        ("Língua Básica de Sinais", False),
                    ]),
                    ("Como a Libras é reconhecida no Brasil pela Lei 10.436/2002?", [
                        ("Como meio legal de comunicação e expressão", True),
                        ("Como um conjunto de gestos sem valor de língua", False),
                        ("Como uma tradução palavra por palavra do português", False),
                    ]),
                    ("A Libras tem gramática própria?", [
                        ("Sim, com estrutura própria, diferente da do português", True),
                        ("Não, ela segue a gramática do português", False),
                        ("Não, ela tem apenas vocabulário", False),
                    ]),
                ],
            },
            {
                "titulo": "Alfabeto manual e saudações",
                "descricao": "A datilologia e os primeiros cumprimentos do dia a dia.",
                "questoes": [
                    ("Para que serve o alfabeto manual (datilologia)?", [
                        ("Para soletrar nomes e palavras que não têm um sinal conhecido", True),
                        ("Para substituir todos os sinais da Libras", False),
                        ("Para indicar apenas números", False),
                    ]),
                    ("No alfabeto manual, cada letra corresponde a:", [
                        ("Uma configuração de mão", True),
                        ("Uma expressão facial", False),
                        ("Um movimento do corpo inteiro", False),
                    ]),
                    ("Na tela da aula, a legenda do vídeo pode ser:", [
                        ("Ativada e desativada pelo aluno", True),
                        ("Lida só depois que o vídeo termina", False),
                        ("Usada apenas por administradores", False),
                    ]),
                ],
            },
        ],
    },
    {
        "titulo": "Família e pessoas",
        "descricao": "Membros da família, pronomes e como se apresentar.",
        "aulas": [
            {
                "titulo": "Membros da família",
                "descricao": "Sinais de parentesco e o uso do dicionário para revisar.",
                "questoes": [
                    ("Qual destes sinais está na categoria Família do dicionário?", [
                        ("Mãe", True),
                        ("Azul", False),
                        ("Obrigado", False),
                    ]),
                    ("Onde você pode rever um sinal a qualquer momento, fora da trilha?", [
                        ("No dicionário de sinais", True),
                        ("Apenas no questionário", False),
                        ("Em nenhum lugar da plataforma", False),
                    ]),
                    ("Em Libras, as expressões faciais:", [
                        ("Fazem parte da língua e podem mudar o sentido do que é dito", True),
                        ("Devem ser evitadas", False),
                        ("Não têm importância", False),
                    ]),
                ],
            },
            {
                "titulo": "Pronomes e apresentação",
                "descricao": "Apontar para pessoas, dizer o próprio nome e o sinal pessoal.",
                "questoes": [
                    ("Em Libras, apontar para uma pessoa presente costuma indicar:", [
                        ("Um pronome, como ele, ela ou você", True),
                        ("Um número", False),
                        ("Uma cor", False),
                    ]),
                    ("Para dizer o próprio nome ao se apresentar, usa-se:", [
                        ("O alfabeto manual ou o sinal pessoal", True),
                        ("Apenas a escrita em papel", False),
                        ("Somente expressões faciais", False),
                    ]),
                    ("O sinal pessoal (sinal de nome) costuma ser:", [
                        ("Atribuído por pessoas surdas da comunidade", True),
                        ("Escolhido por sorteio", False),
                        ("Igual para todas as pessoas", False),
                    ]),
                ],
            },
        ],
    },
    {
        "titulo": "Cores e cotidiano",
        "descricao": "Cores, números e os parâmetros que formam um sinal.",
        "aulas": [
            {
                "titulo": "Cores",
                "descricao": "Sinais de cores e a classe gramatical no dicionário.",
                "questoes": [
                    ("Qual destes sinais está na categoria Cores do dicionário?", [
                        ("Azul", True),
                        ("Pai", False),
                        ("Tchau", False),
                    ]),
                    ("Qual é a classe gramatical das cores no dicionário da plataforma?", [
                        ("Adjetivo", True),
                        ("Verbo", False),
                        ("Advérbio", False),
                    ]),
                    ("Quais são os parâmetros que formam um sinal em Libras?", [
                        ("Configuração de mão, ponto de articulação, movimento, orientação e expressões não manuais", True),
                        ("Apenas a configuração de mão", False),
                        ("Apenas o movimento", False),
                    ]),
                ],
            },
            {
                "titulo": "Números de 1 a 10",
                "descricao": "Os números em Libras e como concluir as aulas da trilha.",
                "questoes": [
                    ("Os números em Libras:", [
                        ("Têm sinais próprios", True),
                        ("São sempre escritos no ar com o dedo", False),
                        ("Não existem em Libras", False),
                    ]),
                    ("Para concluir uma aula na plataforma, é preciso:", [
                        ("Acertar ao menos 70% das questões do questionário", True),
                        ("Assistir ao vídeo três vezes", False),
                        ("Baixar todos os materiais", False),
                    ]),
                    ("Se você não atingir 70% no questionário, pode:", [
                        ("Tentar de novo quantas vezes quiser", True),
                        ("Tentar só mais uma vez", False),
                        ("Esperar um dia para tentar de novo", False),
                    ]),
                ],
            },
        ],
    },
]
