import streamlit as st
import os
import json
import openai
from authlib.integrations.requests_client import OAuth2Session
from dotenv import load_dotenv

# ==== Configurações gerais ====
load_dotenv()
openai.api_key = os.getenv("openai.api_key")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8501/"
AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"
SCOPES = ["openid", "email", "profile"]

# ==== Função de login Google ====
def google_login():
    if st.button("Login com Google"):
        oauth = OAuth2Session(CLIENT_ID, CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPES)
        auth_url, state = oauth.create_authorization_url(AUTHORIZATION_URL)
        st.write(f"[Clique aqui para fazer login]({auth_url})")

    query_params = st.query_params
    auth_code = query_params.get("code", None)

    if auth_code:
        st.info("Autenticando...")

        oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES)
        token_response = oauth.fetch_token(
            TOKEN_URL,
            authorization_response=f"{REDIRECT_URI}?code={auth_code}",
            client_secret=CLIENT_SECRET,
            include_client_id=True,
            auth=None
        )
        st.query_params.clear()

        st.session_state["token"] = token_response
        st.rerun()

    if "token" in st.session_state:
        oauth = OAuth2Session(CLIENT_ID, CLIENT_SECRET, token=st.session_state["token"])
        user_info = oauth.get(USERINFO_URL).json()
        st.session_state["user_email"] = user_info["email"]

        st.image(user_info["picture"], width=100)
        st.write(f"**Nome:** {user_info['name']}")
        st.write(f"**Email:** {user_info['email']}")

        if st.button("Logout"):
            del st.session_state["token"]
            del st.session_state["user_email"]
            st.rerun()

# ==== Execução do login ====
if "user_email" not in st.session_state:
    st.title("🔐 Login com Google")
    google_login()
    st.stop()  # Para aqui até o login ser feito

# ==== Usuário autenticado ====
user_email = st.session_state["user_email"]

# ==== Funções de assistentes ====
def load_user_assistants(email):
    file_path = f"assistants/{email}.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}

def save_user_assistants(email, assistants):
    os.makedirs("assistants", exist_ok=True)
    file_path = f"assistants/{email}.json"
    with open(file_path, "w") as f:
        json.dump(assistants, f, indent=4)

assistants = load_user_assistants(user_email)

# ==== Interface principal ====
st.title("🔹 Área de Assistentes Inteligentes")

with st.sidebar:
    st.header("🔧 Configurar Assistente")
    selected_assistant = st.selectbox("Escolha um assistente", ["Novo assistente"] + list(assistants.keys()))

    if selected_assistant == "Novo assistente":
        assistant_name = st.text_input("Nome do Assistente")
        model = st.selectbox("Modelo", ["gpt-3.5-turbo", "gpt-4"])
        temperature = st.slider("Temperatura", 0.0, 1.0, 0.7)
        max_tokens = st.number_input("Tokens máximos", min_value=100, max_value=4000, value=1000)
        instructions = st.text_area("Instruções do Assistente")
        uploaded_files = st.file_uploader("Arquivos de Instrução", accept_multiple_files=True)
        file_contents = {file.name: file.read().decode("utf-8") for file in uploaded_files}

        if st.button("Salvar Assistente"):
            if not assistant_name:
                st.warning("Digite um nome para o assistente.")
            else:
                assistants[assistant_name] = {
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "instructions": instructions,
                    "files": file_contents,
                }
                save_user_assistants(user_email, assistants)
                st.success(f"Assistente '{assistant_name}' salvo com sucesso!")
                st.rerun()
    else:
        st.subheader(f"Assistente Selecionado: {selected_assistant}")
        assistant = assistants[selected_assistant]
        st.markdown(f"**Modelo:** {assistant['model']}")
        st.markdown(f"**Temperatura:** {assistant['temperature']}")
        st.markdown(f"**Tokens máximos:** {assistant['max_tokens']}")
        st.markdown(f"**Instruções:** {assistant['instructions']}")
        if assistant.get("files"):
            st.markdown("**Arquivos Carregados:**")
            for name, content in assistant["files"].items():
                with st.expander(name):
                    st.text(content)

if selected_assistant != "Novo assistente":
    st.header(f"💬 Converse com '{selected_assistant}'")
    user_input = st.text_area("Digite sua mensagem:")

    if st.button("Enviar"):
        if not user_input:
            st.warning("Digite uma mensagem para enviar.")
        else:
            system_prompt = assistant["instructions"]
            files_content = "\n\n".join(
                [f"Arquivo {name}:\n{content}" for name, content in assistant.get("files", {}).items()]
            )
            full_context = f"{system_prompt}\n\n{files_content}".strip()

            try:
                response = openai.ChatCompletion.create(
                    model=assistant["model"],
                    temperature=assistant["temperature"],
                    max_tokens=assistant["max_tokens"],
                    messages=[
                        {"role": "system", "content": full_context},
                        {"role": "user", "content": user_input},
                    ],
                )
                reply = response.choices[0].message["content"]
                st.success("Resposta do assistente:")
                st.write(reply)

            except Exception as e:
                st.error(f"Erro ao gerar resposta: {e}")


