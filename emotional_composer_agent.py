# emotional_composer_agent

# Import Pustaka
import streamlit as st
import time
import re 
import logging 
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool 
import json

# Konfigurasi logging dasar
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='agent_composer_narrative.log', filemode='a')


# --- 0. Utility Functions ---

def format_assistant_response(text: str) -> str:
    """Mengaplikasikan formatting BOLD untuk poin penting dan ITALIC untuk kata Inggris umum, KECUALI di dalam blok kode."""
    parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)
    formatted_parts = []
    for part in parts:
        if part.startswith('```') and part.endswith('```'):
            formatted_parts.append(part)
        else:
            keywords_to_bold = ["komposisi", "melodi", "chord", "instrumentasi", "tempo", "emosi", "kunci", "composition", "melody", "key", "tempo", "instrumentation", "emotion", "struktur", "progresi", "genre"]
            for keyword in keywords_to_bold:
                part = re.sub(r'\b(' + re.escape(keyword) + r')\b', r'**\1**', part, flags=re.IGNORECASE)
            english_words = ["rag", "agent", "tool", "api", "prompt", "midi", "genre", "vibe"]
            for word in english_words:
                part = re.sub(r'\b(' + re.escape(word) + r')\b', r'*\1*', part, flags=re.IGNORECASE)
            formatted_parts.append(part)
    return "".join(formatted_parts)


def send_question_to_chat(question):
    """Callback function to set the question."""
    st.session_state['chat_input_text'] = question

def get_dynamic_suggestions(last_answer: str, lang: str):
    """Menghasilkan saran pertanyaan lanjutan yang dinamis dan kontekstual."""
    
    clean_answer = re.sub(r'(\n\n---\n\*\*Saran.*?:.*?)', '', last_answer, flags=re.DOTALL)
    clean_answer_lower = clean_answer.lower()
    
    user_prompts_history = [
        msg["content"].lower() for msg in st.session_state.messages if msg["role"] == "user"
    ]
    
    dynamic_questions = []
    num_assistant_responses = len([msg for msg in st.session_state.messages if msg["role"] == "assistant"])
    
    # Ekstraksi Elemen Kunci dari Jawaban LLM
    key_match = re.search(r'(kunci|key)\s*[:\-\s]\s*([a-gA-G][b#]?\s*(major|minor|maj|min)?)', clean_answer, re.IGNORECASE)
    key_found = key_match.group(2).strip() if key_match else 'C Major' 
    tempo_match = re.search(r'(tempo)\s*[:\-\s]\s*([a-zA-Z]+\s*\(?\d+\s*BPM\)?)', clean_answer, re.IGNORECASE)
    tempo_found = tempo_match.group(2).strip() if tempo_match else 'Lento'
    
    if lang == "indonesian":
        if num_assistant_responses <= 2:
            # Mode MODIFIKASI LAGU (untuk 1-2 interaksi awal)
            dynamic_questions.append(f"Ubah kunci nada **{key_found}** menjadi kunci *relative minor*.")
            dynamic_questions.append("Bagaimana jika progresi *chord* menggunakan *suspended* dan *add9*?")
            dynamic_questions.append(f"Percepat **tempo {tempo_found}** sebanyak 15 BPM dan ubah *beat* drumnya.")
            dynamic_questions.append("Rancang bagian **Bridge** atau **Coda** dengan emosi yang kontras.")
        else:
            # Mode TOPIK BARU (setelah lagu pertama relatif selesai)
            dynamic_questions.append("Saya ingin lagu tentang **optimisme** di kunci **F Major** dengan *genre Pop Rock*.")
            dynamic_questions.append("Buatkan **progresi chord** yang sempurna untuk *slow-dancing* dengan nuansa *soulful*.")
            dynamic_questions.append("Rancang **komposisi** untuk film *action* dengan tempo cepat dan banyak orkestrasi.")
            dynamic_questions.append("Ide lagu untuk suasana **santai di tepi pantai** dengan instrumentasi minimal.")
            
    else: # English (dipertahankan untuk fleksibilitas)
        if num_assistant_responses <= 2:
            dynamic_questions.append(f"Change the key of **{key_found}** to a *relative minor*.")
            dynamic_questions.append("What if the chord progression uses *suspended* and *add9*?")
            dynamic_questions.append(f"Increase the **tempo {tempo_found}** by 15 BPM and change the drum *beat*.")
            dynamic_questions.append("Design a **Bridge** or **Coda** section with a contrasting emotion.")
        else:
            dynamic_questions.append("I want a song about **optimism** in **F Major** key with a *Pop Rock genre*.")
            dynamic_questions.append("Create the perfect **chord progression** for *slow-dancing* with a *soulful vibe*.")
            dynamic_questions.append("Design a **composition** for an *action movie* with fast tempo and heavy orchestration.")
            dynamic_questions.append("A song idea for a **chilled beach setting** with minimal instrumentation.")

        
    filtered_dynamic = [
        q for q in dynamic_questions if not any(q.lower() in p for p in user_prompts_history)
    ]
    
    all_questions = list(set(filtered_dynamic))
    
    return all_questions[:4]


