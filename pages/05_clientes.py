import streamlit as st
import pandas as pd
from core.database import get_connection

st.header("👥 Gestão de Clientes")

conn = get_connection()

# =========================
# FORMULARIO NOVO CLIENTE
# =========================
st.subheader("➕ Cadastrar Novo Cliente")

with st.form("form_cliente"):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome *", placeholder="João Silva")
        cpf = st.text_input("CPF (opcional)", placeholder="123.456.789-00", max_chars=14)
        telefone = st.text_input("Telefone", placeholder="(11) 98765-4321")
    with col2:
        email = st.text_input("E-mail", placeholder="joao@email.com")
        tipo = st.selectbox("Tipo de Cliente", ["Normal", "VIP", "Atacado", "Funcionário"])

    if st.form_submit_button("💾 Salvar Cliente", type="primary", use_container_width=True):
        if not nome.strip():
            st.error("❌ O nome é obrigatório.")
        else:
            try:
                conn.execute(
                    "INSERT INTO clientes (nome, cpf, telefone, email, tipo_cliente) VALUES (?,?,?,?,?)",
                    (nome, cpf if cpf else None, telefone, email, tipo)
                )
                conn.commit()
                st.success(f"✅ Cliente '{nome}' cadastrado com sucesso!")
                st.rerun()
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    st.error("❌ Esse CPF já está cadastrado.")
                else:
                    st.error(f"❌ Erro: {e}")

st.markdown("---")

# =========================
# LISTA DE CLIENTES
# =========================
st.subheader("📋 Clientes Cadastrados")

df = pd.read_sql_query(
    "SELECT id, nome, cpf, telefone, email, tipo_cliente FROM clientes ORDER BY nome",
    conn
)

if df.empty:
    st.info("ℹ️ Ainda não há clientes cadastrados.")
else:
    # Buscador
    busca = st.text_input("🔍 Buscar por nome ou CPF", key="busca_cliente")
    if busca:
        df_filtrado = df[
            df['nome'].str.contains(busca, case=False, na=False) |
            df['cpf'].str.contains(busca, case=False, na=False)
        ]
    else:
        df_filtrado = df

    st.caption(f"Total: {len(df_filtrado)} cliente(s)")
    st.dataframe(
        df_filtrado.rename(columns={
            "id": "ID", "nome": "Nome", "cpf": "CPF",
            "telefone": "Telefone", "email": "E-mail", "tipo_cliente": "Tipo"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # =========================
    # HISTORIAL DE COMPRAS
    # =========================
    st.subheader("📊 Histórico de Compras")

    opcoes = df_filtrado["nome"].tolist()
    cliente_sel = st.selectbox(
        "Selecionar cliente para ver histórico",
        ["— selecione —"] + opcoes
    )

    if cliente_sel != "— selecione —":
        cliente = df_filtrado[df_filtrado["nome"] == cliente_sel].iloc[0]
        id_cliente = int(cliente["id"])

        info = st.columns(3)
        info[0].markdown(f"**👤 Nome:** {cliente['nome']}")
        info[1].markdown(f"**🆔 CPF:** {cliente['cpf'] or '—'}")
        info[2].markdown(f"**⭐ Tipo:** {cliente['tipo_cliente']}")

        vendas = pd.read_sql_query(
            """SELECT v.data_venda, v.numero_cupom, v.codigo_producto,
                      v.cantidad, v.total, v.forma_pagamento,
                      p.nombre_producto
               FROM vendas v
               LEFT JOIN produtos p ON v.codigo_producto = p.codigo_producto
               WHERE v.cliente_id = ?
               ORDER BY v.data_venda DESC""",
            conn,
            params=(id_cliente,)
        )

        if vendas.empty:
            st.info("ℹ️ Esse cliente ainda não realizou compras.")
        else:
            total_gasto = float(vendas['total'].sum())
            num_compras = int(vendas['numero_cupom'].nunique())

            m1, m2, m3 = st.columns(3)
            m1.metric("🛍️ Nº de compras", num_compras)
            m2.metric("💰 Total gasto", f"R$ {total_gasto:.2f}")
            m3.metric("🎯 Ticket médio", f"R$ {total_gasto / num_compras:.2f}")

            st.dataframe(
                vendas.rename(columns={
                    "data_venda": "Data", "numero_cupom": "Cupom",
                    "nombre_producto": "Produto", "cantidad": "Qtd",
                    "total": "Total", "forma_pagamento": "Pagamento"
                }),
                use_container_width=True,
                hide_index=True
            )

    st.markdown("---")

    # =========================
    # EXCLUIR CLIENTE
    # =========================
    st.subheader("🗑️ Excluir Cliente")
    cliente_del = st.selectbox(
        "Selecionar cliente para excluir",
        df["nome"].tolist(),
        format_func=lambda n: f"{n} - {df[df.nome==n].iloc[0]['cpf'] or 'sem CPF'}"
    )
    if st.button("🗑️ Excluir Selecionado", type="primary", use_container_width=True):
        cli_id = int(df[df.nome == cliente_del].iloc[0]["id"])
        conn.execute("DELETE FROM clientes WHERE id = ?", (cli_id,))
        conn.commit()
        st.success(f"✅ Cliente '{cliente_del}' excluído!")
        st.rerun()

conn.close()