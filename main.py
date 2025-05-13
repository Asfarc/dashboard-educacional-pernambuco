# ─── 1. IMPORTS ──────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import io, re, time
import base64, os
from pathlib import Path
import streamlit.components.v1 as components
import psutil
from datetime import datetime

# ─── 2. PAGE CONFIG (primeiro comando Streamlit!) ───────────────────
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 3. ESTILO GLOBAL ──────────────────────────────────────────────
CORES = {
    "primaria": "#6b8190", "secundaria": "#d53e4f", "terciaria": "#0073ba",
    "cinza_claro": "#ffffff", "cinza_medio": "#e0e0e0", "cinza_escuro": "#333333",
    "branco": "#ffffff", "preto": "#000000", "highlight": "#ffdfba",
    "botao_hover": "#fc4e2a", "selecionado": "#08306b",
    "sb_titulo": "#ffffff", "sb_subtitulo": "#ffffff", "sb_radio": "#ffffff",
    "sb_secao": "#ffffff", "sb_texto": "#ffffff", "sb_slider": "#ffffff",
}

css_path = Path(__file__).parent / "static" / "style.css"
st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True)


# ─── 4. FUNÇÕES UTIL ────────────────────────────────────────────────
def beautify(col: str) -> str:
    """Formata o nome de uma coluna para exibição"""
    return " ".join(p.capitalize() for p in col.replace("\n", " ").lower().split())


def beautify_column_header(col: str) -> str:
    """Formata o cabeçalho de uma coluna com abreviações conhecidas"""
    abreviacoes = {
        "Número de Matrículas": "Matrículas",
        "Nome do Município": "Município",
        "Nome da Escola": "Escola",
        "Etapa de Ensino": "Etapa",
        "Cód. Município": "Cód. Mun.",
        "Cód. da Escola": "Cód. Esc.",
        "UF": "UF"
    }

    # Se a coluna está no dicionário, usar a abreviação
    if col in abreviacoes:
        return abreviacoes[col]

    # Caso contrário, usar o comportamento da beautify original
    return " ".join(p.capitalize() for p in col.replace("\n", " ").lower().split())


def aplicar_padrao_numerico_brasileiro(num):
    """Formata números no padrão brasileiro (1.234,56)"""
    if pd.isna(num):
        return "-"
    n = float(num)
    if n.is_integer():
        return f"{int(n):,}".replace(",", ".")
    inteiro, frac = str(f"{n:,.2f}").split('.')
    return f"{inteiro.replace(',', '.')},{frac}"


def format_number_br(num):
    """Formata inteiros no padrão brasileiro (1.234)"""
    try:
        return f"{int(num):,}".replace(",", ".")
    except:
        return str(num)


