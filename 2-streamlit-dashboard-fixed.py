import streamlit as st
import pandas as pd
import numpy as np
import os
import logging
from pathlib import Path
import io
from typing import Tuple, Dict, List, Optional
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

# Configuração inicial
logging.basicConfig(level=logging.INFO)
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- Classes de Serviço Corrigidas ---

class DataLoader:
    @staticmethod
    @st.cache_data(show_spinner="Carregando dados educacionais...")
    def load_education_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        try:
            base_dir = os.getenv("DATA_DIR", "./data")
            return (
                pd.read_parquet(Path(base_dir) / "escolas.parquet"),
                pd.read_parquet(Path(base_dir) / "estado.parquet"),
                pd.read_parquet(Path(base_dir) / "municipio.parquet")
            )
        except Exception as e:
            logging.error(f"Falha no carregamento: {str(e)}")
            st.error("Erro crítico: Base de dados não encontrada")
            st.stop()


class ColumnManager:
    @staticmethod
    def create_column_mapping(df: pd.DataFrame) -> Dict:
        column_map = {}
        for col in df.columns:
            parts = col.lower().split(' de ')
            if 'matrículas' in parts:
                key = parts[-1].strip()
                column_map.setdefault(key, []).append(col)
        return column_map

    @staticmethod
    def get_numeric_columns(df: pd.DataFrame) -> List[str]:
        return df.select_dtypes(include=np.number).columns.tolist()


# --- Lógica de Negócio Atualizada ---

class EducationAnalyzer:
    def __init__(self):
        self.escolas, self.estado, self.municipio = DataLoader.load_education_data()
        self.current_df = None
        self.column_mapping = None

    def apply_filters(self, filters: Dict) -> None:
        # Filtro de dependência administrativa corrigido
        if filters.get('dependency'):
            self.current_df = self.current_df[
                self.current_df['DEPENDENCIA ADMINISTRATIVA'].isin(filters['dependency'])

            # Filtro de ano sanitizado
            if filters.get('year'):
                self.current_df = self.current_df[self.current_df['ANO'] == int(filters['year'])]

    def calculate_metrics(self, column: str) -> Dict:
        return {
            'total': self.current_df[column].sum(),
            'media': self.current_df[column].mean(),
            'mediana': self.current_df[column].median(),
            'min': self.current_df[column].min(),
            'max': self.current_df[column].max()
        }


# --- Interface Principal Corrigida ---

def main_interface():
    analyzer = EducationAnalyzer()

    with st.sidebar:
        st.header("Filtros Principais")
        visualization_level = st.radio(
            "Nível de Visualização:",
            ["Escola", "Município", "Estado"]
        )

        # Correção crucial do mapeamento
        level_mapping = {
            "Escola": "escolas",
            "Município": "municipio",
            "Estado": "estado"
        }
        df_name = level_mapping[visualization_level]
        analyzer.current_df = getattr(analyzer, df_name)

        # Filtros com sanitização
        year_filter = st.selectbox(
            "Ano:",
            options=sorted(analyzer.current_df['ANO'].unique()),
            format_func=lambda x: int(x)
        )

        dependency_filter = st.multiselect(
            "Dependência Administrativa:",
            options=analyzer.current_df['DEPENDENCIA ADMINISTRATIVA'].unique()
        )

        analyzer.apply_filters({
            'year': year_filter,
            'dependency': dependency_filter
        })

    # Layout principal
    st.title("Análise de Matrículas Educacionais")
    col1, col2, col3 = st.columns(3)

    # Métricas atualizadas
    numeric_cols = ColumnManager.get_numeric_columns(analyzer.current_df)
    selected_column = col1.selectbox("Selecione a Métrica:", numeric_cols)
    metrics = analyzer.calculate_metrics(selected_column)

    col1.metric("Total", f"{metrics['total']:,.0f}")
    col2.metric("Média", f"{metrics['media']:,.1f}")
    col3.metric("Variação", f"{metrics['max'] - metrics['min']:,.0f}")

    # Tabela interativa
    st.subheader("Visualização Detalhada")
    grid = AggridTable(analyzer.current_df)
    grid.add_columns([
        {'field': 'ANO', 'filter': 'agNumberFilter'},
        {'field': selected_column, 'type': ['numericColumn', 'numberColumnFilter']}
    ])
    grid_response = grid.build(height=700)

    # Exportação de dados
    with st.expander("Exportar Dados"):
        export_format = st.radio("Formato:", ["CSV", "Excel"])
        export_data = grid_response['data']

        if export_format == "CSV":
            st.download_button(
                "Download CSV",
                data=export_data.to_csv(index=False),
                file_name="dados_filtrados.csv"
            )
        else:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                export_data.to_excel(writer, index=False)
            st.download_button(
                "Download Excel",
                data=output.getvalue(),
                file_name="dados_filtrados.xlsx"
            )


if __name__ == "__main__":
    main_interface()