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

# Biblioteca do AgGrid
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

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
        border-radius: 1px !important;  /* Adicionando esta linha */
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


@st.cache_data
def carregar_dados():
    """
    Carrega os dados das planilhas no formato Parquet.
    - Lê os arquivos: escolas.parquet, estado.parquet e municipio.parquet.
    - Converte colunas que começam com 'Número de' para tipo numérico.
    Em caso de erro, exibe uma mensagem e interrompe a execução.
    """
    try:
        # Definir possíveis localizações dos arquivos
        diretorios_possiveis = [".", "data", "dados", os.path.join(os.path.dirname(__file__), "data")]

        # Tentar encontrar os arquivos em diferentes localizações
        escolas_df = None
        estado_df = None
        municipio_df = None

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

        # Converter colunas numéricas para o tipo correto
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
        # Definir possíveis localizações do arquivo
        diretorios_possiveis = [".", "data", "dados", os.path.join(os.path.dirname(__file__), "data")]

        for diretorio in diretorios_possiveis:
            json_path = os.path.join(diretorio, "mapeamento_colunas.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)

        # Se não encontrou o arquivo em nenhum local
        raise FileNotFoundError("Arquivo mapeamento_colunas.json não encontrado")

    except Exception as e:
        st.error(f"Erro ao carregar o mapeamento de colunas: {e}")
        st.stop()  # Para a execução se não conseguir carregar o arquivo


def criar_mapeamento_colunas(df):
    """
    Cria um dicionário que mapeia as etapas de ensino para os nomes das colunas.
    Esse mapeamento inclui a coluna principal, subetapas e séries, facilitando a seleção
    dos dados conforme os filtros do usuário.
    """
    # Criar mapeamento de colunas (case-insensitive) apenas uma vez
    colunas_map = {col.lower().strip(): col for col in df.columns}

    def obter_coluna_real(nome_padrao):
        # Verifica se a coluna existe exatamente como foi especificada
        if nome_padrao in df.columns:
            return nome_padrao

        # Verifica se existe uma versão case-insensitive da coluna
        nome_normalizado = nome_padrao.lower().strip()
        if nome_normalizado in colunas_map:
            return colunas_map[nome_normalizado]

        # Se não encontrar, retorna o nome original
        return nome_padrao

    # Carrega o mapeamento do arquivo JSON (se falhar, st.stop() será chamado)
    mapeamento_base = carregar_mapeamento_colunas()

    # Ajusta os nomes das colunas
    mapeamento_ajustado = {}

    # Para cada etapa no mapeamento base
    for etapa, config in mapeamento_base.items():
        mapeamento_ajustado[etapa] = {
            "coluna_principal": obter_coluna_real(config.get("coluna_principal", "")),
            "subetapas": {},
            "series": {}
        }

        # Ajusta subetapas
        for subetapa, coluna in config.get("subetapas", {}).items():
            mapeamento_ajustado[etapa]["subetapas"][subetapa] = obter_coluna_real(coluna)

        # Ajusta séries
        for sub, series_dict in config.get("series", {}).items():
            if sub not in mapeamento_ajustado[etapa]["series"]:
                mapeamento_ajustado[etapa]["series"][sub] = {}
            for serie, col_serie in series_dict.items():
                mapeamento_ajustado[etapa]["series"][sub][serie] = obter_coluna_real(col_serie)

    return mapeamento_ajustado


def obter_coluna_dados(etapa, subetapa, serie, mapeamento):
    """
    Determina a coluna de dados com base na etapa, subetapa e série selecionadas.
    """
    if etapa not in mapeamento:
        st.error(ERRO_ETAPA_NAO_ENCONTRADA.format(etapa))
        return ""

    # Caso 1: Nenhuma subetapa selecionada, usa coluna principal da etapa
    if subetapa == "Todas":
        return mapeamento[etapa].get("coluna_principal", "")

    # Verificar se a subetapa existe
    if "subetapas" not in mapeamento[etapa] or subetapa not in mapeamento[etapa]["subetapas"]:
        st.warning(ERRO_SUBETAPA_NAO_ENCONTRADA.format(subetapa, etapa))
        return mapeamento[etapa].get("coluna_principal", "")

    # Caso 2: Nenhuma série específica selecionada, usa coluna da subetapa
    if serie == "Todas":
        return mapeamento[etapa]["subetapas"][subetapa]

    # Verificar se a subetapa tem séries e se a série selecionada existe
    series_subetapa = mapeamento[etapa].get("series", {}).get(subetapa, {})
    if not series_subetapa or serie not in series_subetapa:
        st.warning(ERRO_SERIE_NAO_ENCONTRADA.format(serie, subetapa))
        return mapeamento[etapa]["subetapas"][subetapa]

    # Caso 3: Série específica selecionada
    return series_subetapa[serie]


def verificar_coluna_existe(df, coluna_nome):
    """
    Verifica se uma coluna existe no DataFrame (exato ou case-insensitive).
    Retorna (coluna_existe, coluna_real).
    """
    if not coluna_nome:
        return False, ""

    if coluna_nome in df.columns:
        return True, coluna_nome

    coluna_normalizada = coluna_nome.lower().strip()
    colunas_normalizadas = {col.lower().strip(): col for col in df.columns}
    if coluna_normalizada in colunas_normalizadas:
        return True, colunas_normalizadas[coluna_normalizada]

    return False, coluna_nome


def preparar_tabela_para_exibicao(df_base, colunas_para_exibir, coluna_ordenacao):
    """
    Ordena df_base pela coluna_ordenacao e formata colunas numéricas.
    Retorna (tabela_dados, tabela_exibicao).
    """
    colunas_existentes = [c for c in colunas_para_exibir if c in df_base.columns]
    tabela_dados = df_base[colunas_existentes]

    if coluna_ordenacao in tabela_dados.columns:
        tabela_dados = tabela_dados.sort_values(by=coluna_ordenacao, ascending=False)

    tabela_exibicao = tabela_dados.copy()

    with pd.option_context('mode.chained_assignment', None):
        if coluna_ordenacao in tabela_exibicao.columns:
            tabela_exibicao[coluna_ordenacao] = tabela_exibicao[coluna_ordenacao].apply(
                lambda x: formatar_numero(x) if pd.notnull(x) else "-"
            )
        if '% do Total' in tabela_exibicao.columns:
            tabela_exibicao['% do Total'] = tabela_exibicao['% do Total'].apply(
                lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
            )

    return tabela_dados, tabela_exibicao


def converter_df_para_csv(df):
    """
    Converte DataFrame para CSV, retorna bytes.
    """
    if df is None or df.empty:
        return "Não há dados para exportar.".encode('utf-8')
    try:
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        st.error(f"Erro ao converter para CSV: {str(e)}")
        return "Erro na conversão".encode('utf-8')


def converter_df_para_excel(df):
    """
    Converte DataFrame para Excel, retorna bytes.
    """
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


def exibir_tabela_com_aggrid(df_para_exibir, altura=600, coluna_dados=None, posicao_totais="bottom"):
    """
    Exibe DataFrame no AgGrid com paginação, barra de status e seleções de célula.
    Também configura opcionalmente uma linha de totais fixada no topo ou rodapé,
    de acordo com o parâmetro posicao_totais (“top”, “bottom” ou None).
    """
    if df_para_exibir is None or df_para_exibir.empty:
        st.warning("Não há dados para exibir na tabela.")
        return {"data": pd.DataFrame()}

    is_large_dataset = len(df_para_exibir) > 5000
    is_very_large_dataset = len(df_para_exibir) > 10000

    if is_very_large_dataset:
        st.warning(
            f"O conjunto de dados tem {formatar_numero(len(df_para_exibir))} linhas, "
            "o que pode causar lentidão na visualização."
        )
        mostrar_tudo = st.checkbox("Carregar todos os dados (pode ser lento)", value=False)
        if not mostrar_tudo:
            tem_total = False
            total_rows = []

            for col in df_para_exibir.columns:
                mask = df_para_exibir[col].astype(str).str.contains('TOTAL', case=False, na=False)
                if mask.any():
                    total_indices = df_para_exibir.index[mask]
                    total_rows.extend(total_indices.tolist())
                    tem_total = True

            if isinstance(df_para_exibir.index, pd.Index):
                mask = df_para_exibir.index.astype(str).str.contains('TOTAL', case=False, na=False)
                if mask.any():
                    total_indices = df_para_exibir.index[mask]
                    total_rows.extend(total_indices.tolist())
                    tem_total = True

            indices_para_manter = df_para_exibir.index[:5000].tolist()
            if tem_total:
                total_rows = list(dict.fromkeys(total_rows))
                indices_para_manter.extend(total_rows)
            df_para_exibir = df_para_exibir.loc[indices_para_manter]
            st.info("Mostrando amostra de 5.000 registros (de um total maior)")

    js_agg_functions = JsCode(f"""
    function(params) {{
        try {{
            const dataColumn = "{coluna_dados if coluna_dados else ''}";
            if (!dataColumn) return 'Coluna de dados não definida';

            const values = [];
            let totalSum = 0;
            let count = 0;

            params.api.forEachNodeAfterFilter(node => {{
                if (!node.data) return;

                let isTotal = false;
                for (const key in node.data) {{
                    if (node.data[key] && 
                        node.data[key].toString().toUpperCase().includes('TOTAL')) {{
                        isTotal = true;
                        break;
                    }}
                }}
                if (isTotal) return;

                const cellValue = node.data[dataColumn];
                if (cellValue !== null && cellValue !== undefined) {{
                    const numValue = Number(cellValue.toString().replace(/[^0-9.,]/g, '').replace(',', '.'));
                    if (!isNaN(numValue)) {{
                        values.push(numValue);
                        totalSum += numValue;
                        count++;
                    }}
                }}
            }});
            const formatNum = function(num) {{
                let formatted = new Intl.NumberFormat('pt-BR', {{ maximumFractionDigits: 2 }}).format(num);
                formatted = formatted.replace(/\\./g, '_');
                formatted = formatted.replace(/,/g, '.');
                formatted = formatted.replace(/_/g, '.');
                return formatted;
            }};
            if (values.length === 0) {{
                return 'Não há dados numéricos';
            }}
            const avg = totalSum / count;
            values.sort((a, b) => a - b);
            const min = values[0];
            const max = values[values.length - 1];
            return `Total: ${{formatNum(totalSum)}} | Média: ${{formatNum(avg)}} | Mín: ${{formatNum(min)}} | Máx: ${{formatNum(max)}}`;
        }} catch (error) {{
            console.error('Erro ao calcular estatísticas:', error);
            return 'Erro ao calcular estatísticas';
        }}
    }}
    """)

    gb = GridOptionsBuilder.from_dataframe(df_para_exibir)

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

    # Configuração otimizada para colunas específicas
    if "ANO" in df_para_exibir.columns:
        gb.configure_column(
            "ANO",
            width=80,
            maxWidth=80,
            suppressSizeToFit=True,
            wrapText=False,
            cellStyle={'overflow': 'hidden', 'text-overflow': 'ellipsis', 'white-space': 'nowrap'},
            headerWrapText=True
        )

    if "CODIGO DO MUNICIPIO" in df_para_exibir.columns:
        gb.configure_column(
            "CODIGO DO MUNICIPIO",
            width=160,
            maxWidth=160,
            suppressSizeToFit=True,
            wrapText=False,
            cellStyle={'overflow': 'hidden', 'text-overflow': 'ellipsis', 'white-space': 'nowrap'},
            headerWrapText=True
        )

    if "NOME DO MUNICIPIO" in df_para_exibir.columns:
        gb.configure_column(
            "NOME DO MUNICIPIO",
            width=220,
            maxWidth=220,
            suppressSizeToFit=True,
            wrapText=False,
            cellStyle={'overflow': 'hidden', 'text-overflow': 'ellipsis', 'white-space': 'nowrap'},
            headerWrapText=True
        )

    if "CODIGO DA ESCOLA" in df_para_exibir.columns:
        gb.configure_column(
            "CODIGO DA ESCOLA",
            width=140,
            maxWidth=140,
            suppressSizeToFit=True,
            wrapText=False,
            cellStyle={'overflow': 'hidden', 'text-overflow': 'ellipsis', 'white-space': 'nowrap'},
            headerWrapText=True
        )

    if "NOME DA ESCOLA" in df_para_exibir.columns:
        gb.configure_column(
            "NOME DA ESCOLA",
            width=150,
            maxWidth=150,
            suppressSizeToFit=True,
            wrapText=False,
            cellStyle={'overflow': 'hidden', 'text-overflow': 'ellipsis', 'white-space': 'nowrap'},
            headerWrapText=True
        )

    if "DEPENDENCIA ADMINISTRATIVA" in df_para_exibir.columns:
        gb.configure_column(
            "DEPENDENCIA ADMINISTRATIVA",
            width=180,
            maxWidth=180,
            suppressSizeToFit=True,
            wrapText=False,
            cellStyle={'overflow': 'hidden', 'text-overflow': 'ellipsis', 'white-space': 'nowrap'},
            headerWrapText=True
        )

    if "CODIGO DA UF" in df_para_exibir.columns:
        gb.configure_column(
            "CODIGO DA UF",
            width=100,
            maxWidth=100,
            suppressSizeToFit=True,
            wrapText=False,
            cellStyle={'overflow': 'hidden', 'text-overflow': 'ellipsis', 'white-space': 'nowrap'},
            headerWrapText=True
        )

    if "NOME DA UF" in df_para_exibir.columns:
        gb.configure_column(
            "NOME DA UF",
            width=120,
            maxWidth=120,
            suppressSizeToFit=True,
            wrapText=False,
            cellStyle={'overflow': 'hidden', 'text-overflow': 'ellipsis', 'white-space': 'nowrap'},
            headerWrapText=True
        )

    # Determinar qual coluna de nome deve mostrar "TOTAL"
    coluna_nome_principal = None
    if "NOME DA ESCOLA" in df_para_exibir.columns:
        coluna_nome_principal = "NOME DA ESCOLA"
    elif "NOME DO MUNICIPIO" in df_para_exibir.columns:
        coluna_nome_principal = "NOME DO MUNICIPIO"
    elif "NOME DA UF" in df_para_exibir.columns:
        coluna_nome_principal = "NOME DA UF"

    # Configurar colunas para controle da linha de totais
    colunas_sem_totais = [
        "ANO",
        "CODIGO DA ESCOLA",
        "NOME DA ESCOLA",
        "CODIGO DO MUNICIPIO",
        "NOME DO MUNICIPIO",
        "CODIGO DA UF",
        "NOME DA UF"
    ]

    for coluna in df_para_exibir.columns:
        if coluna in colunas_sem_totais:
            if coluna == coluna_nome_principal:
                gb.configure_column(
                    coluna,
                    aggFunc=None,
                    cellRenderer=JsCode("""
                    function(params) {
                        if (params.node && params.node.rowPinned) {
                            return '<b>TOTAL</b>';
                        }
                        return params.value;
                    }
                    """).js_code
                )
            else:
                gb.configure_column(coluna, aggFunc=None)
        elif coluna == "DEPENDENCIA ADMINISTRATIVA":
            gb.configure_column(
                coluna,
                aggFunc=None,
                cellRenderer=JsCode("""
                function(params) {
                    if (params.node && params.node.rowPinned) {
                        return '<b>TODAS</b>';
                    }
                    return params.value;
                }
                """).js_code
            )
        elif coluna == coluna_dados or coluna.startswith("Número de"):
            # Apenas somar a coluna de matrículas e colunas que começam com "Número de"
            gb.configure_column(
                coluna,
                type=["numericColumn", "numberColumnFilter"],
                filter="agNumberColumnFilter",
                aggFunc="sum",
                valueFormatter=JsCode("""
                function(params) {
                    if (params.value == null) return '';
                    return new Intl.NumberFormat('pt-BR').format(params.value);
                }
                """).js_code
            )
        elif df_para_exibir[coluna].dtype.kind in 'ifc':
            gb.configure_column(
                coluna,
                type=["numericColumn", "numberColumnFilter"],
                filter="agNumberColumnFilter",
                aggFunc="sum",
                valueFormatter=JsCode("""
                function(params) {
                    if (params.value == null) return '';
                    return new Intl.NumberFormat('pt-BR').format(params.value);
                }
                """).js_code
            )

    js_estilo_linha_totais = JsCode("""
    function(params) {
        // Verifique se é uma linha pinnada (total)
        if (params.node && params.node.rowPinned) {
            return {
                'background-color': '#f0f2f7',
                'font-weight': 'bold',
                'border-top': '2px solid #ccc'
            };
        }
        return null;
    }
    """)

    # Configurar seleção de células, clipboard e paginação
    gb.configure_grid_options(
        rowSelection='none',
        suppressRowDeselection=True,
        suppressRowClickSelection=True,
        enableRangeSelection=True,
        enableRangeHandle=True,
        clipboardDelimiter='\t',
        suppressCopyRowsToClipboard=True,
        copyHeadersToClipboard=True,
        ensureDomOrder=True,

        pagination=True,
        paginationAutoPageSize=False,
        paginationPageSize=25,
        paginationSizeSelector=[5, 10, 25, 50, 100],
        localeText=localeText,
        # Removido grandTotalRow (não compatível com st_aggrid)
        suppressAggFuncInHeader=True,  # Mantém apenas a supressão do texto de soma no header
        # Define estilo da linha pinned (caso exista)
        rowStyle=js_estilo_linha_totais.js_code
    )

    # Se tiver coluna de dados numéricos, configurar como numericColumn
    if coluna_dados and coluna_dados in df_para_exibir.columns:
        gb.configure_column(
            coluna_dados,
            type=["numericColumn", "numberColumnFilter"],
            filter="agNumberColumnFilter",
            aggFunc="sum",
            enableValue=True,
            valueFormatter=JsCode("""
            function(params) {
                if (params.value == null || params.value === undefined) return '';
                return new Intl.NumberFormat('pt-BR').format(params.value);
            }
            """).js_code,
            cellStyle=JsCode("""
            function(params) {
                if (params.node && params.node.rowPinned) {
                    return {
                        'font-weight': 'bold',
                        'background-color': '#f0f2f7'
                    };
                }
                return null;
            }
            """).js_code
        )

    # Otimizações para grandes datasets
    if is_large_dataset:
        gb.configure_grid_options(
            rowBuffer=100,
            animateRows=False,
            suppressColumnVirtualisation=False,
            suppressRowVirtualisation=False,
            enableCellTextSelection=True,
            enableBrowserTooltips=True
        )

    # Barra de status personalizada (mostra estatísticas de soma, média, min, max, etc.)
    gb.configure_grid_options(
        statusBar={
            'statusPanels': [
                {'statusPanel': 'agTotalRowCountComponent', 'align': 'left'},
                {'statusPanel': 'agFilteredRowCountComponent', 'align': 'left'},
                {
                    'statusPanel': 'agCustomStatsToolPanel',
                    'statusPanelParams': {
                        'aggStatFunc': js_agg_functions.js_code
                    }
                }
            ]
        }
    )

    # Barra lateral e configs avançadas
    gb.configure_side_bar()

    # Ajustes finais de seleção e foco
    gb.configure_grid_options(
        rowSelection=False,
        suppressRowClickSelection=True,
        cellSelection=True,
        enableRangeSelection=True,
        enableRangeHandle=True,
        suppressMultiRangeSelection=False,
        suppressCellFocus=False,
        tabToNextHeader=False,
        enableCellTextSelection=False,
        copyHeadersToClipboard=True,
        clipboardDelimiter='\t',
        suppressMenuHide=True,
        suppressMovableColumns=False,
        suppressRowHoverHighlight=True,
        suppressRowDeselection=True,
    )

    # -------------------------------------------------------------------
    # NOVO: Adicionar linha de totais fixada (pinned) no topo ou rodapé
    # -------------------------------------------------------------------
    if posicao_totais in ("bottom", "top") and coluna_dados and (coluna_dados in df_para_exibir.columns):
        pinned_row = {}
        # Valor total da coluna_dados
        total_matriculas = df_para_exibir[coluna_dados].sum()

        # Preenche o dicionário da pinned row
        pinned_row[coluna_dados] = total_matriculas

        # Exibe "TOTAL" em alguma coluna de nome (se existir)
        if coluna_nome_principal:
            pinned_row[coluna_nome_principal] = "TOTAL"

        # Configura pinnedBottomRowData ou pinnedTopRowData
        if posicao_totais == "bottom":
            gb.configure_grid_options(pinnedBottomRowData=[pinned_row])
        else:
            gb.configure_grid_options(pinnedTopRowData=[pinned_row])

    grid_options = gb.build()

    st.markdown("""
        <style>
        .nav-panel {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-bottom: 15px;
        }
        .nav-button {
            background-color: #f0f2f6;
            padding: 8px 15px;
            border-radius: 5px;
            border: 1px solid #ddd;
            color: #0066cc;
            font-weight: bold;
            text-align: center;
            cursor: pointer;
            margin: 0;
            transition: background-color 0.2s, transform 0.1s;
        }
        .nav-button:hover {
            background-color: #e0e5f2;
            transform: translateY(-1px);
        }
        .nav-button:active {
            transform: translateY(1px);
        }
        </style>
    """, unsafe_allow_html=True)

    grid_return = AgGrid(
        df_para_exibir,
        gridOptions=grid_options,
        height=altura,
        custom_css="""
            .ag-row-selected { background-color: transparent !important; }
            .numeric-cell { text-align: right; }

            .ag-cell.ag-cell-range-selected,
            .ag-cell.ag-cell-range-selected-1,
            .ag-cell.ag-cell-range-selected-2,
            .ag-cell.ag-cell-range-selected-3,
            .ag-cell.ag-cell-range-selected-4 {
                background-color: #e6f2ff !important; 
                color: #000 !important; 
            }
            .ag-row {
                background-color: inherit !important;
            }
            .ag-row:hover {
                background-color: inherit !important;
            }
            .ag-row-selected,
            .ag-row-selected:hover {
                background-color: transparent !important;
                border: none !important;
            }
            .ag-header-cell-text { 
                font-weight: bold !important;
                white-space: normal !important;
                line-height: 1.2 !important;
                overflow: visible !important;
                font-size: 12px !important;
            }
            .ag-header-cell {
                padding: 4px !important;
                height: auto !important;
                min-height: 50px !important;
                display: flex !important;
                align-items: center !important;
            }
            .ag-header-row {
                height: auto !important;
            }
            .ag-cell { 
                overflow: hidden; 
                text-overflow: ellipsis; 
            }
        """,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        theme="streamlit",
        key=f"aggrid_{id(df_para_exibir)}"
    )

    js_clipboard_helper = """
    <script>
        setTimeout(function() {
            try {
                const gridDiv = document.querySelector('.ag-root-wrapper');
                if (gridDiv && gridDiv.gridOptions && gridDiv.gridOptions.api) {
                    const api = gridDiv.gridOptions.api;
                    document.addEventListener('keydown', function(e) {
                        if (e.ctrlKey && e.key === 'c') {
                            api.copySelectedRangeToClipboard(true);
                        }
                        if (e.ctrlKey && e.key === 'a') {
                            e.preventDefault();
                            const allColumns = api.getColumns();
                            if (allColumns.length > 0) {
                                const range = {
                                    startRow: 0,
                                    endRow: api.getDisplayedRowCount() - 1,
                                    startColumn: allColumns[0],
                                    endColumn: allColumns[allColumns.length - 1]
                                };
                                api.addCellRange(range);
                            }
                        }
                    });
                }
            } catch(e) {
                console.error('Erro ao configurar clipboard:', e);
            }
        }, 800);
    </script>
    """
    st.markdown(js_clipboard_helper, unsafe_allow_html=True)

    js_fix_headers = """
    <script>
        setTimeout(function() {
            try {
                const gridDivs = document.querySelectorAll('.ag-header-row');
                gridDivs.forEach(function(div) {
                    div.style.height = 'auto';
                    div.style.minHeight = '50px';
                });
                const headerCells = document.querySelectorAll('.ag-header-cell-text');
                headerCells.forEach(function(cell) {
                    cell.style.whiteSpace = 'normal';
                    cell.style.overflow = 'visible';
                });
            } catch(e) { console.error('Erro ao ajustar cabeçalhos:', e); }
        }, 500);
    </script>
    """
    st.markdown(js_fix_headers, unsafe_allow_html=True)

    filtered_data = grid_return['data']
    if len(filtered_data) != len(df_para_exibir):
        st.info(
            f"Filtro aplicado: mostrando {formatar_numero(len(filtered_data))} "
            f"de {formatar_numero(len(df_para_exibir))} registros."
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

# Seleção do nível de agregação
tipo_visualizacao = st.sidebar.radio(
    "Nível de Agregação:",
    ["Escola", "Município", "Estado"]
)

# Escolha do DataFrame
if tipo_visualizacao == "Escola":
    df = escolas_df
elif tipo_visualizacao == "Município":
    df = municipio_df
else:
    df = estado_df

# Mapeamento de colunas para a seleção de etapas
mapeamento_colunas = criar_mapeamento_colunas(df)

# Filtro do Ano
if "ANO" in df.columns:
    # Ordena em ordem decrescente (mais recente primeiro)
    anos_disponiveis = sorted(df["ANO"].unique(), reverse=True)

    # Substituir selectbox por multiselect
    anos_selecionados = st.sidebar.multiselect(
        "Ano do Censo:",
        options=anos_disponiveis,
        default=[anos_disponiveis[0]],  # Agora seleciona o ano mais recente (primeiro da lista)
        key="anos_multiselect"
    )

    # Verificar se pelo menos um ano foi selecionado
    if not anos_selecionados:
        st.warning("Por favor, selecione pelo menos um ano.")
        st.stop()

    # Filtrar o DataFrame para incluir todos os anos selecionados
    df_filtrado = df[df["ANO"].isin(anos_selecionados)]
else:
    st.error("A coluna 'ANO' não foi encontrada nos dados carregados.")
    st.stop()

# Filtro de Etapa de Ensino
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

# Filtro de Dependência Administrativa
if "DEPENDENCIA ADMINISTRATIVA" in df.columns:
    dependencias_disponiveis = sorted(df["DEPENDENCIA ADMINISTRATIVA"].unique())

    # Usa o componente nativo st.pills
    dependencia_selecionada = st.sidebar.pills(
        "DEPENDENCIA ADMINISTRATIVA:",
        options=dependencias_disponiveis,
        default=dependencias_disponiveis,  # Todas selecionadas por padrão
        selection_mode="multi",
        label_visibility="visible"
    )

    # Aplicar filtro
    if dependencia_selecionada:
        df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"].isin(dependencia_selecionada)]
    else:
        # DataFrame vazio se nenhuma opção selecionada
        df_filtrado = df_filtrado[0:0]
else:
    st.warning("A coluna 'DEPENDENCIA ADMINISTRATIVA' não foi encontrada nos dados carregados.")

# Determinar a coluna de dados
coluna_dados = obter_coluna_dados(etapa_selecionada, subetapa_selecionada, serie_selecionada, mapeamento_colunas)

coluna_existe, coluna_real = verificar_coluna_existe(df_filtrado, coluna_dados)
if coluna_existe:
    coluna_dados = coluna_real
    # Filtrar valores > 0
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

    with pd.option_context('mode.chained_assignment', None):
        tabela_exibicao[coluna_dados] = tabela_exibicao[coluna_dados].apply(
            lambda x: formatar_numero(x) if pd.notnull(x) else "-"
        )
else:
    tabela_dados = df_filtrado[colunas_existentes].copy()
    tabela_exibicao = tabela_dados.copy()

# Preparar a tabela para exibição imediata
tabela_filtrada = tabela_exibicao.copy()

# Adicionar linha de totais
try:
    tabela_com_totais = tabela_filtrada
except Exception as e:
    st.warning(f"Não foi possível adicionar a linha de totais: {str(e)}")

# Exibir a tabela imediatamente
altura_tabela = 600  # Altura padrão fixa

# Verificar se a posição dos totais foi definida
if 'posicao_totais' not in locals():
    posicao_totais = "Rodapé"  # Valor padrão

posicao_totais_map = {
    "Rodapé": "bottom",
    "Topo": "top",
    "Nenhum": None
}

# Garantir que os dados são numéricos antes de enviar ao AgGrid
if coluna_dados and coluna_dados in tabela_com_totais.columns:
    with pd.option_context('mode.chained_assignment', None):
        tabela_com_totais[coluna_dados] = pd.to_numeric(tabela_com_totais[coluna_dados], errors='coerce')
        tabela_com_totais[coluna_dados] = tabela_com_totais[coluna_dados].fillna(0)

try:
    grid_result = exibir_tabela_com_aggrid(
        tabela_com_totais,
        altura=altura_tabela,
        coluna_dados=coluna_dados,
        posicao_totais=posicao_totais_map.get(posicao_totais)
    )
except Exception as e:
    st.error(f"Erro ao exibir tabela no AgGrid: {str(e)}")
    st.dataframe(tabela_com_totais, height=altura_tabela)

# Mostrar configurações APÓS a tabela
tab1, tab2 = st.tabs(["Configurações", "Resumo Estatístico"])

with tab1:
    st.write("### Configurações de exibição")
    col1, col2, col3, col4 = st.columns(4)

    with col4:
        altura_personalizada = st.checkbox(ROTULO_AJUSTAR_ALTURA, value=False, help=DICA_ALTURA_TABELA)
        if altura_personalizada:
            altura_manual = st.slider("Altura da tabela (pixels)",
                                      min_value=200,
                                      max_value=1000,
                                      value=600,
                                      step=50)
        else:
            altura_manual = 600

    with col1:
        total_registros = len(tabela_exibicao)
        mostrar_todos = st.checkbox(ROTULO_MOSTRAR_REGISTROS, value=True)

        posicao_totais = st.radio(
            "Linha de totais:",
            ["Rodapé", "Topo", "Nenhum"],
            index=0,  # Padrão: Rodapé
            horizontal=True
        )

    with col2:
        st.write(" ")
    with col3:
        modo_desempenho = st.checkbox(ROTULO_MODO_DESEMPENHO, value=True,
                                      help=DICA_MODO_DESEMPENHO)

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
                    tabela_dados = df_filtrado_tabela[colunas_tabela].sort_values(by=coluna_dados, ascending=False)
                    tabela_exibicao = tabela_dados.copy()
                    with pd.option_context('mode.chained_assignment', None):
                        if coluna_dados in tabela_exibicao.columns:
                            tabela_exibicao[coluna_dados] = tabela_exibicao[coluna_dados].apply(
                                lambda x: formatar_numero(x) if pd.notnull(x) else "-"
                            )
                        if '% do Total' in tabela_exibicao.columns:
                            tabela_exibicao['% do Total'] = tabela_exibicao['% do Total'].apply(
                                lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
                            )
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

    altura_tabela = altura_manual

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
                file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{anos_selecionados}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        except Exception as e:
            st.error(f"Erro ao preparar Excel para download: {str(e)}")


# -------------------------------
# Rodapé do Dashboard
# -------------------------------
st.markdown("---")
st.markdown(RODAPE_NOTA)
