# ======================  utils.py  ======================
import pandas as pd


def beautify(col: str) -> str:
    """Transforma 'CODIGO DO MUNICIPIO' -> 'Codigo Do Municipio'."""
    col = col.replace("\n", " ").strip()
    return " ".join(p.capitalize() for p in col.lower().split())


def format_number_br(num):
    """6883 -> '6.883'  |  1234.5 -> '1.234,50'. Retorna '-' p/ NaN."""
    if pd.isna(num) or num == "-":
        return "-"
    try:
        n = float(num)
        if n.is_integer():
            return f"{int(n):,}".replace(",", ".")
        inteiro, frac = str(f"{n:,.2f}").split(".")
        return f"{inteiro.replace(',', '.')},{frac}"
    except Exception:
        return str(num)
