import streamlit as st
import pandas as pd
import io
import seaborn as sns
import matplotlib as plt
import matplotlib.pyplot as plt

# Función para calcular la diferencia en meses entre dos fechas
def calculate_kpi(end_date, start_date):
    if pd.isnull(start_date) or pd.isnull(end_date):
        return None  # Si alguna de las fechas está vacía, el KPI no se calcula
    return round(((end_date - start_date).days / 30), 2)

# Función para calcular la productividad basada en el KPI
def calculate_productivity(kpi):
    if kpi is None:
        return "Datos insuficientes"
    if kpi < 6:
        return "Eficiente"
    elif kpi < 8:
        return "Aceptable"
    elif kpi < 12:
        return "Con Demora"
    else:
        return "Alta Demora"

# Función para obtener el año de la fecha correspondiente a la operación
def get_year_for_operation(date):
    return date.year if pd.notnull(date) else None

# Función para obtener solo la primera palabra del nombre de la estación
def get_first_word(station):
    return station.split()[0] if station else None

# Función principal de la app de Streamlit
def run():
    st.set_page_config(page_title="Análisis de Eficiencia Operativa", page_icon="📊")

    uploaded_file = st.file_uploader("Carga tu archivo Excel", type=["xlsx"])

    if uploaded_file is not None:
        data = pd.read_excel(uploaded_file)

        # Convertir las columnas de fecha a datetime y extraer el año
        date_columns = ['FechaCartaConsulta', 'FechaAprobacion', 'FechaVigencia', 'FechaElegibilidad', 'FechaPrimeDesembolso']
        for col in date_columns:
            data[col] = pd.to_datetime(data[col], errors='coerce')

        # Mapeo de estaciones a sus respectivas columnas de fecha
        operations = {
            'Elegibilidad - Vigencia': ('FechaVigencia', 'FechaElegibilidad'),
            'PrimerDesembolso - Elegibilidad': ('FechaElegibilidad', 'FechaPrimeDesembolso'),
            'Vigencia - Aprobacion': ('FechaAprobacion', 'FechaVigencia'),
            'Aprobacion - Carta Consulta': ('FechaCartaConsulta', 'FechaAprobacion')
        }

        # Lista para almacenar los resultados
        results = []

        # Procesar las filas del DataFrame
        for index, row in data.iterrows():
            for operation, (start_col, end_col) in operations.items():
                kpi = calculate_kpi(row[end_col], row[start_col])
                productividad = calculate_productivity(kpi)
                year = get_year_for_operation(row[end_col])
                results.append({
                    'ESTACIONES': get_first_word(operation),
                    'ANO': year,
                    'PAIS': row['PAIS'],
                    'CODIGO': row['NO. OPERACION'],
                    'APODO': row['APODO'],
                    'Indicador_Principal': row[end_col].strftime('%d/%m/%Y') if pd.notnull(row[end_col]) else None,
                    'Indicador_Secundario': row[start_col].strftime('%d/%m/%Y') if pd.notnull(row[start_col]) else None,
                    'TIPO_DE_KPI': operation,
                    'KPI': kpi,
                    'Productividad': productividad
                })

        # Convertir la lista de resultados en un DataFrame
        results_df = pd.DataFrame(results)

        # Mostrar el DataFrame en la aplicación
        st.write("Datos Procesados:")
        st.dataframe(results_df)

        # Convertir el DataFrame a un archivo de Excel para la descarga
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            results_df.to_excel(writer, index=False)
        st.download_button(
            label="Descargar como Excel",
            data=output.getvalue(),
            file_name='resultados_kpi_productividad.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # Configuración de estilo de Seaborn
        sns.set_theme(style="whitegrid")

        # Título de la página
        st.title("Análisis de Operaciones con Alta y Con Demora")

        # Asumiendo que 'results_df' es el DataFrame que ya está preparado con los datos necesarios

        # Filtro de línea temporal para el año
        years = results_df['ANO'].dropna().astype(int)
        min_year, max_year = int(years.min()), int(years.max())
        selected_years = st.slider('Selecciona el rango de años:', min_year, max_year, (min_year, max_year))

        # Filtro para seleccionar país
        unique_countries = results_df['PAIS'].unique()
        selected_country = st.selectbox('Selecciona un País', ['Todos'] + list(unique_countries))

        # Filtramos el DataFrame para obtener solo las operaciones con alta y con demora y dentro del rango de años seleccionado
        delayed_operations = results_df[
            results_df['Productividad'].isin(['Alta Demora', 'Con Demora']) &
            (results_df['ANO'] >= selected_years[0]) &
            (results_df['ANO'] <= selected_years[1])
        ]

        # Si se selecciona un país específico, aplicamos ese filtro
        if selected_country != 'Todos':
            delayed_operations = delayed_operations[delayed_operations['PAIS'] == selected_country]

        # Cálculos para el análisis
        average_kpi_delayed = delayed_operations['KPI'].mean()
        unique_operations_count_delayed = delayed_operations['CODIGO'].nunique()
        total_stations_delayed = len(delayed_operations)

        # Mostrar métricas clave
        st.header("Métricas Clave de Operaciones Retrasadas")
        col1, col2, col3 = st.columns(3)
        col1.metric("Tiempo Promedio en Meses (Retraso)", f"{average_kpi_delayed:.2f}")
        col2.metric("Operaciones Únicas Retrasadas", unique_operations_count_delayed)
        col3.metric("Total de Estaciones Retrasadas", total_stations_delayed)

        # Definir el tamaño de la figura para los gráficos
        figsize = (12, 8)

        # Paleta de colores para los países
        country_colors = {
            "ARGENTINA": "#36A9E1",
            "BOLIVIA": "#F39200",
            "BRASIL": "#009640",
            "PARAGUAY": "#E30613",
            "URUGUAY": "#27348B"
        }

        # Preparación de datos para el gráfico de barras apiladas
        # Calculamos el KPI promedio por año y país
        kpi_by_year_country = delayed_operations.pivot_table(values='KPI', index='ANO', columns='PAIS', aggfunc='mean').fillna(0)

        # Aseguramos que los años sean enteros y se muestren como tal en el eje X
        kpi_by_year_country.index = kpi_by_year_country.index.astype(int)

        # Gráfico de barras apiladas con colores específicos
        st.subheader("KPI Promedio por Año y País")
        fig, ax = plt.subplots(figsize=figsize)
        kpi_by_year_country.plot(kind='bar', stacked=True, color=[country_colors.get(x, '#333333') for x in kpi_by_year_country.columns], ax=ax)

        # Agregar etiquetas de valor a cada segmento de barra y un total en la parte superior
        for i, (year, values) in enumerate(kpi_by_year_country.iterrows()):
            # Acumulador para la altura a la que se debe colocar la etiqueta
            height_accumulator = 0
            for country in values.index:
                value = values[country]
                if value > 0:  # Solo mostrar etiquetas para valores positivos
                    # La posición Y es la acumulada más la mitad del valor actual de la barra
                    label_y = height_accumulator + (value / 2)
                    ax.text(i, label_y, f'{int(value)}', ha='center', va='center', fontsize=9, color='white')
                    # Actualizamos el acumulador con el valor de la barra actual
                    height_accumulator += value
            # Colocar la etiqueta del total acumulado en la parte superior de la barra
            ax.text(i, height_accumulator, f'{int(height_accumulator)}', ha='center', va='bottom', fontsize=9, color='black')

        ax.set_ylabel('KPI Promedio')
        ax.set_xlabel('Año')
        # Corregir las etiquetas del eje X para asegurarnos de que sean enteros
        ax.set_xticklabels([str(x) for x in kpi_by_year_country.index], rotation=0)
        ax.legend(title='País', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        st.pyplot(fig)

        # Filtrar solo las operaciones con "Alta Demora"
        alta_demora_df = results_df[
            (results_df['Productividad'] == 'Alta Demora') &
            (results_df['ANO'] >= selected_years[0]) &
            (results_df['ANO'] <= selected_years[1])
        ]

        # Crear el DataFrame pivotado con el KPI promedio por país y año
        summary_df = alta_demora_df.pivot_table(
            values='KPI', 
            index='PAIS', 
            columns='ANO', 
            aggfunc='mean'
        ).fillna(0)

        # Redondear los valores a dos decimales
        summary_df = summary_df.round(2)

        # Convertir el índice 'ANO' a enteros
        summary_df.columns = summary_df.columns.astype(int)

        # Mostrar el DataFrame resumen en la aplicación
        st.write("Resumen de KPI Promedio por País y Año (Alta Demora):")
        st.dataframe(summary_df)

        # Convertir el DataFrame resumen a un objeto de bytes Excel para la descarga
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            summary_df.to_excel(writer, index=True)  # index=True para incluir los países en el Excel
            writer.close()  # No es necesario llamar a save() cuando se usa 'with'
        output.seek(0)  # Regresar al principio del stream para la descarga

        # Botón de descarga en Streamlit
        st.download_button(
            label="Descargar Resumen como Excel",
            data=output,
            file_name='resumen_alta_demora.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

if __name__ == "__main__":
    run()

