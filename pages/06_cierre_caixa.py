import streamlit as st
import pandas as pd
from datetime import date, datetime
import plotly.graph_objects as go
from core.database import get_connection
# --- GUARDIA: solo administrador ---
if st.session_state.get('user_role') != 'admin':
    st.error("🚫 Solo el administrador puede ver esta página.")
    st.page_link("app.py", label="🏠 Volver al Inicio", use_container_width=True)
    st.stop()

st.header("🧾 Cuadre de Caixa — Cierre de Turno")

conn = get_connection()

# --- Datos de la empresa (para el reporte) ---
empresa = conn.execute("SELECT * FROM config_empresa WHERE id = 1").fetchone()

# --- Crear tabla de cierres si no existe ---
conn.execute("""
CREATE TABLE IF NOT EXISTS cierres_caja (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    usuario TEXT,
    hora_cierre TEXT,
    fondo_inicial REAL,
    num_vendas INTEGER,
    total_ventas REAL,
    total_dinheiro REAL,
    total_pix REAL,
    total_credito REAL,
    total_debito REAL,
    efectivo_esperado REAL,
    efectivo_contado REAL,
    diferencia REAL,
    observaciones TEXT
)
""")
conn.commit()

# --- Función de estilo para gráficos ---
def estilo(fig, height=350):
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

# --- Fecha del turno ---
fecha_sel = st.date_input("Fecha del turno", value=date.today())
fecha_str = fecha_sel.strftime("%Y-%m-%d")

# --- Ventas del día ---
df = pd.read_sql_query(
    "SELECT * FROM vendas WHERE date(data_venda) = ?",
    conn,
    params=[fecha_str]
)

total_ventas = float(df['total'].sum()) if not df.empty else 0.0
num_vendas = int(df['numero_cupom'].nunique()) if not df.empty else 0

def suma_pago(forma):
    if df.empty:
        return 0.0
    return float(df[df['forma_pagamento'] == forma]['total'].sum())

total_dinheiro = suma_pago('Dinheiro')
total_pix = suma_pago('Pix')
total_credito = suma_pago('Cartão de Crédito')
total_debito = suma_pago('Cartão de Débito')

st.markdown("---")
st.subheader(f"📅 Resumen del día {fecha_str}")

if df.empty:
    st.info("No hay ventas registradas en esta fecha.")
else:
    m1, m2, m3 = st.columns(3)
    m1.metric("Nº de ventas", num_vendas)
    m2.metric("Total vendido", f"R$ {total_ventas:.2f}")
    m3.metric("Ticket promedio", f"R$ {total_ventas / num_vendas:.2f}" if num_vendas else "R$ 0.00")

    st.markdown("**Ventas por forma de pago:**")
    
    # Gráfico de dona con Plotly
    formas_pago = {
        'Dinheiro': total_dinheiro,
        'Pix': total_pix,
        'Crédito': total_credito,
        'Débito': total_debito
    }
    formas_pago = {k: v for k, v in formas_pago.items() if v > 0}
    
    if formas_pago:
        fig_pago = go.Figure(go.Pie(
            labels=list(formas_pago.keys()),
            values=list(formas_pago.values()),
            hole=0.55,
            marker=dict(colors=["#636EFA", "#00CC96", "#FFA15A", "#AB63FA"]),
            textinfo="label+percent",
        ))
        st.plotly_chart(estilo(fig_pago, 300), use_container_width=True)
    else:
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("💵 Dinheiro", f"R$ {total_dinheiro:.2f}")
        p2.metric("📱 Pix", f"R$ {total_pix:.2f}")
        p3.metric("💳 Crédito", f"R$ {total_credito:.2f}")
        p4.metric("💳 Débito", f"R$ {total_debito:.2f}")

st.markdown("---")

# --- Verificar si ya hay cierre para esta fecha ---
cierre = conn.execute(
    "SELECT * FROM cierres_caja WHERE fecha = ?", (fecha_str,)
).fetchone()

