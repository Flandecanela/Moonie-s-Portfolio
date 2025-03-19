import streamlit as st
from supabase import create_client, Client
import requests
from PIL import Image
from io import BytesIO
import pandas as pd
import datetime

# --- Configuración de Supabase ---
SUPABASE_URL = "https://pibviflccqjlzaaxvxdw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBpYnZpZmxjY3FqbHphYXh2eGR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk3NTQ2NDIsImV4cCI6MjA1NTMzMDY0Mn0.5BzQPsuPW5ToOC1bkW72229LJUDBUhOHo8woAeiir0Y"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Funciones auxiliares ---
def obtener_direct_image_url(url: str) -> str:
    if "imgur.com" in url and "i.imgur.com" not in url:
        url = url.split('?')[0].rstrip('/')
        image_id = url.split('/')[-1]
        return f"https://i.imgur.com/{image_id}.jpg"
    return url

@st.cache_data
def obtener_Obras_df() -> pd.DataFrame:
    # Obtener datos de Supabase
    response = supabase.table("Obras").select("id, Título, Fecha, Enlace, Tipo, Serie, Técnica").execute()
    data = response.data
    df = pd.DataFrame(data)
    if not df.empty:
        # Convertir la columna de fecha a datetime
        df['Fecha'] = pd.to_datetime(df['Fecha'], format="%Y-%m-%d", errors='coerce')
    return df

@st.cache_data
def cargar_imagen(url: str):
    url_directa = obtener_direct_image_url(url)
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://imgur.com"}
    try:
        response = requests.get(url_directa, headers=headers)
        response.raise_for_status()
        imagen = Image.open(BytesIO(response.content))
        return imagen
    except Exception as e:
        st.error(f"Error al cargar la imagen desde {url_directa}: {e}")
        return None

# --- Main ---

# Cargar datos
df_obras = obtener_Obras_df()
if df_obras.empty:
    st.error("No se pudieron cargar las Obras. Revisa la conexión con Supabase.")
    st.stop()

# Inicializar variables de sesión
if "started" not in st.session_state:
    st.session_state.started = False
if "selected_icon" not in st.session_state:
    st.session_state.selected_icon = None
if "popup_closed" not in st.session_state:
    st.session_state.popup_closed = False

# Pantalla de inicio
if not st.session_state.started:
    st.title("Portafolio de relación de Aiden y Europa")
    try:
        with open("inicio_text.txt", "r", encoding="utf-8") as file:
            inicio_text = file.read()
    except FileNotFoundError:
        inicio_text = "El archivo 'inicio_text.txt' no se encontró. Por favor, verifica la ruta."
    st.write(inicio_text)
    
    if st.button("Actualizar datos", key="actualizar_inicio"):
        st.cache_data.clear()
    if st.button("Iniciar"):
        st.session_state.started = True

# Selección de época
elif st.session_state.started and st.session_state.selected_icon is None:
    st.title("Selecciona una época")
    col1, col2, col3 = st.columns(3)
    if col1.button("1. Reconocimiento (2017-01-01 a 2021-06-27)"):
        st.session_state.selected_icon = 1
    if col2.button("2. Distanciamiento (2021-06-28 a 2023-07-24)"):
        st.session_state.selected_icon = 2
    if col3.button("3. Reencuentro (2023-07-25 al presente)"):
        st.session_state.selected_icon = 3

# Popup modal de información
elif st.session_state.selected_icon is not None and not st.session_state.popup_closed:
    file_name = f"popup_text_{st.session_state.selected_icon}.txt"
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            popup_text = file.read()
    except FileNotFoundError:
        popup_text = f"El archivo '{file_name}' no se encontró."
    st.markdown(popup_text)
    if st.button("Cerrar"):
        st.session_state.popup_closed = True

# Mostrar obras filtradas y con filtros adicionales
elif st.session_state.popup_closed:
    # Definir el rango de fechas según el ícono seleccionado
    if st.session_state.selected_icon == 1:
        start_date, end_date = pd.Timestamp("2017-01-01"), pd.Timestamp("2021-06-27")
    elif st.session_state.selected_icon == 2:
        start_date, end_date = pd.Timestamp("2021-06-28"), pd.Timestamp("2023-07-24")
    elif st.session_state.selected_icon == 3:
        start_date, end_date = pd.Timestamp("2023-07-25"), pd.Timestamp("2025-03-01")
    
    # Filtrar obras por fecha usando operaciones vectorizadas
    df_filtrado = df_obras[(df_obras['Fecha'] >= start_date) & (df_obras['Fecha'] <= end_date)]
    
    # Filtros en la barra lateral
    st.sidebar.title("Filtros")
    tipos = sorted(df_filtrado['Tipo'].dropna().unique().tolist())
    series = sorted(df_filtrado['Serie'].dropna().unique().tolist())
    tecnicas = sorted(df_filtrado['Técnica'].dropna().unique().tolist())
    
    tipo_filtro = st.sidebar.multiselect("Tipo", options=tipos, default=tipos)
    serie_filtro = st.sidebar.multiselect("Serie", options=series, default=series)
    tecnica_filtro = st.sidebar.multiselect("Técnica", options=tecnicas, default=tecnicas)
    
    st.sidebar.markdown("### Contadores")
    st.sidebar.metric("Obras totales en rango", len(df_filtrado))
    
    # Aplicar filtros adicionales
    df_final = df_filtrado[
        (df_filtrado['Tipo'].isin(tipo_filtro)) &
        (df_filtrado['Serie'].isin(serie_filtro)) &
        (df_filtrado['Técnica'].isin(tecnica_filtro))
    ]
    st.sidebar.metric("Obras mostradas", len(df_final))
    
    # Ordenar por fecha
    orden = st.sidebar.radio("Ordenar por fecha", ("Más antigua a más reciente", "Más reciente a más antigua"))
    ascending = True if orden == "Más antigua a más reciente" else False
    df_final = df_final.sort_values(by="Fecha", ascending=ascending)
    
    # Botón para volver a selección de íconos
    if st.button("Volver a selección de íconos"):
        st.session_state.selected_icon = None
        st.session_state.popup_closed = False

    st.header("Obras")
    
    # Mostrar obras en cuadrícula usando st.columns (5 por fila)
    if not df_final.empty:
        n_columns = 5
        rows = [df_final.iloc[i:i+n_columns] for i in range(0, df_final.shape[0], n_columns)]
        for row in rows:
            cols = st.columns(n_columns)
            for idx, (_, obra) in enumerate(row.iterrows()):
                with cols[idx]:
                    st.markdown(f"**{obra['Título']}**")
                    image_url = obtener_direct_image_url(obra["Enlace"])
                    st.image(image_url, width=150)
                    st.markdown(f"{obra['Tipo']} | {obra['Serie']} | {obra['Técnica']}")
                    st.markdown(f"Fecha: {obra['Fecha'].strftime('%Y-%m-%d')}")
    else:
        st.info("No se encontraron obras con los filtros seleccionados.")
