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

        # Cálculo de KPI Promedio y conteo de operaciones
        average_kpi = filtered_df['KPI'].mean()
        operation_count = len(filtered_df)

        # Mostrar métricas de KPI Promedio y conteo de operaciones
        st.header("Métricas Clave")
        col1, col2 = st.columns(2)
        col1.metric("Tiempo Promedio en Meses", f"{average_kpi:.2f}")
        col2.metric("Total de Estaciones", operation_count)
       
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

        # Gráfico de barras de KPI promedio por país con etiquetas de valor
        st.subheader("Tiempo de Respuesta Promedio en Meses por País")
        fig, ax = plt.subplots(figsize=figsize)
        # Asegúrese de que el ordenamiento sea ascendente para que el país con el menor KPI promedio aparezca primero
        kpi_avg_by_country = filtered_df.groupby('PAIS')['KPI'].mean().sort_values(ascending=True)
        sns.barplot(x=kpi_avg_by_country.values, y=kpi_avg_by_country.index, ax=ax, palette='viridis')
        add_value_labels(ax, is_horizontal=True)
        plt.tight_layout()
        st.pyplot(fig)

        # Gráfico de barras de conteo de operaciones por nivel de productividad con etiquetas de valor
        st.subheader("Eficiencia en Tiempos de Respuesta")
        fig, ax = plt.subplots(figsize=figsize)
        # Obtenemos el conteo de productividad y lo ordenamos de menor a mayor
        productivity_count = filtered_df['Productividad'].value_counts().sort_values()
        # Creamos el gráfico de barras horizontal
        sns.barplot(x=productivity_count.values, y=productivity_count.index, ax=ax, palette='Spectral')
        # Llamamos a la función para agregar etiquetas a las barras
        add_value_labels(ax, is_horizontal=True)
        plt.tight_layout()
        st.pyplot(fig)

        # Gráfico de barras de KPI a lo largo del tiempo (si los datos lo permiten)
        st.subheader("Tendencia de KPI a lo largo del tiempo")
        if len(filtered_df['ANO'].unique()) > 1:
            fig, ax = plt.subplots(figsize=(10, 5))
            # Calculamos el KPI promedio por año y aseguramos que ANO sea entero
            kpi_trend = filtered_df.groupby('ANO')['KPI'].mean().reset_index()
            kpi_trend['ANO'] = kpi_trend['ANO'].astype(int)  # Convertimos ANO a entero
            kpi_trend['KPI'] = kpi_trend['KPI'].round().astype(int)  # Redondeamos el KPI a entero
            # Creamos el gráfico de barras
            sns.barplot(data=kpi_trend, x='ANO', y='KPI', ax=ax, palette='viridis')
            # Añadimos las etiquetas de valores a las barras
            for bar in ax.patches:
                bar_height = bar.get_height()
                ax.annotate(f'{int(bar_height)}',
                            xy=(bar.get_x() + bar.get_width() / 2, bar_height),
                            xytext=(0, 3),  # 3 puntos de offset vertical
                            textcoords="offset points",
                            ha='center', va='bottom')
            # Mejoramos el layout y mostramos el gráfico
            plt.tight_layout()
            st.pyplot(fig)



if __name__ == "__main__":
    run()






