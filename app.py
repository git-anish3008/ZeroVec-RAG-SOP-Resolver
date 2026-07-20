import streamlit as st
import os
import tempfile
import ollama
from rag_engine import process_and_store_documents, query_knowledge_base

# ==========================================
# UI CONFIGURATION
# ==========================================
st.set_page_config(page_title="Vectorless RAG Office Assistant", page_icon="🗂️", layout="wide")
st.title("🗂️ Vectorless Office Assistant")

# Initialize chat history in Streamlit's Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================================
# SIDEBAR: DOCUMENT UPLOAD (PHASE 2)
# ==========================================
with st.sidebar:
    st.header("1. Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload Office PDFs here",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )

    if st.button("Process & Index Documents"):
        if not uploaded_files:
            st.warning("Please upload at least one document first.")
        else:
            # We must save Streamlit's in-memory files to disk so Docling can read them
            temp_dir = tempfile.mkdtemp()
            file_paths = []

            for uploaded_file in uploaded_files:
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                file_paths.append(temp_path)

            # The Spinner! This prevents the UI from freezing while Docling works.
            with st.spinner("Parsing hierarchy and building BM25 index... This may take a moment."):
                success, message = process_and_store_documents(file_paths)

                if success:
                    st.success(message)
                else:
                    st.error(message)

# ==========================================
# MAIN WINDOW: CHAT INTERFACE (PHASE 3)
# ==========================================
st.header("2. Ask Questions")

# Render existing chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input Box
if user_input := st.chat_input("Ask a question about your documents..."):

    # 1. Display user message instantly
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 2. Retrieve context from LanceDB
    with st.chat_message("assistant"):
        with st.spinner("Searching BM25 Index..."):
            context = query_knowledge_base(user_input)

        if context == "ERROR_EMPTY_DB":
            st.error("The knowledge base is empty. Please upload and process documents first.")
        elif not context:
            st.warning("No relevant information found in the documents.")
        else:
            # 3. Construct the Strict Prompt
            prompt = f"""You are a helpful and precise office assistant. 
            Answer the user's question using ONLY the context provided below. 
            If the answer is not contained in the context, explicitly state: "I cannot answer this based on the provided documents."

            Context:
            {context}

            Question: {user_input}
            Answer:"""

            # 4. Stream the response from the local Qwen model
            st_placeholder = st.empty()
            full_response = ""

            try:
                # We use stream=True so the UI feels fast and responsive
                stream = ollama.chat(
                    model='qwen2.5:3b',
                    messages=[{'role': 'user', 'content': prompt}],
                    stream=True
                )

                for chunk in stream:
                    full_response += chunk['message']['content']
                    st_placeholder.markdown(full_response + "▌")

                # Render final response without the cursor
                st_placeholder.markdown(full_response)

                # Expandable accordion so the user can see exactly where the LLM got its data
                with st.expander("View Retrieved Context"):
                    st.text(context)

            except Exception as e:
                st.error(f"Error communicating with Ollama: {e}")

            # Save assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
