import streamlit as st
import pandas as pd
import numpy as np
import os
from pathlib import Path
import io
import json
import re
from constantes import *

# Biblioteca do AgGrid
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

# Inicialização do tempo de execução
import time

if 'tempo_inicio' not in st.session_state:
    st.session_state['tempo_inicio'] = time.time()

# -------------------------------
# Configuração Inicial da Página
# -------------------------------
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS unificado e otimizado
css_unificado = """
/* CSS Unificado e Otimizado para o Dashboard */

/* Estilo da Barra Lateral */
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

[data-testid="stSidebar"] > div {
    position: relative;
    z-index: 1;
}

/* Texto branco para elementos da barra lateral */
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

/* Estilo de itens selecionados na barra lateral */
[data-testid="stSidebar"] .stMultiSelect [aria-selected="true"] {
    background-color: #e37777 !important;
    color: white !important;
    border-radius: 1px !important;
}

/* Estilo do hover */
[data-testid="stSidebar"] .stMultiSelect [aria-selected="true"]:hover {
    background-color: #d66c6c !important;
    cursor: pointer;
}

/* Remove a cor azul padrão do Streamlit */
[data-testid="stSidebar"] .stMultiSelect [aria-selected="true"]:focus {
    box-shadow: none !important;
}

/* Estilo dos pills na barra lateral */
[data-testid="stSidebar"] div[data-testid="stPills"] {
    margin-top: 8px;
}

/* Botões não selecionados (kind="pills") */
button[kind="pills"][data-testid="stBaseButton-pills"] {
    background-color: transparent !important;
    color: white !important;
    border: 1px solid #e37777 !important;
    border-radius: 1px !important;
    transition: all 0.3s ease;
}

/* Hover em botões não selecionados */
button[kind="pills"][data-testid="stBaseButton-pills"]:hover {
    background-color: rgba(227, 119, 119, 0.2) !important;
}

/* Botões selecionados (kind="pillsActive") */
button[kind="pillsActive"][data-testid="stBaseButton-pillsActive"] {
    background-color: #e37777 !important; 
    color: white !important;          
    border: none !important;
    border-radius: 1px !important;
}

/* Texto nos botões ativos */
button[kind="pillsActive"][data-testid="stBaseButton-pillsActive"] p {
    color: white !important;
    font-weight: bold;
}

/* Estilo para a área principal do dashboard */
.main-header {
    background-color: #f9f9f9;
    padding: 1rem;
    border-radius: 5px;
    margin-bottom: 1rem;
    border-left: 5px solid #364b60;
}

/* Estilos para a tabela Ag-Grid */
.aggrid-custom {
    --ag-header-background-color: #364b60;
    --ag-header-foreground-color: white;
    --ag-header-cell-hover-background-color: #25344d;
    --ag-header-column-separator-color: rgba(255, 255, 255, 0.3);
    --ag-header-column-separator-width: 1px;

    --ag-odd-row-background-color: rgba(54, 75, 96, 0.05);
    --ag-row-hover-color: rgba(54, 75, 96, 0.1);
    --ag-selected-row-background-color: transparent;

    --ag-font-size: 12px;
    --ag-font-family: Arial, sans-serif;
}

/* Centralização de cabeçalhos */
.ag-header-cell {
    display: flex !important;
    width: 100% !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}

.ag-header-cell-label {
    display: flex !important;
    width: 100% !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}

.ag-header-cell-text {
    display: flex !important;
    text-align: center !important;
    align-items: center !important;
    width: 100% !important;
    justify-content: center !important;
    font-weight: bold !important;
    white-space: normal !important;
    line-height: 1.2 !important;
    overflow: visible !important;
    font-size: 12px !important;
}

/* Células numéricas */
.numeric-cell { 
    display: flex !important;
    text-align: center !important;
    width: 100% !important;
    justify-content: center !important;
}

/* Pinned rows (totais) */
.ag-row-pinned {
    font-weight: bold !important;
    background-color: #f8dcdc !important;
}

.ag-row-pinned .ag-cell {
    text-align: center !important;
}

/* Células selecionadas - corrigindo o problema da seleção de linhas */
.ag-cell.ag-cell-range-selected,
.ag-cell.ag-cell-range-selected-1,
.ag-cell.ag-cell-range-selected-2,
.ag-cell.ag-cell-range-selected-3,
.ag-cell.ag-cell-range-selected-4 {
    background-color: #e6f2ff !important; 
    color: #000 !important; 
}

/* Remove linhas selecionadas por completo */
.ag-row-selected {
    background-color: transparent !important;
}

.ag-row-selected:hover {
    background-color: rgba(54, 75, 96, 0.1) !important;
}

/* Garantir que o restante das células permaneça normal */
.ag-row-selected .ag-cell:not(.ag-cell-range-selected):not(.ag-cell-range-selected-1):not(.ag-cell-range-selected-2):not(.ag-cell-range-selected-3):not(.ag-cell-range-selected-4) {
    background-color: inherit !important;
}

/* Estilo para os botões e controles */
.stButton > button, .stDownloadButton > button {
    background-color: #364b60 !important;
    color: white !important;
    border: none !important;
    border-radius: 3px !important;
    transition: all 0.3s ease;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    background-color: #25344d !important;
    transform: translateY(-1px);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

/* Títulos de seção */
h2 {
    color: #364b60;
    border-bottom: 1px solid #e37777;
    padding-bottom: 0.3rem;
    margin-top: 1.5rem;
}

/* Containers para KPIs e métricas */
.metric-container {
    background-color: white;
    border-radius: 5px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    text-align: center;
    transition: all 0.3s ease;
}

.metric-container:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.metric-value {
    font-size: 2rem;
    font-weight: bold;
    color: #364b60;
}

.metric-label {
    font-size: 0.9rem;
    color: #666;
    margin-top: 0.5rem;
}

/* Paginação centralizada */
.ag-paging-panel {
    display: flex !important;
    text-align: center !important;
    align-items: center !important;
    width: 100% !important;
    justify-content: center !important;
}

.ag-root-wrapper {
    margin: 0 auto;
}

/* Responsividade para telas menores */
@media screen and (max-width: 768px) {
    .metric-value {
        font-size: 1.5rem;
    }

    .metric-label {
        font-size: 0.8rem;
    }

    [data-testid="stSidebar"] {
        width: 100% !important;
        margin: 0 !important;
    }
}

/* Estilo KPIs */
.kpi-container {
    background-color: #f9f9f9;
    border-radius: 5px;
    padding: 15px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.kpi-title {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 5px;
}
.kpi-value {
    font-size: 1.8rem;
    font-weight: bold;
    color: #364b60;
}
.kpi-badge {
    background-color: #e6f2ff;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.8rem;
    color: #364b60;
}
"""

