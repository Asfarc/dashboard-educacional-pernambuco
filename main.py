# =============================  main.py  =============================
# Dashboard PNE – filtros antigos (painel superior + filtros manuais)
# --------------------------------------------------------------------
#  ► CSS externo apenas em static/style.css (nada de css_unificado)
#  ► Painel: Ano(s) | Etapa/Subetapa | Rede(s)
#  ► Tabela detalhada com filtros por coluna e paginação
# --------------------------------------------------------------------

# ─── 1. IMPORTS ──────────────────────────────────────────────────────
import streamlit as st, pandas as pd, io, json, os, re, time
from pathlib import Path
from constantes import *                       # TITULO_*, ERRO_*, INFO_* …
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

    if ("Número de Matrículas" in df.columns and
        "Número de Matrículas da Educação Básica" not in df.columns):
        df["Número de Matrículas da Educação Básica"] = df["Número de Matrículas"]

    # tipos
    df["Nível de agregação"] = df["Nível de agregação"].str.lower()
    df["Ano"] = df["Ano"].astype(str)
    for c in df.columns:
        if c.startswith("Número de"):
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # separa por nível
    escolas_df   = df[df["Nível de agregação"] == "escola"].copy()
    municipio_df = df[df["Nível de agregação"] == "município"].copy()
    estado_df    = df[df["Nível de agregação"] == "estado"].copy()
    return escolas_df, estado_df, municipio_df

escolas_df, estado_df, municipio_df = importar_parquet_unico()

# ─── 6. DICIONÁRIO DE ETAPAS ----------------------------------------
@st.cache_data
def ler_dicionario_etapas():
    f = Path("dicionario_das_etapas_de_ensino.json")
    if not f.exists():
        st.error("dicionario_das_etapas_de_ensino.json não encontrado"); st.stop()
    return json.loads(f.read_text(encoding="utf-8"))

def padronizar_dict_etapas(df):
    base = ler_dicionario_etapas()
    norm = {c.replace('\n','').lower(): c for c in df.columns}
    def real(x): return norm.get(x.replace('\n','').lower(), x)
    out={}
    for etapa,cfg in base.items():
        out[etapa]={
            "coluna_principal": real(cfg.get("coluna_principal","")),
            "subetapas":{k:real(v) for k,v in cfg.get("subetapas",{}).items()},
            "series":{k:{s:real(c) for s,c in sd.items()} for k,sd in cfg.get("series",{}).items()}
        }
    return out

def procurar_coluna_matriculas(etapa, sub, serie, mapa):
    if sub=="Todas": return mapa[etapa]["coluna_principal"]
    if serie=="Todas": return mapa[etapa]["subetapas"].get(sub)
    return mapa[etapa]["series"].get(sub,{}).get(serie)

def confirmar_coluna(df, col):
    if col in df.columns: return True,col
    alt={c.replace('\n','').lower():c for c in df.columns}
    key=col.replace('\n','').lower()
    return (key in alt), alt.get(key,col)

# ─── 7. SIDEBAR – nível de agregação --------------------------------
st.sidebar.title("Filtros")
nivel = st.sidebar.radio("Número de Matrículas por:",
                         ["Escola","Município","Estado PE"])
df = {"Escola":escolas_df,"Município":municipio_df,"Estado PE":estado_df}[nivel]
if df.empty: st.error("DataFrame vazio"); st.stop()

