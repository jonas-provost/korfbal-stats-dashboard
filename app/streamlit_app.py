"""Start met:  streamlit run app/streamlit_app.py"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from korfbal_stats.analytics import match_features, player_totals
from korfbal_stats.transform import build_all
from korfbal_stats.validate import validate

st.set_page_config(page_title="Korfbal stats", page_icon="🏐", layout="wide")

PCT = st.column_config.NumberColumn(format="%.1f%%")   # 38.9%
DEC = st.column_config.NumberColumn(format="%.2f")     # 1.25


def pct(x) -> str:
    """Fractie -> '38.9%' (altijd één decimaal, punt als decimaalteken)."""
    return "–" if pd.isna(x) else f"{x * 100:.1f}%"


def percent_cols(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Zet fracties (0-1) om naar 0-100 voor weergave met %-opmaak."""
    out = df.copy()
    out[cols] = out[cols] * 100
    return out


@st.cache_data(show_spinner="Wedstrijden inlezen…")
def load(raw_dir: str, signature: tuple):
    return build_all(Path(raw_dir))


def find_data_dir() -> tuple[Path, bool]:
    """Kiest de datamap: 1) KORFBAL_DATA_DIR, 2) data/raw, 3) demo in sample_data. Geeft (map, is_demo)."""
    env = os.environ.get("KORFBAL_DATA_DIR")
    if env:
        folder = Path(env).expanduser()
        if not any(folder.glob("*.xlsx")):
            st.error(f"KORFBAL_DATA_DIR wijst naar '{folder}', maar daar staan geen .xlsx-bestanden.")
            st.stop()
        return folder, False
    local = ROOT / "data" / "raw"
    if any(local.glob("*.xlsx")):
        return local, False
    return ROOT / "sample_data", True


raw, is_demo = find_data_dir()
files = sorted(raw.glob("*.xlsx"))
model = load(str(raw), tuple((f.name, f.stat().st_mtime) for f in files))

# ---------- Filters ----------
dm = model["dim_match"].sort_values("datum")
st.sidebar.title("Filters")
st.sidebar.caption("📂 Demo-data (fictief)" if is_demo else f"📂 Eigen data ({raw.name})")
season = st.sidebar.selectbox("Seizoen", sorted(dm["seizoen"].unique(), reverse=True))
season_matches = dm[dm["seizoen"] == season]
labels = {r.match_id: f"{r.datum} – {r.tegenstander} ({r.doelpunten_voor}-{r.doelpunten_tegen})"
          for r in season_matches.itertuples()}
selected = st.sidebar.multiselect("Wedstrijd(en)", list(labels), default=list(labels),
                                  format_func=labels.get,
                                  help="Alles geselecteerd = heel seizoen. Kies er één voor één wedstrijd.")
if not selected:
    st.warning("Kies minstens één wedstrijd in de zijbalk.")
    st.stop()

issues = validate(model)
if issues:
    with st.sidebar.expander(f"⚠️ {len(issues)} datacontrole(s)"):
        for i in issues:
            st.write(i)

sel = lambda df: df[df["match_id"].isin(selected)]  # noqa: E731
mf = sel(match_features(model))
mf = mf.assign(label=mf["match_id"].map(labels))
pm = sel(model["fact_player_match"])
pos = sel(model["fact_possession"])
shots = sel(model["fact_shots"])

st.title("🏐 Korfbal statistieken")
st.caption(f"Seizoen {season} · {len(selected)} van {len(season_matches)} wedstrijd(en) geselecteerd")

tab_ov, tab_team, tab_pl, tab_shot = st.tabs(["Overzicht", "Team", "Spelers", "Schotkaart"])

