from data_access import fetch_sample_companies

import csv
import io
from datetime import date

import streamlit as st


st.set_page_config(page_title="Censo Empresas", layout="wide")
st.title("Censo de Empresas - TFM")

with st.sidebar:
    st.header("Filtros")

    reference_date = st.date_input("Fecha de referencia", value=date.today())
    active_only = st.checkbox("Solo empresas activas", value=True)

    province = st.selectbox("Provincia", options=["", "Barcelona", "Madrid", "Valencia"])
    city = st.selectbox("Población", options=["", "Barcelona", "Madrid", "Valencia"])
    epigraph_codes = st.multiselect("Epígrafe", options=["011", "123", "456"])

    search_clicked = st.button("Buscar", type="primary")

st.caption(
    "Una empresa está activa si existe un epígrafe donde "
    "F_INI <= fecha_referencia y F_FIN > fecha_referencia."
)

if search_clicked:
    try:
        rows = fetch_sample_companies(
            reference_date=reference_date,
            limit=10
        )
    except Exception as ex:
        st.error(f"Database error: {ex}")
        st.stop()

    if not rows:
        st.warning("No results found.")
        st.stop()

    st.subheader("Resultados")
    st.dataframe(rows, use_container_width=True, hide_index=True)

    # CSV export without pandas
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

    csv_bytes = output.getvalue().encode("utf-8-sig")

    st.download_button(
        label="Descargar CSV",
        data=csv_bytes,
        file_name="censo_resultados.csv",
        mime="text/csv"
    )