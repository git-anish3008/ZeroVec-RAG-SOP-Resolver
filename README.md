# ZeroVec-RAG: Local SOP Resolver for Field Techs

A lightweight, vectorless Retrieval-Augmented Generation (RAG) backend designed for IT operations. It uses **LanceDB (BM25 Full-Text Search)** and **Docling (Hierarchical Chunking)** to instantly surface precise hardware troubleshooting steps and device management policies from massive Standard Operating Procedure (SOP) libraries.

## The Problem
Field technicians and help desk engineers are drowning in thousands of pages of buried SharePoint SOPs. When an endpoint is down, technicians do not have the time—or the screen real estate—to dig through massive PDFs on a mobile device. They need an on-the-go agent that can instantly surface the exact resolution steps while standing right in front of the broken hardware. 

## The Solution
**ZeroVec-RAG** ditches traditional high-dimensional embeddings in favor of **lexical search (BM25)** and **layout-aware chunking**. By indexing documents using exact-match term frequencies, this backend ensures that queries containing specific error codes, Windows event IDs, or exact policy names return the precise paragraph required. 

The retrieved context is formatted cleanly with source files and section headers, ready to be passed to a local LLM (like Ollama) to generate a concise, mobile-friendly answer.

## Key Features

* **Layout-Aware Chunking:** Uses IBM's `docling` to parse the actual structure of PDFs and Word documents. Critical contextual groups—like warning callouts, nested troubleshooting tables, and sequential steps—remain logically intact.
* **Intelligent Metadata:** Automatically extracts and tags chunks with their hierarchical Table of Contents (TOC) path (e.g., `Troubleshooting > Network > Wi-Fi Config`), providing vital context to the LLM.
* **Exact-Match Precision:** Uses `lancedb`'s native Full-Text Search (FTS) index. Dense embeddings often dilute exact keyword matches into generalized semantic spaces; this lexical approach ensures strict keyword retrieval.
* **Zero Embedding Overhead:** By removing the embedding model entirely, the pipeline drastically reduces CPU/VRAM usage. Documents are indexed locally and appended efficiently without re-embedding massive datasets.
* **100% Local & Private:** Designed to operate entirely locally. No proprietary internal company SOPs, scripts, or infrastructure details are ever sent to an external API.

---

## Installation

Ensure you have Python 3.9+ installed. Install the required dependencies:

```bash
pip install lancedb docling
