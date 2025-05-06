# data_io.py ──────────────────────────────────────────────────────────
import os, io, pandas as pd, streamlit as st

ARQUIVO_UNICO = "dados.parquet"        # deixe o nome aqui se mudar de pasta

# ── FUNÇÃO DE CARGA ──────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Carregando dados.parquet…")
def load_parquets():
    """
    Lê o arquivo único (dados.parquet), faz o tratamento de tipos e
    devolve três DataFrames separados por nível de agregação:
    (escolas_df, estado_df, municipio_df)
    """
    if not os.path.exists(ARQUIVO_UNICO):
        st.error(f"Arquivo {ARQUIVO_UNICO} não encontrado."); st.stop()

    df = pd.read_parquet(ARQUIVO_UNICO)

    # tipos: numéricos e textos
    df["Nível de agregação"] = df["Nível de agregação"].str.lower()
    df["Ano"] = df["Ano"].astype(str)

    for col in df.columns:
        if col.startswith("Número de"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ALIAS p/ compatibilidade com o dicionário de etapas
    if ("Número de Matrículas" in df.columns and
        "Número de Matrículas da Educação Básica" not in df.columns):
        df["Número de Matrículas da Educação Básica"] = df["Número de Matrículas"]

    # separa pelos níveis que o parquet traz
    escolas_df   = df[df["Nível de agregação"] == "escola"].copy()
    municipio_df = df[df["Nível de agregação"] == "município"].copy()
    estado_df    = df[df["Nível de agregação"] == "estado"].copy()

    return escolas_df, estado_df, municipio_df

# ── EXPORTAÇÕES CACHEADAS ────────────────────────────────────────────
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
