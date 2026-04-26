"""PNCP API fetch utilities (curl-based, no httpx dependency)."""

import sys
import json
import re
import io
import subprocess
from pathlib import Path

import pdfplumber

API_BASE  = "https://pncp.gov.br/api/consulta/v1"
PDF_BASE  = "https://pncp.gov.br/api/pncp/v1"
PAGE_SIZE = 10
MIN_CHARS = 5000


def _curl(url: str, extra: list[str] | None = None) -> bytes | None:
    cmd = ["curl", "-sL", "--max-time", "30", "-H", "User-Agent: Mozilla/5.0"]
    if extra:
        cmd.extend(extra)
    cmd.append(url)
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=35)
        return r.stdout if r.returncode == 0 else None
    except Exception as e:
        print(f"    [curl] {e}", file=sys.stderr)
        return None


def fetch_contracts(date_str: str, page: int) -> tuple[list[dict], int]:
    url  = (f"{API_BASE}/contratos?dataInicial={date_str}&dataFinal={date_str}"
            f"&pagina={page}&tamanhoPagina={PAGE_SIZE}")
    data = _curl(url, ["-H", "Accept: application/json"])
    if not data:
        return [], 0
    try:
        d = json.loads(data)
        return d.get("data", []), d.get("totalRegistros", 0)
    except Exception as e:
        print(f"    [json] {e}", file=sys.stderr)
        return [], 0


def fetch_edital(cnpj: str, year: int, seq: int) -> bytes | None:
    data = _curl(f"{PDF_BASE}/orgaos/{cnpj}/compras/{year}/{seq}/arquivos/1")
    return data if (data and data[:4] == b"%PDF") else None


def extract_pdf(pdf_bytes: bytes) -> str | None:
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            texts = [p.extract_text() for p in pdf.pages[:20] if p.extract_text()]
            text  = re.sub(r"\s+", " ", " ".join(texts)).strip()
            return text if len(text) >= MIN_CHARS else None
    except Exception:
        return None


def parse_compra_ref(item: dict) -> tuple[str, int, int] | None:
    ref   = item.get("numeroControlePncpCompra", "")
    parts = ref.split("-") if ref else []
    if len(parts) < 3:
        return None
    seq_ano = parts[-1]
    if "/" not in seq_ano:
        return None
    seq_str, ano_str = seq_ano.split("/")
    try:
        return parts[0], int(ano_str), int(seq_str)
    except ValueError:
        return None


def is_good(item: dict) -> bool:
    valor = item.get("valorGlobal") or item.get("valorInicial") or 0
    return not (valor and valor < 50_000)
