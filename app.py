import streamlit as st
import os
from core.database import inicializar_db, get_connection
from core.auth import mostrar_login

st.set_page_config(page_title="Savatech Starter", page_icon="🏪", layout="wide")

# --- INICIALIZACIÓN DE BASE DE DATOS Y RESGUARDOS ---
inicializar_db()

# Inyector de seguridad redundante para garantizar la existencia de la columna Pix
conn_alter = get_connection()
try:
    conn_alter.execute("ALTER TABLE config_empresa ADD COLUMN pix_chave TEXT;")
    conn_alter.commit()
except Exception:
    pass
finally:
    conn_alter.close()

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

# --- DEFINICIÓN DE PÁGINAS MEDIANTE OBJETOS ---
# Esto evita fallas con nombres de archivos repetidos y repara el KeyError: 'url_pathname'
pag_caixa = st.Page("pages/04_caixa.py", title="Caixa PDV", icon="🧾")
pag_clientes = st.Page("pages/05_clientes.py", title="Clientes", icon="👥")
pag_dashboard = st.Page("pages/01_dashboard.py", title="Dashboard", icon="📊")
pag_relatorios = st.Page("pages/07_relatorios.py", title="Relatórios", icon="📈")
pag_cierre = st.Page("pages/06_cierre_caixa.py", title="Cierre de Caixa", icon="🔐")
pag_usuarios = st.Page("pages/98_usuarios.py", title="Usuários", icon="👤")
pag_config = st.Page("pages/99_config_empresa.py", title="Configuração", icon="⚙️")

# --- OCULTAR MENÚ AUTOMÁTICO SI NO ES ADMIN ---
if user_role != 'admin':
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"], [data-testid="stSidebarNavContainer"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# --- SIDEBAR CON IDENTIDAD DE LA EMPRESA ---
conn = get_connection()
empresa = conn.execute("SELECT * FROM config_empresa WHERE id = 1").fetchone()
conn.close()

with st.sidebar:
    if empresa and empresa['logo_path'] and os.path.exists(empresa['logo_path']):
        st.image(empresa['logo_path'], width=180)
    else:
        st.markdown("## 🏪")
    
    if empresa:
        st.title(empresa['nome_empresa'])
        st.caption(f"Plano: {empresa['plano']} | 👤 {st.session_state['user_name']}")
    else:
        st.title("Minha Loja")
        st.caption(f"👤 {st.session_state['user_name']}")
        
    if user_role == 'admin':
        st.success("👑 Administrador")
    else:
        st.info("🧾 Cajero")
    
    if st.button("🏠 Inicio", use_container_width=True):
        st.rerun()
        
    st.page_link(pag_caixa, use_container_width=True)
    st.page_link(pag_clientes, use_container_width=True)
    
    st.markdown("---")
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['user_name'] = None
        st.session_state['user_role'] = None
        st.rerun()

# ===== PANTALLA PRINCIPAL DE BIENVENIDA =====
st.title(f"🏪 Bem-vindo, {st.session_state['user_name']}!")
st.markdown("### Selecione um módulo para começar:")
st.markdown("---")

if user_role == 'admin':
    # ===== PANEL VISUAL COMPLETO PARA EL ADMINISTRADOR =====
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏠 Inicio (Página Actual)", use_container_width=True, disabled=True):
            pass
    with col2:
        st.page_link(pag_caixa, use_container_width=True)
    with col3:
        st.page_link(pag_clientes, use_container_width=True)
        
    st.markdown("---")
    st.markdown("### 🔧 Administração")
    
    col4, col5, col6 = st.columns(3)
    with col4:
        st.page_link(pag_dashboard, use_container_width=True)
    with col5:
        st.info("📦 Productos administrados desde Caixa")
    with col6:
        st.page_link(pag_relatorios, use_container_width=True)
        
    col7, col8, col9 = st.columns(3)
    with col7:
        st.page_link(pag_cierre, use_container_width=True)
    with col8:
        st.page_link(pag_usuarios, use_container_width=True)
    with col9:
        st.page_link(pag_config, use_container_width=True)
        
    st.markdown("---")
    st.info("💡 También puedes usar el menú de la barra lateral izquierda.")

else:
    # ===== PANEL COMPACTO PARA EL CAJERO =====
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏠 Inicio", use_container_width=True):
            st.rerun()
    with col2:
        st.page_link(pag_caixa, use_container_width=True)
    with col3:
        st.page_link(pag_clientes, use_container_width=True)
        
    st.markdown("---")
    st.info("💡 Como cajero tienes acceso a Caixa y Clientes.")
