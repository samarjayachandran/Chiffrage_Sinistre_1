import streamlit as st
import pandas as pd
import unicodedata
from pathlib import Path

# =========================================================
# CONSTANTS
# =========================================================
REPL_MAP = {
    r"\'ea": "ê",
    r"\'e9": "é",
    r"\'e8": "è",
    r"\'b": "",
    r"\'ef": "ï",
    r"\'e7": "ç",
    r"\'e2": "â",
    r"\'9c": "œ",
    r"\'e0": "à",
    r"\'ee": "î",
}

SELECTOR_MAP = {
    "Menuiseries extérieures": "Extérieure",
    "Menuiserie intérieure": "Intérieure",
    "Revêtements de sol": "Sol",
    "Revêtements murs et plafonds": "Murs et plafonds",
    "Charpente - Ossature": "Charpente - Ossature",
    "Maçonnerie - Gros œuvre": "Maçonnerie - Gros œuvre",
    "Plomberie": "Plomberie",
    "Electricité": "Electricité",
    "Chauffage - Ventilation - Climatisation": "Chauffage - Ventilation - Climatisation",
}

CATEGORY_MERGE_MAP = {
    "Revêtements de sol": "Revêtements intérieurs",
    "Revêtements murs et plafonds": "Revêtements intérieurs",
    "Menuiseries extérieures": "Menuiseries",
    "Menuiserie intérieure": "Menuiseries",
    "Charpente - Ossature": "Structure",
    "Maçonnerie - Gros œuvre": "Structure",
    "Plomberie": "Réseaux techniques",
    "Electricité": "Réseaux techniques",
    "Chauffage - Ventilation - Climatisation": "Réseaux techniques",
}

LOW_CARBON_KEYWORDS = [
    "bas carbone", "chaume", "végétalisée", "biosourcé", "biosourcée",
    "laine", "chanvre", "ouate de cellulose",
]

NONE_SENTINEL = "— Aucune sélection —"

# Navy / white palette
NAVY = "#0a1f3d"
NAVY_LIGHT = "#122b54"
NAVY_MID = "#1a3a6b"
WHITE = "#ffffff"
OFF_WHITE = "#f0f2f6"
ACCENT_BLUE = "#4a90d9"
ACCENT_GREEN = "#5cb85c"


