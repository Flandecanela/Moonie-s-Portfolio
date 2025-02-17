import streamlit as st
from supabase import create_client, Client
import requests
from PIL import Image
from io import BytesIO
import pandas as pd
import plotly.express as px


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

# Función para obtener las Obras de arte de la tabla "Obras"
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

# Obtenemos los datos
data = obtener_Obras()

# Si no se obtuvieron datos, se muestra un mensaje
if not data:
    st.error("No se pudieron cargar las Obras. Revisa la conexión con Supabase.")
    st.stop()

# Extraer las opciones únicas para cada filtro a partir de los datos
Tipos = sorted(list({obra["Tipo"] for obra in data}))
Contenidos = sorted(list({obra["Contenido"] for obra in data}))
Técnicas = sorted(list({obra["Técnica"] for obra in data}))

# Barra lateral con los filtros
st.sidebar.title("Filtros")
Tipo_filtro = st.sidebar.multiselect("Tipo", options=Tipos, default=Tipos)
Contenido_filtro = st.sidebar.multiselect("Contenido", options=Contenidos, default=Contenidos)
Técnica_filtro = st.sidebar.multiselect("Técnica", options=Técnicas, default=Técnicas)

# Filtrar las Obras según las selecciones
Obras_filtradas = [
    obra for obra in data
    if obra["Tipo"] in Tipo_filtro and obra["Contenido"] in Contenido_filtro and obra["Técnica"] in Técnica_filtro
]

# Título de la aplicación
st.title("Moonie's Portfolio")

# Sección desplegable para las estadísticas y mapas
with st.expander("Ver estadísticas y mapas", expanded=False):
    # Convertimos las obras filtradas en un DataFrame para los gráficos
    df_filtrado = pd.DataFrame(Obras_filtradas)
    if not df_filtrado.empty:
        # Dividimos la sección en dos columnas: izquierda para los gráficos circulares y derecha para el sunburst
        col_izq, col_der = st.columns([2, 1])
        
        with col_izq:
            st.markdown("Estadísticas por categoría")
            # Creamos tres columnas para los diagramas circulares
            col_tipo, col_contenido, col_tecnica = st.columns(3)
            
            # Gráfico circular para "Tipo"
            fig_tipo = px.pie(df_filtrado, names='Tipo', title="Tipo")
            fig_tipo.update_layout(width=400, height=400, margin=dict(l=20, r=20, t=40, b=20))
            with col_tipo:
                st.plotly_chart(fig_tipo, use_container_width=False)
            
            # Gráfico circular para "Contenido"
            fig_contenido = px.pie(df_filtrado, names='Contenido', title="Contenido")
            fig_contenido.update_layout(width=400, height=400, margin=dict(l=20, r=20, t=40, b=20))
            with col_contenido:
                st.plotly_chart(fig_contenido, use_container_width=False)
            
            # Gráfico circular para "Técnica"
            fig_tecnica = px.pie(df_filtrado, names='Técnica', title="Técnica")
            fig_tecnica.update_layout(width=400, height=400, margin=dict(l=20, r=20, t=40, b=20))
            with col_tecnica:
                st.plotly_chart(fig_tecnica, use_container_width=False)
        
        with col_der:
            st.markdown("Mapa de calor")
            fig_sunburst = px.sunburst(
                df_filtrado,
                path=['Tipo', 'Contenido', 'Técnica'],
                title="Categorías"
            )
            fig_sunburst.update_layout(width=400, height=400, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_sunburst, use_container_width=False)
    else:
        st.info("No hay datos para mostrar en los gráficos.")

# Mostrar obras en formato de tarjetas
st.header("Obras")
num_columnas = 3  # Número de columnas por fila
columnas = st.columns(num_columnas)

for index, obra in enumerate(Obras_filtradas):
    with columnas[index % num_columnas]:
        st.markdown(
            f"""
            <div>
                <h4 style="margin-bottom: 5px;">{obra["Título"]}</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )
        imagen = cargar_imagen(obra["Enlace"])
        if imagen is not None:
            st.image(imagen, use_container_width=True)
        else:
            st.write("Imagen no disponible.")
        st.caption(f"{obra['Tipo']} | {obra['Contenido']} | {obra['Técnica']}")
        st.write(f"**Fecha:** {obra['Fecha']}")
        st.markdown("---")
