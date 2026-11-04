import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Delay Impact Index (DII)", page_icon="🚨", layout="wide")
st.title("🚧 Delay Impact Index (DII) App")

# Στήλες που πρέπει να έχει το αρχείο Excel
COLUMNS = ["Εργασία", "Καθυστέρηση (ημ)", "Απόκλιση (€)", "Domino (εργασίες)",
           "Νέες Εργασίες (ημ)", "Νέες Εργασίες (€)"]
NUMERIC = COLUMNS[1:]

CATEGORIES = ["Χαμηλή Επίπτωση", "Μέτρια Επίπτωση", "Σοβαρή Επίπτωση", "Κρίσιμη Καθυστέρηση"]
COLORS = {"Χαμηλή Επίπτωση": "#4CAF50", "Μέτρια Επίπτωση": "#F5A623",
          "Σοβαρή Επίπτωση": "#E4572E", "Κρίσιμη Καθυστέρηση": "#8B1E3F"}

# ---------------- Ρυθμίσεις (πλευρική στήλη) ----------------
st.sidebar.header("⚙️ Όρια ενεργοποίησης (thresholds)")
T = {
    "delay_days": st.sidebar.number_input("Καθυστέρηση χρόνου > (ημέρες)", 0, 365, 5),
    "cost_over": st.sidebar.number_input("Απόκλιση κόστους > (€)", 0, 1_000_000, 1000, step=100),
    "domino_tasks": st.sidebar.number_input("Domino effect > (εργασίες)", 0, 100, 2),
    "new_tasks_days": st.sidebar.number_input("Πρόσθετες εργασίες – χρόνος > (ημέρες)", 0, 365, 2),
    "new_tasks_cost": st.sidebar.number_input("Πρόσθετες εργασίες – κόστος > (€)", 0, 1_000_000, 500, step=100),
    "critical_days": st.sidebar.number_input("Κρίσιμη όταν καθυστέρηση > (ημέρες)", 0, 365, 15),
}
with st.sidebar.expander("⚖️ Συντελεστές βαρύτητας (για προχωρημένους)"):
    st.caption("Στην αρχική εκδοχή του δείκτη όλα τα βάρη είναι 1, "
               "οπότε ο DII ισούται με το πλήθος των ενεργών flags.")
    W = {
        "t": st.number_input("w₁ – Χρόνος", 0.0, 5.0, 1.0, 0.1),
        "c": st.number_input("w₂ – Κόστος", 0.0, 5.0, 1.0, 0.1),
        "d": st.number_input("w₃ – Domino effect", 0.0, 5.0, 1.0, 0.1),
        "r": st.number_input("w₄ – Πρόσθετες εργασίες (rework)", 0.0, 5.0, 1.0, 0.1),
    }


def κατηγορία_από_τιμή(dii):
    if dii >= 3:
        return "Κρίσιμη Καθυστέρηση"
    if dii >= 2:
        return "Σοβαρή Επίπτωση"
    if dii >= 1:
        return "Μέτρια Επίπτωση"
    return "Χαμηλή Επίπτωση"


def υπολογισμός_dii(df):
    df = df.copy()
    # Μετατροπή σε αριθμούς: κενά ή «–» γίνονται 0 και σημειώνονται
    ελλιπή = df[NUMERIC].apply(pd.to_numeric, errors="coerce").isna().any(axis=1)
    df[NUMERIC] = df[NUMERIC].apply(pd.to_numeric, errors="coerce").fillna(0)

    # Τέσσερα flags (0 ή 1), ένα για κάθε παράμετρο του δείκτη
    df["Flag χρόνου"] = (df["Καθυστέρηση (ημ)"] > T["delay_days"]).astype(int)
    df["Flag κόστους"] = (df["Απόκλιση (€)"] > T["cost_over"]).astype(int)
    df["Flag domino"] = (df["Domino (εργασίες)"] > T["domino_tasks"]).astype(int)
    df["Flag rework"] = ((df["Νέες Εργασίες (ημ)"] > T["new_tasks_days"]) |
                         (df["Νέες Εργασίες (€)"] > T["new_tasks_cost"])).astype(int)

    df["Flags"] = df[["Flag χρόνου", "Flag κόστους", "Flag domino", "Flag rework"]].sum(axis=1)
    # DII = w1·ft + w2·fc + w3·fd + w4·fr
    df["DII"] = (W["t"] * df["Flag χρόνου"] + W["c"] * df["Flag κόστους"] +
                 W["d"] * df["Flag domino"] + W["r"] * df["Flag rework"]).round(2)

    df["Κατηγορία DII"] = [
        "Κρίσιμη Καθυστέρηση" if d > T["critical_days"] else κατηγορία_από_τιμή(v)
        for d, v in zip(df["Καθυστέρηση (ημ)"], df["DII"])
    ]
    df["Ελλιπή δεδομένα"] = ελλιπή.map({True: "Ναι", False: ""})
    return df


def σύνοψη(df):
    n = len(df)
    rows = [("Πλήθος εργασιών", str(n)), ("Μέσος DII", f"{df['DII'].mean():.2f}".replace(".", ","))]
    for c in CATEGORIES:
        k = int((df["Κατηγορία DII"] == c).sum())
        rows.append((f"Ποσοστό: {c}", f"{100 * k / n:.1f}%  ({k})"))
    rows.append(("Συνολική κρισιμότητα έργου (βάσει μέσου DII)", κατηγορία_από_τιμή(df["DII"].mean())))
    return pd.DataFrame(rows, columns=["Δείκτης", "Τιμή"])


