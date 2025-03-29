import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from pathlib import Path
import io
import json
import re
from constantes import *
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -------------------------------
# Configuração Inicial da Página
# -------------------------------
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

css_sidebar = """
<style>
    /* Cria um overlay para toda a sidebar */
    [data-testid="stSidebar"]::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: #364b60;
        z-index: -1;
        border-radius: 1px;
        margin: 1rem;
        padding: 1rem;
    }

    /* Garante que os controles fiquem visíveis acima do overlay */
    [data-testid="stSidebar"] > div {
        position: relative;
        z-index: 1;
    }

    /* Texto branco para todos os elementos */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stRadio span:not([role="radio"]) {
        color: white !important;
    }

    /* Mantém o texto das opções em preto */
    [data-testid="stSidebar"] option,
    [data-testid="stSidebar"] select,
    [data-testid="stSidebar"] [data-baseweb="select"] div {
        color: black !important;
    }

    /* ------ REGRAS ATUALIZADAS ------ */
    /* Altera TODOS os itens selecionados na sidebar */
    [data-testid="stSidebar"] .stMultiSelect [aria-selected="true"] {
        background-color: #364b60 !important;
        color: white !important;
        border-radius: 1px !important;
    }

    /* Altera o hover */
    [data-testid="stSidebar"] .stMultiSelect [aria-selected="true"]:hover {
        background-color: #2a3a4d !important;
        cursor: pointer;
    }

    /* Remove a cor azul padrão do Streamlit */
    [data-testid="stSidebar"] .stMultiSelect [aria-selected="true"]:focus {
        box-shadow: none !important;
    }
</style>
"""

st.markdown(css_sidebar, unsafe_allow_html=True)

css_pills = """
<style>
    /* Estilo específico para os pills na barra lateral */
    [data-testid="stSidebar"] div[data-testid="stPills"] {
        margin-top: 8px;
    }

    /* Botões não selecionados (kind="pills") */
    button[kind="pills"][data-testid="stBaseButton-pills"] {
        background-color: transparent !important;
        color: white !important;
        border: 1px solid #e37777 !important;
        border-radius: 1px !important;
        /* etc. */
    }

    /* Botões selecionados (kind="pillsActive") */
    button[kind="pillsActive"][data-testid="stBaseButton-pillsActive"] {
        background-color: #e37777 !important; 
        color: white !important;          
        border: none !important;
        border-radius: 1px !important;
        /* etc. */
    }

    /* Caso precise estilizar o <p> lá dentro (texto em si) */
    button[kind="pillsActive"][data-testid="stBaseButton-pillsActive"] p {
        color: white !important;
        font-weight: bold; /* Exemplo extra */
    }
</style>
"""

st.markdown(css_pills, unsafe_allow_html=True)


# -------------------------------
# Funções Auxiliares
# -------------------------------
def formatar_numero(numero):
    """
    Formata números grandes adicionando separadores de milhar em padrão BR:
    Ex.: 1234567 -> '1.234.567'
         1234.56 -> '1.234,56'
    Se o número for NaN ou '-', retorna '-'.
    """
    if pd.isna(numero) or numero == "-":
        return "-"
    try:
        # Exibe sem casas decimais se for inteiro
        if float(numero).is_integer():
            return f"{int(numero):,}".replace(",", ".")
        else:
            # 2 casas decimais
            parte_inteira = int(float(numero))
            parte_decimal = abs(float(numero) - parte_inteira)
            inteiro_fmt = f"{parte_inteira:,}".replace(",", ".")
            decimal_fmt = f"{parte_decimal:.2f}".replace("0.", "").replace(".", ",")
            return f"{inteiro_fmt},{decimal_fmt}"
    except (ValueError, TypeError):
        return str(numero)


