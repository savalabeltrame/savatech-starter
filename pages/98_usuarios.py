import streamlit as st
import pandas as pd
from core.database import get_connection

st.header("👥 Gestão de Usuários")

# --- GUARDIA: solo administrador ---
if st.session_state.get('user_role') != 'admin':
    st.error("🚫 Solo el administrador puede ver esta página.")
    st.page_link("app.py", label="🏠 Volver al Inicio", use_container_width=True)
    st.stop()

conn = get_connection()

# =========================
# CREAR NUEVO USUARIO
# =========================
st.subheader("➕ Novo Usuário")

with st.form("form_usuario"):
    col1, col2 = st.columns(2)
    with col1:
        usuario = st.text_input("Usuário (login) *", placeholder="joao")
        nome = st.text_input("Nome completo *", placeholder="João Silva")
    with col2:
        senha = st.text_input("Senha *", type="password", placeholder="••••••")
        nivel = st.selectbox("Nível de Acesso", ["admin", "cajero"])

    if st.form_submit_button("💾 Criar Usuário", type="primary", use_container_width=True):
        if not usuario.strip() or not nome.strip() or not senha.strip():
            st.error("❌ Preencha todos os campos obrigatórios.")
        else:
            try:
                conn.execute(
                    "INSERT INTO usuarios (usuario, senha, nome, nivel) VALUES (?,?,?,?)",
                    (usuario, senha, nome, nivel)
                )
                conn.commit()
                st.success(f"✅ Usuário '{usuario}' criado com sucesso!")
                st.rerun()
            except Exception as e:
                if "UNIQUE constraint" in str(e):
                    st.error("❌ Esse nome de usuário já existe.")
                else:
                    st.error(f"❌ Erro: {e}")

st.markdown("---")

# =========================
# LISTA DE USUÁRIOS
# =========================
st.subheader("📋 Usuários Cadastrados")

df = pd.read_sql_query("SELECT id, usuario, nome, nivel FROM usuarios ORDER BY id", conn)

if not df.empty:
    st.dataframe(
        df.rename(columns={'id': 'ID', 'usuario': 'Login', 'nome': 'Nome', 'nivel': 'Nível'}),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    st.subheader("🗑️ Excluir Usuário")

    usuarios_del = df[df['usuario'] != 'admin']  # el admin no se puede borrar
    if usuarios_del.empty:
        st.info("Solo existe el usuario admin (no se puede borrar).")
    else:
        sel = st.selectbox(
            "Selecionar usuário para excluir",
            usuarios_del['usuario'].tolist(),
            format_func=lambda u: f"{u} ({usuarios_del[usuarios_del.usuario==u].iloc[0]['nome']})"
        )
        if st.button("🗑️ Excluir Selecionado", type="primary", use_container_width=True):
            conn.execute("DELETE FROM usuarios WHERE usuario = ?", (sel,))
            conn.commit()
            st.success(f"✅ Usuário '{sel}' excluído!")
            st.rerun()

conn.close()