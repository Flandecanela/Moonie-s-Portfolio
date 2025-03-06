import streamlit as st
from supabase import create_client, Client
import requests
from PIL import Image
from io import BytesIO
import pandas as pd
import plotly.express as px
import datetime

# Configuración de Supabase: reemplaza con tus datos
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
    response = supabase.table("Obras").select("id, Título, Fecha, Enlace, Tipo, Contenido, Técnica").execute()
    return response.data

# Función para cargar la imagen desde la URL
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
    filtered = []
    for obra in data:
        try:
            fecha = datetime.datetime.strptime(obra["Fecha"], "%Y-%m-%d")
        except Exception as e:
            continue
        if start <= fecha <= end:
            filtered.append(obra)
    return filtered

# Obtenemos los datos
data = obtener_Obras()

if not data:
    st.error("No se pudieron cargar las Obras. Revisa la conexión con Supabase.")
    st.stop()

# Inicializamos variables de sesión para controlar el flujo de la aplicación
if "started" not in st.session_state:
    st.session_state["started"] = False
if "selected_icon" not in st.session_state:
    st.session_state["selected_icon"] = None
if "popup_closed" not in st.session_state:
    st.session_state["popup_closed"] = False

# ----- Pantalla de inicio -----
if not st.session_state["started"]:
    st.title("Bienvenido a Moonie's Portfolio")
    st.write("Esta aplicación muestra obras de arte filtradas por rangos de fecha y categorías. Aquí puedes explorar diferentes períodos de creación de las obras. Haz clic en 'Iniciar' para comenzar.")
    if st.button("Iniciar"):
        st.session_state["started"] = True
        st.experimental_rerun()

# ----- Pantalla de selección de íconos -----
if st.session_state["started"] and st.session_state["selected_icon"] is None:
    st.title("Selecciona un ícono")
    col1, col2, col3 = st.columns(3)
    if col1.button("Ícono 1"):
        st.session_state["selected_icon"] = 1
        st.experimental_rerun()
    if col2.button("Ícono 2"):
        st.session_state["selected_icon"] = 2
        st.experimental_rerun()
    if col3.button("Ícono 3"):
        st.session_state["selected_icon"] = 3
        st.experimental_rerun()

# ----- Popup modal de información -----
if st.session_state["selected_icon"] is not None and not st.session_state["popup_closed"]:
    with st.modal("Información"):
        st.write(f"Placeholder: Este es un texto de ejemplo para el Ícono {st.session_state['selected_icon']}.")
        if st.button("Cerrar", key="cerrar_popup"):
            st.session_state["popup_closed"] = True
            st.experimental_rerun()

# ----- Mostrar obras filtradas por fecha tras cerrar el popup -----
if st.session_state["popup_closed"]:
    # Definir rangos de fecha según el ícono seleccionado
    if st.session_state["selected_icon"] == 1:
        start_date = "2017-01-01"
        end_date = "2021-06-27"
    elif st.session_state["selected_icon"] == 2:
        start_date = "2021-01-28"
        end_date = "2023-07-24"
    elif st.session_state["selected_icon"] == 3:
        start_date = "2023-07-25"
        end_date = "2025-03-01"
    
    filtered_artworks = filter_by_date(data, start_date, end_date)
    st.header("Obras filtradas por fecha")
    
    if filtered_artworks:
        num_columnas = 3
        columnas = st.columns(num_columnas)
        for index, obra in enumerate(filtered_artworks):
            with columnas[index % num_columnas]:
                st.markdown(f"<div><h4 style='margin-bottom: 5px;'>{obra['Título']}</h4></div>", unsafe_allow_html=True)
                imagen = cargar_imagen(obra["Enlace"])
                if imagen is not None:
                    st.image(imagen, use_container_width=True)
                else:
                    st.write("Imagen no disponible.")
                st.caption(f"{obra['Tipo']} | {obra['Contenido']} | {obra['Técnica']}")
                st.write(f"**Fecha:** {obra['Fecha']}")
                st.markdown("---")
    else:
        st.info("No se encontraron obras en el rango de fechas seleccionado.")
    
    # Botón para volver a la selección de íconos (reinicia la vista de popup)
    if st.button("Volver a selección de íconos"):
        st.session_state["selected_icon"] = None
        st.session_state["popup_closed"] = False
        st.experimental_rerun()