# --- 1. Konfigurasi Awal & LLM Setup ---
APP_TITLE_PART_2 = "Emotional Composer Bot 🎶" 
try:
    google_api_key = st.secrets.get("google_api_key")
    if not google_api_key:
        st.error("🚨 Kunci Google AI API ('google_api_key') tidak ditemukan di st.secrets.")
        st.stop()
except Exception:
    st.error("🚨 Kunci Google AI API ('google_api_key') tidak ditemukan.")
    st.stop()

# PERBAIKAN KRITIS 1: Inisialisasi LLM di luar blok if/else
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        temperature=0.8 
    )
except Exception as e:
    st.error(f"Error saat menginisialisasi LLM: {e}")
    st.stop()


# --- 2. Page Configuration & Styling ---
st.set_page_config(layout="wide")

css_fix = """
<style>
/* Penyesuaian Agar Chord Sheet Terlihat Sangat Rapi */
.stMarkdown pre {
    white-space: pre-wrap;
    word-break: break-all;
    font-family: monospace;
    line-height: 1.8; 
    background-color: #1f1f1f;
    border: 1px solid #333333;
    padding: 15px; 
    border-radius: 5px;
    overflow-x: auto; 
    font-size: 16px; 
}
.suggestion-chip-container {
    padding: 10px 0; 
    margin-top: 10px; 
    display: flex; 
    flex-wrap: wrap; 
}
.suggestion-chip-container .stButton > button {
    border-radius: 20px;
    background-color: #2b2b2b; 
    border: 1px solid #444444;
    color: #f0f0f0;
    padding: 8px 18px;
    margin: 5px; 
    font-size: 15px;
    transition: background-color 0.2s;
    white-space: nowrap; 
    line-height: 1.2;
}
</style>
"""
st.markdown(css_fix, unsafe_allow_html=True)


col1, col2 = st.columns([3, 1])
with col1:
    st.title(f"**{APP_TITLE_PART_2}**")
    st.caption("Emotional Composition Assistant (Streaming Mode)")
with col2:
    st.write(" ") 
    reset_button = st.button("⟳ New Chat", help="Reset Conversation")


# --- 3. Agent Initialization & State Management ---

