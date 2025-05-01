# data_io.py  ─────────────────────────────────────────────
import os, io, pandas as pd, streamlit as st

# ── FUNÇÃO DE CARGA ──────────────────────────────────────
@st.cache_data(ttl=3600)
def load_parquets():
    """Carrega e tipa os três .parquet esperados; retorna (escola, uf, mun)."""
    paths = {
        "escolas": "escolas.parquet",
        "estado":  "estado.parquet",
        "municipio":"municipio.parquet",
    }
    if not all(os.path.exists(p) for p in paths.values()):
        st.error("Arquivos .parquet não encontrados."); st.stop()

    dfs = {k: pd.read_parquet(p) for k, p in paths.items()}

    for df in dfs.values():
        for col in df.columns:
            if col.startswith("Número de"):
                df[col] = pd.to_numeric(df[col], errors="coerce")
            elif col in ("ANO", "CODIGO DO MUNICIPIO",
                         "CODIGO DA ESCOLA", "CODIGO DA UF"):
                df[col] = df[col].astype(str)
    return dfs["escolas"], dfs["estado"], dfs["municipio"]

# ── EXPORTAÇÕES CACHEADAS ─────────────────────────────────
@st.cache_data
def df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data
def df_to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as wr:
        df.to_excel(wr, index=False, sheet_name="Dados")
        ws, wb = wr.sheets["Dados"], wr.book
        header = wb.add_format(
            {"bold": True, "text_wrap": True, "valign": "top",
             "fg_color": "#364b60", "font_color": "white", "border": 1}
        )
        for c, name in enumerate(df.columns):
            ws.write(0, c, name, header)
            ws.set_column(c, c, max(len(name), 12))
    return buf.getvalue()
