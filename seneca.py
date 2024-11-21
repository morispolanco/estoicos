import streamlit as st
import requests
import os

# Configurar la clave de API de x.ai 
XAI_API_KEY = st.secrets["XAI_API_KEY"]

def generar_libro(titulo, num_capitulos, num_secciones):
    try:
        # 1. Generar el esquema del libro
        esquema_prompt = f"Genera un esquema detallado para un libro titulado '{titulo}' con {num_capitulos} capítulos, cada uno con {num_secciones} secciones. Lista los títulos de cada capítulo y sus respectivas secciones."
        
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
                        "content": "You are a test assistant."
                    },
                    {
                        "role": "user",
                        "content": esquema_prompt
                    }
                ],
                "model": "grok-beta",
                "stream": False,
                "temperature": 0
            }
        )

        if esquema_response.status_code != 200:
            st.error(f"Error al generar el esquema: {esquema_response.text}")
            return ""

        esquema = esquema_response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

        # Parsear el esquema para obtener capítulos y secciones
        lineas = esquema.split('\n')
        capitulos = {}
        cap = ""
        for linea in lineas:
            if linea.lower().startswith("capítulo"):
                cap = linea.strip()
                capitulos[cap] = []
            elif linea.lower().startswith("- sección") or linea.lower().startswith("sección"):
                seccion = linea.replace("- ", "").strip()
                capitulos[cap].append(seccion)
        
        # 2. Generar contenido para cada sección
        libro = f"# {titulo}\n\n"
        for cap_num, (capitulo, secciones) in enumerate(capitulos.items(), 1):
            libro += f"## {capitulo}\n\n"
            for sec_num, seccion in enumerate(secciones, 1):
                # Extraer título de la sección
                titulo_seccion = seccion.split(":")[1].strip() if ":" in seccion else seccion
                seccion_prompt = f"Escribe una sección detallada titulada '{titulo_seccion}' para el capítulo '{capitulo}' de un libro sobre '{titulo}'."
                
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
                                "content": "You are a test assistant."
                            },
                            {
                                "role": "user",
                                "content": seccion_prompt
                            }
                        ],
                        "model": "grok-beta",
                        "stream": False,
                        "temperature": 0
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
