import streamlit as st
import requests
from bs4 import BeautifulSoup
from docx import Document
from io import BytesIO
import roman
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
Welcome to the **Seneca Letters Reimagined** app! Transform the timeless wisdom of Seneca into actionable insights tailored for today's corporate managers. Whether you're navigating leadership challenges, striving for work-life balance, or aiming to boost productivity, let Seneca guide you through the complexities of the modern workplace.

**How to Use:**
1. Enter the number of the letter you wish to adapt.
2. Click "Generate Adaptation" to receive a modernized version of the letter.
3. Repeat the process for multiple letters.
4. Once done, download all your adapted letters in a single Word document.
""")

# Initialize session state for storing adapted letters
if 'adapted_letters' not in st.session_state:
    st.session_state['adapted_letters'] = {}

# Function to convert integer to Roman numeral
def int_to_roman(num):
    try:
        return roman.toRoman(num)
    except roman.InvalidRomanNumeralError:
        return None

# Function to fetch original letter content from Wikisource
def fetch_letter_content(letter_num):
    roman_num = int_to_roman(letter_num)
    if not roman_num:
        return None, "Invalid letter number. Please enter a number between 1 and 65."
    
    url = f"https://en.wikisource.org/wiki/Moral_letters_to_Lucilius/Letter_{roman_num}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return None, f"Letter {letter_num} not found. Please ensure the letter number is between 1 and 65."
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract the main content of the letter
    content_div = soup.find('div', {'class': 'mw-parser-output'})
    if not content_div:
        return None, "Unable to parse the letter content."
    
    paragraphs = content_div.find_all(['p', 'h2', 'h3'])
    letter_content = ""
    for para in paragraphs:
        if para.name in ['h2', 'h3']:
            continue  # Skip headers
        letter_content += para.get_text(separator="\n") + "\n\n"
    
    if not letter_content.strip():
        return None, "Letter content is empty."
    
    return letter_content.strip(), None

# Function to adapt the letter using Tune Studio API
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

# Sidebar for user input
st.sidebar.header("Generate Adapted Letters")
with st.sidebar.form(key='letter_form'):
    letter_number = st.number_input("Enter Letter Number (1-65)", min_value=1, max_value=65, step=1)
    submit_button = st.form_submit_button(label='Generate Adaptation')

if submit_button:
    with st.spinner('Fetching and adapting the letter...'):
        original, error = fetch_letter_content(letter_number)
        if error:
            st.error(error)
        else:
            adaptation, api_error = adapt_letter(original)
            if api_error:
                st.error(api_error)
            else:
                st.success(f"**Adapted Letter {letter_number} Generated Successfully!**")
                st.markdown(f"### **Letter {letter_number} Adaptation:**")
                st.write(adaptation)
                
                # Store the adapted letter in session state
                st.session_state['adapted_letters'][letter_number] = adaptation

# Display adapted letters
if st.session_state['adapted_letters']:
    st.markdown("---")
    st.header("📝 Your Adapted Letters")
    sorted_letters = dict(sorted(st.session_state['adapted_letters'].items()))
    for num, content in sorted_letters.items():
        st.markdown(f"**Letter {num}:**")
        st.write(content)
        st.markdown("---")

    # Button to generate Word document
    if st.button("📥 Download All Adapted Letters as Word Document"):
        with st.spinner('Generating Word document...'):
            doc = Document()
            doc.add_heading('Adapted Letters of Seneca to Lucilius', 0)

            for num, content in sorted_letters.items():
                doc.add_heading(f'Letter {num}', level=1)
                doc.add_paragraph(content)
                doc.add_page_break()

            # Save the document to a BytesIO object
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            # Provide download button
            st.download_button(
                label="✅ Download Word Document",
                data=buffer,
                file_name="Adapted_Seneca_Letters.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

# Footer
st.markdown("---")
st.markdown("© 2024 Seneca Letters Reimagined | Powered by Streamlit and Tune Studio API")

