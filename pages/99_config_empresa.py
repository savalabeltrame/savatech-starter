import streamlit as st
import os
from PIL import Image
from core.database import get_connection, LOGOS_DIR
# --- GUARDIA: solo administrador ---
if st.session_state.get('user_role') != 'admin':
    st.error("🚫 Solo el administrador puede ver esta página.")
    st.page_link("app.py", label="🏠 Volver al Inicio", use_container_width=True)
    st.stop()

st.header("🏢 Configuração da Minha Empresa")
st.info("ℹ️ Personalize os dados que aparecerão nos cupons y en el sistema.")

conn = get_connection()
emp = conn.execute("SELECT * FROM config_empresa WHERE id = 1").fetchone()

with st.form("form_empresa"):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome da Empresa *", value=emp['nome_empresa'])
        cnpj = st.text_input("CNPJ / CPF", value=emp['cnpj'] or '')
        telefone = st.text_input("Telefone / WhatsApp", value=emp['telefone'] or '')
    with col2:
        email = st.text_input("E-mail", value=emp['email'] or '')
        endereco = st.text_input("Endereço", value=emp['endereco'] or '')
        plano = st.selectbox(
            "Plano Contratado",
            options=['Starter', 'Pro', 'Enterprise'],
            index=['Starter', 'Pro', 'Enterprise'].index(emp['plano'])
        )

    logo_file = st.file_uploader("🎨 Logo da Empresa (PNG/JPG)", type=['png', 'jpg', 'jpeg'])

    salvar = st.form_submit_button(
        "💾 Salvar Configurações",
        type="primary",
        use_container_width=True
    )

if salvar:
    try:
        if not nome:
            st.session_state["msg_config"] = ("error", "❌ Informe o nome da empresa.")
        else:
            logo_path = emp['logo_path'] or ''

            if logo_file is not None:
                os.makedirs(LOGOS_DIR, exist_ok=True)
                logo_path = os.path.join(LOGOS_DIR, 'logo_empresa.png')
                logo_file.seek(0)
                Image.open(logo_file).save(logo_path, format="PNG")

            cur = conn.execute("""
                UPDATE config_empresa
                SET nome_empresa=?, cnpj=?, endereco=?, telefone=?, email=?, logo_path=?, plano=?
                WHERE id = 1
            """, (nome, cnpj, endereco, telefone, email, logo_path, plano))
            conn.commit()

            if cur.rowcount == 0:
                st.session_state["msg_config"] = (
                    "warning",
                    "⚠️ Nenhuma linha atualizada. Verifique se existe id=1 na tabela config_empresa."
                )
            else:
                st.session_state["msg_config"] = ("success", "✅ Configurações salvas com sucesso!")

    except Exception as e:
        st.session_state["msg_config"] = ("error", f"❌ Erro ao salvar: {e}")

    st.rerun()

if "msg_config" in st.session_state:
    tipo, texto = st.session_state.pop("msg_config")
    if tipo == "success":
        st.success(texto)
        st.balloons()
    elif tipo == "warning":
        st.warning(texto)
    else:
        st.error(texto)

conn.close()
if emp['logo_path'] and os.path.exists(emp['logo_path']):
    st.subheader("🎨 Logo atual")
    st.image(emp['logo_path'], width=200)
else:
    st.info("Nenhum logo salvo ainda.")
  