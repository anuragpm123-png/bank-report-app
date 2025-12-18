import streamlit as st
import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Bank Report Generator", layout="wide")
st.title("🏦 Bank Statement Report Generator")

uploaded_file = st.file_uploader("Upload Bank Statement PDF", type="pdf")

rows = []

# ---------- HELPER FUNCTION ----------
def clean_amount(x):
    x = str(x).replace(",", "").strip()
    if x.startswith("(") and x.endswith(")"):
        return -float(x[1:-1])
    return float(x) if x and x != "None" else 0.0

# ---------- PDF EXTRACTION ----------
if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table[1:]:
                if len(row) < 9:
                    continue
                rows.append({
                    "Date": row[0],
                    "Particulars": row[2],
                    "Withdrawals": row[6],
                    "Deposits": row[7],
                    "Balance": row[8]
                })

# ---------- REPORT ----------
if rows:
    df = pd.DataFrame(rows)

    # Clean numeric columns
    df["Withdrawals"] = df["Withdrawals"].apply(clean_amount)
    df["Deposits"] = df["Deposits"].apply(clean_amount)
    df["Balance"] = df["Balance"].apply(clean_amount)

    # Date handling
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.sort_values("Date")

    st.success("✅ Report generated successfully")

    # ---------- FULL TABLE ----------
    st.subheader("📋 Full Transaction Report")
    st.table(df)  # static table to bypass PyArrow

    # ---------- SUMMARY ----------
    st.subheader("📊 Summary")
    total_debit = df["Withdrawals"].sum()
    total_credit = df["Deposits"].sum()
    net_cash = total_credit - total_debit

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Debit", f"₹ {total_debit:,.2f}")
    c2.metric("Total Credit", f"₹ {total_credit:,.2f}")
    c3.metric("Net Cash Flow", f"₹ {net_cash:,.2f}")

    # ---------- MONTHLY REPORT ----------
    st.subheader("📅 Monthly Report")
    df["Month"] = df["Date"].dt.strftime("%B %Y")
    monthly = df.groupby("Month")[["Withdrawals", "Deposits"]].sum()
    st.table(monthly)

    # ---------- MONTHLY BAR CHART ----------
    st.subheader("📊 Monthly Debit vs Credit")
    fig1, ax1 = plt.subplots()
    monthly.plot(kind="bar", ax=ax1)
    ax1.set_ylabel("Amount")
    ax1.set_xlabel("Month")
    plt.xticks(rotation=45)
    st.pyplot(fig1)

    # ---------- BALANCE TREND ----------
    st.subheader("📈 Balance Trend Over Time")
    fig2, ax2 = plt.subplots()
    ax2.plot(df["Date"], df["Balance"], marker='o')
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Balance")
    plt.xticks(rotation=45)
    st.pyplot(fig2)

    # ---------- EXPENSE CATEGORIES ----------
    st.subheader("🧾 Expense Categories")

    def categorize(desc):
        d = str(desc).lower()
        if "loan" in d: return "Loan"
        if "salary" in d: return "Salary"
        if "neft" in d: return "NEFT"
        if "upi" in d: return "UPI"
        if "transfer" in d or "tfr" in d: return "Transfer"
        return "Others"

    df["Category"] = df["Particulars"].apply(categorize)
    category_summary = df.groupby("Category")["Withdrawals"].sum()
    st.table(category_summary)

    # ---------- PIE CHART ----------
    st.subheader("🥧 Expense Category Chart")
    fig3, ax3 = plt.subplots()
    category_summary.plot.pie(autopct="%1.1f%%", ylabel="", ax=ax3)
    st.pyplot(fig3)

    # ---------- EXCEL DOWNLOAD ----------
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    st.download_button(
        "⬇ Download Excel Report",
        data=output,
        file_name="bank_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("📄 Upload a bank statement PDF to generate the report.")
