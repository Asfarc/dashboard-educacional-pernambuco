import altair as alt

# Configuração ESSENCIAL para formato numérico brasileiro
alt.renderers.set_embed_options({
    'formatLocale': {
        'decimal': ',',
        'thousands': '.',
        'grouping': [3],
        'currency': ['R$', '']
    },
    'timeFormatLocale': 'pt_BR'  # Opcional para datas em português
})

# Dicionário que centraliza parâmetros estilísticos e facilita ajustes # dee2e6
PARAMETROS_ESTILO_CONTAINER = {
    "raio_borda": 8,
    "cor_borda": "#dee2e6",
    "cor_titulo": "#dee2e6",
    "tamanho_fonte_titulo": "1.2rem",  # Aumentei para 19.2px
    "tamanho_fonte_conteudo": "1.05rem", # 16.8px (sutilmente maior)
    "cor_fonte_conteudo": "#364b60"
}

def obter_estilo_css_container(params=None) -> str:
    if params is None:
        params = PARAMETROS_ESTILO_CONTAINER

    return f"""
    <style>
    /* 1. Container Pai - Apenas Espaçamento */
    .container-custom {{
        padding: 1rem !important;
        margin-bottom: 1rem !important;
        background: transparent !important;
    }}

    /* 2. Tabela - Borda Externa */
    .custom-table {{
        border: 1px solid {params["cor_borda"]} !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        border-collapse: separate !important;
    }}

    /* 3. Largura das Colunas  */
    .custom-table col:nth-child(1) {{ width: 30%; }}  /* Coluna do ícone + label */
    .custom-table col:nth-child(2) {{ width: 15%; }}  /* Federal */
    .custom-table col:nth-child(3) {{ width: 15%; }}  /* Estaduais */
    .custom-table col:nth-child(4) {{ width: 15%; }}  /* Municipais */
    .custom-table col:nth-child(5) {{ width: 15%; }}  /* Privadas */
    .custom-table col:nth-child(6) {{ width: 10%; }}  /* Total */

    /* 4. Tamanho da Fonte  */
    .container-title {{
        font-size: {params["tamanho_fonte_titulo"]} !important;  /* Deve ser 1.2rem */
        color: {params["cor_titulo"]} !important;
    }}

    .container-text {{
        font-size: {params["tamanho_fonte_conteudo"]} !important;  /* Deve ser 1.05rem */
        color: {params["cor_fonte_conteudo"]} !important;
    }}

    /* 5. Tamanho dos Ícones  */
    .icone {{
        width: 50px !important;
        height: 50px !important;
        vertical-align: middle !important;
        margin-right: 6px !important;
    }}

    /* 6. Linha de Matrículas - A partir da coluna Federal */
    .custom-table tbody tr:nth-child(2) td:nth-child(n+2) {{
        border-top: 1px solid {params["cor_borda"]} !important;
        border-bottom: 1px solid {params["cor_borda"]} !important;
    }}

    /* 7. Remove Bordas Internas */
    .custom-table td,
    .custom-table th {{
        border: none !important;
        background: transparent !important;
    }}

    /* 8. Remove Borda do Cabeçalho */
    .custom-table thead tr {{
        border-bottom: none !important;
        box-shadow: none !important;
    }}
    </style>
    """

# Importando pandas para acesso à função isna
import pandas as pd


# Função para formatar números com padrão brasileiro
def aplicar_padrao_numerico_brasileiro(numero):
    """
    Formata números grandes adicionando separadores de milhar em padrão BR:
    Ex.: 1234567 -> '1.234.567'
         1234.56 -> '1.234,56'
    Se o número for NaN ou '-', retorna '-'.
    Aplica formatação apenas a valores numéricos.

    Parâmetros:
        numero: O número a ser formatado

    Retorna:
        String formatada com o padrão brasileiro de números
    """
    if pd.isna(numero) or numero == "-":
        return "-"

    try:
        float_numero = float(numero)
        if float_numero.is_integer():
            return f"{int(float_numero):,}".replace(",", ".")
        else:
            parte_inteira = int(float_numero)
            parte_decimal = abs(float_numero - parte_inteira)
            inteiro_fmt = f"{parte_inteira:,}".replace(",", ".")
            decimal_fmt = f"{parte_decimal:.2f}".replace("0.", "").replace(".", ",")
            return f"{inteiro_fmt},{decimal_fmt}"
    except (ValueError, TypeError):
        return str(numero)

# Mantemos a função anterior por compatibilidade, mas usando a nova implementação
def formatar_numero_com_pontos_milhar(numero: float) -> str:
    """
    Função compatível com o código existente que usa a implementação de
    aplicar_padrao_numerico_brasileiro.
    """
    return aplicar_padrao_numerico_brasileiro(numero)

# Função modificada com controle de tamanho de texto
def construir_grafico_linha_evolucao(
    df_transformado,
    largura=450,
    altura=300,
    espessura_linha=5,
    tamanho_ponto=100,
    tamanho_texto_eixo=16,
    tamanho_texto_legenda=16,
    tamanho_titulo_eixo=18,
    tamanho_titulo_legenda=18
):
    # Antes de criar o gráfico, faça:
    df_transformado['Valor'] = df_transformado['Valor'].astype(float)
    # Configurações de estilo
    fonte = "Arial"
    cor_grafico = "#364b60"

    # Mantém as cores das categorias
    cores_categorias = {
        'Escolas': '#364b60',
        'Matrículas': '#cccccc',
        'Professores': '#a3b8cb'
    }

    # Criação do gráfico com parâmetros ajustáveis
    grafico = alt.Chart(df_transformado).mark_line(
        strokeWidth=espessura_linha,
        point={"filled": True, "size": tamanho_ponto}
    ).encode(
        x=alt.X('Ano:O',
                axis=alt.Axis(
                    #values=[2015, 2020, 2023],
                    title="Ano",
                    labelFontSize=tamanho_texto_eixo,          # Usa novo parâmetro
                    titleFontSize=tamanho_titulo_eixo,         # Usa novo parâmetro
                    titleFont=fonte,
                    labelFont=fonte,
                    labelAngle=0
                )),
        y=alt.Y('Valor:Q',
                axis=alt.Axis(
                    title="Quantidade",
                    labelFontSize=tamanho_texto_eixo,          # Usa novo parâmetro
                    titleFontSize=tamanho_titulo_eixo,          # Usa novo parâmetro
                    titleFont=fonte,
                    labelFont=fonte,
                    format='.0f',
                    labelExpr="replace(format(datum.value, '.0f'), ',', '.')"
                )),
        color=alt.Color('Categoria:N',
                        legend=alt.Legend(
                            title="",
                            titleFontSize=tamanho_titulo_legenda,  # Usa novo parâmetro
                            labelFontSize=tamanho_texto_legenda,   # Usa novo parâmetro
                            titleFont=fonte,
                            labelFont=fonte,
                            orient='top',
                            titleAnchor='middle'
                        ),
                        scale=alt.Scale(
                            domain=list(cores_categorias.keys()),
                            range=list(cores_categorias.values())
                        ))
    ).properties(
        width=largura,
        height=altura
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        gridColor='#f0f0f0',
        domainColor=cor_grafico,
        titleColor=cor_grafico,
        labelColor=cor_grafico
    )

    return grafico