import streamlit as st
import pandas as pd
from datetime import date
from core.database import get_connection
# --- GUARDIA: solo administrador ---
if st.session_state.get('user_role') != 'admin':
    st.error("🚫 Solo el administrador puede ver esta página.")
    st.page_link("app.py", label="🏠 Volver al Inicio", use_container_width=True)
    st.stop()

st.header("📦 Gestão de Produtos")

conn = get_connection()

# --- Detectar rol ---
user_role = st.session_state.get('user_role', 'cajero')
es_admin = (user_role == 'admin')

# Cargar todos los productos una sola vez
df_produtos = pd.read_sql_query(
    """SELECT id, codigo_producto, nombre_producto, categoria,
              precio_costo, precio_venta, estoque_atual, stock_minimo, validade
       FROM produtos ORDER BY nombre_producto""",
    conn
)

# =========================
# ZONA DE ADMINISTRACIÓN (solo admin)
# =========================
if es_admin:
    tab1, tab2, tab3 = st.tabs(["➕ Cadastrar", "✏️ Editar", "🗑️ Excluir"])

    # ----- TAB 1: CADASTRAR -----
    with tab1:
        st.subheader("➕ Novo Produto")
        with st.form("form_produto"):
            col1, col2 = st.columns(2)
            with col1:
                codigo = st.text_input("Código *", placeholder="P001")
                nome = st.text_input("Nome *", placeholder="Arroz 5kg")
                categoria = st.text_input("Categoria", placeholder="Alimentos")
                validade = st.date_input("Data de Validade (opcional)", value=None)
            with col2:
                custo = st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.01)
                venda = st.number_input("Preço de Venda (R$)", min_value=0.0, step=0.01)
                estoque = st.number_input("Estoque Inicial", min_value=0, step=1)
                minimo = st.number_input("Estoque Mínimo", min_value=0, value=5)

            if st.form_submit_button("💾 Salvar Produto", type="primary", use_container_width=True):
                if not codigo.strip() or not nome.strip():
                    st.error("❌ Preencha código e nome.")
                else:
                    validade_str = validade.strftime("%Y-%m-%d") if validade else None
                    try:
                        conn.execute(
                            """INSERT INTO produtos 
                            (codigo_producto, nombre_producto, categoria, precio_costo, 
                             precio_venta, estoque_atual, stock_minimo, validade) 
                            VALUES (?,?,?,?,?,?,?,?)""",
                            (codigo, nome, categoria, custo, venda, estoque, minimo, validade_str)
                        )
                        conn.commit()
                        st.success(f"✅ Produto '{nome}' salvo com sucesso!")
                        st.rerun()
                    except Exception as e:
                        if "UNIQUE constraint failed" in str(e):
                            st.error("❌ Já existe um produto com esse código.")
                        else:
                            st.error(f"❌ Erro: {e}")

    # ----- TAB 2: EDITAR -----
    with tab2:
        st.subheader("✏️ Editar Produto")
        if df_produtos.empty:
            st.info("ℹ️ Não há produtos para editar.")
        else:
            opcoes = [f"{row['codigo_producto']} - {row['nombre_producto']}" for _, row in df_produtos.iterrows()]
            sel = st.selectbox("Selecionar produto", opcoes, key="editar_sel")

            if sel:
                cod_sel = sel.split(" - ")[0]
                prod = df_produtos[df_produtos["codigo_producto"] == cod_sel].iloc[0]

                with st.form("form_editar"):
                    c1, c2 = st.columns(2)
                    with c1:
                        novo_nome = st.text_input("Nome", value=prod["nombre_producto"])
                        nova_cat = st.text_input("Categoria", value=prod["categoria"] or "")
                        novo_custo = st.number_input("Preço de Custo (R$)", value=float(prod["precio_costo"]), step=0.01)
                        novo_venda = st.number_input("Preço de Venda (R$)", value=float(prod["precio_venta"]), step=0.01)
                    with c2:
                        novo_estoque = st.number_input("Estoque Atual", value=int(prod["estoque_atual"]), step=1)
                        novo_min = st.number_input("Estoque Mínimo", value=int(prod["stock_minimo"]), step=1)
                        val_atual = prod["validade"]
                        val_date = pd.to_datetime(val_atual).date() if val_atual else None
                        nova_val = st.date_input("Data de Validade", value=val_date)

                    if st.form_submit_button("💾 Atualizar Produto", type="primary", use_container_width=True):
                        nova_val_str = nova_val.strftime("%Y-%m-%d") if nova_val else None
                        try:
                            conn.execute(
                                """UPDATE produtos SET
                                    nombre_producto=?, categoria=?, precio_costo=?,
                                    precio_venta=?, estoque_atual=?, stock_minimo=?, validade=?
                                   WHERE codigo_producto=?""",
                                (novo_nome, nova_cat, novo_custo, novo_venda,
                                 novo_estoque, novo_min, nova_val_str, cod_sel)
                            )
                            conn.commit()
                            st.success(f"✅ Produto '{novo_nome}' atualizado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro: {e}")

    # ----- TAB 3: EXCLUIR -----
    with tab3:
        st.subheader("🗑️ Excluir Produto")
        if df_produtos.empty:
            st.info("ℹ️ Não há produtos para excluir.")
        else:
            opcoes = [f"{row['codigo_producto']} - {row['nombre_producto']} (estoque: {row['estoque_atual']})" for _, row in df_produtos.iterrows()]
            sel = st.selectbox("Produto a excluir", opcoes, key="excluir_sel")

            if sel:
                cod_sel = sel.split(" - ")[0]
                st.warning(f"⚠️ Você está prestes a excluir permanentemente o produto **{cod_sel}**.")
                if st.button("🗑️ Confirmar Exclusão", type="primary", use_container_width=True):
                    try:
                        conn.execute("DELETE FROM produtos WHERE codigo_producto = ?", (cod_sel,))
                        conn.commit()
                        st.success("✅ Produto excluído!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")

    st.markdown("---")

