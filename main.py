from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import re
import time

FACES = Path("faces.txt")
ENDPOINT = "https://query.wikidata.org/sparql"
CHUNK_SIZE = 40
SLEEP_SECONDS = 1.2
CONTINENTES = {"Europa", "América do Norte", "América do Sul", "América"}

def ler_faces():
    jogadores = []
    for linha in FACES.read_text(encoding="utf-8-sig").splitlines():
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s*(\d+)\s*(?:[-–:;]|\s)\s*(.*)$", linha)
        if m:
            jogadores.append((m.group(1), m.group(2).strip()))
    return jogadores

def chunks(lista, tamanho):
    for i in range(0, len(lista), tamanho):
        yield lista[i:i + tamanho]

def consulta_wikidata(nomes):
    valores = " ".join(json.dumps(nome, ensure_ascii=False) for nome in nomes)
    query = f"""
    SELECT DISTINCT ?nome ?jogador ?clubeLabel ?paisLabel ?continenteLabel WHERE {{
      VALUES ?nome {{ {valores} }}
      ?jogador rdfs:label ?nome;
               wdt:P106/wdt:P279* wd:Q937857;
               p:P54 ?vinculo.
      FILTER(LANG(?nome) IN ("en","pt","es","fr","de","it"))
      ?vinculo ps:P54 ?clube.
      FILTER NOT EXISTS {{ ?vinculo pq:P582 ?fim. }}
      FILTER NOT EXISTS {{ ?jogador wdt:P570 ?falecimento. }}
      ?clube wdt:P17 ?pais.
      ?pais wdt:P30 ?continente.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "pt,en,es". }}
    }}
    """
    params = urlencode({"query": query, "format": "json"})
    req = Request(
        ENDPOINT + "?" + params,
        headers={"User-Agent": "FootballLife27FaceFilter/1.0 (GitHub Actions)", "Accept": "application/sparql-results+json"}
    )
    with urlopen(req, timeout=90) as resposta:
        dados = json.loads(resposta.read().decode("utf-8"))
    encontrados = {}
    for item in dados["results"]["bindings"]:
        nome = item["nome"]["value"]
        continente = item["continenteLabel"]["value"]
        if continente in CONTINENTES or "America" in continente or "América" in continente:
            encontrados.setdefault(nome.casefold(), []).append({
                "clube": item.get("clubeLabel", {}).get("value", "Clube não identificado"),
                "pais": item.get("paisLabel", {}).get("value", "País não identificado"),
                "continente": continente,
                "wikidata": item["jogador"]["value"]
            })
    return encontrados

def main():
    if not FACES.exists():
        raise SystemExit("O arquivo faces.txt não foi encontrado.")

    jogadores = ler_faces()
    por_nome = {}
    pendentes = []
    for lote in chunks(jogadores, CHUNK_SIZE):
        nomes = list(dict.fromkeys(nome for _, nome in lote if nome))
        try:
            por_nome.update(consulta_wikidata(nomes))
        except Exception as erro:
            pendentes.extend((id_, nome, f"Erro na consulta: {erro}") for id_, nome in lote)
        time.sleep(SLEEP_SECONDS)

    candidatos = []
    ids_com_candidato = set()
    for id_, nome in jogadores:
        resultados = por_nome.get(nome.casefold(), [])
        unicos = {(r["clube"], r["pais"], r["continente"], r["wikidata"]) for r in resultados}
        if len(unicos) == 1:
            clube, pais, continente, entidade = next(iter(unicos))
            candidatos.append(f"{id_} - {nome} | {clube} | {pais} | {continente} | {entidade}")
            ids_com_candidato.add(id_)
        elif len(unicos) > 1:
            pendentes.append((id_, nome, "Mais de um resultado possível no Wikidata"))
        else:
            pendentes.append((id_, nome, "Sem vínculo atual confirmado no Wikidata"))

    Path("jogadores_europa_americas.txt").write_text(
        "ID - Nome | Clube | País | Continente | Wikidata\n" + "\n".join(candidatos) + ("\n" if candidatos else ""),
        encoding="utf-8"
    )
    Path("pendentes_revisao.txt").write_text(
        "ID - Nome | Motivo\n" + "\n".join(f"{i} - {n} | {motivo}" for i, n, motivo in pendentes),
        encoding="utf-8"
    )
    Path("resumo.txt").write_text(
        f"Total de faces lidas: {len(jogadores)}\n"
        f"Candidatos encontrados (precisam de conferência): {len(candidatos)}\n"
        f"Pendentes de revisão: {len(pendentes)}\n"
        "Atenção: vínculo sem data final no Wikidata não prova, sozinho, que o jogador continua ativo.\n",
        encoding="utf-8"
    )
    print(Path("resumo.txt").read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()
