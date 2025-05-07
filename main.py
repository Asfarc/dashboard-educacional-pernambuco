# =============================  main.py  =============================
# Dashboard • Matrículas (formato longo) – versão otimizada
# --------------------------------------------------------------------
#  ► Painel: Ano(s) | Etapa | Subetapa | Série | Rede(s)
#  ► Filtros em cascata (Etapa → Subetapa → Série)
#  ► DataFrame paginado + filtros por coluna
# --------------------------------------------------------------------

# ─── 1. IMPORTS ──────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import altair as alt
import io, re, time
import base64, os
from pathlib import Path
import streamlit.components.v1 as components

# ─── 2. PAGE CONFIG (primeiro comando Streamlit!) ───────────────────
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 2‑B. MÚSICA DE FUNDO ───────────────────────────────────────────
def _musica_de_fundo(arquivo_mp3: str,
                      volume: float = 0.25,
                      flag: str = "musica_injetada"):
    """
    Injeta um <audio> invisível e tenta tocar automaticamente.
    Se o navegador bloquear, exibe um botão "▶️ Tocar música".
    Executa só uma vez por sessão (controlado por st.session_state[flag]).
    """
    if st.session_state.get(flag):
        return

    # procura o arquivo em possíveis caminhos
    caminhos = [
        arquivo_mp3,                              # raiz do repo
        f"static/{arquivo_mp3}",                  # pasta static (Streamlit Cloud)
        Path(__file__).parent / "static" / arquivo_mp3
    ]
    for c in caminhos:
        if os.path.exists(c):
            mp3_bytes = Path(c).read_bytes()
            break
    else:
        st.warning("Áudio não encontrado."); return

    b64 = base64.b64encode(mp3_bytes).decode()
    components.html(
        f"""
        <audio id="bg-music" loop>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
          const audio = document.getElementById('bg-music');
          audio.volume = {volume};
          audio.play().catch(() => {{
              const btn = document.createElement('button');
              btn.textContent = "▶️ Tocar música";
              btn.style = `
                  position:fixed; bottom:20px; left:20px; z-index:10000;
                  padding:8px 16px; font-size:16px; cursor:pointer;
              `;
              btn.onclick = () => {{ audio.play(); btn.remove(); }};
              document.body.appendChild(btn);
          }});
        </script>
        """,
        height=0, width=0
    )
    st.session_state[flag] = True

def tocar_musica_sidebar():
    """Interface simples na sidebar para escolher e ativar a música."""
    musicas = {
        "Sol da Minha Vida": "01 ROBERTA MIRANDA SOL DA MINHA VIDA.mp3",
        "Vá Com Deus":      "02 ROBERTA MIRANDA VA COM DEUS.mp3",
    }

    with st.sidebar:
        st.markdown("### 🎵 Música")
        ativar = st.checkbox("Ativar música", value=True)
        if not ativar:
            # se o usuário desmarcar, remove flag para parar nas próximas execuções
            st.session_state.pop("musica_injetada", None)
            return

        musica_sel = st.selectbox("Selecionar música:", list(musicas.keys()))
    _musica_de_fundo(musicas[musica_sel])

# chama logo após a configuração da página
tocar_musica_sidebar()

# SEÇÃO ÚNICA DE ESTILOS - Todas as configurações visuais em um só lugar
# ===================================================================
# Cores do tema
CORES = {
    # Cores principais
    "primaria": "#ffdfba",  # SIDEBAR
    "secundaria": "#d53e4f",  # TÍTULOS DOS FILTROS
    "terciaria": "#0073ba",  # Botões rádio - Azul (corrigido para usar o mesmo valor)

    # Cores neutras
    "cinza_claro": "#ffffff",  # Cinza claro (fundo de painéis)
    "cinza_medio": "#ffffff",  # Cinza médio (bordas)
    "cinza_escuro": "#f6b119",  # Cinza escuro (texto)
    "branco": "#ffffff",  # Branco
    "preto": "#000000",  # Preto (corrigido - estava vermelho)

    # Cores funcionais
    "highlight": "#ffdfba",  # Azul claro (cabeçalhos de tabela)
    "botao_hover": "#fc4e2a",  # Cor de hover para botões
    "selecionado": "#08306b",  # Cor para itens selecionados

    # Cores específicas para sidebar
    "sidebar_titulo": "#000000",             # Título "Filtros"
    "sidebar_subtitulo": "#000000",          # Subtítulo "Número de Matrículas por:"
    "sidebar_radio_texto": "#ffffff",        # NOVO! Texto dos botões rádio (Escola, Município, Estado PE)
    "sidebar_secao": "#000000",              # Seções como "Download" e "Configurações avançadas"
    "sidebar_texto_normal": "#ffffff",       # Texto normal na sidebar
    "sidebar_slider_cor": "#000000",         # Cor para sliders na sidebar
    "sidebar_slider_texto": "#ffffff",       # Texto do slider (Altura da tabela)
}

