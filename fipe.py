import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
from dotenv import load_dotenv
import os

# ==== Configurações ====
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8501/"
AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"
SCOPES = ["openid", "email", "profile"]

def google_login():
    if st.button("Login com Google"):
        oauth = OAuth2Session(CLIENT_ID, CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPES)
        auth_url, state = oauth.create_authorization_url(AUTHORIZATION_URL)
        st.write(f"[Clique aqui para fazer login]({auth_url})")

    query_params = st.query_params
    auth_code = query_params.get("code", None)

    if auth_code:
        oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES)
        token_response = oauth.fetch_token(
            TOKEN_URL,
            authorization_response=f"{REDIRECT_URI}?code={auth_code}",
            client_secret=CLIENT_SECRET,
            include_client_id=True,
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
        if st.button("Continuar"):
            st.rerun()  
            
        if st.button("Logout"):
            del st.session_state["token"]
            del st.session_state["user_email"]
            st.rerun()

if "show_login" not in st.session_state:
    st.session_state["show_login"] = False

if st.session_state["show_login"]==False:    
    if st.button("⚙️"):
        st.session_state["show_login"] = True
        st.rerun()
else:
    if "user_email" not in st.session_state:
        st.title("🔐 Login com Google")
        google_login()
        st.stop()
        user_email = st.session_state["user_email"]
        st.rerun()


try: 
    st.whrite(f"Olá {user_email}")
except:
    st.write("Olá, usuário")

brand = st.selectbox("Marca", ["VW", "FIAT", "FORD", "GM"])
model = st.selectbox("Modelo", ["Gol", "Palio", "Ka", "Onix"])
year = st.number_input("Ano", min_value=1990, max_value=2022, value=2022)

if st.button("Consultar"):
    st.write(f"Consultando FIPE de {brand} {model} {year}...")
    st.write