st.markdown(css_unificado, unsafe_allow_html=True)


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


@st.cache_data(ttl=3600)  # Cache por 1 hora
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

            # Adiciona formatação para o Excel
            workbook = writer.book
            worksheet = writer.sheets['Dados']

            # Formato para números
            formato_numero = workbook.add_format({'num_format': '#,##0'})
            formato_cabecalho = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#364b60',
                'font_color': 'white',
                'border': 1
            })

            # Aplica formato de cabeçalho
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, formato_cabecalho)

            # Aplica formato numérico para colunas que começam com "Número de"
            for i, col in enumerate(df.columns):
                if col.startswith("Número de"):
                    worksheet.set_column(i, i, 15, formato_numero)
                else:
                    worksheet.set_column(i, i, 15)

            # Ajusta a largura das colunas
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)

        return output.getvalue()
    except Exception as e:
        st.error(f"Erro ao converter para Excel: {str(e)}")
        output = io.BytesIO()
        output.write("Erro na conversão".encode('utf-8'))
        return output.getvalue()


def exibir_tabela_com_aggrid(df_para_exibir, altura=600, coluna_dados=None, posicao_totais="bottom",
                             tipo_visualizacao=None):
    """
    Exibe DataFrame no AgGrid, com opções de:
      - Paginação, seleção de intervalos, status bar custom (opcional)
      - Linha de totais fixada no topo ou rodapé (pinned row), se posicao_totais != None
      - Unifica o "Total de linhas" e a soma da coluna de matrículas na mesma pinned row
    """

    if df_para_exibir is None or df_para_exibir.empty:
        st.warning("Não há dados para exibir na tabela.")
        return {"data": pd.DataFrame()}

    # Exemplo de função JS que calcula soma/média/min/máx (usada na StatusBar se quiser manter):
    js_agg_functions = JsCode(f"""
    function(params) {{
        try {{
            const dataColumn = "{coluna_dados if coluna_dados else ''}";
            if (!dataColumn) return 'Coluna de dados não definida';

            let values = [];
            let totalSum = 0;
            let count = 0;

            params.api.forEachNodeAfterFilter(node => {{
                if (!node.data) return;
                const cellValue = node.data[dataColumn];
                if (cellValue !== null && cellValue !== undefined) {{
                    // Tentar converter p/ número
                    const numValue = parseFloat(
                      (""+cellValue)
                        .replaceAll('.', '')     // remove milhares
                        .replaceAll(',', '.')   // troca vírgula decimal por ponto
                    );
                    if (!isNaN(numValue)) {{
                        values.push(numValue);
                        totalSum += numValue;
                        count++;
                    }}
                }}
            }});

            if (values.length === 0) {{
                return 'Não há dados';
            }}

            const avg = totalSum / count;
            const min = Math.min(...values);
            const max = Math.max(...values);

            // Agora formatamos no padrão PT-BR
            const formatBR = num => new Intl.NumberFormat('pt-BR', {{ maximumFractionDigits: 2 }}).format(num);
            return 'Total: ' + formatBR(totalSum)
                 + ' | Média: ' + formatBR(avg)
                 + ' | Mín: ' + formatBR(min)
                 + ' | Máx: ' + formatBR(max);
        }} catch (error) {{
            console.error('Erro ao calcular estatísticas:', error);
            return 'Erro ao calcular estatísticas';
        }}
    }}
    """)

    # Constrói o GridOptions
    gb = GridOptionsBuilder.from_dataframe(df_para_exibir)

    # Texto de tradução/locale
    localeText = dict(
        contains="Contém",
        notContains="Não contém",
        equals="Igual a",
        notEqual="Diferente de",
        startsWith="Começa com",
        endsWith="Termina com",
        blank="Em branco",
        notBlank="Não em branco",
        thousandSeparator=".",
        decimalSeparator=",",
        applyFilter="Aplicar",
        resetFilter="Limpar",
        clearFilter="Limpar",
        cancelFilter="Cancelar",
        lessThan="Menor que",
        greaterThan="Maior que",
        lessThanOrEqual="Menor ou igual a",
        greaterThanOrEqual="Maior ou igual a",
        inRange="No intervalo",
        filterOoo="Filtrado",
        noRowsToShow="Sem dados para exibir",
        enabled="Habilitado",
        search="Buscar",
        selectAll="Selecionar todos",
        searchOoo="Buscar...",
        blanks="Em branco",
        noMatches="Sem correspondência",
        columns="Colunas",
        filters="Filtros",
        rowGroupColumns="Agrupar por",
        rowGroupColumnsEmptyMessage="Arraste colunas aqui para agrupar",
        valueColumns="Valores",
        pivotMode="Modo Pivot",
        groups="Grupos",
        values="Valores",
        pivots="Pivôs",
        valueColumnsEmptyMessage="Arraste aqui para agregar",
        pivotColumnsEmptyMessage="Arraste aqui para definir pivô",
        toolPanelButton="Painéis",
        loadingOoo="Carregando...",
        page="Página",
        PageSize="Tamanho da Página",
        next="Próximo",
        last="Último",
        first="Primeiro",
        previous="Anterior",
        of="de",
        to="até",
        rows="linhas",
        loading="Carregando...",
        totalRows="Total de linhas",
        totalAndFilteredRows="Linhas",
        selectedRows="Selecionadas",
        filteredRows="Filtradas",
        sum="Soma",
        min="Mínimo",
        max="Máximo",
        average="Média",
        count="Contagem"
    )

    # Configurações padrão de cada coluna
    gb.configure_default_column(
        groupable=True,
        editable=False,
        wrapText=True,
        autoHeight=False,
        filter="agTextColumnFilter",
        floatingFilter=True,
        filterParams={
            "filterOptions": ["contains", "equals", "startsWith", "endsWith"],
            "buttons": ["apply", "reset"],
            "closeOnApply": False
        },
        resizable=True,
        sortable=True,
        suppressMenu=False,
        headerWrapText=True,
        autoHeaderHeight=True
    )

    # Exemplo de ajustes manuais em colunas específicas (se houver)
    ajuste_colunas = {
        "ANO": 50,
        "CODIGO DO MUNICIPIO": 200,
        "NOME DO MUNICIPIO": 220,
        "CODIGO DA ESCOLA": 200,
        "NOME DA ESCOLA": 300,
        "DEPENDENCIA ADMINISTRATIVA": 200,
        "CODIGO DA UF": 200,
        "NOME DA UF": 200
    }
    largura_padrao_numericas = 50

    for col, largura in ajuste_colunas.items():
        if col in df_para_exibir.columns:
            gb.configure_column(
                col,
                minWidth=largura,
                maxWidth=800,
                suppressSizeToFit=False,
                wrapText=False,
                cellStyle={
                    'overflow': 'hidden',
                    'textAlign': 'left',
                    'text-overflow': 'ellipsis',
                    'white-space': 'nowrap',
                },
                headerClass="centered-header",
            )

    # Se detectar colunas que começam com "Número de", configurar como numéricas
    for coluna in df_para_exibir.columns:
        if coluna.startswith("Número de"):
            gb.configure_column(
                coluna,
                type=["numericColumn", "numberColumnFilter"],
                filter="agNumberColumnFilter",
                aggFunc="sum",
                minWidth=largura_padrao_numericas,
                maxWidth=300,
                # --- Formatação do Valor (Incluindo Pinned Row) ---
                valueFormatter=JsCode("""
                    function(params) {
                        // Se for pinned row, formata o valor mesmo que seja 0
                        if (params.node && params.node.rowPinned) {
                            return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(params.value);
                        }

                        // Para células normais
                        if (params.value == null || params.value === undefined) return '';
                        return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(params.value);
                    }
                """).js_code,
                # --- Estilo Condicional (Células Normais + Pinned Row) ---
                cellStyle=JsCode("""
                    function(params) {
                        const baseStyle = {
                            'text-align': 'center',
                            'font-weight': '500'
                        };

                        // Aplica estilo adicional se for pinned row
                        if (params.node && params.node.rowPinned) {
                            return {
                                ...baseStyle,
                                'font-weight': 'bold',
                                'background-color': '#F8DCDC'
                            };
                        }

                        return baseStyle;
                    }
                """).js_code
            )
        else:
            # Mantém como texto
            gb.configure_column(
                coluna,
                filter="agTextColumnFilter",
            )

        if "ANO" in df_para_exibir.columns:
            gb.configure_column(
                "ANO",
                cellStyle=JsCode("""
                    function(params) {
                        if (params.node && params.node.rowPinned) {
                            return { 'font-weight': 'bold', 'background-color': '#F8DCDC' };
                        }
                    }
                """),
                type=[],  # remove numericColumn
                filter="agTextColumnFilter",
                valueFormatter=None
            )

    # Configurações gerais do grid
    gb.configure_grid_options(
        defaultColDef={
            "headerClass": "centered-header",
            "suppressMovable": False,
            "headerComponentParams": {
                "template":
                    '<div class="ag-cell-label-container" role="presentation">'
                    '  <span ref="eMenu" class="ag-header-icon ag-header-cell-menu-button"></span>'
                    '  <div ref="eLabel" class="ag-header-cell-label" role="presentation" style="display: flex; justify-content: center; text-align: center;">'
                    '    <span ref="eText" class="ag-header-cell-text" role="columnheader" style="text-align: center;"></span>'
                    '    <span ref="eFilter" class="ag-header-icon ag-header-label-icon ag-filter-icon"></span>'
                    '    <span ref="eSortOrder" class="ag-header-icon ag-header-label-icon ag-sort-order"></span>'
                    '    <span ref="eSortAsc" class="ag-header-icon ag-header-label-icon ag-sort-ascending-icon"></span>'
                    '    <span ref="eSortDesc" class="ag-header-icon ag-header-label-icon ag-sort-descending-icon"></span>'
                    '    <span ref="eSortNone" class="ag-header-icon ag-header-label-icon ag-sort-none-icon"></span>'
                    '  </div>'
                    '</div>'
            }
        },
        rowStyle={"textAlign": "center"},
        enableCellTextSelection=True,
        clipboardDelimiter='\t',
        ensureDomOrder=True,
        pagination=True,
        paginationAutoPageSize=False,
        paginationPageSize=25,
        paginationSizeSelector=[5, 10, 25, 50, 100],
        localeText=localeText,
        suppressAggFuncInHeader=True,

        # Configurações para corrigir a seleção de células
        enableRangeSelection=True,          # Habilita seleção de intervalo
        enableRangeHandle=True,             # Habilita alça para arrastar seleção
        suppressRowClickSelection=True,     # Suprime seleção de linha ao clicar
        rowSelection="none",                # Desativa seleção de linha
        rowMultiSelectWithClick=False,      # Desativa multi-seleção de linhas
        cellSelection="multiple",           # Permite selecionar múltiplas células

        # Exemplo de manter somente o 'agCustomStatsToolPanel' no status bar (removendo totalRows e filteredRows):
        statusBar={
            'statusPanels': [
                {
                    'statusPanel': 'agCustomStatsToolPanel',
                    'statusPanelParams': {
                        'aggStatFunc': js_agg_functions.js_code
                    }
                }
            ]
        },
        onGridReady=JsCode("""
            function(params) {
                setTimeout(() => {
                    try {
                        const gridElement = document.querySelector('.ag-root-wrapper');
                        const paginationElement = document.querySelector('.ag-paging-panel');
                        if (gridElement && paginationElement) {
                            paginationElement.style.width = gridElement.clientWidth + 'px';
                        }
                        params.api.sizeColumnsToFit();
                    } catch(e) {
                        console.error('Erro no onGridReady:', e);
                    }
                }, 300);
            }
        """),
        onColumnResized=JsCode("""
            function(params) {
                const gridElement = document.querySelector('.ag-root-wrapper');
                const paginationElement = document.querySelector('.ag-paging-panel');
                if (gridElement && paginationElement) {
                    paginationElement.style.width = gridElement.clientWidth + 'px';
                }
            }
        """),
        onColumnVisibilityChanged=JsCode("""
            function(params) {
                setTimeout(() => {
                    params.api.sizeColumnsToFit();
                    const gridElement = document.querySelector('.ag-root-wrapper');
                    const paginationElement = document.querySelector('.ag-paging-panel');
                    if (gridElement && paginationElement) {
                        paginationElement.style.width = gridElement.clientWidth + 'px';
                    }
                }, 100);
            }
        """),
        onFilterChanged=JsCode("""
            function(params) {
                setTimeout(() => {
                    const gridElement = document.querySelector('.ag-root-wrapper');
                    const paginationElement = document.querySelector('.ag-paging-panel');
                    if (gridElement && paginationElement) {
                        paginationElement.style.width = gridElement.clientWidth + 'px';
                    }
                }, 100);
            }
        """)
    )

    # Barra lateral interna do AG Grid
    gb.configure_side_bar()

    # Ajustes de desempenho para grandes datasets (opcional)
    if len(df_para_exibir) > 5000:
        gb.configure_grid_options(
            rowBuffer=100,
            animateRows=False,
            suppressColumnVirtualisation=False,
            suppressRowVirtualisation=False,
            enableCellTextSelection=True,
            enableBrowserTooltips=True,
            defaultColDef={"headerClass": "centered-header"},
            rowStyle={"textAlign": "center"}
        )

    # --------------------------------------------------------------------------------
    # Pinned Row unificando "Total de linhas" (na primeira coluna) e soma de 'coluna_dados'
    # --------------------------------------------------------------------------------
    # 1) soma_valor como int
    soma_valor = int(df_para_exibir[coluna_dados].sum()) if coluna_dados in df_para_exibir.columns else 0
    total_linhas = int(len(df_para_exibir))

    # 2) pinned row: texto na coluna "ANO", número puro na coluna de matrículas
    pinned_row_data = {
        "ANO": f"Total de linhas: {total_linhas:,}".replace(",", "."),
    }

    # Adicionar o valor do coluna_dados se existir
    if coluna_dados in df_para_exibir.columns:
        pinned_row_data[coluna_dados] = soma_valor

    grid_options = gb.build()

    if posicao_totais == "bottom":
        grid_options["pinnedBottomRowData"] = [pinned_row_data]
    elif posicao_totais == "top":
        grid_options["pinnedTopRowData"] = [pinned_row_data]

    # --------------------------------------------------------------------------------
    # Renderização do grid
    # --------------------------------------------------------------------------------
    grid_return = AgGrid(
        df_para_exibir,
        gridOptions=grid_options,
        height=altura,
        custom_css="""
            /* Estilo para todas as pinned rows */
            .ag-row-pinned {
                font-weight: bold !important;
                background-color: #f2f2f2 !important;
            }
            
            /* Alinhamento do texto na pinned row */
            .ag-row-pinned .ag-cell {
                text-align: center !important;
            }
            
            /* Alinhamento especial para a coluna de mensagem (se necessário) */
            .ag-row-pinned .ag-cell[col-id='NOME DA ESCOLA'] {
                text-align: left !important;
            } 
            /* Centralização de cabeçalhos */
            .ag-header-cell {
                display: flex !important;
                width: 100% !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
            }
            .ag-header-cell-label {
                display: flex !important;
                width: 100% !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
            }
            .ag-header-cell-text {
                display: flex !important;
                text-align: center !important;
                align-items: center !important;
                width: 100% !important;
                justify-content: center !important;
                font-weight: bold !important;
                white-space: normal !important;
                line-height: 1.2 !important;
                overflow: visible !important;
                font-size: 12px !important;
            }
            .centered-header .ag-header-cell-label {
                justify-content: center !important;
                text-align: center !important;
            }

            /* Paginação centralizada */
            .ag-paging-panel {
                display: flex !important;
                text-align: center !important;
                align-items: center !important;
                width: 100% !important;
                justify-content: center !important;
            }
            .ag-root-wrapper {
                margin: 0 auto;
            }

            /* Seleção e hover */
            .ag-row-selected { 
                background-color: transparent !important; 
            }
            .ag-row {
                background-color: inherit !important;
            }
            .ag-row:hover {
                background-color: rgba(54, 75, 96, 0.1) !important;
            }
            .ag-row-selected,
            .ag-row-selected:hover {
                background-color: transparent !important;
                border: none !important;
            }

            /* Células selecionadas (range selection) */
            .ag-cell.ag-cell-range-selected,
            .ag-cell.ag-cell-range-selected-1,
            .ag-cell.ag-cell-range-selected-2,
            .ag-cell.ag-cell-range-selected-3,
            .ag-cell.ag-cell-range-selected-4 {
                background-color: #e6f2ff !important; 
                color: #000 !important; 
            }

            /* Remover seleção de linha completa */
            .ag-row-selected .ag-cell:not(.ag-cell-range-selected):not(.ag-cell-range-selected-1):not(.ag-cell-range-selected-2):not(.ag-cell-range-selected-3):not(.ag-cell-range-selected-4) {
                background-color: inherit !important;
            }

            /* Células numéricas */
            .numeric-cell { 
                display: flex !important;
                text-align: center !important;
                width: 100% !important;
                justify-content: center !important;
            }
        """,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        theme="balham",
        key=f"aggrid_{tipo_visualizacao}_{id(df_para_exibir)}"
    )

    # Ajuste final via JS para centralizar cabeçalhos (backup)
    js_simplified_fix = """
    <script>
        function centralizeHeaders() {
            try {
                if (!document.getElementById('aggrid-header-fix')) {
                    const styleEl = document.createElement('style');
                    styleEl.id = 'aggrid-header-fix';
                    styleEl.innerHTML = `
                        .ag-header-cell-text {
                            width: 100% !important;
                            text-align: center !important;
                            justify-content: center !important;
                        }
                        .ag-header-cell-label {
                            justify-content: center !important;
                            width: 100% !important;
                        }
                    `;
                    document.head.appendChild(styleEl);
                }
            } catch(e) {
                console.error('Erro na centralização:', e);
            }
        }

        for (let i = 1; i <= 5; i++) {
            setTimeout(centralizeHeaders, i * 500);
        }
    </script>
    """
    st.markdown(js_simplified_fix, unsafe_allow_html=True)

    # Exibe info de quantos registros foram filtrados, se quiser
    filtered_data = grid_return['data']
    if len(filtered_data) != len(df_para_exibir):
        st.info(
            f"Filtro aplicado: mostrando {len(filtered_data):,} "
            f"de {len(df_para_exibir):,} registros."
        )

    return grid_return

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

    # Adiciona botões para facilitar a seleção
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Último Ano", key="btn_ultimo_ano"):
            anos_selecionados = [anos_disponiveis[0]]
    with col2:
        if st.button("Todos Anos", key="btn_todos_anos"):
            anos_selecionados = anos_disponiveis

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

    # Exibe um contador com o total de opções disponíveis
    st.sidebar.caption(f"Total de {len(dependencias_disponiveis)} dependências disponíveis")

    # Adiciona botões para facilitar a seleção
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Selecionar Todas", key="btn_todas_dep"):
            dependencia_selecionada = dependencias_disponiveis
    with col2:
        if st.button("Limpar Seleção", key="btn_limpar_dep"):
            dependencia_selecionada = []

    # Usa o componente pills para seleção
    dependencia_selecionada = st.sidebar.pills(
        "DEPENDENCIA ADMINISTRATIVA:",
        options=dependencias_disponiveis,
        default=dependencias_disponiveis,
        selection_mode="multi",
        label_visibility="visible"
    )

    # Feedback visual sobre a seleção
    if dependencia_selecionada:
        st.sidebar.success(f"{len(dependencia_selecionada)} dependência(s) selecionada(s)")
        df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"].isin(dependencia_selecionada)]
    else:
        st.sidebar.warning("Nenhuma dependência selecionada. Selecione pelo menos uma.")
        df_filtrado = df_filtrado[0:0]  # DataFrame vazio
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

