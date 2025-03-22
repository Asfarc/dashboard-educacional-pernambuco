import streamlit as st

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

# Controla o que é exportado pelo módulo
__all__ = ['navegar_tabela']