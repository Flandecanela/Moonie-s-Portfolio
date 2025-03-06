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
    return [
        obra for obra in data 
        if start <= datetime.datetime.strptime(obra["Fecha"], "%Y-%m-%d") <= end
    ]

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
    st.write(
        "Esta pequeña aplicación está pensada para enseñar de forma sintética los dibujos que Aiden ha hecho sobre su relación conmigo a lo largo de ya casi ocho años de conocerme. A través de ellos se puede dar cuenta de una parte importante de nuestra historia de vida."
        "Las obras están divididas en tres momentos, correspondientes a los años en los que nos conocimos y afianzamos nuestra relación, en los que nos distanciamos, y los que nos reencontramos y nos hicimos pareja"
    )
    st.write("Haz doble clic en «Iniciar» para 
