import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from streamlit.logger import get_logger

def run():
    # Set page config
    st.set_page_config(
        page_title="Análisis de Proyectos",
        page_icon="📊",
    )

    # Upload the Excel file
    uploaded_file = st.file_uploader("Carga tu archivo Excel", type=["xlsx"])

    if uploaded_file is not None:
        data = pd.read_excel(uploaded_file)

        # App title and description
        st.title("Análisis de Proyectos")
        st.write("Análisis de la duración en meses entre diferentes etapas de los proyectos.")

        # User input for country selection
        country = st.selectbox("Selecciona un país:", data['PAIS'].unique())

        # User input for analysis type
        analysis_type = st.selectbox("Selecciona el tipo de análisis:", ["CartaConsulta-Aprobación", "Aprobación-Vigencia", "Vigencia-Elegibilidad", "Elegibilidad-PrimeDesembolso"])

        # Visualization
        if analysis_type == "CartaConsulta-Aprobación":
            column = 'Meses_CartaConsulta_Aprobacion'
        elif analysis_type == "Aprobación-Vigencia":
            column = 'Meses_Aprobacion_Vigencia'
        elif analysis_type == "Vigencia-Elegibilidad":
            column = 'Meses_Vigencia_Elegibilidad'
        else:
            column = 'Meses_Elegibilidad_PrimeDesembolso'

        # Filter data by country
        filtered_data = data[data['PAIS'] == country]

        # Group by year of approval and calculate the mean of the selected column
        grouped = filtered_data.groupby('AÑOAprobacion')[column].mean()

        # Plotting
        fig, ax = plt.subplots(figsize=(10, 6))
        grouped.plot(kind='bar', ax=ax, color='lightblue')
        ax.set_ylabel('Meses')
        ax.set_xlabel('Año de Aprobación')
        ax.set_title(f'{analysis_type} - {country}')
        for bar in ax.patches:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, round(yval, 0), ha='center', va='bottom')

        st.pyplot(fig)

        # Optional: Sidebar information or other components can be added here

if __name__ == "__main__":
    run()