@st.cache_data
def carregar_dados():
    """
    Carrega os dados das planilhas no formato Parquet.
    - Lê os arquivos: escolas.parquet, estado.parquet e municipio.parquet.
    - Converte colunas que começam com 'Número de' para tipo numérico.
    Em caso de erro, exibe uma mensagem e interrompe a execução.
    """
    try:
        diretorios_possiveis = [".", "data", "dados", os.path.join(os.path.dirname(__file__), "data")]

        escolas_df = estado_df = municipio_df = None
        for diretorio in diretorios_possiveis:
            escolas_path = os.path.join(diretorio, "escolas.parquet")
            estado_path = os.path.join(diretorio, "estado.parquet")
            municipio_path = os.path.join(diretorio, "municipio.parquet")

            if os.path.exists(escolas_path) and os.path.exists(estado_path) and os.path.exists(municipio_path):
                escolas_df = pd.read_parquet(escolas_path)
                estado_df = pd.read_parquet(estado_path)
                municipio_df = pd.read_parquet(municipio_path)
                break

        if escolas_df is None or estado_df is None or municipio_df is None:
            raise FileNotFoundError(ERRO_ARQUIVOS_NAO_ENCONTRADOS)

        for df_ in [escolas_df, estado_df, municipio_df]:
            for col in df_.columns:
                if col.startswith("Número de"):
                    df_[col] = pd.to_numeric(df_[col], errors='coerce')

        return escolas_df, estado_df, municipio_df

    except Exception as e:
        st.error(ERRO_CARREGAR_DADOS.format(e))
        st.info(INFO_VERIFICAR_ARQUIVOS)
        st.stop()