# =========================================================
# THEME: inject navy-blue / white CSS
# =========================================================
def inject_theme():
    st.markdown(
        f"""
        <style>
        /* ---- main background ---- */
        .stApp {{
            background-color: {NAVY};
            color: {WHITE};
        }}

        /* ---- sidebar ---- */
        section[data-testid="stSidebar"] {{
            background-color: {NAVY_LIGHT};
        }}

        /* ---- header / toolbar ---- */
        header[data-testid="stHeader"] {{
            background-color: {NAVY} !important;
        }}

        /* ---- tab labels ---- */
        button[data-baseweb="tab"] {{
            color: {WHITE} !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            border-bottom-color: {ACCENT_BLUE} !important;
            color: {ACCENT_BLUE} !important;
        }}

        /* ---- widget labels ---- */
        .stSelectbox label, .stRadio label, .stCheckbox label,
        .stNumberInput label, .stTextInput label,
        .stMultiSelect label, .stSlider label {{
            color: {WHITE} !important;
        }}

        /* ---- metric cards ---- */
        [data-testid="stMetricValue"] {{
            color: {WHITE} !important;
        }}
        [data-testid="stMetricLabel"] {{
            color: #b0bec5 !important;
        }}

        /* ---- markdown / text ---- */
        .stMarkdown, .stMarkdown p, .stMarkdown li,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
        .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {{
            color: {WHITE} !important;
        }}

        /* ---- info / warning / success boxes ---- */
        div[data-testid="stNotification"] {{
            background-color: {NAVY_LIGHT} !important;
            color: {WHITE} !important;
        }}

        /* ---- dataframe container ---- */
        .stDataFrame {{
            border: 1px solid {NAVY_MID};
            border-radius: 6px;
        }}

        /* ---- radio button text ---- */
        .stRadio div[role="radiogroup"] label span {{
            color: {WHITE} !important;
        }}

        /* ---- dividers ---- */
        hr {{
            border-color: {NAVY_MID} !important;
        }}

        /* ---- buttons ---- */
        .stButton > button {{
            border: 1px solid {ACCENT_BLUE};
            color: {WHITE};
        }}
        .stButton > button:hover {{
            background-color: {NAVY_MID};
            border-color: {WHITE};
        }}
        .stButton > button[kind="primary"] {{
            background-color: {ACCENT_BLUE};
            color: {WHITE};
        }}

        /* ---- expander ---- */
        details summary span {{
            color: {WHITE} !important;
        }}
        details {{
            border-color: {NAVY_MID} !important;
        }}

        /* ---- caption ---- */
        .stCaption, small {{
            color: #90a4ae !important;
        }}

        /* ---- tab content container ---- */
        .stTabs [data-testid="stTabContent"] {{
            background-color: {NAVY};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# LOGO
# =========================================================
def render_logo():
    """Display the REVERT logo if the file exists, otherwise fall back to text."""
    logo_path = Path(__file__).parent / "revert_logo.png"
    if logo_path.exists():
        col_logo, col_title = st.columns([1, 4])
        with col_logo:
            st.image(str(logo_path), width=160)
        with col_title:
            st.markdown(
                f'<h1 style="margin-top:18px;color:{WHITE};">Chiffrage sinistre — Comparateur carbone</h1>',
                unsafe_allow_html=True,
            )
    else:
        st.title("Chiffrage sinistre — Comparateur carbone")


# =========================================================
# UTILITY FUNCTIONS
# =========================================================
def normalize_text(value: str) -> str:
    if pd.isna(value):
        return ""
    text = str(value).lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text


NORMALIZED_LOW_CARBON_KEYWORDS = [normalize_text(x) for x in LOW_CARBON_KEYWORDS]


def is_low_carbon_option(row: pd.Series) -> bool:
    text = f"{row.get('Sous_categorie', '')} {row.get('Produit_process', '')}"
    text_norm = normalize_text(text)
    keyword_match = any(kw in text_norm for kw in NORMALIZED_LOW_CARBON_KEYWORDS)
    emissions = row.get("Emissions_CO2")
    emissions_rule = pd.notna(emissions) and float(emissions) <= 0
    return keyword_match or emissions_rule


@st.cache_data
def load_df(html_path: str) -> pd.DataFrame:
    tables = pd.read_html(html_path)
    if not tables:
        raise ValueError("No tables found in carbon_data.html")
    df = tables[0].copy()
    df.columns = [
        "Categorie",
        "Sous_categorie",
        "Produit_process",
        "Unite",
        "Type_prestation",
        "Prestation",
        "Emissions_CO2",
    ]
    df = df.iloc[1:].reset_index(drop=True)
    for col in df.columns:
        if df[col].dtype == object:
            s = df[col].astype(str)
            for pat, repl in REPL_MAP.items():
                s = s.str.replace(pat, repl, regex=False)
            df[col] = s
    df["Emissions_CO2"] = pd.to_numeric(df["Emissions_CO2"], errors="coerce")
    df["Categorie_old"] = df["Categorie"]
    df["Selector"] = df["Categorie"].map(SELECTOR_MAP)
    df["Categorie"] = df["Categorie"].replace(CATEGORY_MERGE_MAP)
    return df


def build_candidates(filtered_df: pd.DataFrame) -> pd.DataFrame:
    candidates = (
        filtered_df[
            [
                "Categorie", "Categorie_old", "Selector",
                "Sous_categorie", "Produit_process", "Unite",
                "Type_prestation", "Prestation", "Emissions_CO2",
            ]
        ]
        .dropna(subset=["Produit_process", "Emissions_CO2"])
        .drop_duplicates()
        .copy()
    )
    if candidates.empty:
        return candidates
    candidates["Option_famille"] = candidates.apply(
        lambda row: "Option bas carbone" if is_low_carbon_option(row) else "Standard",
        axis=1,
    )
    candidates = candidates.sort_values(
        ["Option_famille", "Emissions_CO2", "Produit_process"],
        ascending=[True, True, True],
    ).reset_index(drop=True)
    return candidates


def get_reduction_label(pct: float) -> str:
    if pct > 40:
        return "Réduction basse carbone"
    elif pct >= 20:
        return "Réduction performante"
    else:
        return "Réduction standard"


def get_reduction_color(pct: float) -> str:
    if pct > 40:
        return "#2e7d32"
    elif pct >= 20:
        return "#f9a825"
    else:
        return "#e65100"


# =========================================================
# CALLBACKS for mutual-exclusivity between the two columns
# =========================================================
def _on_std_change(key_prefix: str):
    lc_key = f"lc_radio_{key_prefix}"
    if st.session_state.get(f"std_radio_{key_prefix}") != NONE_SENTINEL:
        st.session_state[lc_key] = NONE_SENTINEL


def _on_lc_change(key_prefix: str):
    std_key = f"std_radio_{key_prefix}"
    if st.session_state.get(f"lc_radio_{key_prefix}") != NONE_SENTINEL:
        st.session_state[std_key] = NONE_SENTINEL


# =========================================================
# RENDER: KEYWORD SEARCH
# =========================================================
def render_search(df: pd.DataFrame):
    """Full-text keyword search across all columns of the dataset."""
    st.subheader("Recherche par mot-clé")
    query = st.text_input(
        "Entrez un ou plusieurs mots-clés (séparés par des espaces)",
        key="search_query",
        placeholder="ex. laine chanvre plomberie",
    )

    if not query or not query.strip():
        st.info("Saisissez un mot-clé pour lancer la recherche.")
        return

    keywords = query.strip().lower().split()

    # Search across all string columns
    str_cols = [c for c in df.columns if df[c].dtype == object]
    mask = pd.Series(False, index=df.index)
    for kw in keywords:
        kw_norm = normalize_text(kw)
        col_mask = pd.Series(False, index=df.index)
        for col in str_cols:
            col_mask |= df[col].apply(lambda v: kw_norm in normalize_text(v))
        mask |= col_mask

    results = df[mask].copy()

    if results.empty:
        st.warning(f"Aucun résultat pour « {query} ».")
        return

    st.markdown(f"**{len(results)}** résultat(s) pour « {query} »")

    display = results[
        ["Categorie_old", "Sous_categorie", "Produit_process", "Unite",
         "Type_prestation", "Prestation", "Emissions_CO2"]
    ].copy()
    display = display.rename(columns={
        "Categorie_old": "Catégorie",
        "Sous_categorie": "Sous-catégorie",
        "Produit_process": "Produit / process",
        "Unite": "Unité",
        "Type_prestation": "Type de prestation",
        "Emissions_CO2": "Émissions CO₂ (kg / unité)",
    })
    st.dataframe(display, use_container_width=True, hide_index=True)


# =========================================================
# RENDER: FULL DATASET TABLE
# =========================================================
def render_full_dataset(df: pd.DataFrame):
    """Expandable section showing the entire dataset."""
    with st.expander("📂 Afficher l'ensemble des données", expanded=False):
        st.markdown(f"**{len(df)}** lignes au total")
        display = df[
            ["Categorie_old", "Sous_categorie", "Produit_process", "Unite",
             "Type_prestation", "Prestation", "Emissions_CO2"]
        ].copy()
        display = display.rename(columns={
            "Categorie_old": "Catégorie",
            "Sous_categorie": "Sous-catégorie",
            "Produit_process": "Produit / process",
            "Unite": "Unité",
            "Type_prestation": "Type de prestation",
            "Emissions_CO2": "Émissions CO₂ (kg / unité)",
        })
        st.dataframe(display, use_container_width=True, hide_index=True, height=600)


# =========================================================
# RENDER: CATEGORY-ONLY MODE
# =========================================================
def render_category_browse(df: pd.DataFrame, key_prefix: str):
    categories = sorted(df["Categorie"].dropna().unique().tolist())
    cat = st.selectbox("Catégorie", categories, key=f"{key_prefix}_cat_browse")

    filtered = df[df["Categorie"] == cat]
    products = (
        filtered[["Categorie_old", "Sous_categorie", "Produit_process", "Unite", "Emissions_CO2"]]
        .dropna(subset=["Produit_process", "Emissions_CO2"])
        .drop_duplicates()
        .sort_values(["Sous_categorie", "Emissions_CO2"])
        .reset_index(drop=True)
    )
    products = products.rename(columns={
        "Categorie_old": "Catégorie d'origine",
        "Sous_categorie": "Sous-catégorie",
        "Produit_process": "Produit / process",
        "Unite": "Unité",
        "Emissions_CO2": "Émissions CO₂ (kg / unité)",
    })

    st.write(f"**{len(products)}** produits trouvés dans la catégorie **{cat}**")
    st.dataframe(products, use_container_width=True, hide_index=True)


# =========================================================
# RENDER: TWO-COLUMN PRODUCT SELECTION (radio in each column)
# =========================================================
def render_product_selection(candidates: pd.DataFrame, key_prefix: str):
    if candidates.empty:
        st.warning("Aucun produit correspondant à cette sélection.")
        return None

    std_df = candidates[candidates["Option_famille"] == "Standard"].reset_index(drop=True)
    lc_df = candidates[candidates["Option_famille"] == "Option bas carbone"].reset_index(drop=True)

    def _labels(sub_df):
        labels = [NONE_SENTINEL]
        for _, row in sub_df.iterrows():
            labels.append(
                f"{row['Produit_process']}  —  "
                f"{float(row['Emissions_CO2']):.2f} kg CO₂ / {row['Unite']}"
            )
        return labels

    std_labels = _labels(std_df)
    lc_labels = _labels(lc_df)

    st.markdown("**Produits disponibles** — sélectionnez directement dans l'une des deux colonnes")

    col_std, col_lc = st.columns(2)

    with col_std:
        st.markdown(
            f'<div style="background:{NAVY_MID};padding:8px 12px;border-radius:6px;'
            f'margin-bottom:4px;color:{WHITE};"><b>Standard</b></div>',
            unsafe_allow_html=True,
        )
        if std_df.empty:
            st.caption("Aucune option standard disponible.")
            std_choice = NONE_SENTINEL
        else:
            std_choice = st.radio(
                "Standard",
                std_labels,
                key=f"std_radio_{key_prefix}",
                on_change=_on_std_change,
                args=(key_prefix,),
                label_visibility="collapsed",
            )

    with col_lc:
        st.markdown(
            f'<div style="background:#1b5e20;padding:8px 12px;border-radius:6px;'
            f'margin-bottom:4px;color:{WHITE};"><b>Option bas carbone</b></div>',
            unsafe_allow_html=True,
        )
        if lc_df.empty:
            st.caption("Aucune option bas carbone disponible.")
            lc_choice = NONE_SENTINEL
        else:
            lc_choice = st.radio(
                "Bas carbone",
                lc_labels,
                key=f"lc_radio_{key_prefix}",
                on_change=_on_lc_change,
                args=(key_prefix,),
                label_visibility="collapsed",
            )

    if std_choice != NONE_SENTINEL:
        idx = std_labels.index(std_choice) - 1
        return std_df.iloc[idx]
    elif lc_choice != NONE_SENTINEL:
        idx = lc_labels.index(lc_choice) - 1
        return lc_df.iloc[idx]
    else:
        st.info("Veuillez sélectionner un produit dans l'une des deux colonnes.")
        return None


# =========================================================
# RENDER: SHARED SELECTION PANEL (single workflow, two add buttons)
# =========================================================
def render_selection_panel(df: pd.DataFrame):
    KP = "shared"

    for cfg in ("config_1", "config_2"):
        bk = f"basket_{cfg}"
        if bk not in st.session_state:
            st.session_state[bk] = []

    mode = st.radio(
        "Mode de sélection",
        ["Chiffrage détaillé", "Recherche par catégorie"],
        key=f"mode_{KP}",
        horizontal=True,
    )

    if mode == "Recherche par catégorie":
        render_category_browse(df, KP)
        return

    categories = sorted(df["Categorie"].dropna().unique().tolist())
    cat = st.selectbox("Catégorie", categories, key=f"cat_{KP}")

    d1 = df[df["Categorie"] == cat]
    selector_options = sorted(
        [x for x in d1["Selector"].dropna().unique().tolist() if x != ""]
    )

    sel_value = None
    if selector_options:
        sel_value = st.selectbox("Sélecteur", selector_options, key=f"sel_{KP}")
        d2 = d1[d1["Selector"] == sel_value]
    else:
        d2 = d1

    sous_cats = sorted(d2["Sous_categorie"].dropna().unique().tolist())
    if not sous_cats:
        st.info("Aucune sous-catégorie disponible pour cette sélection.")
        return
    sous_cat = st.selectbox("Sous-catégorie", sous_cats, key=f"scat_{KP}")

    d3 = d2[d2["Sous_categorie"] == sous_cat]
    type_prests = sorted(d3["Type_prestation"].dropna().unique().tolist())
    if not type_prests:
        st.info("Aucun type de prestation disponible.")
        return
    type_prest = st.selectbox("Type de prestation", type_prests, key=f"tp_{KP}")

    d4 = d3[d3["Type_prestation"] == type_prest]
    prests = sorted(d4["Prestation"].dropna().unique().tolist())
    if not prests:
        st.info("Aucune prestation disponible.")
        return
    prest = st.selectbox("Prestation", prests, key=f"prest_{KP}")

    d5 = d4[d4["Prestation"] == prest]
    candidates = build_candidates(d5)

    selected_row = render_product_selection(candidates, KP)
    if selected_row is None:
        return

    unit = str(selected_row["Unite"]) if pd.notna(selected_row["Unite"]) else ""
    emissions_per_unit = float(selected_row["Emissions_CO2"])

    use_price = st.checkbox(
        f"Ajouter un prix unitaire (€ / {unit})",
        key=f"use_price_{KP}",
    )
    price_per_unit = 0.0
    if use_price:
        price_per_unit = st.number_input(
            f"Prix (€ / {unit})",
            min_value=0.0,
            value=0.0,
            step=0.01,
            key=f"price_{KP}",
        )

    qty = st.number_input(
        f"Quantité ({unit})",
        min_value=0.0,
        value=1.0,
        step=1.0,
        key=f"qty_{KP}",
    )

    emissions_total = emissions_per_unit * qty

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(f"kg CO₂ / {unit}", f"{emissions_per_unit:.2f}")
    with col_m2:
        st.metric("kg CO₂ total", f"{emissions_total:.2f}")

    if use_price and price_per_unit > 0:
        st.metric("Coût estimé (€)", f"{price_per_unit * qty:.2f}")

    def _make_entry():
        return {
            "Categorie": str(selected_row["Categorie"]),
            "Selector": "" if sel_value is None else str(sel_value),
            "Sous_categorie": str(selected_row["Sous_categorie"]),
            "Type_prestation": str(selected_row["Type_prestation"]),
            "Prestation": str(prest),
            "Option_famille": str(selected_row["Option_famille"]),
            "Produit_process": str(selected_row["Produit_process"]),
            "Unite": unit,
            "Quantite": float(qty),
            "Emissions_specifiques": emissions_per_unit,
            "kg_CO2_total": emissions_total,
            "Prix_unitaire": price_per_unit if (use_price and price_per_unit > 0) else None,
            "Prix_total": (price_per_unit * qty) if (use_price and price_per_unit > 0) else None,
        }

    st.markdown("---")
    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button(
            "➕ Ajouter à **Configuration 1**",
            key="add_config_1",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["basket_config_1"].append(_make_entry())
            st.rerun()
    with btn2:
        if st.button(
            "➕ Ajouter à **Configuration 2**",
            key="add_config_2",
            type="secondary",
            use_container_width=True,
        ):
            st.session_state["basket_config_2"].append(_make_entry())
            st.rerun()


# =========================================================
# RENDER: BASKET  (smart cost handling)
# =========================================================
def _render_basket(config_key: str):
    basket_key = f"basket_{config_key}"
    basket = st.session_state.get(basket_key, [])

    if not basket:
        st.info("Aucune ligne ajoutée.")
        return

    basket_df = pd.DataFrame(basket)

    missing_price_indices = [
        i for i, row in enumerate(basket)
        if row.get("Prix_unitaire") is None or row.get("Prix_total") is None
    ]
    all_have_price = len(missing_price_indices) == 0

    display_df = basket_df.copy()
    display_df["Quantite"] = display_df["Quantite"].round(2)
    display_df["Emissions_specifiques"] = display_df["Emissions_specifiques"].round(2)
    display_df["kg_CO2_total"] = display_df["kg_CO2_total"].round(2)

    display_df["Prix_unitaire_display"] = display_df["Prix_unitaire"].apply(
        lambda v: f"{v:.2f} €" if pd.notna(v) and v is not None else "⚠️ manquant"
    )
    display_df["Prix_total_display"] = display_df["Prix_total"].apply(
        lambda v: f"{v:.2f} €" if pd.notna(v) and v is not None else "⚠️ manquant"
    )

    rename_map = {
        "Selector": "Sélecteur",
        "Sous_categorie": "Sous-catégorie",
        "Type_prestation": "Type de prestation",
        "Option_famille": "Famille d'option",
        "Produit_process": "Produit / process",
        "Unite": "Unité",
        "Quantite": "Quantité",
        "Emissions_specifiques": "Émissions (kg CO₂ / unité)",
        "kg_CO2_total": "kg CO₂ total",
        "Prix_unitaire_display": "Prix unitaire",
        "Prix_total_display": "Prix total",
    }
    display_df = display_df.rename(columns=rename_map)

    show_cols = [
        "Categorie", "Sélecteur", "Sous-catégorie", "Type de prestation",
        "Prestation", "Famille d'option", "Produit / process", "Unité",
        "Quantité", "Émissions (kg CO₂ / unité)", "kg CO₂ total",
        "Prix unitaire", "Prix total",
    ]
    available_cols = [c for c in show_cols if c in display_df.columns]
    st.dataframe(display_df[available_cols], use_container_width=True, hide_index=True)

    total_co2 = float(basket_df["kg_CO2_total"].sum())
    st.markdown(f"**Total CO₂ : {total_co2:.2f} kg**")

    if all_have_price:
        total_price = sum(
            row["Prix_total"] for row in basket if row.get("Prix_total") is not None
        )
        st.markdown(f"**Coût total : {total_price:.2f} €**")
    else:
        st.warning(
            "**Coût total indisponible** — veuillez renseigner un prix unitaire "
            "pour chaque ligne afin de voir le coût global."
        )
        missing_descriptions = []
        for idx in missing_price_indices:
            row = basket[idx]
            missing_descriptions.append(
                f"- **Ligne {idx + 1}** : {row['Produit_process']} "
                f"({row['Quantite']} {row['Unite']})"
            )
        st.markdown(
            "Les lignes suivantes n'ont pas de prix :\n" + "\n".join(missing_descriptions)
        )

        st.markdown("##### Compléter les prix manquants")
        changed = False
        for idx in missing_price_indices:
            row = basket[idx]
            unit = row.get("Unite", "")
            col_label, col_input, col_btn = st.columns([3, 2, 1])
            with col_label:
                st.markdown(
                    f"**Ligne {idx + 1}** — {row['Produit_process']} "
                    f"({row['Quantite']} {unit})"
                )
            with col_input:
                new_price = st.number_input(
                    f"Prix (€ / {unit})",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    key=f"retro_price_{config_key}_{idx}",
                    label_visibility="collapsed",
                )
            with col_btn:
                if st.button("✓", key=f"retro_apply_{config_key}_{idx}"):
                    if new_price > 0:
                        st.session_state[basket_key][idx]["Prix_unitaire"] = new_price
                        st.session_state[basket_key][idx]["Prix_total"] = (
                            new_price * row["Quantite"]
                        )
                        changed = True
        if changed:
            st.rerun()

    by_cat = (
        basket_df.groupby("Categorie", as_index=False)["kg_CO2_total"]
        .sum()
        .sort_values("kg_CO2_total", ascending=False)
    )
    st.markdown("**Répartition CO₂ par catégorie :**")
    st.dataframe(
        by_cat.rename(columns={"kg_CO2_total": "kg CO₂ total"}).round(2),
        use_container_width=True,
        hide_index=True,
    )

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("Retirer dernière ligne", key=f"rm_{config_key}"):
            st.session_state[basket_key].pop()
            st.rerun()
    with col_b2:
        if st.button("Vider le chiffrage", key=f"clr_{config_key}"):
            st.session_state[basket_key].clear()
            st.rerun()
    with col_b3:
        if basket:
            csv_data = basket_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Exporter CSV",
                data=csv_data,
                file_name=f"chiffrage_{config_key}.csv",
                mime="text/csv",
                key=f"dl_{config_key}",
            )


# =========================================================
# RENDER: RUNNING TOTALS
# =========================================================
def render_running_totals():
    b1 = st.session_state.get("basket_config_1", [])
    b2 = st.session_state.get("basket_config_2", [])

    total_co2_1 = sum(r["kg_CO2_total"] for r in b1) if b1 else 0.0
    total_co2_2 = sum(r["kg_CO2_total"] for r in b2) if b2 else 0.0

    def _price_total(basket):
        if not basket:
            return None
        if all(r.get("Prix_total") is not None for r in basket):
            return sum(r["Prix_total"] for r in basket)
        return None

    price1 = _price_total(b1)
    price2 = _price_total(b2)

    col1, col_sep, col2 = st.columns([5, 1, 5])

    with col1:
        st.markdown(
            f"""
            <div style="padding:12px 16px;border:2px solid {ACCENT_BLUE};border-radius:8px;
                        background:{NAVY_LIGHT};">
                <div style="font-weight:700;color:{ACCENT_BLUE};margin-bottom:6px;">
                    Configuration 1 — {len(b1)} ligne(s)
                </div>
                <div style="font-size:1.3em;color:{WHITE};">
                    🏭 <b>{total_co2_1:.2f}</b> kg CO₂
                </div>
                {"<div style='font-size:1.3em;color:" + WHITE + ";'>💶 <b>" + f"{price1:.2f}" + "</b> €</div>" if price1 is not None else ("<div style='font-size:0.85em;color:#90a4ae;'>⚠️ Prix incomplets</div>" if b1 else "")}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_sep:
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:center;'
            f'height:100%;font-size:1.5em;color:#5c6bc0;">vs</div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="padding:12px 16px;border:2px solid #7e57c2;border-radius:8px;
                        background:{NAVY_LIGHT};">
                <div style="font-weight:700;color:#7e57c2;margin-bottom:6px;">
                    Configuration 2 — {len(b2)} ligne(s)
                </div>
                <div style="font-size:1.3em;color:{WHITE};">
                    🏭 <b>{total_co2_2:.2f}</b> kg CO₂
                </div>
                {"<div style='font-size:1.3em;color:" + WHITE + ";'>💶 <b>" + f"{price2:.2f}" + "</b> €</div>" if price2 is not None else ("<div style='font-size:0.85em;color:#90a4ae;'>⚠️ Prix incomplets</div>" if b2 else "")}
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# RENDER: COMPARISON
# =========================================================
def render_comparison():
    b1 = st.session_state.get("basket_config_1", [])
    b2 = st.session_state.get("basket_config_2", [])

    if not b1 and not b2:
        st.info(
            "Ajoutez des lignes dans au moins une configuration "
            "pour voir la comparaison."
        )
        return

    df1 = pd.DataFrame(b1) if b1 else pd.DataFrame()
    df2 = pd.DataFrame(b2) if b2 else pd.DataFrame()

    total1 = float(df1["kg_CO2_total"].sum()) if not df1.empty else 0.0
    total2 = float(df2["kg_CO2_total"].sum()) if not df2.empty else 0.0

    def _safe_price_total(basket_list):
        if not basket_list:
            return None
        if all(row.get("Prix_total") is not None for row in basket_list):
            return sum(row["Prix_total"] for row in basket_list)
        return None

    price1 = _safe_price_total(b1)
    price2 = _safe_price_total(b2)

    if total1 == 0 and total2 == 0:
        better_label = "—"
        worse_label = "—"
    elif total1 <= total2:
        better_label = "Configuration 1"
        worse_label = "Configuration 2"
    else:
        better_label = "Configuration 2"
        worse_label = "Configuration 1"

    baseline = max(total1, total2)
    best = min(total1, total2)
    reduction_pct = ((baseline - best) / baseline * 100) if baseline > 0 else 0.0

    label = get_reduction_label(reduction_pct)
    color = get_reduction_color(reduction_pct)

    st.subheader("Résumé comparatif")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Configuration 1")
        st.metric("kg CO₂ total", f"{total1:.2f}")
        if price1 is not None:
            st.metric("Coût total (€)", f"{price1:.2f}")
        elif b1:
            st.caption("⚠️ Prix incomplets — coût total indisponible")
        st.caption(f"{len(b1)} ligne(s)")
    with col2:
        st.markdown("##### Configuration 2")
        st.metric("kg CO₂ total", f"{total2:.2f}")
        if price2 is not None:
            st.metric("Coût total (€)", f"{price2:.2f}")
        elif b2:
            st.caption("⚠️ Prix incomplets — coût total indisponible")
        st.caption(f"{len(b2)} ligne(s)")

    st.divider()
    if total1 == total2:
        st.info("Les deux configurations ont le même bilan carbone.")
    elif total1 == 0.0 or total2 == 0.0:
        filled = "Configuration 1" if total1 > 0 else "Configuration 2"
        st.info(
            f"Seule la **{filled}** contient des lignes. "
            "Remplissez les deux pour comparer."
        )
    else:
        st.markdown(
            f"""
            <div style="
                padding: 16px 24px;
                border: 2px solid {color};
                border-radius: 10px;
                text-align: center;
                margin-bottom: 12px;
                background: {NAVY_LIGHT};
            ">
                <div style="font-size: 0.95em; color: #b0bec5;">
                    <b>{better_label}</b> offre une réduction de
                </div>
                <div style="
                    font-size: 2.2em;
                    font-weight: bold;
                    color: {color};
                    margin: 4px 0;
                ">{reduction_pct:.1f} %</div>
                <div style="
                    font-size: 1.1em;
                    font-weight: 600;
                    color: {color};
                ">{label}</div>
                <div style="font-size: 0.85em; color: #90a4ae; margin-top: 6px;">
                    par rapport à {worse_label}
                    ({abs(total1 - total2):.2f} kg CO₂ en moins)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if price1 is not None and price2 is not None:
        price_diff = price2 - price1
        cheaper = "Configuration 1" if price_diff >= 0 else "Configuration 2"
        st.markdown(
            f"**{cheaper}** est moins chère de **{abs(price_diff):.2f} €**."
        )

    st.divider()
    st.subheader("Comparaison par catégorie")

    cats1 = (
        df1.groupby("Categorie")["kg_CO2_total"].sum()
        if not df1.empty
        else pd.Series(dtype=float)
    )
    cats2 = (
        df2.groupby("Categorie")["kg_CO2_total"].sum()
        if not df2.empty
        else pd.Series(dtype=float)
    )

    all_cats = sorted(set(cats1.index.tolist()) | set(cats2.index.tolist()))
    if all_cats:
        comp_rows = []
        for cat in all_cats:
            v1 = cats1.get(cat, 0.0)
            v2 = cats2.get(cat, 0.0)
            delta = v2 - v1
            comp_rows.append({
                "Catégorie": cat,
                "Config 1 (kg CO₂)": round(v1, 2),
                "Config 2 (kg CO₂)": round(v2, 2),
                "Δ (kg CO₂)": round(delta, 2),
            })
        comp_df = pd.DataFrame(comp_rows)
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Détails par configuration")
    det1, det2 = st.columns(2)
    with det1:
        st.markdown("**Configuration 1**")
        if not df1.empty:
            show = df1[
                ["Categorie", "Produit_process", "Option_famille", "Quantite", "kg_CO2_total"]
            ].copy()
            show = show.rename(columns={
                "Produit_process": "Produit",
                "Option_famille": "Famille",
                "Quantite": "Qté",
                "kg_CO2_total": "kg CO₂",
            }).round(2)
            st.dataframe(show, use_container_width=True, hide_index=True)
        else:
            st.info("Vide")
    with det2:
        st.markdown("**Configuration 2**")
        if not df2.empty:
            show = df2[
                ["Categorie", "Produit_process", "Option_famille", "Quantite", "kg_CO2_total"]
            ].copy()
            show = show.rename(columns={
                "Produit_process": "Produit",
                "Option_famille": "Famille",
                "Quantite": "Qté",
                "kg_CO2_total": "kg CO₂",
            }).round(2)
            st.dataframe(show, use_container_width=True, hide_index=True)
        else:
            st.info("Vide")


# =========================================================
# MAIN
# =========================================================
def main():
    st.set_page_config(
        page_title="REVERT — Chiffrage sinistre",
        page_icon="🏗️",
        layout="wide",
    )

    inject_theme()
    render_logo()

    df = load_df("carbon_data.html")

    tab_chiffrage, tab_search, tab_baskets, tab_cmp = st.tabs([
        "🔧 Sélection produit",
        "🔍 Recherche",
        "📋 Paniers (Config 1 & 2)",
        "📊 Comparaison",
    ])

    with tab_chiffrage:
        render_selection_panel(df)
        st.divider()
        st.subheader("Totaux en cours")
        render_running_totals()

    with tab_search:
        render_search(df)

    with tab_baskets:
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.subheader("Configuration 1")
            _render_basket("config_1")
        with col_b2:
            st.subheader("Configuration 2")
            _render_basket("config_2")

    with tab_cmp:
        render_comparison()

    # --- Full dataset at the very bottom (visible on all tabs) ---
    st.divider()
    render_full_dataset(df)


if __name__ == "__main__":
    main()
