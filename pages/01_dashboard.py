import streamlit as st
import pandas as pd
from datetime import date, timedelta
import plotly.graph_objects as go
from core.database import get_connection
# --- GUARDIA: solo administrador ---
if st.session_state.get('user_role') != 'admin':
    st.error("🚫 Solo el administrador puede ver esta página.")
    st.page_link("app.py", label="🏠 Volver al Inicio", use_container_width=True)
    st.stop()

st.title("📊 Dashboard General")
st.caption("Resumen en tiempo real de tu negocio.")

conn = get_connection()

vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
if not vendas.empty:
    vendas["data_venda"] = pd.to_datetime(vendas["data_venda"])

produtos = pd.read_sql_query("SELECT * FROM produtos", conn)
clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
cierres = pd.read_sql_query("SELECT * FROM cierres_caja", conn)

hoy = date.today()
ayer = hoy - timedelta(days=1)

COLORS = ["#636EFA", "#00CC96", "#FFA15A", "#AB63FA", "#EF553B"]


def estilo(fig, height=320):
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def total_dia(d):
    if vendas.empty:
        return 0.0
    return float(vendas[vendas["data_venda"].dt.date == d]["total"].sum())


total_hoy = total_dia(hoy)
delta = round(total_hoy - total_dia(ayer), 2)

v_hoy = vendas[vendas["data_venda"].dt.date == hoy] if not vendas.empty else vendas
cupons_hoy = int(v_hoy["numero_cupom"].nunique()) if not v_hoy.empty else 0
ticket = total_hoy / cupons_hoy if cupons_hoy else 0.0

# =========================
# RESUMEN DE HOY
# =========================
st.markdown("### 🏪 Resumen de hoy")
k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Vendido hoy", f"R$ {total_hoy:.2f}", delta=delta)
k2.metric("🧾 Cupones", cupons_hoy)
k3.metric("🎯 Ticket promedio", f"R$ {ticket:.2f}")
k4.metric("👥 Clientes", len(clientes))

st.divider()

# =========================
# SECCIÓN VENTAS
# =========================
st.markdown("### 💰 Ventas")

if vendas.empty:
    st.info("Aún no hay ventas. Cuando vendas en Caixa, aquí aparecen tus gráficos.")
else:
    c1, c2 = st.columns([2, 1])

    with c1:
        st.markdown("**📈 Ingresos — últimos 14 días**")
        inicio = hoy - timedelta(days=13)
        v14 = vendas[vendas["data_venda"].dt.date >= inicio]
        por_dia = v14.groupby(v14["data_venda"].dt.date)["total"].sum()
        idx = pd.date_range(inicio, hoy).map(lambda t: t.date())
        por_dia = por_dia.reindex(idx, fill_value=0.0)

        fig = go.Figure(go.Scatter(
            x=list(idx), y=por_dia.values,
            mode="lines+markers", fill="tozeroy",
            line=dict(color="#636EFA", width=3),
            fillcolor="rgba(99,110,250,0.25)",
            marker=dict(size=7),
        ))
        fig.update_yaxes(title_text="R$")
        st.plotly_chart(estilo(fig), use_container_width=True)

    with c2:
        st.markdown("**💳 Por forma de pago**")
        por_pago = vendas.groupby("forma_pagamento")["total"].sum().sort_values(ascending=False)
        fig2 = go.Figure(go.Pie(
            labels=por_pago.index, values=por_pago.values,
            hole=0.55, marker=dict(colors=COLORS),
            textinfo="label+percent",
        ))
        st.plotly_chart(estilo(fig2), use_container_width=True)

    st.markdown("**🏆 Top 5 productos más vendidos**")
    top = (
        vendas.groupby("codigo_producto")["cantidad"].sum()
        .sort_values(ascending=False).head(5)
    )
    nombres = produtos.set_index("codigo_producto")["nombre_producto"] if not produtos.empty else pd.Series(dtype=str)
    top_df = top.reset_index()
    top_df["nombre_producto"] = top_df["codigo_producto"].map(nombres).fillna(top_df["codigo_producto"])

    fig3 = go.Figure(go.Bar(
        x=top_df["cantidad"], y=top_df["nombre_producto"], orientation="h",
        marker=dict(color=COLORS[:len(top_df)]),
        text=top_df["cantidad"], textposition="auto",
    ))
    fig3.update_xaxes(title_text="Unidades vendidas")
    st.plotly_chart(estilo(fig3), use_container_width=True)

st.divider()

# =========================
# SECCIÓN STOCK
# =========================
st.markdown("### 📦 Stock")

if produtos.empty:
    st.info("No hay productos cadastrados.")
else:
    bajo = produtos[produtos["estoque_atual"] <= produtos["stock_minimo"]]
    s1, s2 = st.columns(2)
    s1.metric("🚨 Productos con stock bajo", len(bajo))
    s2.metric("🏬 Productos activos", len(produtos))

    st.markdown("**📉 Los 10 productos con menos stock**")
    p10 = produtos.sort_values("estoque_atual").head(10)
    colores = [
        "#EF553B" if e <= m else "#00CC96"
        for e, m in zip(p10["estoque_atual"], p10["stock_minimo"])
    ]
    fig4 = go.Figure(go.Bar(
        x=p10["nombre_producto"], y=p10["estoque_atual"],
        marker=dict(color=colores),
        text=p10["estoque_atual"], textposition="auto",
    ))
    st.plotly_chart(estilo(fig4), use_container_width=True)

    if not bajo.empty:
        st.warning("Productos que necesitas reponer:")
        st.dataframe(
            bajo[["codigo_producto", "nombre_producto", "estoque_atual", "stock_minimo"]],
            hide_index=True, use_container_width=True
        )

st.divider()

# =========================
# SECCIÓN CIERRES DE CAJA
# =========================
st.markdown("### 🔐 Cierres de caja")

if cierres.empty:
    st.info("Todavía no hay cierres de turno registrados.")
else:
    ultimo = cierres.iloc[-1]
    g1, g2, g3 = st.columns(3)
    g1.metric("📅 Último cierre", ultimo["fecha"])
    g2.metric("💵 Total vendido", f"R$ {ultimo['total_ventas']:.2f}")
    g3.metric("⚖️ Diferencia", f"R$ {ultimo['diferencia']:.2f}")

    st.markdown("**🗂️ Total vendido por cierre**")
    colores_c = ["#00CC96" if abs(d) < 0.01 else "#EF553B" for d in cierres["diferencia"]]
    fig5 = go.Figure(go.Bar(
        x=cierres["fecha"], y=cierres["total_ventas"],
        marker=dict(color=colores_c),
        text=cierres["total_ventas"], textposition="auto",
    ))
    st.plotly_chart(estilo(fig5), use_container_width=True)

conn.close()