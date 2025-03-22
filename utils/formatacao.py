import pandas as pd

def formatar_numero(numero):
    """
    Formata números grandes adicionando separadores de milhar.
    Se o número for NaN ou '-', retorna '-'.
    """
    if pd.isna(numero) or numero == "-":
        return "-"
    try:
        return f"{int(numero):,}".replace(",", ".")
    except (ValueError, TypeError):
        # Se não conseguir converter para inteiro, tenta formatar como float
        try:
            return f"{float(numero):,.2f}".replace(",", ".")
        except (ValueError, TypeError):
            return str(numero)

# Controla o que é exportado pelo módulo
__all__ = ['formatar_numero']