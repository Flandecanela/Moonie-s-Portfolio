import streamlit as st
from supabase import create_client, Client
import requests
from PIL import Image
from io import BytesIO
import pandas as pd
import plotly.express as px
import datetime

# Configuración de Supabase
SUPABASE_URL = "https://pibviflccqjlzaaxvxdw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBpYnZpZmxjY3FqbHphYXh2eGR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk3NTQ2NDIsImV4cCI6MjA1NTMzMDY0Mn0.5BzQPsuPW5ToOC1bkW72229LJUDBUhOHo8woAeiir0Y"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Función para transformar enlaces de Imgur a enlaces directos de imagen
def obtener_direct_image_url(url: str) -> str:
    if "imgur.com" in url and "i.imgur.com" not in url:
        url = url.split('?')[0].rstrip('/')
        image_id = url.split('/')[-1]
        return f"https://i.imgur.com/{image_id}.jpg"
    return url

# Función para obtener las Obras de la tabla "Obras"
@st.cache_data
def obtener_Obras():
    response = supabase.table("Obras").select("id, Título, Fecha, Enlace, Tipo, Serie, Técnica").execute()
    return response.data

# Función para cargar la imagen desde la URL (no se usa para mostrar, pero se mantiene para otros usos)
@st.cache_data
def cargar_imagen(url: str):
    url_directa = obtener_direct_image_url(url)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://imgur.com"
    }
    try:
        response = requests.get(url_directa, headers=headers)
        response.raise_for_status()
        imagen = Image.open(BytesIO(response.content))
        return imagen
    except Exception as e:
        st.error(f"Error al cargar la imagen desde {url_directa}: {e}")
        return None

# Función para filtrar obras por rango de fecha (formato YYYY-MM-DD)
def filter_by_date(data, start_date, end_date):
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    return [
        obra for obra in data 
        if start <= datetime.datetime.strptime(obra["Fecha"], "%Y-%m-%d") <= end
    ]

# Se elimina el botón de actualizar datos del ámbito global

# Obtener los datos de Supabase
data = obtener_Obras()
if not data:
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
    # Se carga el texto de inicio desde un archivo
    try:
        with open("inicio_text.txt", "r", encoding="utf-8") as file:
            inicio_text = file.read()
    except FileNotFoundError:
        inicio_text = "El archivo 'inicio_text.txt' no se encontró. Por favor, verifica la ruta."
    st.write(inicio_text)
    
    # El botón de actualizar datos se muestra únicamente en la pantalla de inicio
    if st.button("Actualizar datos", key="actualizar_inicio"):
        st.cache_data.clear()
    if st.button("Iniciar"):
        st.session_state.started = True

# Pantalla de selección de íconos
elif st.session_state.started and st.session_state.selected_icon is None:
    st.title("Selecciona una época")
    col1, col2, col3 = st.columns(3)
    if col1.button("1.Reconocimiento (2017.01.01 - 2021.06.27)"):
        st.session_state.selected_icon = 1
    if col2.button("2. Distanciamiento (2021.06.28 - 2023.07.24)"):
        st.session_state.selected_icon = 2
    if col3.button("3. Reencuentro (2023.07.25 - 2025.03.01)"):
        st.session_state.selected_icon = 3

# Popup modal de información (simulado)
elif st.session_state.selected_icon is not None and not st.session_state.popup_closed:
    # Se carga el texto del popup desde un archivo según el ícono seleccionado
    file_name = f"popup_text_{st.session_state.selected_icon}.txt"
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            popup_text = file.read()
    except FileNotFoundError:
        popup_text = f"El archivo '{file_name}' no se encontró."
    st.markdown(popup_text)
    if st.button("Cerrar"):
        st.session_state.popup_closed = True

# Mostrar obras filtradas con filtros adicionales, contadores dinámicos y botón en la parte superior
elif st.session_state.popup_closed:
    # Definir el rango de fechas según el ícono seleccionado
    if st.session_state.selected_icon == 1:
        start_date = "2017-01-01"
        end_date = "2021-06-27"
    elif st.session_state.selected_icon == 2:
        start_date = "2021-01-28"
        end_date = "2023-07-24"
    elif st.session_state.selected_icon == 3:
        start_date = "2023-07-25"
        end_date = "2025-03-01"
    
    # Filtrar obras por fecha
    filtered_artworks = filter_by_date(data, start_date, end_date)

    # En el sidebar ya no se muestra el botón "Actualizar datos"
    st.sidebar.title("Filtros")
    
    # Filtros para refinar los resultados
    tipos = sorted({obra["Tipo"] for obra in filtered_artworks})
    series = sorted({obra["Serie"] for obra in filtered_artworks})
    tecnicas = sorted({obra["Técnica"] for obra in filtered_artworks})
    tipo_filtro = st.sidebar.multiselect("Tipo", options=tipos, default=tipos)
    serie_filtro = st.sidebar.multiselect("Serie", options=series, default=series)
    tecnica_filtro = st.sidebar.multiselect("Técnica", options=tecnicas, default=tecnicas)

    # Contadores dinámicos en la barra lateral
    st.sidebar.markdown("### Contadores")
    st.sidebar.metric("Obras totales en rango", len(filtered_artworks))
    obras_filtradas = [
        obra for obra in filtered_artworks
        if obra["Tipo"] in tipo_filtro and obra["Serie"] in serie_filtro and obra["Técnica"] in tecnica_filtro
    ]
    st.sidebar.metric("Obras mostradas", len(obras_filtradas))
    
    # NUEVO: Opción para ordenar las obras por fecha
    orden = st.sidebar.radio("Ordenar por fecha", ("Más antigua a más reciente", "Más reciente a más antigua"))
    # Ordenamos usando la fecha (se convierte el string a datetime para comparar)
    obras_ordenadas = sorted(
        obras_filtradas, 
        key=lambda obra: datetime.datetime.strptime(obra["Fecha"], "%Y-%m-%d"), 
        reverse=(orden == "Más reciente a más antigua")
    )

    # Botón para volver a selección de íconos, ubicado en la parte superior
    if st.button("Volver a selección de íconos"):
        st.session_state.selected_icon = None
        st.session_state.popup_closed = False

    # Título
    st.header("Obras")

    # Mostrar obras filtradas en 5 columnas, con títulos de fuente más pequeña e imágenes clicables
    if obras_ordenadas:
        num_columnas = 5
        columnas = st.columns(num_columnas)
        for index, obra in enumerate(obras_ordenadas):
            with columnas[index % num_columnas]:
                # Título con fuente más pequeña
                st.markdown(f"<div style='font-size: 16px; margin-bottom: 5px;'>{obra['Título']}</div>", unsafe_allow_html=True)
                # Obtener la URL directa de la imagen
                image_url = obtener_direct_image_url(obra["Enlace"])
                # Imagen clicable para expandir (abre en nueva pestaña)
                st.markdown(f'<a href="{image_url}" target="_blank"><img src="{image_url}" width="150"></a>', unsafe_allow_html=True)
                st.caption(f"{obra['Tipo']} | {obra['Serie']} | {obra['Técnica']}")
                st.write(f"**Fecha:** {obra['Fecha']}")
                st.markdown("---")
    else:
        st.info("No se encontraron obras con los filtros seleccionados.")
