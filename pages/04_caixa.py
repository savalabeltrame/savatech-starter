import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
from core.database import get_connection
from utils.cupom_pdf import gerar_pdf_cupom

st.header("💰 Caixa PDV")

conn = get_connection()
empresa = conn.execute("SELECT * FROM config_empresa WHERE id = 1").fetchone()

df_produtos = pd.read_sql_query(
    "SELECT codigo_producto, nombre_producto, precio_venta, estoque_atual FROM produtos ORDER BY nombre_producto",
    conn
)
df_clientes = pd.read_sql_query("SELECT id, nome, cpf, telefone FROM clientes ORDER BY nome", conn)

if df_produtos.empty:
    st.warning("⚠️ Cadastre produtos antes de vender.")
    st.stop()

if "carrinho" not in st.session_state:
    st.session_state["carrinho"] = []

# =========================
# GENERADOR PIX (QR Code oficial BR Code)
# =========================
def emv(pid, payload):
    return f"{pid:02}{len(payload):02}{payload}"

def crc16(payload):
    payload += "6304"
    crc = 0xFFFF
    for ch in payload:
        crc ^= ord(ch) << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if (crc & 0x8000) else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"

def gerar_pix(chave, valor, nome):
    nome = (nome or "EMPRESA")[:25].upper()
    payload = (
        emv(0, "01")
        + emv(26, emv(0, "br.gov.bcb.pix") + emv(1, chave))
        + emv(52, "0000")
        + emv(53, "986")
        + (emv(54, f"{valor:.2f}") if valor > 0 else "")
        + emv(58, "BR")
        + emv(59, nome)
        + emv(60, "BRASIL")
        + emv(62, emv(5, "***"))
    )
    return payload + crc16(payload)

# =========================
# FUNCIÓN AGREGAR AL CARRITO
# =========================
def agregar(codigo, qtd):
    prod = df_produtos[df_produtos.codigo_producto == codigo]
    if prod.empty:
        return False, f"Código no encontrado: {codigo}"
    prod = prod.iloc[0]
    ya = sum(i['qtd'] for i in st.session_state["carrinho"] if i['codigo'] == codigo)
    if ya + qtd > prod['estoque_atual']:
        return False, f"Estoque insuficiente. Disponível: {prod['estoque_atual']}"
    for item in st.session_state["carrinho"]:
        if item['codigo'] == codigo:
            item['qtd'] += qtd
            item['subtotal'] = item['qtd'] * item['preco']
            return True, prod['nombre_producto']
    st.session_state["carrinho"].append({
        'codigo': codigo,
        'nome': prod['nombre_producto'],
        'qtd': qtd,
        'preco': float(prod['precio_venta']),
        'subtotal': qtd * float(prod['precio_venta'])
    })
    return True, prod['nombre_producto']

# =========================
# 📷 SCANNER LÁSER / DIGITAR CÓDIGO
# =========================
st.subheader("📷 Escanear producto")
scan = st.text_input(
    "Pase el lector láser o digite el código y presione Enter",
    key="scan_input",
    placeholder="Ej: P001",
)

if scan and scan != st.session_state.get("last_scan"):
    st.session_state["last_scan"] = scan
    ok, msg = agregar(scan.strip(), 1)
    if ok:
        st.session_state["scan_input"] = ""
        st.toast(f"🛒 {msg} agregado al carrinho", icon="✅")
        st.rerun()
    else:
        st.error(f"❌ {msg}")

st.markdown("---")

# =========================
# AGREGAR MANUAL (selectbox)
# =========================
with st.expander("➕ Agregar manualmente (sin scanner)"):
    col_add1, col_add2, col_add3 = st.columns([3, 1, 1])
    with col_add1:
        codigo_sel = st.selectbox(
            "Produto", df_produtos['codigo_producto'].tolist(), key="sel_produto",
            format_func=lambda c: f"{c} - {df_produtos[df_produtos.codigo_producto==c].iloc[0]['nombre_producto']} (estoque: {df_produtos[df_produtos.codigo_producto==c].iloc[0]['estoque_atual']})"
        )
    with col_add2:
        qtd_sel = st.number_input("Qtd", min_value=1, step=1, value=1, key="qtd_add")
    with col_add3:
        st.write("")
        if st.button("➕ Adicionar", use_container_width=True, type="primary"):
            ok, msg = agregar(codigo_sel, int(qtd_sel))
            if ok:
                st.toast(f"🛒 {msg} agregado", icon="✅")
                st.rerun()
            else:
                st.error(f"❌ {msg}")

