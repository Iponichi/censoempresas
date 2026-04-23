import csv
import io
from datetime import date
from typing import Any

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


def normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def filter_epigraph_options(
    epigraph_options: list[dict[str, str]],
    search_text: str,
) -> list[dict[str, str]]:
    normalized_search = normalize_text(search_text)

    if not normalized_search:
        return epigraph_options

    search_words = normalized_search.split()

    filtered_options: list[dict[str, str]] = []
    for option in epigraph_options:
        searchable_text = normalize_text(
            f'{option.get("codigo", "")} {option.get("nombre", "")} {option.get("label", "")}'
        )

        if all(word in searchable_text for word in search_words):
            filtered_options.append(option)

    return filtered_options


def ensure_epigraph_state() -> None:
    if "selected_epigraph_labels" not in st.session_state:
        st.session_state.selected_epigraph_labels = []

    if "epigraph_search_text" not in st.session_state:
        st.session_state.epigraph_search_text = ""



def add_epigraphs_to_selection(new_labels: list[str]) -> None:
    current_labels = st.session_state.selected_epigraph_labels.copy()

    for label in new_labels:
        if label not in current_labels:
            current_labels.append(label)

    st.session_state.selected_epigraph_labels = current_labels


def remove_epigraph_from_selection(label_to_remove: str) -> None:
    st.session_state.selected_epigraph_labels = [
        label
        for label in st.session_state.selected_epigraph_labels
        if label != label_to_remove
    ]


def clear_epigraph_selection() -> None:
    st.session_state.selected_epigraph_labels = []


def convert_rows_to_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def render_applied_filters_summary(
    temporal_mode: str,
    reference_date: date | None,
    date_from: date | None,
    date_to: date | None,
    province: str,
    cities: list[str],
    selected_epigraph_labels: list[str],
    view_mode: str,
) -> None:
    if temporal_mode == "date":
        temporal_text = "Activas en una fecha"
        date_text = reference_date.strftime("%d/%m/%Y") if reference_date else "-"
    else:
        temporal_text = "Con actividad en un rango"
        date_from_text = date_from.strftime("%d/%m/%Y") if date_from else "-"
        date_to_text = date_to.strftime("%d/%m/%Y") if date_to else "-"
        date_text = f"{date_from_text} - {date_to_text}"

    province_text = province if province else "Todas"

    st.markdown("### Filtros aplicados")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(f"**Modo temporal:** {temporal_text}")
        st.write(f"**Fecha / rango:** {date_text}")

    with col2:
        st.write(f"**Provincia:** {province_text}")
        st.write(f"**Modo de visualización:** {view_mode}")

    with col3:
        st.write(f"**Localidades seleccionadas:** {len(cities)}")
        st.write(f"**Epígrafes aplicados al filtro:** {len(selected_epigraph_labels)}")


def render_applied_filters_detail(
    province: str,
    cities: list[str],
    selected_epigraph_labels: list[str],
) -> None:
    province_text = province if province else "Todas"
    city_items = cities if cities else ["Todas"]
    epigraph_items = selected_epigraph_labels if selected_epigraph_labels else ["Todos"]

    with st.expander("Ver detalle de filtros", expanded=False):
        st.write(f"**Provincia:** {province_text}")

        st.write("**Localidades:**")
        for city in city_items:
            st.write(f"- {city}")

        st.write("**Epígrafes:**")
        for label in epigraph_items:
            st.write(f"- {label}")


today = date.today()
default_year = today.year - 1
year_start = date(default_year, 1, 1)
year_end = date(default_year, 12, 31)

