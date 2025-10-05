# emotional_composer_agent

# Import Pustaka
import streamlit as st
import time
import re 
import logging 
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool 
import json
import os 
from typing import List, Dict, Any 

# 🌟 IMPOR FUNGSI DATABASE DARI FILE TERPISAH 🌟
from database_tools import save_suggestion_history 

# Konfigurasi logging dasar
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='agent_composer_narrative.log', filemode='a')


# --- 0. Utility Functions ---

def format_assistant_response(text: str) -> str:
    """Mengaplikasikan formatting BOLD untuk poin penting dan ITALIC untuk kata Inggris umum, KECUALI di dalam blok kode."""
    # ... (fungsi ini tidak berubah dari perbaikan sebelumnya)
    parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)
    formatted_parts = []
    for part in parts:
        if part.startswith('```') and part.endswith('```'):
            formatted_parts.append(part)
        else:
            keywords_to_bold = ["komposisi", "melodi", "chord", "instrumentasi", "tempo", "emosi", "kunci", "composition", "melody", "key", "tempo", "instrumentation", "emotion", "struktur", "progresi", "genre", "dynamics", "groove"]
            for keyword in keywords_to_bold:
                # Menggunakan boundary \b untuk menghindari bolding di dalam kata lain
                part = re.sub(r'\b(' + re.escape(keyword) + r')\b', r'**\1**', part, flags=re.IGNORECASE)
            english_words = ["rag", "agent", "tool", "api", "prompt", "midi", "genre", "vibe", "groove", "dynamics", "beat", "solo"]
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
    # Dapatkan jumlah balasan asisten yang substantif (setelah pesan pembuka)
    num_assistant_responses = len([msg for msg in st.session_state.messages if msg["role"] == "assistant"]) - 1
    if num_assistant_responses < 0: num_assistant_responses = 0
    
    # PERBAIKAN KRITIS: Dapatkan status has_chord_sheet di sini.
    has_chord_sheet = "```" in clean_answer or any("```" in msg["content"] for msg in st.session_state.messages if msg["role"] == "assistant")
    is_musical_composition_phase = has_chord_sheet

    # Ekstraksi Elemen Kunci dari Jawaban LLM (Hanya dilakukan jika sudah ada output musik)
    key_found = 'C Major'
    tempo_found = 'Lento'
    
    if is_musical_composition_phase:
        # Pengecekan pada jawaban terbaru (last_answer) untuk akurasi
        key_match = re.search(r'(kunci|key)\s*[:\-\s]\s*([a-gA-G][b#]?\s*(major|minor|maj|min)?)', clean_answer, re.IGNORECASE)
        key_found = key_match.group(2).strip() if key_match else 'C Major' 
        tempo_match = re.search(r'(tempo)\s*[:\-\s]\s*([a-zA-Z]+\s*\(?\d+\s*BPM\)?)', clean_answer, re.IGNORECASE)
        tempo_found = tempo_match.group(2).strip() if tempo_match else 'Lento'


    # === LOGIKA SARAN YANG DINAMIS BERDASARKAN FASE ===
    
    # Batas Transisi Diperpanjang: Memberikan lebih banyak ruang untuk modifikasi satu lagu.
    TRANSITION_THRESHOLD = 7 # Akan pindah ke Fase 3 setelah balasan asisten ke-8 (num_assistant_responses > 7)
    
    if lang == "indonesian":
        
        if not is_musical_composition_phase:
            # FASE 1: NARATIF / EMOSIONAL / PENDAMPING (Belum ada komposisi)
            dynamic_questions.extend([
                "Saya sedang merasa **kebingungan**, coba terjemahkan ke dalam musik.",
                "Tolong buatkan **melodi** yang mengekspresikan **kerinduan yang mendalam**.",
                "Saya ingin lagu tentang **perasaan damai** setelah badai.",
                "Ide **komposisi** untuk film dokumenter tentang luar angkasa.",
                "Apa saja **genre** yang bisa Anda bantu rancang?",
                "Saran komposisi untuk adegan **misterius** dan penuh ketegangan.",
            ])
        
        elif num_assistant_responses <= TRANSITION_THRESHOLD:
            # FASE 2: MODIFIKASI LAGU (Konteks musikal jelas, dan masih fokus pada satu lagu)
            dynamic_questions.extend([
                f"Ubah **kunci nada {key_found}** menjadi kunci *relative minor*.",
                "Bagaimana jika progresi *chord* menggunakan ***suspended* dan *add9***?",
                f"Percepat **tempo {tempo_found}** sebanyak 15 BPM dan ubah *beat* drumnya.",
                "Rancang bagian **Bridge** atau **Coda** dengan **emosi** yang kontras.",
                "Tambahkan **perkusi** yang lebih ritmis, seperti *Latin beat* atau *funk*.",
                "Ganti **instrumentasi** utama menjadi piano solo dan strings.",
                "Bagaimana cara membuat *progresi chord* ini terdengar lebih **minor dan gelap**?",
            ])
        else:
            # FASE 3: TOPIK BARU / MODIFIKASI LANJUT (Diskusi sudah panjang, saatnya pindah lagu, tapi tetap fleksibel)
            dynamic_questions.extend([
                "Saya ingin lagu tentang **optimisme** di kunci **F Major** dengan *genre Pop Rock*.",
                "Rancang **soundtrack** untuk suasana **kota yang sibuk** di malam hari (key Bb minor).",
                "Buatkan **progresi chord** yang sempurna untuk *slow-dancing* dengan nuansa *soulful*.",
                "Ide **lagu tidur** dengan instrumentasi minimalis dan nuansa hangat.",
                "Bagaimana jika kita buat versi **akustik** dari komposisi yang tadi?", # Opsi modifikasi umum
                "Buatkan saya *jingle* yang **ceria dan mudah diingat**.",
            ])
            
    else: # English (Logika serupa untuk Bahasa Inggris)
        
        if not is_musical_composition_phase:
            # FASE 1: NARRATIVE / EMOTIONAL / GUIDANCE
            dynamic_questions.extend([
                "I'm feeling **confused**, try translating it into music.",
                "Please create a **melody** that expresses **deep longing**.",
                "I want a song about the **feeling of peace** after a storm.",
                "A **composition** idea for a documentary about outer space.",
                "What **genres** can you help me design?",
                "Suggest a composition for a **mysterious** and tense scene.",
            ])
            
        elif num_assistant_responses <= TRANSITION_THRESHOLD:
            # FASE 2: SONG MODIFICATION
            dynamic_questions.extend([
                f"Change the key of **{key_found}** to a *relative minor*.",
                "What if the chord progression uses **suspended and add9**?",
                f"Increase the **tempo {tempo_found}** by 15 BPM and change the drum *beat*.",
                "Design a **Bridge** or **Coda** section with a contrasting emotion.",
                "Add more rhythmic **percussion**, like a *Latin beat* or *funk*.",
                "Change the main **instrumentation** to a solo piano and strings.",
                "How can I make this *chord progression* sound more **minor and dark**?",
            ])
        else: 
            # FASE 3: NEW TOPIC / ADVANCED MODIFICATION
            dynamic_questions.extend([
                "I want a song about **optimism** in **F Major** key with a *Pop Rock genre*.",
                "Design a **soundtrack** for a **busy city** at night (key Bb minor).",
                "Create the perfect **chord progression** for *slow-dancing* with a *soulful vibe*.",
                "An idea for a **lullaby** with minimalist instrumentation and a warm feel.",
                "What if we create an **acoustic** version of the previous composition?",
                "Make me an **upbeat and memorable** *jingle*.",
            ])

        
    filtered_dynamic = [
        q for q in dynamic_questions if not any(q.lower() in p for p in user_prompts_history)
    ]
    
    # Ambil 4 saran terbaik yang unik
    all_questions = list(set(filtered_dynamic))
    
    return all_questions[:4]


