import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def run():
    # Set page config
    st.set_page_config(page_title="Análisis de Proyectos", page_icon="📊")

    # Upload the Excel file
    uploaded_file = st.file_uploader("Carga tu archivo Excel", type=["xlsx"])

    if uploaded_file is not None:
        data = pd.read_excel(uploaded_file)

        # Convert the columns to datetime format (if they aren't already)
        date_columns = ['FechaCartaConsulta', 'FechaAprobacion', 'FechaVigencia', 'FechaElegibilidad', 'FechaPrimeDesembolso']
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

        # Find the min and max year from all relevant year columns
        year_columns = ['AÑO' + col[5:] for col in date_columns]
        min_year = int(data[year_columns].min().min())
        max_year = int(data[year_columns].max().max())

        # Slider for year range selection
        year_range = st.slider('Selecciona el rango de años:', min_value=min_year, max_value=max_year, value=(min_year, max_year))

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

        # Filter data by country and ensure that the months are non-negative and greater than zero
        filtered_data = data[(data['PAIS'] == country) & (data[month_column] >= 0)]

        # Filter data based on the selected year range
        filtered_data = filtered_data[(filtered_data[year_column] >= year_range[0]) & (filtered_data[year_column] <= year_range[1])]

        # Group by the appropriate year column and calculate the mean of the selected column
        grouped = filtered_data.groupby(year_column)[month_column].mean().reset_index()

        # Round the months to two decimal places
        grouped[month_column] = grouped[month_column].round(2)

        # Count the number of unique operations per year where the difference is calculated
        operations_count = filtered_data.groupby(year_column)['NO. OPERACION'].nunique().reset_index()
        operations_count.rename(columns={'NO. OPERACION': 'Operaciones por Año'}, inplace=True)

        # Count the total number of unique operations where the difference is calculated
        operation_total = filtered_data['NO. OPERACION'].nunique()

        # Merge the unique operations count with the mean duration data
        final_data = pd.merge(grouped, operations_count, on=year_column)

        # Display the metrics at the top
        total_average = final_data[month_column].mean()
        col1, col2 = st.columns(2)
        col1.metric("Promedio Total de Meses", f"{total_average:.2f}")
        col2.metric("Proyectos Totales", operation_total)

        # Plotting
        fig, ax = plt.subplots(figsize=(10, 6))
        final_data.plot(kind='bar', x=year_column, y=month_column, ax=ax, color='lightblue', legend=False)
        ax.set_ylabel('Meses')
        ax.set_xlabel('Año')
        ax.set_title(f'{analysis_type} - {country}')
        for bar in ax.patches:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, int(round(yval)), ha='center', va='bottom')

        st.pyplot(fig)

        # Show the final data table
        st.write("Detalles por año:")
        st.dataframe(final_data)

if __name__ == "__main__":
    run()


