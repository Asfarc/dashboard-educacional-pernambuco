import pandas as pd
import os

# Caminhos dos arquivos
escola_path = r"C:\Users\User\Downloads\escolas.parquet"
municipio_path = r"C:\Users\User\Downloads\municipio.parquet"
estado_path = r"C:\Users\User\Downloads\estado.parquet"


def analisar_parquet(caminho, nome_arquivo):
    """Analisa a estrutura de um arquivo parquet e retorna informações detalhadas."""
    print(f"\n{'=' * 80}")
    print(f"ANÁLISE DO ARQUIVO: {nome_arquivo}")
    print(f"{'=' * 80}")

    if not os.path.exists(caminho):
        print(f"ERRO: Arquivo {caminho} não encontrado!")
        return None

    try:
        # Carrega o arquivo
        df = pd.read_parquet(caminho)

        # Informações básicas
        print(f"Número de linhas: {df.shape[0]}")
        print(f"Número de colunas: {df.shape[1]}")

        # Lista todas as colunas
        print("\nLISTA DE COLUNAS:")
        for i, col in enumerate(df.columns):
            print(f"{i}: {col}")

        # Informações sobre os tipos de dados
        print("\nTIPOS DE DADOS:")
        print(df.dtypes)

        # Estatísticas básicas para colunas numéricas
        print("\nESTATÍSTICAS BÁSICAS:")
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                print(f"\nColuna: {col}")
                print(f"  Min: {df[col].min()}")
                print(f"  Max: {df[col].max()}")
                print(f"  Média: {df[col].mean()}")
                print(f"  Valores não-nulos: {df[col].count()} de {len(df)}")

        # Colunas específicas de matrículas
        colunas_matriculas = [col for col in df.columns if col.startswith("Número de Matrículas")]
        print(f"\nTotal de colunas de matrículas: {len(colunas_matriculas)}")

        return {
            "dataframe": df,
            "colunas": df.columns.tolist(),
            "colunas_matriculas": colunas_matriculas
        }

    except Exception as e:
        print(f"ERRO ao processar {nome_arquivo}: {str(e)}")
        return None


# Analisar cada arquivo
escola_info = analisar_parquet(escola_path, "escolas.parquet")
municipio_info = analisar_parquet(municipio_path, "municipio.parquet")
estado_info = analisar_parquet(estado_path, "estado.parquet")

# Verificar consistência das colunas de matrículas
print("\n" + "=" * 80)
print("VERIFICAÇÃO DE CONSISTÊNCIA DAS COLUNAS DE MATRÍCULAS")
print("=" * 80)

if all([escola_info, municipio_info, estado_info]):
    # Obter todas as colunas de matrículas de todos os arquivos
    todas_colunas_matriculas = set()
    for info in [escola_info, municipio_info, estado_info]:
        todas_colunas_matriculas.update(info["colunas_matriculas"])

    print(f"Total de colunas únicas de matrículas encontradas: {len(todas_colunas_matriculas)}")

    # Verificar cada coluna em cada arquivo
    print("\nVERIFICAÇÃO DE CONSISTÊNCIA:")
    for coluna in sorted(todas_colunas_matriculas):
        em_escola = coluna in escola_info["colunas"]
        em_municipio = coluna in municipio_info["colunas"]
        em_estado = coluna in estado_info["colunas"]

        status = "OK" if all([em_escola, em_municipio, em_estado]) else "INCONSISTENTE"

        print(f"{coluna}: {status}")
        print(f"  Escola: {'Presente' if em_escola else 'Ausente'}")
        print(f"  Município: {'Presente' if em_municipio else 'Ausente'}")
        print(f"  Estado: {'Presente' if em_estado else 'Ausente'}")

    # Verificar se há colunas extras em algum arquivo
    print("\nCOLUNAS EXCLUSIVAS EM CADA ARQUIVO:")

    escola_exclusivas = set(escola_info["colunas"]) - set(municipio_info["colunas"]) - set(estado_info["colunas"])
    if escola_exclusivas:
        print(f"\nColunas exclusivas em ESCOLA ({len(escola_exclusivas)}):")
        for col in sorted(escola_exclusivas):
            print(f"  {col}")

    municipio_exclusivas = set(municipio_info["colunas"]) - set(escola_info["colunas"]) - set(estado_info["colunas"])
    if municipio_exclusivas:
        print(f"\nColunas exclusivas em MUNICÍPIO ({len(municipio_exclusivas)}):")
        for col in sorted(municipio_exclusivas):
            print(f"  {col}")

    estado_exclusivas = set(estado_info["colunas"]) - set(escola_info["colunas"]) - set(municipio_info["colunas"])
    if estado_exclusivas:
        print(f"\nColunas exclusivas em ESTADO ({len(estado_exclusivas)}):")
        for col in sorted(estado_exclusivas):
            print(f"  {col}")

    # Verificar colunas comuns a todos os arquivos
    colunas_comuns = set(escola_info["colunas"]) & set(municipio_info["colunas"]) & set(estado_info["colunas"])
    print(f"\nTotal de colunas comuns aos três arquivos: {len(colunas_comuns)}")

    # Resumo final
    print("\nRESUMO FINAL:")
    print(f"Total de colunas em ESCOLA: {len(escola_info['colunas'])}")
    print(f"Total de colunas em MUNICÍPIO: {len(municipio_info['colunas'])}")
    print(f"Total de colunas em ESTADO: {len(estado_info['colunas'])}")
    print(f"Colunas comuns aos três arquivos: {len(colunas_comuns)}")

    # Verificar se todas as colunas de matrículas têm o mesmo nome exato nos três arquivos
    colunas_matriculas_consistentes = True
    for coluna in todas_colunas_matriculas:
        if not all([
            coluna in escola_info["colunas"],
            coluna in municipio_info["colunas"],
            coluna in estado_info["colunas"]
        ]):
            colunas_matriculas_consistentes = False
            break

    if colunas_matriculas_consistentes:
        print("\nTodas as colunas de matrículas têm exatamente o mesmo nome nos três arquivos.")
    else:
        print("\nALERTA: Existem inconsistências nos nomes das colunas de matrículas entre os arquivos.")
else:
    print("Não foi possível completar a verificação de consistência devido a erros no processamento dos arquivos.")