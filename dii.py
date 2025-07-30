import streamlit as st
import pandas as pd

st.set_page_config(page_title="Delay Impact Index (DII)", page_icon="🚨")

st.title("🚧 Delay Impact Index (DII) App")

# Thresholds
THRESHOLDS = {
    "delay_days": 5,
    "cost_over": 1000,
    "domino_tasks": 2,
    "new_tasks_days": 2,
    "new_tasks_cost": 500
}

# Επιλογή Mode
mode = st.radio("Επιλογή τρόπου εισαγωγής δεδομένων:", ["📂 Upload Excel", "✏️ Manual Input"])

def υπολογισμός_dii(df):
    # Υπολογισμός flags
    df["Flags"] = 0
    df["Flags"] += (df["Καθυστέρηση (ημ)"] > THRESHOLDS["delay_days"]).astype(int)
    df["Flags"] += (df["Απόκλιση (€)"] > THRESHOLDS["cost_over"]).astype(int)
    df["Flags"] += (df["Domino (εργασίες)"] > THRESHOLDS["domino_tasks"]).astype(int)
    df["Flags"] += (df["Νέες Εργασίες (ημ)"] > THRESHOLDS["new_tasks_days"]).astype(int)
    df["Flags"] += (df["Νέες Εργασίες (€)"] > THRESHOLDS["new_tasks_cost"]).astype(int)

    # Κατηγοριοποίηση
    def κατηγορία(row):
        if row["Καθυστέρηση (ημ)"] > 15 or row["Flags"] >= 3:
            return "🚨 Κρίσιμη Καθυστέρηση"
        elif row["Flags"] == 2:
            return "🔴 Σοβαρή Επίπτωση"
        elif row["Flags"] == 1:
            return "🟠 Μέτρια Επίπτωση"
        else:
            return "🟢 Χαμηλή Επίπτωση"
    df["Κατηγορία DII"] = df.apply(κατηγορία, axis=1)
    return df

if mode == "📂 Upload Excel":
    uploaded_file = st.file_uploader("📂 Ανέβασε το αρχείο Excel", type=["xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            df = υπολογισμός_dii(df)
            st.dataframe(df)
            output_path = "DII_results.xlsx"
            df.to_excel(output_path, index=False)
            with open(output_path, "rb") as f:
                st.download_button("📥 Κατέβασε τα αποτελέσματα", f, file_name="DII_results.xlsx")
        except Exception as e:
            st.error(f"⚠️ Σφάλμα: {e}")
    else:
        st.info("➕ Ανέβασε Excel για να ξεκινήσεις...")

elif mode == "✏️ Manual Input":
    num_tasks = st.number_input("Πλήθος εργασιών", min_value=1, step=1)
    tasks = []
    for i in range(num_tasks):
        st.subheader(f"Εργασία {i+1}")
        task_name = st.text_input(f"Όνομα Εργασίας {i+1}", key=f"name_{i}")
        delay_days = st.number_input(f"Καθυστέρηση (ημ) - {task_name}", min_value=0, step=1, key=f"delay_{i}")
        cost_over = st.number_input(f"Απόκλιση (€) - {task_name}", min_value=0.0, step=100.0, key=f"cost_{i}")
        domino = st.number_input(f"Domino (εργασίες) - {task_name}", min_value=0, step=1, key=f"domino_{i}")
        new_tasks_days = st.number_input(f"Νέες Εργασίες (ημ) - {task_name}", min_value=0, step=1, key=f"new_days_{i}")
        new_tasks_cost = st.number_input(f"Νέες Εργασίες (€) - {task_name}", min_value=0.0, step=100.0, key=f"new_cost_{i}")
        
        tasks.append({
            "Εργασία": task_name,
            "Καθυστέρηση (ημ)": delay_days,
            "Απόκλιση (€)": cost_over,
            "Domino (εργασίες)": domino,
            "Νέες Εργασίες (ημ)": new_tasks_days,
            "Νέες Εργασίες (€)": new_tasks_cost
        })

    if st.button("Υπολόγισε DII"):
        df = pd.DataFrame(tasks)
        df = υπολογισμός_dii(df)
        st.dataframe(df)
        output_path = "DII_results_manual.xlsx"
        df.to_excel(output_path, index=False)
        with open(output_path, "rb") as f:
            st.download_button("📥 Κατέβασε τα αποτελέσματα", f, file_name="DII_results_manual.xlsx")
