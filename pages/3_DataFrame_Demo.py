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

        # Sidebar para filtros
        st.sidebar.header("Filtros")

        # Supongamos que 'results_df' es el DataFrame creado anteriormente y contiene los datos necesarios

        # Filtro de línea temporal para el año
        if 'ANO' in results_df.columns:
            years = results_df['ANO'].dropna().astype(int)
            min_year, max_year = int(years.min()), int(years.max())
            selected_years = st.sidebar.slider('Selecciona el rango de años:', min_year, max_year, (min_year, max_year))

        # Filtro por estación con opción "Todas"
        if 'ESTACIONES' in results_df.columns:
            all_stations = ['Todas'] + list(results_df['ESTACIONES'].dropna().unique())
            selected_station = st.sidebar.selectbox('Selecciona una Estación', all_stations)

        # Aplicar filtros al DataFrame
        filtered_df = results_df[
            (results_df['ANO'] >= selected_years[0]) &
            (results_df['ANO'] <= selected_years[1])
        ]
        if selected_station != 'Todas':
            filtered_df = filtered_df[filtered_df['ESTACIONES'].str.contains(selected_station)]

        # Organizar el contenido en bloques
        # Bloque de estadísticas resumidas
        st.header("Estadísticas Resumidas")
        col1, col2 = st.columns(2)
        col1.metric("Total de Operaciones", len(filtered_df))
        col2.metric("Eficiencia Promedio de Operaciones", f"{filtered_df['KPI'].mean():.2f}")

        # Mostrar los datos filtrados en el dashboard
        st.header("Datos Filtrados")
        st.dataframe(filtered_df)

        # Función auxiliar para agregar etiquetas de valor en los gráficos de barra
        def add_value_labels(ax, spacing=5):
            for rect in ax.patches:
                y_value = rect.get_height()
                x_value = rect.get_x() + rect.get_width() / 2
                label = "{:.2f}".format(y_value)
                ax.annotate(label, (x_value, y_value), xytext=(0, spacing),
                            textcoords="offset points", ha='center', va='bottom')

        # Incluir gráficos
        st.header("Gráficos Analíticos")
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("Tiempos de Respuestas en Meses")
            kpi_avg_by_country = filtered_df.groupby('PAIS')['KPI'].mean().sort_values()
            fig, ax = plt.subplots()
            bars = sns.barplot(x=kpi_avg_by_country.index, y=kpi_avg_by_country.values, ax=ax, palette='viridis')
            add_value_labels(ax)
            st.pyplot(fig)

        with col4:
            st.subheader("Productividad")
            productivity_count = filtered_df['Productividad'].value_counts()
            fig, ax = plt.subplots()
            bars = sns.barplot(x=productivity_count.index, y=productivity_count.values, ax=ax, palette='Spectral')
            add_value_labels(ax)
            st.pyplot(fig)

        # Gráfico de líneas de KPI a lo largo del tiempo (si los datos lo permiten)
        if len(filtered_df['ANO'].unique()) > 1:
            st.subheader("Tendencia de KPI a lo largo del tiempo")
            kpi_trend = filtered_df.groupby('ANO')['KPI'].mean()
            fig, ax = plt.subplots()
            sns.lineplot(x=kpi_trend.index, y=kpi_trend.values, ax=ax)
            st.pyplot(fig)

if __name__ == "__main__":
    run()