else:
    # =========================
    # MODO CONSULTA (cajero)
    # =========================
    st.info("🔎 **Modo consulta:** você pode buscar códigos e preços, mas não pode alterar produtos.")

# =========================
# LISTA + BUSCADOR (para todos)
# =========================
st.subheader("📋 Lista de Produtos")

if df_produtos.empty:
    st.info("ℹ️ Nenhum produto cadastrado ainda.")
else:
    busca = st.text_input("🔍 Buscar por código, nome ou categoria", key="busca_prod")
    if busca:
        df_filtrado = df_produtos[
            df_produtos["codigo_producto"].str.contains(busca, case=False, na=False) |
            df_produtos["nombre_producto"].str.contains(busca, case=False, na=False) |
            df_produtos["categoria"].fillna("").str.contains(busca, case=False, na=False)
        ]
    else:
        df_filtrado = df_produtos

    st.caption(f"Total: {len(df_filtrado)} produto(s)")

    mostrar = df_filtrado.copy().rename(columns={
        "codigo_producto": "Código", "nombre_producto": "Nome",
        "categoria": "Categoria", "precio_costo": "Custo", "precio_venta": "Venda",
        "estoque_atual": "Estoque", "stock_minimo": "Mín", "validade": "Validade"
    })

    if es_admin:
        colunas = ["Código", "Nome", "Categoria", "Custo", "Venda", "Estoque", "Mín", "Validade"]
    else:
        # El cajero NO ve el precio de costo (margen del negocio)
        colunas = ["Código", "Nome", "Categoria", "Venda", "Estoque", "Validade"]

    st.dataframe(mostrar[colunas], use_container_width=True, hide_index=True)

    # =========================
    # ALERTAS (solo admin)
    # =========================
    if es_admin:
        st.markdown("---")
        col_alert1, col_alert2 = st.columns(2)

        with col_alert1:
            st.markdown("### 🚨 Estoque Baixo")
            baixos = df_produtos[df_produtos["estoque_atual"] <= df_produtos["stock_minimo"]]
            if baixos.empty:
                st.success("✅ Todos os produtos com estoque saudável.")
            else:
                st.error(f"{len(baixos)} produto(s) abaixo do mínimo:")
                for _, row in baixos.iterrows():
                    st.markdown(f"- **{row['nombre_producto']}** → {row['estoque_atual']} un. (mín: {row['stock_minimo']})")

        with col_alert2:
            st.markdown("### ⏰ Próximos do Vencimento")
            if df_produtos["validade"].notna().any():
                hoje = date.today()
                prods_val = df_produtos[df_produtos["validade"].notna()].copy()
                prods_val["validade_dt"] = pd.to_datetime(prods_val["validade"])
                prods_val["dias"] = (prods_val["validade_dt"].dt.date - hoje).dt.days
                por_vencer = prods_val[prods_val["dias"].between(0, 30)].sort_values("dias")
                vencidos = prods_val[prods_val["dias"] < 0]

                if not vencidos.empty:
                    st.error(f"🚨 {len(vencidos)} produto(s) **VENCIDO(S)**:")
                    for _, row in vencidos.iterrows():
                        st.markdown(f"- **{row['nombre_producto']}** → venceu há {abs(row['dias'])} dias")

                if not por_vencer.empty:
                    st.warning(f"⚠️ {len(por_vencer)} produto(s) vencem em 30 dias:")
                    for _, row in por_vencer.iterrows():
                        st.markdown(f"- **{row['nombre_producto']}** → em {row['dias']} dias")

                if vencidos.empty and por_vencer.empty:
                    st.success("✅ Nenhum produto vencido ou por vencer em 30 dias.")
            else:
                st.info("ℹ️ Nenhum produto com data de validade cadastrada.")

conn.close()