if cierre:
    # ===== TURNO YA CERRADO =====
    st.subheader("🔒 Turno ya cerrado")
    st.success(f"Cierre registrado por {cierre['usuario']} a las {cierre['hora_cierre']}.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Efectivo esperado", f"R$ {cierre['efectivo_esperado']:.2f}")
    c2.metric("Efectivo contado", f"R$ {cierre['efectivo_contado']:.2f}")
    c3.metric("Diferencia", f"R$ {cierre['diferencia']:.2f}")
    c4.metric("Total vendido", f"R$ {cierre['total_ventas']:.2f}")

    if abs(cierre['diferencia']) < 0.01:
        st.success("✅ Cuadre correcto.")
    elif cierre['diferencia'] < 0:
        st.error(f"⚠️ Faltante de R$ {abs(cierre['diferencia']):.2f}.")
    else:
        st.warning(f"⚠️ Sobrante de R$ {cierre['diferencia']:.2f}.")

    if cierre['observaciones']:
        st.info(f"Observaciones: {cierre['observaciones']}")

    reporte = (
        "================================\n"
        "        CIERRE DE CAJA\n"
        f" {empresa['nome_empresa']}\n"
        f" Fecha: {fecha_str}\n"
        f" Operador: {cierre['usuario']}\n"
        f" Hora de cierre: {cierre['hora_cierre']}\n"
        "--------------------------------\n"
        f" Nº de ventas: {cierre['num_vendas']}\n"
        f" Total vendido: R$ {cierre['total_ventas']:.2f}\n"
        f" Dinheiro: R$ {cierre['total_dinheiro']:.2f}\n"
        f" Pix: R$ {cierre['total_pix']:.2f}\n"
        f" Cartão de Crédito: R$ {cierre['total_credito']:.2f}\n"
        f" Cartão de Débito: R$ {cierre['total_debito']:.2f}\n"
        "--------------------------------\n"
        f" Fondo inicial: R$ {cierre['fondo_inicial']:.2f}\n"
        f" Efectivo esperado: R$ {cierre['efectivo_esperado']:.2f}\n"
        f" Efectivo contado: R$ {cierre['efectivo_contado']:.2f}\n"
        f" DIFERENCIA: R$ {cierre['diferencia']:.2f}\n"
        f" Observaciones: {cierre['observaciones']}\n"
        "================================\n"
    )
    st.download_button(
        "🖨️ Baixar cuadre (TXT)",
        data=reporte,
        file_name=f"cuadre_{fecha_str}.txt",
        mime="text/plain",
        use_container_width=True
    )

else:
    # ===== HACER EL CIERRE =====
    st.subheader("🔐 Realizar cierre del turno")

    fondo = st.number_input("Fondo inicial de caja (monto de apertura)", min_value=0.0, value=0.0, step=10.0)
    contado = st.number_input("Efectivo contado en cajón", min_value=0.0, value=0.0, step=10.0)
    obs = st.text_area("Observaciones (opcional)")

    esperado = fondo + total_dinheiro
    diferencia = contado - esperado

    st.write(f"💵 Efectivo esperado en cajón: **R$ {esperado:.2f}**")

    if abs(diferencia) < 0.01:
        st.success("✅ Cuadre correcto.")
    elif diferencia < 0:
        st.error(f"⚠️ Faltante: R$ {abs(diferencia):.2f}")
    else:
        st.warning(f"⚠️ Sobrante: R$ {diferencia:.2f}")

    if st.button("🔒 Finalizar cierre de turno", type="primary", use_container_width=True):
        conn.execute(
            """INSERT INTO cierres_caja
            (fecha, usuario, hora_cierre, fondo_inicial, num_vendas, total_ventas,
             total_dinheiro, total_pix, total_credito, total_debito,
             efectivo_esperado, efectivo_contado, diferencia, observaciones)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (fecha_str, st.session_state.get('user_name', ''),
             datetime.now().strftime('%H:%M'), fondo, num_vendas, total_ventas,
             total_dinheiro, total_pix, total_credito, total_debito,
             esperado, contado, diferencia, obs)
        )
        conn.commit()
        st.success("✅ Cierre de turno registrado.")
        st.rerun()

# --- Historial de cierres con gráficos ---
st.markdown("---")
st.subheader("🗂️ Historial de cierres")

hist = pd.read_sql_query(
    """SELECT fecha, usuario, num_vendas, total_ventas,
              efectivo_esperado, efectivo_contado, diferencia
       FROM cierres_caja ORDER BY fecha DESC""",
    conn
)

if not hist.empty:
    # Gráfico de barras: ventas vs diferencia por día
    st.markdown("**📊 Ventas y cuadres de los últimos cierres**")
    
    fig_hist = go.Figure()
    
    # Barras de ventas totales
    fig_hist.add_trace(go.Bar(
        name='Total Vendido',
        x=hist['fecha'],
        y=hist['total_ventas'],
        marker_color='#636EFA',
        text=hist['total_ventas'],
        textposition='auto',
    ))
    
    # Línea de diferencia (faltante/sobrante)
    colores_dif = ['#00CC96' if abs(d) < 0.01 else '#EF553B' for d in hist['diferencia']]
    fig_hist.add_trace(go.Bar(
        name='Diferencia',
        x=hist['fecha'],
        y=hist['diferencia'],
        marker_color=colores_dif,
        text=hist['diferencia'],
        textposition='auto',
    ))
    
    fig_hist.update_layout(
        barmode='group',
        xaxis_title="Fecha",
        yaxis_title="R$",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(estilo(fig_hist, 400), use_container_width=True)
    
    # Tabla con el historial
    st.dataframe(
        hist.rename(columns={
            'fecha': 'Fecha',
            'usuario': 'Operador',
            'num_vendas': 'Nº Ventas',
            'total_ventas': 'Total Vendido',
            'efectivo_esperado': 'Esperado',
            'efectivo_contado': 'Contado',
            'diferencia': 'Diferencia'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Resumen del historial
    st.markdown("---")
    st.markdown("**📈 Resumen del historial**")
    
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total de cierres", len(hist))
    r2.metric("Ventas totales", f"R$ {hist['total_ventas'].sum():.2f}")
    r3.metric("Cuadres correctos", len(hist[abs(hist['diferencia']) < 0.01]))
    r4.metric("Cierres con diferencia", len(hist[abs(hist['diferencia']) >= 0.01]))
    
else:
    st.info("Aún no hay cierres registrados.")

conn.close()