# =============================  main.py  =============================
# Dashboard • Matrículas (formato longo)
# --------------------------------------------------------------------
#  ► CSS externo: static/style.css
#  ► Painel: Ano(s) | Etapa | Subetapa | Rede(s)
#  ► Tabela detalhada com filtros por coluna e paginação
# --------------------------------------------------------------------

# ─── 1. IMPORTS ──────────────────────────────────────────────────────
import streamlit as st, pandas as pd, io, os, re, time
from pathlib import Path
from constantes import *                       # TITULO_*, ERRO_*, INFO_* …
from layout_primeiros_indicadores import (
    obter_estilo_css_container,
    PARAMETROS_ESTILO_CONTAINER,
)

# ─── 2. CONFIG. DA PÁGINA ────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── 3. INJETAR CSS ─────────────────────────────────────────────────
st.markdown(obter_estilo_css_container(PARAMETROS_ESTILO_CONTAINER),
            unsafe_allow_html=True)
css_file = Path("static/style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css_file}</style>", unsafe_allow_html=True)

# ─── 4. UTILITÁRIOS --------------------------------------------------
def beautify(col: str) -> str:
    return " ".join(p.capitalize() for p in col.replace("\n", " ").lower().split())

def aplicar_padrao_numerico_brasileiro(num):
    if pd.isna(num) or num == "-": return "-"
    try:
        n = float(num)
        if n.is_integer():
            return f"{int(n):,}".replace(",", ".")
        inteiro, frac = str(f"{n:,.2f}").split(".")
        return f"{inteiro.replace(',', '.')},{frac}"
    except Exception:
        return str(num)

def format_number_br(num):
    try: return f"{int(num):,}".replace(",", ".")
    except Exception: return str(num)

# ─── 5. IMPORTA .PARQUET ÚNICO ───────────────────────────────────────
@st.cache_resource(show_spinner="Carregando dados.parquet…")
def importar_parquet_unico():
    df = pd.read_parquet("dados.parquet")

    # 1. Converte códigos numéricos para texto (sem “.0”)
    for cod_col in ["Cód. Município", "Cód. da Escola"]:
        if cod_col in df.columns:
            df[cod_col] = (
                pd.to_numeric(df[cod_col], errors="coerce")  # garante INT64
                  .astype("Int64")                           # mantém nulos
                  .astype(str)                               # vira texto
                  .replace("<NA>", "")                       # tira 'NaN'
            )

    # 2. Cria colunas Etapa, Subetapa, Série
    def _split_etapa(s):
        partes = s.split(" - ")
        etapa = partes[0]
        subetapa = partes[1] if len(partes) > 1 else "—"
        serie = " - ".join(partes[2:]) if len(partes) > 2 else "—"
        return etapa, subetapa, serie

    df[["Etapa", "Subetapa", "Série"]] = df["Etapa de Ensino"].apply(
        lambda x: pd.Series(_split_etapa(x))
    )

    # 3. Ajusta tipos
    df["Nível de agregação"] = df["Nível de agregação"].str.lower()
    df["Ano"] = df["Ano"].astype(str)
    df["Número de Matrículas"] = pd.to_numeric(df["Número de Matrículas"], errors="coerce")

    # 4. Separa por nível de agregação
    escolas_df   = df[df["Nível de agregação"] == "escola"].copy()
    municipio_df = df[df["Nível de agregação"] == "município"].copy()
    estado_df    = df[df["Nível de agregação"] == "estado"].copy()

    return escolas_df, estado_df, municipio_df

# Carrega os três DataFrames que o resto do app usa
escolas_df, estado_df, municipio_df = importar_parquet_unico()


# ─── 7. SIDEBAR – nível de agregação --------------------------------
st.sidebar.title("Filtros")
nivel = st.sidebar.radio("Número de Matrículas por:",
                         ["Escola", "Município", "Estado PE"])
df = {"Escola": escolas_df, "Município": municipio_df, "Estado PE": estado_df}[nivel]
if df.empty: st.error("DataFrame vazio"); st.stop()