@st.cache_data
def carregar_mapeamento_colunas():
    """
    Carrega o mapeamento de colunas a partir do arquivo JSON.
    """
    try:
        diretorios_possiveis = [".", "data", "dados", os.path.join(os.path.dirname(__file__), "data")]

        for diretorio in diretorios_possiveis:
            json_path = os.path.join(diretorio, "mapeamento_colunas.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)

        raise FileNotFoundError("Arquivo mapeamento_colunas.json não encontrado")

    except Exception as e:
        st.error(f"Erro ao carregar o mapeamento de colunas: {e}")
        st.stop()


def criar_mapeamento_colunas(df):
    colunas_map = {col.lower().strip(): col for col in df.columns}

    def obter_coluna_real(nome_padrao):
        if nome_padrao in df.columns:
            return nome_padrao
        nome_normalizado = nome_padrao.lower().strip()
        if nome_normalizado in colunas_map:
            return colunas_map[nome_normalizado]
        return nome_padrao

    mapeamento_base = carregar_mapeamento_colunas()
    mapeamento_ajustado = {}

    for etapa, config in mapeamento_base.items():
        mapeamento_ajustado[etapa] = {
            "coluna_principal": obter_coluna_real(config.get("coluna_principal", "")),
            "subetapas": {},
            "series": {}
        }

        for subetapa, coluna in config.get("subetapas", {}).items():
            mapeamento_ajustado[etapa]["subetapas"][subetapa] = obter_coluna_real(coluna)

        for sub, series_dict in config.get("series", {}).items():
            if sub not in mapeamento_ajustado[etapa]["series"]:
                mapeamento_ajustado[etapa]["series"][sub] = {}
            for serie, col_serie in series_dict.items():
                mapeamento_ajustado[etapa]["series"][sub][serie] = obter_coluna_real(col_serie)

    return mapeamento_ajustado


def obter_coluna_dados(etapa, subetapa, serie, mapeamento):
    if etapa not in mapeamento:
        st.error(ERRO_ETAPA_NAO_ENCONTRADA.format(etapa))
        return ""

    if subetapa == "Todas":
        return mapeamento[etapa].get("coluna_principal", "")

    if "subetapas" not in mapeamento[etapa] or subetapa not in mapeamento[etapa]["subetapas"]:
        st.warning(ERRO_SUBETAPA_NAO_ENCONTRADA.format(subetapa, etapa))
        return mapeamento[etapa].get("coluna_principal", "")

    if serie == "Todas":
        return mapeamento[etapa]["subetapas"][subetapa]

    series_subetapa = mapeamento[etapa].get("series", {}).get(subetapa, {})
    if not series_subetapa or serie not in series_subetapa:
        st.warning(ERRO_SERIE_NAO_ENCONTRADA.format(serie, subetapa))
        return mapeamento[etapa]["subetapas"][subetapa]

    return series_subetapa[serie]


def verificar_coluna_existe(df, coluna_nome):
    if not coluna_nome:
        return False, ""
    if coluna_nome in df.columns:
        return True, coluna_nome
    coluna_normalizada = coluna_nome.lower().strip()
    colunas_normalizadas = {col.lower().strip(): col for col in df.columns}
    if coluna_normalizada in colunas_normalizadas:
        return True, colunas_normalizadas[coluna_normalizada]
    return False, coluna_nome


def converter_df_para_csv(df):
    if df is None or df.empty:
        return "Não há dados para exportar.".encode('utf-8')
    try:
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        st.error(f"Erro ao converter para CSV: {str(e)}")
        return "Erro na conversão".encode('utf-8')


def converter_df_para_excel(df):
    if df is None or df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame({"Sem dados": []}).to_excel(writer, index=False, sheet_name='Sem_Dados')
        return output.getvalue()
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')
        return output.getvalue()
    except Exception as e:
        st.error(f"Erro ao converter para Excel: {str(e)}")
        output = io.BytesIO()
        output.write("Erro na conversão".encode('utf-8'))
        return output.getvalue()


def exibir_tabela_plotly_avancada(df_para_exibir, altura=600, coluna_dados=None, posicao_totais="bottom",
                                  tipo_visualizacao=None):
    """
    Versão avançada da exibição de DataFrame usando Plotly Table
    """
    if df_para_exibir is None or df_para_exibir.empty:
        st.warning("Não há dados para exibir na tabela.")
        return {"data": pd.DataFrame()}

    # Verificar se o conjunto de dados é muito grande
    is_very_large_dataset = len(df_para_exibir) > 10000
    if is_very_large_dataset:
        st.warning(
            f"O conjunto de dados tem {formatar_numero(len(df_para_exibir))} linhas, "
            "o que pode causar lentidão na visualização."
        )
        mostrar_tudo = st.checkbox("Carregar todos os dados (pode ser lento)", value=False)
        if not mostrar_tudo:
            df_para_exibir = df_para_exibir.head(5000).copy()
            st.info("Mostrando amostra de 5.000 registros (de um total maior)")

    # Criar uma cópia para não modificar o DataFrame original
    df_exibicao = df_para_exibir.copy()

    # Calcular totais para colunas numéricas
    totais = {}
    if coluna_dados and coluna_dados in df_exibicao.columns:
        for col in df_exibicao.columns:
            if col.startswith("Número de") or col == coluna_dados:
                try:
                    totais[col] = df_para_exibir[col].sum()
                except:
                    totais[col] = ""

    # Formatar colunas numéricas
    for col in df_exibicao.columns:
        if col.startswith("Número de") or col == coluna_dados:
            if pd.api.types.is_numeric_dtype(df_exibicao[col]):
                df_exibicao[col] = df_exibicao[col].apply(lambda x: formatar_numero(x) if pd.notnull(x) else "-")

    # Definir cores e estilos
    header_color = '#364b60'
    cell_colors = ['#f9f9f9', 'white']
    total_row_color = '#e6f2ff'

    # Preparar dados
    header_values = list(df_exibicao.columns)
    cell_values = [df_exibicao[col].tolist() for col in df_exibicao.columns]

    # Configurações de estilo das células
    cell_align = ['center'] * len(df_exibicao.columns)

    # Criar lista de cores para alternância de linhas
    if len(df_exibicao) > 0:
        fill_color = []
        for i, col in enumerate(df_exibicao.columns):
            if posicao_totais == "top":
                # Primeira linha é o total
                row_colors = [total_row_color] + [cell_colors[j % 2] for j in range(len(df_exibicao))]
            elif posicao_totais == "bottom":
                # Última linha é o total
                row_colors = [cell_colors[j % 2] for j in range(len(df_exibicao))] + [total_row_color]
            else:
                # Sem linha de total
                row_colors = [cell_colors[j % 2] for j in range(len(df_exibicao))]
            fill_color.append(row_colors)
    else:
        fill_color = [cell_colors[0]]

    # Adicionar linha de totais se necessário
    if posicao_totais in ["top", "bottom"] and totais:
        total_row = []
        for col in df_exibicao.columns:
            if col == list(df_exibicao.columns)[0]:
                total_row.append("TOTAL")
            elif col in totais:
                total_row.append(formatar_numero(totais[col]))
            else:
                total_row.append("")

        if posicao_totais == "top":
            cell_values = [[total_row[i]] + values for i, values in enumerate(cell_values)]
        else:  # bottom
            cell_values = [values + [total_row[i]] for i, values in enumerate(cell_values)]

    # Criar a tabela Plotly
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=header_values,
            fill_color=header_color,
            align='center',
            font=dict(color='white', size=13, family="Arial"),
            height=40
        ),
        cells=dict(
            values=cell_values,
            fill_color=fill_color if len(df_exibicao) > 0 else [cell_colors[0]],
            align=cell_align,
            font=dict(color='black', size=12, family="Arial"),
            height=35,
            line=dict(color='#d6d6d6', width=1)
        )
    )])

    # Adicionar estatísticas abaixo da tabela se coluna_dados existir
    if coluna_dados and coluna_dados in df_para_exibir.columns:
        try:
            dados_numericos = pd.to_numeric(df_para_exibir[coluna_dados], errors='coerce')
            soma = dados_numericos.sum()
            media = dados_numericos.mean()
            minimo = dados_numericos.min()
            maximo = dados_numericos.max()

            estatisticas = (
                f"Total: {formatar_numero(soma)} | "
                f"Média: {formatar_numero(media)} | "
                f"Mín: {formatar_numero(minimo)} | "
                f"Máx: {formatar_numero(maximo)}"
            )

            # Mostrar estatísticas abaixo da tabela
            st.caption(estatisticas)
        except Exception as e:
            st.caption(f"Não foi possível calcular estatísticas: {str(e)}")

    # Ajustar layout
    fig.update_layout(
        margin=dict(l=5, r=5, t=5, b=5),
        height=altura
    )

    # Exibir a tabela
    st.plotly_chart(fig, use_container_width=True, config={
        'displayModeBar': False,
        'scrollZoom': True
    })

    # Retornar estrutura semelhante ao AgGrid para compatibilidade
    return {"data": df_para_exibir}