# Tipografia
FONTES = {
    "titulo": "1.1rem",
    "conteudo": "1rem",
    "filtro_titulo": "0.90rem",
}

# Parâmetros para containers
PARAMETROS_ESTILO_CONTAINER = {
    "raio_borda": 8,
    "cor_borda": CORES["cinza_medio"],
    "cor_titulo": CORES["cinza_escuro"],
    "tamanho_fonte_titulo": FONTES["titulo"],
    "tamanho_fonte_conteudo": FONTES["conteudo"],
    "cor_fonte_conteudo": CORES["cinza_escuro"],
}

# CSS para containers
def obter_estilo_css_container(p=PARAMETROS_ESTILO_CONTAINER) -> str:
    return f"""
    <style>
    .container-custom{{padding:0!important;margin:0!important;background:transparent!important}}
    .container-title{{font-size:{p['tamanho_fonte_titulo']};color:{p['cor_titulo']}}}
    .container-text {{font-size:{p['tamanho_fonte_conteudo']};color:{p['cor_fonte_conteudo']}}}
    </style>
    """

# CSS principal - todos os estilos em um único bloco
CSS_COMPLETO = f"""
/* ===== PAINEL DE FILTROS ========================================== */
.panel-filtros{{
    background:{CORES["cinza_claro"]};
    border:1px solid {CORES["cinza_medio"]};
    border-radius:6px;
    padding:0.2rem 1rem 0.5rem;
    margin-bottom:0.5rem;
}}

.panel-row{{display:flex;flex-wrap:nowrap;gap:0.8rem}}
.panel-row>div{{flex:1 1 0}}

.filter-title{{
    font-weight:600;
    color:{CORES["secundaria"]};
    font-size:{PARAMETROS_ESTILO_CONTAINER["tamanho_fonte_conteudo"]};
    margin:0 0 0.15rem
}}

/* ===== SIDEBAR ===================================================== */
[data-testid="stSidebar"]{{width:260px!important;min-width:260px!important}}
[data-testid="stSidebar"]::before{{
    content:"";position:absolute;top:0;left:0;width:100%;height:100%;
    background:{CORES["primaria"]};border-radius:1px;z-index:0}}
[data-testid="stSidebar"]>div{{position:relative;z-index:1;padding:2rem 1rem!important}}

/* Título principal da sidebar "Filtros" */
[data-testid="stSidebar"] h1 {{
    color:{CORES["sidebar_titulo"]}!important;
    font-size:1.8rem!important;
    font-weight:700!important;
    margin-bottom:1.5rem!important;
}}

/* Subtítulo "Número de Matrículas por:" */
[data-testid="stSidebar"] .stRadio span {{
    color:{CORES["sidebar_subtitulo"]}!important;
}}

/* Título "Configurações avançadas" e "Download" */
[data-testid="stSidebar"] h3, 
[data-testid="stSidebar"] [data-testid="stExpander"] summary p {{
    color:{CORES["sidebar_secao"]}!important;
    font-size:1.2rem!important;
    font-weight:600!important;
    margin:1.5rem 0 0.8rem!important;
}}

/* Texto normal como "Altura da tabela (px)" */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {{
    color:{CORES["sidebar_texto_normal"]}!important;
}}

/* Texto do slider - seletor mais específico e direto */
div[data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stSlider"] label {{
    color: {CORES["sidebar_slider_texto"]}!important;
    font-weight: 600!important;
}}

/* Sliders na sidebar */
[data-testid="stSidebar"] [data-testid="stSlider"] div[role="slider"] {{
    background-color: {CORES["sidebar_slider_cor"]}!important;
}}

/* Outros elementos de UI na sidebar */
[data-testid="stSidebar"] option,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] [data-baseweb=select] div{{
    color:{CORES["preto"]}!important
}}

[data-testid="stSidebar"] .stMultiSelect [aria-selected=true]{{
    background:{CORES["selecionado"]}!important;
    color:{CORES["branco"]}!important;
    border-radius:1px!important
}}

/* ===== BOTÕES ====================================================== */
.stButton>button,.stDownloadButton>button{{
    background:{CORES["cinza_escuro"]}!important;color:{CORES["branco"]}!important;border:none!important;
    border-radius:3px!important;transition:all .3s}}
.stButton>button:hover,.stDownloadButton>button:hover{{
    background:{CORES["botao_hover"]}!important;transform:translateY(-1px);
    box-shadow:0 2px 5px rgba(0,0,0,.1)}}

/* ===== MULTISELECT E BOTÕES RÁDIO ================================== */
/* Reduzir a largura do container do multiselect */
[data-testid="stMultiSelect"] {{
    max-width: 460px !important;
    width: 100% !important;
}}

/* Ajustar o container principal */
.panel-filtros [data-baseweb="select"] {{
    max-width: 100px !important;
}}

/* Reduzir largura do dropdown quando expandido */
[data-baseweb="popover"] {{
    max-width: 100px !important;
}}

/* Estilo para os botões rádio de nível */
.stRadio > div {{
    padding: 10px 0;
}}

/* Texto dentro dos botões rádio (Escola, Município, Estado PE) */
.stRadio > div > label > div > p {{
    color: {CORES["sidebar_radio_texto"]} !important;
}}

.stRadio > div > label {{
    background-color: {CORES["terciaria"]};
    border: 1px solid {CORES["preto"]};
    border-radius: 6px;
    padding: 10px;
    margin: 5px 0;
    display: flex;
    align-items: center;
    transition: all 0.2s ease;
}}

.stRadio > div > label:hover {{
    background-color: {CORES["cinza_medio"]};
    transform: translateY(-2px);
}}

.stRadio > div [data-testid="stMarkdownContainer"] p {{
    margin: 0;
    font-weight: 500;
}}

/* ===== TABELA E CABEÇALHOS ======================================== */
/* Configuração para os cabeçalhos da tabela */
.column-header {{
    text-align: center;
    font-weight: bold;
    background-color: {CORES["highlight"]};
    padding: 12px 4px;
    border-radius: 0px;
    margin-bottom: 2px;
    height: 45px;
    display: flex;
    align-items: center;
    justify-content: center;
}}

/* Centralização dos números na tabela */
[data-testid="stDataFrame"] table tbody tr td:last-child {{
    text-align: center !important;
}}

/* Também centraliza o cabeçalho da última coluna */
[data-testid="stDataFrame"] table thead tr th:last-child {{
    text-align: center !important;
}}
"""