if "agent" not in st.session_state:
    try:
        available_tools = [] 
        
        # --- SYSTEM PROMPT ---
        system_prompt = (
            "You are an expert Emotional Composer Agent. Your primary role is to interpret the user's emotions, stories, or mood descriptions "
            "and translate them into a detailed, professional musical composition idea. Your output must include the **key, tempo, mood, primary instruments, a conceptual chord progression, and a detailed musical narrative.**"
            
            "**CRITICAL RULE: YOU MUST RESPOND IN THE SAME LANGUAGE THE USER USED IN THEIR LAST MESSAGE.** "
            
            # Stabilitas & Efisiensi
            "**CRITICAL RULE: CONTEXT COMPRESSION.** After five turns of conversation, you MUST mentally summarize the preceding discussion into a single concise paragraph for internal context, but DO NOT show this summary to the user."
            "**CONSTRAINT:** You cannot generate technical musical notation like tablature, sheet music, or specific note sequences (e.g., C4, E4). Always provide conceptual descriptions instead of technical data."
            
            # PERSYARATAN RITME DAN FEEL
            "**RHYTHMIC REQUIREMENT:** Every composition must specify the **Time Signature** (e.g., 4/4, 3/4) and the overall **Groove/Feel** (e.g., Swing, Straight, Shuffle, Bossa Nova)."
            
            # PERSYARATAN WARNA SUARA DAN DINAMIKA
            "**TIMBRAL REQUIREMENT:** You must specify the **Dynamics** (e.g., *mf, p, f*) and **Specific Instrumental Techniques/Effects** (e.g., *pizzicato strings, flanger effect on guitar, muted brass*) for the primary instruments to achieve the desired emotional color."
            
            # Kualitas Komposisi
            "**STRUCTURAL REQUIREMENT:** Every composition must include a minimum of **[VERSE 1], [CHORUS], dan [BRIDGE]** atau **[CODA]**. Clearly label each section in your response and in the chord sheet."
            "**HARMONIC REQUIREMENT:** To ensure a rich, professional sound, your chord progressions must actively utilize **extensions (e.g., maj7, add9, 11th), suspensions (sus2, sus4), or non-diatonic/altered chords (e.g., V7alt) in at least three different chords.** Explicitly mention the musical impact of these complex chords in your description."
            "**NARRATIVE INTEGRATION MANDATE:** You must explicitly describe **how** the chosen Key, Tempo, Instrumentation, **Groove, and Dynamics** reflect or resolve the user's emotional narrative. Detail the story arc within the music theory."
            
            # Format Kritis
            "**FORMAT RULE 1 (CHORD SHEET - CRITICAL FOR VISUAL ALIGNMENT):** You MUST format the core composition idea using a **lyric/chord sheet style** inside a single Markdown code block (` ``` `)."
            "To achieve perfect alignment: 1. Use a four-line structure: [Section Name], Chord line, Lyric/Description line, and then a blank line. 2. **CHORD LINE:** Use **EXACT SPACES** to position the chord name precisely above the word/syllable. 3. **LYRIC LINE:** Add **EXTRA SPACES** between words (minimum 2 spaces) to visually separate the words."
            
            "Example of required ALIGNED CHORD format:"
            "```"
            "[VERSE 1]"
            "Gm        Cmaj7        F"
            "My  weary  heart  keeps  beating  slow"
            "```"
            
            "Your final response must be creative, evocative, and highly technical in its musical descriptions."
        )
        
        st.session_state.agent = create_react_agent(model=llm, tools=available_tools, prompt=system_prompt)
    except Exception as e:
        st.error(f"Error saat menginisialisasi Agent: {e}")
        st.stop()

if 'chat_input_key' not in st.session_state: st.session_state['chat_input_key'] = time.time() 
if 'chat_input_text' not in st.session_state: st.session_state['chat_input_text'] = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "last_user_language" not in st.session_state: st.session_state["last_user_language"] = "indonesian" 
if "show_suggestion_chips" not in st.session_state: st.session_state["show_suggestion_chips"] = False
if "dynamic_suggestions" not in st.session_state: st.session_state["dynamic_suggestions"] = []
    
if reset_button:
    keys_to_reset = ["agent", "messages", "chat_input_text", "last_user_language", "show_suggestion_chips", "dynamic_suggestions"] 
    for key in keys_to_reset: st.session_state.pop(key, None)
    st.session_state['chat_input_key'] = time.time() 
    st.rerun() 

# --- 4. Display Past Messages ---
st.divider()

if not st.session_state.messages: 
    initial_greeting = (
        "Halo! Saya adalah **Emotional Composer Bot** 🎶. Ceritakanlah tentang **perasaan, kisah, atau suasana hati** yang ingin Anda terjemahkan menjadi musik."
        "Saya akan merancang ide **komposisi** lengkap, disajikan dalam **format lirik/chord sheet** yang rapi. Saya hanya bisa memberikan **deskripsi musikal**."
    )
    with st.chat_message("assistant"):
        st.markdown(initial_greeting)
    st.session_state.messages.append({"role": "assistant", "content": initial_greeting})


for i, msg in enumerate(st.session_state.messages):
    if msg["role"] != "assistant" or i > 0: 
        with st.chat_message(msg["role"]): 
            clean_content = re.sub(r'(\n\n---\n\*\*Saran.*?:.*?)', '', msg["content"], flags=re.DOTALL) 
            clean_content = re.sub(r'(\n\n---\n\*\*Suggestion.*?:.*?)', '', clean_content, flags=re.DOTALL)
            formatted_text = format_assistant_response(clean_content)
            st.markdown(formatted_text)


