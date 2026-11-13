import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import date
import io

st.set_page_config(page_title="NESCO Distributors - Business Dashboard", layout="wide", page_icon="🤎")

# --- PALETTE + HOVER GLOW ---
st.markdown("""
<style>
.stApp { background: #F7F1EB; }
h1,h2,h3 { color: #714329 !important; }
.blue-bar { background: #714329; color: #FFFFFF !important; padding: 13px 16px; border-radius: 12px; font-weight: 800; font-size: 18px; margin: 16px 0 10px 0; transition: all 0.3s ease; }
.blue-bar:hover { box-shadow: 0 8px 24px rgba(113,67,41,0.35); transform: translateY(-2px); }
.blue-bar * { color: white !important; }
.sub-bar { background: #B08463; color: white !important; padding: 10px 14px; border-radius: 10px; font-weight: 700; font-size: 15px; margin: 14px 0 8px 0; transition: all 0.3s ease; }
.sub-bar:hover { box-shadow: 0 8px 20px rgba(176,132,99,0.4); transform: translateY(-1px); }
.sub-bar * { color: white !important; }
.finance-box { background: #FFFFFF; border: 1.5px solid #B5A192; border-radius: 14px; padding: 14px; text-align: center; box-shadow: 0 2px 12px rgba(113,67,41,0.08); transition: all 0.3s ease; cursor: pointer; }
.finance-box:hover { border: 2.5px solid #714329 !important; box-shadow: 0 12px 28px rgba(113,67,41,0.30), 0 0 0 4px rgba(208,185,167,0.35) !important; transform: translateY(-4px) scale(1.03); background: #FFFEFD !important; backdrop-filter: blur(4px); }
.finance-box .label { color: #714329 !important; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; }
.finance-box .value { color: #714329 !important; font-size: 26px; font-weight: 900; }
.finance-box:hover .value { color: #B08463 !important; }
.info-box { background: #D0B9A7; border: 1px solid #B5A192; border-radius: 12px; padding: 14px 16px; color: #2B1A12 !important; transition: all 0.3s ease; cursor: pointer; }
.info-box:hover { border: 2px solid #714329 !important; box-shadow: 0 10px 24px rgba(113,67,41,0.25) !important; transform: translateY(-2px); backdrop-filter: blur(3px); background: #E8D9CC !important; }
.info-box * { color: #2B1A12 !important; }
.stButton>button { background: #714329 !important; color: white !important; font-weight: 800 !important; border-radius: 12px !important; border: none !important; transition: all 0.3s ease !important; }
.stButton>button:hover { background: #B08463 !important; box-shadow: 0 8px 20px rgba(113,67,41,0.35) !important; transform: translateY(-2px) scale(1.02) !important; border: 2px solid #714329 !important; }
.stDownloadButton>button { background: #B08463 !important; color: white !important; font-weight: 800 !important; border-radius: 12px !important; border: none !important; transition: all 0.3s ease !important; }
.stDownloadButton>button:hover { background: #714329 !important; box-shadow: 0 8px 20px rgba(113,67,41,0.35) !important; transform: translateY(-2px) scale(1.02) !important; }
section[data-testid="stSidebar"] { background: #714329 !important; }
section[data-testid="stSidebar"] * { color: white !important; }
section[data-testid="stSidebar"] button { background: #FFFFFF !important; color: #714329 !important; font-weight: 800 !important; border-radius: 10px !important; width: 100%; transition: all 0.3s ease !important; }
section[data-testid="stSidebar"] button:hover { background: #D0B9A7 !important; color: #714329 !important; box-shadow: 0 6px 18px rgba(0,0,0,0.25) !important; transform: translateX(4px) scale(1.02) !important; border: 2px solid #FFFFFF !important; }
section[data-testid="stSidebar"] .sidebar-title { color: #D0B9A7 !important; font-weight: 900; letter-spacing: 1px; font-size: 13px; margin: 18px 0 6px 0; }
.stTextInput input:hover, .stNumberInput input:hover { border-color: #714329 !important; box-shadow: 0 0 0 3px rgba(208,185,167,0.4) !important; }
</style>
""", unsafe_allow_html=True)

if "login" not in st.session_state: st.session_state.login = False
if not st.session_state.login:
    st.markdown("<div class='blue-bar' style='text-align:center'>🤎 NESCO - Private</div>", unsafe_allow_html=True)
    st.write("For authorized person only.")
    pw = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if pw == st.secrets.get("APP_PASSWORD", "Nesco123"):
            st.session_state.login = True; st.rerun()
        else: st.error("Wrong password!")
    st.stop()

@st.cache_resource
def get_db():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None
db = get_db()