# -------------------------------
# Carregamento de Dados
# -------------------------------
try:
    escolas_df, estado_df, municipio_df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    st.stop()

# ======================================
# CONFIGURAÇÃO DA BARRA LATERAL (FILTROS)
# ======================================
st.sidebar.title("Filtros")

tipo_visualizacao = st.sidebar.radio(
    "Nível de Agregação:",
    ["Escola", "Município", "Estado"]
)

if tipo_visualizacao == "Escola":
    df = escolas_df
elif tipo_visualizacao == "Município":
    df = municipio_df
else:
    df = estado_df

mapeamento_colunas = criar_mapeamento_colunas(df)

# Filtro do Ano
if "ANO" in df.columns:
    anos_disponiveis = sorted(df["ANO"].unique(), reverse=True)
    anos_selecionados = st.sidebar.multiselect(
        "Ano do Censo:",
        options=anos_disponiveis,
        default=[anos_disponiveis[0]],
        key="anos_multiselect"
    )
    if not anos_selecionados:
        st.warning("Por favor, selecione pelo menos um ano.")
        st.stop()

    df_filtrado = df[df["ANO"].isin(anos_selecionados)]
else:
    st.error("A coluna 'ANO' não foi encontrada nos dados carregados.")
    st.stop()

etapas_disponiveis = list(mapeamento_colunas.keys())
etapa_selecionada = st.sidebar.selectbox(
    "Etapa de Ensino:",
    etapas_disponiveis
)

if etapa_selecionada not in mapeamento_colunas:
    st.error(f"A etapa '{etapa_selecionada}' não foi encontrada no mapeamento de colunas.")
    st.stop()

# Filtro de Subetapa
if "subetapas" in mapeamento_colunas[etapa_selecionada] and mapeamento_colunas[etapa_selecionada]["subetapas"]:
    subetapas_disponiveis = list(mapeamento_colunas[etapa_selecionada]["subetapas"].keys())
    subetapa_selecionada = st.sidebar.selectbox(
        "Subetapa:",
        ["Todas"] + subetapas_disponiveis
    )
else:
    subetapa_selecionada = "Todas"

# Filtro de Série
series_disponiveis = []
if (subetapa_selecionada != "Todas"
        and "series" in mapeamento_colunas[etapa_selecionada]
        and subetapa_selecionada in mapeamento_colunas[etapa_selecionada]["series"]):
    series_disponiveis = list(mapeamento_colunas[etapa_selecionada]["series"][subetapa_selecionada].keys())
    serie_selecionada = st.sidebar.selectbox(
        "Série:",
        ["Todas"] + series_disponiveis
    )
