# =============================  main.py  =============================
# Dashboard PNE – versão “filtros antigos” (sidebar + painel superior)
# --------------------------------------------------------------------
# • Mantém o CSS externo em static/style.css  ➜  NÃO existe css_unificado
# • Reutiliza todas as funções auxiliares originais
# • Carrega arquivos .parquet (escolas, município, estado)
# • Painel de filtros: Ano(s) | Etapa / Subetapa | Rede(s)
# • Tabela paginada com filtros por coluna + botões download
# --------------------------------------------------------------------

# ─── 1. IMPORTS ──────────────────────────────────────────────────────
import streamlit as st, pandas as pd, io, json, os, re, time
from pathlib import Path

# constantes.py deve ter: TITULO_DASHBOARD, TITULO_DADOS_DETALHADOS,
# ERRO_* e INFO_* usados abaixo
from constantes import *

from layout_primeiros_indicadores import (
    obter_estilo_css_container,
    PARAMETROS_ESTILO_CONTAINER,
    construir_grafico_linha_evolucao,
)

# ─── 2. CONFIG. DA PÁGINA ────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── 3. INJETAR CSS (EXTERNO) ────────────────────────────────────────
st.markdown(obter_estilo_css_container(PARAMETROS_ESTILO_CONTAINER),
            unsafe_allow_html=True)

css_file = Path("static/style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css_file}</style>", unsafe_allow_html=True)

# ─── 4. FUNÇÕES UTILITÁRIAS (beautify, formato BR, etc.) ─────────────
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

# ─── 5. CARREGAR ARQUIVOS PARQUET ────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Carregando dados…")
def importar_arquivos_parquet():
    paths = ["escolas.parquet", "estado.parquet", "municipio.parquet"]
    if not all(Path(p).exists() for p in paths):
        st.error(ERRO_ARQUIVOS_NAO_ENCONTRADOS); st.stop()

    escolas, estado, municipio = [pd.read_parquet(p) for p in paths]

    # conversões básicas
    for _df in (escolas, estado, municipio):
        for c in _df.columns:
            if c.startswith("Número de"):
                _df[c] = pd.to_numeric(_df[c], errors="coerce")
            elif c in ["ANO", "CODIGO DO MUNICIPIO", "CODIGO DA ESCOLA", "CODIGO DA UF"]:
                _df[c] = _df[c].astype(str)

    return escolas, estado, municipio

escolas_df, estado_df, municipio_df = importar_arquivos_parquet()

# ─── 6. DICIONÁRIO DE ETAPAS ────────────────────────────────────────
@st.cache_data
def ler_dicionario_etapas():
    f = Path("dicionario_das_etapas_de_ensino.json")
    if not f.exists():
        st.error("dicionario_das_etapas_de_ensino.json não encontrado"); st.stop()
    return json.loads(f.read_text(encoding="utf-8"))

def padronizar_dict_etapas(df):
    base = ler_dicionario_etapas()
    norm = {c.replace('\n','').lower(): c for c in df.columns}

    def real(nome):
        return norm.get(nome.replace('\n','').lower(), nome)

    out = {}
    for etapa, cfg in base.items():
        out[etapa] = {
            "coluna_principal": real(cfg.get("coluna_principal", "")),
            "subetapas": {k: real(v) for k,v in cfg.get("subetapas", {}).items()},
            "series": {k: {s: real(c) for s,c in sd.items()} for k,sd in cfg.get("series", {}).items()}
        }
    return out

def procurar_coluna_matriculas(etapa, sub, serie, mapa):
    if sub == "Todas": return mapa[etapa]["coluna_principal"]
    if serie == "Todas": return mapa[etapa]["subetapas"].get(sub)
    return mapa[etapa]["series"].get(sub, {}).get(serie)

def confirmar_coluna(df, col):
    if col in df.columns: return True, col
    alt = {c.replace('\n','').lower(): c for c in df.columns}
    key = col.replace('\n','').lower()
    return (key in alt), alt.get(key, col)

# ─── 7. SIDEBAR – nível de agregação ─────────────────────────────────
st.sidebar.title("Filtros")

nivel = st.sidebar.radio("Número de Matrículas por:",
                         ["Escola", "Município", "Estado PE"])

df = {"Escola": escolas_df, "Município": municipio_df, "Estado PE": estado_df}[nivel]
if df.empty:
    st.error("DataFrame vazio."); st.stop()