def load(table):
    if db is None: return pd.DataFrame()
    try:
        res = db.table(table).select("*").order("id", desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def save(table, data):
    try: db.table(table).insert(data).execute(); return True
    except Exception as e: st.error(f"Error: {e}"); return False

def box(label, value):
    st.markdown(f"<div class='finance-box'><div class='label'>{label}</div><div class='value'>{value}</div></div>", unsafe_allow_html=True)
def bar(title): st.markdown(f"<div class='blue-bar'>{title}</div>", unsafe_allow_html=True)
def subbar(title): st.markdown(f"<div class='sub-bar'>{title}</div>", unsafe_allow_html=True)
def export_csv(df, filename):
    if df is not None and not df.empty:
        st.download_button("⬇️ Export CSV", df.to_csv(index=False), filename, "text/csv")
def legend_table(rows):
    df = pd.DataFrame(rows, columns=["Term", "What It Means"])
    st.dataframe(df, use_container_width=True, hide_index=True)

def download_full_excel(sales_df, purch_df, prods_df, exps_df, inv_df, wd_df, notes_df, recap_df, summary_dict):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dash = pd.DataFrame([
            ["OVERALL BUSINESS SUMMARY", "", ""],["Total Capital Invested", summary_dict["capital"], ""],["Total Revenue", summary_dict["revenue"], ""],["Gross Profit", summary_dict["gross_profit"], ""],["Gross Margin %", summary_dict["margin"], ""],["Total Purchase Cost", summary_dict["purchase_cost"], ""],["Total Expenses", summary_dict["expenses"], ""],["Cash Position", summary_dict["cash"], ""],["Current Stock Value", summary_dict["stock_value"], ""],["Total Outstanding (Debtors)", summary_dict["outstanding"], ""],["", "", ""],["CASH POSITION", "", ""],["Cash on Hand", summary_dict["cash"], ""],["Cash Collected (Received)", summary_dict["received"], ""],["Total Withdrawn", summary_dict["withdrawn"], ""],
        ], columns=["Metric", "Value (PKR)", "Notes"])
        dash.to_excel(writer, sheet_name="Dashboard", index=False)
        if recap_df is not None and not recap_df.empty:
            recap_df.to_excel(writer, sheet_name="Dashboard", index=False, startrow=len(dash)+3)
        notes_df.to_excel(writer, sheet_name="Notes", index=False)
        p = prods_df.copy()
        if not p.empty:
            p = p.rename(columns={"product":"Product Name","category":"Category","price":"Default Sale Rate (PKR)","notes":"Notes"})
            p = p[[c for c in ["Product Name","Category","Default Sale Rate (PKR)","Notes"] if c in p.columns]]
        p.to_excel(writer, sheet_name="Products", index=False)
        pu = purch_df.copy()
        if not pu.empty:
            pu = pu.rename(columns={"date":"Date","product":"Product","quantity":"Qty Purchased","cost":"Purchase Cost/Unit (PKR)","total":"Total Cost (PKR)","notes":"Notes"})
            pu = pu[[c for c in ["Date","Product","Qty Purchased","Purchase Cost/Unit (PKR)","Total Cost (PKR)","Notes"] if c in pu.columns]]
        pu.to_excel(writer, sheet_name="Purchases", index=False)
        s = sales_df.copy()
        if not s.empty:
            s = s.rename(columns={"date":"Date","product":"Product","customer":"Customer","quantity":"Qty Sold","effective_rate":"Sale Rate (PKR)","revenue":"Revenue (PKR)","avg_cost":"Avg Cost/Unit","cogs":"COGS (PKR)","profit":"Profit (PKR)","margin":"Margin %","received":"Amount Received","outstanding":"Amount Outstanding","payment_status":"Payment Status","discount":"Discount (PKR)","rate_override":"Rate Override"})
            cols = ["Date","Product","Customer","Qty Sold","Sale Rate (PKR)","Revenue (PKR)","Avg Cost/Unit","COGS (PKR)","Profit (PKR)","Margin %","Amount Received","Amount Outstanding","Payment Status","Discount (PKR)","Rate Override"]
            s = s[[c for c in cols if c in s.columns]]
        s.to_excel(writer, sheet_name="Sales", index=False)
        if recap_df is not None and not recap_df.empty:
            recap_df.to_excel(writer, sheet_name="Inventory Summary", index=False)
        e = exps_df.copy()
        if not e.empty:
            e = e.rename(columns={"date":"Date","expense":"Expense","amount":"Amount (PKR)","notes":"Notes"})
            e = e[[c for c in ["Date","Expense","Amount (PKR)","Notes"] if c in e.columns]]
        e.to_excel(writer, sheet_name="Expenses", index=False)
        iv = inv_df.copy()
        if not iv.empty:
            iv = iv.rename(columns={"owner":"Investor","amount":"Amount (PKR)","date":"Date","note":"Notes"})
            iv = iv[[c for c in ["Investor","Amount (PKR)","Date","Notes"] if c in iv.columns]]
        iv.to_excel(writer, sheet_name="Investment", index=False)
        w = wd_df.copy()
        if not w.empty:
            w = w.rename(columns={"date":"Date","person":"Withdrawn By","amount":"Amount (PKR)","note":"Notes"})
            w = w[[c for c in ["Date","Withdrawn By","Amount (PKR)","Notes"] if c in w.columns]]
        w.to_excel(writer, sheet_name="Withdrawals", index=False)
    output.seek(0)
    return output.getvalue()

def calc_avg_cost(purch):
    if purch.empty or "product" not in purch: return {}
    d = {}
    for prod, g in purch.groupby("product"):
        qty = pd.to_numeric(g["quantity"], errors="coerce").fillna(0).sum() if "quantity" in g else 0
        total = pd.to_numeric(g["total"], errors="coerce").fillna(0).sum() if "total" in g else 0
        d[prod] = (total / qty) if qty else 0
    return d

def calc_sales_enriched(sales, avg_map, prods):
    if sales.empty: return sales.copy()
    df = sales.copy()
    prod_rate = {}
    if not prods.empty and "product" in prods:
        for _, r in prods.iterrows():
            rate = r.get("price", r.get("default_sale_rate", 0))
            prod_rate[r["product"]] = float(rate) if pd.notna(rate) else 0
    for c in ["quantity","price","discount","rate_override","received"]:
        if c not in df: df[c] = 0
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0)
    df["rate_override"] = pd.to_numeric(df["rate_override"], errors="coerce").fillna(0)
    df["received"] = pd.to_numeric(df["received"], errors="coerce").fillna(0)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    def eff_rate(row):
        if row["rate_override"] and row["rate_override"] > 0: return row["rate_override"]
        if row["price"] and row["price"] > 0: return row["price"]
        return prod_rate.get(row.get("product",""), 0)
    df["effective_rate"] = df.apply(eff_rate, axis=1)
    df["avg_cost"] = df["product"].map(avg_map).fillna(0)
    df["revenue"] = df["quantity"] * df["effective_rate"] - df["discount"]
    df["total"] = df["revenue"]
    df["cogs"] = df["quantity"] * df["avg_cost"]
    df["profit"] = df["revenue"] - df["cogs"]
    df["margin"] = df.apply(lambda r: (r["profit"]/r["revenue"]*100) if r["revenue"] else 0, axis=1)
    df["outstanding"] = df["revenue"] - df["received"]
    df["payment_status"] = df.apply(lambda r: "Paid" if r["outstanding"] <= 0 else ("Partial" if r["received"]>0 else "Unpaid"), axis=1)
    return df

