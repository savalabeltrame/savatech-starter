import streamlit as st
import os
from core.database import inicializar_db, get_connection
from core.auth import mostrar_login

st.set_page_config(page_title="Savatech Starter", page_icon="🏪", layout="wide")

inicializar_db()

# --- CONTROL DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = None
    st.session_state['user_role'] = None

if not st.session_state['logged_in']:
    mostrar_login()
    st.stop()

# --- Obtener rol del usuario ---
user_role = st.session_state.get('user_role', 'cajero')

# --- OCULTAR MENÚ AUTOMÁTICO SI NO ES ADMIN ---
if user_role != 'admin':
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavContainer"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# --- SIDEBAR CON IDENTIDAD DE LA EMPRESA ---
conn = get_connection()
empresa = conn.execute("SELECT * FROM config_empresa WHERE id = 1").fetchone()
conn.close()

with st.sidebar:
    if empresa['logo_path'] and os.path.exists(empresa['logo_path']):
        st.image(empresa['logo_path'], width=180)
    else:
        st.markdown("## 🏪")
    st.title(empresa['nome_empresa'])
    st.caption(f"Plano: {empresa['plano']} | 👤 {st.session_state['user_name']}")

    if user_role == 'admin':
        st.success("👑 Administrador")
    else:
        st.info("🧾 Cajero")
        st.page_link("app.py", label="🏠 Inicio", use_container_width=True)
        st.page_link("pages/04_caixa.py", label="🧾 Caixa PDV", use_container_width=True)
        st.page_link("pages/05_clientes.py", label="👥 Clientes", use_container_width=True)
        st.page_link("pages/02_produtos.py", label="📦 Consulta de Produtos", use_container_width=True)

    st.markdown("---")
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['user_name'] = None
        st.session_state['user_role'] = None
        st.rerun()

# ===== PANTALLA PRINCIPAL (DASHBOARD) =====
st.title(f"🏪 Bem-vindo, {st.session_state['user_name']}!")
st.markdown("### Selecione um módulo para começar:")

st.markdown("---")

if user_role == 'admin':
    # ===== ADMIN VE TODO =====
    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("app.py", label="🏠 Inicio", use_container_width=True, disabled=True)
    with col2:
        st.page_link("pages/04_caixa.py", label="🧾 Caixa PDV", use_container_width=True)
    with col3:
        st.page_link("pages/05_clientes.py", label="👥 Clientes", use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔧 Administração")

    col4, col5, col6 = st.columns(3)
    with col4:
        st.page_link("pages/01_dashboard.py", label="📊 Dashboard", use_container_width=True)
    with col5:
        st.page_link("pages/02_produtos.py", label="📦 Produtos", use_container_width=True)
    with col6:
        st.page_link("pages/07_relatorios.py", label="📈 Relatórios", use_container_width=True)

    col7, col8, col9 = st.columns(3)
    with col7:
        st.page_link("pages/06_cierre_caixa.py", label="🔐 Cierre de Caixa", use_container_width=True)
    with col8:
        st.page_link("pages/98_usuarios.py", label="👤 Usuários", use_container_width=True)
    with col9:
        st.page_link("pages/99_config_empresa.py", label="⚙️ Configuração", use_container_width=True)

    st.markdown("---")
    st.info("💡 También puedes usar el menú de la barra lateral izquierda.")

else:
    # ===== CAJERO: CAIXA, CLIENTES Y CONSULTA DE PRODUTOS =====
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.page_link("app.py", label="🏠 Inicio", use_container_width=True, disabled=True)
    with col2:
        st.page_link("pages/04_caixa.py", label="🧾 Caixa PDV", use_container_width=True)
    with col3:
        st.page_link("pages/05_clientes.py", label="👥 Clientes", use_container_width=True)
    with col4:
        st.page_link("pages/02_produtos.py", label="📦 Consulta Produtos", use_container_width=True)

    st.markdown("---")
    st.info("💡 Como cajero tienes acceso a Caixa, Clientes y consulta de códigos/precios de productos.")