# --- 1. Konfigurasi Awal & LLM Setup ---
APP_TITLE_PART_2 = "Emotional Composer Bot 🎶" 
try:
    # PERHATIAN: Pastikan Anda telah membuat file .streamlit/secrets.toml
    google_api_key = st.secrets.get("google_api_key")
    if not google_api_key:
        st.error("🚨 Kunci Google AI API ('google_api_key') tidak ditemukan di st.secrets.")
        st.stop()
except Exception:
    st.error("🚨 Kunci Google AI API ('google_api_key') tidak ditemukan.")
    st.stop()

# Inisialisasi LLM
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
        
        # --- SYSTEM PROMPT DENGAN PENINGKATAN KUALITAS OUTPUT ---
        system_prompt = (
            "You are an expert Emotional Composer Agent. Your primary role is to interpret the user's emotions, stories, or mood descriptions "
            "and translate them into a detailed, professional musical composition idea. Your output must include the **key, tempo, mood, primary instruments, a conceptual chord progression, and a detailed musical narrative.**"
            
            "**CRITICAL RULE: YOU MUST RESPOND IN THE SAME LANGUAGE THE USER USED IN THEIR LAST MESSAGE.** "
            
            "**CRITICAL RULE: STRICT ADHERENCE** You must strictly adhere to ALL formatting rules and musical requirements below. **DO NOT generate content that violates the rules.**"
            "**CONSTRAINT:** You cannot generate technical musical notation like tablature, sheet music, or specific note sequences (e.g., C4, E4). Always provide conceptual descriptions instead of technical data."
            
            "**RHYTHMIC REQUIREMENT:** Every composition must specify the **Time Signature** (e.g., 4/4, 3/4) and the overall **Groove/Feel** (e.g., Swing, Straight, Shuffle, Bossa Nova)."
            "**TIMBRAL REQUIREMENT:** You must specify the **Dynamics** (e.g., *mf, p, f*) and **Specific Instrumental Techniques/Effects** (e.g., *pizzicato strings, flanger effect on guitar, muted brass*) for the primary instruments to achieve the desired emotional color."
            "**STRUCTURAL REQUIREMENT:** Every composition must include a minimum of **[VERSE 1], [CHORUS], dan [BRIDGE]** atau **[CODA]**. Clearly label each section in your response and in the chord sheet."
            "**HARMONIC REQUIREMENT:** To ensure a rich, professional sound, your chord progressions must actively utilize **extensions (e.g., maj7, add9, 11th), suspensions (sus2, sus4), or non-diatonic/altered chords (e.g., V7alt) in at least three different chords.** Explicitly mention the musical impact of these complex chords in your description."
            "**NARRATIVE INTEGRATION MANDATE:** You must explicitly describe **how** the chosen Key, Tempo, Instrumentation, **Groove, and Dynamics** reflect or resolve the user's emotional narrative. Detail the story arc within the music theory."
            
            "**FORMAT RULE 1 (CHORD SHEET - CRITICAL FOR VISUAL ALIGNMENT):** You MUST format the core composition idea using a **lyric/chord sheet style** inside a single Markdown code block (` ``` `). **This code block MUST appear at the very end of your response, after all narrative descriptions.**"
            "To achieve perfect alignment: 1. Use a four-line structure: [Section Name], Chord line, Lyric/Description line, and then a blank line. 2. **CHORD LINE:** Use **MINIMAL 4 SPACES** untuk memposisikan nama chord tepat di atas kata/suku kata. 3. **LYRIC LINE:** Tambahkan **SPASI EKSTRA** di antara kata (minimal 2 spasi) untuk memisahkan kata secara visual."
            
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
if "dynamic_suggestions" not in st.session_state: st.session_state["dynamic_suggestions"] = []
    
if reset_button:
    keys_to_reset = ["agent", "messages", "chat_input_text", "last_user_language", "dynamic_suggestions"] 
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


# Loop tampilan riwayat
for i, msg in enumerate(st.session_state.messages):
    # Logika untuk menghindari duplikasi pesan pembuka
    if i == 0 and len(st.session_state.messages) > 1 and msg["role"] == "assistant":
        continue
    
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


st.session_state["dynamic_suggestions"] = []

if prompt:
    
    # PERBAIKAN: Deteksi bahasa yang lebih baik (heuristik yang diperluas)
    english_keywords = ["the", "is", "are", "you", "what", "how", "why", "idea", "mood", "composition", "melody", "change", "key", "tempo"]
    prompt_words = prompt.lower().split()
    english_word_count = sum(1 for word in prompt_words if word in english_keywords)
    is_prompt_in_english = english_word_count > (len(prompt_words) / 3) 
    st.session_state["last_user_language"] = "english" if is_prompt_in_english else "indonesian"
    
    # Tampilkan prompt pengguna di chat SEBELUM proses agent dimulai
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Tambahkan prompt ke riwayat SEBELUM streaming dimulai
    st.session_state.messages.append({"role": "user", "content": prompt}) 
    
    with st.chat_message("assistant"): 
        
        # 🌟 LOGIKA PERBAIKAN SPINNER (Menggunakan Logic yang Ditingkatkan) 🌟
        
        # 1. Cek apakah sudah ada output komposisi (kode block) di riwayat
        has_chord_sheet = any("```" in msg["content"] for msg in st.session_state.messages if msg["role"] == "assistant")
        
        # 2. Hitung jumlah balasan asisten sejak awal (untuk menentukan panjang diskusi)
        num_assistant_responses = len([msg for msg in st.session_state.messages if msg["role"] == "assistant"])
        if num_assistant_responses > 0 and st.session_state.messages[0]["role"] == "assistant":
             num_assistant_responses -= 1 # Abaikan salam awal

        
        # Kriteria untuk menggunakan Spinner Musikal Spesifik:
        is_musical_focus_phase = has_chord_sheet and num_assistant_responses <= 7 


        if is_musical_focus_phase:
            # Spinner spesifik tentang musik (modifikasi/lanjutan)
            if st.session_state["last_user_language"] == "english":
                spinner_text = "Composer Agent is translating emotion into music..."
            else:
                spinner_text = "Agen Komposer sedang menerjemahkan emosi ke musik..."
        else:
            # Spinner umum untuk percakapan naratif/non-musikal/topik baru
            if st.session_state["last_user_language"] == "english":
                spinner_text = "Analyzing your request, please wait..."
            else:
                spinner_text = "Menganalisa permintaan Anda, mohon tunggu..."
        # 🌟 AKHIR LOGIKA PERBAIKAN SPINNER 🌟

        with st.spinner(spinner_text):
            
            messages = []
            for msg in st.session_state.messages: 
                # Pastikan menghapus saran dari riwayat sebelum dikirim ke LLM
                clean_content = re.sub(r'(\n\n---\n\*\*Saran.*?:.*?)', '', msg["content"], flags=re.DOTALL) 
                clean_content = re.sub(r'(\n\n---\n\*\*Suggestion.*?:.*?)', '', clean_content, flags=re.DOTALL)
                
                if msg["role"] == "user": messages.append(HumanMessage(content=clean_content))
                elif msg["role"] == "assistant": messages.append(AIMessage(content=clean_content))
            
            # 🌟 IMPLEMENTASI STREAMING & FALLBACK 🌟
            answer_container = st.empty()
            full_answer = ""
            answer = "" 
            
            try:
                # --- FASE 1: STREAMING (Dioptimalkan untuk LangGraph) ---
                stream = st.session_state.agent.stream({"messages": messages})
                
                for chunk in stream:
                    if "messages" in chunk:
                        latest_chunk = chunk["messages"][-1]
                        
                        # Filter ketat: Hanya terima AIMessage yang bukan Tool Calls
                        if isinstance(latest_chunk, AIMessage) and not latest_chunk.tool_calls and not latest_chunk.tool_responses:
                            content = latest_chunk.content
                            
                            # Pastikan konten adalah string non-kosong
                            if isinstance(content, str) and content.strip(): 
                                full_answer += content
                                answer_container.markdown(format_assistant_response(full_answer + "▌")) 
                            
                # Hapus kursor setelah stream selesai
                answer = full_answer.replace("▌", "").strip()

            except Exception as e:
                logging.error(f"LLM streaming failed: {e}. Trying fallback...")
                answer = "" 
            
            # --- FASE 2: FALLBACK (Jika streaming gagal atau kosong) ---
            # PERBAIKAN: Jika streaming menghasilkan jawaban terlalu pendek, anggap gagal dan coba fallback.
            if not answer or len(answer) < 50: 
                logging.info(f"Answer too short ({len(answer)} chars) or empty. Trying fallback.")
                try:
                    response = st.session_state.agent.invoke({"messages": messages})
                    if "messages" in response and response["messages"]:
                        fallback_message = response["messages"][-1]
                        if isinstance(fallback_message, AIMessage) and fallback_message.content:
                            answer = fallback_message.content.strip()
                        else:
                            answer = "Agent produced non-text or empty output (Fallback mode)."
                    else:
                        answer = "Agent produced no messages (Fallback mode)."
                except Exception as e:
                    logging.error(f"LLM Fallback failed: {e}")
                    is_english = st.session_state["last_user_language"] == "english"
                    answer = (
                        f"**[AGENT FAILURE]** Both streaming and fallback failed: {e}. Please use 'New Chat'." 
                        if is_english 
                        else f"**[KEGAGALAN AGEN]** Streaming dan fallback gagal: {e}. Mohon gunakan 'New Chat'."
                    )
            
            # Tampilkan Jawaban Final (setelah streaming atau fallback)
            is_english = st.session_state["last_user_language"] == "english"
            
            if answer.startswith("**[AGENT FAILURE]**") or answer.startswith("**[KEGAGALAN AGEN]**"):
                 # Tampilkan pesan error jika terjadi kegagalan total
                 answer_container.markdown(format_assistant_response(answer))
            elif not answer or len(answer) < 50: # Pengecekan final setelah fallback
                # Tampilkan pesan error yang lebih jelas jika output tetap kosong
                final_error = (
                    f"**[ERROR RESPONS AGEN]** {spinner_text} failed to produce output. Please try rephrasing your request or clicking 'New Chat'." 
                    if is_english 
                    else f"**[ERROR RESPONS AGEN]** {spinner_text} gagal menghasilkan output. Mohon coba ulangi pertanyaan Anda atau klik 'New Chat'."
                )
                answer = final_error
                answer_container.markdown(format_assistant_response(answer))
            else:
                # Jika ada jawaban yang valid, tampilkan
                answer_container.markdown(format_assistant_response(answer)) 

        
        
        is_informational_answer = not any(kw in answer.lower() for kw in ["gagal", "mohon maaf", "terjadi kesalahan", "sorry", "error", "fail", "failure", "kegagalan"])
        
        # LOGIKA SUGGESTION CHIPS: Hanya tampilkan jika jawaban substantif 
        if is_informational_answer and len(answer) > 100:
            st.session_state["dynamic_suggestions"] = get_dynamic_suggestions(answer, st.session_state["last_user_language"])
            
            if st.session_state["dynamic_suggestions"]:
                # 🌟 MENGGUNAKAN FUNGSI DARI FILE TERPISAH 🌟
                save_suggestion_history(
                    user_prompt=prompt, 
                    assistant_response=answer, 
                    suggestions=st.session_state["dynamic_suggestions"]
                )
        else:
            st.session_state["dynamic_suggestions"] = [] # Pastikan kosong jika tidak ada saran
        
        message_to_save = {"role": "assistant", "content": answer}
        st.session_state.messages.append(message_to_save)
        
        # 🌟 Trigger Rerun HANYA jika prompt datang dari Chip
        if prompt_from_state: 
            st.session_state['chat_input_key'] = time.time()
            st.rerun()

# --- 6. CHIP PERTANYAAN INTERAKTIF ---

if st.session_state.get("dynamic_suggestions"):
    st.markdown('<div class="suggestion-chip-container">', unsafe_allow_html=True)
    questions = st.session_state["dynamic_suggestions"]
    cols = st.columns(len(questions))
    for i, question in enumerate(questions):
        if i < len(cols):
            with cols[i]:
                st.button(label=question, key=f"final_chip_q_{hash(question)}_{i}", on_click=send_question_to_chat, args=[question])
    st.markdown('</div>', unsafe_allow_html=True)