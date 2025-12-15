import streamlit as st
import pandas as pd
import yfinance as yf
import json
import numpy as np
from datetime import datetime

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config("Long-Term Investing", layout="wide")

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
@st.cache_data
def load_json(file):
    return json.load(open(file))

baskets = load_json("baskets.json")
rules = load_json("rules.json")
notes = load_json("notes.json")

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(
        columns=["Stock", "Qty", "Avg"]
    )

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
@st.cache_data(ttl=60)
def get_ltp(symbol):
    try:
        return yf.Ticker(symbol).history(period="1d")["Close"].iloc[-1]
    except:
        return np.nan

def calculate_metrics(df):
    df["CMP"] = df["Stock"].apply(get_ltp)
    df["Value"] = df["Qty"] * df["CMP"]
    df["P&L %"] = ((df["CMP"] - df["Avg"]) / df["Avg"]) * 100
    return df

def review_action(pnl):
    if pnl >= rules["profit_booking_percent"]:
        return "💰 Consider Profit Booking"
    if pnl <= rules["avoid_averaging_percent"]:
        return "❌ Avoid Averaging"
    if pnl <= rules["review_loss_percent"]:
        return "⚠️ Review"
    return "Hold"

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Portfolio", "Import CSV", "Baskets", "Rebalancer", "Daily Review", "Notes", "Rulebook"]
)

# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
if page == "Dashboard":
    st.title("🏠 Investing Dashboard")

    if st.session_state.portfolio.empty:
        st.info("No holdings added yet")
    else:
        df = calculate_metrics(st.session_state.portfolio.copy())
        total = df["Value"].sum()
        pnl = (df["Value"].sum() - (df["Qty"]*df["Avg"]).sum()) / (df["Qty"]*df["Avg"]).sum() * 100

        col1, col2, col3 = st.columns(3)
        col1.metric("Portfolio Value", f"₹{total:,.0f}")
        col2.metric("Overall P&L %", f"{pnl:.2f}%")
        col3.metric("Stocks Held", len(df))

# -------------------------------------------------
# PORTFOLIO
# -------------------------------------------------
elif page == "Portfolio":
    st.title("📈 My Portfolio")

    with st.form("add"):
        c1, c2, c3 = st.columns(3)
        stock = c1.text_input("Stock (Yahoo format)")
        qty = c2.number_input("Qty", 1)
        avg = c3.number_input("Avg Price", 0.0)
        submit = st.form_submit_button("Save")

        if submit:
            df = st.session_state.portfolio
            df = df[df["Stock"] != stock]
            df.loc[len(df)] = [stock, qty, avg]
            st.session_state.portfolio = df
            st.success("Saved")

    if not st.session_state.portfolio.empty:
        df = calculate_metrics(st.session_state.portfolio.copy())
        st.dataframe(df, use_container_width=True)

# -------------------------------------------------
# CSV IMPORT
# -------------------------------------------------
elif page == "Import CSV":
    st.title("📂 Import Holdings CSV")

    file = st.file_uploader("Upload CSV (Stock,Qty,Avg)")
    if file:
        df = pd.read_csv(file)
        st.session_state.portfolio = df
        st.success("Portfolio imported")

# -------------------------------------------------
# BASKETS
# -------------------------------------------------
elif page == "Baskets":
    st.title("🧺 Stock Basket Templates")

    for b in baskets:
        with st.expander(b["name"]):
            st.write("Risk:", b["risk"])
            st.write("Horizon:", b["horizon"])
            st.table(pd.DataFrame(b["stocks"].items(), columns=["Stock", "Weight %"]))

# -------------------------------------------------
# REBALANCER
# -------------------------------------------------
elif page == "Rebalancer":
    st.title("⚖️ Basket Rebalancer")

    total_capital = st.number_input("Total Capital ₹", 10000)
    basket = st.selectbox("Select Basket", [b["name"] for b in baskets])

    b = next(x for x in baskets if x["name"] == basket)
    rows = []

    for stock, w in b["stocks"].items():
        cmp = get_ltp(stock)
        allocation = total_capital * w / 100
        qty = allocation / cmp if cmp else 0
        rows.append([stock, w, round(cmp,2), int(qty)])

    st.table(pd.DataFrame(rows, columns=["Stock","Weight %","CMP","Ideal Qty"]))

# -------------------------------------------------
# DAILY REVIEW
# -------------------------------------------------
elif page == "Daily Review":
    st.title("🔁 Daily / Quarterly Review")

    if st.session_state.portfolio.empty:
        st.warning("No holdings")
    else:
        df = calculate_metrics(st.session_state.portfolio.copy())
        df["Action"] = df["P&L %"].apply(review_action)
        st.dataframe(df[["Stock","P&L %","Action"]], use_container_width=True)

# -------------------------------------------------
# NOTES
# -------------------------------------------------
elif page == "Notes":
    st.title("🧠 Stock Notes")

    stock = st.text_input("Stock")
    note = st.text_area("Your Notes")

    if st.button("Save Note"):
        notes[stock] = {
            "note": note,
            "updated": str(datetime.now())
        }
        json.dump(notes, open("notes.json","w"), indent=2)
        st.success("Saved")

    if notes:
        st.subheader("Saved Notes")
        for k,v in notes.items():
            st.markdown(f"**{k}** — {v['note']}")

# -------------------------------------------------
# RULEBOOK
# -------------------------------------------------
elif page == "Rulebook":
    st.title("📘 Investing Rulebook")
    for k,v in rules.items():
        st.write(f"• **{k.replace('_',' ').title()}** : {v}")

st.caption("Personal use only • Discipline > Emotions")
