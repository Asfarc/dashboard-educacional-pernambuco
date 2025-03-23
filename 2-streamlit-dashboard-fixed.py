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
        for df in [escolas_df, estado_df, municipio_df]:
            for col in df.columns:
                if col.startswith("Número de"):
                    df[col] = pd.to_numeric(df[col], errors='coerce')

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

    # Função auxiliar para verificar e obter o nome correto da coluna
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

    # Carrega o mapeamento do arquivo JSON (se falhar, st.stop() será chamado na função)
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
        for subetapa, series_dict in config.get("series", {}).items():
            if subetapa not in mapeamento_ajustado[etapa]["series"]:
                mapeamento_ajustado[etapa]["series"][subetapa] = {}

            for serie, coluna in series_dict.items():
                mapeamento_ajustado[etapa]["series"][subetapa][serie] = obter_coluna_real(coluna)

    return mapeamento_ajustado

def obter_coluna_dados(etapa, subetapa, serie, mapeamento):
    """
    Determina a coluna de dados com base na etapa, subetapa e série selecionadas.

    Parâmetros:
    etapa (str): Etapa de ensino selecionada
    subetapa (str): Subetapa selecionada ("Todas" ou nome específico)
    serie (str): Série selecionada ("Todas" ou nome específico)
    mapeamento (dict): Mapeamento de colunas

    Retorna:
    str: Nome da coluna de dados
    """
    # Verificar se a etapa existe no mapeamento
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
    Verifica se uma coluna existe no DataFrame, tentando encontrar uma correspondência
    exata ou insensível a maiúsculas/minúsculas.

    Parâmetros:
    df (DataFrame): DataFrame a ser verificado
    coluna_nome (str): Nome da coluna a procurar

    Retorna:
    tuple: (coluna_existe, coluna_real)
        coluna_existe (bool): Indica se a coluna foi encontrada.
        coluna_real (str): Nome real da coluna encontrada ou nome original
    """
    if not coluna_nome:
        return False, ""

    # Verifica se a coluna existe exatamente como especificada
    if coluna_nome in df.columns:
        return True, coluna_nome

    # Verifica se existe uma versão case-insensitive
    coluna_normalizada = coluna_nome.lower().strip()
    colunas_normalizadas = {col.lower().strip(): col for col in df.columns}

    if coluna_normalizada in colunas_normalizadas:
        return True, colunas_normalizadas[coluna_normalizada]

    # Não encontrou a coluna
    return False, coluna_nome


def adicionar_linha_totais(df, coluna_dados):
    """
    Adiciona uma linha de totais ao DataFrame.

    Parâmetros:
    df (DataFrame): DataFrame a ser processado
    coluna_dados (str): Nome da coluna de dados numéricos

    Retorna:
    DataFrame: DataFrame com a linha de totais adicionada
    """
    if df.empty:
        return df

    # Verificar se TOTAL já existe no dataframe
    if 'TOTAL' in df.index or (df.iloc[:, 0] == 'TOTAL').any():
        return df

    # Criar uma linha de totais
    totais = {}

    # Inicializar todas as colunas como vazias
    for col in df.columns:
        totais[col] = ""

    # Primeira coluna como "TOTAL"
    if len(df.columns) > 0:
        totais[df.columns[0]] = "TOTAL"

    # Calcular total para a coluna de dados
    if coluna_dados in df.columns:
        # Usar sum() apenas em valores numéricos
        try:
            valor_total = pd.to_numeric(df[coluna_dados], errors='coerce').sum()
            totais[coluna_dados] = valor_total  # Manter numérico para cálculos
        except Exception:
            totais[coluna_dados] = ""

    # Definir percentual como 100%
    if '% do Total' in df.columns:
        totais['% do Total'] = 100.0

    # Criar DataFrame com a linha de totais
    linha_totais = pd.DataFrame([totais], index=['TOTAL'])

    # Concatenar com o DataFrame original
    return pd.concat([df, linha_totais])

# -----------------------------------------------------------------
# 1. Função para centralizar ORDENAR e FORMATAR (CASO VOCÊ QUEIRA)
# -----------------------------------------------------------------
def preparar_tabela_para_exibicao(df_base, colunas_para_exibir, coluna_ordenacao):
    """
    Ordena o DataFrame base pela coluna_ordenacao (se existir), cria uma cópia
    e formata as colunas numéricas e percentuais para exibição.
    Retorna (tabela_dados, tabela_exibicao).
    """
    # Filtra só colunas que existem
    colunas_existentes = [c for c in colunas_para_exibir if c in df_base.columns]
    tabela_dados = df_base[colunas_existentes]

    # Ordenar se a coluna principal existir
    if coluna_ordenacao in tabela_dados.columns:
        tabela_dados = tabela_dados.sort_values(by=coluna_ordenacao, ascending=False)

    # Cria cópia para exibir (formatar sem mexer nos dados brutos)
    tabela_exibicao = tabela_dados.copy()

    # Aplicando formatações
    with pd.option_context('mode.chained_assignment', None):
        # Formata a coluna principal
        if coluna_ordenacao in tabela_exibicao.columns:
            tabela_exibicao[coluna_ordenacao] = tabela_exibicao[coluna_ordenacao].apply(
                lambda x: formatar_numero(x) if pd.notnull(x) else "-"
            )

        # Formata '% do Total'
        if '% do Total' in tabela_exibicao.columns:
            tabela_exibicao['% do Total'] = tabela_exibicao['% do Total'].apply(
                lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
            )

    return tabela_dados, tabela_exibicao

def converter_df_para_csv(df):
    """Converte DataFrame para formato CSV, incluindo tratamento para DataFrame vazio."""
    if df is None or df.empty:
        return "Não há dados para exportar.".encode('utf-8')
    try:
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        st.error(f"Erro ao converter para CSV: {str(e)}")
        return "Erro na conversão".encode('utf-8')

def converter_df_para_excel(df):
    """Converte DataFrame para formato Excel, incluindo tratamento para DataFrame vazio."""
    if df is None or df.empty:
        # Retorna um arquivo Excel válido mas com uma aba vazia
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
# --------------------------------------------------------
# 2. (Opcional) Função para centralizar NAVEGAÇÃO no AgGrid
# --------------------------------------------------------
def navegar_tabela(label_botao, key_botao, posicao='top'):
    """
    Cria um botão que, quando clicado, rola a tabela AgGrid para o topo ou para o final.
    :param label_botao: Texto que aparece no botão (ex: "⏫ Primeira Linha").
    :param key_botao: Chave única para o botão.
    :param posicao: 'top' ou 'bottom' -- define a direção da rolagem.
    """
    if st.button(label_botao, key=key_botao):
        scroll_script = f"""
            <script>
                setTimeout(function() {{
                    try {{
                        const gridDiv = document.querySelector('.ag-root-wrapper');
                        if (gridDiv && gridDiv.gridOptions && gridDiv.gridOptions.api) {{
                            const api = gridDiv.gridOptions.api;
                            if ('{posicao}' === 'top') {{
                                api.ensureIndexVisible(0);
                                api.setFocusedCell(0, api.getColumnDefs()[0].field);
                            }} else {{
                                const lastIndex = api.getDisplayedRowCount() - 1;
                                if (lastIndex >= 0) {{
                                    api.ensureIndexVisible(lastIndex);
                                    api.setFocusedCell(lastIndex, api.getColumnDefs()[0].field);
                                }}
                            }}
                        }}
                    }} catch(e) {{ console.error(e); }}
                }}, 300);
            </script>
        """
        st.markdown(scroll_script, unsafe_allow_html=True)

# Função para exibir a tabela com AgGrid - implementação corrigida
def exibir_tabela_com_aggrid(df_para_exibir, altura=600, coluna_dados=None):
    """
    Exibe uma tabela aprimorada usando AgGrid com todas as melhorias implementadas
    corretamente e otimizações de robustez.

    Args:
        df_para_exibir (DataFrame): Dados a serem exibidos
        altura (int): Altura da tabela em pixels
        coluna_dados (str): Nome da coluna principal de dados numéricos

    Returns:
        dict: Resposta do grid contendo dados filtrados/ordenados
    """
    # Validar entrada
    if df_para_exibir is None or df_para_exibir.empty:
        st.warning("Não há dados para exibir na tabela.")
        return {"data": pd.DataFrame()}

    # Verificar o tamanho dos dados para otimizações - sem copiar o dataframe
    is_large_dataset = len(df_para_exibir) > 5000
    is_very_large_dataset = len(df_para_exibir) > 10000

    # Para grandes datasets, mostrar aviso e opção de limitar
    if is_very_large_dataset:
        st.warning(
            f"O conjunto de dados tem {formatar_numero(len(df_para_exibir))} linhas, o que pode causar lentidão na visualização.")
        mostrar_tudo = st.checkbox("Carregar todos os dados (pode ser lento)", value=False)
        if not mostrar_tudo:
            # Verificar se há linha TOTAL usando método eficiente
            tem_total = False
            total_rows = []

            # Verificar em cada coluna, não apenas na primeira
            for col in df_para_exibir.columns:
                mask = df_para_exibir[col].astype(str).str.contains('TOTAL', case=False, na=False)
                if mask.any():
                    total_indices = df_para_exibir.index[mask]
                    total_rows.extend(total_indices.tolist())
                    tem_total = True

            # Também verificar no índice
            if isinstance(df_para_exibir.index, pd.Index):
                mask = df_para_exibir.index.astype(str).str.contains('TOTAL', case=False, na=False)
                if mask.any():
                    total_indices = df_para_exibir.index[mask]
                    total_rows.extend(total_indices.tolist())
                    tem_total = True

            # Criar uma lista com os índices que queremos manter
            indices_para_manter = df_para_exibir.index[:5000].tolist()

            # Adicionar linhas de totais se existirem
            if tem_total:
                # Eliminar duplicatas e preservar ordem
                total_rows = list(dict.fromkeys(total_rows))
                indices_para_manter.extend(total_rows)

            # Usar loc para criar view
            df_para_exibir = df_para_exibir.loc[indices_para_manter]
            st.info(f"Mostrando amostra de 5.000 registros (de um total maior)")

    # Preparar strings de JavaScript seguros para uso no AgGrid

    # 1. LINHA DE TOTAIS - implementação mais segura para detectar TOTAL
    js_total_row = JsCode("""
    function(params) {
        try {
            // Verifica se há dados na linha
            if (!params.data) {
                return null;
            }

            // Verifica qualquer coluna com TOTAL (case insensitive)
            let isTotal = false;
            for (const key in params.data) {
                if (params.data[key] !== null && 
                    params.data[key] !== undefined &&
                    params.data[key].toString().toUpperCase().includes('TOTAL')) {
                    isTotal = true;
                    break;
                }
            }

            // Verifica se é a última linha (para totais calculados dinamicamente)
            if (isTotal || 
                (params.node && params.api && 
                params.node.rowIndex === (params.api.getDisplayedRowCount() - 1))) {
                return {
                    'font-weight': 'bold',
                    'background-color': '#e6f2ff',
                    'border-top': '2px solid #b3d9ff',
                    'color': '#0066cc'
                };
            }
            return null;
        } catch (error) {
            console.error('Erro ao estilizar linha:', error);
            return null;
        }
    }
    """)

    # 5. ESTATÍSTICAS - implementação mais robusta
    js_agg_functions = JsCode("""
    function(params) {
        try {
            // Obter coluna de dados principal
            const dataColumn = "%s";
            if (!dataColumn) return 'Coluna de dados não definida';

            // Coletar todos os valores visíveis
            const values = [];
            let totalSum = 0;
            let count = 0;

            params.api.forEachNodeAfterFilter(node => {
                if (!node.data) return;

                // Verifica se não é linha de TOTAL
                let isTotal = false;
                for (const key in node.data) {
                    if (node.data[key] && 
                        node.data[key].toString().toUpperCase().includes('TOTAL')) {
                        isTotal = true;
                        break;
                    }
                }
                if (isTotal) return;

                // Extrai o valor como número
                const cellValue = node.data[dataColumn];
                if (cellValue !== null && cellValue !== undefined) {
                    const numValue = Number(cellValue.toString().replace(/[^0-9.,]/g, '').replace(',', '.'));
                    if (!isNaN(numValue)) {
                        values.push(numValue);
                        totalSum += numValue;
                        count++;
                    }
                }
            });
            // Formatar para exibição amigável
            const formatNum = function(num) {
                // Primeiro formatar usando Intl.NumberFormat
                let formatted = new Intl.NumberFormat('pt-BR', { 
                    maximumFractionDigits: 2 
                }).format(num);

                // Depois converter para usar ponto como separador
                // Substituir pontos por underscores temporariamente
                formatted = formatted.replace(/\\./g, '_');
                // Substituir vírgulas por pontos
                formatted = formatted.replace(/,/g, '.');
                // Substituir underscores de volta para pontos
                formatted = formatted.replace(/_/g, '.');
                return formatted;
            };
            // Calcular estatísticas
            if (values.length === 0) {
                return 'Não há dados numéricos';
            }
            const avg = totalSum / count;
            values.sort((a, b) => a - b);
            const min = values[0];
            const max = values[values.length - 1];
            // Mensagem formatada
            return `Total: ${formatNum(totalSum)} | Média: ${formatNum(avg)} | Mín: ${formatNum(min)} | Máx: ${formatNum(max)}`;
        } catch (error) {
            console.error('Erro ao calcular estatísticas:', error);
            return 'Erro ao calcular estatísticas';
        }
    }
    """ % (coluna_dados if coluna_dados else ''))

    # Configurar o construtor de opções do grid
    gb = GridOptionsBuilder.from_dataframe(df_para_exibir)

    # 1. Adicione um objeto de localização personalizado para PT-BR
    localeText = {
        # Textos dos filtros
        "contains": "Contém",
        "notContains": "Não contém",
        "equals": "Igual a",
        "notEqual": "Diferente de",
        "startsWith": "Começa com",
        "endsWith": "Termina com",
        "blank": "Em branco",
        "notBlank": "Não em branco",

        # Configure essa função personalizada para formatar números
        "thousandSeparator": ".",
        "decimalSeparator": ",",

        # Botões dos filtros
        "applyFilter": "Aplicar",
        "resetFilter": "Limpar",
        "clearFilter": "Limpar",
        "cancelFilter": "Cancelar",

        # Rótulos de comparação numérica
        "lessThan": "Menor que",
        "greaterThan": "Maior que",
        "lessThanOrEqual": "Menor ou igual a",
        "greaterThanOrEqual": "Maior ou igual a",
        "inRange": "No intervalo",

        # Textos da barra de status
        "filterOoo": "Filtrado",
        "noRowsToShow": "Sem dados para exibir",
        "enabled": "Habilitado",

        # Outras opções comuns
        "search": "Buscar",
        "selectAll": "Selecionar todos",
        "searchOoo": "Buscar...",
        "blanks": "Em branco",
        "noMatches": "Sem correspondência",

        # Textos do painel de colunas/filtros
        "columns": "Colunas",
        "filters": "Filtros",
        "rowGroupColumns": "Agrupar por",
        "rowGroupColumnsEmptyMessage": "Arraste colunas aqui para agrupar",
        "valueColumns": "Valores",
        "pivotMode": "Modo Pivot",
        "groups": "Grupos",
        "values": "Valores",
        "pivots": "Pivôs",
        "valueColumnsEmptyMessage": "Arraste aqui para agregar",
        "pivotColumnsEmptyMessage": "Arraste aqui para definir pivô",
        "toolPanelButton": "Painéis",

        # Outros rótulos da UI
        "loadingOoo": "Carregando...",
        "page": "Página",
        "next": "Próximo",
        "last": "Último",
        "first": "Primeiro",
        "previous": "Anterior",
        "of": "de",
        "to": "até",
        "rows": "linhas",
        "loading": "Carregando...",

        # Statuses da barra de status
        "totalRows": "Total de linhas",
        "totalAndFilteredRows": "Linhas",
        "selectedRows": "Selecionadas",
        "filteredRows": "Filtradas",

        # Textos de agregação
        "sum": "Soma",
        "min": "Mínimo",
        "max": "Máximo",
        "average": "Média",
        "count": "Contagem"
    }

    # 2. CONFIGURAÇÃO PADRÃO PARA TODAS AS COLUNAS
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
        suppressMenu=False
    )

    # Configurar larguras específicas para colunas selecionadas
    if "ANO" in df_para_exibir.columns:
        gb.configure_column("ANO", width=80)

    if "CODIGO DO MUNICIPIO" in df_para_exibir.columns:
        gb.configure_column("CODIGO DO MUNICIPIO", width=80)

    if "NOME DO MUNICIPIO" in df_para_exibir.columns:
        gb.configure_column("NOME DO MUNICIPIO", width=200)

    if "CODIGO DA ESCOLA" in df_para_exibir.columns:
        gb.configure_column("CODIGO DA ESCOLA", width=80)

    if "NOME DA ESCOLA" in df_para_exibir.columns:
        gb.configure_column("NOME DA ESCOLA", width=300)

    if "DEPENDENCIA ADMINISTRATIVA" in df_para_exibir.columns:
        gb.configure_column("DEPENDENCIA ADMINISTRATIVA", width=100)

    # Adicionar barra de pesquisa rápida e estilo para linha de totais
    gb.configure_grid_options(
        enableQuickFilter=True,
        quickFilterText="",
        getRowStyle=js_total_row,
        suppressCellFocus=False,
        alwaysShowVerticalScroll=True,
        localeText=localeText,
    )

    # Configurar colunas numéricas específicas
    if coluna_dados and coluna_dados in df_para_exibir.columns:
        gb.configure_column(
            coluna_dados,
            type=["numericColumn", "numberColumnFilter"],
            filter="agNumberColumnFilter",
            filterParams={
                "inRangeInclusive": True,
                "applyButton": True,
                "clearButton": True
            },
            aggFunc="sum",
            enableValue=True,
            cellClass="numeric-cell"
        )

    # 4. OTIMIZAÇÃO PARA GRANDES DATASETS
    if is_large_dataset:
        gb.configure_grid_options(
            rowBuffer=100,
            animateRows=False,
            suppressColumnVirtualisation=False,
            suppressRowVirtualisation=False,
            enableCellTextSelection=True,
            enableBrowserTooltips=True
        )
        if is_very_large_dataset and mostrar_tudo:
            gb.configure_grid_options(
                rowModelType='clientSide',
                cacheBlockSize=100,
                maxBlocksInCache=10
            )

    # 5. ESTATÍSTICAS
    gb.configure_grid_options(
        statusBar={
            'statusPanels': [
                {
                    'statusPanel': 'agTotalRowCountComponent',
                    'align': 'left'
                },
                {
                    'statusPanel': 'agFilteredRowCountComponent',
                    'align': 'left'
                },
                {
                    'statusPanel': 'agCustomStatsToolPanel',
                    'statusPanelParams': {
                        'aggStatFunc': js_agg_functions
                    }
                }
            ]
        }
    )

    # Barra lateral e seleção
    gb.configure_side_bar()
    gb.configure_selection('single')

    # Construir as opções finais do grid
    grid_options = gb.build()

    # Interface para controles de navegação
    st.write("### Navegação da tabela")

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

    # Botões de navegação acima
    col_nav_top1, col_nav_top2 = st.columns([1, 1])
    with col_nav_top1:
        navegar_tabela(ROTULO_BTN_PRIMEIRA_LINHA, "btn_top_1", posicao='top')
    with col_nav_top2:
        navegar_tabela(ROTULO_BTN_ULTIMA_LINHA, "btn_bottom_1", posicao='bottom')

    # Dicas de navegação
    st.markdown(DICAS_NAVEGACAO, unsafe_allow_html=True)

    # Renderizar o grid
    grid_return = AgGrid(
        df_para_exibir,
        gridOptions=grid_options,
        height=altura,
        custom_css="""
            .ag-row-selected { background-color: #eff7ff !important; }
            .numeric-cell { text-align: right; }
            .ag-header-cell-text { font-weight: bold; }
            .ag-cell { overflow: hidden; text-overflow: ellipsis; }
        """,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        theme="streamlit",
        key=f"aggrid_{id(df_para_exibir)}"
    )

    # Botões de navegação abaixo
    col_nav_bot1, col_nav_bot2 = st.columns([1, 1])
    with col_nav_bot1:
        navegar_tabela("⏫ Primeira Linha", "btn_top_2", posicao='top')
    with col_nav_bot2:
        navegar_tabela("⏬ Última Linha", "btn_bottom_2", posicao='bottom')

    # Feedback sobre filtros aplicados
    filtered_data = grid_return['data']
    if len(filtered_data) != len(df_para_exibir):
        st.info(f"Filtro aplicado: mostrando {formatar_numero(len(filtered_data))} de {formatar_numero(len(df_para_exibir))} registros.")

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

# Seleção do DataFrame conforme o nível escolhido
if tipo_visualizacao == "Escola":
    df = escolas_df
elif tipo_visualizacao == "Município":
    df = municipio_df
else:
    df = estado_df

# Agora crie o mapeamento de colunas usando o DataFrame selecionado
mapeamento_colunas = criar_mapeamento_colunas(df)

# Filtro do Ano
if "ANO" in df.columns:
    anos_disponiveis = sorted(df["ANO"].unique())
    ano_selecionado = st.sidebar.selectbox("Ano do Censo:", anos_disponiveis)
    df_filtrado = df[df["ANO"] == ano_selecionado]
else:
    st.error("A coluna 'ANO' não foi encontrada nos dados carregados.")
    st.stop()

# Filtro da DEPENDENCIA ADMINISTRATIVA
if "DEPENDENCIA ADMINISTRATIVA" in df.columns:
    dependencias_disponiveis = sorted(df["DEPENDENCIA ADMINISTRATIVA"].unique())
    dependencia_selecionada = st.sidebar.multiselect(
        "DEPENDENCIA ADMINISTRATIVA:",
        dependencias_disponiveis,
        default=dependencias_disponiveis
    )
    if dependencia_selecionada:
        df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"].isin(dependencia_selecionada)]
else:
    st.warning("A coluna 'DEPENDENCIA ADMINISTRATIVA' não foi encontrada nos dados carregados.")

# Filtro da Etapa de Ensino
etapas_disponiveis = list(mapeamento_colunas.keys())
etapa_selecionada = st.sidebar.selectbox(
    "Etapa de Ensino:",
    etapas_disponiveis
)

# Verificação se a etapa está no mapeamento
if etapa_selecionada not in mapeamento_colunas:
    st.error(f"A etapa '{etapa_selecionada}' não foi encontrada no mapeamento de colunas.")
    st.stop()

# Filtro da Subetapa
if "subetapas" in mapeamento_colunas[etapa_selecionada] and mapeamento_colunas[etapa_selecionada]["subetapas"]:
    subetapas_disponiveis = list(mapeamento_colunas[etapa_selecionada]["subetapas"].keys())
    subetapa_selecionada = st.sidebar.selectbox(
        "Subetapa:",
        ["Todas"] + subetapas_disponiveis
    )
else:
    subetapa_selecionada = "Todas"

# Filtro para a Série, se aplicável
series_disponiveis = []
if (subetapa_selecionada != "Todas" and
        "series" in mapeamento_colunas[etapa_selecionada] and
        subetapa_selecionada in mapeamento_colunas[etapa_selecionada]["series"]):
    series_disponiveis = list(mapeamento_colunas[etapa_selecionada]["series"][subetapa_selecionada].keys())
    serie_selecionada = st.sidebar.selectbox(
        "Série:",
        ["Todas"] + series_disponiveis
    )
else:
    serie_selecionada = "Todas"

# -------------------------------
# Determinação da Coluna de Dados
# -------------------------------
coluna_dados = obter_coluna_dados(etapa_selecionada, subetapa_selecionada, serie_selecionada, mapeamento_colunas)

# Verifica se a coluna existe no DataFrame
coluna_existe, coluna_real = verificar_coluna_existe(df_filtrado, coluna_dados)
if coluna_existe:
    coluna_dados = coluna_real
else:
    st.warning(f"A coluna '{coluna_dados}' não está disponível nos dados.")
    coluna_principal = mapeamento_colunas[etapa_selecionada].get("coluna_principal", "")
    coluna_existe, coluna_principal_real = verificar_coluna_existe(df_filtrado, coluna_principal)

    if coluna_existe:
        coluna_dados = coluna_principal_real
        st.info(f"Usando '{coluna_dados}' como alternativa")
    else:
        st.error("Não foi possível encontrar dados para a etapa selecionada.")
        st.stop()

# -------------------------------
# Cabeçalho e Informações Iniciais
# -------------------------------
st.title(TITULO_DASHBOARD)
st.markdown(f"**Visualização por {tipo_visualizacao} - Ano: {ano_selecionado}**")

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
    colunas_adicionais = ["CODIGO DA ESCOLA", "NOME DA ESCOLA", "CODIGO DO MUNICIPIO",
                          "NOME DO MUNICIPIO", "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"]
elif tipo_visualizacao == "Município":
    colunas_adicionais = ["CODIGO DO MUNICIPIO", "NOME DO MUNICIPIO",
                          "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"]
else:
    colunas_adicionais = ["CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"]

for col in colunas_adicionais:
    if col in df_filtrado.columns:
        colunas_tabela.append(col)

if coluna_dados in df_filtrado.columns:
    colunas_tabela.append(coluna_dados)

colunas_existentes = [col for col in colunas_tabela if col in df_filtrado.columns]
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

tab1, tab2 = st.tabs(["Visão Tabular", "Resumo Estatístico"])

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

    with col2:
        st.write(" ")
    with col3:
        modo_desempenho = st.checkbox(ROTULO_MODO_DESEMPENHO, value=True,
                                      help=DICA_MODO_DESEMPENHO)

    st.write("### Filtros da tabela")
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
        tabela_com_totais = adicionar_linha_totais(tabela_filtrada, coluna_dados)
    except Exception as e:
        st.warning(f"Não foi possível adicionar a linha de totais: {str(e)}")
        tabela_com_totais = tabela_filtrada

    altura_tabela = altura_manual
    try:
        grid_result = exibir_tabela_com_aggrid(tabela_com_totais, altura=altura_tabela, coluna_dados=coluna_dados)
    except Exception as e:
        st.error(f"Erro ao exibir tabela no AgGrid: {str(e)}")
        st.dataframe(tabela_com_totais, height=altura_tabela)

    col1, col2 = st.columns(2)
    with col1:
        try:
            csv_data = converter_df_para_csv(tabela_dados)
            st.download_button(
                label=ROTULO_BTN_DOWNLOAD_CSV,
                data=csv_data,
                file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{ano_selecionado}.csv',
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
                file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{ano_selecionado}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        except Exception as e:
            st.error(f"Erro ao preparar Excel para download: {str(e)}")

with tab2:
    if coluna_dados in tabela_dados.columns:
        col1, col2 = st.columns(2)

        with col1:
            try:
                try:
                    total_valor = formatar_numero(tabela_dados[coluna_dados].sum())
                except:
                    total_valor = "-"
                try:
                    media_valor = formatar_numero(tabela_dados[coluna_dados].mean())
                except:
                    media_valor = "-"
                try:
                    mediana_valor = formatar_numero(tabela_dados[coluna_dados].median())
                except:
                    mediana_valor = "-"
                try:
                    min_valor = formatar_numero(tabela_dados[coluna_dados].min())
                except:
                    min_valor = "-"
                try:
                    max_valor = formatar_numero(tabela_dados[coluna_dados].max())
                except:
                    max_valor = "-"
                try:
                    std_valor = formatar_numero(tabela_dados[coluna_dados].std())
                except:
                    std_valor = "-"

                resumo = pd.DataFrame({
                    'Métrica': ['Total', 'Média', 'Mediana', 'Mínimo', 'Máximo', 'Desvio Padrão'],
                    'Valor': [total_valor, media_valor, mediana_valor, min_valor, max_valor, std_valor]
                })

                st.write("### Resumo Estatístico")
                resumo_estilizado = resumo.style.set_properties(**{'text-align': 'center'}) \
                    .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
                st.dataframe(resumo_estilizado, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Erro ao calcular estatísticas: {str(e)}")
                st.write("Não foi possível calcular as estatísticas para os dados atuais.")

        with col2:
            try:
                st.write("### Top 5 Valores")
                if len(tabela_dados) > 0:
                    try:
                        top5 = tabela_dados.nlargest(min(5, len(tabela_dados)), coluna_dados)

                        colunas_exibir = []
                        if tipo_visualizacao == "Escola" and "NOME DA ESCOLA" in top5.columns:
                            colunas_exibir.append("NOME DA ESCOLA")
                        elif tipo_visualizacao == "Município" and "NOME DO MUNICIPIO" in top5.columns:
                            colunas_exibir.append("NOME DO MUNICIPIO")
                        elif "NOME DA UF" in top5.columns:
                            colunas_exibir.append("NOME DA UF")

                        if "DEPENDENCIA ADMINISTRATIVA" in top5.columns:
                            colunas_exibir.append("DEPENDENCIA ADMINISTRATIVA")

                        if coluna_dados in top5.columns:
                            colunas_exibir.append(coluna_dados)

                        if '% do Total' in top5.columns:
                            colunas_exibir.append('% do Total')

                        colunas_exibir = [c for c in colunas_exibir if c in top5.columns]

                        if colunas_exibir:
                            top5_exibir = top5[colunas_exibir].copy()

                            if coluna_dados in top5_exibir.columns:
                                top5_exibir[coluna_dados] = top5_exibir[coluna_dados].apply(
                                    lambda x: formatar_numero(x) if pd.notnull(x) else "-"
                                )

                            if '% do Total' in top5_exibir.columns:
                                top5_exibir['% do Total'] = top5_exibir['% do Total'].apply(
                                    lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
                                )

                            top5_estilizado = top5_exibir.style.set_properties(**{'text-align': 'center'}) \
                                .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
                            st.dataframe(top5_estilizado, use_container_width=True, hide_index=True)
                        else:
                            st.info(INFO_SEM_COLUNAS_TOP5)
                    except Exception as e:
                        st.error(ERRO_CALCULAR_TOP5.format(str(e)))
                        st.info(INFO_NAO_CALCULADO_TOP5)
                else:
                    st.info(INFO_SEM_DADOS_TOP5)
            except Exception as e:
                st.error(f"Erro ao processar top 5: {str(e)}")
    else:
        st.warning(AVISO_COLUNA_NAO_DISPONIVEL.format(coluna_dados))

# -------------------------------
# Rodapé do Dashboard
# -------------------------------
st.markdown("---")
st.markdown(RODAPE_NOTA)