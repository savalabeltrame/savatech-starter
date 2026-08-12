import streamlit as st
import pandas as pd
from datetime import date, timedelta
from core.database import get_connection

st.header("📊 Relatórios")

conn = get_connection()

# =========================
# PERÍODO
# =========================
periodo = st.selectbox(
    "Período",
    ["Hoy", "Últimos 7 días", "Este mes", "Todo el historial"]
)

df = pd.read_sql_query("SELECT * FROM vendas", conn)

if not df.empty:
    df['data_venda'] = pd.to_datetime(df['data_venda'])
    hoy = date.today()

    if periodo == "Hoy":
        df = df[df['data_venda'].dt.date == hoy]
    elif periodo == "Últimos 7 días":
        inicio = pd.Timestamp(hoy - timedelta(days=6))
        df = df[df['data_venda'] >= inicio]
    elif periodo == "Este mes":
        df = df[
            (df['data_venda'].dt.year == hoy.year) &
            (df['data_venda'].dt.month == hoy.month)
        ]

st.markdown("---")

# =========================
# VENTAS
# =========================
st.subheader(f"💰 Ventas — {periodo}")

if df.empty:
    st.info("No hay ventas en el período seleccionado.")
else:
    total_ventas = float(df['total'].sum())
    num_cupons = int(df['numero_cupom'].nunique())
    unidades = int(df['cantidad'].sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total vendido", f"R$ {total_ventas:.2f}")
    k2.metric("Nº de cupones", num_cupons)
    k3.metric("Ticket promedio", f"R$ {total_ventas / num_cupons:.2f}" if num_cupons else "R$ 0.00")
    k4.metric("Unidades vendidas", unidades)

    st.markdown("**Ventas por día:**")
    por_dia = df.groupby(df['data_venda'].dt.date)['total'].sum()
    st.bar_chart(por_dia)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Por forma de pago:**")
        por_pago = df.groupby('forma_pagamento')['total'].sum().reset_index()
        por_pago.columns = ['Forma de pago', 'Total']
        st.dataframe(por_pago, hide_index=True, use_container_width=True)

    with c2:
        st.markdown("**Por operador:**")
        por_op = df.groupby(df['usuario'].fillna('Sin registro'))['total'].sum().reset_index()
        por_op.columns = ['Operador', 'Total']
        st.dataframe(por_op, hide_index=True, use_container_width=True)

    st.markdown("**🏆 Productos más vendidos:**")
    top = df.groupby('codigo_producto').agg(
        unidades=('cantidad', 'sum'),
        total=('total', 'sum')
    ).reset_index().sort_values('total', ascending=False).head(10)

    nombres = pd.read_sql_query("SELECT codigo_producto, nombre_producto FROM produtos", conn)
    top = top.merge(nombres, on='codigo_producto', how='left')
    top = top[['codigo_producto', 'nombre_producto', 'unidades', 'total']]
    st.dataframe(top, hide_index=True, use_container_width=True)

st.markdown("---")

# =========================
# PRODUCTOS POR VENCER
# =========================
st.subheader("⏰ Productos por vencer")

dias = st.selectbox("Mostrar productos que vencen en (días):", [7, 15, 30], index=1)

prods = pd.read_sql_query(
    "SELECT codigo_producto, nombre_producto, estoque_atual, validade FROM produtos WHERE validade IS NOT NULL AND validade != ''",
    conn
)

if not prods.empty:
    prods['validade_dt'] = pd.to_datetime(prods['validade'], errors='coerce')
    prods = prods.dropna(subset=['validade_dt'])
    prods['dias_restantes'] = (prods['validade_dt'].dt.date - date.today()).dt.days

    por_vencer = prods[prods['dias_restantes'] <= dias].sort_values('dias_restantes')

    if not por_vencer.empty:
        vencidos = por_vencer[por_vencer['dias_restantes'] < 0]
        if not vencidos.empty:
            st.error(f"🚨 Hay {len(vencidos)} producto(s) VENCIDO(S).")

        mostrar = por_vencer[['codigo_producto', 'nombre_producto', 'estoque_atual', 'validade', 'dias_restantes']]
        st.dataframe(mostrar, hide_index=True, use_container_width=True)
    else:
        st.success(f"Ningún producto vence en los próximos {dias} días.")
else:
    st.info("Ningún producto tiene fecha de vencimiento registrada todavía.")

st.markdown("---")

# =========================
# STOCK BAJO
# =========================
st.subheader("📦 Stock bajo")

bajo = pd.read_sql_query(
    """SELECT codigo_producto, nombre_producto, estoque_atual, stock_minimo
       FROM produtos WHERE estoque_atual <= stock_minimo
       ORDER BY estoque_atual""",
    conn
)

if not bajo.empty:
    st.warning(f"{len(bajo)} producto(s) en o por debajo del stock mínimo.")
    st.dataframe(bajo, hide_index=True, use_container_width=True)
else:
    st.success("Todo el stock está por encima del mínimo.")

conn.close()