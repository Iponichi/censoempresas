import streamlit as st
st.set_page_config(page_title="Censo Empresas", layout="wide")


from data_access import get_cities, get_epigraph_codes, get_provinces, search_companies

import csv, io
from datetime import date

st.title("Censo de Empresas - TFM")

with st.sidebar:
    st.header("Filtros")

    reference_date = st.date_input("Fecha de referencia", value=date.today())
    active_only = st.checkbox("Solo empresas activas", value=True)

    @st.cache_data(ttl=1800)
    def _cached_provinces() -> list[str]:
        return get_provinces()

    @st.cache_data(ttl=1800)
    def _cached_epigraphs() -> list[str]:
        return get_epigraph_codes()

    provinces = [""] + _cached_provinces()
    province = st.selectbox("Provincia", options=provinces)

    # Cities depend on selected province (avoid huge dropdown)
    @st.cache_data(ttl=1800)
    def _cached_cities(prov: str) -> list[str]:
        return get_cities(prov)

    if province:
        cities = [""] + _cached_cities(province)
    else:
        cities = [""]

    city = st.selectbox("Localidad", options=cities)

    epigraph_codes = st.multiselect("Epígrafe", options=_cached_epigraphs())

    search_clicked = st.button("Buscar", type="primary")

st.caption(
    "Una empresa está activa si existe un epígrafe donde "
    "F_INICIO <= fecha_referencia y F_FIN > fecha_referencia."
)

if search_clicked:
    try:
        rows = search_companies(
            reference_date=reference_date,
            active_only=active_only,
            province=province if province else None,
            city=city if city else None,
            epigraph_codes=epigraph_codes if epigraph_codes else None,
            limit=200,
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