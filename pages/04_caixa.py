import streamlit as st
import pandas as pd
from datetime import datetime
from core.database import get_connection
from utils.cupom_pdf import gerar_pdf_cupom

st.header("💰 Caixa PDV")

conn = get_connection()

# =========================
# CARGAR DATOS
# =========================
df_produtos = pd.read_sql_query(
    "SELECT codigo_producto, nombre_producto, precio_venta, estoque_atual FROM produtos ORDER BY nombre_producto",
    conn
)

df_clientes = pd.read_sql_query(
    "SELECT id, nome, cpf, telefone FROM clientes ORDER BY nome",
    conn
)

if df_produtos.empty:
    st.warning("⚠️ Cadastre produtos antes de vender.")
    st.stop()

# =========================
# INICIALIZAR CARRITO
# =========================
if "carrinho" not in st.session_state:
    st.session_state["carrinho"] = []

# =========================
# AGREGAR PRODUCTO AL CARRITO
# =========================
st.subheader("➕ Agregar produto ao carrinho")

col_add1, col_add2, col_add3 = st.columns([3, 1, 1])

with col_add1:
    codigo_sel = st.selectbox(
        "Produto",
        df_produtos['codigo_producto'].tolist(),
        key="sel_produto",
        format_func=lambda c: f"{c} - {df_produtos[df_produtos.codigo_producto==c].iloc[0]['nombre_producto']} (estoque: {df_produtos[df_produtos.codigo_producto==c].iloc[0]['estoque_atual']})"
    )

with col_add2:
    qtd_sel = st.number_input("Qtd", min_value=1, step=1, value=1, key="qtd_add")

with col_add3:
    st.write("")
    st.write("")
    if st.button("➕ Adicionar", use_container_width=True, type="primary"):
        prod = df_produtos[df_produtos.codigo_producto == codigo_sel].iloc[0]
        estoque_disp = prod['estoque_atual']

        # Verificar si ya está en el carrito
        ya_en_carrinho = sum(i['qtd'] for i in st.session_state["carrinho"] if i['codigo'] == codigo_sel)
        qtd_total = ya_en_carrinho + qtd_sel

        if qtd_total > estoque_disp:
            st.error(f"❌ Estoque insuficiente. Disponível: {estoque_disp} (no carrinho já há {ya_en_carrinho})")
        else:
            # Agregar o sumar al carrito
            agregado = False
            for item in st.session_state["carrinho"]:
                if item['codigo'] == codigo_sel:
                    item['qtd'] += qtd_sel
                    item['subtotal'] = item['qtd'] * item['preco']
                    agregado = True
                    break

            if not agregado:
                st.session_state["carrinho"].append({
                    'codigo': codigo_sel,
                    'nome': prod['nombre_producto'],
                    'qtd': qtd_sel,
                    'preco': float(prod['precio_venta']),
                    'subtotal': qtd_sel * float(prod['precio_venta'])
                })
            st.rerun()

st.markdown("---")

# =========================
# CARRITO VISUAL
# =========================
st.subheader("🛒 Carrinho")

if not st.session_state["carrinho"]:
    st.info("🛒 O carrinho está vazio. Adicione produtos acima.")
