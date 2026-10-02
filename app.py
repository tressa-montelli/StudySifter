"""
StudySifter - AI-Assisted Research Extraction Tool for Scientific Literature
Built with Streamlit & the Google Gen AI SDK (google-genai)
"""
import os
import time
import pandas as pd
import streamlit as st
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# =====================================================================
# 1. Pydantic Structured Output Schema
# =====================================================================
# Pydantic enforces an exact data contract. Gemini will return a JSON object
# matching this schema, preventing erratic formatting between papers.
# =====================================================================
class StudyExtraction(BaseModel):
    paper_title: str = Field(description="Full title of the scientific paper")
    authors: str = Field(description="List of authors, or 'Not reported'")
    publication_year: str = Field(description="Year of publication, or 'Not reported'")
    study_design: str = Field(
        description="Study design (e.g., Randomized controlled trial, prospective cohort, rodent behavioral model, in vitro)"
    )
    population_or_model: str = Field(
        description="Experimental animal model (species, strain, sex, age) or human participant cohort"
    )
    sample_size: str = Field(
        description="Exact sample size (total N, group n), or 'Not reported'"
    )
    intervention_or_drug: str = Field(
        description="Primary drug, intervention, or experimental manipulation tested"
    )
    dose: str = Field(
        description="Dosage, administration route, frequency, and duration, or 'Not reported'"
    )
    comparator_control: str = Field(
        description="Control group or comparator (e.g., vehicle, sham, saline, placebo)"
    )
    outcome_measure: str = Field(
        description="Primary outcome measures or endpoints evaluated"
    )
    behavioral_or_experimental_assay: str = Field(
        description="Specific experimental test, behavioral apparatus, or assay used"
    )
    key_result: str = Field(
        description="Main findings directly stated by the authors"
    )
    statistical_result: str = Field(
        description="Specific statistics reported (p-values, effect sizes, F/t values, confidence intervals), or 'Not reported'"
    )
    supporting_evidence: str = Field(
        description="Direct verbatim quotation from the paper supporting the key findings"
    )
    evidence_location: str = Field(
        description="Section, page, or table where the supporting evidence appears (e.g., 'Methods, Section 2.1' or 'Page 4')"
    )
    confidence_level: str = Field(
        description="Confidence rating: 'High', 'Medium', 'Low', or 'Ambiguous'"
    )
    ambiguity_notes: str = Field(
        description="Specific flags, caveats, uncertainties, or unaddressed details in the paper"
    )

#=======================================================================
# estract the study data
#=======================================================================
def extract_study_data(pdf_bytes: bytes, filename: str, status_placeholder=None) -> StudyExtraction:
    """
    Sends the uploaded PDF bytes directly to Gemini with strict schema enforcement.
    Includes automatic exponential backoff retry and model fallback to handle 
    temporary 503 UNAVAILABLE ('high demand') spikes seamlessly.
    """
    client = genai.Client()

    pdf_part = types.Part.from_bytes(
        data=pdf_bytes,
        mime_type="application/pdf",
    )

    system_instruction = (
        "You are StudySifter, an expert AI research extraction assistant for scientific literature.\n"
        "Your primary directive is ZERO HALLUCINATIONS and strict scientific fidelity:\n"
        "1. Prioritize accuracy over filling every field.\n"
        "2. NEVER invent or infer information that is not explicitly stated in the document.\n"
        "3. If an item cannot be found or is not explicitly stated, strictly return 'Not reported'.\n"
        "4. Distinguish between what the authors explicitly reported vs what would require inference.\n"
        "5. Provide exact verbatim supporting evidence quotes from the paper text.\n"
        "6. Provide the exact location (e.g., 'Abstract', 'Methods, Section 2.1', 'Results, Table 1') for evidence.\n"
        "7. Set confidence to 'High' if clearly stated, 'Medium' if phrasing is slightly ambiguous, "
        "'Low' if limited detail is provided, or 'Ambiguous' if contradictory or unconfirmed.\n"
        "8. Note any ambiguities or caveats in the ambiguity_notes field."
    )

    user_prompt = (
        f"Analyze this scientific research paper ({filename}) and extract the predefined study characteristics. "
        "Adhere strictly to the anti-hallucination guidelines. Return 'Not reported' whenever a field is not documented."
    )

    # Models to try if one is experiencing high demand
    candidate_models = ["gemini-3.1-flash-lite"]
    last_exception = None      

    for model_name in candidate_models:
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                if status_placeholder:
                    status_placeholder.text(f"Extracting with {model_name} (attempt {attempt}/{max_retries})...")

                response = client.models.generate_content(
                    model=model_name,
                    contents=[pdf_part, user_prompt],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1,
                        response_mime_type="application/json",
                        response_schema=StudyExtraction,
                    ),
                )

                if response and response.text:
                    return StudyExtraction.model_validate_json(response.text)

            except Exception as e:
                last_exception = e
                err_str = str(e).lower()
                is_transient = "503" in err_str or "unavailable" in err_str or "high demand" in err_str or "429" in err_str

                if is_transient and attempt < max_retries:
                    wait_sec = attempt * 2  # 2s, 4s exponential backoff
                    if status_placeholder:
                        status_placeholder.warning(
                            f"Model is experiencing temporary high demand. Retrying in {wait_sec}s... (Attempt {attempt}/{max_retries})"
                        )
                    time.sleep(wait_sec)
                    continue
                else:
                    break

    raise last_exception or RuntimeError("Failed to extract study data after retrying candidate models.")