else:
    serie_selecionada = "Todas"

if "DEPENDENCIA ADMINISTRATIVA" in df.columns:
    dependencias_disponiveis = sorted(df["DEPENDENCIA ADMINISTRATIVA"].unique())
    dependencia_selecionada = st.sidebar.pills(
        "DEPENDENCIA ADMINISTRATIVA:",
        options=dependencias_disponiveis,
        default=dependencias_disponiveis,
        selection_mode="multi",
        label_visibility="visible"
    )
    if dependencia_selecionada:
        df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"].isin(dependencia_selecionada)]
    else:
        df_filtrado = df_filtrado[0:0]
else:
    st.warning("A coluna 'DEPENDENCIA ADMINISTRATIVA' não foi encontrada nos dados carregados.")

coluna_dados = obter_coluna_dados(etapa_selecionada, subetapa_selecionada, serie_selecionada, mapeamento_colunas)
coluna_existe, coluna_real = verificar_coluna_existe(df_filtrado, coluna_dados)
if coluna_existe:
    coluna_dados = coluna_real
    df_filtrado = df_filtrado[pd.to_numeric(df_filtrado[coluna_dados], errors='coerce') > 0]
else:
    st.warning(f"A coluna '{coluna_dados}' não está disponível nos dados.")
    coluna_principal = mapeamento_colunas[etapa_selecionada].get("coluna_principal", "")
    coluna_existe, coluna_principal_real = verificar_coluna_existe(df_filtrado, coluna_principal)
    if coluna_existe:
        coluna_dados = coluna_principal_real
        st.info(f"Usando '{coluna_dados}' como alternativa")
        df_filtrado = df_filtrado[pd.to_numeric(df_filtrado[coluna_dados], errors='coerce') > 0]
    else:
        st.error("Não foi possível encontrar dados para a etapa selecionada.")
        st.stop()

# -------------------------------
# Cabeçalho e Informações Iniciais
# -------------------------------
st.title(TITULO_DASHBOARD)
anos_texto = ", ".join(map(str, anos_selecionados))
st.markdown(f"**Visualização por {tipo_visualizacao} - Anos: {anos_texto}**")

filtro_texto = f"**Etapa:** {etapa_selecionada}"
if subetapa_selecionada != "Todas":
    filtro_texto += f" | **Subetapa:** {subetapa_selecionada}"
    if serie_selecionada != "Todas" and serie_selecionada in series_disponiveis:
        filtro_texto += f" | **Série:** {serie_selecionada}"
st.markdown(filtro_texto)

# -------------------------------
# Seção de Indicadores (KPIs)
# -------------------------------
col1, col2, col3 = st.columns(3)

try:
    total_matriculas = df_filtrado[coluna_dados].sum()
    with col1:
        st.metric(ROTULO_TOTAL_MATRICULAS, formatar_numero(total_matriculas))
except Exception as e:
    with col1:
        st.metric("Total de Matrículas", "-")
        st.caption(f"Erro ao calcular: {str(e)}")

with col2:
    try:
        if tipo_visualizacao == "Escola":
            if len(df_filtrado) > 0:
                media_por_escola = df_filtrado[coluna_dados].mean()
                st.metric(ROTULO_MEDIA_POR_ESCOLA, formatar_numero(media_por_escola))
            else:
                st.metric("Média de Matrículas por Escola", "-")
        else:
            if "DEPENDENCIA ADMINISTRATIVA" in df_filtrado.columns:
                media_por_dependencia = df_filtrado.groupby("DEPENDENCIA ADMINISTRATIVA")[coluna_dados].mean()
                if not media_por_dependencia.empty:
                    media_geral = media_por_dependencia.mean()
                    st.metric(ROTULO_MEDIA_MATRICULAS, formatar_numero(media_geral))
                else:
                    st.metric("Média de Matrículas", "-")
            else:
                st.metric("Média de Matrículas", formatar_numero(df_filtrado[coluna_dados].mean()))
    except Exception as e:
        st.metric("Média de Matrículas", "-")
        st.caption(f"Erro ao calcular: {str(e)}")