# ─── 4‑B. PAGINAÇÃO ────────────────────────────────────────────────
class Paginator:
    """Classe para gerenciar a paginação de DataFrames"""

    def __init__(self, total, page_size=25, current=1):
        # Limita o page_size a 10.000 se for maior
        self.page_size = min(page_size, 10000)
        self.total_pages = max(1, (total - 1) // self.page_size + 1)
        self.current = max(1, min(current, self.total_pages))
        self.start = (self.current - 1) * self.page_size
        self.end = min(self.start + self.page_size, total)

    def slice(self, df: pd.DataFrame) -> pd.DataFrame:
        """Retorna uma fatia do DataFrame correspondente à página atual"""
        return df.iloc[self.start:self.end]


# ─── 5. DEFINIÇÃO DE MODELO DE DADOS POR MODALIDADE ──────────────────────
class ModalidadeConfig:
    """Configuração por tipo de modalidade de ensino"""

    def __init__(self, arquivo, etapa_valores=None, subetapa_valores=None, serie_col=None, texto_ajuda=None):
        self.arquivo = arquivo
        self.etapa_valores = etapa_valores or {}  # valores de etapa para facilitar seleção padrão
        self.subetapa_valores = subetapa_valores or {}  # valores de subetapa específicos
        self.serie_col = serie_col  # nome da coluna de série, se existir
        self.texto_ajuda = texto_ajuda  # texto de ajuda contextual para esta modalidade


# ─── 6. CONFIGURAÇÕES DE MODALIDADE ────────────────────────────────────
MODALIDADES = {
    "Ensino Regular": ModalidadeConfig(
        arquivo="Ensino Regular.parquet",
        etapa_valores={
            "padrao": "Educação Infantil"  # valor padrão para seleção inicial
        },
        serie_col="Ano/Série",
        texto_ajuda="No Ensino Regular, selecione primeiro a Etapa (Infantil, Fundamental ou Médio), depois a Subetapa e, se desejar, uma Série específica."
    ),
    "EJA - Educação de Jovens e Adultos": ModalidadeConfig(
        arquivo="EJA - Educação de Jovens e Adultos.parquet",
        etapa_valores={
            "padrao": "EJA - Total",
            "totais": ["EJA - Total", "EJA Ensino Fundamental - Total", "EJA Ensino Médio - Total"]  # Novos totais
        },
        subetapa_valores={
            "EJA Ensino Fundamental": ["EJA Anos Iniciais", "EJA Anos Finais", "EJA Ensino Fundamental - Curso FIC"],
            "EJA Ensino Médio": ["EJA Ensino Médio - Sem componente profissionalizante",
                                 "EJA Ensino Médio - Curso FIC",
                                 "EJA Ensino Médio - Curso Técnico Integrado"]
        },
        texto_ajuda="Selecione a Etapa (Total ou específica). Para etapas específicas, escolha a Subetapa."
    ),
    "Educação Profissional": ModalidadeConfig(
        arquivo="Educação Profissional.parquet",
        etapa_valores={
            "padrao": "Educação Profissional - Total",
            "totais": ["Educação Profissional - Total"]  # identifica valores que representam totais
        },
        texto_ajuda="Na Educação Profissional, selecione primeiro a Etapa (Educação Profissional - Total, Formação Inicial Continuada (FIC) ou Educação profissional técnica de nível médio) e depois a subetapa específica, quando disponível."
    )
}


# ─── 7. FUNÇÃO DE CARREGAMENTO PADRONIZADA ────────────────────────────
@st.cache_resource(show_spinner="⏳ Carregando dados…")
def carregar_dados(modalidade_key):
    """Carrega e normaliza os dados para a modalidade selecionada"""
    config = MODALIDADES[modalidade_key]
    caminho = config.arquivo

    try:
        df = pd.read_parquet(caminho, engine="pyarrow")
    except Exception as e:
        st.error(f"Erro ao carregar arquivo '{caminho}': {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    tempo_inicio = time.time()

    # Normalização comum a todas as modalidades
    for cod in ["Cód. Município", "Cód. da Escola"]:
        if cod in df.columns:
            df[cod] = (pd.to_numeric(df[cod], errors="coerce")
                       .astype("Int64").astype(str)
                       .replace("<NA>", ""))

    df["Ano"] = df["Ano"].astype(str)
    df["Número de Matrículas"] = pd.to_numeric(
        df["Número de Matrículas"], errors="coerce"
    )

    # Garantir que todas as colunas necessárias existam
    if "Etapa" not in df.columns:
        df["Etapa"] = ""

    if "Subetapa" not in df.columns:
        df["Subetapa"] = ""

    # Adicionar coluna de Série para modalidades que não a possuem
    if config.serie_col is None and "Série" not in df.columns:
        df["Série"] = ""
    elif config.serie_col is not None and config.serie_col in df.columns:
        # Renomear a coluna de série conforme configuração
        df["Série"] = df[config.serie_col]

    # Converter para categóricos para economia de memória
    for col in ["Etapa", "Subetapa", "Série", "Rede"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    # Formato padrão para nível de agregação
    df["Nível de agregação"] = df["Nível de agregação"].str.lower()

    # Registra a métrica de tempo de carregamento
    tempo_carga = time.time() - tempo_inicio
    st.session_state["tempo_carga"] = tempo_carga

    # Retorna views
    return (
        df[df["Nível de agregação"].eq("escola")],
        df[df["Nível de agregação"].eq("município")],
        df[df["Nível de agregação"].eq("estado")],
    )

# ─── 8. CONSTRUÇÃO DOS FILTROS DINÂMICOS ─────────────────────────────
def construir_filtros_ui(df, modalidade_key, nivel):
    """Constrói os filtros de UI baseados na modalidade e dados disponíveis"""
    config = MODALIDADES[modalidade_key]

    # Layout em duas colunas
    c_left, c_right = st.columns([0.4, 0.8], gap="large")

    # Detectar modalidade para compatibilidade
    is_eja = modalidade_key == "EJA - Educação de Jovens e Adultos"
    is_prof = modalidade_key == "Educação Profissional"

    # Filtros comuns a todas as modalidades (coluna esquerda)
    with c_left:
        # Ano(s)
        st.markdown(
            '<div class="filter-title" '
            'style="margin:0;padding:0;display:flex;align-items:center;height:32px">'
            'Ano(s)</div>',
            unsafe_allow_html=True
        )
        anos_disp = sorted(df["Ano"].unique(), reverse=True)
        default_anos = [anos_disp[0]] if anos_disp else []
        anos_sel = st.multiselect(
            "Ano(s)",
            anos_disp,
            default=default_anos,
            key="ano_sel",
            label_visibility="collapsed"
        )

        # Rede(s)
        st.markdown(
            '<div class="filter-title" '
            'style="margin-top:-12px;padding:0;display:flex;align-items:center;height:32px">'
            'Rede(s)</div>',
            unsafe_allow_html=True
        )
        redes_disp = sorted(df["Rede"].dropna().unique())
        default_redes = ["Pública e Privada"] if "Pública e Privada" in redes_disp else []
        redes_sel = st.multiselect(
            "Rede(s)",
            redes_disp,
            default=default_redes,
            key="rede_sel",
            label_visibility="collapsed"
        )

    # Filtros específicos por modalidade (coluna direita)
    with c_right:
        filtros = {}

        # Etapa
        st.markdown(
            '<div class="filter-title" '
            'style="margin:0;padding:0;display:flex;align-items:center;height:32px">'
            'Etapa</div>',
            unsafe_allow_html=True
        )

        # Recupera valores de Etapa e valor padrão
        etapas_disp = sorted(df["Etapa"].unique())
        padrao = config.etapa_valores.get("padrao", "")
        default_etapas = [padrao] if padrao in etapas_disp else [etapas_disp[0]] if etapas_disp else []

        etapa_sel = st.multiselect(
            "Etapa",
            etapas_disp,
            default=default_etapas,
            key="etapa_sel",
            label_visibility="collapsed"
        )
        filtros["etapa"] = etapa_sel

        # Subetapa - mostrar apenas se Etapa foi selecionada
        st.markdown(
            '<div class="filter-title" '
            'style="margin-top:-12px;padding:0;display:flex;align-items:center;height:32px">'
            'Subetapa</div>',
            unsafe_allow_html=True
        )

        # Verificar se o valor selecionado de Etapa é um "Total"
        is_etapa_total = etapa_sel and etapa_sel[0] in config.etapa_valores.get("totais", [])

        if etapa_sel and not is_etapa_total:
            # CORREÇÃO AQUI: Evitar operações diretas com tipos categoria
            # Criar máscaras booleanas separadamente
            etapa_mask = df["Etapa"].isin(etapa_sel)
            notna_mask = df["Subetapa"].notna()

            # Para o filtro de "Total", usamos string methods que funcionam com categorias
            if "Subetapa" in df.columns and isinstance(df["Subetapa"].dtype, pd.CategoricalDtype):
                # Converter para string antes de usar str.contains
                total_mask = ~df["Subetapa"].astype(str).str.contains("Total", na=False)
            else:
                total_mask = ~df["Subetapa"].str.contains("Total", na=False)

            # Aplicar os filtros sequencialmente
            temp_df = df[etapa_mask]
            temp_df = temp_df[temp_df["Subetapa"].notna()]
            temp_df = temp_df[~temp_df["Subetapa"].astype(str).str.contains("Total", na=False)]

            sub_disp = sorted(temp_df["Subetapa"].unique())

            if sub_disp:
                sub_sel = st.multiselect(
                    "Subetapa",
                    sub_disp,
                    default=[],
                    key="sub_sel",
                    label_visibility="collapsed"
                )
            else:
                st.text("Nenhuma subetapa disponível para esta etapa.")
                sub_sel = []
        else:
            # Para etapas "Total" ou quando nenhuma etapa está selecionada
            if is_etapa_total:
                st.text(f"Nenhuma subetapa para {etapa_sel[0]}.")
            else:
                st.text("Selecione uma etapa primeiro.")
            sub_sel = []

        filtros["subetapa"] = sub_sel

        # Série - apenas para Ensino Regular e se subetapa NÃO for total
        if (
                modalidade_key == "Ensino Regular"
                and etapa_sel
                and sub_sel
                and not any("Total" in sub for sub in sub_sel)  # Nova verificação
        ):
            st.markdown(
                '<div class="filter-title" style="margin-top:-12px;padding:0;display:flex;align-items:center;height:32px">'
                'Série</div>',
                unsafe_allow_html=True
            )

            # Filtra séries apenas para subetapas não totais
            temp_df = df[df["Etapa"].isin(etapa_sel)]
            temp_df = temp_df[temp_df["Subetapa"].isin(sub_sel)]
            temp_df = temp_df[temp_df["Série"].notna()]

            serie_disp = sorted(temp_df["Série"].unique())

            if serie_disp:
                serie_sel = st.multiselect(
                    "Série",
                    serie_disp,
                    default=[],
                    key="serie_sel",
                    label_visibility="collapsed"
                )
            else:
                st.text("Nenhuma série disponível para esta subetapa.")
                serie_sel = []

            filtros["serie"] = serie_sel
        else:
            filtros["serie"] = []

    return anos_sel, redes_sel, filtros


# ─── 9. FUNÇÃO DE FILTRO UNIFICADA ─────────────────────────────────
def filtrar_dados(df, modalidade_key, anos, redes, filtros):
    """Filtra dados de forma unificada para qualquer modalidade"""
    config = MODALIDADES[modalidade_key]

    # Aplicamos os filtros sequencialmente
    result_df = df.copy()

    # Filtros básicos (comuns a todas as modalidades)
    result_df = result_df[result_df["Ano"].isin(anos)]

    if redes:
        result_df = result_df[result_df["Rede"].isin(redes)]

    # ─── LÓGICA ESPECÍFICA PARA EJA ────────────────────────────────
    if modalidade_key == "EJA - Educação de Jovens e Adultos":
        etapa_sel = filtros.get("etapa", [])
        subetapa_sel = filtros.get("subetapa", [])

        # Aplica filtro de etapa
        if etapa_sel:
            result_df = result_df[result_df["Etapa"].isin(etapa_sel)]

        # Aplica subetapa apenas se não for total
        if (etapa_sel and
            not any(e in config.etapa_valores.get("totais", []) for e in etapa_sel) and  # CORREÇÃO AQUI
            subetapa_sel):
            result_df = result_df[result_df["Subetapa"].isin(subetapa_sel)]

    # ─── LÓGICA PARA DEMAIS MODALIDADES ────────────────────────────
    else:
        # Etapa
        etapa_sel = filtros.get("etapa", [])
        if etapa_sel:
            result_df = result_df[result_df["Etapa"].isin(etapa_sel)]
            is_etapa_total = any(e in config.etapa_valores.get("totais", []) for e in etapa_sel)  # CORREÇÃO AQUI

            # Lógica específica para Ensino Regular
            if modalidade_key == "Ensino Regular" and not is_etapa_total and not filtros.get("subetapa"):
                result_df = result_df[result_df["Subetapa"].astype(str).str.contains("Total", na=False)]

        # Subetapa (só aplicar se não for total)
        subetapa_sel = filtros.get("subetapa", [])
        if subetapa_sel and etapa_sel and not any(e in config.etapa_valores.get("totais", []) for e in etapa_sel):  # CORREÇÃO AQUI
            result_df = result_df[result_df["Subetapa"].isin(subetapa_sel)]

        # Série - apenas para Ensino Regular e se não for total
        serie_sel = filtros.get("serie", [])
        if (
            serie_sel
            and modalidade_key == "Ensino Regular"
            and etapa_sel
            and not any(e in config.etapa_valores.get("totais", []) for e in etapa_sel)
            and not any("Total" in sub for sub in subetapa_sel)  # Nova verificação
        ):
            result_df = result_df[result_df["Série"].isin(serie_sel)]

    return result_df

# ─── 10. INICIALIZAÇÃO E CARREGAMENTO ─────────────────────────────────
# Inicializa o cronômetro da sessão se não existir
if "tempo_inicio" not in st.session_state:
    st.session_state["tempo_inicio"] = time.time()

# ----- Seleção de modalidade e chamada protegida ---------------------
try:
    with st.sidebar:
        st.sidebar.title("Modalidade")
        tipo_ensino = st.radio(
            "Selecione a modalidade",
            list(MODALIDADES.keys()),
            index=0,
            label_visibility="collapsed"
        )

    # Mostrar spinner personalizado enquanto carrega
    with st.spinner("Carregando dados..."):
        escolas_df, municipio_df, estado_df = carregar_dados(tipo_ensino)

    # Verificar se os DataFrames estão vazios
    if escolas_df.empty and municipio_df.empty and estado_df.empty:
        st.error(f"Não foi possível carregar os dados para '{tipo_ensino}'. Verifique se os arquivos parquet existem.")
        st.stop()

except Exception as e:
    st.error(f"Erro ao carregar '{tipo_ensino}': {str(e)}")
    st.stop()

# ─── 11. SELEÇÃO DE NÍVEL DE AGREGAÇÃO ─────────────────────────────
st.sidebar.title("Filtros")
nivel = st.sidebar.radio(
    "Nível de Agregação",
    ["Escolas", "Municípios", "Pernambuco"],
    label_visibility="collapsed",
    key="nivel_sel"
)

# Selecionar o DataFrame baseado no nível
df_base = {
    "Escolas": escolas_df,
    "Municípios": municipio_df,
    "Pernambuco": estado_df
}[nivel]

if df_base.empty:
    st.warning(f"Não há dados disponíveis para o nível de agregação '{nivel}'.")
    st.stop()

# ─── 12. PAINEL DE FILTROS DINÂMICOS ─────────────────────────────
with st.container():
    st.markdown('<div class="panel-filtros" style="margin-top:-30px">', unsafe_allow_html=True)

    # Construir a interface de filtros com base na modalidade
    anos_sel, redes_sel, filtros_especificos = construir_filtros_ui(
        df_base,
        tipo_ensino,
        nivel
    )

    # Fechar o painel de filtros
    st.markdown('</div>', unsafe_allow_html=True)

# ─── 13. VALIDAÇÃO E APLICAÇÃO DE FILTROS ─────────────────────────
# Verificação de filtros obrigatórios
if not anos_sel:
    st.warning("Por favor, selecione pelo menos um ano.")
    st.stop()

if not redes_sel:
    st.warning("Por favor, selecione pelo menos uma rede de ensino.")
    st.stop()

# Aplicar filtros unificados
df_filtrado = filtrar_dados(
    df_base,
    tipo_ensino,
    anos_sel,
    redes_sel,
    filtros_especificos
)

# Indicador visual de resultados
num_total = len(df_base)
num_filtrado = len(df_filtrado)

if num_filtrado > 0:
    percent = (num_filtrado / num_total) * 100
    st.markdown(
        f"""
        <div class="stats-container">
            Exibindo 
            <strong class="stats-count">{format_number_br(num_filtrado)}</strong> de 
            <strong class="stats-total">{format_number_br(num_total)}</strong> registros
            (<span class="stats-percent">{percent:.1f}%</span>)
        </div>
        """,
        unsafe_allow_html=True
    )


else:
    # Mensagens específicas por modalidade quando não há dados
    config = MODALIDADES[tipo_ensino]
    if config.texto_ajuda:
        st.warning(f"""
        Não há dados para esta combinação de filtros.

        {config.texto_ajuda}
        """)
    else:
        st.warning("Não há dados após os filtros aplicados. Por favor, ajuste os critérios de seleção.")
    st.stop()

# ─── 14. ALTURA DA TABELA (slider) ───────────────────────────────────────
with st.sidebar.expander("Configurações", False):
    # Adicionar um estilo personalizado para o texto do slider
    st.markdown("""
    <style>
    /* ─── Slider: título e valores na mesma cor ─── */
    [data-testid="stExpander"] [data-testid="stSlider"] > div:first-child {
        color: #FFFFFF !important;   /* título */
    }
    [data-testid="stExpander"] [data-testid="stSlider"] > div:nth-child(2) {
        color: #FFFFFF !important;   /* valor atual */
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    altura_tabela = st.slider("Altura da tabela (px)", 200, 1000, 600, 50)

    # Adicionando opção para definir o número de linhas por página
    options_paginacao = [10, 25, 50, 100, 250, 500, 10000]
    default_index = options_paginacao.index(10000) if 10000 in options_paginacao else 0


    def format_page_size(opt):
        return "Mostrar todos" if opt == 10000 else str(opt)


    page_size = st.selectbox(
        "Linhas por página",
        options=options_paginacao,
        index=default_index,
        format_func=format_page_size
    )

    st.session_state["page_size"] = page_size

    # Uso de memória
    ram_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2
    st.sidebar.markdown(
        f'<div class="ram-indicator">💾 RAM usada: <b>{ram_mb:.0f} MB</b></div>',
        unsafe_allow_html=True
    )

# ─── 15. TABELA PERSONALIZADA COM FILTROS INTEGRADOS ────────────────
# 1. Colunas visíveis baseadas no nível de agregação
vis_cols = ["Ano"]

# Adicionar coluna UF apenas quando o nível de agregação for "Pernambuco"
if nivel == "Pernambuco":
    # Garantir que a coluna UF exista no DataFrame
    df_filtrado = df_filtrado.copy()  # Cria uma cópia para não modificar o original
    df_filtrado["UF"] = "Pernambuco"  # Cria a coluna com valor fixo
    vis_cols += ["UF"]  # Adiciona UF logo após o Ano

if nivel == "Escolas":
    vis_cols.extend(["Nome do Município", "Nome da Escola"])
elif nivel == "Municípios":
    vis_cols.append("Nome do Município")

# 2. Colunas de Etapa e Subetapa
vis_cols.append("Etapa")
vis_cols.append("Subetapa")

# 3. (NOVO) Coluna Ano/Série para Ensino Regular
if tipo_ensino == "Ensino Regular":
    # Pega o nome da coluna configurada em MODALIDADES
    config = MODALIDADES[tipo_ensino]
    # Se preferir usar o nome original ("Ano/Série"), verifique se existe:
    serie_col = config.serie_col if config.serie_col in df_filtrado.columns else "Série"
    vis_cols.append(serie_col)

# 4. Colunas finais
vis_cols.extend(["Rede", "Número de Matrículas"])

# Puxa só as colunas selecionadas (não precisamos mais renomear Etapa)
df_tabela = df_filtrado[vis_cols].copy()

# Não é mais necessário renomear a coluna, pois estamos usando o nome original "Etapa"
# df_tabela = df_tabela.rename(columns={etapa_col: "Etapa"})

# 4. CSS para centralizar coluna numérica
st.markdown("""
<style>

/* Centraliza a coluna de matrículas */
[data-testid="stDataFrame"] table tbody tr td:last-child,
[data-testid="stDataFrame"] table thead tr th:last-child {
    text-align:center !important;
}

/* Destaca linhas ao passar o mouse */
[data-testid="stDataFrame"] table tbody tr:hover {
    background-color: rgba(107, 129, 144, 0.1) !important;
}
section[data-testid="stSidebar"] {
  background: #2f3e4e !important;
  border-left: 4px solid #ffdfba !important;
}
/* Bordas mais claras e estilo mais limpo */
[data-testid="stDataFrame"] table {
    border-collapse: collapse !important;
}

[data-testid="stDataFrame"] table th {
    background-color: #f0f0f0 !important;
    border-bottom: 2px solid #ddd !important;
    font-weight: 600 !important;
}

[data-testid="stDataFrame"] table td {
    border-bottom: 1px solid #eee !important;
}
</style>
""", unsafe_allow_html=True)

# 5. Cabeçalhos dos Filtros de texto
col_headers = st.columns(len(vis_cols))
for col, slot in zip(vis_cols, col_headers):
    with slot:
        # Use beautify_column_header em vez de beautify para os cabeçalhos
        header_name = beautify_column_header(col)

        extra = " style='text-align:center'" if col == "Número de Matrículas" else ""
        st.markdown(f"<div class='column-header'{extra}>{header_name}</div>",
                    unsafe_allow_html=True)

# 6. Filtros de coluna
col_filters = st.columns(len(vis_cols))
filter_values = {}
for col, slot in zip(vis_cols, col_filters):
    with slot:
        filter_values[col] = st.text_input(
            f"Filtro para {beautify_column_header(col)}",
            key=f"filter_{col}",
            label_visibility="collapsed",
            placeholder=f"Filtrar {beautify_column_header(col).lower()}..."
        )

# 7. Aplicação dos filtros de texto com feedback visual
mask = pd.Series(True, index=df_tabela.index)
filtros_ativos = False

for col, val in filter_values.items():
    if val.strip():
        filtros_ativos = True
        s = df_tabela[col]
        if col.startswith("Número de") or pd.api.types.is_numeric_dtype(s):
            v = val.replace(",", ".")
            if re.fullmatch(r"-?\d+(\.\d+)?", v):
                # Filtro exato para números
                mask &= s == float(v)
            else:
                # Filtro por texto em valores numéricos convertidos
                mask &= s.astype(str).str.contains(val, case=False)
        else:
            # Filtro por texto em colunas de texto
            mask &= s.astype(str).str.contains(val, case=False)

df_texto = df_tabela[mask]

# 8. Mostrar feedback de filtros ativos
if filtros_ativos:
    num_filtrados = len(df_texto)
    num_total = len(df_tabela)
    st.markdown(
        f"<div style='margin-top:-10px;margin-bottom:10px;'>"
        f"<span style='font-size:0.85rem;color:#666;background:#f5f5f5;padding:2px 8px;border-radius:4px;'>"
        f"Filtro: <b>{format_number_br(num_filtrados)}</b> de "
        f"<b>{format_number_br(num_total)}</b> linhas"
        f"</span></div>",
        unsafe_allow_html=True
    )

# 9. Paginação
page_size = st.session_state.get("page_size", 10000)
pag = Paginator(len(df_texto), page_size=page_size,
                current=st.session_state.get("current_page", 1))
df_page = pag.slice(df_texto)

# 10. Formatação numérica
df_show = df_page.copy()

# Identificar colunas numéricas antes de renomear
colunas_numericas = df_show.filter(like="Número de").columns.tolist()

# Renomear as colunas para os cabeçalhos beautificados
df_show.columns = [beautify_column_header(col) for col in df_show.columns]

# Aplicar formatação às colunas numéricas renomeadas
for col in colunas_numericas:
    col_beautificada = beautify_column_header(col)
    if col_beautificada in df_show.columns:
        df_show[col_beautificada] = df_show[col_beautificada].apply(aplicar_padrao_numerico_brasileiro)

# 11. Configurar largura das colunas proporcionalmente
num_colunas = len(df_show.columns)
largura_base = 150  # Ajuste este valor conforme necessário
config_colunas = {
    col: {"width": f"{largura_base}px"} for col in df_show.columns
}

# Configuração especial para a coluna de matrículas (mais estreita)
col_matriculas = beautify_column_header("Número de Matrículas")
if col_matriculas in config_colunas:
    config_colunas[col_matriculas] = {"width": "120px"}

# 12. Exibir a tabela com todas as configurações
st.dataframe(
    df_show,
    column_config=config_colunas,
    height=altura_tabela,
    use_container_width=True,
    hide_index=True
)

# ─── 16. CONTROLES DE NAVEGAÇÃO ────────────────────────────────────
if pag.total_pages > 1:  # Só mostra controles se houver mais de uma página
    b1, b2, b3, b4 = st.columns([1, 1, 1, 2])

    with b1:
        if st.button("◀", disabled=pag.current == 1, key="prev_page",
                     help="Página anterior", use_container_width=True):
            st.session_state["current_page"] = pag.current - 1
            st.rerun()
    with b2:
        if st.button("▶", disabled=pag.current == pag.total_pages, key="next_page",
                     help="Próxima página", use_container_width=True):
            st.session_state["current_page"] = pag.current + 1
            st.rerun()

    with b3:
        # Opções de paginação com "Mostrar todos"
        page_options = [10, 25, 50, 100, 250, 500, 10000]


        # Função para formatar o rótulo
        def format_page_size(opt):
            return "Mostrar todos" if opt == 10000 else str(opt)


        new_ps = st.selectbox(
            "Itens por página",
            options=page_options,
            index=page_options.index(page_size),
            format_func=format_page_size,
            label_visibility="collapsed",
            key="page_size_select"
        )

        if new_ps != page_size:
            st.session_state["page_size"] = new_ps
            st.session_state["current_page"] = 1
            st.rerun()

    with b4:
        st.markdown(
            f"<div style='text-align:right;padding-top:8px;'>"
            f"<span style='font-weight:500;'>"
            f"Página {pag.current}/{pag.total_pages} · "
            f"{format_number_br(len(df_texto))} linhas</span></div>",
            unsafe_allow_html=True
        )
else:
    # Se houver apenas uma página, mostra apenas o total de linhas
    st.markdown(
        f"""
        <div style="text-align: right; padding: 8px 0;">
            <span style="font-family: Arial, sans-serif; font-weight: 600;">Total:</span>
            <span>{format_number_br(len(df_texto))} linhas</span>
        </div>
        """,
        unsafe_allow_html=True
    )


# ─── 17. DOWNLOADS (on‑click) ───────────────────────────────────────
def gerar_csv():
    """Prepara os dados para download em formato CSV"""
    # Usar df_texto que já contém os dados filtrados
    try:
        csv_data = df_texto.to_csv(index=False).encode("utf-8")
        st.session_state["csv_bytes"] = csv_data
        st.session_state["download_pronto"] = True
        return csv_data
    except Exception as e:
        st.error(f"Erro ao gerar CSV: {str(e)}")
        return None


def gerar_xlsx():
    """Prepara os dados para download em formato Excel"""
    try:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
            # Configura a planilha com formatação melhorada
            df_texto.to_excel(w, index=False, sheet_name="Dados")
            # Acessa a planilha para formatar
            worksheet = w.sheets["Dados"]
            # Formata os cabeçalhos
            header_format = w.book.add_format({
                'bold': True,
                'bg_color': '#FFDFBA',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            for col_num, value in enumerate(df_texto.columns.values):
                worksheet.write(0, col_num, value, header_format)
            # Ajusta largura das colunas
            for i, col in enumerate(df_texto.columns):
                max_len = max(
                    df_texto[col].astype(str).apply(len).max(),
                    len(str(col))
                ) + 2  # adiciona um pouco de espaço
                worksheet.set_column(i, i, max_len)

        st.session_state["xlsx_bytes"] = buf.getvalue()
        st.session_state["download_pronto"] = True
        return buf.getvalue()
    except Exception as e:
        st.error(f"Erro ao gerar Excel: {str(e)}")
        return None


# Adicionar um título para os botões de download
st.sidebar.markdown("### Download")

# Informação sobre os dados que serão baixados
num_linhas_download = len(df_texto)
st.sidebar.markdown(
    f"<div style='font-size:0.85rem;margin-bottom:8px;color:white;'>"
    f"Download de <b>{format_number_br(num_linhas_download)}</b> linhas"
    f"</div>",
    unsafe_allow_html=True
)

# Criar duas colunas na sidebar para os botões
col1, col2 = st.sidebar.columns(2)

# Colocar o botão CSV na primeira coluna
with col1:
    st.download_button(
        "Em CSV",
        data=gerar_csv() if "csv_bytes" not in st.session_state else st.session_state["csv_bytes"],
        key="csv_dl",
        mime="text/csv",
        file_name=f"dados_{datetime.now().strftime('%Y%m%d')}.csv",
        on_click=gerar_csv,
        disabled=len(df_texto) == 0
    )

# Colocar o botão Excel na segunda coluna
with col2:
    st.download_button(
        "Em Excel",
        data=io.BytesIO().getvalue() if "xlsx_bytes" not in st.session_state else st.session_state["xlsx_bytes"],
        key="xlsx_dl",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_name=f"dados_{datetime.now().strftime('%Y%m%d')}.xlsx",
        on_click=gerar_xlsx,
        disabled=len(df_texto) == 0
    )

# ─── 18. RODAPÉ ─────────────────────────────────────────────────────
st.markdown("---")

# Layout de rodapé em colunas
footer_left, footer_right = st.columns([3, 1])

with footer_left:
    st.caption("© Dashboard Educacional – atualização: Mai 2025")

    # Informações de desempenho
    delta = time.time() - st.session_state.get("tempo_inicio", time.time())
    tempo_carga = st.session_state.get("tempo_carga", 0)

    st.caption(
        f"⏱️ Tempo de processamento: {delta:.2f}s (carga: {tempo_carga:.2f}s)"
    )

with footer_right:
    # Build info mais visível
    st.caption(f"Build: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

# Reinicia o timer para a próxima atualização
st.session_state["tempo_inicio"] = time.time()
# ====================================================================