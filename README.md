# StudySifter
**[Live Demo](https://studysifter-ng23jbnc4ixp587gq4ny2z.streamlit.app/)**

> Try the deployed application by uploading a scientific research paper in PDF format.
StudySifter is an AI-assisted scientific literature extraction prototype built with Python, Streamlit, Pydantic, Pandas, and the Google Gen AI SDK. It implements a structured LLM extraction pipeline that converts scientific research papers from PDF documents into standardized, reviewable study data.

The project was designed around a common evidence-synthesis problem: extracting consistent study characteristics from heterogeneous scientific papers while preserving enough source information for a human reviewer to validate the model's output.

Instead of generating a free-form summary, StudySifter defines a typed extraction schema with Pydantic and passes that schema to Gemini as the required response structure. The model processes the uploaded PDF directly and returns structured JSON containing predefined study characteristics such as study design, population or experimental model, sample size, intervention, dose, comparator, outcome measures, experimental assays, statistical results, and key findings.

To make LLM-generated extraction more auditable, the schema also requires supporting evidence, evidence location, confidence level, and ambiguity notes. The prompting logic explicitly instructs the model not to infer undocumented information and to return `Not reported` when a value cannot be supported by the source document.

The application converts validated model output into a Pandas DataFrame for review in the Streamlit interface and supports CSV export for downstream analysis.

## Technical Features

- **Structured LLM output:** Uses a Pydantic `BaseModel` as a response schema to constrain Gemini output to a predefined data contract.
- **Direct PDF processing:** Sends uploaded scientific PDFs to the Gemini API as `application/pdf` input without requiring a separate manual text-extraction step.
- **Schema validation:** Parses model responses with Pydantic before extracted data is accepted by the application.
- **Evidence traceability:** Requests verbatim supporting evidence and document locations alongside extracted findings.
- **Uncertainty handling:** Captures confidence levels and ambiguity notes and explicitly represents unavailable information as `Not reported`.
- **Hallucination mitigation:** Uses explicit extraction constraints and a low generation temperature to prioritize source-grounded responses over completion of missing fields.
- **API resilience:** Implements retry logic and exponential backoff for transient API failures and rate-limit conditions.
- **Interactive application:** Uses Streamlit for PDF upload, execution status, structured results, evidence review, and session-state persistence.
- **Data transformation:** Converts validated extraction results into a Pandas DataFrame.
- **Export workflow:** Generates downloadable CSV output for downstream research or analytical workflows.
- **Credential security:** Reads the Gemini API credential from an environment variable rather than storing credentials in source code.
## Architecture

StudySifter follows a structured extraction pipeline:

```text
Scientific PDF
      │
      ▼
Streamlit Upload Interface
      │
      ▼
PDF converted to Gemini-compatible input
      │
      ▼
Gemini API
  ├── System extraction instructions
  ├── Low-temperature generation
  └── Pydantic response schema
      │
      ▼
Structured JSON Response
      │
      ▼
Pydantic Validation
      │
      ▼
StudyExtraction Object
      │
      ▼
Pandas DataFrame
      │
      ├── Streamlit Results Display
      ├── Evidence / Ambiguity Review
      └── CSV Export
## How It Works

1. A user uploads a scientific research paper through the Streamlit interface.
2. The application reads the uploaded document as PDF bytes and constructs a Gemini-compatible `application/pdf` input.
3. StudySifter sends the document to Gemini with:
   - A system instruction defining extraction and source-grounding requirements
   - A predefined Pydantic response schema
   - A low generation temperature (`0.1`)
4. Gemini returns a structured JSON response conforming to the `StudyExtraction` schema.
5. Pydantic validates and parses the response into a `StudyExtraction` object.
6. The validated extraction is stored in Streamlit session state and transformed into a Pandas DataFrame.
7. The interface presents the extracted characteristics alongside evidence, source-location, confidence, and ambiguity information.
8. The structured results can be exported as a CSV file for downstream review or analysis.

## Design Decisions

### Structured Output Instead of Free-Form Generation
StudySifter uses a Pydantic response schema rather than asking the model to return an unrestricted summary. This creates a consistent data contract between the LLM and the application and makes responses easier to validate and transform programmatically.

### Source-Grounded Extraction
The extraction prompt prioritizes information explicitly stated in the source document. When information cannot be located, the model is instructed to return `Not reported` rather than infer a value.

### Human-Review-Oriented Design
StudySifter is designed as an AI-assisted extraction tool rather than an autonomous evidence-review system. Supporting quotations, evidence locations, confidence ratings, and ambiguity notes are surfaced so that extracted information can be checked against the original paper.

### API Error Handling
The extraction function detects transient API conditions such as rate limits and service-unavailable responses and includes retry/backoff behavior rather than immediately terminating the workflow.

## Limitations

StudySifter is a prototype and its output should not be treated as a substitute for human review of the original scientific literature.

- LLM-generated extractions may still contain incorrect, incomplete, or unsupported information despite schema constraints and source-grounding instructions.
- Confidence ratings are generated by the model and are not calibrated probabilities of correctness.
- Evidence quotations and reported source locations should be verified against the original PDF.
- PDF formatting, tables, figures, scanned documents, and unusual article structures may affect extraction quality.
- The current extraction schema is predefined and may not capture every study characteristic required for a particular systematic review or research domain.
- The current prototype processes papers individually rather than implementing a complete multi-document systematic-review pipeline.

## Running Locally

### Prerequisites

- Python 3.10+
- A Google Gemini API key

### 1. Clone the repository

```bash
git clone <repository-url>
cd studysifter
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Gemini API key

StudySifter reads the API key from the `GEMINI_API_KEY` environment variable.

On macOS or Linux:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

Do not store API credentials directly in the source code or commit them to GitHub.

### 5. Start the application

```bash
streamlit run app.py
```

Streamlit will start the local application and provide a URL that can be opened in a web browser.

## Tech Stack

- **Python** — application logic and API integration
- **Streamlit** — interactive web application
- **Google Gen AI SDK** — Gemini API integration and PDF processing
- **Pydantic** — structured response schema and validation
- **Pandas** — tabular transformation and CSV generation