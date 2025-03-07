import streamlit as st
import os
import json
import openai
from authlib.integrations.requests_client import OAuth2Session
from dotenv import load_dotenv

# ==== Configurações ====
load_dotenv()
openai.api_key = os.getenv("openai.api_key")     # chave da API do OpenAI
CLIENT_ID = os.getenv("CLIENT_ID")              # ID do cliente do Google
CLIENT_SECRET = os.getenv("CLIENT_SECRET")      # Segredo do cliente do Google
REDIRECT_URI = "http://localhost:8501/"         # URI de redirecionamento
AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth" # URL de autorização do Google
TOKEN_URL = "https://oauth2.googleapis.com/token"              # URL de token do Google 
USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"  # URL de informações do usuário
SCOPES = ["openid", "email", "profile"]                         # Escopos da API


# Função para login com Google
def google_login():
    if st.button("Login com Google"):                                                               # Botão de login com Google para iniciar o processo de autenticação   
        oauth = OAuth2Session(CLIENT_ID, CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPES)    # Cria uma sessão OAuth2 com os parâmetros necessários           
        auth_url, state = oauth.create_authorization_url(AUTHORIZATION_URL)                          # Gera a URL de autorização e o estado (state) para a sessão OAuth2
        st.write(f"[Clique aqui para fazer login]({auth_url})")                                      # Exibe a URL de autorização para o usuário clicar

    query_params = st.query_params                                                                   # Obtém os parâmetros da URL da página
    auth_code = query_params.get("code", None)                                                       # Obtém o código de autorização da URL

    if auth_code:                                                                                    # Verifica se o código de autorização foi recebido
        oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES)                    # Cria uma nova sessão OAuth2 com os parâmetros necessários    
        token_response = oauth.fetch_token(                                                          # Obtém o token de acesso da sessão OAuth2
            TOKEN_URL,
            authorization_response=f"{REDIRECT_URI}?code={auth_code}",
            client_secret=CLIENT_SECRET,
            include_client_id=True,
        )
        
        st.query_params.clear()                                                                       # Limpa os parâmetros da URL
        st.session_state["token"] = token_response                                                    # Armazena o token de acesso na sessão do Streamlit
        st.rerun()                                                                                    # Reinicia a página para atualizar o estado

    if "token" in st.session_state:                                                                   # Verifica se o token de acesso está na sessão do Streamlit
        oauth = OAuth2Session(CLIENT_ID, CLIENT_SECRET, token=st.session_state["token"])            # Cria uma nova sessão OAuth2 com os parâmetros necessários
        user_info = oauth.get(USERINFO_URL).json()                                                   # Obtém as informações do usuário da sessão OAuth2
        st.session_state["user_email"] = user_info["email"]                                          # Armazena o email do usuário na sessão do Streamlit

        st.image(user_info["picture"], width=100)                                                    # Exibe a foto do usuário
        st.write(f"**Nome:** {user_info['name']}")                                                  # Exibe o nome do usuário
        st.write(f"**Email:** {user_info['email']}")                                                # Exibe o email do usuário
        if st.button("Continuar"):
            st.rerun()                                                                                # Reinicia a página para atualizar o estado

        if st.button("Logout"):                                                                      # Botão de logout
            del st.session_state["token"]                                                              # Remove o token e o email do usuário da sessão do Streamlit
            del st.session_state["user_email"]
            st.rerun()                                                                                # Reinicia a página para atualizar o estado

if "user_email" not in st.session_state:                                                                 # Verifica se o email do usuário não está na sessão do Streamlit
    st.title("🔐 Login com Google")                                                                     # Título da página de login
    google_login()                                                                                       # Chama a função de login com Google
    st.stop()                                                                                           # Para aqui até o login ser feito

user_email = st.session_state["user_email"]                                                         # Obtém o email do usuário autenticado

def load_user_assistants(email):                                                                     # Função para carregar os assistentes do usuário
    file_path = f"assistants/{email}.json"                                                          # Caminho do arquivo de assistentes do usuário
    if os.path.exists(file_path):                                                                     # Verifica se o arquivo existe
        with open(file_path, "r") as f:                                                              # Abre o arquivo para leitura
            return json.load(f)                                                                       # Retorna o conteúdo do arquivo em formato de dicionário
    return {}                                                                                         # Retorna um dicionário vazio se o arquivo não existir

def save_user_assistants(email, assistants):                                                         # Função para salvar os assistentes do usuário
    os.makedirs("assistants", exist_ok=True)                                                          # Cria o diretório "assistants" se não existir
    file_path = f"assistants/{email}.json"                                                            # Caminho do arquivo de assistentes do usuário
    with open(file_path, "w") as f:
        json.dump(assistants, f, indent=4)


assistants = load_user_assistants(user_email)                                                          # Carrega os assistentes do usuário

st.title("🔹 Área de Assistentes Inteligentes")                                                      # Título da página

