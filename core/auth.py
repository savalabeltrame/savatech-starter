import streamlit as st
import hashlib
from core.database import get_connection


def hash_senha(senha):
    """Genera un hash SHA-256 de la contraseña."""
    return hashlib.sha256(senha.encode()).hexdigest()


def mostrar_login():
    """Muestra la pantalla de login con diseño profesional."""
    
    # Configuración de la página de login
    st.set_page_config(page_title="Login - Savatech", page_icon="🔐", layout="centered")
    
    # Centrar el contenido
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Logo y título
        st.markdown(
            """
            <div style='text-align: center;'>
                <h1>🏪 Savatech Starter</h1>
                <p style='color: gray;'>Sistema de Gestão Comercial</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        # Formulario de login
        with st.form("login_form"):
            st.markdown("### 🔐 Acesso ao Sistema")
            st.caption("Digite suas credenciais para continuar")
            
            usuario = st.text_input("👤 Usuário", placeholder="admin")
            senha = st.text_input("🔑 Senha", type="password", placeholder="••••••")
            
            entrar = st.form_submit_button("Entrar", use_container_width=True, type="primary")
            
            if entrar:
                if not usuario.strip() or not senha.strip():
                    st.error("❌ Preencha usuário e senha.")
                else:
                    conn = get_connection()
                    
                    # Buscar usuario (acepta tanto hash como texto plano para compatibilidad)
                    row = conn.execute(
                        "SELECT nome, nivel, senha FROM usuarios WHERE usuario = ?",
                        (usuario,)
                    ).fetchone()
                    
                    if row:
                        # Verificar contraseña (acepta hash o texto plano)
                        senha_hash = hash_senha(senha)
                        senha_correta = (
                            row['senha'] == senha_hash or  # Hash correcto
                            row['senha'] == senha  # Texto plano (legacy)
                        )
                        
                        if senha_correta:
                            st.session_state['logged_in'] = True
                            st.session_state['user_name'] = row['nome']
                            st.session_state['user_role'] = row['nivel']
                            
                            # Si la contraseña está en texto plano, actualizarla a hash
                            if row['senha'] == senha:
                                conn.execute(
                                    "UPDATE usuarios SET senha = ? WHERE usuario = ?",
                                    (senha_hash, usuario)
                                )
                                conn.commit()
                            
                            conn.close()
                            st.success("✅ Login realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Senha incorreta.")
                    else:
                        st.error("❌ Usuário não encontrado.")
                    
                    conn.close()
        
        st.markdown("---")
        st.caption("💡 Usuário padrão: admin | Senha: admin123")


def logout():
    """Cierra la sesión del usuario."""
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = None
    st.session_state['user_role'] = None
    st.rerun()


def requer_login():
    """Verifica si el usuario está logueado, si no, redirige al login."""
    if not st.session_state.get('logged_in', False):
        mostrar_login()
        st.stop()


def requer_rol(rol_requerido):
    """Verifica si el usuario tiene el rol necesario para acceder."""
    requer_login()
    if st.session_state.get('user_role') != rol_requerido:
        st.error(f"🚫 No tienes permisos para acceder a esta página.")
        st.page_link("app.py", label="🏠 Volver al Inicio", use_container_width=True)
        st.stop()