# Aplica os estilos CSS
st.markdown(obter_estilo_css_container(), unsafe_allow_html=True)
st.markdown(f"<style>{CSS_COMPLETO}</style>", unsafe_allow_html=True)

# ─── 4. FUNÇÕES UTIL ────────────────────────────────────────────────
def beautify(col: str) -> str:
    return " ".join(p.capitalize() for p in col.replace("\n", " ").lower().split())

def aplicar_padrao_numerico_brasileiro(num):
    if pd.isna(num): return "-"
    n = float(num)
    if n.is_integer():
        return f"{int(n):,}".replace(",", ".")
    inteiro, frac = str(f"{n:,.2f}").split(".")
    return f"{inteiro.replace(',', '.')},{frac}"

def format_number_br(num):
    try:    return f"{int(num):,}".replace(",", ".")
    except: return str(num)

# ─── 5. CARGA DO PARQUET (rápido + tipos category) ──────────────────
@st.cache_data(ttl=None, persist=True, show_spinner="Carregando dados…")
def carregar_dados():
    df = pd.read_parquet("dados.parquet", engine="pyarrow")

    for cod in ["Cód. Município", "Cód. da Escola"]:
        if cod in df.columns:
            df[cod] = (
                pd.to_numeric(df[cod], errors="coerce")
                .astype("Int64").astype(str).replace("<NA>", "")
            )

    def _split(s: str):
        p = s.split(" - ")
        etapa = p[0]
        sub   = p[1] if len(p) > 1 else ""
        serie = " - ".join(p[2:]) if len(p) > 2 else ""
        return etapa, sub, serie

    df[["Etapa", "Subetapa", "Série"]] = df["Etapa de Ensino"].apply(
        lambda x: pd.Series(_split(x))
    )

    df["Nível de agregação"] = df["Nível de agregação"].str.lower()
    df["Ano"] = df["Ano"].astype(str)
    df["Número de Matrículas"] = pd.to_numeric(df["Número de Matrículas"], errors="coerce")

    for c in ["Etapa", "Subetapa", "Série", "Rede"]:
        df[c] = df[c].astype("category")

    return (
        df[df["Nível de agregação"] == "escola"].copy(),
        df[df["Nível de agregação"] == "município"].copy(),
        df[df["Nível de agregação"] == "estado"].copy(),
    )

