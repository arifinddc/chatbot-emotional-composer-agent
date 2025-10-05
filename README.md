# Emotional Composer Bot 🎶

> Hello! I'm the **Emotional Composer Bot** 🎶. Tell me about the feelings, stories, or mood you want to translate into music. I will design a complete composition idea for you, presented in a neat lyric/chord sheet format. I can only provide musical descriptions, not technical notation.

---

## 1. Target Audience

The project is designed for a diverse creative community:

* **Amateur Songwriters and Musicians** seeking music theory inspiration or a starting point for new songs, especially when facing *writer's block*.
* **Creative Industry Professionals** like **sound designers** and **content creators** who require precise, technical musical specifications for film, game, or podcast projects.

---

## 2. Core Functionality (How the Chatbot Helps)

The chatbot functions as a **"Co-Composer" AI** to enhance the creative workflow:

* It translates **narrative emotions** (e.g., 'melancholy but hopeful') into **structured and technical music composition specifications** (key, tempo, dynamics, complex chord progressions).
* It provides **contextual modification suggestions** (e.g., "Change key to relative minor") to help users iteratively develop and refine the initial idea.

---

## 3. The Role of the AI Agent

The AI operates as an **Expert Composer Agent** with three critical roles:

* The agent is tasked with translating user emotions and narratives into **structured theoretical music specifications** that adhere to strict formatting rules.
* It ensures the output is technically sound, incorporating required elements like **extended chords** and **timbral techniques**.
* It manages a **smart conversational flow** (through contextual *spinner* logic and follow-up suggestions) to maintain focus on the current musical idea.

---

## 4. Technology Stack (AI Model & Frameworks)

The application is built on a modern AI stack focused on reliability and structured output:

* **Primary AI Model:** **Gemini 2.5 Flash** is the core model, chosen for its speed and ability to adhere to complex, multi-step instructions (crucial for the *chord sheet* format).
* **Integration:** The model is integrated via the **LangChain Google Generative AI** library (`ChatGoogleGenerativeAI`).
* **Orchestration:** The conversational logic and state management are orchestrated using the **LangGraph** framework (`create_react_agent`), ensuring the agent follows the defined composition workflow.
* **Database:** Uses a decoupled **SQLite** file (`database_tools.py`) to save suggestion history.
* **Frontend:** **Streamlit** is used for the interactive web interface.

***

### How to Run Locally

1.  **Clone the Repository:**
    ```bash
    git clone [YOUR_REPO_URL]
    cd emotional-composer-bot
    ```
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Setup API Key:** Create a folder named `.streamlit` in the project root and add a file named `secrets.toml` inside it:
    ```toml
    # .streamlit/secrets.toml
    google_api_key="YOUR_GEMINI_API_KEY_HERE"
    ```
4.  **Run the Application:**
    ```bash
    streamlit run emotional_composer_agent.py
    ```