st.markdown("---")

# =========================
# 🛒 CARRITO
# =========================
st.subheader("🛒 Carrinho")

if not st.session_state["carrinho"]:
    st.info("🛒 O carrinho está vazio. Escaneie ou adicione produtos.")
else:
    for idx, item in enumerate(st.session_state["carrinho"]):
        cols = st.columns([0.5, 3, 1, 1.2, 1.2, 1])
        with cols[0]:
            if st.button("❌", key=f"rm_{idx}"):
                st.session_state["carrinho"].pop(idx)
                st.rerun()
        with cols[1]:
            st.markdown(f"**{item['nome']}**")
            st.caption(f"Cód: {item['codigo']}")
        with cols[2]:
            if st.button("➖", key=f"menos_{idx}"):
                if item['qtd'] > 1:
                    st.session_state["carrinho"][idx]['qtd'] -= 1
                    st.session_state["carrinho"][idx]['subtotal'] = st.session_state["carrinho"][idx]['qtd'] * item['preco']
                else:
                    st.session_state["carrinho"].pop(idx)
                st.rerun()
        with cols[3]:
            st.markdown(f"**{item['qtd']}x**")
        with cols[4]:
            if st.button("➕", key=f"mais_{idx}"):
                ok, msg = agregar(item['codigo'], 1)
                if not ok:
                    st.toast(f"⚠️ {msg}", icon="⚠️")
                st.rerun()
        with cols[5]:
            st.markdown(f"**R$ {item['subtotal']:.2f}**")

    st.markdown("---")

    # =========================
    # CLIENTE + DESCUENTO
    # =========================
    st.subheader("👤 Cliente")
    opcoes_cliente = ["Consumidor Final"] + [f"{row['nome']} - CPF: {row['cpf']}" for _, row in df_clientes.iterrows()]
    cliente_sel = st.selectbox("Selecionar cliente", opcoes_cliente, key="cliente_sel")

    subtotal = sum(i['subtotal'] for i in st.session_state["carrinho"])
    desconto = st.number_input("💸 Desconto (R$)", min_value=0.0, value=0.0, step=0.50, key="desconto_input")
    total = max(subtotal - desconto, 0.0)

    col_tot = st.columns(3)
    col_tot[0].metric("Subtotal", f"R$ {subtotal:.2f}")
    col_tot[1].metric("Desconto", f"R$ {desconto:.2f}")
    col_tot[2].metric("🎯 TOTAL", f"R$ {total:.2f}")

    st.markdown("---")

    # =========================
    # 💳 PAGAMENTO
    # =========================
    st.subheader("💳 Pagamento")
    forma_pagamento = st.selectbox(
        "Forma de pagamento",
        ['Dinheiro', 'Pix', 'Cartão de Crédito', 'Cartão de Débito'],
        key="forma_pag"
    )

    pode_finalizar = True

    if forma_pagamento == 'Dinheiro':
        valor_recebido = st.number_input("💵 Valor recebido do cliente (R$)", min_value=0.0, value=float(total), step=1.0, key="valor_recebido")
        if valor_recebido >= total:
            st.success(f"💵 Troco: R$ {valor_recebido - total:.2f}")
        else:
            st.error(f"⚠️ Faltante: R$ {total - valor_recebido:.2f}")
            pode_finalizar = False

    if forma_pagamento == 'Pix':
        chave_pix = empresa['pix_chave'] if 'pix_chave' in empresa.keys() and empresa['pix_chave'] else None

        if not chave_pix:
            st.warning("⚠️ Configure a chave Pix da empresa para gerar o QR Code.")
            nova_chave = st.text_input("Chave Pix (CPF, CNPJ, e-mail ou aleatória)")
            if st.button("💾 Salvar chave Pix", use_container_width=True):
                conn.execute("UPDATE config_empresa SET pix_chave = ? WHERE id = 1", (nova_chave,))
                conn.commit()
                st.rerun()
            pode_finalizar = False
        else:
            st.markdown("**📱 Exiba o QR Code para o cliente escanear:**")
            payload = gerar_pix(chave_pix, total, empresa['nome_empresa'])
            img = qrcode.make(payload)
            c1, c2 = st.columns([1, 1])
            with c1:
                st.image(img, width=230)
            with c2:
                st.markdown(f"**Valor: R$ {total:.2f}**")
                st.caption("Pix copia e cola:")
                st.code(payload, language=None)
            pix_ok = st.checkbox("✅ Pagamento Pix confirmado pelo banco", key="pix_ok")
            if not pix_ok:
                pode_finalizar = False

    # =========================
    # FINALIZAR
    # =========================
    if st.button("✅ FINALIZAR VENDA", type="primary", use_container_width=True, disabled=not pode_finalizar):
        cupom = int(datetime.now().strftime('%Y%m%d%H%M%S'))
        usuario = st.session_state.get('user_name', 'Desconhecido')

        cliente_id = None
        if cliente_sel != "Consumidor Final":
            nome_cliente = cliente_sel.split(" - CPF:")[0]
            cli = df_clientes[df_clientes['nome'] == nome_cliente]
            if not cli.empty:
                cliente_id = int(cli.iloc[0]['id'])

        try:
            for item in st.session_state["carrinho"]:
                conn.execute(
                    "UPDATE produtos SET estoque_atual = estoque_atual - ? WHERE codigo_producto = ?",
                    (item['qtd'], item['codigo'])
                )
                conn.execute(
                    """INSERT INTO vendas 
                    (numero_cupom, codigo_producto, cantidad, total, forma_pagamento, usuario, cliente_id, desconto) 
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (cupom, item['codigo'], item['qtd'], item['subtotal'], forma_pagamento,
                     usuario, cliente_id, desconto / len(st.session_state["carrinho"]))
                )
            conn.commit()
            st.session_state['ultimo_cupom'] = cupom
            st.session_state["carrinho"] = []
            st.success(f"✅ Venda registrada! Cupom {cupom} — Total R$ {total:.2f}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao registrar venda: {e}")

    if st.button("🗑️ Limpar carrinho (cancelar venda)", use_container_width=True):
        st.session_state["carrinho"] = []
        st.rerun()

# =========================
# 📄 CUPOM PDF
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
            itens.append({'nome': p['nombre_producto'] if p else l['codigo_producto'],
                          'qtd': l['cantidad'], 'unit': p['precio_venta'] if p else 0, 'total': l['total']})
        total_cupom = sum(i['total'] for i in itens)

        with st.expander("👁️ Ver ticket (pré-visualização)", expanded=True):
            st.markdown(f"### {empresa['nome_empresa']}")
            st.caption(f"Cupom: {cupom} | Data: {linhas[0]['data_venda']} | Forma: {linhas[0]['forma_pagamento']}")
            for i in itens:
                st.markdown(f"**{i['qtd']}x** {i['nome']} — R$ {i['unit']:.2f} → R$ {i['total']:.2f}")
            st.markdown("---")
            st.markdown(f"### **TOTAL: R$ {total_cupom:.2f}**")

        try:
            pdf_bytes = bytes(gerar_pdf_cupom(cupom, linhas[0]['data_venda'], itens, total_cupom, linhas[0]['forma_pagamento']))
            st.download_button("📄 Baixar Cupom em PDF", data=pdf_bytes,
                               file_name=f"cupom_{cupom}.pdf", mime="application/pdf", use_container_width=True)
        except Exception as e:
            st.warning(f"⚠️ Não foi possível gerar o PDF: {e}")

conn.close()