# ---------- Overzicht ----------
with tab_ov:
    w, g, v = (int((mf["resultaat"] == r).sum()) for r in "WGV")
    c = st.columns(5)
    c[0].metric("Wedstrijden", len(mf))
    c[1].metric("W / G / V", f"{w} / {g} / {v}")
    c[2].metric("Doelpunten", f"{int(mf['doelpunten_voor'].sum())} – {int(mf['doelpunten_tegen'].sum())}")
    c[3].metric("Doelsaldo", f"{int(mf['doelsaldo'].sum()):+d}")
    c[4].metric("Winstpercentage", pct(w / len(mf)))

    long = mf.melt(id_vars="label", value_vars=["doelpunten_voor", "doelpunten_tegen"],
                   var_name="wie", value_name="doelpunten")
    long["wie"] = long["wie"].map({"doelpunten_voor": "Voor", "doelpunten_tegen": "Tegen"})
    st.plotly_chart(px.bar(long, x="label", y="doelpunten", color="wie", barmode="group",
                           labels={"label": "", "doelpunten": "Doelpunten", "wie": ""}),
                    width="stretch")
    if len(mf) > 1:
        cum = mf.assign(cumulatief=mf["doelsaldo"].cumsum())
        st.plotly_chart(px.line(cum, x="datum", y="cumulatief", markers=True,
                                labels={"cumulatief": "Cumulatief doelsaldo", "datum": ""}),
                        width="stretch")
    st.dataframe(mf[["datum", "tegenstander", "doelpunten_voor", "doelpunten_tegen", "resultaat"]],
                 hide_index=True, width="stretch")

# ---------- Team ----------
with tab_team:
    tot = mf[["schoten", "goals", "veld_schoten", "veld_goals", "vrijworp_gescoord", "vrijworp_totaal",
              "penalty_gescoord", "penalty_totaal", "doorloper_gescoord", "doorloper_totaal"]].sum()
    div = lambda a, b: a / b if b else float("nan")  # noqa: E731

    st.subheader("Schieten")
    c = st.columns(5)
    for col, (naam, gesc, tot_n) in zip(c, [
        ("Schotpercentage", tot.goals, tot.schoten),
        ("Veldschot", tot.veld_goals, tot.veld_schoten),
        ("Vrijworp", tot.vrijworp_gescoord, tot.vrijworp_totaal),
        ("Penalty", tot.penalty_gescoord, tot.penalty_totaal),
        ("Doorloper", tot.doorloper_gescoord, tot.doorloper_totaal),
    ]):
        col.metric(naam, pct(div(gesc, tot_n)), f"{int(gesc)}/{int(tot_n)}", delta_color="off")

    st.subheader("Aanvallen: wij vs tegenstander")
    rows = []
    for naam, own in [("Wij", 1), ("Tegenstander", 0)]:
        p = pos[pos["eigen_aanval"] == own]
        n = len(p)
        rows.append({"Team": naam, "Aanvallen": n, "Kansen": int(p["aantal_kansen"].sum()),
                     "Kansen per aanval": div(p["aantal_kansen"].sum(), n),
                     "Aanvallen met doelpunt %": div(p["doelpunt"].sum(), n) * 100,
                     "Aanvallen zonder kans %": div((p["aantal_kansen"] == 0).sum(), n) * 100})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                 column_config={"Kansen per aanval": DEC, "Aanvallen met doelpunt %": PCT,
                                "Aanvallen zonder kans %": PCT})

    if len(selected) == 1:
        st.subheader("Verloop van de aanvallen")
        p = pos.assign(Doelpunt=pos["doelpunt"].map({1: "Ja", 0: "Nee"}))
        st.plotly_chart(px.bar(p, x="aanval_nr", y="aantal_kansen", color="Doelpunt", pattern_shape="team",
                               color_discrete_map={"Ja": "#2e9d5b", "Nee": "#b0b7c3"},
                               labels={"aanval_nr": "Aanval", "aantal_kansen": "Kansen", "team": "Team"}),
                        width="stretch")
    else:
        st.subheader("Per wedstrijd")
        per = mf.rename(columns={
            "label": "Wedstrijd", "schotpercentage": "Schot %", "veldschot_pct": "Veldschot %",
            "kansen_per_aanval_eigen": "Kansen/aanval (wij)", "goals_per_aanval_eigen": "Doelpunt % aanval (wij)",
            "kansen_per_aanval_tegen": "Kansen/aanval (tegen)", "goals_per_aanval_tegen": "Doelpunt % aanval (tegen)",
        })
        pct_cols = ["Schot %", "Veldschot %", "Doelpunt % aanval (wij)", "Doelpunt % aanval (tegen)"]
        per = percent_cols(per[["Wedstrijd", *pct_cols, "Kansen/aanval (wij)", "Kansen/aanval (tegen)"]], pct_cols)
        cfg = {c: PCT for c in pct_cols} | {"Kansen/aanval (wij)": DEC, "Kansen/aanval (tegen)": DEC}
        st.dataframe(per, hide_index=True, width="stretch", column_config=cfg)

