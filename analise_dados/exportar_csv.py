"""
Copia o CSV de logs do backend ou baixa o export completo via API (SQLite).

Uso:
  python exportar_csv.py              # copia backend/rfid_access_log.csv (ou APP_CSV_PATH)
  python exportar_csv.py --api       # GET /v1/access-events/export.csv (servidor Flask ativo)
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
BACKEND_DIR = REPO_ROOT / "backend"
DEFAULT_LOCAL = Path(os.environ.get("APP_CSV_PATH", str(BACKEND_DIR / "rfid_access_log.csv")))
DEST = ROOT / "dados" / "access_events.csv"
DEFAULT_API = os.environ.get(
    "HYDRA_EXPORT_URL",
    "http://10.1.25.75:5173/v1/access-events/export.csv",
)


def copy_local(src: Path) -> None:
    if not src.is_file():
        print(f"Arquivo nao encontrado: {src}", file=sys.stderr)
        print(
            "Inicie o sistema para gerar logs ou use --api com o backend em execucao.",
            file=sys.stderr,
        )
        sys.exit(1)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, DEST)
    print(f"Copiado: {src} -> {DEST}")


def fetch_api(url: str) -> None:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
    except requests.RequestException as exc:
        print(f"Falha ao baixar {url}: {exc}", file=sys.stderr)
        sys.exit(1)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_bytes(r.content)
    print(f"Baixado: {url} -> {DEST}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta logs de acesso para analise_dados/dados/")
    parser.add_argument(
        "--api",
        action="store_true",
        help="Baixa CSV gerado a partir do banco (inclui coluna id, ordenacao completa).",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_API,
        help=f"URL do export CSV (padrao: {DEFAULT_API})",
    )
    parser.add_argument(
        "--origem",
        default=str(DEFAULT_LOCAL),
        help="Caminho do CSV local do leitor/backend (padrao: APP_CSV_PATH ou backend/rfid_access_log.csv)",
    )
    args = parser.parse_args()

    if args.api:
        fetch_api(args.url)
    else:
        copy_local(Path(args.origem))


if __name__ == "__main__":
    main()
