from datetime import date

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Censo Empresas", layout="wide")

st.title("Censo de Empresas - TFM")

with st.sidebar:
    st.header("Filtros")

    reference_date = st.date_input("Fecha de referencia", value=date.today())
    active_only = st.checkbox("Solo empresas activas", value=True)

    province = st.selectbox("Provincia", options=["", "Barcelona", "Madrid", "Valencia"])
    city = st.selectbox("Población", options=["", "Barcelona", "Madrid", "Valencia"])

    epigraph = st.multiselect("Epígrafe", options=["011", "123", "456"])

    search_clicked = st.button("Buscar", type="primary")


st.caption(
    "Una empresa está activa si existe un epígrafe donde "
    "F_INI <= fecha_referencia y F_FIN > fecha_referencia."
)

if search_clicked:
    demo_data = [
        {
            "tax_id": "B00000000",
            "nombre": "EMPRESA DEMO SL",
            "provincia": province or "Barcelona",
            "poblacion": city or "Barcelona",
            "epigrafe": epigraph[0] if epigraph else "011",
            "fecha_referencia": reference_date,
            "activa": active_only,
        }
    ]

    df = pd.DataFrame(demo_data)

    st.subheader("Resultados")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "Descargar CSV",
        csv,
        file_name="censo_demo.csv",
        mime="text/csv",
    )
else:
    st.info("Configura los filtros y pulsa Buscar.")
