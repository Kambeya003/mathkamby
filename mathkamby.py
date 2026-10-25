from datetime import datetime
import hashlib
import os
import random
import re
import sqlite3
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="MathKamby Portal", page_icon="📚", layout="wide"
)

# --- ESTILIZAÇÃO CSS AVANÇADA ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .meu-cartao {
        background-color: #1e293b;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #334155;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        margin-bottom: 20px;
    }
    .titulo-destaque {
        color: #38bdf8;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .texto-suave {
        color: #94a3b8;
        font-size: 0.95rem;
    }
    .painel-admin {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-left: 5px solid #6366f1;
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .quadro-virtual {
        background-color: #0f172a;
        border: 2px dashed #38bdf8;
        padding: 20px;
        border-radius: 12px;
        color: #e2e8f0;
        font-family: 'Courier New', Courier, monospace;
        white-space: pre-wrap;
        margin-bottom: 20px;
    }
    .carta-matematica {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        border: 2px solid #818cf8;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(129, 140, 248, 0.3);
        margin-bottom: 20px;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #4338ca 0%, #2563eb 100%);
        box-shadow: 0 6px 16px rgba(79, 70, 229, 0.5);
        transform: translateY(-1px);
    }
    </style>
""",
    unsafe_allow_html=True,
)

DB_NAME = "meu_site.db"
UPLOAD_DIR = "uploads"
AUDIO_DIR = "audios_gravados"
AVATAR_DIR = "avatars_usuarios"
MUSIC_DIR = "musicas_estudo"


# --- 1. CONFIGURAÇÃO DA BASE DE DADOS ---
def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            senha_hash TEXT,
            tipo TEXT DEFAULT 'usuario',
            avatar TEXT DEFAULT '👤'
        )
    """)

  try:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN avatar TEXT DEFAULT '👤'")
  except sqlite3.OperationalError:
    pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            autor TEXT,
            conteudo TEXT,
            tipo_msg TEXT DEFAULT 'texto',
            caminho_audio TEXT,
            data_envio TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS arquivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            autor TEXT,
            nome_arquivo TEXT,
            caminho_arquivo TEXT,
            data_envio TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS rascunho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conteudo TEXT,
            caminho_audio TEXT,
            atualizado_em TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS duvidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            autor TEXT,
            pergunta TEXT,
            caminho_audio TEXT,
            data_envio TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            autor TEXT,
            estrelas INTEGER,
            comentario TEXT,
            data_envio TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS ranking_jogo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            autor TEXT,
            modo TEXT,
            nivel INTEGER,
            pontos INTEGER,
            tempo_total REAL,
            data_jogo TEXT
        )
    """)

  try:
    cursor.execute(
        "ALTER TABLE ranking_jogo ADD COLUMN modo TEXT DEFAULT 'Aritmético'"
    )
  except sqlite3.OperationalError:
    pass

  conn.commit()
  conn.close()


def hash_senha(senha):
  return hashlib.sha256(senha.encode()).hexdigest()


def validar_forca_senha(senha):
  if len(senha) < 8:
    return False, "A palavra-passe deve ter pelo menos 8 caracteres."
  if not re.search(r"[A-Z]", senha):
    return False, "Deve conter pelo menos uma letra maiúscula."
  if not re.search(r"[a-z]", senha):
    return False, "Deve conter pelo menos uma letra minúscula."
  if not re.search(r"\d", senha):
    return False, "Deve conter pelo menos um número."
  if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
    return False, (
        "Deve conter pelo menos um caractere especial (ex: !, @, #, $...)."
    )
  return True, ""


def registar_usuario(nome, senha):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  tipo_conta = "admin" if nome.strip().lower() == "kamby" else "usuario"
  avatar_inicial = "perfil.jpg" if nome.strip().lower() == "kamby" else "👤"
  try:
    cursor.execute(
        "INSERT INTO usuarios (nome, senha_hash, tipo, avatar) VALUES (?, ?, ?,"
        " ?)",
        (nome, hash_senha(senha), tipo_conta, avatar_inicial),
    )
    conn.commit()
    sucesso = True
  except sqlite3.IntegrityError:
    sucesso = False
  conn.close()
  return sucesso


def verificar_login(nome, senha):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT senha_hash, tipo, avatar FROM usuarios WHERE nome = ?", (nome,)
  )
  resultado = cursor.fetchone()
  conn.close()
  if resultado and resultado[0] == hash_senha(senha):
    return True, resultado[1], resultado[2]
  return False, "usuario", "👤"


def obter_avatar_usuario(nome):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("SELECT avatar FROM usuarios WHERE nome = ?", (nome,))
  res = cursor.fetchone()
  conn.close()
  return res[0] if res else "👤"


def atualizar_avatar_bd(nome, novo_avatar):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE usuarios SET avatar = ? WHERE nome = ?", (novo_avatar, nome)
  )
  conn.commit()
  conn.close()


def salvar_audio_disco(audio_bytes, prefixo="audio"):
  os.makedirs(AUDIO_DIR, exist_ok=True)
  nome_ficheiro = f"{prefixo}_{int(datetime.now().timestamp())}.wav"
  caminho = os.path.join(AUDIO_DIR, nome_ficheiro)
  with open(caminho, "wb") as f:
    f.write(audio_bytes.getbuffer())
  return caminho


def salvar_mensagem(autor, conteudo, tipo_msg="texto", caminho_audio=None):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  cursor.execute(
      "INSERT INTO mensagens (autor, conteudo, tipo_msg, caminho_audio, data_envio) VALUES (?, ?, ?, ?, ?)",
      (autor, conteudo, tipo_msg, caminho_audio, data),
  )
  conn.commit()
  conn.close()


def carregar_historico(usuario=None, eh_admin=False):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  if eh_admin or not usuario:
    # O Administrador vê todo o histórico do sistema
    cursor.execute(
        "SELECT id, autor, conteudo, tipo_msg, caminho_audio, data_envio FROM"
        " mensagens ORDER BY id"
    )
  else:
    # O Utilizador comum vê as mensagens dele próprio E as respostas enviadas pelo admin ("Kamby" ou "Assistente")
    cursor.execute(
        "SELECT id, autor, conteudo, tipo_msg, caminho_audio, data_envio FROM"
        " mensagens WHERE autor = ? OR autor COLLATE NOCASE = 'kamby' OR autor"
        " = 'Assistente' ORDER BY id",
        (usuario,),
    )
  mensagens = cursor.fetchall()
  conn.close()
  return mensagens

def apagar_mensagem_bd(id_msg):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("SELECT caminho_audio FROM mensagens WHERE id = ?", (id_msg,))
  res = cursor.fetchone()
  if res and res[0] and os.path.exists(res[0]):
    try:
      os.remove(res[0])
    except Exception:
      pass
  cursor.execute("DELETE FROM mensagens WHERE id = ?", (id_msg,))
  conn.commit()
  conn.close()


def limpar_todo_chat():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("DELETE FROM mensagens")
  conn.commit()
  conn.close()


def obter_rascunho():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT conteudo, caminho_audio, atualizado_em FROM rascunho ORDER BY id"
      " DESC LIMIT 1"
  )
  res = cursor.fetchone()
  conn.close()
  return res if res else ("O quadro virtual ainda está vazio.", None, "")


def atualizar_rascunho(novo_conteudo, caminho_audio=None):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  cursor.execute("DELETE FROM rascunho")
  cursor.execute(
      "INSERT INTO rascunho (conteudo, caminho_audio, atualizado_em) VALUES"
      " (?, ?, ?)",
      (novo_conteudo, caminho_audio, data),
  )
  conn.commit()
  conn.close()


def enviar_duvida(autor, pergunta, caminho_audio=None):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  cursor.execute(
      "INSERT INTO duvidas (autor, pergunta, caminho_audio, data_envio) VALUES"
      " (?, ?, ?, ?)",
      (autor, pergunta, caminho_audio, data),
  )
  conn.commit()
  conn.close()


def listar_duvidas():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, autor, pergunta, caminho_audio, data_envio FROM duvidas ORDER"
      " BY id DESC"
  )
  duvidas = cursor.fetchall()
  conn.close()
  return duvidas


def apagar_duvida(id_duvida):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("SELECT caminho_audio FROM duvidas WHERE id = ?", (id_duvida,))
  res = cursor.fetchone()
  if res and res[0] and os.path.exists(res[0]):
    try:
      os.remove(res[0])
    except Exception:
      pass
  cursor.execute("DELETE FROM duvidas WHERE id = ?", (id_duvida,))
  conn.commit()
  conn.close()


def salvar_avaliacao(autor, estrelas, comentario):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  cursor.execute(
      "INSERT INTO avaliacoes (autor, estrelas, comentario, data_envio) VALUES"
      " (?, ?, ?, ?)",
      (autor, estrelas, comentario, data),
  )
  conn.commit()
  conn.close()


def listar_avaliacoes():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, autor, estrelas, comentario, data_envio FROM avaliacoes"
      " ORDER BY id DESC"
  )
  avaliacoes = cursor.fetchall()
  conn.close()
  return avaliacoes


def media_avaliacoes():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("SELECT AVG(estrelas), COUNT(*) FROM avaliacoes")
  res = cursor.fetchone()
  conn.close()
  if res and res[1] > 0:
    return round(res[0], 1), res[1]
  return 0.0, 0


def guardar_pontuacao_jogo(autor, modo, nivel, pontos, tempo_total):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  cursor.execute(
      "INSERT INTO ranking_jogo (autor, modo, nivel, pontos, tempo_total,"
      " data_jogo) VALUES (?, ?, ?, ?, ?, ?)",
      (autor, modo, nivel, pontos, tempo_total, data),
  )
  conn.commit()
  conn.close()


def obter_ranking_jogo():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT autor, modo, nivel, pontos, tempo_total, data_jogo FROM"
      " ranking_jogo ORDER BY pontos DESC, tempo_total ASC LIMIT 10"
  )
  ranking = cursor.fetchall()
  conn.close()
  return ranking


def salvar_arquivo(autor, arquivo_up):
  os.makedirs(UPLOAD_DIR, exist_ok=True)
  caminho = os.path.join(UPLOAD_DIR, arquivo_up.name)
  with open(caminho, "wb") as f:
    f.write(arquivo_up.getbuffer())

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  cursor.execute(
      "INSERT INTO arquivos (autor, nome_arquivo, caminho_arquivo, data_envio)"
      " VALUES (?, ?, ?, ?)",
      (autor, arquivo_up.name, caminho, data),
  )
  conn.commit()
  conn.close()
  return caminho


def listar_arquivos_bd():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, autor, nome_arquivo, caminho_arquivo, data_envio FROM"
      " arquivos ORDER BY id DESC"
  )
  arquivos = cursor.fetchall()
  conn.close()
  return arquivos


def apagar_arquivo_bd(id_arq, caminho_arq):
  if os.path.exists(caminho_arq):
    try:
      os.remove(caminho_arq)
    except Exception:
      pass
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("DELETE FROM arquivos WHERE id = ?", (id_arq,))
  conn.commit()
  conn.close()


init_db()

# --- GESTÃO DE SESSÃO ---
if "logado" not in st.session_state:
  st.session_state.logado = False
if "usuario_atual" not in st.session_state:
  st.session_state.usuario_atual = ""
if "tipo_usuario" not in st.session_state:
  st.session_state.tipo_usuario = ""
if "avatar_atual" not in st.session_state:
  st.session_state.avatar_atual = "👤"

# Estados do Jogo
if "jogo_a_decorrer" not in st.session_state:
  st.session_state.jogo_a_decorrer = False
if "pergunta_atual_idx" not in st.session_state:
  st.session_state.pergunta_atual_idx = 0
if "questoes_jogo" not in st.session_state:
  st.session_state.questoes_jogo = []
if "pontos_jogo" not in st.session_state:
  st.session_state.pontos_jogo = 0
if "tempo_inicio" not in st.session_state:
  st.session_state.tempo_inicio = 0
if "nivel_jogo" not in st.session_state:
  st.session_state.nivel_jogo = 1
if "modo_jogo" not in st.session_state:
  st.session_state.modo_jogo = "Aritmético"

# Estado do Jogo de Sorte do Dado
if "dado_jogado" not in st.session_state:
  st.session_state.dado_jogado = False
if "resultado_dado" not in st.session_state:
  st.session_state.resultado_dado = 0
if "carta_sorteada" not in st.session_state:
  st.session_state.carta_sorteada = ""


# --- TELA DE LOGIN / BLOQUEIO ---
if not st.session_state.logado:
  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    st.markdown(
        """
            <div class="meu-cartao" style="text-align: center;">
                <h2 class="titulo-destaque">🔐 Acesso Restrito</h2>
                <p class="texto-suave">Portal privado protegido por autenticação.</p>
            </div>
            """,
        unsafe_allow_html=True,
    )

    aba_login, aba_registo = st.tabs(["🔑 Entrar", "📝 Criar Conta"])

    with aba_login:
      st.markdown('<div class="meu-cartao">', unsafe_allow_html=True)
      user_login = st.text_input("Nome de Utilizador", key="login_user_privado")
      senha_login = st.text_input(
          "Palavra-passe", type="password", key="login_pass_privado"
      )
      if st.button(
          "Entrar no Sistema", key="btn_login_privado", use_container_width=True
      ):
        sucesso, tipo, av = verificar_login(user_login, senha_login)
        if sucesso:
          st.session_state.logado = True
          st.session_state.usuario_atual = user_login
          st.session_state.tipo_usuario = tipo
          st.session_state.avatar_atual = av
          st.success("Login efetuado com sucesso!")
          st.rerun()
        else:
          st.error("Utilizador ou palavra-passe incorretos.")
      st.markdown("</div>", unsafe_allow_html=True)

    with aba_registo:
      st.markdown('<div class="meu-cartao">', unsafe_allow_html=True)
      novo_user = st.text_input(
          "Escolha um Nome de Utilizador", key="reg_user_privado"
      )
      nova_senha = st.text_input(
          "Crie uma Palavra-passe", type="password", key="reg_pass_privado"
      )
      confirma_senha = st.text_input(
          "Confirme a Palavra-passe", type="password", key="reg_conf_privado"
      )
      st.markdown(
          '<p class="texto-suave">ℹ️ Mínimo 8 caracteres, maiúsculas, minúsculas,'
          " números e símbolos.</p>",
          unsafe_allow_html=True,
      )
      if st.button(
          "Registar Nova Conta",
          key="btn_reg_privado",
          use_container_width=True,
      ):
        if not novo_user or not nova_senha:
          st.warning("Preencha todos os campos.")
        elif nova_senha != confirma_senha:
          st.error("As palavras-passe não coincidem.")
        else:
          valido, mensagem_erro = validar_forca_senha(nova_senha)
          if not valido:
            st.error(mensagem_erro)
          else:
            if registar_usuario(novo_user, nova_senha):
              st.success("Conta criada! Vai à aba 'Entrar'.")
            else:
              st.error("Este utilizador já existe.")
      st.markdown("</div>", unsafe_allow_html=True)

# --- APLICATIVO PRINCIPAL ---
else:
  with st.sidebar:
    avatar_sidebar = st.session_state.avatar_atual
    if avatar_sidebar and os.path.exists(avatar_sidebar):
      st.image(avatar_sidebar, width=80)
    else:
      st.markdown(
          f"<h1 style='text-align: center;'>{avatar_sidebar}</h1>",
          unsafe_allow_html=True,
      )

    st.markdown(
        f'<div class="meu-cartao" style="text-align: center;">'
        f'<h3 class="titulo-destaque">👤 {st.session_state.usuario_atual.upper()}</h3>'
        f'<p class="texto-suave">Cargo: {st.session_state.tipo_usuario.upper()}</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    # --- REPRODUTOR DE ÁUDIO PARA ESTUDO ---
    st.markdown("---")
    st.markdown("🎧 **Música de Fundo para Estudo:**")
    os.makedirs(MUSIC_DIR, exist_ok=True)
    musicas_disponiveis = [
        f
        for f in os.listdir(MUSIC_DIR)
        if f.endswith((".mp3", ".wav", ".ogg", ".m4a"))
    ]

    if musicas_disponiveis:
      musica_escolhida = st.selectbox(
          "Escolha uma faixa:", musicas_disponiveis
      )
      caminho_musica = os.path.join(MUSIC_DIR, musica_escolhida)
      st.audio(caminho_musica, loop=True)
    else:
      st.info(
          "📂 Coloca ficheiros `.m4a` ou `.mp3` na pasta `musicas_estudo` para"
          " ouvires enquanto estudas!"
      )
      if st.session_state.tipo_usuario == "admin":
        uploaded_music = st.file_uploader(
            "Enviar faixa de áudio",
            type=["mp3", "wav", "m4a"],
            key="up_music_admin",
        )
        if uploaded_music is not None:
          caminho_m = os.path.join(MUSIC_DIR, uploaded_music.name)
          with open(caminho_m, "wb") as f:
            f.write(uploaded_music.getbuffer())
          st.success("Música carregada com sucesso!")
          st.rerun()

    # Botão de Contacto WhatsApp
    st.markdown("---")
    st.markdown("💬 **Falar com o Criador:**")
    st.markdown(
        '<a href="https://wa.me/244936385827" target="_blank">'
        '<button style="width:100%; background-color:#25D366; color:white;'
        " border:none; border-radius:10px; padding:10px; font-weight:bold;"
        ' cursor:pointer;">📱 Enviar WhatsApp</button></a>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    if st.button("🚪 Terminar Sessão", use_container_width=True):
      st.session_state.logado = False
      st.session_state.usuario_atual = ""
      st.session_state.tipo_usuario = ""
      st.session_state.avatar_atual = "👤"
      st.rerun()

  st.markdown(
      """
        <div class="meu-cartao">
            <h1 class="titulo-destaque">📚 Portal MathKamby</h1>
            <p class="texto-suave">Repositório académico e central de comunicação interativa.</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  aba_biblioteca, aba_chat, aba_jogo, aba_perfil = st.tabs(
      [
          "📂 Repositório & Quadro",
          "💬 Chat e Histórico",
          "🎮 Desafios & Jogos",
          "⚙️ Meu Perfil",
      ]
  )

  # --- ABA 1: BIBLIOTECA, QUADRO VIRTUAL, DÚVIDAS E AVALIAÇÃO ---
  with aba_biblioteca:
    st.markdown(
        '<h3 class="titulo-destaque">📌 Quadro Virtual / Rascunho Oficial</h3>',
        unsafe_allow_html=True,
    )

    @st.fragment(run_every=0.5)
    def actualizar_quadro_automatico():
      conteudo_atual, audio_atual, data_atualizacao = obter_rascunho()

      if st.session_state.tipo_usuario == "admin":
        with st.expander("✏️ [Admin] Atualizar o Quadro Virtual (Texto & Áudio)"):
          novo_texto_rascunho = st.text_area(
              "Escreve ou altera o rascunho aqui:",
              value=conteudo_atual,
              height=120,
          )
          audio_rascunho_up = st.audio_input("Gravar áudio para o quadro")

          if st.button("Publicar Atualização no Quadro"):
            caminho_a = audio_atual
            if audio_rascunho_up is not None:
              caminho_a = salvar_audio_disco(audio_rascunho_up, "quadro")

            atualizar_rascunho(novo_texto_rascunho, caminho_a)
            st.success("Quadro virtual atualizado com sucesso!")
            st.rerun()

      st.markdown(
          f'<div class="quadro-virtual">{conteudo_atual}</div>',
          unsafe_allow_html=True,
      )
      if audio_atual and os.path.exists(audio_atual):
        st.audio(audio_atual)
      if data_atualizacao:
        st.caption(f"🕒 Última atualização do rascunho: {data_atualizacao}")

    actualizar_quadro_automatico()

    st.divider()

    @st.fragment(run_every=0.5)
    def actualizar_avaliacoes():
      st.markdown(
          '<h3 class="titulo-destaque">⭐ Avaliação do Conteúdo</h3>',
          unsafe_allow_html=True,
      )
      media_val, total_val = media_avaliacoes()
      if total_val > 0:
        st.markdown(
            f'<p class="texto-suave">Média atual do portal: <b>{media_val} ⭐</b>'
            f" ({total_val} avaliações registadas)</p>",
            unsafe_allow_html=True,
        )
      else:
        st.markdown(
            '<p class="texto-suave">Ainda não há avaliações. Sê o primeiro a'
            " avaliar!</p>",
            unsafe_allow_html=True,
        )

      with st.form("form_avaliacao", clear_on_submit=True):
        estrelas_escolhidas = st.slider(
            "Classifica a tua satisfação com o portal:", 1, 5, 5
        )
        comentario_aval = st.text_input(
            "Comentário opcional sobre a tua experiência:"
        )
        btn_enviar_aval = st.form_submit_button("Enviar Avaliação")
        if btn_enviar_aval:
          salvar_avaliacao(
              st.session_state.usuario_atual,
              estrelas_escolhidas,
              comentario_aval,
          )
          st.success("Obrigado pela tua avaliação!")
          st.rerun()

    actualizar_avaliacoes()

    if st.session_state.tipo_usuario == "admin":
      with st.expander("📊 Ver Detalhes das Avaliações Recebidas"):
        lista_avals = listar_avaliacoes()
        for id_av, aut_av, est_av, com_av, dat_av in lista_avals:
          st.markdown(
              f"**{aut_av}**: {'⭐' * est_av} ({est_av}/5) - _{com_av}_"
              f" <small>({dat_av})</small>",
              unsafe_allow_html=True,
          )

    st.divider()

    st.markdown(
        '<h3 class="titulo-destaque">❓ Caixa de Dúvidas & Sugestões</h3>',
        unsafe_allow_html=True,
    )

    with st.form("form_duvida", clear_on_submit=True):
      pergunta_usuario = st.text_area("Escreve a tua dúvida ou sugestão...")
      audio_duvida_up = st.audio_input("Gravar voz para dúvida")

      btn_enviar_duvida = st.form_submit_button("Enviar Dúvida / Sugestão")
      if btn_enviar_duvida:
        caminho_d_audio = None
        if audio_duvida_up is not None:
          caminho_d_audio = salvar_audio_disco(audio_duvida_up, "duvida")

        if pergunta_usuario.strip() or caminho_d_audio:
          enviar_duvida(
              st.session_state.usuario_atual,
              pergunta_usuario,
              caminho_d_audio,
          )
          st.success("Recebido com sucesso!")
          st.rerun()
        else:
          st.warning("Escreve um texto ou grava um áudio antes de enviar.")

    lista_duvidas = listar_duvidas()
    if lista_duvidas:
      st.markdown("#### Histórico de Dúvidas & Sugestões Recebidas:")
      for id_d, autor_d, perg_d, cam_aud_d, data_d in lista_duvidas:
        st.markdown(
            f'<div class="meu-cartao"><b>👤 {autor_d}</b> <span'
            f' class="texto-suave">({data_d})</span><br>{perg_d}',
            unsafe_allow_html=True,
        )
        if cam_aud_d and os.path.exists(cam_aud_d):
          st.audio(cam_aud_d)

        if st.session_state.tipo_usuario == "admin":
          if st.button(
              "✔️ Marcar como Resolvida / Apagar", key=f"del_duvida_{id_d}"
          ):
            apagar_duvida(id_d)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    if st.session_state.tipo_usuario == "admin":
      st.markdown(
          """
            <div class="painel-admin">
                <h3 class="titulo-destaque">⚙️ Painel de Administração de Ficheiros</h3>
                <p class="texto-suave">Como administrador (Kamby), podes enviar ou remover ficheiros do repositório.</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
      with st.expander("➕ Adicionar Novo Livro ou PDF"):
        novo_doc = st.file_uploader(
            "Escolhe o documento",
            type=["pdf", "txt", "docx"],
            key="upload_doc_bib",
        )
        if novo_doc is not None:
          if st.button("Carregar para a Biblioteca"):
            salvar_arquivo(st.session_state.usuario_atual, novo_doc)
            st.success(
                f"O documento '{novo_doc.name}' foi adicionado com sucesso!"
            )
            st.rerun()

    st.markdown(
        '<h3 class="titulo-destaque" style="margin-top: 20px;">📥 Documentos'
        " Disponíveis</h3>",
        unsafe_allow_html=True,
    )
    lista_docs = listar_arquivos_bd()

    if not lista_docs:
      st.info("Ainda não existem documentos carregados na base de dados.")
    else:
      for id_arq, autor, nome_arq, caminho_arq, data_envio in lista_docs:
        if os.path.exists(caminho_arq):
          st.markdown('<div class="meu-cartao">', unsafe_allow_html=True)
          if st.session_state.tipo_usuario == "admin":
            col1, col2, col3 = st.columns([3, 1, 1])
          else:
            col1, col2 = st.columns([4, 1])
            col3 = None

          with col1:
            st.markdown(f"**📄 {nome_arq}**")
            st.markdown(
                f'<p class="texto-suave">Adicionado por: {autor} em'
                f" {data_envio}</p>",
                unsafe_allow_html=True,
            )

          with col2:
            with open(caminho_arq, "rb") as f:
              bytes_arq = f.read()
            st.download_button(
                label="Baixar",
                data=bytes_arq,
                file_name=nome_arq,
                mime="application/octet-stream",
                key=f"download_{id_arq}",
                use_container_width=True,
            )

          if col3 and st.session_state.tipo_usuario == "admin":
            with col3:
              if st.button(
                  "🗑️ Apagar", key=f"del_arq_{id_arq}", use_container_width=True
              ):
                apagar_arquivo_bd(id_arq, caminho_arq)
                st.success(f"Ficheiro '{nome_arq}' eliminado!")
                st.rerun()

          st.markdown("</div>", unsafe_allow_html=True)
        else:
          st.warning(f"O arquivo '{nome_arq}' está registado, mas falta na pasta.")

  # --- ABA 2: CHAT ---
  with aba_chat:
    st.markdown(
        '<div class="meu-cartao">'
        '<h3 class="titulo-destaque">💬 Central de Mensagens</h3>'
        '<p class="texto-suave">Histórico de conversas registadas no sistema.</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    if st.session_state.tipo_usuario == "admin":
      if st.button("🧹 Limpar Todo o Histórico de Chat"):
        limpar_todo_chat()
        st.success("O histórico de mensagens foi limpo com sucesso!")
        st.rerun()

    @st.fragment(run_every=0.3)
    def actualizar_chat_automatico():
      # Utilizador normal vê apenas o seu histórico; Admin vê tudo se desejar
      eh_admin = st.session_state.tipo_usuario == "admin"
      historico = carregar_historico(
          st.session_state.usuario_atual, eh_admin=eh_admin
      )

      if not historico:
        st.info("Ainda não tens mensagens no teu histórico privado.")

      for id_msg, autor, conteudo, tipo_m, cam_aud, data in historico:
        if autor == "Assistente":
          avatar_autor = "🤖"
        else:
          avatar_autor = obter_avatar_usuario(autor)

        with st.chat_message(autor, avatar=avatar_autor):
          if tipo_m == "texto":
            st.write(conteudo)
          elif tipo_m == "audio" and cam_aud and os.path.exists(cam_aud):
            st.audio(cam_aud)

          st.caption(f"Enviado em: {data}")

          if st.session_state.tipo_usuario == "admin":
            if st.button("❌ Apagar Mensagem", key=f"del_msg_{id_msg}"):
              apagar_mensagem_bd(id_msg)
              st.rerun()

    actualizar_chat_automatico()

    st.markdown("---")
    st.markdown("#### Enviar Nova Mensagem:")
    opcao_envio = st.radio(
        "Tipo de mensagem:", ["Texto", "Gravar Áudio"], horizontal=True
    )

    if opcao_envio == "Texto":
      if prompt := st.chat_input("Escreve a tua mensagem..."):
        salvar_mensagem(
            st.session_state.usuario_atual, prompt, tipo_msg="texto"
        )
        st.success("Recebido com sucesso!")
        st.rerun()
    else:
      audio_chat_up = st.audio_input("Gravar mensagem de voz")
      if audio_chat_up is not None:
        if st.button("Enviar Áudio para o Chat"):
          caminho_chat_aud = salvar_audio_disco(audio_chat_up, "chat")
          salvar_mensagem(
              st.session_state.usuario_atual,
              "",
              tipo_msg="audio",
              caminho_audio=caminho_chat_aud,
          )
          st.success("Recebido com sucesso!")
          st.rerun()

  # --- ABA 3: DESAFIOS & JOGOS ---
  with aba_jogo:
    st.markdown(
        '<div class="meu-cartao">'
        '<h3 class="titulo-destaque">🎮 Centro de Desafios & Jogos</h3>'
        '<p class="texto-suave">Testa a tua agilidade mental, raciocínio lógico, cálculo de restos e tenta a tua sorte no dado matemático para ganhar cartas secretas com fórmulas!</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    sub_aba_jogo = st.radio(
        "Escolha a categoria de jogo:",
        [
            "⚡ Desafios Cronometrados (Aritmético, Regra de 3 & Restos)",
            "🎲 Dado da Sorte Matemáticos (Cartas & Fórmulas)",
        ],
        horizontal=True,
    )

    if sub_aba_jogo == "⚡ Desafios Cronometrados (Aritmético, Regra de 3 & Restos)":
      if not st.session_state.jogo_a_decorrer:
        modo_escolhido = st.selectbox(
            "Escolha o Modo de Jogo:",
            [
                "⚡ Desafio Aritmético (Cálculo Rápido)",
                "📐 Desafio de Regra de Três Simples (Raciocínio)",
                "➗ Desafio de Resto de Divisão (Módulo)",
            ],
        )

        nivel_selecionado = st.selectbox(
            "Selecione o Nível de Dificuldade:",
            [
                "Nível 1 (Números de 1 a 99)",
                "Nível 2 (Números de 100 a 999)",
                "Nível 3 (Números de 1000 a 9999)",
            ],
        )

        if st.button("🚀 Iniciar Desafio de 10 Exercícios"):
          nivel_num = 1
          if "Nível 2" in nivel_selecionado:
            nivel_num = 2
          elif "Nível 3" in nivel_selecionado:
            nivel_num = 3

          st.session_state.nivel_jogo = nivel_num
          st.session_state.pontos_jogo = 0
          st.session_state.pergunta_atual_idx = 0
          st.session_state.tempo_inicio = datetime.now().timestamp()

          if "Regra de Três" in modo_escolhido:
            st.session_state.modo_jogo = "Regra de Três"
          elif "Resto" in modo_escolhido:
            st.session_state.modo_jogo = "Resto da Divisão"
          else:
            st.session_state.modo_jogo = "Aritmético"

          questoes = []
          for _ in range(10):
            if st.session_state.modo_jogo == "Aritmético":
              if nivel_num == 1:
                n1, n2 = random.randint(1, 99), random.randint(1, 99)
              elif nivel_num == 2:
                n1, n2 = random.randint(100, 999), random.randint(100, 999)
              else:
                n1, n2 = random.randint(1000, 9999), random.randint(1000, 9999)

              op = random.choice(["+", "-", "×"])
              if op == "+":
                resp_correta = n1 + n2
              elif op == "-":
                if n1 < n2:
                  n1, n2 = n2, n1
                resp_correta = n1 - n2
              else:
                if nivel_num == 3:
                  n1, n2 = random.randint(10, 99), random.randint(10, 99)
                elif nivel_num == 2:
                  n1, n2 = random.randint(10, 99), random.randint(2, 9)
                else:
                  n1, n2 = random.randint(1, 12), random.randint(1, 12)
                resp_correta = n1 * n2

              opcoes = [resp_correta]
              while len(opcoes) < 4:
                falso = resp_correta + random.choice(
                    [-15, -10, -5, -2, 2, 5, 10, 15]
                )
                if falso not in opcoes and falso >= 0:
                  opcoes.append(falso)
              random.shuffle(opcoes)

              questoes.append({
                  "enunciado": f"{n1} {op} {n2} = ?",
                  "correta": resp_correta,
                  "opcoes": opcoes,
              })
            elif st.session_state.modo_jogo == "Regra de Três":
              if nivel_num == 1:
                a = random.randint(2, 10)
                b = a * random.randint(2, 9)
                c = random.randint(2, 10)
              elif nivel_num == 2:
                a = random.randint(5, 25)
                b = a * random.randint(2, 12)
                c = random.randint(5, 20)
              else:
                a = random.randint(10, 50)
                b = a * random.randint(5, 20)
                c = random.randint(10, 50)

              resp_correta = int((c * b) / a)
              while ((c * b) % a) != 0:
                c = random.randint(2, 30)
                resp_correta = int((c * b) / a)

              opcoes = [resp_correta]
              while len(opcoes) < 4:
                falso = resp_correta + random.choice(
                    [-8, -4, -2, 2, 4, 6, 8, 12]
                )
                if falso not in opcoes and falso >= 0:
                  opcoes.append(falso)
              random.shuffle(opcoes)

              enunciado_texto = (
                  f"Se {a} unidades custam {b}, quanto custam {c} unidades?"
              )
              questoes.append({
                  "enunciado": enunciado_texto,
                  "correta": resp_correta,
                  "opcoes": opcoes,
              })
            else:
              if nivel_num == 1:
                dividendo = random.randint(10, 99)
                divisor = random.randint(2, 9)
              elif nivel_num == 2:
                dividendo = random.randint(100, 999)
                divisor = random.randint(3, 25)
              else:
                dividendo = random.randint(1000, 9999)
                divisor = random.randint(10, 99)

              resp_correta = dividendo % divisor
              opcoes = [resp_correta]
              while len(opcoes) < 4:
                falso = random.randint(0, divisor - 1)
                if falso not in opcoes:
                  opcoes.append(falso)
              random.shuffle(opcoes)

              enunciado_texto = f"Qual é o resto da divisão inteira de {dividendo} por {divisor}? ({dividendo} mod {divisor})"
              questoes.append({
                  "enunciado": enunciado_texto,
                  "correta": resp_correta,
                  "opcoes": opcoes,
              })

          st.session_state.questoes_jogo = questoes
          st.session_state.jogo_a_decorrer = True
          st.rerun()

        st.markdown("---")
        st.markdown("🏆 **Ranking de Competição Global (Top 10):**")
        ranking = obter_ranking_jogo()
        if ranking:
          for idx, (aut, mod, niv, pts, t_tot, dat) in enumerate(ranking, 1):
            st.markdown(
                f"**{idx}. {aut}** — [{mod}] Nível {niv} | **{pts}/10** corretas"
                f" em **{t_tot:.1f}s** <small>({dat})</small>",
                unsafe_allow_html=True,
            )
        else:
          st.info("Ainda não há pontuações registadas. Sê o primeiro a jogar!")

      else:
        idx = st.session_state.pergunta_atual_idx
        questoes = st.session_state.questoes_jogo
        modo_atual = st.session_state.modo_jogo

        if idx < 10:
          q = questoes[idx]
          st.markdown(
              f"### Exercício {idx + 1} de 10 — Modo: {modo_atual} (Nível"
              f" {st.session_state.nivel_jogo})"
          )
          st.markdown(
              f'<div class="meu-cartao" style="text-align: center;"><h3'
              f' class="titulo-destaque">{q["enunciado"]}</h3></div>',
              unsafe_allow_html=True,
          )

          escolha_usuario = st.radio(
              "Seleciona a resposta correta:", q["opcoes"], key=f"resp_q_{idx}"
          )

          if st.button("Confirmar Resposta"):
            if escolha_usuario == q["correta"]:
              st.session_state.pontos_jogo += 1
              frases_parabens = [
                  "🎉 Fantástico! Resposta certeira!",
                  "🔥 Excelente! Estás a dominar os números!",
                  "⭐ Brilhante! Continua com esse ritmo!",
                  "🚀 Mandaste muito bem! Parabéns!",
                  "👏 Perfeito! O teu raciocínio está afiado!",
              ]
              st.success(random.choice(frases_parabens))
            else:
              st.error(f"Ops! A resposta correta era {q['correta']}.")

            st.session_state.pergunta_atual_idx += 1
            st.rerun()
        else:
          tempo_fim = datetime.now().timestamp()
          tempo_total = round(tempo_fim - st.session_state.tempo_inicio, 2)
          pontos = st.session_state.pontos_jogo
          nivel = st.session_state.nivel_jogo
          modo = st.session_state.modo_jogo

          guardar_pontuacao_jogo(
              st.session_state.usuario_atual, modo, nivel, pontos, tempo_total
          )

          st.markdown(
              '<div class="meu-cartao" style="text-align: center;">'
              '<h2 class="titulo-destaque">🎉 Desafio Concluído com Sucesso!</h2>'
              f"<p>Modo: <b>{modo}</b> | Nível: <b>{nivel}</b></p>"
              f"<p>Acertaste <b>{pontos} de 10</b> exercícios.</p>"
              f"<p>Tempo total: <b>{tempo_total} segundos</b>.</p>"
              "<p style='color: #38bdf8; font-weight: bold;'>Incrível esforço! O teu cérebro agradece este treino matemático! 🧠✨</p>"
              "</div>",
              unsafe_allow_html=True,
          )

          if st.button("Jogar Novamente"):
            st.session_state.jogo_a_decorrer = False
            st.rerun()

    else:
      st.markdown(
          '<h3 class="titulo-destaque">🎲 Sorte do Dado Matemático</h3>',
          unsafe_allow_html=True,
      )
      st.markdown(
          '<p class="texto-suave">Escolhe um número de 1 a 6. Depois, rola o dado'
          " do sistema. Se a tua sorte acertar no número do dado, ganhas uma"
          " **Carta Secreta** com uma fórmula ou curiosidade matemática"
          " exclusiva!</p>",
          unsafe_allow_html=True,
      )

      col_d1, col_d2 = st.columns(2)
      with col_d1:
        numero_escolhido = st.number_input(
            "Escolhe o teu palpite (1 a 6):", min_value=1, max_value=6, value=1
        )

      if st.button("🎲 Rolar o Dado da Sorte!"):
        resultado_dado = random.randint(1, 6)
        st.session_state.resultado_dado = resultado_dado
        st.session_state.dado_jogado = True

        cartas_curiosidades = [
            (
                "📜 Carta Secreta #1: A Identidade de Euler",
                "Fórmula: $e^{i\\pi} + 1 = 0$\n\nCuriosidade: Considerada a"
                " fórmula mais bonita da matemática, pois une cinco das"
                " constantes mais importantes ($0, 1, \\pi, e, i$).",
            ),
            (
                "📜 Carta Secreta #2: Teorema de Pitágoras",
                "Fórmula: $a^2 + b^2 = c^2$\n\nCuriosidade: Essencial na"
                " geometria para calcular distâncias entre pontos e em"
                " construções civis há milhares de anos.",
            ),
            (
                "📜 Carta Secreta #3: A Sétima Maravilha (Número Pi)",
                "Fórmula: $\\pi \\approx 3.14159...$\n\nCuriosidade: É um"
                " número irracional que representa a proporção entre o"
                " perímetro de qualquer círculo e o seu diâmetro.",
            ),
            (
                "📜 Carta Secreta #4: Soma de PA (Progressão Aritmética)",
                "Fórmula: $S_n = \\frac{(a_1 + a_n) \\cdot n}{2}$\n\nCuriosidade:"
                " Diz a lenda que o jovem Gauss descobriu esta fórmula em"
                " segundos na escola primária para somar números de 1 a"
                " 100!",
            ),
            (
                "📜 Carta Secreta #5: Sequência de Fibonacci",
                "Fórmula: $F_n = F_{n-1} + F_{n-2}$\n\nCuriosidade: Presente"
                " em toda a natureza, desde a disposição das pétalas de flores"
                " até às espirais das galáxias.",
            ),
            (
                "📜 Carta Secreta #6: Propriedade dos Restos (Congruência)",
                "Fórmula: $a \\equiv b \\pmod m$\n\nCuriosidade: Usada"
                " profundamente na criptografia moderna (como na segurança dos"
                " telemóveis e bancos digitais)!",
            ),
            (
                "📜 Carta Secreta #7: Sobre números primos",
                "2 é o único número primo par.",
            ),
            (
                "📜 Carta Secreta #8: Números pares vs primos",
                "Nem todo número ímpar é primo, como por exemplo o número 21.",
            ),
        ]
        st.session_state.carta_sorteada = cartas_curiosidades[
            resultado_dado - 1
        ]

      if st.session_state.dado_jogado:
        res = st.session_state.resultado_dado
        st.markdown(
            f"### 🎲 O dado tirou: **{res}**", unsafe_allow_html=True
        )

        if numero_escolhido == res:
          titulo_carta, texto_carta = st.session_state.carta_sorteada
          st.success(
              f"🎉 PARABÉNS! Acertaste em cheio na previsão do dado!"
              " Conquistaste uma Carta Secreta!"
          )
          st.markdown(
              f"""
                <div class="carta-matematica">
                    <h3 style="color: #38bdf8;">{titulo_carta}</h3>
                    <p style="white-space: pre-wrap; color: #f8fafc; font-size: 1.05rem;">{texto_carta}</p>
                </div>
                """,
              unsafe_allow_html=True,
          )
        else:
          st.warning(
              f"Quase! Escolheste o {numero_escolhido} mas o dado deu"
              f" {res}. Tenta novamente para desbloquear a carta secreta!"
          )

  # --- ABA 4: PERFIL ---
  with aba_perfil:
    st.markdown(
        '<div class="meu-cartao">'
        '<h3 class="titulo-destaque">⚙️ Personalizar Perfil & Avatar</h3>'
        '<p class="texto-suave">Escolhe uma foto do teu dispositivo ou um avatar padrão para te representar no chat.</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)

    with col_a:
      st.markdown("#### 🖼️ Enviar Foto Personalizada")
      foto_up = st.file_uploader(
          "Escolhe uma imagem (JPG, PNG)",
          type=["jpg", "jpeg", "png"],
          key="upload_foto_perfil",
      )
      if foto_up is not None:
        os.makedirs(AVATAR_DIR, exist_ok=True)
        caminho_foto = os.path.join(
            AVATAR_DIR, f"{st.session_state.usuario_atual}_perfil.jpg"
        )
        with open(caminho_foto, "wb") as f:
          f.write(foto_up.getbuffer())

        if st.button("Guardar Nova Foto de Perfil"):
          atualizar_avatar_bd(st.session_state.usuario_atual, caminho_foto)
          st.session_state.avatar_atual = caminho_foto
          st.success("Foto de perfil atualizada com sucesso!")
          st.rerun()

    with col_b:
      st.markdown("#### 🎭 Ou Selecionar um Emoji / Avatar Padrão")
      escolha_emoji = st.selectbox(
          "Escolhe um ícone:",
          ["👤", "👨‍💻", "📚", "📐", "🚀", "💡", "🎯", "⭐", "🦊", "🦁"],
      )
      if st.button("Definir Emoji como Avatar"):
        atualizar_avatar_bd(st.session_state.usuario_atual, escolha_emoji)
        st.session_state.avatar_atual = escolha_emoji
        st.success("Avatar alterado com sucesso!")
        st.rerun()
