import streamlit as st
import requests
import re

# Configurar la clave de API de x.ai
XAI_API_KEY = st.secrets["XAI_API_KEY"]

def parse_esquema(esquema):
    capitulos = {}
    cap_pattern = re.compile(r'Capítulo\s*\d+[:\.\-]?\s*(.*)', re.IGNORECASE)
    seccion_pattern = re.compile(r'(?:-|\*)\s*Sección\s*\d+[:\.\-]?\s*(.*)', re.IGNORECASE)

    cap = None
    for linea in esquema.split('\n'):
        cap_match = cap_pattern.match(linea)
        if cap_match:
            cap = cap_match.group(1).strip()
            capitulos[cap] = []
            continue
        seccion_match = seccion_pattern.match(linea)
        if seccion_match and cap:
            seccion = seccion_match.group(1).strip()
            capitulos[cap].append(seccion)
    
    return capitulos

def generar_libro(titulo, num_capitulos, num_secciones):
    try:
        # 1. Generar el esquema del libro
        esquema_prompt = (
            f"Necesito que generes un esquema detallado para un libro titulado '{titulo}'. "
            f"El libro debe tener {num_capitulos} capítulos, y cada capítulo debe estar dividido en {num_secciones} secciones. "
            f"Proporciona los títulos de cada capítulo y las secciones correspondientes de manera clara y organizada."
        )
        
        esquema_response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {XAI_API_KEY}"
            },
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un asistente experto en estructuración y generación de contenido para libros. Ayudas a crear esquemas detallados y desarrollas el contenido de cada sección de manera clara y coherente."
                    },
                    {
                        "role": "user",
                        "content": esquema_prompt
                    }
                ],
                "model": "grok-beta",
                "stream": False,
                "temperature": 0.7
            }
        )

        if esquema_response.status_code != 200:
            st.error(f"Error al generar el esquema: {esquema_response.text}")
            return ""

        esquema = esquema_response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # **Agregar depuración: Mostrar el esquema generado**
        st.subheader("Esquema Generado")
        st.text(esquema)

        # Parsear el esquema usando expresiones regulares
        capitulos = parse_esquema(esquema)
        
        if not capitulos:
            st.error("No se pudieron extraer los capítulos y secciones del esquema generado. Revisa el esquema o ajusta los prompts.")
            return ""

        # 2. Generar contenido para cada sección
        libro = f"# {titulo}\n\n"
        for cap_num, (capitulo, secciones) in enumerate(capitulos.items(), 1):
            libro += f"## {capitulo}\n\n"
            for sec_num, seccion in enumerate(secciones, 1):
                # Extraer título de la sección
                if ":" in seccion:
                    titulo_seccion = seccion.split(":", 1)[1].strip()
                else:
                    titulo_seccion = seccion
                seccion_prompt = (
                    f"Escribe una sección detallada titulada '{titulo_seccion}' para el capítulo '{capitulo}' de un libro sobre '{titulo}'. "
                    f"La sección debe tener aproximadamente 300 palabras, ser clara, coherente y proporcionar información relevante y bien estructurada sobre el tema."
                )
                
                seccion_response = requests.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {XAI_API_KEY}"
                    },
                    json={
                        "messages": [
                            {
                                "role": "system",
                                "content": "Eres un escritor experto que ayuda a desarrollar contenido de libros de manera clara y coherente."
                            },
                            {
                                "role": "user",
                                "content": seccion_prompt
                            }
                        ],
                        "model": "grok-beta",
                        "stream": False,
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                )

                if seccion_response.status_code != 200:
                    st.error(f"Error al generar la sección '{titulo_seccion}': {seccion_response.text}")
                    contenido_seccion = "Error al generar esta sección."
                else:
                    contenido_seccion = seccion_response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                
                libro += f"### {seccion}\n\n{contenido_seccion}\n\n"
        
        return libro

    except Exception as e:
        st.error(f"Ocurrió un error: {e}")
        return ""

def main():
    st.title("Generador de Libros con IA usando x.ai")
    st.write("Introduce los detalles de tu libro y deja que la IA lo escriba por ti.")
    
    # Formulario para ingresar detalles del libro
    with st.form(key='book_form'):
        titulo = st.text_input("Título del Libro", "Introducción a la Inteligencia Artificial")
        num_capitulos = st.number_input("Número de Capítulos", min_value=1, max_value=50, value=5)
        num_secciones = st.number_input("Número de Secciones por Capítulo", min_value=1, max_value=20, value=4)
        submit_button = st.form_submit_button(label='Generar Libro')
    
    if submit_button:
        st.info("Generando el libro, por favor espera...")
        # Llamar a la función para generar el libro
        libro = generar_libro(titulo, num_capitulos, num_secciones)
        if libro:
            st.success("Libro generado exitosamente!")
            st.download_button(
                label="Descargar Libro",
                data=libro,
                file_name=f"{titulo.replace(' ', '_')}.txt",
                mime="text/plain"
            )
            st.text_area("Contenido del Libro", libro, height=600)

if __name__ == "__main__":
    main()
