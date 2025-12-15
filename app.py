import streamlit as st
import pandas as pd
import json

# ---------------- CONFIG ----------------
st.set_page_config(page_title="My Investing Dashboard", layout="wide")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_baskets():
    return json.load(open("baskets.json"))

@st.cache_data
def load_rules():
    return json.load(open("rules.json"))

baskets = load_baskets()
rules = load_rules()

# ---------------- SESSION STATE ----------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(
        columns=["Stock", "Qty", "Avg", "CMP"]
    )

# ---------------- SIDEBAR ----------------
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Dashboard", "My Portfolio", "Stock Baskets", "Daily Review", "Tools", "Rulebook"]
)

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.title("🏠 Dashboard")

    df = st.session_state.portfolio.copy()
    if not df.empty:
        df["Value"] = df["Qty"] * df["CMP"]
        df["P&L %"] = ((df["CMP"] - df["Avg"]) / df["Avg"]) * 100
        total_value = df["Value"].sum()
        overall_pnl = df["P&L %"].mean()
    else:
        total_value = 0
        overall_pnl = 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Portfolio Value", f"₹{total_value:,.0f}")
    col2.metric("Avg P&L %", f"{overall_pnl:.2f}%")
    col3.metric("Active Baskets", len(baskets))

# ---------------- MY PORTFOLIO ----------------
elif page == "My Portfolio":
    st.title("📈 My Portfolio")

    with st.form("add_stock"):
        col1, col2, col3, col4 = st.columns(4)
        stock = col1.text_input("Stock")
        qty = col2.number_input("Quantity", min_value=1)
        avg = col3.number_input("Avg Price", min_value=0.0)
        cmp = col4.number_input("CMP", min_value=0.0)
        add = st.form_submit_button("Add / Update")

        if add:
            df = st.session_state.portfolio
            df = df[df["Stock"] != stock]
            df.loc[len(df)] = [stock, qty, avg, cmp]
            st.session_state.portfolio = df
            st.success("Stock added / updated")

    if not st.session_state.portfolio.empty:
        df = st.session_state.portfolio.copy()
        df["Value"] = df["Qty"] * df["CMP"]
        df["P&L %"] = ((df["CMP"] - df["Avg"]) / df["Avg"]) * 100
        st.dataframe(df, use_container_width=True)

# ---------------- STOCK BASKETS ----------------
elif page == "Stock Baskets":
    st.title("🧺 Stock Basket Templates")

    for b in baskets:
        with st.expander(f"{b['name']} | Risk: {b['risk']}"):
            st.write("**Horizon:**", b["horizon"])
            df = pd.DataFrame(
                list(b["stocks"].items()),
                columns=["Stock", "Weight %"]
            )
            st.table(df)

# ---------------- DAILY REVIEW ----------------
elif page == "Daily Review":
    st.title("🔁 Daily Review")

    if st.session_state.portfolio.empty:
        st.warning("No portfolio data")
    else:
        df = st.session_state.portfolio.copy()
        df["P&L %"] = ((df["CMP"] - df["Avg"]) / df["Avg"]) * 100

        def action(pnl):
            if pnl > 20:
                return "Hold"
            if pnl < rules["avoid_averaging_loss_percent"]:
                return "❌ Avoid Averaging"
            if pnl < -15:
                return "⚠️ Review"
            return "Hold"

        df["Action"] = df["P&L %"].apply(action)
        st.dataframe(df[["Stock", "P&L %", "Action"]], use_container_width=True)

# ---------------- TOOLS ----------------
elif page == "Tools":
    st.title("🛠️ Tools")

    st.subheader("Average Price Calculator")
    q1 = st.number_input("Qty 1", 1)
    p1 = st.number_input("Price 1")
    q2 = st.number_input("Qty 2", 1)
    p2 = st.number_input("Price 2")

    if st.button("Calculate Average"):
        avg_price = (q1*p1 + q2*p2) / (q1+q2)
        st.success(f"New Average Price: ₹{avg_price:.2f}")

# ---------------- RULEBOOK ----------------
elif page == "Rulebook":
    st.title("📘 Investing Rulebook")

    for k, v in rules.items():
        st.write(f"• **{k.replace('_',' ').title()}** : {v}")

    st.info("Discipline beats emotions. Follow rules strictly.")

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("Personal investing tool • Not SEBI registered advice")