# ------------------------------
# Configurações da tabela (movidas para sidebar)
# ------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### Configurações da tabela")

altura_personalizada = st.sidebar.checkbox(ROTULO_AJUSTAR_ALTURA, value=False, help=DICA_ALTURA_TABELA)
if altura_personalizada:
    altura_manual = st.sidebar.slider("Altura da tabela (pixels)", 200, 1000, 600, 50)
else:
    altura_manual = 600

posicao_totais = st.sidebar.radio(
    "Linha de totais:",
    ["Rodapé", "Topo", "Nenhum"],
    index=0,
    horizontal=True
)

modo_desempenho = st.sidebar.checkbox(ROTULO_MODO_DESEMPENHO, value=True, help=DICA_MODO_DESEMPENHO)

# Incluir outras colunas
st.sidebar.markdown("### Colunas adicionais")
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

todas_colunas = [col for col in df_filtrado.columns if col not in colunas_tabela]
if todas_colunas:
    colunas_adicionais_selecionadas = st.sidebar.multiselect(
        "Selecionar colunas adicionais:",
        todas_colunas,
        placeholder="Selecionar colunas adicionais..."
    )
    if colunas_adicionais_selecionadas:
        colunas_tabela.extend(colunas_adicionais_selecionadas)

# Botões de download
st.sidebar.markdown("### Download dos dados")
col1, col2 = st.sidebar.columns(2)