# --- SIDEBAR: DASHBOARD & NOTES AS 2 SEPARATE TITLES ---
if "menu" not in st.session_state: st.session_state.menu = "Dashboard"
st.sidebar.markdown("<div style='font-size:28px;font-weight:900'>🤎 NESCO</div><div style='font-size:14px;opacity:.9'>Distributors</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='sidebar-title'>DASHBOARD</div>", unsafe_allow_html=True)
if st.sidebar.button("📊 Dashboard"): st.session_state.menu = "Dashboard"; st.rerun()
st.sidebar.markdown("<div class='sidebar-title'>NOTES</div>", unsafe_allow_html=True)
if st.sidebar.button("📝 Notes & How-To Guide"): st.session_state.menu = "Notes"; st.rerun()
st.sidebar.markdown("<div class='sidebar-title'>SHEETS</div>", unsafe_allow_html=True)
for label, key in [("📦 Products","Products"),("🛒 Purchases","Purchases"),("🧾 Sales","Sales"),("📋 Inventory Summary","Inventory Summary"),("💸 Expenses","Expenses"),("💰 Investment","Investment"),("🏧 Withdrawals","Withdrawals"),("📤 Excel / CSV Upload","Excel Upload"),("💾 Auto-Save Excel","Auto-Save Excel")]:
    if st.sidebar.button(label): st.session_state.menu = key; st.rerun()
st.sidebar.markdown("---")
st.sidebar.success("Private Mode: ON 🔒")
if st.sidebar.button("Logout"): st.session_state.login = False; st.rerun()
menu = st.session_state.menu

sales_raw = load("sales"); purch = load("purchases"); prods = load("products")
exps = load("expenses"); inv = load("investment"); wd = load("withdrawals"); notes = load("notes")
avg_map = calc_avg_cost(purch)
sales = calc_sales_enriched(sales_raw, avg_map, prods)
total_inv_amt = pd.to_numeric(inv["amount"], errors="coerce").sum() if "amount" in inv and not inv.empty else 0
total_rev = sales["revenue"].sum() if "revenue" in sales and not sales.empty else 0
total_cogs = sales["cogs"].sum() if "cogs" in sales and not sales.empty else 0
gross_profit = total_rev - total_cogs
gross_margin = (gross_profit/total_rev*100) if total_rev else 0
total_purch_cost = pd.to_numeric(purch["total"], errors="coerce").sum() if "total" in purch and not purch.empty else 0
total_exp = pd.to_numeric(exps["amount"], errors="coerce").sum() if "amount" in exps and not exps.empty else 0
total_wd = pd.to_numeric(wd["amount"], errors="coerce").sum() if "amount" in wd and not wd.empty else 0
total_out = sales["outstanding"].sum() if "outstanding" in sales and not sales.empty else 0
total_received = sales["received"].sum() if "received" in sales and not sales.empty else 0
cash_on_hand = total_inv_amt + total_received - total_purch_cost - total_exp - total_wd
stock_value = 0
if not prods.empty:
    for _, pr in prods.iterrows():
        pname = pr["product"]
        pq = purch[purch["product"]==pname]["quantity"].sum() if not purch.empty and "product" in purch else 0
        sq = sales[sales["product"]==pname]["quantity"].sum() if not sales.empty and "product" in sales else 0
        stock_value += (pq - sq) * avg_map.get(pname, 0)
recap_df = pd.DataFrame()
if not sales.empty and "product" in sales:
    recap_df = sales.groupby("product").agg(Total_Revenue=("revenue","sum"), Total_Profit=("profit","sum"), Total_Qty_Sold=("quantity","sum")).reset_index()
    purch_g = purch.groupby("product").agg(Total_Qty_Purchased=("quantity","sum")).reset_index() if not purch.empty and "product" in purch else pd.DataFrame()
    recap_df = recap_df.merge(purch_g, on="product", how="left").fillna(0)
    recap_df["Remaining Stock"] = recap_df["Total_Qty_Purchased"] - recap_df["Total_Qty_Sold"]
    recap_df["Avg Cost/Unit"] = recap_df["product"].map(avg_map).fillna(0)
    recap_df["Remaining Value"] = recap_df["Remaining Stock"] * recap_df["Avg Cost/Unit"]
    recap_df["Margin %"] = recap_df.apply(lambda r: (r["Total_Profit"]/r["Total_Revenue"]*100) if r["Total_Revenue"] else 0, axis=1)
summary_dict = {"capital": total_inv_amt, "revenue": total_rev, "gross_profit": gross_profit, "margin": gross_margin, "purchase_cost": total_purch_cost, "expenses": total_exp, "cash": cash_on_hand, "stock_value": stock_value, "outstanding": total_out, "received": total_received, "withdrawn": total_wd}

