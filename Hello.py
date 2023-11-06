import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from streamlit.logger import get_logger

def run():
    # Set page config
    st.set_page_config(page_title="Análisis de Proyectos", page_icon="📊")

    # Upload the Excel file
    uploaded_file = st.file_uploader("Carga tu archivo Excel", type=["xlsx"])

    if uploaded_file is not None:
        data = pd.read_excel(uploaded_file)

        # Define the date columns
        date_columns = ['FechaCartaConsulta', 'FechaAprobacion', 'FechaVigencia', 'FechaElegibilidad', 'FechaPrimeDesembolso']
        # Convert the columns to datetime format (if they aren't already)
        for col in date_columns:
            data[col] = pd.to_datetime(data[col], errors='coerce')

        # Calculate the difference in months between the specified columns
        for i in range(len(date_columns) - 1):
            start_col = date_columns[i]
            end_col = date_columns[i + 1]
            diff_col_name = 'Meses_' + start_col[5:] + '_' + end_col[5:]
            data[diff_col_name] = ((data[end_col] - data[start_col]).dt.days / 30).clip(lower=0)

        # Extract year from each date column and create new columns with year information
        for col in date_columns:
            data['AÑO' + col[5:]] = data[col].dt.year

        # App title and description
        st.title("Análisis de Proyectos")
        st.write("Análisis de la duración en meses entre diferentes etapas de los proyectos.")

        # User input for country selection
        country = st.selectbox("Selecciona un país:", data['PAIS'].unique())

        # User input for analysis type
        analysis_type = st.selectbox("Selecciona el tipo de análisis:", ["CartaConsulta-Aprobación", "Aprobación-Vigencia", "Vigencia-Elegibilidad", "Elegibilidad-PrimeDesembolso"])
        # Determine the column for analysis based on the user's selection
        column_mapping = {
            "CartaConsulta-Aprobación": ('Meses_CartaConsulta_Aprobacion', 'AÑOAprobacion'),
            "Aprobación-Vigencia": ('Meses_Aprobacion_Vigencia', 'AÑOVigencia'),
            "Vigencia-Elegibilidad": ('Meses_Vigencia_Elegibilidad', 'AÑOElegibilidad'),
            "Elegibilidad-PrimeDesembolso": ('Meses_Elegibilidad_PrimeDesembolso', 'AÑOPrimeDesembolso')
        }
        month_column, year_column = column_mapping[analysis_type]

        # Filter data by country and ensure that the months are non-negative
        filtered_data = data[(data['PAIS'] == country) & (data[month_column] >= 0)]

        # Group by the appropriate year column and calculate the mean of the selected column
        grouped = filtered_data.groupby(year_column)[month_column].mean().reset_index()

        # Round the months to two decimal places
        grouped[month_column] = grouped[month_column].round(2)

        # Display metrics
        promedio_meses = grouped[month_column].mean()
        total_operaciones = grouped[month_column].count()
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Promedio de Meses", value=f"{promedio_meses:.2f}")
        with col2:
            st.metric(label="Total de Proyectos", value=total_operaciones)
        
        # Plotting
        fig, ax = plt.subplots(figsize=(10, 6))
        grouped.plot(kind='bar', x=year_column, y=month_column, ax=ax, color='lightblue', legend=False)
        ax.set_ylabel('Meses')
        ax.set_xlabel('Año')
        ax.set_title(f'{analysis_type} - {country}')
        for bar in ax.patches:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, int(round(yval)), ha='center', va='bottom')

        st.pyplot(fig)

        # Group by the appropriate year column and calculate the mean and count of the selected column
        grouped = filtered_data.groupby(year_column)[month_column].agg(['mean', 'count']).reset_index()

        # Round the 'mean' column to two decimal places
        grouped['mean'] = grouped['mean'].round(2)

        # Rename the columns for clarity
        grouped.columns = [year_column, 'Promedio_Meses', 'Cantidad_Operaciones']

        # Show the table
        st.write("Tabla de análisis:")
        st.dataframe(grouped)

        # Optional: Sidebar information or other components can be added here

if __name__ == "__main__":
    run()





