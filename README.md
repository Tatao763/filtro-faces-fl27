# Filtro de faces — Football Life 27 (GitHub Actions)

## O que esta versão faz
Executa automaticamente a separação por ID sempre que você altera `faces.txt` ou `lendas_ids.txt`, ou quando inicia a ação manualmente no GitHub.

**Atenção:** esta versão ainda NÃO pesquisa na internet se o jogador se aposentou. Ela compara os IDs da lista com `lendas_ids.txt`. A verificação de aposentadoria precisa ser implementada e validada com fontes confiáveis antes de classificar automaticamente.

## Configuração
1. No GitHub, crie um repositório chamado `filtro-faces-fl27`.
2. Extraia o ZIP deste projeto no seu celular ou computador.
3. Envie todos os arquivos e pastas extraídos para o repositório. Ative a opção de mostrar arquivos ocultos para incluir `.github/workflows/filtrar.yml`.
4. Abra `faces.txt` e substitua o exemplo pela sua lista completa, mantendo o formato `ID - Nome`.
5. Em `lendas_ids.txt`, coloque um ID confirmado por linha. Não use IDs presumidos.
6. Salve/commit as alterações.

## Como executar
- Abra a aba **Actions** do repositório.
- Selecione **Filtrar faces do Football Life 27**.
- Clique em **Run workflow** e confirme.
- Quando terminar, abra a execução e baixe o arquivo `resultados-faces-fl27` em **Artifacts**.

Também executa automaticamente quando `faces.txt`, `lendas_ids.txt` ou `main.py` são alterados.

## Arquivos de saída
- `lendas_filtradas.txt`
- `outros_jogadores.txt`
- `linhas_para_corrigir.txt`
- `resumo.txt`

## Formato de entrada
`faces.txt`:
```text
12345 - Nome do jogador
12346 - Outro jogador
```

`lendas_ids.txt`:
```text
12345
```