# --- DASHBOARD ---
if menu == "Dashboard":
    bar("NESCO Distributors - Business Dashboard")
    st.markdown("<div class='info-box'><b>Dashboard:</b> Summary of your whole business. You do not type anything here. Everything comes automatically from Purchases, Sales, Expenses, Investment and Products.</div>", unsafe_allow_html=True)
    subbar("OVERALL BUSINESS SUMMARY")
    st.markdown("<div class='info-box'><b>What is this?</b> Total picture till today - capital, sales, profit, expenses, cash in hand, and what customers still owe you.</div>", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1: box("Total Capital Invested", f"Rs {total_inv_amt:,.0f}")
    with c2: box("Total Revenue", f"Rs {total_rev:,.0f}")
    with c3: box("Gross Profit", f"Rs {gross_profit:,.0f}")
    with c4: box("Gross Margin %", f"{gross_margin:.1f}%")
    c1,c2,c3,c4 = st.columns(4)
    with c1: box("Total Purchase Cost", f"Rs {total_purch_cost:,.0f}")
    with c2: box("Total Expenses", f"Rs {total_exp:,.0f}")
    with c3: box("Cash Position", f"Rs {cash_on_hand:,.0f}")
    with c4: box("Total Outstanding (Debtors)", f"Rs {total_out:,.0f}")
    subbar("CASH POSITION")
    st.markdown("<div class='info-box'><b>What is this?</b> Real cash in your hand / bank right now. Profit and Cash are NOT the same - Profit includes money customers still have to pay, Cash is only what you have actually received.</div>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1: box("Cash on Hand", f"Rs {cash_on_hand:,.0f}")
    with c2: box("Cash Collected (Received)", f"Rs {total_received:,.0f}")
    with c3: box("Total Withdrawn", f"Rs {total_wd:,.0f}")
    subbar("LATEST DAY SNAPSHOT / LAST 7 DAYS / MONTH TO DATE / YEAR TO DATE")
    st.markdown("<div class='info-box'><b>What is this?</b> How did you perform - Today, Last 7 Days, This Month, and This Year. Revenue = How much you sold, Profit = Revenue - COGS, Cash Collected = How much cash actually came in.</div>", unsafe_allow_html=True)
    if not sales.empty and "date" in sales:
        sales["date_parsed"] = pd.to_datetime(sales["date"], errors="coerce")
        today = sales["date_parsed"].max()
        latest = sales[sales["date_parsed"]==today]
        last7 = sales[sales["date_parsed"] >= today - pd.Timedelta(days=7)]
        mtd = sales[(sales["date_parsed"].dt.month==today.month) & (sales["date_parsed"].dt.year==today.year)]
        ytd = sales[sales["date_parsed"].dt.year==today.year]
        tdf = pd.DataFrame([
            ["Latest Day", today.date() if pd.notna(today) else "", f"{latest['revenue'].sum():,.0f}", f"{latest['profit'].sum():,.0f}", f"{latest['received'].sum():,.0f}"],
            ["Last 7 Days", "7 Days", f"{last7['revenue'].sum():,.0f}", f"{last7['profit'].sum():,.0f}", f"{last7['received'].sum():,.0f}"],
            ["Month to Date", today.strftime("%b %Y") if pd.notna(today) else "", f"{mtd['revenue'].sum():,.0f}", f"{mtd['profit'].sum():,.0f}", f"{mtd['received'].sum():,.0f}"],
            ["Year to Date", today.year if pd.notna(today) else "", f"{ytd['revenue'].sum():,.0f}", f"{ytd['profit'].sum():,.0f}", f"{ytd['received'].sum():,.0f}"],
        ], columns=["Period","Date","Revenue (PKR)","Profit (PKR)","Cash Collected (PKR)"])
        st.dataframe(tdf, use_container_width=True)
    subbar("PER PRODUCT RECAP")
    st.markdown("<div class='info-box'><b>What is this?</b> Product by product summary - Which product is giving you most profit, which product has most stock left, and what is the value of that remaining stock.</div>", unsafe_allow_html=True)
    if not recap_df.empty: st.dataframe(recap_df, use_container_width=True)
    bar("LEGEND & HOW THE CALCULATIONS WORK")
    st.markdown("<div class='info-box'><b>Blue Text</b> = Type your own data here (Purchases, Sales, Products, Expenses, Investment, Debtors sheets) | <b>Black Text</b> = Formula, calculating automatically - don't overwrite | <b>Green Text</b> = Pulled from another sheet</div>", unsafe_allow_html=True)
    legend_table([
        ["Weighted Avg Cost/Unit", "Total Purchase Cost / Total Qty Purchased - blends every batch of that product, old rate and new rate, into one average"],
        ["COGS (Cost of Goods Sold)", "Qty Sold x Weighted Avg Cost/Unit"],
        ["Gross Profit", "Revenue - COGS"],
        ["Gross Margin %", "Gross Profit / Revenue"],
        ["Remaining Stock", "Total Qty Purchased - Total Qty Sold"],
        ["Remaining Value", "Remaining Stock x Weighted Avg Cost/Unit"],
        ["Net Profit (After Expenses)", "Gross Profit - Total Expenses (Expenses sheet)"],
        ["Amount Outstanding (per sale)", "Revenue - Amount Received - this is what makes someone a debtor, does NOT reduce Profit or Revenue anywhere"],
        ["Total Outstanding (Debtors)", "Sum of every unpaid / partly-paid sale, plus anything logged on the Debtors sheet's own table"],
        ["Cash Basis Profit (Collected So Far)", "Net Profit (After Expenses) - Total Outstanding (Debtors) - an estimate of profit you've actually collected in cash"],
        ["Cash at Hand", "Total Capital Invested + Total Cash Collected - Total Purchase Cost - Total Expenses - actual money the business has right now, unlike Profit which counts credit sales too"],
        ["Last 7 Days / Month to Date / Year to Date", "Same Latest Revenue / Profit / Cash month on the rest of the sheet, just filtered to that date range - they move forward on their own as today's date changes"],
    ])
    bar("HOW TO USE - WITH YOUR OWN NUMBERS")
    st.markdown("<div class='info-box'>A full worked example with your own numbers, plus the daily routine, is in the Notes sheet.</div>", unsafe_allow_html=True)
    legend_table([
        ["How to add a new product", "Type its name in the Products sheet. A new row appears in Inventory Summary and Dashboard automatically (first 10 product slots are pre-built, extend the Inventory Summary table down for more)"],
        ["How to record a new purchase", "Add a row in the Purchases sheet (Date, Product, Qty, Rate) - even for a product you already stock, at a different rate. The weighted-average cost updates instantly everywhere."],
        ["How to record a sale", "Add a row in the Sales sheet (Date, Product, Customer, Qty, Revenue, cost, profit and margin) themselves in."],
        ["How to record a stock expense (transport, rent, wages, packing)", "Add a row in the Expenses sheet. It feeds Net Profit (After Expenses) on the Dashboard"],
        ["Deleting a row", "Just delete it from the table (right-click > Delete > Table Rows). Every total updates on its own - nothing to fix manually."],
        ["Total Withdrawal (Profit Kept Aside)", "Sum of everything on the Withdrawals sheet - money taken out of the business and not reinvested. Subtracted from Cash at Hand only. Profit and Margin figures are unaffected, since that money was still genuinely earned."],
        ["How to record a withdrawal", "Add a row in the Withdrawals sheet (Date, Amount, Notes) any time profit is taken out of the business rather than reinvested. It reduces Cash at Hand immediately - it does not touch Profit."],
    ])

elif menu == "Notes":
    bar("Notes & How-To Guide")
    st.markdown("<div class='info-box'><b>Read this once</b> - it explains exactly how every number in the workbook is calculated, and what to do daily.</div>", unsafe_allow_html=True)
    st.subheader("Add Entry - New Note")
    with st.form("add_note"):
        c1,c2 = st.columns(2)
        d = c1.date_input("Note Date", value=date.today()); t = c2.text_input("Title")
        n = st.text_area("Note")
        if st.form_submit_button("Save Note"):
            if save("notes", {"date": str(d), "title": t, "note": n}): st.success("Saved! Dashboard auto-updated."); st.rerun()
    if not notes.empty: st.dataframe(notes, use_container_width=True); export_csv(notes, "notes.csv")

    bar("WORKBOOK MAP")
    legend_table([
        ["Dashboard", "Summary of the whole business, updates automatically"],
        ["Notes", "How-to guide and worked examples"],
        ["Products", "Master list of everything you stock. Add a new product first, before it appears anywhere else"],
        ["Purchases", "Every purchase batch you make, one row each - including repeat purchases of the same product at a new rate"],
        ["Sales", "Every sale you make, one row each - customer, qty, rate, revenue, cost, profit"],
        ["Inventory Summary", "Automatic roll-up per product: stock on hand, average cost, revenue, profit"],
        ["Expenses", "General business costs that are NOT the cost of the goods themselves (transport, rent, wages, packing, etc.)"],
        ["Investment", "Capital put into the business by owners / partners"],
        ["Debtors", "Money customers owe you (they took product on credit and haven't paid in full). The top line total updates itself from the Sales sheet"],
    ])
    bar("YOUR DAILY ROUTINE")
    legend_table([
        ["1. Bought stock today?", "Go to Purchases, add one row: Date, Product (from the dropdown), Qty, Rate. Total Cost fills itself in."],
        ["2. Sold something today?", "Go to Sales, add one row: Date, Product, Customer (optional), Qty, Rate. Revenue, Avg Cost, COGS, Profit and Margin all fill themselves in."],
        ["3. Spent money on something that is NOT stock - transport, rent, wages, packing?", "Go to Expenses, add one row."],
        ["4. Check", "Inventory Summary and the Dashboard update instantly - there is nothing else to touch."],
    ])
    bar("HOW THE WEIGHTED AVERAGE COST WORKS - A WORKED EXAMPLE")
    st.markdown("<div class='info-box'>Suppose you first buy 40 units of a product at 1,450 each. Then later buy 30 more at a discounted 1,440 each. Instead of tracking two separate prices, this workbook blends them into a single average cost per unit, weighted by how many units came at each price.<br><br><b>Step 1 - Total cost:</b> (40 x 1,450) + (30 x 1,440) = 58,000 + 43,200 = 101,200 PKR<br><b>Step 2 - Total units:</b> 40 + 30 = 70 units<br><b>Step 3 - Average cost:</b> 101,200 / 70 = 1,445.71 PKR per unit<br><br>This is exactly what already happened automatically in your Purchases and Inventory Summary sheets. To see the average for any specific product, on the Purchases sheet, click the small filter arrow on the Product column header - it is already there - the sheet is filtered.</div>", unsafe_allow_html=True)
    bar("HOW EACH NUMBER IS CALCULATED")
    legend_table([
        ["Weighted Avg Cost / Unit", "Total Purchase Cost / Total Qty Purchased for that product (Purchases sheet) - blends every batch"],
        ["COGS (Cost of Goods Sold)", "Qty Sold x Weighted Avg Cost/Unit - uses the current blended average, the same for every sale of that product"],
        ["Revenue", "Qty Sold x Sale Rate - Discount. Sale Rate = Rate Override if given, otherwise Default Sale Rate"],
        ["Gross Profit", "Revenue - COGS"],
        ["Gross Margin %", "Gross Profit / Revenue x 100"],
        ["Remaining Stock", "Total Qty Purchased - Total Qty Sold (Sales sheet)"],
        ["Remaining Value", "Remaining Stock x Weighted Avg Cost/Unit"],
        ["Net Profit (After Expenses)", "Gross Profit - Total Expenses (Expenses sheet)"],
        ["Total Outstanding (Debtors)", "Sum of every unpaid / partly-paid sale - Revenue - Amount Received"],
        ["Cash Basis Profit (Collected So Far)", "Net Profit (After Expenses) - Total Outstanding (Debtors)"],
        ["Cash at Hand", "Total Capital Invested + Total Cash Collected - Total Purchase Cost - Total Expenses - Total Withdrawals"],
    ])
    bar("ADDING A NEW PRODUCT")
    st.markdown("<div class='info-box'>Type its name (and optionally category / default sale rate) into the Products sheet. A new row appears in Inventory Summary and the Dashboard automatically. First 10 product slots are pre-built. Need more? Just select the last row of the Inventory Summary table, drag the small fill-handle at its bottom-right corner down, and the formulas copy themselves down.</div>", unsafe_allow_html=True)
    bar("DELETING SOMETHING")
    st.markdown("<div class='info-box'>Just delete the row inside any table (Purchases, Sales, Products, Expenses, Investment, Debtors) and choose Delete &gt; Table Rows. Every total, average, and profit figure updates on its own - there is nothing to fix manually afterwards.</div>", unsafe_allow_html=True)
    bar("DEBTORS - WHEN SOMEONE TAKES PRODUCT AND HASN'T PAID")
    st.markdown("<div class='info-box'>When you record a sale, the Amount Received (PKR) column defaults to the full amount (assumes paid in full) the moment you fill in Qty and Rate. If the customer pays less, just type what they actually paid. The rest becomes Amount Outstanding (what is still owed on that sale) and Payment Status (Paid / Partially Paid / Unpaid) - the last two columns on the Sales sheet update themselves. The Debtors sheet totals all outstanding amounts automatically - that is your who-owes-me-money figure. There is also a manual table on the Debtors sheet if you want to log anything extra.<br><br><b>Important - this does NOT reduce Gross Profit, Revenue, or Margin anywhere in this workbook.</b> Standard accounting counts a sale as revenue and profit the moment the goods leave your hands, whether or not the cash has arrived yet - that is why Inventory Summary and the Dashboard's profit figures stay the same regardless of who has and hasn't paid. What outstanding debtors DOES affect is how much of that profit is actually sitting in your pocket right now. That is why the Dashboard has a separate Cash-Basis Profit (Collected So Far) card - it is Net Profit (After Expenses) minus everything still outstanding. Both numbers are useful for different questions: Net Profit tells you if the business is profitable; Cash-Basis Profit tells you how much of that you can actually spend right now.</div>", unsafe_allow_html=True)
    bar("CASH AT HAND - HOW IT'S DIFFERENT FROM PROFIT")
    st.markdown("<div class='info-box'>Profit counts a sale the moment it happens, even if the customer hasn't paid yet. Cash at Hand counts only money that has actually arrived. That is why the two are different.<br><br><b>Quick check built into the workbook:</b> Cash at Hand + Current Stock Value should equal Total Capital Invested + Net Profit (After Expenses) - Total Withdrawals. If you ever want to check, add up those figures from the Dashboard.</div>", unsafe_allow_html=True)
    bar("LAST 7 DAYS / MONTH TO DATE / YEAR TO DATE")
    st.markdown("<div class='info-box'>These sections on the Dashboard total your Units Sold, Revenue, Profit and Cash Collected over rolling and calendar windows, all anchored to today's date. Last 7 Days = Today and the 6 days before it. Month to Date = The 1st of this month through Today. Year to Date = Jan 1st through Today. As you keep adding rows to Sales day after day, these figures widen and shift forward automatically, and they'll be accurate again the next time you open the file, whatever today's date is by then.</div>", unsafe_allow_html=True)
    bar("A NOTE ON THE 1,000 PKR EXPENSE FROM YOUR OLD FILE")
    st.markdown("<div class='info-box'>You had one line '1,000 PKR Expense' - figure wasn't linked to any product / COGS since it wasn't the cost of the goods themselves (most likely Transport, Rent, Wages or Packing). It now lives on the Expenses sheet as a general business cost, and it feeds Net Profit (After Expenses) on the Dashboard - kept separate from product cost / COGS. Add more rows there as you spend, and rename this one once you recall exactly what it was for.</div>", unsafe_allow_html=True)
    bar("WITHDRAWALS - WHEN YOU TAKE PROFIT OUT OF THE BUSINESS")
    st.markdown("<div class='info-box'>It subtracts from Cash at Hand on the Dashboard right away, since that money has physically left the business. It does NOT reduce Gross Profit, Net Profit, or Margin % anywhere - the business still earned that money; you've just moved it out.<br><br><b>To record a withdrawal:</b> Add a row in the Withdrawals sheet (Date, Amount, Notes) any time profit is taken out of the business rather than reinvested. It reduces Cash at Hand immediately.</div>", unsafe_allow_html=True)
    bar("DISCOUNTS / SHORT CHANGE (added)")
    st.markdown("<div class='info-box'>New Discount (PKR) column on the Sales sheet (last column). Use it when a customer is short on change and you let a small amount go (e.g. 5 or 10 PKR). Type the amount forgiven there. Revenue is reduced: Qty x Sale Rate MINUS Discount, so Profit, Margin, Amount Outstanding and the Dashboard all update. Enter the actual cash received in Amount Received. With the discount recorded, the sale still shows as Fully Paid instead of leaving a tiny fake balance in Debtors. Default 0 (no discount) on every row, so all existing figures are unchanged.</div>", unsafe_allow_html=True)
    bar("SALE RATE FIX (corrected)")
    st.markdown("<div class='info-box'>Previously 'Default Sale Rate' for Sugar and Olpers Big had been set to a purchase-level rate (950 and 2360). They are now the real selling prices (1000 and 2500). Any Sales row that auto-pulls the default rate (rather than a typed rate) now uses the correct selling price instead of showing a near-zero or negative profit.</div>", unsafe_allow_html=True)
    bar("SALE RATE - NOW AUTO-FETCHES (set the price once)")
    st.markdown("<div class='info-box'>Set each product's selling price ONCE in the Products sheet, in the 'Default Sale Rate (PKR)' column. From that price, the Sales sheet fills itself in. On the Sales sheet, just pick the product from the dropdown - the Sale Rate fills automatically from the Products sheet. Add a new sale row and it fills itself in too.<br><br>Sold something at a special one-off price? Type that price in the new Rate Override (PKR) column on that row. Leave it blank the rest of the time. This is safer than typing directly over the Sale Rate. The rate stays linked to the Products sheet, so change the price there once and every future sale follows. To change the price for an existing product? Just update the Products sheet, no need to change old sales.</div>", unsafe_allow_html=True)
    bar("NEW SALE ROWS NOW FILL THEMSELVES IN")
    st.markdown("<div class='info-box'>The Sales sheet is pre-built down to row 200. To log a sale, just fill Date, Product (dropdown), Customer, Qty and Amount Received on the next empty row. Sale Rate, Revenue, Avg Cost, COGS, Profit, Margin, Outstanding and Payment Status all calculate the moment you pick the product and enter the quantity. Use Discount (PKR) for any amount you forgive, use Rate Override (PKR) only for a one-off special price. Both stay blank normally.</div>", unsafe_allow_html=True)
    bar("PURCHASES - DEFAULT SALE RATE SHOWN NEXT TO PURCHASE RATE")
    st.markdown("<div class='info-box'>The Purchases sheet now has a 'Default Sale Rate (PKR)' column right after 'Purchase Rate (PKR)'. It pulls each product's selling price from the Products sheet. It is there purely for reference while you enter a purchase - so you can see your margin at a glance (e.g. buying Sugar at 7000 when the sale rate is also 7000). It is there purely for reference while you enter a purchase.</div>", unsafe_allow_html=True)

elif menu == "Products":
    bar("Products")
    st.markdown("<div class='info-box'>Master product list - add a new row first when stocking a new product. Default Sale Rate is the normal selling price. If you sell at a different price for one customer, use Rate Override in Sales.</div>", unsafe_allow_html=True)
    st.subheader("Add Entry - New Product")
    with st.form("add_prod"):
        c1,c2,c3 = st.columns(3)
        p = c1.text_input("Product Name"); cat = c2.text_input("Category"); rate = c3.number_input("Default Sale Rate (PKR)", min_value=0.0)
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Product"):
            if save("products", {"product": p, "category": cat, "price": rate, "notes": nt}): st.success("Saved!"); st.rerun()
    st.subheader("All Products")
    st.dataframe(prods, use_container_width=True); export_csv(prods, "products.csv")
    bar("HOW TO USE - PRODUCTS")
    legend_table([["Default Sale Rate", "Normal selling price for this product. Sales will use this unless Rate Override is given."],["Category", "For your own grouping - e.g. Milk / Carton, Biscuit, etc."]])

elif menu == "Purchases":
    bar("Purchases")
    st.markdown("<div class='info-box'>One row per purchase batch. Buying the same product again at a new cost - just add another row. Average recalculates automatically.</div>", unsafe_allow_html=True)
    st.subheader("Add Entry - New Purchase")
    with st.form("add_p"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date", value=date.today()); prod = c2.text_input("Product"); qty = c3.number_input("Qty Purchased", min_value=1, value=1)
        cost = c1.number_input("Purchase Cost/Unit (PKR)", min_value=0.0); nt = c2.text_input("Notes")
        if st.form_submit_button("Save Purchase"):
            if save("purchases", {"date": str(d), "product": prod, "quantity": qty, "cost": cost, "total": qty*cost, "notes": nt}): st.success("Saved!"); st.rerun()
    st.subheader("All Purchases")
    st.dataframe(purch, use_container_width=True); export_csv(purch, "purchases.csv")
    bar("HOW TO USE - PURCHASES")
    legend_table([["Total Cost (PKR)", "Qty Purchased x Purchase Cost/Unit - calculates automatically."],["Weighted Avg Cost", "Total Purchase Cost / Total Qty Purchased. New batch at new cost changes the average for all future sales."]])

elif menu == "Sales":
    bar("Sales")
    st.markdown("<div class='info-box'>One row per sale. Avg Cost, COGS, Profit and Margin calculate automatically - and so does the total when you enter Amount Received / Outstanding. Discount and Rate Override are at the last - they change Revenue.</div>", unsafe_allow_html=True)
    st.subheader("Add Entry - New Sale")
    with st.form("add_sale"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date", value=date.today()); prod = c2.text_input("Product"); cust = c3.text_input("Customer")
        qty = c1.number_input("Qty Sold", min_value=1, value=1)
        rate = c2.number_input("Sale Rate (PKR) - leave empty to use Default", min_value=0.0)
        disc = c3.number_input("Discount (PKR)", min_value=0.0)
        override = c1.number_input("Rate Override - if special rate for this sale", min_value=0.0)
        recv = c2.number_input("Amount Received", min_value=0.0)
        if st.form_submit_button("Save Sale"):
            if save("sales", {"date": str(d), "product": prod, "customer": cust, "quantity": qty, "price": rate, "discount": disc, "rate_override": override if override>0 else None, "received": recv}):
                st.success("Saved!"); st.rerun()
    st.subheader("All Sales")
    show_cols = ["date","product","customer","quantity","effective_rate","revenue","avg_cost","cogs","profit","margin","received","outstanding","payment_status","discount","rate_override"]
    disp = sales.copy()
    rename = {"date":"Date","product":"Product","customer":"Customer","quantity":"Qty Sold","effective_rate":"Sale Rate (PKR)","revenue":"Revenue (PKR)","avg_cost":"Avg Cost/Unit","cogs":"COGS (PKR)","profit":"Profit (PKR)","margin":"Margin %","received":"Amount Received","outstanding":"Amount Outstanding","payment_status":"Payment Status","discount":"Discount (PKR)","rate_override":"Rate Override"}
    disp = disp[[c for c in show_cols if c in disp.columns]].rename(columns=rename)
    st.dataframe(disp, use_container_width=True); export_csv(disp, "sales.csv")
    if not disp.empty:
        st.plotly_chart(px.bar(sales, x="product", y="revenue", title="Revenue by Product", color_discrete_sequence=["#714329","#B08463","#B9937B"]), use_container_width=True)
    bar("HOW TO USE - SALES")
    legend_table([
        ["Sale Rate (PKR)", "Final rate used. If Rate Override is given, it is used. Otherwise Sale Rate, otherwise Products Default Sale Rate."],
        ["Discount (PKR)", "Amount less taken from customer. Revenue = (Qty x Final Rate) - Discount."],
        ["Rate Override", "Special price for this one sale only. Does NOT change Products Default Sale Rate."],
        ["Amount Received", "Cash actually received now. Rest becomes Amount Outstanding."],
        ["Amount Outstanding", "Revenue - Amount Received. Money still to collect."],
        ["Payment Status", "Paid if Outstanding = 0, Partial if some received, Unpaid if nothing received."],
    ])

elif menu == "Inventory Summary":
    bar("Inventory Summary")
    st.markdown("<div class='info-box'>One row per product, pulled from Purchases and Sales. Nothing here to type - add a product in the Products sheet and it appears here automatically.</div>", unsafe_allow_html=True)
    if not prods.empty:
        rows=[]
        for _, pr in prods.iterrows():
            pname = pr["product"]
            pq = purch[purch["product"]==pname]["quantity"].sum() if not purch.empty and "product" in purch else 0
            sq = sales[sales["product"]==pname]["quantity"].sum() if not sales.empty and "product" in sales else 0
            avgc = avg_map.get(pname, 0); rem = pq - sq
            rev = sales[sales["product"]==pname]["revenue"].sum() if not sales.empty else 0
            prof = sales[sales["product"]==pname]["profit"].sum() if not sales.empty else 0
            rows.append({"Product": pname, "Total Qty Purchased": pq, "Total Qty Sold": sq, "Remaining Stock": rem, "Avg Cost/Unit": round(avgc,2), "Remaining Value": round(rem*avgc,2), "Total Revenue": round(rev,2), "Total Profit": round(prof,2), "Margin %": round((prof/rev*100) if rev else 0,2)})
        idf = pd.DataFrame(rows)
        st.dataframe(idf, use_container_width=True); export_csv(idf, "inventory_summary.csv")
    else: st.info("No product yet.")
    bar("HOW TO USE - INVENTORY SUMMARY")
    legend_table([["Remaining Stock", "Total Qty Purchased - Total Qty Sold."],["Remaining Value", "Remaining Stock x Avg Cost/Unit."],["Do Not Type Here", "This sheet is formula only. Type in Products, Purchases and Sales."]])

elif menu == "Expenses":
    bar("Expenses")
    st.markdown("<div class='info-box'>Operating costs - transport, rent, wages, etc. These are NOT part of Purchase Cost.</div>", unsafe_allow_html=True)
    st.subheader("Add Entry - New Expense")
    with st.form("add_exp"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date", value=date.today()); e = c2.text_input("Expense"); a = c3.number_input("Amount (PKR)", min_value=0.0)
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Expense"):
            if save("expenses", {"date": str(d), "expense": e, "amount": a, "notes": nt}): st.success("Saved!"); st.rerun()
    st.subheader("All Expenses")
    st.dataframe(exps, use_container_width=True); export_csv(exps, "expenses.csv")
    bar("HOW TO USE - EXPENSES")
    legend_table([["Expense", "Any business cost other than buying stock - e.g. Rent, Transport, Wages."],["Total Expenses", "Reduces Cash at Hand. Does NOT change COGS or Gross Profit directly."]])

elif menu == "Investment":
    bar("Investment")
    st.markdown("<div class='info-box'>Capital put into the business by each owner / partner.</div>", unsafe_allow_html=True)
    st.subheader("Add Entry - New Investment")
    with st.form("add_inv"):
        c1,c2,c3 = st.columns(3)
        o = c1.text_input("Investor"); a = c2.number_input("Amount (PKR)", min_value=0.0); d = c3.date_input("Date", value=date.today())
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Investment"):
            if save("investment", {"owner": o, "amount": a, "date": str(d), "note": nt}): st.success("Saved!"); st.rerun()
    st.subheader("All Investment")
    st.dataframe(inv, use_container_width=True); export_csv(inv, "investment.csv")
    st.metric("Total Capital Invested", f"Rs {total_inv_amt:,.0f}")
    bar("HOW TO USE - INVESTMENT")
    legend_table([["Total Capital Invested", "Sum of all Investment. Starting money for the business. Increases Cash at Hand."]])

elif menu == "Withdrawals":
    bar("Withdrawals")
    st.markdown("<div class='info-box'>Profit taken out of the business for personal use - not an expense.</div>", unsafe_allow_html=True)
    st.subheader("Add Entry - New Withdrawal")
    with st.form("add_wd"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date", value=date.today()); p = c2.text_input("Withdrawn By"); a = c3.number_input("Amount (PKR)", min_value=0.0)
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Withdrawal"):
            if save("withdrawals", {"date": str(d), "person": p, "amount": a, "note": nt}): st.success("Saved!"); st.rerun()
    st.subheader("All Withdrawals")
    st.dataframe(wd, use_container_width=True); export_csv(wd, "withdrawals.csv")
    st.metric("Total Withdrawn", f"Rs {total_wd:,.0f}")
    bar("HOW TO USE - WITHDRAWALS")
    legend_table([["Total Withdrawn", "Profit taken home. Reduces Cash at Hand. NOT an expense, does NOT reduce Gross Profit."]])

elif menu == "Excel Upload":
    bar("Excel / CSV Upload - Data Directly From Excel To Website")
    st.markdown("<div class='info-box'>Upload your Excel / CSV sheet. Headings must match the website headings. Data goes directly to Supabase and Dashboard auto-updates.</div>", unsafe_allow_html=True)
    table = st.selectbox("Which Sheet To Upload To?", ["products","purchases","sales","expenses","investment","withdrawals","notes"])
    st.code({"products": "Product Name, Category, Default Sale Rate (PKR), Notes","purchases": "Date, Product, Qty Purchased, Purchase Cost/Unit (PKR), Notes","sales": "Date, Product, Customer, Qty Sold, Sale Rate (PKR), Discount (PKR), Rate Override, Amount Received","expenses": "Date, Expense, Amount (PKR), Notes","investment": "Investor, Amount (PKR), Date, Notes","withdrawals": "Date, Withdrawn By, Amount (PKR), Notes","notes": "Date, Title, Note"}[table])
    file = st.file_uploader("Drag & Drop Excel / CSV Here", type=["xlsx","csv"])
    if file is not None:
        try:
            df = pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file)
            st.write("Original Headings:", list(df.columns))
            mapping = {"product name":"product","product":"product","category":"category","default sale rate (pkr)":"price","default sale rate":"price","sale rate (pkr)":"price","sale rate":"price","price":"price","date":"date","qty purchased":"quantity","qty sold":"quantity","qty":"quantity","quantity":"quantity","purchase cost/unit (pkr)":"cost","purchase cost":"cost","cost":"cost","customer":"customer","amount received":"received","received":"received","discount (pkr)":"discount","discount":"discount","rate override":"rate_override","expense":"expense","amount (pkr)":"amount","amount":"amount","investor":"owner","owner":"owner","withdrawn by":"person","person":"person","title":"title","note":"note","notes":"notes"}
            df.columns = [mapping.get(str(c).strip().lower(), str(c).strip().lower()) for c in df.columns]
            st.write("Mapped Headings:", list(df.columns)); st.dataframe(df)
            if st.button("Save To Supabase - Auto-Save"):
                if table=="purchases" and "quantity" in df.columns and "cost" in df.columns:
                    df["total"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0) * pd.to_numeric(df["cost"], errors="coerce").fillna(0)
                for _, row in df.iterrows():
                    d = {k:(None if pd.isna(v) else v) for k,v in row.to_dict().items()}
                    if "date" in d and d["date"] is not None:
                        try: d["date"] = str(pd.to_datetime(d["date"]).date())
                        except: pass
                    db.table(table).insert(d).execute()
                st.success("All saved! Dashboard auto-updated."); st.rerun()
        except Exception as e: st.error(f"Excel Error: {e}")
    st.markdown("---")
    st.subheader("Quick Add Entry - Without Excel")
    st.write("If you don't have Excel ready, use Add Entry form on each sheet.")

elif menu == "Auto-Save Excel":
    bar("Auto-Save Excel - Download Full Workbook Like Your Original Excel")
    st.markdown("<div class='info-box'><b>How Auto-Save Works:</b> 1. You add entries or upload CSV - data auto-saves to Supabase. 2. Dashboard auto-updates. 3. Click below to download the full Excel file - it is generated automatically from live data, with the same sheets and same headings as your original Excel. Save that file on your laptop as backup.</div>", unsafe_allow_html=True)
    st.write("This file will contain: Dashboard + Notes + Products + Purchases + Sales + Inventory Summary + Expenses + Investment + Withdrawals")
    if st.button("🔄 Generate & Auto-Save Excel Now"):
        excel_bytes = download_full_excel(sales, purch, prods, exps, inv, wd, notes, recap_df, summary_dict)
        st.download_button("⬇️ Download NESCO-Full-Workbook.xlsx", excel_bytes, "NESCO-Full-Workbook.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.success("Excel generated from live data - same headings as your original Excel!")
    st.markdown("---")
    st.subheader("Auto-Save Status")
    st.write(f"✅ Products: {len(prods)} rows | Purchases: {len(purch)} rows | Sales: {len(sales)} rows | Expenses: {len(exps)} rows | Investment: {len(inv)} rows | Withdrawals: {len(wd)} rows")
    st.write("Every new entry is auto-saved instantly. No need to press Save in Excel.")