# Preparar dados para tabela
colunas_existentes = [c for c in colunas_tabela if c in df_filtrado.columns]

if coluna_dados in df_filtrado.columns:
    with pd.option_context('mode.chained_assignment', None):
        df_filtrado_tabela = df_filtrado[colunas_existentes].copy()
        df_filtrado_tabela[coluna_dados] = pd.to_numeric(df_filtrado_tabela[coluna_dados], errors='coerce')

    tabela_dados = df_filtrado_tabela.sort_values(by=coluna_dados, ascending=False)
    tabela_exibicao = tabela_dados.copy()
else:
    tabela_dados = df_filtrado[colunas_existentes].copy()
    tabela_exibicao = tabela_dados.copy()

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

# -------------------------------
# Cabeçalho e Informações Iniciais
# -------------------------------
st.title(TITULO_DASHBOARD)

# Cabeçalho com estilo personalizado
st.markdown(
    f"""
    <div class="main-header">
        <h3>Visualização por {tipo_visualizacao} - Anos: {', '.join(map(str, anos_selecionados))}</h3>
        <p>{etapa_selecionada} {f'| {subetapa_selecionada}' if subetapa_selecionada != 'Todas' else ''} {f'| {serie_selecionada}' if serie_selecionada != 'Todas' and serie_selecionada in series_disponiveis else ''}</p>
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# Seção de Indicadores (KPIs)
# -------------------------------
st.markdown("## Indicadores")

# Cria um container com borda e fundo para os KPIs
kpi_container = st.container()
with kpi_container:
    col1, col2, col3 = st.columns(3)

    try:
        total_matriculas = df_filtrado[coluna_dados].sum()
        with col1:
            st.markdown(f'<div class="kpi-container"><p class="kpi-title">{ROTULO_TOTAL_MATRICULAS}</p><p class="kpi-value">{formatar_numero(total_matriculas)}</p><span class="kpi-badge">Total</span></div>', unsafe_allow_html=True)
    except Exception as e:
        with col1:
            st.markdown(f'<div class="kpi-container"><p class="kpi-title">Total de Matrículas</p><p class="kpi-value">-</p><span class="kpi-badge">Erro</span></div>', unsafe_allow_html=True)
            st.caption(f"Erro ao calcular: {str(e)}")

    with col2:
        try:
            if tipo_visualizacao == "Escola":
                if len(df_filtrado) > 0:
                    media_por_escola = df_filtrado[coluna_dados].mean()
                    st.markdown(f'<div class="kpi-container"><p class="kpi-title">{ROTULO_MEDIA_POR_ESCOLA}</p><p class="kpi-value">{formatar_numero(media_por_escola)}</p><span class="kpi-badge">Média</span></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="kpi-container"><p class="kpi-title">Média de Matrículas por Escola</p><p class="kpi-value">-</p><span class="kpi-badge">Sem dados</span></div>', unsafe_allow_html=True)
            else:
                if "DEPENDENCIA ADMINISTRATIVA" in df_filtrado.columns:
                    media_por_dependencia = df_filtrado.groupby("DEPENDENCIA ADMINISTRATIVA")[coluna_dados].mean()
                    if not media_por_dependencia.empty:
                        media_geral = media_por_dependencia.mean()
                        st.markdown(f'<div class="kpi-container"><p class="kpi-title">{ROTULO_MEDIA_MATRICULAS}</p><p class="kpi-value">{formatar_numero(media_geral)}</p><span class="kpi-badge">Média</span></div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="kpi-container"><p class="kpi-title">Média de Matrículas</p><p class="kpi-value">-</p><span class="kpi-badge">Sem dados</span></div>', unsafe_allow_html=True)
                else:
                    media_geral = df_filtrado[coluna_dados].mean()
                    st.markdown(f'<div class="kpi-container"><p class="kpi-title">Média de Matrículas</p><p class="kpi-value">{formatar_numero(media_geral)}</p><span class="kpi-badge">Média</span></div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown('<div class="kpi-container"><p class="kpi-title">Média de Matrículas</p><p class="kpi-value">-</p><span class="kpi-badge">Erro</span></div>', unsafe_allow_html=True)
            st.caption(f"Erro ao calcular: {str(e)}")

    with col3:
        try:
            if tipo_visualizacao == "Escola":
                total_escolas = len(df_filtrado)
                st.markdown(
                    f'<div class="kpi-container"><p class="kpi-title">{ROTULO_TOTAL_ESCOLAS}</p>'
                    f'<p class="kpi-value">{formatar_numero(total_escolas)}</p>'
                    f'<span class="kpi-badge">Contagem</span></div>',
                    unsafe_allow_html=True
                )
            elif tipo_visualizacao == "Município":
                total_municipios = len(df_filtrado)
                st.markdown(
                    f'<div class="kpi-container"><p class="kpi-title">{ROTULO_TOTAL_MUNICIPIOS}</p>'
                    f'<p class="kpi-value">{formatar_numero(total_municipios)}</p>'
                    f'<span class="kpi-badge">Contagem</span></div>',
                    unsafe_allow_html=True
                )
            else:  # Estado
                max_valor = df_filtrado[coluna_dados].max()
                st.markdown(
                    f'<div class="kpi-container"><p class="kpi-title">{ROTULO_MAXIMO_MATRICULAS}</p>'
                    f'<p class="kpi-value">{formatar_numero(max_valor)}</p>'
                    f'<span class="kpi-badge">Máximo</span></div>',
                    unsafe_allow_html=True
                )
        except Exception as e:
            if tipo_visualizacao == "Escola":
                st.markdown(
                    '<div class="kpi-container"><p class="kpi-title">Total de Escolas</p>'
                    '<p class="kpi-value">-</p>'
                    '<span class="kpi-badge">Erro</span></div>',
                    unsafe_allow_html=True
                )
            elif tipo_visualizacao == "Município":
                st.markdown(
                    '<div class="kpi-container"><p class="kpi-title">Total de Municípios</p>'
                    '<p class="kpi-value">-</p>'
                    '<span class="kpi-badge">Erro</span></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="kpi-container"><p class="kpi-title">Máximo de Matrículas</p>'
                    '<p class="kpi-value">-</p>'
                    '<span class="kpi-badge">Erro</span></div>',
                    unsafe_allow_html=True
                )
            st.caption(f"Erro ao calcular: {str(e)}")

# -------------------------------
# Seção de Tabela de Dados Detalhados
# -------------------------------
st.markdown(f"## {TITULO_DADOS_DETALHADOS}")

# Definição do mapeamento para posição dos totais
posicao_totais_map = {
    "Rodapé": "bottom",
    "Topo": "top",
    "Nenhum": None
}

# Verifica se há dados antes de exibir a tabela
if tabela_exibicao.empty:
    st.warning("Não há dados para exibir com os filtros selecionados.")
else:
    try:
        # Correção do erro para Município e Estado
        # Verificar se há null values em qualquer coluna do DataFrame
        for col in tabela_exibicao.columns:
            if tabela_exibicao[col].isnull().any():
                # Preencher valores nulos com string vazia para evitar o erro
                tabela_exibicao[col] = tabela_exibicao[col].fillna('')

        # Exibe a tabela usando a função corrigida
        grid_result = exibir_tabela_com_aggrid(
            tabela_exibicao,
            altura=altura_manual,
            coluna_dados=coluna_dados,
            posicao_totais=posicao_totais_map.get(posicao_totais),
            tipo_visualizacao=tipo_visualizacao
        )
    except Exception as e:
        st.error(f"Erro ao exibir tabela no AgGrid: {str(e)}")
        # Fallback para o dataframe nativo do Streamlit
        st.dataframe(tabela_exibicao, height=altura_manual)

# -------------------------------
# Rodapé do Dashboard
# -------------------------------
st.markdown("---")
st.markdown(RODAPE_NOTA)

# Adiciona informações sobre o tempo de execução
tempo_final = time.time()
tempo_total = round(tempo_final - st.session_state.get('tempo_inicio', tempo_final), 2)
st.session_state['tempo_inicio'] = tempo_final
st.caption(f"Tempo de processamento: {tempo_total} segundos")
