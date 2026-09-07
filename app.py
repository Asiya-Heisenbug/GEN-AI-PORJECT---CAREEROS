import json
import os
from pathlib import Path

import streamlit as st

from ai_analyzer import analyze_comparison, analyze_resume, answer_question
from github_client import fetch_repositories
from jd_analyzer import analyze_job_description
from jd_validator import validate_job_data
from json_validator import validate_resume_data
from resume_parser import extract_text

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "resumes" / "resume_data.json"
JD_DATA_FILE = ROOT / "data" / "job_descriptions" / "job_data.json"

st.set_page_config(page_title="Resume + JD Analyzer", page_icon="🎯", layout="wide")
st.title("Resume + JD Analyzer")
st.caption("Give the AI the whole resume and job description. Compare them, visualize the fit, and ask anything.")

for key, default in {"profile": None, "job": None, "comparison": None, "messages": [], "github": None}.items():
    st.session_state.setdefault(key, default)

with st.sidebar:
    st.header("AI setup")
    st.write("Extraction model")
    st.code(os.getenv("OLLAMA_EXTRACTION_MODEL", "llama3.2"))
    st.write("Matching + chat model")
    st.code(os.getenv("OLLAMA_MATCHING_MODEL", "qwen2.5vl:7b"))
    st.caption("The extraction model creates the JSON files. Qwen only compares them and answers questions.")
    github_value = st.text_input("GitHub username or profile URL", placeholder="octocat")
    if st.button("Load GitHub projects"):
        try:
            st.session_state.github = fetch_repositories(github_value)
            st.success(f"Loaded {len(st.session_state.github['projects'])} repositories.")
        except (OSError, ValueError) as error:
            st.error(f"GitHub could not be loaded: {error}")
    st.divider()
    st.write("**Workflow**")
    st.write("1. Analyze resume\n2. Analyze job description\n3. Compare\n4. Ask questions")

resume_col, jd_col = st.columns(2, gap="large")
with resume_col:
    st.subheader("1. Resume", anchor=False)
    uploaded_file = st.file_uploader("Upload the complete resume", type=["pdf", "docx"], key="resume")
    if uploaded_file and st.button("Analyze full resume", type="primary", use_container_width=True):
        with st.spinner("Reading every page and analyzing the complete resume..."):
            try:
                text = extract_text(uploaded_file)
                result = analyze_resume(text)
                st.session_state.profile = validate_resume_data(result)
                DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
                DATA_FILE.write_text(json.dumps(st.session_state.profile, indent=2), encoding="utf-8")
                st.session_state.comparison = None
                st.success("Resume analyzed and saved as structured JSON.")
            except (RuntimeError, ValueError, TimeoutError) as error:
                st.error(str(error))
    if st.session_state.profile:
        profile = st.session_state.profile
        personal = profile.get("personal", profile)
        st.info(f"**{personal.get('name') or profile.get('name') or 'Candidate'}**\n\n{profile.get('summary') or profile.get('resume_summary') or 'Profile extracted.'}")
        with st.expander("View complete extracted profile"):
            st.json(profile)

with jd_col:
    st.subheader("2. Job description", anchor=False)
    jd_text = st.text_area("Paste the complete JD", height=235, placeholder="Paste every section of the job description here...", key="jd")
    if st.button("Analyze full job description", type="primary", use_container_width=True):
        if not jd_text.strip():
            st.warning("Paste the job description first.")
        else:
            with st.spinner("Analyzing every requirement and responsibility..."):
                try:
                    result = analyze_job_description(jd_text)
                    st.session_state.job = validate_job_data(result)
                    JD_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
                    JD_DATA_FILE.write_text(json.dumps(st.session_state.job, indent=2), encoding="utf-8")
                    st.session_state.comparison = None
                    st.success("Job description analyzed.")
                except (RuntimeError, ValueError) as error:
                    st.error(str(error))
    if st.session_state.job:
        job = st.session_state.job
        st.info(f"**{job.get('job_title') or job.get('role') or 'Target role'}** at {job.get('company') or 'Company not specified'}\n\n{job.get('summary') or 'Job requirements extracted.'}")
        with st.expander("View complete extracted job"):
            st.json(job)

if st.session_state.profile and st.session_state.job:
    st.divider()
    st.header("3. Side-by-side fit analysis")
    if st.button("Compare resume against this JD", type="primary"):
        with st.spinner("Comparing the complete candidate profile against the complete job..."):
            try:
                st.session_state.comparison = analyze_comparison(
                    st.session_state.profile,
                    st.session_state.job,
                    st.session_state.github,
                )
            except (RuntimeError, ValueError) as error:
                st.error(str(error))

    comparison = st.session_state.comparison
    if comparison:
        score = int(comparison.get("overall_fit_score", comparison.get("match_score", 0)) or 0)
        st.metric("Overall fit", f"{score}%")
        left, right = st.columns(2)
        with left:
            st.subheader("Candidate evidence", anchor=False)
            st.write(comparison.get("strongest_evidence", comparison.get("matched_skills", [])))
            st.subheader("Recommended projects", anchor=False)
            st.write(comparison.get("recommended_projects", []))
        with right:
            st.subheader("Job gaps", anchor=False)
            st.write(comparison.get("gaps", comparison.get("missing_skills", [])))
            st.subheader("Interview topics", anchor=False)
            st.write(comparison.get("interview_topics", []))

        chart_data = {"Matched": len(comparison.get("matched_skills", [])), "Partial": len(comparison.get("partial_matches", [])), "Missing": len(comparison.get("missing_skills", []))}
        st.subheader("Skill coverage", anchor=False)
        st.bar_chart(chart_data, horizontal=True)
        st.write(comparison.get("explanation", ""))
        if st.session_state.github:
            with st.expander("GitHub projects used for recommendations"):
                for project in st.session_state.github.get("projects", []):
                    st.write(f"**{project['name']}** · {project['language'] or 'No language'} — {project['description'] or 'No description'}")

        st.divider()
        st.header("4. Ask anything about you + this job")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        question = st.chat_input("Am I suitable? What am I missing? Which project should I mention?")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                with st.spinner("Searching your resume, this JD, and the comparison..."):
                    try:
                        answer = answer_question(question, st.session_state.profile, st.session_state.job, comparison, st.session_state.github)
                    except (RuntimeError, ValueError) as error:
                        answer = f"I could not query Ollama: {error}"
                st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
else:
    st.divider()
    st.info("Analyze both the resume and job description to unlock side-by-side charts and Career AI chat.")
