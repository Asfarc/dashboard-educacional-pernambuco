import pandas as pd
import os
import textwrap


def analisar_excel(caminho_arquivo, linha_cabecalho):
    """
    Analisa uma planilha Excel e gera um relatório detalhado sobre sua estrutura.

    Args:
        caminho_arquivo (str): Caminho para o arquivo Excel
        linha_cabecalho (int): Número da linha que contém os cabeçalhos (0-indexed)

    Returns:
        None: O resultado é impresso no console
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(caminho_arquivo):
            print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
            return

        # Verificar a extensão do arquivo
        if not (caminho_arquivo.endswith('.xlsx') or caminho_arquivo.endswith('.xls')):
            print(f"Aviso: O arquivo '{caminho_arquivo}' pode não ser um arquivo Excel válido.")

        # Carregar os dados do Excel
        df = pd.read_excel(caminho_arquivo, header=linha_cabecalho)

        # Gerar relatório
        print("\n" + "=" * 80)
        print(f"RELATÓRIO DE ANÁLISE: {os.path.basename(caminho_arquivo)}")
        print("=" * 80)

        # Dimensões
        total_linhas, total_colunas = df.shape
        print(f"\nDIMENSÕES DA PLANILHA:")
        print(f"Total de linhas: {total_linhas}")
        print(f"Total de colunas: {total_colunas}")

        # Informações das colunas
        print("\nINFORMAÇÕES DAS COLUNAS:")
        print(f"{'POSIÇÃO':<10}{'NOME':<30}{'TIPO':<15}{'VALORES ÚNICOS':<15}{'EXEMPLOS DE VALORES (até 6)'}")
        print("-" * 80)

        for i, coluna in enumerate(df.columns):
            valores_unicos = df[coluna].nunique()
            tipo_dados = str(df[coluna].dtype)

            # Obter valores únicos se forem 6 ou menos
            exemplos = ""
            if valores_unicos <= 6 and valores_unicos > 0:
                valores_lista = df[coluna].dropna().unique()
                # Limitar o tamanho de cada valor para exibição
                valores_formatados = [str(val)[:20] + "..." if len(str(val)) > 20 else str(val) for val in
                                      valores_lista]
                exemplos = ", ".join(valores_formatados)

            print(f"{i:<10}{coluna[:28]:<30}{tipo_dados:<15}{valores_unicos:<15}{exemplos}")

        # Verificar valores nulos
        total_nulos = df.isna().sum().sum()
        if total_nulos > 0:
            print("\nVALORES AUSENTES:")
            for coluna in df.columns:
                nulos_coluna = df[coluna].isna().sum()
                if nulos_coluna > 0:
                    percentual = (nulos_coluna / total_linhas) * 100
                    print(f"{coluna}: {nulos_coluna} valores ausentes ({percentual:.2f}%)")

        # Mostrar primeiras e últimas linhas
        print("\nEXEMPLOS DE DADOS:")
        print("-" * 80)

        # Definir quantas linhas mostrar
        n_linhas = 3

        # Mostrar primeiras linhas
        print(f"\nPRIMEIRAS {n_linhas} LINHAS:")
        primeiras_linhas = df.head(n_linhas).to_string()
        print(primeiras_linhas)

        # Mostrar últimas linhas
        print(f"\nÚLTIMAS {n_linhas} LINHAS:")
        ultimas_linhas = df.tail(n_linhas).to_string()
        print(ultimas_linhas)

        # Gerar texto formatado para prompt de LLM
        print("\nTEXTO FORMATADO PARA PROMPT DE LLM:")
        print("-" * 80)

        prompt_text = gerar_texto_prompt(df, caminho_arquivo, total_linhas, total_colunas, n_linhas)
        print(prompt_text)

        # Perguntar se deseja copiar o texto do prompt
        try:
            resposta = input("\nDeseja salvar o texto do prompt em um arquivo? (s/n): ")
            if resposta.lower() == 's':
                nome_arquivo = os.path.splitext(os.path.basename(caminho_arquivo))[0] + "_prompt.txt"
                with open(nome_arquivo, 'w', encoding='utf-8') as f:
                    f.write(prompt_text)
                print(f"Texto do prompt salvo em '{nome_arquivo}'")
        except:
            print("Não foi possível salvar o arquivo.")

        print("\nANÁLISE CONCLUÍDA COM SUCESSO!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nERRO AO ANALISAR O ARQUIVO: {str(e)}")


def gerar_texto_prompt(df, caminho_arquivo, total_linhas, total_colunas, n_linhas):
    """
    Gera um texto formatado para ser usado como parte de um prompt para LLMs
    """
    nome_arquivo = os.path.basename(caminho_arquivo)

    # Formatar informações sobre colunas
    info_colunas = []
    for i, coluna in enumerate(df.columns):
        valores_unicos = df[coluna].nunique()
        tipo_dados = str(df[coluna].dtype)

        # Formatar exemplos de valores únicos
        exemplos = ""
        if valores_unicos <= 6 and valores_unicos > 0:
            valores_lista = df[coluna].dropna().unique()
            # Limitar o tamanho de cada valor para exibição
            valores_formatados = [str(val)[:30] + "..." if len(str(val)) > 30 else str(val) for val in valores_lista]
            exemplos = f" Valores: [{', '.join(valores_formatados)}]"

        info_colunas.append(
            f"   - Coluna {i}: '{coluna}' (tipo: {tipo_dados}, valores únicos: {valores_unicos}){exemplos}")

    # Formatar exemplos de linhas
    primeiras_linhas = df.head(n_linhas).to_string()
    ultimas_linhas = df.tail(n_linhas).to_string()

    # Detectar valores ausentes
    colunas_com_ausentes = []
    for coluna in df.columns:
        nulos_coluna = df[coluna].isna().sum()
        if nulos_coluna > 0:
            percentual = (nulos_coluna / total_linhas) * 100
            colunas_com_ausentes.append(f"   - '{coluna}': {nulos_coluna} valores ausentes ({percentual:.2f}%)")

    # Montar o texto do prompt
    prompt = textwrap.dedent(f"""
    A planilha '{nome_arquivo}' contém {total_linhas} linhas e {total_colunas} colunas.

    Estrutura da planilha:
    {os.linesep.join(info_colunas)}

    Primeiras {n_linhas} linhas:
    ```
    {primeiras_linhas}
    ```

    Últimas {n_linhas} linhas:
    ```
    {ultimas_linhas}
    ```
    """)

    # Adicionar informações sobre valores ausentes, se houver
    if colunas_com_ausentes:
        prompt += textwrap.dedent(f"""
        Valores ausentes:
        {os.linesep.join(colunas_com_ausentes)}
        """)

    prompt += textwrap.dedent("""
    Por favor, use essas informações para entender a estrutura dos dados quando for
    realizar análises ou transformações nesta planilha.
    """)

    return prompt


if __name__ == "__main__":
    # Solicitar informações do usuário
    print("ANALISADOR DE PLANILHAS EXCEL")
    print("-" * 30)

    caminho_arquivo = input("Informe o caminho completo do arquivo Excel: ")

    linha_cabecalho_valida = False
    linha_cabecalho = 0

    while not linha_cabecalho_valida:
        try:
            linha_cabecalho = int(input("Informe o número da linha do cabeçalho (0 para primeira linha): "))
            if linha_cabecalho >= 0:
                linha_cabecalho_valida = True
            else:
                print("Erro: O número da linha deve ser maior ou igual a 0.")
        except ValueError:
            print("Erro: Por favor, informe um número inteiro válido.")

    # Executar a análise
    analisar_excel(caminho_arquivo, linha_cabecalho)