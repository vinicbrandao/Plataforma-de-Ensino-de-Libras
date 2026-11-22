# Amostras para o conteúdo inicial

Esta pasta guarda os vídeos e as legendas usados por `python manage.py criar_conteudo_inicial` ([spec 0005](../docs/specs/0005-conteudo-inicial.md)). Os arquivos não vão para o Git: só este LEIA-ME é versionado.

Se faltar algum arquivo, o comando cria o que der, deixa não publicada a aula sem vídeo ou legenda, não cria o sinal sem vídeo e lista o que falta. Depois de colocar os arquivos, rode o comando de novo: ele anexa o que faltava e publica as aulas completas, sem duplicar nada.

## Formatos

- Vídeos: **MP4**. Até 200 MB por aula e 20 MB por sinal. O vídeo de sinal deve ser curto e sem áudio, porque toca em loop no dicionário.
- Legendas: **WebVTT (.vtt)**, em português, começando com a linha `WEBVTT`. Legendas `.srt` não são aceitas.
- Os nomes precisam ser exatamente os listados abaixo: minúsculas, sem acentos e com hífen no lugar do espaço.

## Aulas (`amostras/aulas/`): 12 arquivos

| Arquivo do vídeo | Arquivo da legenda | Módulo | Aula |
|---|---|---|---|
| `m1-a1.mp4` | `m1-a1.vtt` | Primeiros passos | O que é Libras |
| `m1-a2.mp4` | `m1-a2.vtt` | Primeiros passos | Alfabeto manual e saudações |
| `m2-a1.mp4` | `m2-a1.vtt` | Família e pessoas | Membros da família |
| `m2-a2.mp4` | `m2-a2.vtt` | Família e pessoas | Pronomes e apresentação |
| `m3-a1.mp4` | `m3-a1.vtt` | Cores e cotidiano | Cores |
| `m3-a2.mp4` | `m3-a2.vtt` | Cores e cotidiano | Números de 1 a 10 |

## Sinais (`amostras/sinais/`): 15 arquivos

| Categoria | Arquivos |
|---|---|
| Saudações | `oi.mp4`, `tchau.mp4`, `bom-dia.mp4`, `obrigado.mp4`, `por-favor.mp4` |
| Família | `mae.mp4`, `pai.mp4`, `irmao.mp4`, `avo.mp4`, `filho.mp4` |
| Cores | `azul.mp4`, `vermelho.mp4`, `verde.mp4`, `amarelo.mp4`, `branco.mp4` |

## Estrutura final

```text
amostras/
├── LEIA-ME.md
├── aulas/
│   ├── m1-a1.mp4
│   ├── m1-a1.vtt
│   └── ... (até m3-a2)
└── sinais/
    ├── oi.mp4
    └── ... (15 arquivos)
```