# ─── 8. PAINEL ANO / ETAPA / SUB / SÉRIE / REDE ---------------------
st.markdown("""
<style>
.panel-filtros{background:#eef2f7;border:1px solid #dce6f3;border-radius:6px;
padding:0.7rem 1rem 1rem;margin-bottom:1.2rem;}
.filter-title{font-weight:600;color:#364b60;font-size:0.92rem;margin-bottom:0.25rem}
.stSelectbox>div,.stMultiSelect>div{min-height:38px}
</style>""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="panel-filtros">', unsafe_allow_html=True)
    c_ano, c_etapa, c_sub, c_serie, c_rede = st.columns([1.0, 1.6, 1.6, 1.6, 1.4],
                                                        gap="small")

    # ----- Ano(s)
    with c_ano:
        st.markdown('<div class="filter-title">Ano(s)</div>', unsafe_allow_html=True)
        anos_disp = sorted(df["Ano"].unique(), reverse=True)
        all_anos  = st.checkbox("Tudo", True, key="anos_all")
        anos_sel  = st.multiselect("", anos_disp,
                                   default=(anos_disp if all_anos else anos_disp[:1]),
                                   key="anos_multiselect")
        if all_anos and len(anos_sel) != len(anos_disp):
            st.session_state["anos_all"] = False

    # ----- Etapa
    with c_etapa:
        st.markdown('<div class="filter-title">Etapa</div>', unsafe_allow_html=True)
        etapas_disp = sorted(df["Etapa"].unique())
        etapa_sel   = st.selectbox("", ["Todas"] + etapas_disp, key="etapa_sel")

    # ----- Subetapa (depende da Etapa selecionada)
    with c_sub:
        st.markdown('<div class="filter-title">Subetapa</div>', unsafe_allow_html=True)
        if etapa_sel == "Todas":
            sub_disp = sorted(df["Subetapa"].unique())
        else:
            sub_disp = sorted(df[df["Etapa"] == etapa_sel]["Subetapa"].unique())
        sub_sel = st.selectbox("", ["Todas"] + sub_disp, key="sub_sel")

    # ----- Série (depende de Etapa e Subetapa)
    with c_serie:
        st.markdown('<div class="filter-title">Série</div>', unsafe_allow_html=True)
        mask = df["Etapa"].eq(etapa_sel) if etapa_sel != "Todas" else True
        if sub_sel != "Todas":
            mask &= df["Subetapa"].eq(sub_sel)
        serie_disp = sorted(df[mask]["Série"].unique())
        serie_sel  = st.selectbox("", ["Todas"] + serie_disp, key="serie_sel")

    # ----- Rede(s)
    with c_rede:
        st.markdown('<div class="filter-title">Rede(s)</div>', unsafe_allow_html=True)
        redes_disp = sorted(df["Rede"].dropna().unique())
        all_rede   = st.checkbox("Tudo", True, key="rede_all")
        rede_sel   = st.multiselect("", redes_disp,
                                    default=(redes_disp if all_rede else []),
                                    key="dep_selection")
        if all_rede and len(rede_sel) != len(redes_disp):
            st.session_state["rede_all"] = False
    st.markdown('</div>', unsafe_allow_html=True)


# ─── 9. APLICA FILTROS AO DATAFRAME ---------------------------------
df_filt = df[df["Ano"].isin(st.session_state["anos_multiselect"])]

if rede_sel:
    df_filt = df_filt[df_filt["Rede"].isin(rede_sel)]
if etapa_sel != "Todas":
    df_filt = df_filt[df_filt["Etapa"] == etapa_sel]
if sub_sel != "Todas":
    df_filt = df_filt[df_filt["Subetapa"] == sub_sel]
if serie_sel != "Todas":
    df_filt = df_filt[df_filt["Série"] == serie_sel]

# ─── 10. EXPANDER CONFIG. AVANÇADAS ---------------------------------
with st.sidebar.expander("Configurações avançadas da tabela", False):
    altura_tabela = st.slider("Altura da tabela (px)", 200, 1000, 600, 50)

# >>>>>>>   RECUPERA AS COLUNAS QUE VAMOS MOSTRAR   <<<<<<<<<
base_cols = ["Ano", "Etapa", "Subetapa", "Série", "Número de Matrículas"]

if nivel == "Escola":
    base_cols += [
        "Cód. da Escola", "Nome da Escola",
        "Cód. Município", "Nome do Município",
        "Rede"
    ]
elif nivel == "Município":
    base_cols += [
        "Cód. Município", "Nome do Município",
        "Rede"
    ]
else:  # Estado
    base_cols += ["Rede"]   # parquet não tem código/nome de UF

colunas_visiveis = [c for c in base_cols if c in df_filt.columns]

# só as colunas previamente escolhidas ----------------
df_para_tabela = df_filt[colunas_visiveis].copy()

if df_para_tabela.empty:
    st.warning("Não há dados para exibir."); st.stop()

# ─── 11. TABELA + FILTROS LOCAIS ------------------------------------
num_cols   = len(df_para_tabela.columns)
pesos      = [1] * num_cols
header_cols = st.columns(pesos, gap="small")
filter_cols = st.columns(pesos, gap="small")

col_filters = {}
ALTURA_TITULO = 46

for i, col_name in enumerate(df_para_tabela.columns):
    with header_cols[i]:
        st.markdown(
            f"<div style='height:{ALTURA_TITULO}px;font-weight:600;"
            f"overflow-wrap:break-word;overflow:hidden'>{beautify(col_name)}</div>",
            unsafe_allow_html=True
        )
    with filter_cols[i]:
        col_filters[col_name] = st.text_input(
            "", key=f"filter_{i}_{col_name}",
            placeholder=f"Filtrar {beautify(col_name)}…",
            label_visibility="collapsed"
        )

df_texto_filtrado = df_para_tabela.copy()
for col_name, filtro in col_filters.items():
    if filtro:
        expr = re.escape(filtro)
        try:
            if (col_name.startswith("Número de") or
                pd.api.types.is_numeric_dtype(df_texto_filtrado[col_name])):
                ponto = filtro.replace(",", ".")
                if ponto.replace(".", "", 1).isdigit() and ponto.count(".") <= 1:
                    df_texto_filtrado = df_texto_filtrado[
                        df_texto_filtrado[col_name] == float(ponto)
                    ]
                else:
                    df_texto_filtrado = df_texto_filtrado[
                        df_texto_filtrado[col_name].astype(str)
                        .str.contains(expr, case=False, regex=True)
                    ]
            else:
                df_texto_filtrado = df_texto_filtrado[
                    df_texto_filtrado[col_name].astype(str)
                    .str.contains(expr, case=False, regex=True)
                ]
        except Exception as e:
            st.warning(f"Erro ao filtrar {col_name}: {e}")

# Paginação manual
PAGE_SIZE = st.session_state.get("page_size", 50)
chunks = [df_texto_filtrado[i:i + PAGE_SIZE]
          for i in range(0, len(df_texto_filtrado), PAGE_SIZE)] or [df_texto_filtrado]
total_pg = len(chunks)
pg_atual = st.session_state.get("current_page", 1)
pg_atual = max(1, min(pg_atual, total_pg))
st.session_state["current_page"] = pg_atual
df_pagina = chunks[pg_atual - 1].reset_index(drop=True)

# Exibe tabela ----------------------------------------------------------------------------
for c in df_pagina.columns:
    if c.startswith("Número de"):
        df_pagina[c] = df_pagina[c].apply(aplicar_padrao_numerico_brasileiro)

st.dataframe(df_pagina, height=altura_tabela, use_container_width=True, hide_index=True)

# ─ botões de paginação -------------------------------------------------------------------
b1, b2, b3, b4 = st.columns([1, 1, 1, 2])
with b1:
    if st.button("◀ Anterior", disabled=pg_atual == 1):
        st.session_state["current_page"] = pg_atual - 1
        st.rerun()
with b2:
    if st.button("Próximo ▶", disabled=pg_atual == total_pg):
        st.session_state["current_page"] = pg_atual + 1
        st.rerun()
with b3:
    novo_psz = st.selectbox(
        "Itens", [10, 25, 50, 100],
        index=[10, 25, 50, 100].index(PAGE_SIZE),
        label_visibility="collapsed"
    )
    if novo_psz != PAGE_SIZE:
        st.session_state["page_size"] = novo_psz
        st.session_state["current_page"] = 1
        st.rerun()
with b4:
    st.markdown(f"**Página {pg_atual}/{total_pg} "
                f"• Total {format_number_br(len(df_texto_filtrado))} registros**")

# ─── 12. DOWNLOADS (sidebar) ----------------------------------------
csv_bytes = df_texto_filtrado.to_csv(index=False).encode("utf-8")
xlsx_buf = io.BytesIO()
with pd.ExcelWriter(xlsx_buf, engine="xlsxwriter") as w:
    df_texto_filtrado.to_excel(w, index=False, sheet_name="Dados")
st.sidebar.download_button("CSV", csv_bytes, "dados.csv", "text/csv")
st.sidebar.download_button(
    "Excel", xlsx_buf.getvalue(),
    "dados.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ─── 13. KPI + GRÁFICO (adicione se quiser) -------------------------

# ─── 14. RODAPÉ ------------------------------------------------------
st.markdown("---")
st.caption("© Dashboard Educacional – atualização: Mar 2025")
st.caption(
    f"Tempo de processamento: "
    f"{time.time() - st.session_state.get('tempo_inicio', time.time()):.2f}s"
)
st.session_state['tempo_inicio'] = time.time()
# ====================================================================
