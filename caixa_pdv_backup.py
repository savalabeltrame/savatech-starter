import streamlit as st

st.title("🧾 Caixa PDV")
st.write("Módulo de Punto de Venta.")

# Botón para volver al inicio
if st.button("🏠 Volver al Inicio"):
    st.switch_page("app.py")

st.markdown("---")

# Inicializar carrito en session_state
if "carrito" not in st.session_state:
    st.session_state["carrito"] = []

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Agregar Producto")
    with st.form("form_venta"):
        producto = st.text_input("Producto")
        cantidad = st.number_input("Cantidad", min_value=1, value=1)
        precio = st.number_input("Precio", min_value=0.0, value=0.0, format="%.2f")
        
        enviado = st.form_submit_button("Agregar a la venta", use_container_width=True)
        
        if enviado:
            if not producto.strip():
                st.warning("Escribe el nombre del producto.")
            elif precio <= 0:
                st.warning("El precio debe ser mayor a cero.")
            else:
                total_item = cantidad * precio
                st.session_state["carrito"].append({
                    "Producto": producto,
                    "Cantidad": cantidad,
                    "Precio": precio,
                    "Total": total_item
                })
                st.success(f"Agregado: {producto}")

with col2:
    st.subheader("Resumen de Venta")
    if st.session_state["carrito"]:
        st.dataframe(st.session_state["carrito"], use_container_width=True, hide_index=True)
        total_general = sum(item["Total"] for item in st.session_state["carrito"])
        st.metric(label="Total a cobrar", value=f"${total_general:,.2f}")
        
        if st.button("🗑️ Limpiar Venta", use_container_width=True):
            st.session_state["carrito"] = []
            st.rerun()
    else:
        st.info("El carrito está vacío.")