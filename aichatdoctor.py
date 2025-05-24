import os
import streamlit as st
import streamlit_authenticator as stauth

from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


HF_TOKEN = os.environ.get("HF_TOKEN")
HUGGING_FACE_REPO_ID="mistralai/Mistral-7B-Instruct-v0.3"
DB_FAISS_PATH="vectorstore/db_faiss"

# ---- AUTHENTICATION ----

credentials = {
    "usernames": {
        "sid": {
            "name": "Sid",
            "password": '$2b$12$79bxSVc3yaid8cofgvIaKuvN1QVjl1a4IpLz.n41XK0C17C9.sXr2'
        },
        "luxcima": {
            "name": "Luxcima",
            "password": '$2b$12$Olji3539bfrebrtaWKuDS..Mn48v7veZq9WMHKXYlH8r2uTEpF15m'
        },
        "mayank": {
            "name": "Mayank",
            "password": '$2b$12$H5iOUqxZS/v1DTxkOYhLe.emuOIbkseOJu0kGjjR5XU2e9YqG3Nc6'
        }
    }
}

authenticator = stauth.Authenticate(
    credentials, "ai-chat-doctor", "auth", 1
)

@st.cache_resource
def get_vectorstore():
    embedding_model=HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    db = FAISS.load_local(DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)
    return db


def set_custom_prompt(custom_prompt_template):
    prompt=PromptTemplate(
        template=custom_prompt_template,
        input_variables=["context", "question"]
    )
    return prompt

def load_llm(huggingface_repo_id, HF_TOKEN):
    llm = HuggingFaceEndpoint(
        repo_id=huggingface_repo_id,
        huggingfacehub_api_token=HF_TOKEN, 
        temperature=0.5
    )
    return llm

def main():
    st.title("Sid's AI chat doctor")

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        st.chat_message(message['role']).markdown(message['content'])

    prompt=st.chat_input(
        "Enter your prompt here"
    )

    if prompt:
        st.chat_message('user', avatar="🧑‍💻").markdown(prompt)
        st.session_state.messages.append({'role': 'user', 'content':prompt})

        custom_prompt_template = """
            Use the pieces of information provided in the context to answer user's question.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            Don't provide anything out of the given context

            Context: {context}
            Question: {question}

            Start the answer directly. No small talk please.
            """

        try:
            vectorstore = get_vectorstore()
            if vectorstore is None:
                st.error("Failed to load the vector store")
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=load_llm(huggingface_repo_id=HUGGING_FACE_REPO_ID, HF_TOKEN=HF_TOKEN),
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={'k':3}),
                return_source_documents=True,
                chain_type_kwargs={
                    "prompt": set_custom_prompt(custom_prompt_template)
                }
            )

            response = qa_chain.invoke({'query': prompt})

            result = response['result']
            source_documents = response['source_documents']
            # Format assistant's main response
            response_md = f"""**🧠 Answer:**\n\n{result}\n\n---\n**📚 Source Documents:**\n"""

            # Add formatted sources
            for i, doc in enumerate(source_documents, 1):
                metadata = doc.metadata
                page = metadata.get("page_label", "?")
                source = metadata.get("source", "Unknown Source")
                snippet = doc.page_content.strip().replace("\n", " ")[:300]
                response_md += f"\n**{i}. Page {page}** — *{source}*\n> {snippet}...\n"

            # Display nicely in chat
            st.chat_message('assistant', avatar="🤖").markdown(response_md, unsafe_allow_html=True)
            st.session_state.messages.append({'role': 'assistant', 'content': response_md})

        except Exception as e:
            st.error(f"Error : {str(e)}")

try:
    authenticator.login()
except Exception as e:
    st.error(e)

if st.session_state.get('authentication_status'):
    authenticator.logout()
    st.write(f'Welcome *{st.session_state.get("name")}*')
    main()

elif st.session_state.get('authentication_status') is False:
    st.error('Username/password is incorrect')
elif st.session_state.get('authentication_status') is None:
    st.warning('Please enter your username and password')