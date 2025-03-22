import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from componentes.aggrid.js_code import js_total_row, get_agg_functions_js, percent_formatter
from componentes.aggrid.locale_pt_br import locale_pt_br
from constantes import (
    ROTULO_BTN_PRIMEIRA_LINHA, ROTULO_BTN_ULTIMA_LINHA, DICAS_NAVEGACAO,
    INFO_FILTRO_APLICADO, AVISO_SEM_DADOS_TABELA
)
from utils.formatacao import formatar_numero
from componentes.navegacao import navegar_tabela


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

    # Configurar o construtor de opções do grid
    gb = GridOptionsBuilder.from_dataframe(df_para_exibir)



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

    # Adicionar barra de pesquisa rápida e estilo para linha de totais
    gb.configure_grid_options(
        enableQuickFilter=True,
        quickFilterText="",
        getRowStyle=js_total_row,
        suppressCellFocus=False,
        alwaysShowVerticalScroll=True,
        localeText=locale_pt_br,
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

        # Verificar se coluna de percentual existe
        if '% do Total' in df_para_exibir.columns:
            gb.configure_column(
                '% do Total',
                type=["numericColumn", "numberColumnFilter"],
                filter="agNumberColumnFilter",
                valueFormatter=percent_formatter,
                aggFunc="avg",
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
    # Gerar o código JS com a coluna correta
    js_agg_functions = get_agg_functions_js(coluna_dados)
    # Usar a variável normalmente na configuração
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


# Controla o que é exportado pelo módulo
__all__ = ['adicionar_linha_totais', 'exibir_tabela_com_aggrid']