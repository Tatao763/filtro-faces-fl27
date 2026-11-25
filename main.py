from pathlib import Path
import re

FACES = Path("faces.txt")
LENDAS_IDS = Path("lendas_ids.txt")

def carregar_ids():
    resultado = set()
    for linha in LENDAS_IDS.read_text(encoding="utf-8-sig").splitlines():
        m = re.match(r"^\s*(\d+)", linha.strip())
        if m:
            resultado.add(int(m.group(1)))
    return resultado

def main():
    if not FACES.exists() or not LENDAS_IDS.exists():
        raise SystemExit("Crie faces.txt e lendas_ids.txt antes de executar.")

    ids_lendas = carregar_ids()
    lendas, outros, invalidas = [], [], []

    for linha in FACES.read_text(encoding="utf-8-sig").splitlines():
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s*(\d+)\s*(?:[-–:;]|\s)\s*(.*)$", linha)
        if not m:
            invalidas.append(linha)
            continue
        face_id, nome = int(m.group(1)), m.group(2).strip()
        (lendas if face_id in ids_lendas else outros).append(f"{face_id} - {nome}")

    Path("lendas_filtradas.txt").write_text("\n".join(lendas) + ("\n" if lendas else ""), encoding="utf-8")
    Path("outros_jogadores.txt").write_text("\n".join(outros) + ("\n" if outros else ""), encoding="utf-8")
    Path("linhas_para_corrigir.txt").write_text("\n".join(invalidas) + ("\n" if invalidas else ""), encoding="utf-8")

    ids = [int(x.split(" - ", 1)[0]) for x in lendas]
    resumo = [
        f"Faces classificadas como lendas: {len(lendas)}",
        f"Outras faces: {len(outros)}",
        f"Linhas para corrigir: {len(invalidas)}",
        f"Maior ID classificado como lenda: {max(ids) if ids else 'nenhum'}",
    ]
    Path("resumo.txt").write_text("\n".join(resumo) + "\n", encoding="utf-8")
    print("\n".join(resumo))

if __name__ == "__main__":
    main()
