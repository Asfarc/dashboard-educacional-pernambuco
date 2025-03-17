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


# --- Classes de Serviço ---

class DataLoader:
    """Carregamento seguro e eficiente de dados com cache"""

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
    """Gerenciamento dinâmico de estrutura de colunas"""

    @staticmethod
    def create_column_mapping(df: pd.DataFrame) -> Dict:
        """Cria mapeamento dinâmico de colunas baseado em padrões"""
        column_map = {}
        for col in df.columns:
            parts = col.lower().split(' de ')
            if 'matrículas' in parts:
                key = parts[-1].strip()
                column_map.setdefault(key, []).append(col)
        return column_map

    @staticmethod
    def get_numeric_columns(df: pd.DataFrame) -> List[str]:
        """Identifica colunas numéricas automaticamente"""
        return df.select_dtypes(include=np.number).columns.tolist()


# --- Componentes de UI ---

class AggridTable:
    """Componente AgGrid altamente configurável"""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.gb = GridOptionsBuilder.from_dataframe(df)
        self._configure_defaults()

    def _configure_defaults(self):
        """Configurações base de performance e segurança"""
        self.gb.configure_default_column(
            resizable=True,
            filterable=True,
            sortable=True,
            editable=False,
            wrapText=True,
            autoHeight=True,
            suppressMenu=True
        )

        if len(self.df) > 10000:
            self.gb.configure_grid_options(
                rowModelType='serverSide',
                cacheBlockSize=100,
                maxBlocksInCache=10,
                suppressRowVirtualisation=True
            )

    def add_columns(self, columns: List[Dict]):
        """Adiciona configurações específicas de coluna"""
        for col_config in columns:
            self.gb.configure_column(**col_config)

    def build(self, height: int = 600) -> Dict:
        """Renderiza o grid final"""
        return AgGrid(
            self.df,
            gridOptions=self.gb.build(),
            height=height,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            fit_columns_on_grid_load=True,
            theme="streamlit",
            key="main_grid"
        )


# --- Lógica de Negócio ---

class EducationAnalyzer:
    """Núcleo de análise de dados educacionais"""

    def __init__(self):
        self.escolas, self.estado, self.municipio = DataLoader.load_education_data()
        self.current_df = None
        self.column_mapping = None

    def apply_filters(self, filters: Dict) -> None:
        """Aplica filtros ao dataset atual"""
        query_parts = []
        if 'dependency' in filters:
            query_parts.append(f"`DEPENDENCIA ADMINISTRATIVA` in {filters['dependency']}")
        if 'year' in filters:
            query_parts.append(f"ANO == {filters['year']}")

        if query_parts:
            self.current_df = self.current_df.query(' and '.join(query_parts))

    def calculate_metrics(self, column: str) -> Dict:
        """Calcula métricas principais para uma coluna"""
        return {
            'total': self.current_df[column].sum(),
            'media': self.current_df[column].mean(),
            'mediana': self.current_df[column].median(),
            'min': self.current_df[column].min(),
            'max': self.current_df[column].max()
        }


# --- Interface Principal ---

def main_interface():
    """Configura a interface principal do dashboard"""
    analyzer = EducationAnalyzer()

    with st.sidebar:
        st.header("Filtros Principais")
        visualization_level = st.radio(
            "Nível de Visualização:",
            ["Escola", "Município", "Estado"]
        )

        # Atualiza dataset baseado na seleção
        analyzer.current_df = getattr(analyzer, visualization_level.lower())
        analyzer.column_mapping = ColumnManager.create_column_mapping(analyzer.current_df)

        # Filtros dinâmicos
        year_filter = st.selectbox(
            "Ano:",
            sorted(analyzer.current_df['ANO'].unique())
        )
        dependency_filter = st.multiselect(
            "Dependência Administrativa:",
            analyzer.current_df['DEPENDENCIA ADMINISTRATIVA'].unique()
        )

        analyzer.apply_filters({
            'year': year_filter,
            'dependency': dependency_filter
        })

    # Layout principal
    st.title("Análise de Matrículas Educacionais")
    display_main_content(analyzer)


def display_main_content(analyzer: EducationAnalyzer):
    """Exibe conteúdo principal do dashboard"""
    col1, col2, col3 = st.columns(3)
    numeric_cols = ColumnManager.get_numeric_columns(analyzer.current_df)

    with col1:
        selected_column = st.selectbox("Selecione a Métrica:", numeric_cols)

    metrics = analyzer.calculate_metrics(selected_column)

    # Cards de métricas
    col1.metric("Total", f"{metrics['total']:,.0f}")
    col2.metric("Média", f"{metrics['media']:,.1f}")
    col3.metric("Variação", f"{metrics['max'] - metrics['min']:,.0f}")

    # Tabela interativa
    st.subheader("Visualização Detalhada")
    table_config = [
        {'field': 'ANO', 'filter': 'agNumberFilter'},
        {'field': selected_column, 'type': ['numericColumn', 'numberColumnFilter']}
    ]

    grid = AggridTable(analyzer.current_df)
    grid.add_columns(table_config)
    grid_response = grid.build(height=700)

    # Controles de exportação
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


# --- Ponto de Entrada ---
if __name__ == "__main__":
    main_interface()