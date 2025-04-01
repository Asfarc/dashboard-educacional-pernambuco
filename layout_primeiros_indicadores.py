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

# -----------------------------------------------------
# Dicionário Central de Configurações (ATUALIZADO)
# -----------------------------------------------------
PARAMETROS_ESTILO_CONTAINER = {
    "raio_borda": 8,
    "cor_borda": "#dee2e6",
    "cor_titulo": "#364b60",
    "tamanho_fonte_titulo": "1.1rem",
    "tamanho_fonte_conteudo": "1rem",
    "cor_fonte_conteudo": "#364b60",
    "largura_colunas": [30, 14, 14, 14, 14, 14]  # Novo: porcentagens das colunas
}

CONFIG_GRAFICO = {
    # Dimensões
    "largura": 680,
    "altura": 280,

    # Estilo da Linha
    "espessura_linha": 5,
    "tamanho_ponto": 100,
    "raio_borda": PARAMETROS_ESTILO_CONTAINER["raio_borda"],

    # Texto
    "tamanho_texto_eixo": 14,
    "tamanho_texto_legenda": 16,
    "tamanho_titulo_eixo": 14,
    "tamanho_titulo_legenda": 18,
    "fonte": "Arial",

    # Cores
    "cor_fundo": "#ffffff",
    "cor_grade": "#f0f0f0",
    "cor_borda": PARAMETROS_ESTILO_CONTAINER["cor_borda"],
    "cores_categorias": {
        'Escolas': '#364b60',
        'Matrículas': '#cccccc',
        'Professores': '#a3b8cb'
    }

}
def obter_estilo_css_container(params=None) -> str:
    if params is None:
        params = PARAMETROS_ESTILO_CONTAINER

    return f"""
    <style>
    /* 1. Container Pai - Apenas Espaçamento */
    .container-custom {{
        padding: 0rem !important;
        margin-bottom: 0rem !important;
        background: transparent !important;
    }}

    /* 2. Tabela - Borda Externa */
    .custom-table {{
        border: 1px solid {params["cor_borda"]} !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        border-collapse: separate !important;
        table-layout: fixed !important;
        width: 100% !important;
        font-size: {params["tamanho_fonte_conteudo"]} !important;  /* Novo */
    }}

    /* 3. Largura das Colunas Ajustada */
    .custom-table colgroup col:nth-child(1) {{ width: 30% !important; }}  /* Reduzido de 35% */
    .custom-table colgroup col:nth-child(2) {{ width: 14% !important; }}  /* Federal */
    .custom-table colgroup col:nth-child(3) {{ width: 14% !important; }}  /* Estaduais */
    .custom-table colgroup col:nth-child(4) {{ width: 14% !important; }}  /* Municipais */
    .custom-table colgroup col:nth-child(5) {{ width: 14% !important; }}  /* Privadas */
    .custom-table colgroup col:nth-child(6) {{ width: 14% !important; }}  /* Aumentado de 10% */
    
    /* Espaçamento interno das células */
    .custom-table td, .custom-table th {{
        padding: 8px 10px !important;  /* Reduz padding vertical */
        white-space: nowrap !important;  /* Evita quebra de linha */
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}

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
    .vega-embed {{
    border: 1px solid #dee2e6 !important;
    border-radius: 8px !important;
    padding: 12px !important;
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
def construir_grafico_linha_evolucao(df_transformado, **kwargs):
    config = {**CONFIG_GRAFICO, **kwargs}

    # Pré-processamento
    df = df_transformado.copy()
    df['Valor'] = df['Valor'].astype(float)

    # Construção do gráfico
    grafico = alt.Chart(df).mark_line(
        strokeWidth=config['espessura_linha'],
        point=alt.OverlayMarkDef(
            size=config['tamanho_ponto'],
            filled=True,
            color='white',
            stroke=CONFIG_GRAFICO['cores_categorias']['Escolas']
        )
    ).encode(
        x=alt.X('Ano:O',
                axis=alt.Axis(
                    title="Ano",
                    labelFontSize=config['tamanho_texto_eixo'],
                    titleFontSize=config['tamanho_titulo_eixo'],
                    titleFont=config['fonte'],
                    labelFont=config['fonte']
                )),
        y=alt.Y('Valor:Q',
                axis=alt.Axis(
                    title="Quantidade",
                    labelFontSize=config['tamanho_texto_eixo'],
                    titleFontSize=config['tamanho_titulo_eixo'],
                    titleFont=config['fonte'],
                    labelFont=config['fonte'],
                    format='.0f'
                )),
        color=alt.Color('Categoria:N',
                        legend=alt.Legend(
                            title=None,
                            labelFontSize=config['tamanho_texto_legenda'],
                            titleFontSize=config['tamanho_titulo_legenda'],
                            labelFont=config['fonte'],
                            orient='top'
                        ),
                        scale=alt.Scale(
                            domain=list(config['cores_categorias'].keys()),
                            range=list(config['cores_categorias'].values())
                        )
                        )  # <-- Fechamento do color
    ).properties(
        width=config['largura'],
        height=config['altura']
    ).configure_view(
        strokeWidth=0,  # Espessura da borda
        stroke=config['cor_borda'],  # Cor da borda
        cornerRadius=config['raio_borda'],  # Arredondamento
        fill=config['cor_fundo']
    ).configure_axis(
        gridColor=config['cor_grade'],
        domainColor=config['cores_categorias']['Escolas'],
        titleColor=config['cores_categorias']['Escolas'],
        labelColor=config['cores_categorias']['Escolas']
    )

    return grafico