# --- 5. Handle User Input and Agent Communication (Processing Logic) ---

prompt_from_state = st.session_state.get('chat_input_text', "")
if prompt_from_state:
    prompt = prompt_from_state
    st.session_state['chat_input_text'] = "" 
else:
    prompt = st.chat_input("Describe your mood (e.g., 'melancholy but hopeful') or request an edit...", key=st.session_state['chat_input_key'])


st.session_state["show_suggestion_chips"] = False
st.session_state["dynamic_suggestions"] = []

if prompt:
    
    is_prompt_in_english = re.search(r'\b(the|is|are|you|what|how|why|idea|mood|composition|melody)\b', prompt.lower()) is not None
    st.session_state["last_user_language"] = "english" if is_prompt_in_english else "indonesian"
    
    # Tambahkan prompt ke riwayat SEBELUM streaming dimulai
    st.session_state.messages.append({"role": "user", "content": prompt}) 
    
    with st.chat_message("assistant"): 
        spinner_text = "Composer Agent is translating emotion into music..." if is_prompt_in_english else "Agen Komposer sedang menerjemahkan emosi ke musik..."
            
        with st.spinner(spinner_text):
            
            messages = []
            for msg in st.session_state.messages: 
                clean_content = re.sub(r'(\n\n---\n\*\*Saran.*?:.*?)', '', msg["content"], flags=re.DOTALL) 
                clean_content = re.sub(r'(\n\n---\n\*\*Suggestion.*?:.*?)', '', clean_content, flags=re.DOTALL)
                
                if msg["role"] == "user": messages.append(HumanMessage(content=clean_content))
                elif msg["role"] == "assistant": messages.append(AIMessage(content=clean_content))
            
            # --- PERBAIKAN KRITIS 2: IMPLEMENTASI STREAMING ---
            answer_container = st.empty()
            full_answer = ""
            try:
                # Menggunakan .stream() untuk LangGraph Agent
                stream = st.session_state.agent.stream({"messages": messages})
                
                for chunk in stream:
                    if "messages" in chunk:
                        latest_chunk = chunk["messages"][-1]
                        if isinstance(latest_chunk.content, str):
                            full_answer += latest_chunk.content
                            # Tampilkan progres dengan kursor (▌)
                            answer_container.markdown(format_assistant_response(full_answer + "▌")) 
                
                # Setelah stream selesai, hapus kursor dan tampilkan jawaban final
                final_display_answer = full_answer.replace("▌", "")
                answer_container.markdown(format_assistant_response(final_display_answer)) 
                answer = final_display_answer # Simpan jawaban final untuk logika suggestions

            except Exception as e:
                logging.error(f"LLM streaming failed: {e}")
                answer = f"An error occurred in the Agent: {e}" if is_prompt_in_english else f"Terjadi kesalahan pada *Agent*: {e}"
        
        
        is_informational_answer = not any(kw in answer.lower() for kw in ["gagal", "mohon maaf", "terjadi kesalahan", "sorry", "error", "fail"])
        if is_informational_answer:
            st.session_state["dynamic_suggestions"] = get_dynamic_suggestions(answer, st.session_state["last_user_language"])
            st.session_state["show_suggestion_chips"] = True

        
        message_to_save = {"role": "assistant", "content": answer}
        st.session_state.messages.append(message_to_save)
        
        # 🌟 Trigger Rerun HANYA jika prompt datang dari Chip
        if prompt_from_state: 
            st.session_state['chat_input_key'] = time.time()
            st.rerun()

# --- 6. CHIP PERTANYAAN INTERAKTIF ---

if st.session_state.get("show_suggestion_chips", False) and st.session_state.get("dynamic_suggestions"):
    st.markdown('<div class="suggestion-chip-container">', unsafe_allow_html=True)
    questions = st.session_state["dynamic_suggestions"]
    cols = st.columns(len(questions))
    for i, question in enumerate(questions):
        if i < len(cols):
            with cols[i]:
                st.button(label=question, key=f"final_chip_q_{time.time()}_{i}", on_click=send_question_to_chat, args=[question])
    st.markdown('</div>', unsafe_allow_html=True)