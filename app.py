from fractions import Fraction
import re
import pandas as pd
import streamlit as st

def display_specific_designations_auto(df: pd.DataFrame):
    """
    ✅ Auto-detect:
      - marques/fournisseurs
      - modèles (designation)
      - chaussures (via famille/ssfamille/designation)
      - grille de tailles attendue (pas + min/max typiques par marque+rayon)
      - tailles manquantes par modèle + rayon

    Colonnes attendues (minimum):
      - designation, taille, rayon
      - et idéalement: marque OU fournisseur
      - (optionnel) famille, ssfamille
    """

    # ----------------------------
    # Helpers: parsing tailles
    # ----------------------------
    UNICODE_FRAC = {
        "½": Fraction(1, 2),
        "⅓": Fraction(1, 3),
        "⅔": Fraction(2, 3),
        "¼": Fraction(1, 4),
        "¾": Fraction(3, 4),
        "⅕": Fraction(1, 5),
        "⅖": Fraction(2, 5),
        "⅗": Fraction(3, 5),
        "⅘": Fraction(4, 5),
        "⅙": Fraction(1, 6),
        "⅚": Fraction(5, 6),
    }

    def _clean_size_str(x) -> str:
        if pd.isna(x):
            return ""
        s = str(x).strip().upper()
        # enlever les mentions de systèmes
        s = s.replace("US", "").replace("UK", "").replace("EU", "")
        s = s.replace(",", ".")
        # enlever suffixes courants non-numeriques
        s = re.sub(r"\b(W|WMNS|WOMAN|WOMEN)\b", "", s).strip()
        # normaliser séparateurs
        s = s.replace("-", " ")
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def parse_size_to_fraction(x):
        """
        Retourne Fraction (denom <= 6) ou None si impossible.
        Gère:
          - "7", "7.5"
          - "7 1/3", "7 2/3"
          - "7⅓"
        """
        s = _clean_size_str(x)
        if not s:
            return None

        # cas unicode fraction (ex: 7⅓)
        for symb, frac in UNICODE_FRAC.items():
            if symb in s:
                base = s.replace(symb, "").strip()
                base = base if base else "0"
                try:
                    base_f = Fraction(float(base)).limit_denominator(6)
                    return (base_f + frac).limit_denominator(6)
                except:
                    return None

        # cas "7 1/3"
        m = re.match(r"^(\d+)\s+(\d+)\s*/\s*(\d+)$", s)
        if m:
            a = int(m.group(1))
            b = int(m.group(2))
            c = int(m.group(3))
            if c != 0:
                return (Fraction(a, 1) + Fraction(b, c)).limit_denominator(6)

        # cas "7.5" ou "7"
        m = re.match(r"^(\d+(\.\d+)?)$", s)
        if m:
            try:
                return Fraction(float(s)).limit_denominator(6)
            except:
                return None

        # fallback: extraire le 1er nombre dans la chaîne
        m = re.search(r"(\d+(\.\d+)?)", s)
        if m:
            try:
                return Fraction(float(m.group(1))).limit_denominator(6)
            except:
                return None

        return None

    def infer_step(frac_sizes):
        """
        Déduit le pas de tailles parmi des candidats.
        On choisit le plus GRAND pas qui explique bien les tailles (évite 1/4 si 1/2 suffit).
        """
        uniq = sorted(set(frac_sizes))
        if len(uniq) < 2:
            return Fraction(1, 1)

        # candidats (tu peux en ajouter si besoin)
        candidates = [Fraction(1, 1), Fraction(1, 2), Fraction(1, 3), Fraction(1, 4), Fraction(1, 6)]
        base = uniq[0]

        def score(step):
            ok = 0
            for v in uniq:
                d = v - base
                # exact divisibility en Fractions
                if (d / step).denominator == 1:
                    ok += 1
            return ok / max(1, len(uniq))

        # trier par (score desc, step desc)
        ranked = sorted(candidates, key=lambda stp: (score(stp), float(stp)), reverse=True)

        # prendre le meilleur qui a un score solide
        best = ranked[0]
        if score(best) >= 0.9:
            return best

        # sinon fallback: prendre le plus petit diff
        diffs = [uniq[i+1] - uniq[i] for i in range(len(uniq)-1) if uniq[i+1] > uniq[i]]
        return min(diffs) if diffs else Fraction(1, 1)

    def round_to_step(x: Fraction, step: Fraction, mode="floor"):
        """
        Arrondit x sur la grille de step.
        """
        q = x / step
        if q.denominator != 1:
            # q est fraction -> floor/ceil
            if mode == "floor":
                n = q.numerator // q.denominator
            else:
                n = -(-q.numerator // q.denominator)  # ceil
        else:
            n = q.numerator
        return Fraction(n, 1) * step

    def format_size(fr: Fraction, step: Fraction):
        """
        Format affichage:
          - si pas en 1/3 => "7.0", "7.5"
          - si pas en 1/3 => "7", "7 1/3", "7 2/3"
        """
        # si la taille est entière
        if fr.denominator == 1:
            return str(fr.numerator)

        # tiers
        if step in [Fraction(1, 3), Fraction(1, 6)] and fr.denominator in [3, 6]:
            whole = fr.numerator // fr.denominator
            rem = fr - whole
            if rem == 0:
                return str(whole)
            # ramener en /3 si possible
            rem3 = rem.limit_denominator(3)
            if rem3.denominator == 3:
                return f"{whole} {rem3.numerator}/{rem3.denominator}"
            return f"{float(fr):.2f}"

        # demi / quart -> afficher en .0 / .5 etc
        val = float(fr)
        # .1f si ça colle bien
        if abs(val * 2 - round(val * 2)) < 1e-9:
            return f"{val:.1f}"
        return f"{val:.2f}"

    # ----------------------------
    # Choix colonne marque vs fournisseur
    # ----------------------------
    brand_col = "marque" if "marque" in df.columns else ("fournisseur" if "fournisseur" in df.columns else None)
    if brand_col is None:
        st.error("Il manque la colonne 'marque' ou 'fournisseur'.")
        return

    required = ["designation", "taille", "rayon"]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        st.error(f"Colonnes manquantes: {missing_cols}")
        return

    # ----------------------------
    # Filtre chaussures (auto)
    # ----------------------------
    df_work = df.copy()
    for c in ["famille", "ssfamille", "designation", "rayon", brand_col]:
        if c in df_work.columns:
            df_work[c] = df_work[c].fillna("").astype(str)

    shoe_mask = pd.Series(False, index=df_work.index)
    if "famille" in df_work.columns:
        shoe_mask |= df_work["famille"].str.upper().str.contains("CHAUSS", na=False)
    if "ssfamille" in df_work.columns:
        shoe_mask |= df_work["ssfamille"].str.upper().str.contains("CHAUSS", na=False)
    # fallback (si pas famille/ssfamille fiables)
    shoe_mask |= df_work["designation"].str.upper().str.contains("SHOE|CHAUSS|RUN|TRAIL|RANDO", na=False)

    df_shoes = df_work[shoe_mask].copy()
    if df_shoes.empty:
        st.warning("Je n'ai trouvé aucune ligne 'chaussures' automatiquement. J'affiche tout le fichier.")
        df_shoes = df_work.copy()

    # ----------------------------
    # CSS (tes boutons)
    # ----------------------------
    st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #000000;
        color: #FFFFFF;
        border: 2px solid #FFFFFF;
        border-radius: 4px;
        padding: 12px 20px;
        font-weight: bold;
        width: 100%;
        margin: 5px 0;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## TAILLES MANQUANTES (AUTO)")

    # ----------------------------
    # UI: sélection marque/fournisseur auto
    # ----------------------------
    brands = sorted([b for b in df_shoes[brand_col].unique() if str(b).strip() != ""])
    if not brands:
        st.warning(f"Aucune valeur trouvée dans '{brand_col}'.")
        return

    cols = st.columns(4)
    for i, b in enumerate(brands[:20]):  # boutons pour les 20 premiers
        with cols[i % 4]:
            if st.button(b, key=f"auto_brand_btn_{b}"):
                st.session_state.auto_selected_brand = b

    selected_brand = st.session_state.get("auto_selected_brand", None)
    # si plus de 20 marques, selectbox
    if len(brands) > 20:
        selected_brand = st.selectbox("Choisir une marque/fournisseur :", brands, index=0)
        st.session_state.auto_selected_brand = selected_brand

    if not selected_brand:
        st.info("Sélectionne une marque/fournisseur pour afficher les tailles manquantes.")
        return

    df_b = df_shoes[df_shoes[brand_col].str.upper() == str(selected_brand).upper()].copy()
    if df_b.empty:
        st.warning("Aucune ligne pour cette marque/fournisseur.")
        return

    # ----------------------------
    # Préparer tailles numériques
    # ----------------------------
    df_b["size_frac"] = df_b["taille"].apply(parse_size_to_fraction)
    df_b = df_b.dropna(subset=["size_frac"]).copy()
    if df_b.empty:
        st.warning("Impossible de parser les tailles (colonne 'taille') en valeurs numériques.")
        return

    # ----------------------------
    # Construire baseline (min/max/step typiques par marque+rayon)
    # ----------------------------
    grp = df_b.groupby(["designation", "rayon"], dropna=False)

    model_stats = []
    for (des, ray), g in grp:
        sizes = sorted(set(g["size_frac"].tolist()))
        if len(sizes) == 0:
            continue
        step = infer_step(sizes)
        model_stats.append({
            "designation": des,
            "rayon": ray,
            "min_size": sizes[0],
            "max_size": sizes[-1],
            "step": step,
            "n_sizes": len(sizes),
        })

    if not model_stats:
        st.warning("Pas assez de données pour calculer les tailles manquantes.")
        return

    stats_df = pd.DataFrame(model_stats)

    # baseline par rayon (médiane des min/max + pas le plus fréquent)
    baseline = {}
    for ray, g in stats_df.groupby("rayon"):
        # médiane sur float puis reconvertir en fraction (denom <= 6)
        min_med = Fraction(float(pd.Series([float(x) for x in g["min_size"]]).median())).limit_denominator(6)
        max_med = Fraction(float(pd.Series([float(x) for x in g["max_size"]]).median())).limit_denominator(6)

        # pas le plus fréquent
        step_counts = g["step"].value_counts()
        step_mode = step_counts.index[0] if len(step_counts) else Fraction(1, 1)

        baseline[ray] = {"min": min_med, "max": max_med, "step": step_mode}

    # ----------------------------
    # Résultats: tailles manquantes par modèle + rayon
    # ----------------------------
    rows = []
    for _, r in stats_df.iterrows():
        des = r["designation"]
        ray = r["rayon"]

        base = baseline.get(ray, None)
        step = base["step"] if base else r["step"]

        # min/max attendus = baseline (pour détecter aussi les tailles “aux extrêmes” manquantes)
        exp_min = base["min"] if base else r["min_size"]
        exp_max = base["max"] if base else r["max_size"]

        # arrondir sur la grille
        exp_min = round_to_step(exp_min, step, "floor")
        exp_max = round_to_step(exp_max, step, "ceil")

        # tailles présentes
        g = df_b[(df_b["designation"] == des) & (df_b["rayon"] == ray)]
        present = sorted(set(g["size_frac"].tolist()))

        # générer attendu
        expected = []
        cur = exp_min
        # sécurité boucle
        for _k in range(500):
            if cur > exp_max + step / 10:
                break
            expected.append(cur)
            cur += step

        missing = [x for x in expected if x not in set(present)]

        rows.append({
            "Modèle": des,
            "Rayon": ray,
            "Pas détecté": format_size(step, step),
            "Tailles dispo": len(present),
            "Tailles attendues": len(expected),
            "Tailles manquantes": ", ".join(format_size(x, step) for x in missing) if missing else "Complet",
        })

    results_df = pd.DataFrame(rows)
    # Trier: rayon puis modèle
    results_df = results_df.sort_values(["Rayon", "Modèle"], ascending=[True, True])

    st.markdown(f"### {selected_brand} — tailles manquantes détectées automatiquement")
    st.dataframe(results_df, use_container_width=True)

    # ----------------------------
    # Export (Excel / CSV)
    # ----------------------------
    st.markdown("---")
    st.markdown("### Options d'export")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 Exporter en Excel (XLSX)", key=f"auto_export_excel_{selected_brand}"):
            try:
                import io
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    results_df.to_excel(writer, sheet_name="Tailles_manquantes", index=False)
                st.download_button(
                    label="⬇ Télécharger le fichier Excel",
                    data=output.getvalue(),
                    file_name=f"{selected_brand}_tailles_manquantes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"auto_dl_excel_{selected_brand}",
                )
            except Exception as e:
                st.error(f"Erreur export Excel: {e}")

    with col2:
        if st.button("📄 Exporter en CSV", key=f"auto_export_csv_{selected_brand}"):
            try:
                csv = results_df.to_csv(index=False, sep=";")
                st.download_button(
                    label="⬇ Télécharger le fichier CSV",
                    data=csv,
                    file_name=f"{selected_brand}_tailles_manquantes.csv",
                    mime="text/csv",
                    key=f"auto_dl_csv_{selected_brand}",
                )
            except Exception as e:
                st.error(f"Erreur export CSV: {e}")
