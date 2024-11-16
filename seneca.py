import streamlit as st
import requests
from bs4 import BeautifulSoup
from docx import Document
from io import BytesIO
import time

# Set page configuration
st.set_page_config(
    page_title="Seneca Letters Reimagined",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title of the app
st.title("📜 Reimagine Seneca's Letters for the Modern Corporate World")

# Description
st.markdown("""
Bienvenido a la aplicación **Seneca Letters Reimagined**! Transforma la sabiduría atemporal de Seneca en ideas prácticas adaptadas para los gerentes corporativos de hoy en día. Ya sea que estés navegando desafíos de liderazgo, buscando un equilibrio entre el trabajo y la vida personal, o intentando aumentar la productividad, deja que Seneca te guíe a través de las complejidades del entorno laboral moderno.

**Cómo Usar:**
1. Selecciona los números de las cartas que deseas adaptar.
2. Haz clic en "Generar Adaptaciones" para procesar las cartas seleccionadas.
3. Una vez completado, descarga todas tus cartas adaptadas en un único documento Word.
""")

# Initialize session state for storing adapted letters
if 'adapted_letters' not in st.session_state:
    st.session_state['adapted_letters'] = {}

# Función para fetch el contenido original de la carta desde Wikisource
def fetch_letter_content(letter_num):
    url = f"https://en.wikisource.org/wiki/Moral_letters_to_Lucilius/Letter_{letter_num}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return None, f"Carta {letter_num} no encontrada. Asegúrate de que el número de la carta esté entre 1 y 65."
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extraer el contenido principal de la carta
    content_div = soup.find('div', {'class': 'mw-parser-output'})
    if not content_div:
        return None, "No se pudo analizar el contenido de la carta."
    
    paragraphs = content_div.find_all(['p', 'h2', 'h3'])
    letter_content = ""
    for para in paragraphs:
        if para.name in ['h2', 'h3']:
            continue  # Omitir encabezados
        letter_content += para.get_text(separator="\n") + "\n\n"
    
    if not letter_content.strip():
        return None, "El contenido de la carta está vacío."
    
    return letter_content.strip(), None

# Función para adaptar la carta usando la API de Tune Studio
def adapt_letter(original_content):
    api_url = "https://proxy.tune.app/chat/completions"
    api_key = st.secrets["tune_api_key"]
    
    prompt = f"""
Reimagine the following letter from Seneca to Lucilius, adapting it from its original philosophical content into a modern corporate setting. Imagine Seneca is writing in 2024 and Lucilius is a corporate manager. 

# Original Letter Content:
{original_content}

# Adaptation Instructions:
- Maintain the essence of Seneca's wisdom.
- Use simple, contemporary language.
- Incorporate references to modern technology, work-life balance, stress, leadership, and productivity.
- Adjust metaphors and examples to fit today's corporate culture.
"""
    
    payload = {
        "temperature": 0.66,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": "openai/gpt-4o-mini",
        "stream": False,
        "frequency_penalty": 0,
        "max_tokens": 5194
    }

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        adaptation = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        if not adaptation:
            return None, "No se recibió adaptación de la API."
        return adaptation, None
    except requests.exceptions.RequestException as e:
        return None, f"Fallo en la solicitud a la API: {e}"
    except ValueError:
        return None, "Respuesta inválida de la API."

# Sidebar para la entrada del usuario
st.sidebar.header("Generar Cartas Adaptadas en Lote")
with st.sidebar.form(key='batch_form'):
    # Permitir selección múltiple de cartas
    letter_numbers = st.multiselect(
        "Selecciona los Números de las Cartas (1-65)",
        options=list(range(1, 66)),
        default=[1]
    )
    submit_button = st.form_submit_button(label='Generar Adaptaciones')

if submit_button:
    if not letter_numbers:
        st.error("Por favor, selecciona al menos una carta para adaptar.")
    else:
        with st.spinner('Obteniendo y adaptando las cartas seleccionadas...'):
            progress_bar = st.progress(0)
            total = len(letter_numbers)
            success_count = 0
            failed_letters = []
            for idx, letter_num in enumerate(letter_numbers):
                original, error = fetch_letter_content(letter_num)
                if error:
                    failed_letters.append((letter_num, error))
                    progress_bar.progress((idx + 1) / total)
                    continue
                adaptation, api_error = adapt_letter(original)
                if api_error:
                    failed_letters.append((letter_num, api_error))
                else:
                    st.session_state['adapted_letters'][letter_num] = adaptation
                    success_count += 1
                progress_bar.progress((idx + 1) / total)
                time.sleep(0.5)  # Pausa para evitar sobrecargar la API

            progress_bar.empty()
            st.success(f"**¡Adaptaciones completadas!** {success_count} de {total} cartas fueron adaptadas exitosamente.")

            if failed_letters:
                st.warning("Algunas cartas no se pudieron adaptar:")
                for num, msg in failed_letters:
                    st.write(f"- **Carta {num}:** {msg}")

# Mostrar las cartas adaptadas
if st.session_state['adapted_letters']:
    st.markdown("---")
    st.header("📝 Tus Cartas Adaptadas")
    sorted_letters = dict(sorted(st.session_state['adapted_letters'].items()))
    for num, content in sorted_letters.items():
        st.markdown(f"**Carta {num}:**")
        st.write(content)
        st.markdown("---")

    # Botón para generar documento Word
    if st.button("📥 Descargar Todas las Cartas Adaptadas como Documento Word"):
        with st.spinner('Generando documento Word...'):
            doc = Document()
            doc.add_heading('Cartas Adaptadas de Seneca a Lucilius', 0)

            for num, content in sorted_letters.items():
                doc.add_heading(f'Carta {num}', level=1)
                doc.add_paragraph(content)
                doc.add_page_break()

            # Guardar el documento en un objeto BytesIO
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            # Proveer botón de descarga
            st.download_button(
                label="✅ Descargar Documento Word",
                data=buffer,
                file_name="Cartas_Adaptadas_Seneca_Letters.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

# Footer
st.markdown("---")
st.markdown("© 2024 Seneca Letters Reimagined | Powered by Streamlit y Tune Studio API")
