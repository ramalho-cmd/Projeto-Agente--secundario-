import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
import os
from dotenv import load_dotenv


#Configurações OAuth2 do Google
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8501/"  # URL de redirecionamento do OAuth2
AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

# Escopos solicitados
SCOPES = ["openid", "email", "profile"]

# Título do app
st.title("Login com Google no Streamlit")


if st.button("Login com Google"):
        oauth = OAuth2Session(CLIENT_ID, CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPES)
        auth_url, state = oauth.create_authorization_url(AUTHORIZATION_URL)

        # Redireciona o usuário para a URL de login do Google
        st.write(f"[Clique aqui para fazer login]({auth_url})") 

# Captura parâmetros da URL (para quando o Google redireciona de volta com o código de autorização)

query_params = st.query_params
auth_code = query_params.get("code", None)


if auth_code:
    st.info("Autenticando...")

    # Solicitação para trocar código pelo token de acesso
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES)
    token_response = oauth.fetch_token(
        TOKEN_URL,
        authorization_response=f"{REDIRECT_URI}?code={auth_code}",
        client_secret=CLIENT_SECRET,
        include_client_id=True,
        auth=None
    )
    st.query_params.clear()

    # Salva o token na sessão
    st.session_state["token"] = token_response
    st.success("Login realizado com sucesso!")
    st.rerun()


# Se o usuário já estiver autenticado, exibe os dados
if "token" in st.session_state:
    st.success("Login realizado com sucesso!")

    # Requisição para obter os dados do usuário
    oauth = OAuth2Session(CLIENT_ID, CLIENT_SECRET, token=st.session_state["token"])
    user_info = oauth.get(USERINFO_URL).json()

    # Exibe informações do usuário
    st.image(user_info["picture"], width=100)
    st.write(f"**Nome:** {user_info['name']}")
    st.write(f"**Email:** {user_info['email']}")

    #                                               >>>>Função para banco de dados aqui <<<<<

    # Botão de logout
    if st.button("Logout"):
        del st.session_state["token"]
        st.rerun()