with col3:
    try:
        if tipo_visualizacao == "Escola":
            total_escolas = len(df_filtrado)
            st.metric(ROTULO_TOTAL_ESCOLAS, formatar_numero(total_escolas))
        elif tipo_visualizacao == "Município":
            total_municipios = len(df_filtrado)
            st.metric(ROTULO_TOTAL_MUNICIPIOS, formatar_numero(total_municipios))
        else:
            max_valor = df_filtrado[coluna_dados].max()
            st.metric(ROTULO_MAXIMO_MATRICULAS, formatar_numero(max_valor))
    except Exception as e:
        if tipo_visualizacao == "Escola":
            st.metric("Total de Escolas", "-")
        elif tipo_visualizacao == "Município":
            st.metric("Total de Municípios", "-")
        else:
            st.metric("Máximo de Matrículas", "-")
        st.caption(f"Erro ao calcular: {str(e)}")

# -------------------------------
# Seção de Tabela de Dados Detalhados
# -------------------------------
st.markdown(f"## {TITULO_DADOS_DETALHADOS}")

colunas_tabela = []
if "ANO" in df_filtrado.columns:
    colunas_tabela.append("ANO")

if tipo_visualizacao == "Escola":
    colunas_adicionais = [
        "CODIGO DA ESCOLA",
        "NOME DA ESCOLA",
        "CODIGO DO MUNICIPIO",
        "NOME DO MUNICIPIO",
        "CODIGO DA UF",
        "NOME DA UF",
        "DEPENDENCIA ADMINISTRATIVA"
    ]
elif tipo_visualizacao == "Município":
    colunas_adicionais = [
        "CODIGO DO MUNICIPIO",
        "NOME DO MUNICIPIO",
        "CODIGO DA UF",
        "NOME DA UF",
        "DEPENDENCIA ADMINISTRATIVA"
    ]
else:
    colunas_adicionais = [
        "CODIGO DA UF",
        "NOME DA UF",
        "DEPENDENCIA ADMINISTRATIVA"
    ]

for col in colunas_adicionais:
    if col in df_filtrado.columns:
        colunas_tabela.append(col)

if coluna_dados in df_filtrado.columns:
    colunas_tabela.append(coluna_dados)

colunas_existentes = [c for c in colunas_tabela if c in df_filtrado.columns]
colunas_tabela = colunas_existentes

if coluna_dados in df_filtrado.columns:
    with pd.option_context('mode.chained_assignment', None):
        df_filtrado_tabela = df_filtrado[colunas_tabela].copy()
        df_filtrado_tabela[coluna_dados] = pd.to_numeric(df_filtrado_tabela[coluna_dados], errors='coerce')

    tabela_dados = df_filtrado_tabela.sort_values(by=coluna_dados, ascending=False)
    tabela_exibicao = tabela_dados.copy()
else:
    tabela_dados = df_filtrado[colunas_existentes].copy()
    tabela_exibicao = tabela_dados.copy()

tabela_filtrada = tabela_exibicao.copy()

# Por simplicidade, chamamos de 'tabela_com_totais'
tabela_com_totais = tabela_filtrada

altura_tabela = 600

if 'posicao_totais' not in locals():
    posicao_totais = "Rodapé"

posicao_totais_map = {
    "Rodapé": "bottom",
    "Topo": "top",
    "Nenhum": None
}

if coluna_dados and coluna_dados in tabela_com_totais.columns:
    with pd.option_context('mode.chained_assignment', None):
        tabela_com_totais[coluna_dados] = pd.to_numeric(tabela_com_totais[coluna_dados], errors='coerce')
        tabela_com_totais[coluna_dados] = tabela_com_totais[coluna_dados].fillna(0)

try:
    grid_result = exibir_tabela_plotly_avancada(
        tabela_com_totais,
        altura=altura_tabela,
        coluna_dados=coluna_dados,
        posicao_totais=posicao_totais_map.get(posicao_totais),
        tipo_visualizacao=tipo_visualizacao
    )
except Exception as e:
    st.error(f"Erro ao exibir tabela com Plotly: {str(e)}")
    st.dataframe(tabela_com_totais, height=altura_tabela)

tab1, tab2 = st.tabs(["Configurações", "Resumo Estatístico"])

