# StudySifter
[**Live Demo →**](https://studysifter-ng23jbnc4ixp587gq4ny2z.streamlit.app/)

StudySifter is an AI-assisted scientific literature extraction tool built with Python, Streamlit, Pydantic, Pandas, and the Google Gemini API. I built it to explore a problem I encountered while working with scientific literature: extracting the same study characteristics across papers without losing the source information needed to verify them.

Rather than generating a free-form summary, StudySifter uses a Pydantic schema to define the expected output structure. Uploaded PDFs are processed directly by Gemini and returned as structured data containing study design, population/model, sample size, intervention, dose, comparator, outcomes, assays, statistical results, and key findings.

The extraction also includes supporting evidence, evidence location, confidence level, and ambiguity notes. When information is not explicitly reported in the paper, the model is instructed to return `Not reported` rather than infer a value.

## Technical Features

- **Structured LLM output:** Pydantic response schema constrains Gemini output to a predefined data model.
- **Direct PDF processing:** Scientific PDFs are passed to Gemini as `application/pdf` input.
- **Schema validation:** Model responses are parsed and validated before being used by the application.
- **Evidence traceability:** Extracted findings include supporting quotations and source locations for human review.
- **Uncertainty handling:** Confidence levels, ambiguity notes, and explicit missing-data handling are included in the extraction.
- **LLM configuration:** Low-temperature generation and source-grounding instructions are used to reduce unsupported extraction.
- **API error handling:** Retry and backoff logic handles transient service errors and rate-limit conditions.
- **Data workflow:** Validated results are transformed into a Pandas DataFrame and can be exported as CSV.
- **Interactive UI:** Streamlit handles PDF upload, processing status, results display, evidence review, and session state.

## Architecture

```text
Scientific PDF
      │
      ▼
Streamlit Interface
      │
      ▼
Gemini API
  ├── Extraction Instructions
  ├── Pydantic Response Schema
  └── Low-Temperature Generation
      │
      ▼
Structured JSON
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
      ├── Results Display
      ├── Evidence Review
      └── CSV Export
```

## Design

StudySifter is designed as an **AI-assisted extraction tool rather than an autonomous evidence-review system**. The goal is to make LLM output easier to inspect by pairing extracted values with evidence and uncertainty information.

Structured output makes results more consistent and programmatically usable, but it does not guarantee factual accuracy. Supporting quotations and source locations are therefore surfaced for verification against the original paper.

The current prototype processes papers individually and uses a predefined extraction schema. LLM-generated values, evidence locations, and confidence ratings should still be independently verified before use in formal research.

## Tech Stack

**Python · Streamlit · Google Gen AI SDK · Pydantic · Pandas**