# ─── 8. PAINEL ANOS / ETAPA / REDE ----------------------------------
st.markdown("""
<style>
.panel-filtros{background:#eef2f7;border:1px solid #dce6f3;border-radius:6px;
padding:0.7rem 1rem 1rem;margin-bottom:1.2rem;}
.filter-title{font-weight:600;color:#364b60;font-size:0.92rem;margin-bottom:0.25rem}
.stSelectbox>div,.stMultiSelect>div{min-height:38px}
</style>""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="panel-filtros">', unsafe_allow_html=True)
    c_ano, c_etapa, c_rede = st.columns([1.3, 2.2, 1.8], gap="small")

    # ----- Ano(s)
    with c_ano:
        st.markdown('<div class="filter-title">Ano(s)</div>', unsafe_allow_html=True)
        anos_disp = sorted(df["Ano"].unique(), reverse=True)
        all_anos  = st.checkbox("Selecionar tudo", value=True, key="anos_all")
        anos_sel  = st.multiselect(
            "", anos_disp,
            default=(anos_disp if all_anos else anos_disp[:1]),
            key="anos_multiselect"
        )
        if all_anos and len(anos_sel) != len(anos_disp):
            st.session_state["anos_all"] = False

    # ----- Etapa / Subetapa
    mapa = padronizar_dict_etapas(df)
    lista_etapas = list(mapa.keys())
    with c_etapa:
        st.markdown('<div class="filter-title">Etapa / Subetapa</div>', unsafe_allow_html=True)
        etapa_sel = st.selectbox("", lista_etapas, key="etapa_ensino")
        sub_opts  = ["Todas"] + list(mapa[etapa_sel]["subetapas"].keys())
        sub_sel   = st.selectbox("", sub_opts, key="subetapa")

    # ----- Rede(s)
    with c_rede:
        st.markdown('<div class="filter-title">Rede(s)</div>', unsafe_allow_html=True)
        redes_disp = sorted(df["Rede"].dropna().unique())
        all_rede   = st.checkbox("Selecionar tudo", value=True, key="rede_all")
        rede_sel   = st.multiselect(
            "", redes_disp,
            default=(redes_disp if all_rede else []),
            key="dep_selection"
        )
        if all_rede and len(rede_sel) != len(redes_disp):
            st.session_state["rede_all"] = False
    st.markdown('</div>', unsafe_allow_html=True)

# ─── 9. APLICA FILTROS AO DATAFRAME ---------------------------------
df_filt = df[df["Ano"].isin(st.session_state["anos_multiselect"])]

if "Rede" in df_filt.columns and st.session_state["dep_selection"]:
    df_filt = df_filt[df_filt["Rede"].isin(st.session_state["dep_selection"])]

col_mat = procurar_coluna_matriculas(etapa_sel, sub_sel, "Todas", mapa)
_, col_real = confirmar_coluna(df_filt, col_mat)
if col_real in df_filt.columns:
    df_filt = df_filt[pd.to_numeric(df_filt[col_real], errors="coerce") > 0]

# ─── 10. EXPANDER CONFIG. AVANÇADAS ---------------------------------
with st.sidebar.expander("Configurações avançadas da tabela", False):
    altura_tabela = st.slider("Altura da tabela (px)", 200, 1000, 600, 50)

# >>>>>>>   RECUPERA AS COLUNAS QUE VAMOS MOSTRAR   <<<<<<<<<
base_cols = ["Ano"]

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
    base_cols += ["Rede"]   # o parquet não tem código/nome de UF

colunas_visiveis = [c for c in base_cols if c in df_filt.columns]
if col_real and col_real not in colunas_visiveis:
    colunas_visiveis.append(col_real)
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# só as colunas previamente escolhidas ----------------
df_para_tabela = df_filt[colunas_visiveis].copy()


if df_para_tabela.empty:
    st.warning("Não há dados para exibir."); st.stop()

num_cols   = len(df_para_tabela.columns)
pesos      = [1] * num_cols
header_cols = st.columns(pesos, gap="small")
filter_cols = st.columns(pesos, gap="small")

col_filters = {}
ALTURA_TITULO = 46

for i,col_name in enumerate(df_para_tabela.columns):
    with header_cols[i]:
        st.markdown(
            f"<div style='height:{ALTURA_TITULO}px;font-weight:600;"
            f"overflow-wrap:break-word;overflow:hidden'>{beautify(col_name)}</div>",
            unsafe_allow_html=True
        )
    with filter_cols[i]:
        col_filters[col_name] = st.text_input("", key=f"filter_{i}_{col_name}",
                                              placeholder=f"Filtrar {beautify(col_name)}…",
                                              label_visibility="collapsed")

df_texto_filtrado = df_para_tabela.copy()
for col_name, filtro in col_filters.items():
    if filtro:
        expr = re.escape(filtro)
        try:
            if col_name.startswith("Número de") or pd.api.types.is_numeric_dtype(df_texto_filtrado[col_name]):
                ponto = filtro.replace(",",".")
                if ponto.replace(".","",1).isdigit() and ponto.count(".")<=1:
                    df_texto_filtrado = df_texto_filtrado[df_texto_filtrado[col_name]==float(ponto)]
                else:
                    df_texto_filtrado = df_texto_filtrado[
                        df_texto_filtrado[col_name].astype(str).str.contains(expr, case=False, regex=True)]
            else:
                df_texto_filtrado = df_texto_filtrado[
                    df_texto_filtrado[col_name].astype(str).str.contains(expr, case=False, regex=True)]
        except Exception as e:
            st.warning(f"Erro ao filtrar {col_name}: {e}")

# Paginação manual
PAGE_SIZE = st.session_state.get("page_size", 50)
chunks = [df_texto_filtrado[i:i+PAGE_SIZE]
          for i in range(0,len(df_texto_filtrado), PAGE_SIZE)] or [df_texto_filtrado]
total_pg = len(chunks)
pg_atual = st.session_state.get("current_page",1)
pg_atual = max(1,min(pg_atual,total_pg))
st.session_state["current_page"]=pg_atual
df_pagina = chunks[pg_atual-1].reset_index(drop=True)

# Exibe
for c in df_pagina.columns:
    if c.startswith("Número de"):
        df_pagina[c] = df_pagina[c].apply(aplicar_padrao_numerico_brasileiro)

st.dataframe(df_pagina, height=altura_tabela, use_container_width=True, hide_index=True)

# ─ botões de paginação
b1,b2,b3,b4 = st.columns([1,1,1,2])
with b1:
    if st.button("◀ Anterior", disabled=pg_atual==1):
        st.session_state["current_page"] = pg_atual-1; st.rerun()
with b2:
    if st.button("Próximo ▶", disabled=pg_atual==total_pg):
        st.session_state["current_page"] = pg_atual+1; st.rerun()
with b3:
    novo_psz = st.selectbox("Itens", [10,25,50,100],
                            index=[10,25,50,100].index(PAGE_SIZE),
                            label_visibility="collapsed")
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
st.sidebar.download_button("CSV", csv_bytes,"dados.csv","text/csv")
st.sidebar.download_button("Excel", xlsx_buf.getvalue(),
                           "dados.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─── 13. KPI + GRÁFICO (adicione se quiser) -------------------------

# ─── 14. RODAPÉ ------------------------------------------------------
st.markdown("---")
st.caption("© Dashboard Educacional – atualização: Mar 2025")
st.caption(f"Tempo de processamento: "
           f"{time.time()-st.session_state.get('tempo_inicio',time.time()):.2f}s")
st.session_state['tempo_inicio'] = time.time()
# ====================================================================
