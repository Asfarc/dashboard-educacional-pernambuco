import pandas as pd
from utils.formatacao import formatar_numero


def preparar_tabela_para_exibicao(df_base, colunas_para_exibir, coluna_ordenacao):
    """
    Ordena o DataFrame base pela coluna_ordenacao (se existir), cria uma cópia
    e formata as colunas numéricas e percentuais para exibição.

    Parâmetros:
    df_base (DataFrame): DataFrame a ser processado
    colunas_para_exibir (list): Lista de colunas que devem ser exibidas
    coluna_ordenacao (str): Nome da coluna a ser usada para ordenação

    Retorna:
    (DataFrame, DataFrame): Tupla com (tabela_dados, tabela_exibicao)
        tabela_dados: DataFrame com os dados originais (valores numéricos preservados)
        tabela_exibicao: DataFrame formatado para exibição (valores formatados como texto)
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


def calcular_estatisticas(df, coluna_dados):
    """
    Calcula estatísticas descritivas para uma coluna de dados.

    Parâmetros:
    df (DataFrame): DataFrame com os dados
    coluna_dados (str): Nome da coluna para calcular estatísticas

    Retorna:
    DataFrame: DataFrame com as estatísticas calculadas
    """
    if coluna_dados not in df.columns or df.empty:
        # Criar DataFrame vazio com estrutura adequada
        return pd.DataFrame({
            'Métrica': ['Total', 'Média', 'Mediana', 'Mínimo', 'Máximo', 'Desvio Padrão'],
            'Valor': ["-", "-", "-", "-", "-", "-"]
        })

    try:
        total_valor = formatar_numero(df[coluna_dados].sum())
    except:
        total_valor = "-"
    try:
        media_valor = formatar_numero(df[coluna_dados].mean())
    except:
        media_valor = "-"
    try:
        mediana_valor = formatar_numero(df[coluna_dados].median())
    except:
        mediana_valor = "-"
    try:
        min_valor = formatar_numero(df[coluna_dados].min())
    except:
        min_valor = "-"
    try:
        max_valor = formatar_numero(df[coluna_dados].max())
    except:
        max_valor = "-"
    try:
        std_valor = formatar_numero(df[coluna_dados].std())
    except:
        std_valor = "-"

    # Criar DataFrame com as estatísticas
    return pd.DataFrame({
        'Métrica': ['Total', 'Média', 'Mediana', 'Mínimo', 'Máximo', 'Desvio Padrão'],
        'Valor': [total_valor, media_valor, mediana_valor, min_valor, max_valor, std_valor]
    })


def obter_top_valores(df, coluna_dados, n=5, tipo_visualizacao=""):
    """
    Obtém os N maiores valores de uma coluna no DataFrame.

    Parâmetros:
    df (DataFrame): DataFrame com os dados
    coluna_dados (str): Nome da coluna para ordenar e filtrar
    n (int): Número de registros a retornar (padrão=5)
    tipo_visualizacao (str): Tipo de visualização ("Escola", "Município" ou "Estado")

    Retorna:
    DataFrame: DataFrame com os top N valores
    """
    if coluna_dados not in df.columns or df.empty:
        return pd.DataFrame()

    # Obter os N maiores valores
    top_df = df.nlargest(min(n, len(df)), coluna_dados)

    # Selecionar colunas relevantes com base no tipo de visualização
    colunas_exibir = []

    if tipo_visualizacao == "Escola" and "NOME DA ESCOLA" in top_df.columns:
        colunas_exibir.append("NOME DA ESCOLA")
    elif tipo_visualizacao == "Município" and "NOME DO MUNICIPIO" in top_df.columns:
        colunas_exibir.append("NOME DO MUNICIPIO")
    elif "NOME DA UF" in top_df.columns:
        colunas_exibir.append("NOME DA UF")

    if "DEPENDENCIA ADMINISTRATIVA" in top_df.columns:
        colunas_exibir.append("DEPENDENCIA ADMINISTRATIVA")

    if coluna_dados in top_df.columns:
        colunas_exibir.append(coluna_dados)

    if '% do Total' in top_df.columns:
        colunas_exibir.append('% do Total')

    # Filtrar apenas colunas que existem
    colunas_exibir = [c for c in colunas_exibir if c in top_df.columns]

    if not colunas_exibir:
        return pd.DataFrame()

    # Criar cópia com as colunas selecionadas
    top_df_exibir = top_df[colunas_exibir].copy()


    # Formatar valores para exibição
    if coluna_dados in top_df_exibir.columns:
        top_df_exibir[coluna_dados] = top_df_exibir[coluna_dados].apply(
            lambda x: formatar_numero(x) if pd.notnull(x) else "-"
        )

    if '% do Total' in top_df_exibir.columns:
        top_df_exibir['% do Total'] = top_df_exibir['% do Total'].apply(
            lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
        )

    return top_df_exibir


# Controla o que é exportado pelo módulo
__all__ = ['preparar_tabela_para_exibicao', 'calcular_estatisticas', 'obter_top_valores']