def γραφήματα(df):
    counts = [int((df["Κατηγορία DII"] == c).sum()) for c in CATEGORIES]
    labels = [c.split()[0] for c in CATEGORIES]
    colors = [COLORS[c] for c in CATEGORIES]

    fig_pie, ax = plt.subplots(figsize=(5.5, 4))
    nz = [(l, v, col) for l, v, col in zip(labels, counts, colors) if v > 0]
    ax.pie([v for _, v, _ in nz], labels=[f"{l} ({v})" for l, v, _ in nz], colors=[c for *_, c in nz],
           autopct=lambda p: f"{p:.1f}%".replace(".", ","), startangle=90, counterclock=False,
           wedgeprops=dict(edgecolor="white", linewidth=2))
    ax.set_title("Κατανομή κατηγοριών DII")
    ax.axis("equal")

    fig_bar, ax = plt.subplots(figsize=(5.5, 4))
    bars = ax.bar(labels, counts, color=colors)
    for b, v in zip(bars, counts):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.05, str(v), ha="center", va="bottom")
    ax.set_ylabel("Αριθμός εργασιών")
    ax.set_xlabel("Κατηγορία DII")
    ax.set_title("Αριθμός εργασιών ανά κατηγορία DII")
    ax.spines[["top", "right"]].set_visible(False)
    return fig_pie, fig_bar


def png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor="white")
    return buf.getvalue()


def εμφάνιση_αποτελεσμάτων(df):
    res = υπολογισμός_dii(df)
    if (res["Ελλιπή δεδομένα"] == "Ναι").any():
        st.warning("⚠️ Ορισμένες εργασίες έχουν κενές ή μη αριθμητικές τιμές, που μετρήθηκαν ως 0: "
                   + ", ".join(res.loc[res["Ελλιπή δεδομένα"] == "Ναι", "Εργασία"].astype(str)))

    st.subheader("Αποτελέσματα ανά εργασία")
    st.dataframe(res.style.apply(
        lambda r: [f"background-color: {COLORS[r['Κατηγορία DII']]}33"] * len(r), axis=1),
        width="stretch")

    st.subheader("Σύνοψη έργου")
    summ = σύνοψη(res)
    st.table(summ)

    st.subheader("Γραφήματα")
    fig_pie, fig_bar = γραφήματα(res)
    c1, c2 = st.columns(2)
    with c1:
        st.pyplot(fig_pie)
        st.download_button("🖼️ Κατέβασε την πίτα (PNG)", png(fig_pie), "DII_pie.png", "image/png")
    with c2:
        st.pyplot(fig_bar)
        st.download_button("🖼️ Κατέβασε το ραβδόγραμμα (PNG)", png(fig_bar), "DII_bar.png", "image/png")

    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        res.to_excel(w, index=False, sheet_name="Αποτελέσματα")
        summ.to_excel(w, index=False, sheet_name="Σύνοψη")
        pd.DataFrame({"Παράμετρος": list(T) + [f"w_{k}" for k in W],
                      "Τιμή": list(T.values()) + list(W.values())}).to_excel(w, index=False, sheet_name="Ρυθμίσεις")
    st.download_button("📥 Κατέβασε τα αποτελέσματα (Excel)", out.getvalue(), "DII_results.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ---------------- Εισαγωγή δεδομένων ----------------
mode = st.radio("Επιλογή τρόπου εισαγωγής δεδομένων:", ["📂 Upload Excel", "✏️ Manual Input"])

if mode == "📂 Upload Excel":
    uploaded_file = st.file_uploader("📂 Ανέβασε το αρχείο Excel", type=["xlsx"])
    st.caption("Απαιτούμενες στήλες: " + ", ".join(COLUMNS))
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            λείπουν = [c for c in COLUMNS if c not in df.columns]
            if λείπουν:
                st.error("⚠️ Λείπουν οι στήλες: " + ", ".join(λείπουν))
            else:
                εμφάνιση_αποτελεσμάτων(df[COLUMNS])
        except Exception as e:
            st.error(f"⚠️ Σφάλμα: {e}")
    else:
        st.info("➕ Ανέβασε Excel για να ξεκινήσεις...")

else:
    num_tasks = st.number_input("Πλήθος εργασιών", min_value=1, step=1)
    tasks = []
    for i in range(int(num_tasks)):
        st.subheader(f"Εργασία {i + 1}")
        name = st.text_input(f"Όνομα Εργασίας {i + 1}", key=f"name_{i}")
        c = st.columns(5)
        tasks.append({
            "Εργασία": name,
            "Καθυστέρηση (ημ)": c[0].number_input("Καθυστέρηση (ημ)", min_value=0, step=1, key=f"delay_{i}"),
            "Απόκλιση (€)": c[1].number_input("Απόκλιση (€)", min_value=0.0, step=100.0, key=f"cost_{i}"),
            "Domino (εργασίες)": c[2].number_input("Domino (εργασίες)", min_value=0, step=1, key=f"domino_{i}"),
            "Νέες Εργασίες (ημ)": c[3].number_input("Νέες Εργασίες (ημ)", min_value=0, step=1, key=f"new_days_{i}"),
            "Νέες Εργασίες (€)": c[4].number_input("Νέες Εργασίες (€)", min_value=0.0, step=100.0, key=f"new_cost_{i}"),
        })
    if st.button("Υπολόγισε DII"):
        εμφάνιση_αποτελεσμάτων(pd.DataFrame(tasks))
