from data_access import search_companies

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

    province = st.selectbox("Provincia", options=["", "Navarra", "Madrid", "Alava"])
    city = st.selectbox("localidad", options=["", "Pamplona", "Tudela", "Elizondo"])
    epigraph_codes = st.multiselect("Epigrafe", options=["011", "123", "456"])

    search_clicked = st.button("Buscar", type="primary")

st.caption(
    "Una empresa está activa si existe un epígrafe donde "
    "F_INI <= fecha_referencia y F_FIN > fecha_referencia."
)

if search_clicked:
    try:
        rows = search_companies(
            reference_date=reference_date,
            active_only=active_only,
            province=province if province else None,
            city=city if city else None,
            limit=200
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