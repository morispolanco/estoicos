import streamlit as st
import requests
from docx import Document
from docx.shared import Pt
from io import BytesIO
import time
from bs4 import BeautifulSoup
import re
import PyPDF2

# Configuración de la página
st.set_page_config(
    page_title="Adaptador de Obras Filosóficas",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Adaptador de Obras Filosóficas para Estudiantes de 16 Años")

# Descripción
st.markdown("""
Esta aplicación adapta una obra filosófica proporcionada en **PDF** para estudiantes de 16 años, aplicando estrategias de simplificación de lenguaje, relevancia para adolescentes y técnicas de engagement.
""")

# Función para extraer texto de un PDF por capítulos
def extraer_capitulos_pdf(archivo_pdf):
    reader = PyPDF2.PdfReader(archivo_pdf)
    texto_completo = ""
    for page in reader.pages:
        texto_completo += page.extract_text() + "\n"
    
    # Suponiendo que los capítulos están marcados con "Capítulo X" o similar
    capitulos = re.split(r'Capítulo\s+\d+', texto_completo, flags=re.IGNORECASE)
    titulos = re.findall(r'Capítulo\s+\d+', texto_completo, flags=re.IGNORECASE)
    
    capitulos_dict = {}
    for i, cap in enumerate(capitulos[1:], start=1):
        titulo = titulos[i-1] if i-1 < len(titulos) else f"Capítulo {i}"
        capitulos_dict[titulo.strip()] = cap.strip()
    
    return capitulos_dict

# Función para adaptar el contenido usando la API
def adaptar_contenido(contenido_original, titulo_capitulo):
    api_key = st.secrets["api"]["key"]
    url = "https://api.openai.com/v1/chat/completions"  # URL de la API de OpenAI
    
    prompt = f"""
    Adapta el siguiente contenido filosófico para estudiantes de 16 años. Aplica las siguientes estrategias:
    
    **Simplificación del Lenguaje**
    - Reemplaza términos filosóficos complejos con lenguaje cotidiano.
    - Usa oraciones más cortas.
    - Explica conceptos abstractos con analogías relacionadas con la vida diaria de un adolescente.
    - Elimina jerga académica.
    
    **Relevancia para Adolescentes**
    - Conecta las ideas filosóficas con la exploración de la identidad personal, relaciones sociales, desafíos escolares y de la vida, tecnología y experiencias modernas, crecimiento personal e inteligencia emocional.
    
    **Técnicas de Engagement**
    - Incluye un tono conversacional.
    - Usa ejemplos del mundo real.
    - Añade preguntas reflexivas.
    - Desglosa ideas complejas en partes fáciles de entender.
    - Resalta aplicaciones prácticas para la vida diaria.
    
    **Título del Capítulo:**
    {titulo_capitulo}
    
    **Contenido Original:**
    {contenido_original}
    
    **Adaptación:**
    """

    payload = {
        "messages": [
            {"role": "system", "content": "Eres un asistente que adapta textos filosóficos para estudiantes de 16 años aplicando estrategias de simplificación, relevancia y engagement."},
            {"role": "user", "content": prompt}
        ],
        "model": "gpt-4",  # Asegúrate de usar el modelo adecuado
        "temperature": 0.7
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            respuesta = response.json()
            adaptacion = respuesta.get('choices')[0].get('message').get('content').strip()
            return adaptacion
        else:
            st.error(f"Error al adaptar el capítulo {titulo_capitulo}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Excepción al adaptar el capítulo {titulo_capitulo}: {e}")
        return None

# Función para convertir texto con formato básico a Python-docx
def texto_a_docx(paragraph, texto):
    # Puedes implementar más reglas de formato si es necesario
    lines = texto.split('\n')
    for line in lines:
        if line.startswith("**") and line.endswith("**"):
            # Texto en negrita
            run = paragraph.add_run(line.strip('*'))
            run.bold = True
        elif line.endswith("?"):
            # Pregunta reflexiva en itálica
            run = paragraph.add_run(line)
            run.italic = True
        else:
            paragraph.add_run(line)
    paragraph.add_run('\n')

# Cargar el archivo PDF
uploaded_file = st.file_uploader("Sube la obra filosófica en PDF", type=["pdf"])

if uploaded_file is not None:
    capitulos = extraer_capitulos_pdf(uploaded_file)
    st.sidebar.header("Configuración de Adaptación")
    opcion = st.sidebar.selectbox(
        "Seleccione una opción de capítulos a adaptar:",
        ("Seleccionar manualmente", "Adaptar todos los capítulos")
    )
    
    if opcion == "Seleccionar manualmente":
        opciones_capitulos = list(capitulos.keys())
        seleccion = st.sidebar.multiselect(
            "Seleccione los capítulos que desea adaptar:",
            opciones_capitulos,
            default=[opciones_capitulos[0]] if opciones_capitulos else []
        )
        numeros_capitulos = seleccion
    else:
        # Adaptar todos los capítulos
        numeros_capitulos = list(capitulos.keys())
        st.sidebar.info(f"Se procesarán todos los {len(numeros_capitulos)} capítulos disponibles.")
    
    # Botón para iniciar la adaptación
    if st.sidebar.button("Adaptar Capítulos"):
        if not numeros_capitulos:
            st.sidebar.error("Por favor, seleccione al menos un capítulo válido.")
        else:
            documentos = {}
            total = len(numeros_capitulos)
            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, titulo in enumerate(numeros_capitulos, start=1):
                status_text.text(f"Adaptando {titulo} ({idx}/{total})...")

                contenido_original = capitulos[titulo]
                if contenido_original:
                    adaptacion = adaptar_contenido(contenido_original, titulo)
                    if adaptacion:
                        documentos[titulo] = adaptacion
                    else:
                        documentos[titulo] = "Error en la adaptación."
                else:
                    documentos[titulo] = "Contenido no disponible."

                # Actualizar la barra de progreso
                progress = idx / total
                progress_bar.progress(progress)

                # Simular tiempo de espera (puedes eliminar esto en producción)
                time.sleep(0.5)

            status_text.text("Adaptación completa.")
            progress_bar.empty()

            # Crear el documento Word
            doc = Document()
            estilo_normal = doc.styles['Normal']
            estilo_normal.font.name = 'Arial'
            estilo_normal.font.size = Pt(12)

            for titulo, contenido in documentos.items():
                # Agregar título como encabezado de nivel 1
                doc.add_heading(titulo, level=1)

                # Dividir el contenido en párrafos basados en saltos de línea
                paragraphs = contenido.split('\n\n')
                for para in paragraphs:
                    paragraph = doc.add_paragraph()
                    texto_a_docx(paragraph, para)
                doc.add_page_break()

            # Guardar el documento en memoria
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            # Botón para descargar
            st.success("Todos los capítulos han sido adaptados exitosamente.")
            st.download_button(
                label="Descargar Documento Word",
                data=buffer,
                file_name="Adapted_Philosophical_Work.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