with st.sidebar:
    st.header("Filtros")

    temporal_mode = st.radio(
        "Modo temporal",
        options=["Activas en una fecha", "Con actividad en un rango"],
    )

    if temporal_mode == "Activas en una fecha":
        reference_date = st.date_input("Fecha de referencia", value=today)
        date_from = None
        date_to = None
        temporal_mode_value = "date"
    else:
        date_from = st.date_input("Fecha inicio rango", value=year_start)
        date_to = st.date_input("Fecha fin rango", value=year_end)
        reference_date = None
        temporal_mode_value = "range"

        if date_from > date_to:
            st.error("La fecha inicio no puede ser mayor que la fecha fin.")
            st.stop()

    view_mode = st.radio(
        "Modo de visualización",
        options=["Resumen por empresa", "Detalle por epígrafe"],
    )

    try:
        provinces = [""] + cached_provinces()
    except Exception as ex:
        st.error(f"Error cargando provincias: {ex}")
        st.stop()

    province = st.selectbox("Provincia", options=provinces)

    try:
        if province:
            city_options = cached_cities(province)
        else:
            city_options = []
    except Exception as ex:
        st.error(f"Error cargando localidades: {ex}")
        st.stop()

    cities = st.multiselect("Localidades", options=city_options)

    try:
        epigraph_options = cached_epigraph_options()
    except Exception as ex:
        st.error(f"Error cargando epígrafes: {ex}")
        st.stop()

    ensure_epigraph_state()

    st.subheader("Epígrafes")

    st.text_input(
        "Buscar epígrafes por código o descripción",
        key="epigraph_search_text",
        placeholder="Ejemplo: 659, comercio, transporte mercancías",
    )

    filtered_epigraph_options = filter_epigraph_options(
        epigraph_options,
        st.session_state.epigraph_search_text,
    )

    filtered_epigraph_labels = [item["label"] for item in filtered_epigraph_options]

    available_epigraph_labels = [
        label
        for label in filtered_epigraph_labels
        if label not in st.session_state.selected_epigraph_labels
    ]

    epigraphs_to_add = st.multiselect(
        "Resultados encontrados",
        options=available_epigraph_labels,
    )

    col_add, col_clear_search = st.columns(2)

    with col_add:
        if st.button("Añadir"):
            add_epigraphs_to_selection(epigraphs_to_add)
            st.rerun()

    with col_clear_search:
        if st.button("Limpiar texto"):
            st.session_state.epigraph_search_text = ""
            st.rerun()

    st.caption(f"Coincidencias: {len(filtered_epigraph_labels)}")

    selected_epigraph_labels = st.multiselect(
        "Epígrafes seleccionados",
        options=st.session_state.selected_epigraph_labels,
        default=st.session_state.selected_epigraph_labels,
        key="selected_epigraph_labels_widget",
    )

    st.session_state.selected_epigraph_labels = selected_epigraph_labels

    col_remove, col_clear_all = st.columns(2)

    with col_remove:
        epigraph_to_remove = st.selectbox(
            "Quitar uno",
            options=[""] + st.session_state.selected_epigraph_labels,
            index=0,
            key="epigraph_to_remove",
        )
        if st.button("Quitar") and epigraph_to_remove:
            remove_epigraph_from_selection(epigraph_to_remove)
            st.rerun()

    with col_clear_all:
        if st.button("Vaciar selección"):
            clear_epigraph_selection()
            st.rerun()

    epigraph_codes = [
        item["codigo"]
        for item in epigraph_options
        if item["label"] in st.session_state.selected_epigraph_labels
    ]

    search_clicked = st.button("Buscar", type="primary")


st.caption(
    "Empresa activa: existe un registro en CENSO2 donde "
    "F_INICIO <= fecha y F_FIN > fecha."
)

rows: list[dict[str, Any]] = []

if search_clicked:
    try:
        if view_mode == "Resumen por empresa":
            rows = search_companies_summary(
                province=province,
                cities=cities,
                epigraph_codes=epigraph_codes,
                temporal_mode=temporal_mode_value,
                reference_date=reference_date,
                date_from=date_from,
                date_to=date_to,
            )
        else:
            rows = search_companies_detail(
                province=province,
                cities=cities,
                epigraph_codes=epigraph_codes,
                temporal_mode=temporal_mode_value,
                reference_date=reference_date,
                date_from=date_from,
                date_to=date_to,
            )
    except Exception as ex:
        st.error(f"Error en la búsqueda: {ex}")
        st.stop()

    st.subheader("Resultados")

    if not rows:
        st.info("No se han encontrado resultados con los filtros seleccionados.")
    else:
        render_applied_filters_summary(
            temporal_mode=temporal_mode_value,
            reference_date=reference_date,
            date_from=date_from,
            date_to=date_to,
            province=province,
            cities=cities,
            selected_epigraph_labels=st.session_state.selected_epigraph_labels,
            view_mode=view_mode,
        )

        render_applied_filters_detail(
            province=province,
            cities=cities,
            selected_epigraph_labels=st.session_state.selected_epigraph_labels,
        )

        st.divider()

        st.caption("Puedes ordenar los resultados pulsando en la cabecera de cada columna.")

        st.dataframe(rows, use_container_width=True, height=600)

        st.markdown(
            f"<div style='text-align: right; margin-top: 0.25rem; "
            f"font-size: 0.95rem; color: #9aa0a6;'>"
            f"Total registros: <strong>{len(rows)}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )

        csv_data = convert_rows_to_csv(rows)

        st.download_button(
            label="Descargar CSV",
            data=csv_data,
            file_name="censo_empresas.csv",
            mime="text/csv",
        )