else:
    # Tabla con botones para modificar cantidades
    for idx, item in enumerate(st.session_state["carrinho"]):
        col_item = st.columns([0.5, 3, 1, 1.2, 1.2, 1])

        with col_item[0]:
            if st.button("❌", key=f"rm_{idx}", help="Remover"):
                st.session_state["carrinho"].pop(idx)
                st.rerun()

        with col_item[1]:
            st.markdown(f"**{item['nome']}**")
            st.caption(f"Cód: {item['codigo']}")

        with col_item[2]:
            if st.button("➖", key=f"menos_{idx}"):
                if item['qtd'] > 1:
                    st.session_state["carrinho"][idx]['qtd'] -= 1
                    st.session_state["carrinho"][idx]['subtotal'] = st.session_state["carrinho"][idx]['qtd'] * item['preco']
                else:
                    st.session_state["carrinho"].pop(idx)
                st.rerun()

        with col_item[3]:
            st.markdown(f"**{item['qtd']}x**")

        with col_item[4]:
            if st.button("➕", key=f"mais_{idx}"):
                prod_atual = df_produtos[df_produtos.codigo_producto == item['codigo']].iloc[0]
                if item['qtd'] < prod_atual['estoque_atual']:
                    st.session_state["carrinho"][idx]['qtd'] += 1
                    st.session_state["carrinho"][idx]['subtotal'] = st.session_state["carrinho"][idx]['qtd'] * item['preco']
                else:
                    st.toast("Estoque máximo atingido.", icon="⚠️")
                st.rerun()

        with col_item[5]:
            st.markdown(f"**R$ {item['subtotal']:.2f}**")

    st.markdown("---")

    # =========================
    # CLIENTE
    # =========================
    st.subheader("👤 Cliente")
    opcoes_cliente = ["Consumidor Final"] + [f"{row['nome']} - CPF: {row['cpf']}" for _, row in df_clientes.iterrows()]
    cliente_sel = st.selectbox("Selecionar cliente", opcoes_cliente, key="cliente_sel")

    # =========================
    # DESCUENTO
    # =========================
    subtotal = sum(i['subtotal'] for i in st.session_state["carrinho"])
    desconto = st.number_input("💸 Desconto (R$)", min_value=0.0, value=0.0, step=0.50, key="desconto_input")

    total = subtotal - desconto
    if total < 0:
        total = 0.0

    col_tot = st.columns(3)
    col_tot[0].metric("Subtotal", f"R$ {subtotal:.2f}")
    col_tot[1].metric("Desconto", f"R$ {desconto:.2f}")
    col_tot[2].metric("🎯 TOTAL", f"R$ {total:.2f}")

    st.markdown("---")

    # =========================
    # PAGAMENTO
    # =========================
    st.subheader("💳 Pagamento")
    forma_pagamento = st.selectbox(
        "Forma de pagamento",
        ['Dinheiro', 'Pix', 'Cartão de Crédito', 'Cartão de Débito'],
        key="forma_pag"
    )

    valor_recebido = 0.0
    troco = 0.0
    faltante = 0.0

    if forma_pagamento == 'Dinheiro':
        valor_recebido = st.number_input(
            "💵 Valor recebido do cliente (R$)",
            min_value=0.0,
            value=float(total),
            step=1.0,
            key="valor_recebido"
        )
        if valor_recebido >= total:
            troco = valor_recebido - total
            st.success(f"💵 Troco: R$ {troco:.2f}")
        else:
            faltante = total - valor_recebido
            st.error(f"⚠️ Faltante: R$ {faltante:.2f}")

    # =========================
    # FINALIZAR VENTA
    # =========================
    pode_finalizar = (forma_pagamento != 'Dinheiro') or (valor_recebido >= total)

    if st.button("✅ FINALIZAR VENDA", type="primary", use_container_width=True, disabled=not pode_finalizar):
        cupom = int(datetime.now().strftime('%Y%m%d%H%M%S'))
        usuario = st.session_state.get('user_name', 'Desconhecido')

        # Buscar cliente_id si no es Consumidor Final
        cliente_id = None
        if cliente_sel != "Consumidor Final":
            nome_cliente = cliente_sel.split(" - CPF:")[0]
            cli = df_clientes[df_clientes['nome'] == nome_cliente]
            if not cli.empty:
                cliente_id = int(cli.iloc[0]['id'])

        try:
            # Insertar cada item del carrito
            for item in st.session_state["carrinho"]:
                # Descontar stock
                conn.execute(
                    "UPDATE produtos SET estoque_atual = estoque_atual - ? WHERE codigo_producto = ?",
                    (item['qtd'], item['codigo'])
                )
                # Insertar venta
                conn.execute(
                    """INSERT INTO vendas 
                    (numero_cupom, codigo_producto, cantidad, total, forma_pagamento, usuario, cliente_id, desconto) 
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (cupom, item['codigo'], item['qtd'], item['subtotal'], forma_pagamento, usuario, cliente_id, desconto / len(st.session_state["carrinho"]))
                )

            conn.commit()
            st.session_state['ultimo_cupom'] = cupom
            st.session_state["carrinho"] = []
            st.success(f"✅ Venda registrada! Cupom {cupom} — Total R$ {total:.2f}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao registrar venda: {e}")

# =========================
# DESCARGAR CUPOM PDF
# =========================
st.markdown("---")
if 'ultimo_cupom' in st.session_state:
    cupom = st.session_state['ultimo_cupom']
    linhas = conn.execute("SELECT * FROM vendas WHERE numero_cupom = ?", (cupom,)).fetchall()

    if linhas:
        st.subheader(f"📄 Último Cupom: {cupom}")

        itens = []
        for l in linhas:
            p = conn.execute("SELECT nombre_producto, precio_venta FROM produtos WHERE codigo_producto = ?", (l['codigo_producto'],)).fetchone()
            itens.append({
                'nome': p['nombre_producto'] if p else l['codigo_producto'],
                'qtd': l['cantidad'],
                'unit': p['precio_venta'] if p else 0,
                'total': l['total']
            })

        total_cupom = sum(i['total'] for i in itens)
        desconto_total = sum(l['desconto'] for l in linhas) if 'desconto' in linhas[0].keys() else 0

        # Vista previa del ticket
        with st.expander("👁️ Ver ticket (pré-visualização)", expanded=True):
            empresa = conn.execute("SELECT nome_empresa FROM config_empresa WHERE id = 1").fetchone()
            st.markdown(f"### {empresa['nome_empresa']}")
            st.caption(f"Cupom: {cupom} | Data: {linhas[0]['data_venda']} | Forma: {linhas[0]['forma_pagamento']}")

            for i in itens:
                st.markdown(f"**{i['qtd']}x** {i['nome']} — R$ {i['unit']:.2f} → R$ {i['total']:.2f}")

            st.markdown("---")
            st.markdown(f"**Subtotal:** R$ {total_cupom:.2f}")
            if desconto_total > 0:
                st.markdown(f"**Desconto:** R$ {desconto_total:.2f}")
            st.markdown(f"### **TOTAL: R$ {total_cupom - desconto_total:.2f}**")

        # Generar PDF
        try:
            pdf_bytes = gerar_pdf_cupom(cupom, linhas[0]['data_venda'], itens, total_cupom, linhas[0]['forma_pagamento'])
            pdf_bytes = bytes(pdf_bytes)
            st.download_button(
                "📄 Baixar Cupom em PDF",
                data=pdf_bytes,
                file_name=f"cupom_{cupom}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        except Exception as e:
            st.warning(f"⚠️ Não foi possível gerar o PDF: {e}")

# Botón para limpiar carrito manualmente
if st.session_state["carrinho"]:
    st.markdown("---")
    if st.button("🗑️ Limpar carrinho (cancelar venda)", use_container_width=True):
        st.session_state["carrinho"] = []
        st.rerun()

conn.close()