escolas_df, municipio_df, estado_df = carregar_dados()

# ─── 6. SIDEBAR – nível de agregação ────────────────────────────────
st.sidebar.title("Filtros")

# Adicionar estilo para melhorar a aparência dos botões rádio
st.markdown("""
<style>
/* Estilo para os botões rádio de nível */
.stRadio > div {
    padding: 10px 0;
}

.stRadio > div > label {
    background-color: #0073ba;
    border: 1px solid #000000;
    border-radius: 6px;
    padding: 10px;
    margin: 5px 0;
    display: flex;
    align-items: center;
    transition: all 0.2s ease;
}

.stRadio > div > label:hover {
    background-color: #dce6f3;
    transform: translateY(-2px);
}

.stRadio > div [data-testid="stMarkdownContainer"] p {
    margin: 0;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# Colocar o botão rádio original (agora com estilo melhorado)
nivel = st.sidebar.radio(
    "Número de Matrículas por:",
    ["Escola", "Município", "Estado PE"]
)

# Selecionar o DataFrame baseado no nível
df_base = {"Escola": escolas_df, "Município": municipio_df, "Estado PE": estado_df}[nivel]
if df_base.empty:
    st.error("DataFrame vazio"); st.stop()

# ─── 7. PAINEL DE FILTROS ───────────────────────────────────────────

# CSS combinado para todos os ajustes necessários
COMBINED_CSS = """
/* Resto do CSS omitido para brevidade */
"""
st.markdown(f"<style>{COMBINED_CSS}</style>", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="panel-filtros">', unsafe_allow_html=True)

    # 1ª LINHA - Ajuste na proporção para o lado direito ter menos espaço
    c_left, c_right = st.columns([0.5, 0.7], gap="large")

    # Lado esquerdo permanece o mesmo
    with c_left:
        # Ano(s) - com espaço vertical mínimo
        st.markdown('<div class="filter-title" style="margin:0;padding:0">Ano(s)</div>', unsafe_allow_html=True)
        anos_disp = sorted(df_base["Ano"].unique(), reverse=True)
        ano_sel = st.multiselect("", anos_disp, default=anos_disp, key="ano_sel", label_visibility="collapsed")

        # Rede(s) - com margem negativa para aproximar da caixa anterior
        st.markdown('<div class="filter-title" style="margin-top:-12px;padding:0">Rede(s)</div>',
                    unsafe_allow_html=True)
        redes_disp = sorted(df_base["Rede"].dropna().unique())
        rede_sel = st.multiselect("", redes_disp, default=redes_disp, key="rede_sel", label_visibility="collapsed")

    # Lado direito - Ajuste para posicionar Etapa mais à esquerda
    with c_right:
        # Use uma coluna com proporção menor para mover Etapa para a esquerda
        c_right_col1, c_right_col2 = st.columns([0.9, 1])  # Mais espaço para Etapa, menos espaço vazio

        with c_right_col1:
            # Etapa com mínimo de espaço vertical
            st.markdown('<div class="filter-title" style="margin:0;padding:0">Etapa</div>', unsafe_allow_html=True)
            etapas_disp = sorted(df_base["Etapa"].unique())
            etapa_sel = st.multiselect("", etapas_disp, default=[], key="etapa_sel", label_visibility="collapsed")

            # Subetapa - com margem negativa
            if etapa_sel:
                st.markdown('<div class="filter-title" style="margin-top:-12px;padding:0">Subetapa</div>',
                            unsafe_allow_html=True)
                sub_disp = sorted(
                    df_base.loc[
                        df_base["Etapa"].isin(etapa_sel) & (df_base["Subetapa"] != ""),
                        "Subetapa"
                    ].unique()
                )
                sub_sel = st.multiselect("", sub_disp, default=[], key="sub_sel", label_visibility="collapsed")
            else:
                sub_sel = []

            # Série - com margem negativa
            if etapa_sel and sub_sel:
                st.markdown('<div class="filter-title" style="margin-top:-12px;padding:0">Série</div>',
                            unsafe_allow_html=True)
                serie_disp = sorted(
                    df_base.loc[
                        df_base["Etapa"].isin(etapa_sel) &
                        df_base["Subetapa"].isin(sub_sel) &
                        (df_base["Série"] != ""),
                        "Série"
                    ].unique()
                )
                serie_sel = st.multiselect("", serie_disp, default=[], key="serie_sel", label_visibility="collapsed")
            else:
                serie_sel = []

    st.markdown('</div>', unsafe_allow_html=True)   # fecha .panel-filtros


# ─── 8. FUNÇÃO DE FILTRO CACHEADA ───────────────────────────────────
@st.cache_data
def filtrar(base_df,
            anos: tuple,
            redes: tuple,
            etapas: tuple,
            subetapas: tuple,
            series: tuple) -> pd.DataFrame:
    m = base_df["Ano"].isin(anos)
    if redes:      m &= base_df["Rede"].isin(redes)
    if etapas:     m &= base_df["Etapa"].isin(etapas)
    if subetapas:  m &= base_df["Subetapa"].isin(subetapas)
    if series:     m &= base_df["Série"].isin(series)
    return base_df.loc[m]

# Aplica o filtro com base nas seleções
df_filtrado = filtrar(
    df_base,
    tuple(ano_sel),
    tuple(rede_sel),
    tuple(etapa_sel),
    tuple(sub_sel),
    tuple(serie_sel),
)

# ─── 9. ALTURA DA TABELA (slider) ───────────────────────────────────────
with st.sidebar.expander("Configurações avançadas da tabela", False):
    # Adicionar um estilo personalizado para o texto do slider
    st.markdown("""
    <style>
    /* Seletor mais específico para o texto do slider */
    [data-testid="stExpander"] [data-testid="stSlider"] > div:first-child {
        color: #000000 !important;
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    altura_tabela = st.slider("Altura da tabela (px)", 200, 1000, 600, 50)

# ─── 10. TABELA PERSONALIZADA COM FILTROS INTEGRADOS ──────────────────────

# Definição das colunas da tabela
# Reorganiza para colocar Número de Matrículas por último
vis_cols = ["Ano", "Etapa", "Subetapa", "Série"]
if nivel == "Escola":
    vis_cols += ["Cód. da Escola", "Nome da Escola", "Cód. Município", "Nome do Município", "Rede"]
elif nivel == "Município":
    vis_cols += ["Cód. Município", "Nome do Município", "Rede"]
else:
    vis_cols += ["Rede"]
# Adiciona Número de Matrículas como última coluna
vis_cols.append("Número de Matrículas")

# Aplica os filtros principais primeiro
df_tabela = df_filtrado[vis_cols].copy()
if df_tabela.empty:
    st.warning("Não há dados para exibir."); st.stop()

# Adicione este CSS para centralizar os números na coluna de Matrículas
st.markdown("""
<style>
/* Centralização de números na coluna de matrículas */
[data-testid="stDataFrame"] table tbody tr td:last-child {
    text-align: center !important;
}

/* Também centraliza o cabeçalho da última coluna */
[data-testid="stDataFrame"] table thead tr th:last-child {
    text-align: center !important;
}
</style>
""", unsafe_allow_html=True)

# Colunas para cabeçalhos
col_headers = st.columns(len(vis_cols))
for i, col in enumerate(vis_cols):
    with col_headers[i]:
        # Se for a coluna de número de matrículas, aplica um estilo diferente
        if col == "Número de Matrículas":
            st.markdown(f"<div class='column-header' style='text-align:center'>{beautify(col)}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='column-header'>{beautify(col)}</div>", unsafe_allow_html=True)

# Colunas para filtros
col_filters = st.columns(len(vis_cols))
filter_values = {}
for i, col in enumerate(vis_cols):
    with col_filters[i]:
        filter_values[col] = st.text_input("", key=f"filter_{col}", label_visibility="collapsed")

# Aplicar filtros
mask = pd.Series(True, index=df_tabela.index)
for col, value in filter_values.items():
    if value.strip():
        col_s = df_tabela[col]
        if col.startswith("Número de") or pd.api.types.is_numeric_dtype(col_s):
            f_val = value.replace(",", ".")
            if re.fullmatch(r"-?\d+(\.\d+)?", f_val):
                mask &= col_s == float(f_val)
            else:
                mask &= col_s.astype(str).str.contains(value, case=False, regex=False)
        else:
            mask &= col_s.astype(str).str.contains(value, case=False, regex=False)

# Filtrar e preparar para exibição
df_texto = df_tabela[mask]

# Paginação
PAGE_SIZE = st.session_state.get("page_size", 25)
total_pg = max(1, (len(df_texto)-1)//PAGE_SIZE + 1)
pg_atual = min(st.session_state.get("current_page", 1), total_pg)
start = (pg_atual-1)*PAGE_SIZE
df_page = df_texto.iloc[start:start+PAGE_SIZE]

# Formatação para exibição
for c in df_page.columns:
    if c.startswith("Número de"):
        df_page[c] = df_page[c].apply(aplicar_padrao_numerico_brasileiro)

# Exibe a tabela principal
st.dataframe(df_page, height=altura_tabela, use_container_width=True, hide_index=True)

# Navegação
b1, b2, b3, b4 = st.columns([1,1,1,2])
with b1:
    if st.button("◀", disabled=pg_atual==1):
        st.session_state["current_page"] = pg_atual-1; st.rerun()
with b2:
    if st.button("▶", disabled=pg_atual==total_pg):
        st.session_state["current_page"] = pg_atual+1; st.rerun()
with b3:
    new_ps = st.selectbox("Itens", [10,25,50,100],
                        index=[10,25,50,100].index(PAGE_SIZE),
                        label_visibility="collapsed")
    if new_ps != PAGE_SIZE:
        st.session_state["page_size"] = new_ps
        st.session_state["current_page"] = 1; st.rerun()
with b4:
    st.markdown(f"**Página {pg_atual}/{total_pg} · "
                f"{format_number_br(len(df_texto))} registros**")

# ─── 11. DOWNLOADS (on‑click) ───────────────────────────────────────
def gerar_csv():
    # Usar df_texto que já contém os dados filtrados
    st.session_state["csv_bytes"] = df_texto.to_csv(index=False).encode("utf-8")

def gerar_xlsx():
    # Usar df_texto que já contém os dados filtrados
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df_texto.to_excel(w, index=False, sheet_name="Dados")
    st.session_state["xlsx_bytes"] = buf.getvalue()

# Adicionar um título para os botões de download
st.sidebar.markdown("### Download")

# Criar duas colunas na sidebar para os botões
col1, col2 = st.sidebar.columns(2)

# Colocar o botão CSV na primeira coluna
with col1:
    st.download_button(
        "Em CSV",
        data=df_texto.to_csv(index=False).encode("utf-8"),
        key="csv_dl",
        mime="text/csv",
        file_name="dados.csv",
        on_click=gerar_csv
    )

# Colocar o botão Excel na segunda coluna
with col2:
    st.download_button(
        "Em Excel",
        data=io.BytesIO().getvalue() if "xlsx_bytes" not in st.session_state else st.session_state["xlsx_bytes"],
        key="xlsx_dl",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_name="dados.xlsx",
        on_click=gerar_xlsx
    )

# ─── 12. RODAPÉ ─────────────────────────────────────────────────────
st.markdown("---")
st.caption("© Dashboard Educacional – atualização: Mar 2025")
delta = time.time() - st.session_state.get("tempo_inicio", time.time())
st.caption(f"Tempo de processamento: {delta:.2f}s")
st.session_state["tempo_inicio"] = time.time()
# ====================================================================