with tab1:
    st.write("### Configurações de exibição")
    col1, col2 = st.columns(2)

    with col1:
        altura_personalizada = st.checkbox(ROTULO_AJUSTAR_ALTURA, value=False, help=DICA_ALTURA_TABELA)
        if altura_personalizada:
            altura_manual = st.slider("Altura da tabela (pixels)", 200, 1000, 600, 50)
        else:
            altura_manual = 600

    with col2:
        posicao_totais = st.radio(
            "Linha de totais:",
            ["Rodapé", "Topo", "Nenhum"],
            index=0,
            horizontal=True
        )

    altura_tabela = altura_manual

    st.write("### Incluir outras colunas na tabela")
    col5, col6 = st.columns([1, 5])
    with col5:
        st.write("**Colunas:**")
    with col6:
        todas_colunas = [col for col in df_filtrado.columns if col not in colunas_tabela]
        if todas_colunas:
            colunas_adicionais = st.multiselect(
                "",
                todas_colunas,
                label_visibility="collapsed",
                placeholder="Selecionar colunas adicionais..."
            )
            if colunas_adicionais:
                colunas_tabela.extend(colunas_adicionais)
                try:
                    if 'df_filtrado_tabela' in locals():
                        tabela_dados = df_filtrado[colunas_tabela].sort_values(by=coluna_dados, ascending=False)
                    else:
                        tabela_dados = df_filtrado[colunas_tabela].copy()
                    tabela_exibicao = tabela_dados.copy()
                except Exception as e:
                    st.error(f"Erro ao adicionar colunas: {str(e)}")
        else:
            st.write("Não há colunas adicionais disponíveis")

    tabela_filtrada = tabela_exibicao.copy()
    if len(tabela_exibicao) > 1000:
        col_filtrar = st.columns([1])[0]
        with col_filtrar:
            aplicar_filtros = st.button("Aplicar Filtros", type="primary")
        mostrar_dica = True
    else:
        aplicar_filtros = True
        mostrar_dica = False

    try:
        tabela_com_totais = tabela_filtrada
    except Exception as e:
        st.warning(f"Não foi possível adicionar a linha de totais: {str(e)}")

    col1, col2 = st.columns(2)
    with col1:
        try:
            csv_data = converter_df_para_csv(tabela_dados)
            st.download_button(
                label=ROTULO_BTN_DOWNLOAD_CSV,
                data=csv_data,
                file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{"-".join(map(str, anos_selecionados))}.csv',
                mime='text/csv',
            )
        except Exception as e:
            st.error(f"Erro ao preparar CSV para download: {str(e)}")

    with col2:
        try:
            excel_data = converter_df_para_excel(tabela_dados)
            st.download_button(
                label=ROTULO_BTN_DOWNLOAD_EXCEL,
                data=excel_data,
                file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{"-".join(map(str, anos_selecionados))}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        except Exception as e:
            st.error(f"Erro ao preparar Excel para download: {str(e)}")

with tab2:
    st.write("### Resumo Estatístico")

    if coluna_dados and coluna_dados in df_filtrado.columns:
        try:
            # Calcular estatísticas para a coluna de dados principal
            descricao = df_filtrado[coluna_dados].describe()

            # Formatar estatísticas
            estatisticas = {
                "Total": formatar_numero(df_filtrado[coluna_dados].sum()),
                "Média": formatar_numero(descricao["mean"]),
                "Mediana": formatar_numero(descricao["50%"]),
                "Desvio Padrão": formatar_numero(descricao["std"]),
                "Mínimo": formatar_numero(descricao["min"]),
                "Máximo": formatar_numero(descricao["max"]),
                "Contagem": formatar_numero(descricao["count"])
            }

            # Criar DataFrame para exibição
            df_stats = pd.DataFrame(list(estatisticas.items()), columns=["Estatística", "Valor"])

            # Exibir resumo estatístico em tabela
            st.table(df_stats)

            # Adicionar gráfico de distribuição
            st.write("### Distribuição dos Dados")
            fig = px.histogram(
                df_filtrado,
                x=coluna_dados,
                nbins=30,
                title=f"Distribuição de {coluna_dados}",
                labels={coluna_dados: coluna_dados}
            )
            fig.update_layout(bargap=0.1)
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao gerar estatísticas: {str(e)}")
    else:
        st.info("Selecione uma coluna de dados para visualizar estatísticas.")

# -------------------------------
# Rodapé do Dashboard
# -------------------------------
st.markdown("---")
st.markdown(RODAPE_NOTA)