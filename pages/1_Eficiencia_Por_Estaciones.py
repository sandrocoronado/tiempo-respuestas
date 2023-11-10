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

        # Configurar el estilo de Seaborn para los gráficos
        sns.set_theme(style="whitegrid")

        # Título del Dashboard
        st.title("Dashboard de Eficiencia Operativa")

        # Definir la paleta de colores para los países
        country_colors = {
            "ARGENTINA": "#36A9E1",
            "BOLIVIA": "#F39200",
            "BRASIL": "#009640",
            "PARAGUAY": "#E30613",
            "URUGUAY": "#27348B"
        }
        # Filtros en la parte superior
        # Filtro de línea temporal para el año
        years = results_df['ANO'].dropna().astype(int)
        min_year, max_year = int(years.min()), int(years.max())
        selected_years = st.slider('Selecciona el rango de años:', min_year, max_year, (min_year, max_year))

        # Filtro por estación con opción "Todas"
        all_stations = ['Todas'] + list(results_df['ESTACIONES'].dropna().unique())
        selected_station = st.selectbox('Selecciona una Estación', all_stations)

        # Aplicar filtros al DataFrame
        filtered_df = results_df[
            (results_df['ANO'] >= selected_years[0]) &
            (results_df['ANO'] <= selected_years[1])
        ]
        if selected_station != 'Todas':
            filtered_df = filtered_df[filtered_df['ESTACIONES'].str.contains(selected_station)]

        # Filtrar los datos insuficientes para el gráfico de conteo de productividad
        filtered_df = filtered_df[filtered_df['Productividad'] != "Datos insuficientes"]

        # Incluir gráficos
        st.header("         Análisis de la Eficiencia Operativa")
        figsize = (7, 5)  # Definir el tamaño de la figura para los gráficos

        # Cálculo de KPI Promedio y conteo de operaciones únicas
        average_kpi = filtered_df['KPI'].mean()
        unique_operation_count = filtered_df['CODIGO'].nunique()  # Usamos nunique() para contar códigos únicos
        total_stations = len(filtered_df)  # Conteo total de estaciones (filas)

        # Mostrar métricas de KPI Promedio, conteo de operaciones únicas y total de estaciones
        col1, col2, col3 = st.columns(3)
        col1.metric("Tiempo Promedio en Meses", f"{average_kpi:.2f}")
        col2.metric("Proyectos", unique_operation_count)
        col3.metric("Total de Estaciones", total_stations)

       
        # Función auxiliar para agregar etiquetas de valor en los gráficos de barra
        def add_value_labels(ax, is_horizontal=False):
            for rect in ax.patches:
                # Obtener las coordenadas X e Y del comienzo de la barra
                x_value = rect.get_x() + rect.get_width() / 2
                y_value = rect.get_y() + rect.get_height() / 2
                # Decidir si la etiqueta es para un gráfico horizontal o vertical
                if is_horizontal:
                    value = rect.get_width()
                    label = f"{int(value)}"  # Convertir a entero y formatear
                    ax.text(value, y_value, label, ha='left', va='center')
                else:
                    value = rect.get_height()
                    label = f"{int(value)}"  # Convertir a entero y formatear
                    ax.text(x_value, value, label, ha='center', va='bottom')

        # Utilizar st.columns para colocar gráficos lado a lado
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Tiempo de Respuesta Promedio en Meses por País")
            fig, ax = plt.subplots(figsize=figsize)
            
            # Calcular el KPI promedio por país
            kpi_avg_by_country = filtered_df.groupby('PAIS')['KPI'].mean().sort_values(ascending=True)
            
            # Crear una lista de colores que coincida con el orden de los países en 'kpi_avg_by_country'
            country_order = kpi_avg_by_country.index
            country_palette = [country_colors.get(country, "#333333") for country in country_order]

            # Dibujar el gráfico de barras con la paleta de colores específica
            sns.barplot(x=kpi_avg_by_country.values, y=country_order, ax=ax, palette=country_palette)
            
            # Agregar las etiquetas de valor
            add_value_labels(ax, is_horizontal=True)
            
            plt.tight_layout()
            st.pyplot(fig)

        with col2:
            st.subheader("Eficiencia en Tiempos de Respuesta")
            fig, ax = plt.subplots(figsize=figsize)
            productivity_count = filtered_df['Productividad'].value_counts().sort_values()
            sns.barplot(x=productivity_count.values, y=productivity_count.index, ax=ax, palette='Spectral')
            add_value_labels(ax, is_horizontal=True)
            plt.tight_layout()
            st.pyplot(fig)

        # Reemplazamos el gráfico de "Tiempo de Respuesta a lo largo del tiempo" por el gráfico de barras apiladas
        st.subheader("Tiempo Promedio por Año y País")

        # Definir la paleta de colores para los países
        country_colors = {
            "ARGENTINA": "#36A9E1",
            "BOLIVIA": "#F39200",
            "BRASIL": "#009640",
            "PARAGUAY": "#E30613",
            "URUGUAY": "#27348B"
        }

        # Aplicar filtros al DataFrame
        filtered_df = results_df[
            (results_df['ANO'] >= selected_years[0]) &
            (results_df['ANO'] <= selected_years[1])
        ]
        if selected_station != 'Todas':
            filtered_df = filtered_df[filtered_df['ESTACIONES'].str.contains(selected_station)]

        # Preparación de datos para el gráfico de barras apiladas
        kpi_by_year_country = filtered_df.pivot_table(values='KPI', index='ANO', columns='PAIS', aggfunc='mean').fillna(0)
        # Aseguramos que los años sean enteros y se muestren como tal en el eje X
        kpi_by_year_country.index = kpi_by_year_country.index.map(int)

        # Creamos una lista de colores basada en los países presentes en el DataFrame y en el orden correcto
        colors = [country_colors.get(country, "#333333") for country in kpi_by_year_country.columns]

        # Gráfico de barras apiladas con colores específicos
        fig, ax = plt.subplots(figsize=(12, 6))
        kpi_by_year_country.plot(kind='bar', stacked=True, color=colors, ax=ax)

        # Agregar etiquetas de valor a cada segmento de barra
        for i, (year, values) in enumerate(kpi_by_year_country.iterrows()):
            height_accumulator = 0  # Acumulador para la altura de las barras
            for country in values.index:
                value = values[country]
                if value > 0:  # Solo agregamos etiquetas a valores positivos
                    label_y = height_accumulator + (value / 2)
                    ax.text(i, label_y, f'{int(value)}', ha='center', va='center', fontsize=9, color='white')
                    height_accumulator += value
            # Colocar la etiqueta del total acumulado en la parte superior de la barra
            ax.text(i, height_accumulator, f'{int(height_accumulator)}', ha='center', va='bottom', fontsize=9, color='black')

        ax.set_ylabel('KPI Promedio')
        ax.set_xlabel('Año')
        ax.set_xticklabels([str(x) for x in kpi_by_year_country.index], rotation=0)
        ax.legend(title='País', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        st.pyplot(fig)

        filtered_df['ANO'] = filtered_df['ANO'].astype(int)     

        # Pivotear el DataFrame para obtener el KPI promedio por país y año
        kpi_pivot_df = filtered_df.pivot_table(values='KPI', index='PAIS', columns='ANO', aggfunc='mean')

        # Redondear todos los valores numéricos a dos decimales
        kpi_pivot_df = kpi_pivot_df.round(2)

        # Opción para reemplazar los valores None/NaN con un string vacío
        kpi_pivot_df = kpi_pivot_df.fillna('')

        # Convertir las etiquetas de las columnas a enteros (los años)
        kpi_pivot_df.columns = kpi_pivot_df.columns.astype(int)

        # Resetear el índice para llevar 'PAIS' a una columna
        kpi_pivot_df.reset_index(inplace=True)


        # Convertir el DataFrame pivotado a un archivo de Excel para la descarga
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            kpi_pivot_df.to_excel(writer, index=False)
            # No es necesario llamar a writer.save() aquí, se guarda automáticamente al finalizar el bloque with
        output.seek(0)  # Regresamos al principio del stream para que streamlit pueda leer el contenido

        # Muestra el DataFrame en la aplicación
        st.write("Datos Resumidos:")
        st.dataframe(kpi_pivot_df)

        # Botón de descarga en Streamlit
        st.download_button(
            label="Descargar KPI promedio por país y año como Excel",
            data=output,
            file_name='kpi_promedio_por_pais_y_año.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )



if __name__ == "__main__":
    run()






