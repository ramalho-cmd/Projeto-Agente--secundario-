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
