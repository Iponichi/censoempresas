import csv
import io
from datetime import date

import streamlit as st

from data_access import (
    get_cities,
    get_epigraph_options,
    get_provinces,
    search_companies_detail,
    search_companies_summary,
)

st.set_page_config(page_title="Censo Empresas", layout="wide")

st.title("Censo de Empresas - TFM")


@st.cache_data(ttl=1800)
def cached_provinces() -> list[str]:
    return get_provinces()


@st.cache_data(ttl=1800)
def cached_cities(province: str) -> list[str]:
    return get_cities(province)


@st.cache_data(ttl=1800)
def cached_epigraph_options() -> list[dict[str, str]]:
    return get_epigraph_options()


with st.sidebar:
    st.header("Filtros")

    temporal_mode = st.radio(
        "Modo temporal",
        options=["Activas en una fecha", "Con actividad en un rango"],
    )

    if temporal_mode == "Activas en una fecha":
        reference_date = st.date_input("Fecha de referencia", value=date.today())
        date_from = None
        date_to = None
        temporal_mode_value = "date"
    else:
        date_from = st.date_input("Fecha inicio rango", value=date.today())
        date_to = st.date_input("Fecha fin rango", value=date.today())
        reference_date = None
        temporal_mode_value = "range"

    view_mode = st.radio(
        "Modo de visualización",
        options=["Resumen por empresa", "Detalle por epígrafe"],
    )

    provinces = [""] + cached_provinces()
    province = st.selectbox("Provincia", options=provinces)

    if province:
        city_options = cached_cities(province)
    else:
        city_options = []

    cities = st.multiselect("Localidades", options=city_options)

    epigraph_options = cached_epigraph_options()
    epigraph_labels = [item["label"] for item in epigraph_options]

    selected_epigraph_labels = st.multiselect(
        "Epígrafes",
        options=epigraph_labels,
    )

    epigraph_codes = [
        item["codigo"]
        for item in epigraph_options
        if item["label"] in selected_epigraph_labels
    ]

    search_clicked = st.button("Buscar", type="primary")

st.caption(
    "Empresa activa: existe un registro en CENSO2 donde "
    "F_INICIO <= fecha y F_FIN > fecha."
)

if search_clicked:
    try:
        if view_mode == "Resumen por empresa":
            rows = search_companies_summary(
                temporal_mode=temporal_mode_value,
                reference_date=reference_date,
                date_from=date_from,
                date_to=date_to,
                province=province if province else None,
                cities=cities if cities else None,
                epigraph_codes=epigraph_codes if epigraph_codes else None,
                limit=500,
            )
        else:
            rows = search_companies_detail(
                temporal_mode=temporal_mode_value,
                reference_date=reference_date,
                date_from=date_from,
                date_to=date_to,
                province=province if province else None,
                cities=cities if cities else None,
                epigraph_codes=epigraph_codes if epigraph_codes else None,
                limit=1000,
            )

    except Exception as ex:
        st.error(f"Database error: {ex}")
        st.stop()

    if not rows:
        st.warning("No se han encontrado resultados.")
        st.stop()

    st.subheader("Resultados")
    st.dataframe(rows, use_container_width=True, hide_index=True)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

    csv_bytes = output.getvalue().encode("utf-8-sig")

    st.download_button(
        label="Descargar CSV",
        data=csv_bytes,
        file_name="censo_resultados.csv",
        mime="text/csv",
    )