# ---------- Spelers ----------
with tab_pl:
    pt = player_totals(pm).rename(columns={
        "schotpercentage": "schot %", "veldschot_pct": "veldschot %",
        "aandeel_teamgoals": "aandeel teamgoals %", "goals_per_wedstrijd": "goals per wedstrijd"})
    pcols = ["schot %", "veldschot %", "aandeel teamgoals %"]
    table = percent_cols(pt, pcols)[["speler", "wedstrijden", "schoten", "goals", *pcols,
                                     "rebounds", "assists", "steals", "tegengoals", "goals per wedstrijd"]]
    st.dataframe(table, hide_index=True, width="stretch",
                 column_config={c: PCT for c in pcols} | {"goals per wedstrijd": st.column_config.NumberColumn(format="%.1f")})

    left, right = st.columns(2)
    types = pt.melt(id_vars="speler",
                    value_vars=["veld_goals", "vrijworp_gescoord", "penalty_gescoord", "doorloper_gescoord"],
                    var_name="soort", value_name="aantal")
    types["soort"] = types["soort"].map({"veld_goals": "Veld", "vrijworp_gescoord": "Vrijworp",
                                         "penalty_gescoord": "Penalty", "doorloper_gescoord": "Doorloper"})
    left.plotly_chart(px.bar(types, x="speler", y="aantal", color="soort", title="Goals per soort"),
                      width="stretch")
    acts = pt.melt(id_vars="speler", value_vars=["rebounds", "assists", "steals", "tegengoals"],
                   var_name="actie", value_name="aantal")
    right.plotly_chart(px.bar(acts, x="speler", y="aantal", color="actie", barmode="group",
                              title="Acties per speler"), width="stretch")

    st.subheader("Speler per wedstrijd")
    who = st.selectbox("Speler", pt["speler"])
    one = pm[pm["speler"] == who].merge(dm[["match_id", "datum", "tegenstander"]], on="match_id").sort_values("datum")
    st.dataframe(one[["datum", "tegenstander", "schoten", "goals", "rebounds", "assists", "steals", "tegengoals"]],
                 hide_index=True, width="stretch")

# ---------- Schotkaart ----------
with tab_shot:
    all_players = sorted(shots["speler"].unique())
    players = st.multiselect("Spelers", all_players, default=all_players)
    s = shots[shots["speler"].isin(players)]
    if s.empty:
        st.info("Geen schotlocaties voor deze selectie.")
    else:
        s = s.assign(Resultaat=s["doelpunt"].map({1: "Doelpunt", 0: "Gemist"}))
        fig = px.scatter(s, x="x", y="y", color="Resultaat", symbol="speler",
                         color_discrete_map={"Doelpunt": "#2e9d5b", "Gemist": "#d64545"})
        fig.update_yaxes(autorange="reversed", scaleanchor="x")  # app-coördinaten: y wijst naar beneden
        fig.update_traces(marker_size=11)
        st.plotly_chart(fig, width="stretch")

        z = s.groupby(["y_bin", "x_bin"]).agg(schoten=("doelpunt", "size"), goals=("doelpunt", "sum")).reset_index()
        z["pct"] = z["goals"] / z["schoten"] * 100
        piv = z.pivot(index="y_bin", columns="x_bin", values="pct")
        cnt = z.pivot(index="y_bin", columns="x_bin", values="schoten")
        heat = go.Figure(go.Heatmap(z=piv.values, x=piv.columns, y=piv.index, zmin=0, zmax=100,
                                    colorscale="RdYlGn", text=cnt.values, texttemplate="%{text}",
                                    colorbar=dict(title="Score", ticksuffix="%")))
        heat.update_yaxes(autorange="reversed")
        heat.update_layout(title="Scoringspercentage per zone (cijfer = aantal schoten)")
        st.plotly_chart(heat, width="stretch")
