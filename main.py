from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import csv
import io
import json
import re
import time

FACES = Path("faces.txt")
ENDPOINT = "https://query.wikidata.org/sparql"
CHUNK_SIZE = 40
SLEEP_SECONDS = 1.2
CONTINENTES = {"Europa", "América do Norte", "América do Sul", "América"}

def link_transfermarkt(nome):
    return "https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?" + urlencode({"query": nome})

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
    for id_, nome in jogadores:
        resultados = por_nome.get(nome.casefold(), [])
        unicos = {(r["clube"], r["pais"], r["continente"], r["wikidata"]) for r in resultados}
        if len(unicos) == 1:
            clube, pais, continente, entidade = next(iter(unicos))
            candidatos.append((id_, nome, clube, pais, continente, entidade))
        elif len(unicos) > 1:
            pendentes.append((id_, nome, "Mais de um resultado possível no Wikidata"))
        else:
            pendentes.append((id_, nome, "Sem vínculo atual confirmado no Wikidata"))

    with open("jogadores_europa_americas.txt", "w", encoding="utf-8", newline="") as arquivo:
        arquivo.write("ID - Nome | Clube | País | Continente | Wikidata\n")
        for id_, nome, clube, pais, continente, entidade in candidatos:
            arquivo.write(f"{id_} - {nome} | {clube} | {pais} | {continente} | {entidade}\n")

    with open("transfermarkt_conferencia.csv", "w", encoding="utf-8-sig", newline="") as arquivo:
        writer = csv.writer(arquivo, delimiter=";")
        writer.writerow(["ID original", "Jogador", "Clube/país sugeridos pelo Wikidata", "Conferir no Transfermarkt"])
        for id_, nome, clube, pais, continente, entidade in candidatos:
            writer.writerow([id_, nome, f"{clube} / {pais} / {continente}", link_transfermarkt(nome)])
        for id_, nome, motivo in pendentes:
            writer.writerow([id_, nome, motivo, link_transfermarkt(nome)])

    with open("pendentes_revisao.txt", "w", encoding="utf-8") as arquivo:
        arquivo.write("ID - Nome | Motivo | Busca Transfermarkt\n")
        for i, n, motivo in pendentes:
            arquivo.write(f"{i} - {n} | {motivo} | {link_transfermarkt(n)}\n")

    Path("resumo.txt").write_text(
        f"Total de faces lidas: {len(jogadores)}\n"
        f"Candidatos encontrados pelo Wikidata: {len(candidatos)}\n"
        f"Pendentes de revisão: {len(pendentes)}\n"
        "O CSV inclui uma busca do Transfermarkt para cada jogador, para conferência manual.\n"
        "O Transfermarkt não é consultado automaticamente; confirme clube e situação atual no site.\n"
        "Vínculo sem data final no Wikidata não prova, sozinho, que o jogador continua ativo.\n",
        encoding="utf-8"
    )
    print(Path("resumo.txt").read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()
