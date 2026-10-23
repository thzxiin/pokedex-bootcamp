# Pokédex — Catálogo e favoritos

Aplicação acadêmica do Bootcamp II para buscar Pokémon por nome ou número e manter uma coleção de favoritos em banco SQLite real.

> Antes de entregar: substitua todos os campos `PREENCHER` e `SEU_USUARIO_DOCKER`, inclua evidências reais e atualize o status abaixo. Este README ainda é um modelo de entrega, não uma declaração de publicação concluída.

## Identificação e participação

Repositório público: PREENCHER_URL_REPOSITORIO

| Nome completo | Matrícula | GitHub | Responsabilidade | PR principal |
|---|---|---|---|---|
| PREENCHER_NOME | PREENCHER_MATRICULA | PREENCHER_USUARIO | Interface, backend, integração PokéAPI, persistência, testes e Docker | PREENCHER_URL_PR |

Execução individual. Não houve revisão por outro integrante; o requisito de colaboração em grupo não foi cumprido. A aplicação foi preparada com auxílio de IA e deve ser estudada, executada e validada pelo autor antes da entrega. Registre aqui qualquer orientação específica recebida do professor: PREENCHER_OU_INFORMAR_NAO_HOUVE.

## Funcionalidades

- Busca por nome ou número, com validação e mensagem para Pokémon inexistente.
- Exibição de imagem, tipos, altura e peso.
- Inclusão de favoritos sem duplicação, listagem e exclusão.
- Dados persistentes após reiniciar o backend.
- Mensagens para falha de rede ou indisponibilidade da API.
- Interface responsiva em HTML, CSS e JavaScript.

## Arquitetura e banco

Navegador → backend HTTP Python → PokéAPI / SQLite.

O navegador usa endpoints do backend; o backend consulta `https://pokeapi.co/api/v2/pokemon/{nome-ou-id}`. Não há chave de API. A API tem função direta no catálogo: fornece os dados que são salvos nos favoritos. Os testes simulam suas respostas para não depender de internet no CI.

SQLite: tabela `favorites`, com `id INTEGER PRIMARY KEY` e `payload TEXT NOT NULL` contendo JSON do Pokémon. SQL parametrizado evita interpolação de entradas. O arquivo padrão é `data/pokedex.sqlite3`; não é localStorage. O banco é criado automaticamente. Listar/excluir favoritos funciona sem acesso à PokéAPI; buscar/salvar exige conexão. Imagens externas podem não carregar offline.

A coleção é única para esta instância, sem login. O servidor da biblioteca padrão é destinado à demonstração acadêmica local, não a produção pública.

## Executar localmente

Requer Python 3.12 ou superior com SQLite. Não há pacotes Python externos para instalar.

Após clonar o repositório, entre na pasta que contém `app.py`:

```bash
python3 app.py
```

Windows: use `python app.py`, se o executável se chamar `python`.

Abra **http://localhost:8000**. Para encerrar, use `Ctrl+C` no terminal.

Variáveis opcionais: `HOST` (padrão `127.0.0.1`), `PORT` (padrão `8000`) e `DB_PATH` (caminho do banco). No Docker esses valores já estão configurados. Nenhuma senha é necessária.

## Testes

```bash
python3 -m unittest discover -s tests -v
```

São 13 testes automatizados: normalização; rejeição de entradas; IDs/nomes compostos; criar/listar/excluir; duplicação; persistência após reinicialização; exclusão inexistente; mapeamento da API; 404 externo; indisponibilidade externa; página/health; fluxo HTTP completo; entradas e rotas inválidas.

Workflow: `.github/workflows/ci.yml`. Executa em pushes para `main` e PRs destinadas a `main`; o job se chama `testes`. Configure esse check como obrigatório na proteção da branch — apenas ter o arquivo do workflow não bloqueia merge.

## Docker

Requer Docker em execução. Para construir localmente, na pasta do projeto:

```bash
docker build -t pokedex-bootcamp:local .
docker run --rm --name pokedex-local -p 127.0.0.1:8000:8000 -v pokedex-dados:/app/data pokedex-bootcamp:local
```

Imagem pública no Docker Hub: PREENCHER_URL_DOCKER_HUB

Após a publicação, este é o comando completo (troque o usuário antes de entregar):

```bash
docker run --rm --name pokedex -p 127.0.0.1:8000:8000 -v pokedex-dados:/app/data SEU_USUARIO_DOCKER/pokedex-bootcamp:1.0
```

Abra **http://localhost:8000**. O volume `pokedex-dados` preserva a coleção mesmo após remover o container. Para encerrar: `Ctrl+C`. Não execute os servidores local e Docker na mesma porta simultaneamente. A imagem não precisa de variáveis adicionais; `HOST=0.0.0.0`, `PORT=8000` e `DB_PATH=/app/data/pokedex.sqlite3` estão definidos no Dockerfile.

## Evidências e resultados

| Verificação | Status / evidência real |
|---|---|
| Testes locais | 13 testes aprovados no ambiente de preparação; executar novamente no computador do autor |
| Aplicação local, busca real e persistência | PREENCHER_RESULTADO_E_LINK |
| PR com implementação real | PREENCHER_URL_PR |
| Execução CI com sucesso | PREENCHER_URL_EXECUCAO |
| Proteção da main / check obrigatório | PREENCHER_URL_IMAGEM |
| PR bloqueada por teste falhando | PREENCHER_URL_PR_E_IMAGEM_DO_BLOQUEIO |
| Correção posterior e CI aprovado | PREENCHER_URL_COMMIT_E_EXECUCAO |
| Docker Hub público e execução por pull | PREENCHER_URL_E_RESULTADO |
| Conflito de merge | PREENCHER_RELATO_REAL; se não houve, escrever “Não houve conflito de merge.” |

Inclua imagens com URLs absolutas públicas do próprio repositório para que o README também funcione fora dele, no Moodle. Não declare evidências que não foram executadas.

## Estrutura

- `app.py`: backend, acesso à PokéAPI e SQLite.
- `static/`: interface do usuário.
- `tests/test_app.py`: testes unitários e integração HTTP.
- `.github/workflows/ci.yml`: integração contínua.
- `Dockerfile`: imagem da aplicação.
- `docs/evidencias/`: capturas reais da execução.
- `COMECE-AQUI.md`: roteiro de configuração e entrega.

## Limites da validação no ambiente de preparação

Os 13 testes automatizados passaram. Após ajustar o endereço com barra final e identificar a requisição com User-Agent e Accept, a consulta real à PokéAPI retornou Pikachu (ID 25) com sucesso no ambiente de preparação. Confirmar também no computador do autor. Docker não está instalado neste ambiente, portanto construção, publicação e execução da imagem ainda precisam ser validadas. Nenhum repositório, PR ou imagem Docker Hub foi publicado na preparação.

## Referências

- PokéAPI: https://pokeapi.co/docs/v2
- Proteção de branches: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
