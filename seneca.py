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
1. Ingresa el número de la carta que deseas adaptar.
2. Haz clic en "Generar Adaptación" para recibir una versión modernizada de la carta.
3. Repite el proceso para múltiples cartas.
4. Una vez terminado, descarga todas tus cartas adaptadas en un único documento Word.
""")

# Initialize session state for storing adapted letters
if 'adapted_letters' not in st.session_state:
    st.session_state['adapted_letters'] = {}

# Función para fetch el contenido original de la carta desde Wikisource
def fetch_letter_content(letter_num):
    url = f"https://en.wikisource.org/wiki/Moral_letters_to_Lucilius/Letter_{letter_num}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return None, f"Letter {letter_num} not found. Please ensure the letter number is between 1 and 65."
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extraer el contenido principal de la carta
    content_div = soup.find('div', {'class': 'mw-parser-output'})
    if not content_div:
        return None, "Unable to parse the letter content."
    
    paragraphs = content_div.find_all(['p', 'h2', 'h3'])
    letter_content = ""
    for para in paragraphs:
        if para.name in ['h2', 'h3']:
            continue  # Omitir encabezados
        letter_content += para.get_text(separator="\n") + "\n\n"
    
    if not letter_content.strip():
        return None, "Letter content is empty."
    
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
            return None, "No adaptation received from the API."
        return adaptation, None
    except requests.exceptions.RequestException as e:
        return None, f"API request failed: {e}"
    except ValueError:
        return None, "Invalid response from the API."

# Sidebar para la entrada del usuario
st.sidebar.header("Generar Cartas Adaptadas")
with st.sidebar.form(key='letter_form'):
    letter_number = st.number_input("Ingresa el Número de la Carta (1-65)", min_value=1, max_value=65, step=1)
    submit_button = st.form_submit_button(label='Generar Adaptación')

if submit_button:
    with st.spinner('Obteniendo y adaptando la carta...'):
        original, error = fetch_letter_content(letter_number)
        if error:
            st.error(error)
        else:
            adaptation, api_error = adapt_letter(original)
            if api_error:
                st.error(api_error)
            else:
                st.success(f"**¡Carta Adaptada {letter_number} Generada Exitosamente!**")
                st.markdown(f"### **Adaptación de la Carta {letter_number}:**")
                st.write(adaptation)
                
                # Almacenar la carta adaptada en el estado de la sesión
                st.session_state['adapted_letters'][letter_number] = adaptation

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
