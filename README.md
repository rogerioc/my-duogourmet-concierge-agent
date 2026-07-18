---
title: Duo Concierge
emoji: 🍽️
colorFrom: amber
colorTo: slate
sdk: gradio
sdk_version: 6.2.0
app_file: DuoSmolAgent/app.py
pinned: false
---

# 🍽️ Duo Concierge

This is **Duo Concierge**, a project hosting AI agents specialized in recommending and validating restaurants for the Duo Gourmet program in Belo Horizonte (BH) and São Paulo (SP).

It is built on top of the **DuoList BH & SP** interactive map ([Live Map](https://rogerioc.github.io/my-duogourmet-map/) | [GitHub Repo](https://github.com/rogerioc/my-duogourmet-map)).

🤖 **AI-Built Project**: This entire project was developed and orchestrated by **Google Antigravity** (Google DeepMind's agentic coding AI assistant). The detailed execution plan followed during construction can be found in the [AGENT_PLAN.md](AGENT_PLAN.md) file.

---

## 👥 Meet the Agents

The codebase contains **two different agent architectures** sharing a common core logic:

### 1. DuoGeminiAgent (Streamlit + Gemini API)
* **Technology**: Built using Python, Streamlit, and the `google-genai` SDK.
* **Model**: `gemini-2.5-flash`
* **Features**: Dynamic Leaflet map picker for location, timezone detector component, and simulation parameters panel.
* **How to run locally**:
  ```bash
  pip install -r requirements.txt
  streamlit run DuoGeminiAgent/app.py
  ```

### 2. DuoSmolAgent (Gradio + smolagents)
* **Technology**: Built using Python, Gradio, and Hugging Face's `smolagents` library.
* **Model**: `Qwen/Qwen2.5-Coder-32B-Instruct` (Inference API)
* **Features**: Sleek Gradio Chatbot displaying execution logs, reactive browser-based GPS/Timezone detection via JS, and optimized prompts for Hugging Face Spaces.
* **How to run locally**:
  ```bash
  conda activate duogourmet-env
  pip install -r DuoSmolAgent/requirements.txt
  python DuoSmolAgent/app.py
  ```

---

## 📁 File Structure

The project is modularized to avoid code duplication:

* **`data/`**: Central folder containing database JSON files (`restaurantes_bh.json`, `restaurantes_sp.json`).
* **`common/`**: Shared Python library used by both agents.
  * `database.py` - Lazy loading of database files.
  * `geo.py` - Distance calculation using the Haversine formula.
  * `utils.py` - String normalizers and date/time parsers.
  * `tools.py` - Pure Python functions for restaurant search and availability checks.
* **`DuoGeminiAgent/`**: Code specific to the Streamlit Gemini agent.
  * `app.py` - Streamlit UI wrapper.
  * `agent_core.py` - Custom ReAct loop using `google-genai` SDK.
  * `location_picker.py` - Streamlit wrappers for custom components.
  * `gps_component/` & `timezone_component/` - Custom HTML/JS Streamlit components.
* **`DuoSmolAgent/`**: Code specific to the Hugging Face smolagent.
  * `app.py` - Gradio app entrypoint and agent configuration.
  * `Gradio_UI.py` - Custom Gradio dashboard, JS scripts, and chatbot wrappers.
  * `tools.py` - wrappers exposing `common.tools` as `@tool` for `smolagents`.
  * `prompts.yaml` - System prompts guiding Qwen's behavior.

---

## 🔑 Setup & Configuration

* **For DuoGeminiAgent**: You will need a **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/). Enter it in the Streamlit sidebar.
* **For DuoSmolAgent**: You will need a Hugging Face Hub token (`HF_TOKEN`) saved in `DuoSmolAgent/.env` to avoid rate limits on the Inference API.
