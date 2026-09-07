# Resume Analyzer

A small Streamlit application that analyzes resumes and job descriptions with a local Ollama model.

The app provides separate tabs for resume analysis and job-description analysis. JD results include
technical skills, soft skills, responsibilities, qualifications, certifications, and searchable keywords.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Install Ollama, start it with `ollama serve`, and download both models:

   ```powershell
   ollama pull llama3.2
   ollama pull qwen2.5vl:7b
   ```

   The model and Ollama URL are configured in `.env`.
4. Start the app:

   ```powershell
   streamlit run app.py
   ```

## Streamlit Community Cloud

1. Create an app from this GitHub repository, using `main` as the branch and `app.py` as the main file.
2. In the app settings, add these secrets with values for a publicly reachable Ollama-compatible service:

   ```toml
   OLLAMA_HOST = "https://your-ollama-host.example.com"
   OLLAMA_EXTRACTION_MODEL = "llama3.2"
   OLLAMA_MATCHING_MODEL = "qwen2.5vl:7b"
   OLLAMA_TIMEOUT_SECONDS = "900"
   ```

   Streamlit Cloud cannot access Ollama running on your personal computer at `localhost:11434`.

`llama3.2` extracts the resume and JD into JSON. `qwen2.5vl:7b` receives those JSON files for
matching, charts, explanations, and chatbot questions. The latest validated result is stored in `data/resumes/resume_data.json`.
Job-description results are stored in `data/job_descriptions/job_data.json`.
