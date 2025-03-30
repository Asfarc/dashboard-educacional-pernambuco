import streamlit as st
import pandas as pd
import numpy as np
import random

# Configuração da página
st.set_page_config(
    page_title="Dashboard Educacional de Pernambuco",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Função para gerar dados simulados
def gerar_dados_simulados():
    # Lista de municípios de Pernambuco
    municipios = [
        "Recife", "Jaboatão dos Guararapes", "Olinda", "Caruaru", "Petrolina",
        "Paulista", "Cabo de Santo Agostinho", "Camaragibe", "Garanhuns",
        "Vitória de Santo Antão", "Igarassu", "São Lourenço da Mata",
        "Abreu e Lima", "Ipojuca", "Santa Cruz do Capibaribe", "Araripina",
        "Serra Talhada", "Gravatá", "Carpina", "Goiana", "Belo Jardim",
        "Arcoverde", "Pesqueira", "Surubim", "Escada", "Bezerros", "Timbaúba",
        "Palmares", "Moreno", "Ouricuri", "Barreiros", "Salgueiro", "Nazaré da Mata",
        "Limoeiro", "Recife Norte", "Recife Sul", "Recife Leste", "Recife Oeste"
    ]

    # Gerar códigos aleatórios para municípios
    codigos_municipios = {municipio: random.randint(2600000, 2699999) for municipio in municipios}

    # Criar lista para armazenar os dados
    dados = []

    # Dependências administrativas
    dependencias = ["Federal", "Estadual", "Municipal", "Privada"]

    # Gerar dados para cada ano, município e dependência
    for ano in range(2020, 2026):
        for municipio in municipios:
            for dependencia in dependencias:
                # Gerar número de matrículas aleatório
                matriculas = random.randint(100, 10000)

                # Adicionar linha ao conjunto de dados
                dados.append({
                    "Ano": ano,
                    "Município": municipio,
                    "Código do Município": codigos_municipios[municipio],
                    "Dependência Administrativa": dependencia,
                    "Número de Matrículas": matriculas
                })

    return pd.DataFrame(dados)


# Carregar ou gerar dados
@st.cache_data
def carregar_dados():
    # Aqui você poderia carregar dados reais de um arquivo
    # Como estamos usando dados simulados, vamos apenas gerar:
    return gerar_dados_simulados()


df = carregar_dados()

# Título do dashboard com estilo melhorado
st.markdown("""
<style>
.dashboard-title {
    color: #1e3a8a;
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 5px;
    padding-bottom: 0;
}
.dashboard-subtitle {
    color: #64748b;
    font-size: 16px;
    margin-top: 0;
    padding-top: 0;
    margin-bottom: 25px;
}
.divider {
    height: 3px;
    background-image: linear-gradient(to right, #4c8bf5, #e9ecef);
    margin: 1rem 0;
    border-radius: 2px;
}
</style>

<div class="dashboard-title">📊 Dashboard Educacional de Pernambuco</div>
<div class="dashboard-subtitle">Análise de matrículas na educação básica (2020-2025)</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# Container para filtros
with st.container():
    st.subheader("Filtros")

    # Adicionando um estilo visual mais profissional para os filtros
    st.markdown("""
    <style>
    .filter-section {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
    }
    .filter-header {
        font-weight: 600;
        margin-bottom: 10px;
        color: #495057;
    }
    .icon-filter {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        margin-right: 4px;
        cursor: pointer;
        font-size: 14px;
    }
    .icon-filters-container {
        display: flex;
        gap: 2px;
        align-items: center;
    }
    .compact-number-input {
        padding: 0 !important;
        margin: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Layout de colunas para os filtros principais
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="filter-header">Período:</div>', unsafe_allow_html=True)
        # Filtro para Ano
        anos_unicos = sorted(df["Ano"].unique())
        anos_selecionados = st.multiselect("", anos_unicos, default=anos_unicos, label_visibility="collapsed")

    with col2:
        st.markdown('<div class="filter-header">Dependência Administrativa:</div>', unsafe_allow_html=True)
        # Filtro para Dependência Administrativa
        dependencias_unicas = sorted(df["Dependência Administrativa"].unique())
        dependencias_selecionadas = st.multiselect("", dependencias_unicas, default=dependencias_unicas,
                                                   label_visibility="collapsed")

    st.markdown('</div>', unsafe_allow_html=True)

# Inicializar a sessão se não existir
if 'filtro_matriculas_tipo' not in st.session_state:
    st.session_state.filtro_matriculas_tipo = "Sem filtro"

# Aplicar filtros ao dataframe
df_filtrado = df.copy()

# Filtrar por Ano
if anos_selecionados:
    df_filtrado = df_filtrado[df_filtrado["Ano"].isin(anos_selecionados)]

# Filtrar por Dependência Administrativa
if dependencias_selecionadas:
    df_filtrado = df_filtrado[df_filtrado["Dependência Administrativa"].isin(dependencias_selecionadas)]

# Exibir resumo dos dados filtrados
st.markdown("""
<style>
.metrics-container {
    background-color: white;
    border-radius: 10px;
    padding: 15px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.metrics-header {
    font-weight: 600;
    margin-bottom: 15px;
    color: #1e3a8a;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
st.markdown('<div class="metrics-header">Resumo dos Dados</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total de Municípios", df_filtrado["Município"].nunique())

with col2:
    st.metric("Total de Matrículas", f"{df_filtrado['Número de Matrículas'].sum():,}".replace(",", "."))

with col3:
    st.metric("Média de Matrículas",
              f"{int(df_filtrado['Número de Matrículas'].mean()):,}".replace(",", "."))

st.markdown('</div>', unsafe_allow_html=True)

# Tabela de Dados Detalhada com filtros nas colunas
st.markdown("""
<style>
.table-container {
    background-color: white;
    border-radius: 10px;
    padding: 15px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.table-header {
    font-weight: 600;
    margin-bottom: 15px;
    color: #1e3a8a;
    font-size: 18px;
}
.filter-input {
    margin-top: 10px;
    margin-bottom: 10px;
}
.info-text {
    color: #4c8bf5;
    font-size: 14px;
    margin-top: 10px;
    padding: 8px;
    background-color: #f0f7ff;
    border-radius: 5px;
    border-left: 3px solid #4c8bf5;
}
.warning-text {
    color: #dc3545;
    font-size: 14px;
    margin-top: 10px;
    padding: 8px;
    background-color: #fff5f5;
    border-radius: 5px;
    border-left: 3px solid #dc3545;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="table-container">', unsafe_allow_html=True)
st.markdown('<div class="table-header">Tabela de Dados Detalhada</div>', unsafe_allow_html=True)

# Reset do índice para não mostrar a primeira coluna de identificação
df_filtrado = df_filtrado.reset_index(drop=True)

# Adicionando filtros individuais para cada coluna
col_filters = {}
cols = st.columns(len(df_filtrado.columns))

# Adiciona um input de texto para cada coluna
for i, col_name in enumerate(df_filtrado.columns):
    with cols[i]:
        # Para a coluna de Número de Matrículas, adicionamos apenas os ícones de filtro
        if col_name == "Número de Matrículas":
            st.markdown(f"**{col_name}**")

            # Linha com ícones para filtros em uma única linha com os campos de entrada
            icones_col = st.container()
            with icones_col:
                c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1, 1, 1, 1, 1, 5])

                with c1:
                    if st.button("🚫",
                                 key="btn_sem_filtro",
                                 help="Remover filtros",
                                 type="primary" if st.session_state.filtro_matriculas_tipo == "Sem filtro" else "secondary"):
                        st.session_state.filtro_matriculas_tipo = "Sem filtro"
                        st.rerun()

                with c2:
                    if st.button("↗️",
                                 key="btn_acima",
                                 help="Mostrar valores acima de um limite",
                                 type="primary" if st.session_state.filtro_matriculas_tipo == "Acima de" else "secondary"):
                        st.session_state.filtro_matriculas_tipo = "Acima de"
                        st.rerun()

                with c3:
                    if st.button("↘️",
                                 key="btn_abaixo",
                                 help="Mostrar valores abaixo de um limite",
                                 type="primary" if st.session_state.filtro_matriculas_tipo == "Abaixo de" else "secondary"):
                        st.session_state.filtro_matriculas_tipo = "Abaixo de"
                        st.rerun()

                with c4:
                    if st.button("↔️",
                                 key="btn_entre",
                                 help="Mostrar valores entre dois limites",
                                 type="primary" if st.session_state.filtro_matriculas_tipo == "Entre" else "secondary"):
                        st.session_state.filtro_matriculas_tipo = "Entre"
                        st.rerun()

                with c5:
                    if st.button("🔝",
                                 key="btn_top",
                                 help="Mostrar os maiores valores",
                                 type="primary" if st.session_state.filtro_matriculas_tipo == "Top maiores" else "secondary"):
                        st.session_state.filtro_matriculas_tipo = "Top maiores"
                        st.rerun()

                with c6:
                    if st.button("↙️",  # Ícone para menores valores
                                 key="btn_bottom",
                                 help="Mostrar os menores valores",
                                 type="primary" if st.session_state.filtro_matriculas_tipo == "Top menores" else "secondary"):
                        st.session_state.filtro_matriculas_tipo = "Top menores"
                        st.rerun()

                with c7:
                    # Campo para o valor do filtro na mesma linha
                    if st.session_state.filtro_matriculas_tipo == "Acima de":
                        valor_min = st.number_input("",
                                                    min_value=0,
                                                    max_value=int(df["Número de Matrículas"].max()),
                                                    value=1000,
                                                    label_visibility="collapsed")
                        valor_max = None
                        top_n = None

                    elif st.session_state.filtro_matriculas_tipo == "Abaixo de":
                        valor_max = st.number_input("",
                                                    min_value=0,
                                                    max_value=int(df["Número de Matrículas"].max()),
                                                    value=5000,
                                                    label_visibility="collapsed")
                        valor_min = None
                        top_n = None

                    elif st.session_state.filtro_matriculas_tipo == "Entre":
                        st.markdown("**Min:**")
                        valor_min = st.number_input("Min",
                                                    min_value=0,
                                                    max_value=int(df["Número de Matrículas"].max()),
                                                    value=1000,
                                                    label_visibility="collapsed")
                        st.markdown("**Max:**")
                        valor_max = st.number_input("Max",
                                                    min_value=0,
                                                    max_value=int(df["Número de Matrículas"].max()),
                                                    value=5000,
                                                    label_visibility="collapsed")
                        top_n = None

                    elif st.session_state.filtro_matriculas_tipo == "Top maiores" or st.session_state.filtro_matriculas_tipo == "Top menores":
                        top_n = st.number_input("",
                                                min_value=1,
                                                max_value=100,
                                                value=10,
                                                label_visibility="collapsed")
                        valor_min = None
                        valor_max = None

                    else:
                        valor_min = None
                        valor_max = None
                        top_n = None

            # Não adicionamos o campo de texto padrão para esta coluna
            col_filters[col_name] = ""
        else:
            # Para as outras colunas, mantemos o filtro de texto normal
            st.markdown(f"**{col_name}**")
            col_filters[col_name] = st.text_input("",
                                                  key=f"filter_{col_name}",
                                                  label_visibility="collapsed",
                                                  placeholder=f"Filtrar {col_name}...")

# Aplicar filtros avançados para Número de Matrículas
if 'filtro_matriculas_tipo' in st.session_state:
    tipo_filtro = st.session_state.filtro_matriculas_tipo

    if tipo_filtro == "Acima de" and valor_min is not None:
        df_filtrado = df_filtrado[df_filtrado["Número de Matrículas"] > valor_min]

    elif tipo_filtro == "Abaixo de" and valor_max is not None:
        df_filtrado = df_filtrado[df_filtrado["Número de Matrículas"] < valor_max]

    elif tipo_filtro == "Entre" and valor_min is not None and valor_max is not None:
        df_filtrado = df_filtrado[(df_filtrado["Número de Matrículas"] >= valor_min) &
                                  (df_filtrado["Número de Matrículas"] <= valor_max)]

    elif tipo_filtro == "Top maiores" and top_n is not None:
        df_temp = df_filtrado.copy()
        df_temp = df_temp.sort_values(by="Número de Matrículas", ascending=False)
        top_indices = df_temp.head(top_n).index
        df_filtrado = df_filtrado.loc[top_indices]

    elif tipo_filtro == "Top menores" and top_n is not None:
        df_temp = df_filtrado.copy()
        df_temp = df_temp.sort_values(by="Número de Matrículas", ascending=True)
        top_indices = df_temp.head(top_n).index
        df_filtrado = df_filtrado.loc[top_indices]

# Aplicar os filtros de texto das colunas ao dataframe
df_col_filtrado = df_filtrado.copy()
for col_name, filter_text in col_filters.items():
    if filter_text:
        df_col_filtrado = df_col_filtrado[df_col_filtrado[col_name].astype(str).str.contains(filter_text, case=False)]

# Exibir a tabela filtrada
if len(df_col_filtrado) > 0:
    st.dataframe(df_col_filtrado, use_container_width=True, hide_index=True)
    st.markdown(f'<div class="info-text">📊 Exibindo {len(df_col_filtrado)} de {len(df_filtrado)} registros.</div>',
                unsafe_allow_html=True)
else:
    st.markdown('<div class="warning-text">⚠️ Nenhum registro encontrado com os filtros aplicados.</div>',
                unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Rodapé com informações adicionais
st.markdown("""
<style>
.footer {
    text-align: center;
    margin-top: 30px;
    padding-top: 10px;
    border-top: 1px solid #e9ecef;
    color: #6c757d;
    font-size: 12px;
}
</style>
<div class="footer">
    Dashboard criado com Streamlit para análise de dados educacionais de Pernambuco (2020-2025)
    <br>Última atualização: Março/2025
</div>
""", unsafe_allow_html=True)