# ─── 8. PAINEL SUPERIOR (Ano / Etapa / Rede) ─────────────────────────
st.markdown("""
<style>
.panel-filtros{background:#eef2f7;border:1px solid #dce6f3;border-radius:6px;
padding:0.7rem 1rem 1rem;margin-bottom:1.2rem;}
.filter-title{font-weight:600;color:#364b60;font-size:0.92rem;margin-bottom:0.25rem}
.stSelectbox>div,.stMultiSelect>div{min-height:38px}
</style>""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="panel-filtros">', unsafe_allow_html=True)
    c_ano,c_etapa,c_rede = st.columns([1.3,2.2,1.8], gap="small")

    # --- ANO(S) ---
    with c_ano:
        st.markdown('<div class="filter-title">Ano(s)</div>', unsafe_allow_html=True)
        anos_disp = sorted(df["ANO"].unique(), reverse=True)
        select_all_anos = st.checkbox("Selecionar tudo",
                                      value=True, key="anos_all")
        anos_sel = st.multiselect("", anos_disp,
                                  default=(anos_disp if select_all_anos else anos_disp[:1]),
                                  key="anos_multiselect")
        if select_all_anos and len(anos_sel)!=len(anos_disp):
            st.session_state["anos_all"]=False

    # --- ETAPA / SUBETAPA ---
    mapa = padronizar_dict_etapas(df)
    lista_etapas = list(mapa.keys())
    with c_etapa:
        st.markdown('<div class="filter-title">Etapa / Subetapa</div>', unsafe_allow_html=True)
        etapa_sel = st.selectbox("", lista_etapas, key="etapa_ensino")
        sub_opts = ["Todas"]+list(mapa[etapa_sel]["subetapas"].keys())
        sub_sel  = st.selectbox("", sub_opts, key="subetapa")

    # --- REDE(S) ---
    with c_rede:
        st.markdown('<div class="filter-title">Rede(s)</div>', unsafe_allow_html=True)
        redes_disp = sorted(df["DEPENDENCIA ADMINISTRATIVA"].dropna().unique())
        select_all_rede = st.checkbox("Selecionar tudo", value=True, key="rede_all")
        rede_sel = st.multiselect("", redes_disp,
                                  default=(redes_disp if select_all_rede else []),
                                  key="dep_selection")
        if select_all_rede and len(rede_sel)!=len(redes_disp):
            st.session_state["rede_all"]=False

    st.markdown('</div>', unsafe_allow_html=True)

# ─── 9. APLICA FILTROS AOS DADOS ─────────────────────────────────────
if "ANO" not in df.columns:
    st.error("Coluna 'ANO' ausente."); st.stop()

df_filt = df[df["ANO"].isin(st.session_state["anos_multiselect"])]
if "DEPENDENCIA ADMINISTRATIVA" in df_filt.columns:
    if st.session_state["dep_selection"]:
        df_filt = df_filt[df_filt["DEPENDENCIA ADMINISTRATIVA"]
                          .isin(st.session_state["dep_selection"])]
    else:
        df_filt = df_filt[0:0]

col_mat = procurar_coluna_matriculas(etapa_sel, sub_sel, "Todas", mapa)
existe, col_real = confirmar_coluna(df_filt, col_mat)
if existe:
    df_filt = df_filt[pd.to_numeric(df_filt[col_real], errors="coerce") > 0]
else:
    st.warning("Coluna de matrículas não encontrada.")

# ─── 10. CONFIGURAÇÕES DA TABELA (Expander) ──────────────────────────
with st.sidebar.expander("Configurações avançadas da tabela", False):
    altura = st.slider("Altura da tabela (px)", 200, 1000, 600, 50,
                       key="altura_tabela")

# colunas base
base_cols = ["ANO"]
if nivel=="Escola":
    base_cols += ["CODIGO DA ESCOLA","NOME DA ESCOLA",
                  "CODIGO DO MUNICIPIO","NOME DO MUNICIPIO",
                  "DEPENDENCIA ADMINISTRATIVA"]
elif nivel=="Município":
    base_cols += ["CODIGO DO MUNICIPIO","NOME DO MUNICIPIO",
                  "DEPENDENCIA ADMINISTRATIVA"]
else:
    base_cols += ["DEPENDENCIA ADMINISTRATIVA","CODIGO DA UF","NOME DA UF"]

colunas_visiveis = [c for c in base_cols if c in df_filt.columns]
if col_real and col_real not in colunas_visiveis:
    colunas_visiveis.append(col_real)

# ─── 11. EXIBE TABELA (paginada simples) ─────────────────────────────
PAGE = st.session_state.get("pg",1)
PAGE_SZ = st.session_state.get("pg_sz",50)
tot_pg = max(1, -(-len(df_filt)//PAGE_SZ))
PAGE = max(1, min(PAGE, tot_pg))
st.session_state["pg"]=PAGE

pag_df = df_filt.iloc[(PAGE-1)*PAGE_SZ : PAGE*PAGE_SZ][colunas_visiveis].copy()
for c in pag_df.columns:
    if c.startswith("Número de"):
        pag_df[c] = pag_df[c].apply(aplicar_padrao_numerico_brasileiro)

st.dataframe(pag_df.reset_index(drop=True), height=altura,
             use_container_width=True, hide_index=True)

a1,a2,a3=st.columns(3)
with a1:
    if st.button("◀", disabled=PAGE==1):
        st.session_state.pg = PAGE-1; st.rerun()
with a2:
    st.markdown(f"**Página {PAGE}/{tot_pg}**")
with a3:
    if st.button("▶", disabled=PAGE==tot_pg):
        st.session_state.pg = PAGE+1; st.rerun()

# ─── 12. DOWNLOADS (sidebar) ─────────────────────────────────────────
csv_bytes = pag_df.to_csv(index=False).encode("utf-8")
xlsx_buf = io.BytesIO()
with pd.ExcelWriter(xlsx_buf, engine="xlsxwriter") as w:
    pag_df.to_excel(w, index=False, sheet_name="Dados")
st.sidebar.download_button("CSV", csv_bytes, "dados.csv", "text/csv")
st.sidebar.download_button("Excel", xlsx_buf.getvalue(),
                           "dados.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─── 13. KPI + GRÁFICO DEMO (mesmo bloco antigo) ────────────────────
# (omiti para reduzir tamanho — copie seu bloco de KPI/grafico aqui)

# ─── 14. RODAPÉ ──────────────────────────────────────────────────────
st.markdown("---")
st.caption("© Dashboard Educacional – atualização: Mar 2025")
st.caption(f"Tempo de processamento: {time.time()-st.session_state.get('tempo_inicio',time.time()):.2f}s")
st.session_state['tempo_inicio']=time.time()
# ====================================================================