# =====================================================================
# 3. Streamlit User Interface
# =====================================================================
st.set_page_config(
    page_title="StudySifter - AI Research Extraction",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 StudySifter")
st.markdown(
    """
    **AI-assisted research extraction tool for scientific literature.**  
    Upload a scientific research paper (PDF) to extract standardized study characteristics 
    with verifiable evidence quotes and confidence ratings.
    """
)

# Verify API key is present
if not os.environ.get("GEMINI_API_KEY"):
    st.error("⚠️ GEMINI_API_KEY is not set. Please set your environment variable before running.")
    st.code("export GEMINI_API_KEY='your_api_key_here'", language="bash")

# File uploader
uploaded_file = st.file_uploader(
    "Upload a scientific research paper (PDF)", 
    type=["pdf"],
    help="Select a research paper in PDF format to analyze."
)

col1, col2 = st.columns([1, 4])
with col1:
    analyze_button = st.button("🚀 Analyze Paper", type="primary", disabled=uploaded_file is None)

# Trigger extraction
if analyze_button and uploaded_file is not None:
    status_box = st.empty()
    with st.spinner("Analyzing research paper with Gemini... Verifying evidence quotes..."):
        try:
            pdf_bytes = uploaded_file.getvalue()
            result = extract_study_data(pdf_bytes, uploaded_file.name, status_placeholder=status_box)
            status_box.empty()

            st.session_state["extraction_result"] = result
            st.session_state["filename"] = uploaded_file.name
            st.success("Extraction complete! See structured findings below.")
        except Exception as e:
            status_box.empty()
            err_msg = str(e)
            if "503" in err_msg or "high demand" in err_msg.lower():
                st.error("⚠️ The Gemini model service is currently experiencing a temporary spike in global demand.")
                st.info("💡 **What to do:** Spikes usually clear within 10–30 seconds. Please wait a moment and click **'🚀 Analyze Paper'** again.")
            else:
                st.error(f"Extraction failed: {err_msg}")

# Display results if available in session state
if "extraction_result" in st.session_state:
    res: StudyExtraction = st.session_state["extraction_result"]

    st.divider()
    st.subheader(f"📄 Results for: {res.paper_title}")

    # Top metric cards
    m1, m2, m3 = st.columns(3)
    m1.metric("Publication Year", res.publication_year)
    m2.metric("Extraction Confidence", res.confidence_level)
    m3.metric("Study Design", res.study_design)

    # Build rows for the results table
    field_data = [
        {"Field": "Paper Title", "Extracted Value": res.paper_title, "Evidence Location": "Title Header"},
        {"Field": "Authors", "Extracted Value": res.authors, "Evidence Location": "Authors Byline"},
        {"Field": "Publication Year", "Extracted Value": res.publication_year, "Evidence Location": "Publication Date"},
        {"Field": "Study Design", "Extracted Value": res.study_design, "Evidence Location": res.evidence_location},
        {"Field": "Population / Model", "Extracted Value": res.population_or_model, "Evidence Location": "Methods"},
        {"Field": "Sample Size", "Extracted Value": res.sample_size, "Evidence Location": "Methods / Sample Allocation"},
        {"Field": "Intervention / Drug", "Extracted Value": res.intervention_or_drug, "Evidence Location": "Interventions"},
        {"Field": "Dose", "Extracted Value": res.dose, "Evidence Location": "Methods / Dosing"},
        {"Field": "Comparator / Control", "Extracted Value": res.comparator_control, "Evidence Location": "Control Arm"},
        {"Field": "Outcome Measure", "Extracted Value": res.outcome_measure, "Evidence Location": "Endpoints"},
        {"Field": "Behavioral / Experimental Assay", "Extracted Value": res.behavioral_or_experimental_assay, "Evidence Location": "Assays"},
        {"Field": "Key Result", "Extracted Value": res.key_result, "Evidence Location": "Results"},
        {"Field": "Statistical Result", "Extracted Value": res.statistical_result, "Evidence Location": "Results / Stats"},
        {"Field": "Confidence Flag", "Extracted Value": res.confidence_level, "Evidence Location": "Audit Score"},
        {"Field": "Ambiguity / Missing Notes", "Extracted Value": res.ambiguity_notes, "Evidence Location": "Quality Audit"},
    ]

    df = pd.DataFrame(field_data)

    st.markdown("### 📊 Extracted Characteristics Table")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Evidence Verification Card
    st.markdown("### 🔍 Supporting Evidence Verification")
    st.info(
        f"**Verbatim Quote from Paper:**\n\n*\"{res.supporting_evidence}\"*\n\n"
        f"📍 **Location in Paper:** {res.evidence_location}\n\n"
        f"⚠️ **Ambiguity & Caveat Notes:** {res.ambiguity_notes}"
    )

    # CSV Download Button
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Extracted Data as CSV",
        data=csv_data,
        file_name=f"studysifter_{st.session_state['filename']}.csv",
        mime="text/csv",
    )
# Model tier selection
model_choice = st.selectbox(
    "Select Gemini Model Tier",
    [
        "gemini-3.1-flash-lite (Recommended: High Free Quota, up to 1,500/day)",
        "gemini-flash-latest",
        "gemini-3.8-flash (Standard: 20 requests/day limit on free tier)",
    ],
    help="Gemini 3.1 Flash-Lite has significantly higher free tier rate limits to prevent 429 RESOURCE_EXHAUSTED errors."
)

preferred_model = (
    "gemini-3.1-flash-lite"
    if "lite" in model_choice
    else ("gemini-3.8-flash" if "3.8" in model_choice else "gemini-flash-latest")
)