with st.sidebar:                                                                                      # Barra lateral para configuração dos assistentes
    st.header("🔧 Configurar Assistente")                                                               # Título da barra lateral
    selected_assistant = st.selectbox("Escolha um assistente", ["Novo assistente"] + list(assistants.keys()))

    if selected_assistant == "Novo assistente":
        assistant_name = st.text_input("Nome do Assistente")                                             # Campo de texto para o nome do assistente
        model = st.selectbox("Modelo", ["gpt-3.5-turbo", "gpt-4"])                                       # Seleção do modelo
        temperature = st.slider("Temperatura", 0.0, 1.0, 0.7)                                            # Slider para a temperatura
        max_tokens = st.number_input("Tokens máximos", min_value=100, max_value=4000, value=1000)       # Campo de entrada para o número máximo de tokens
        instructions = st.text_area("Instruções do Assistente")                                          # Campo de texto para as instruções do assistente
        uploaded_files = st.file_uploader("Arquivos de Instrução", accept_multiple_files=True)          # Upload de arquivos
        file_contents = {file.name: file.read().decode("utf-8") for file in uploaded_files}             # Conversão dos arquivos para dicionário

        if st.button("Salvar Assistente"):
            if not assistant_name:                                                                       # Verifica se o nome do assistente foi digitado
                st.warning("Digite um nome para o assistente.")
            else:
                assistants[assistant_name] = {
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "instructions": instructions,
                    "files": file_contents,
                }
                save_user_assistants(user_email, assistants)                                              # Salva o assistente no arquivo
                st.success(f"Assistente '{assistant_name}' salvo com sucesso!")                            # Exibe uma mensagem de sucesso
                st.rerun()                                                                                # Reinicia a página para atualizar o estado
    else:
        assistant = assistants[selected_assistant]
        st.subheader(f"Assistente Selecionado: {selected_assistant}")                                     # Título do assistente selecionado
        st.markdown(f"**Modelo:** {assistant['model']}")                                                 # Exibe o modelo do assistente
        st.markdown(f"**Temperatura:** {assistant['temperature']}")                                       # Exibe a temperatura do assistente
        st.markdown(f"**Tokens máximos:** {assistant['max_tokens']}")                                     # Exibe o número máximo de tokens do assistente
        st.markdown(f"**Instruções:** {assistant['instructions']}")                                        # Exibe as instruções do assistente
        if assistant.get("files"):                                                                          # Verifica se há arquivos carregados
            st.markdown("**Arquivos Carregados:**")                                                       # Título dos arquivos carregados
            for name, content in assistant["files"].items():                                                # Itera sobre os arquivos carregados
                with st.expander(name):                                                                     # Exibe o nome do arquivo em um expander
                    st.text(content)                                                                         # Exibe o conteúdo do arquivo

if selected_assistant != "Novo assistente":
    st.header(f"💬 Conversa com '{selected_assistant}'")                                                 # Título da conversa

    if "messages" not in st.session_state:                                                                 # Verifica se a lista de mensagens não está na sessão do Streamlit
        st.session_state["messages"] = []                                                                 # Inicializa a lista de mensagens como uma lista vazia

    # Itera sobre as mensagens na sessão do Streamlit
    for message in st.session_state["messages"]:
        if message["role"] == "user":                                                                     # Verifica se a mensagem é de um usuário
            st.chat_message("user").write(message["content"])                                              # Exibe a mensagem do usuário
        else:
            st.chat_message("assistant").write(message["content"])                                        # Exibe a mensagem do assistente

    if prompt := st.chat_input("Digite sua mensagem..."):
        st.session_state["messages"].append({"role": "user", "content": prompt})                         # Adiciona a mensagem do usuário à lista de mensagens
        st.chat_message("user").write(prompt)                                                            # Exibe a mensagem do usuário

        system_prompt = assistant["instructions"]                                                        # Obtém as instruções do assistente
        files_content = "\n\n".join(                                                                     # Obtém o conteúdo dos arquivos do assistente
            [f"Arquivo {name}:\n{content}" for name, content in assistant.get("files", {}).items()]
        )
        full_context = f"{system_prompt}\n\n{files_content}".strip()                                      # Concatena as instruções e o conteúdo dos arquivos
        messages = [{"role": "system", "content": full_context}] + st.session_state["messages"]          # Cria a lista de mensagens completa

        try:
            # Gera a resposta usando a API do OpenAI
            response = openai.ChatCompletion.create(
                model=assistant["model"],
                temperature=assistant["temperature"],
                max_tokens=assistant["max_tokens"],
                messages=messages,
            )
            reply = response.choices[0].message["content"]                                                # Obtém a resposta da API do OpenAI
            st.session_state["messages"].append({"role": "assistant", "content": reply})                  # Adiciona a resposta ao final da lista de mensagens
            st.chat_message("assistant").write(reply)                                                     # Exibe a resposta

        except Exception as e:
            st.error(f"Erro ao gerar resposta: {e}")                                                      # Exibe uma mensagem de erro
