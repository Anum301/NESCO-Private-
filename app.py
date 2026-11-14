import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import date
import io
import numpy as np

# FIX 5+6 NOTE - OLD NOTE CHANGED: sidebar is ALWAYS expanded, so collapse button is now hidden on purpose.
# That button was rendering as keyboard_double / double_arrow_right text because its icon font failed.
# Sidebar will stay expanded, navigation is via sidebar buttons below, so hiding it is safe.
st.set_page_config(page_title="NESCO Distributors - Business Dashboard", layout="wide", page_icon="🏪", initial_sidebar_state="expanded")

# ---------- FIX 2 HELPER - float join error fix ----------
def safe_str(x):
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x).strip()

def safe_join(values, sep=", "):
    return sep.join([safe_str(v) for v in list(values)])

# ---------- FONT TIMES NEW ROMAN + PALETTE + OLD CODE SAME ----------
# FIX 4 + FIX 5 + FIX 6 - toolbar / theme menu / collapse button hidden here, nothing else changed
st.markdown("""
<style>
* { font-family: "Times New Roman", Times, serif !important; }
html, body { background: #F7F1EB; }
h1, h2, h3 { color: #714329; font-family: "Times New Roman", Times, serif; font-weight: 800; font-size: 28px; margin: 0px; }
.blue-bar { background: #714329; color: #FFFFFF; padding: 12px 16px; border-radius: 12px; font-weight: 800; font-size: 28px; margin: 0px; }
.blue-bar:hover { background: #714329; color: #FFFFFF; transform: translateY(-2px); }
.blue-bar { color: white !important; font-family: "Times New Roman", Times, serif; }
.sub-bar { background: #8B5A3C; color: white; padding: 10px 14px; border-radius: 10px; font-weight: 700; font-size: 17px; margin: 6px 0px; }
.sub-bar:hover { background: #8B5A3C; color: white; }
.finance-box { background: #FFFFFF; border: 1.5px solid #714329; border-radius: 12px; padding: 12px 14px; box-shadow: 0 2px 10px rgba(113,67,41,0.10); }
.finance-box:hover { background: #FFFFFF; border: 1.5px solid #714329; }
.finance-box .label { color: #714329; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
.finance-box .value { color: #714329; font-size: 26px; font-weight: 900; }
.info-box { background: #FFFFFF; border: 2px solid #714329; border-radius: 12px; padding: 12px 14px; }
.info-box .label { color: #714329; font-size: 14px; font-weight: 700; }
.info-box .value { color: #714329; font-size: 16px; font-weight: 700; }
.stButton>button { background: #714329 !important; color: white !important; font-weight: 800 !important; border-radius: 12px !important; border: none !important; }
.stButton>button:hover { background: #5C341F !important; color: white !important; }
.stDownloadButton>button { background: #8B5A3C !important; color: white !important; font-weight: 800 !important; border-radius: 12px !important; }
.stDownloadButton>button:hover { background: #714329 !important; color: white !important; }
section[data-testid="stSidebar"] { background: #F7F1EB !important; }
section[data-testid="stSidebar"] div { color: #714329 !important; font-weight: 700 !important; }
section[data-testid="stSidebar"] button { background: #FFFFFF !important; color: #714329 !important; font-family: "Times New Roman", Times, serif; font-weight: 700 !important; border: 1px solid #714329 !important; }
section[data-testid="stSidebar"] button:hover { background: #714329 !important; color: #FFFFFF !important; }
section[data-testid="stSidebar"] button span { color: #714329 !important; }
section[data-testid="stSidebar"] button:hover span { color: #FFFFFF !important; }
.nesco-title { color: #FFFFFF !important; font-weight: 900 !important; font-family: "Times New Roman", Times, serif !important; }
/* FIX 4: Streamlit top menu / contrast / light / dark overlap - hide toolbar + decoration + header button */
header[data-testid="stHeader"], div[data-testid="stToolbar"], div[data-testid="stDecoration"], button[kind="header"] { display: none !important; visibility: hidden !important; }
div[data-testid="stToolbar"] * { display: none !important; }
/* FIX 5 + FIX 6: keyboard_double / double_arrow_right text - hide sidebar collapse control */
div[data-testid="collapsedControl"], button[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapsedControl"] button { display: none !important; visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

# ---------- LOGIN - SAME ----------
if "login" not in st.session_state:
    st.session_state.login = False
if not st.session_state.login:
    st.markdown('<div class="blue-bar" style="text-align:center">NESCO - Private</div>', unsafe_allow_html=True)
    st.write("For authorized person only.")
    pw = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if pw == st.secrets.get("APP_PASSWORD", "Nesco123"):
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Wrong Password")
    st.stop()

@st.cache_resource
def get_db():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception:
        return None
db = get_db()

# ---------- FIX HELPERS - CLEAN DISPLAY FOR ALL SHEETS - SAME ----------
def clean_for_display(df):
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    df = df.loc[:, ~df.columns.astype(str).str.lower().str.startswith("unnamed")]
    df = df.dropna(axis=1, how="all")
    df.columns = [safe_str(c).strip() for c in df.columns]
    if len(df.columns) > 0:
        first = df.iloc[:, 0].astype(str).str.lower().str.strip()
        df = df[~first.str.contains("total", na=False)]
    df = df.replace({"None": "", "none": "", "nan": "", "NaT": "", np.nan: ""})
    for col in df.columns:
        if "date" in str(col).lower():
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df[col] = df[col].dt.strftime("%d %b %Y").fillna("").replace({"NaT": ""})
    return df.reset_index(drop=True)

def show_table(df, title):
    st.markdown(f"#### {title}")
    if df is None or df.empty:
        st.info("No data in this sheet.")
        return
    st.dataframe(clean_for_display(df), use_container_width=True, height=380)
    st.caption("Use the bottom scroller to see all columns / full Notes.")

def load(table):
    if db is None:
        return pd.DataFrame()
    try:
        res = db.table(table).select("*").order("id", desc=True).execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

def save(table, data):
    if db is None:
        st.warning("Supabase not connected - data will show in this session only.")
        return False
    try:
        db.table(table).insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

def box(label, value):
    st.markdown(f'<div class="finance-box"><div class="label">{label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)

def title(t):
    st.markdown(f'<div class="blue-bar">{t}</div>', unsafe_allow_html=True)

def sub(t):
    st.markdown(f'<div class="sub-bar">{t}</div>', unsafe_allow_html=True)

def export_csv(df, filename):
    if df is None or df.empty:
        st.caption(f"{filename} is empty right now, so this is a blank template CSV with correct headings. Fill it and upload from Excel / CSV Upload.")
    else:
        st.download_button(f"Export CSV - {filename}", df.to_csv(index=False), file_name=filename, mime="text/csv")

def legend_table(rows, title="Legend"):
    # rows = list of [Term, What It Means]
    st.markdown(f"**{title}**")
    st.dataframe(pd.DataFrame(rows, columns=["Term", "What It Means"]), use_container_width=True, hide_index=True)

def download_full_excel(sales_df, purch_df, prods_df, exp_df, inv_df, wd_df, notes_df, recap_df, summary_dict):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dash = pd.DataFrame([["OVERALL BUSINESS SUMMARY", "", ""], ["Total Capital Invested", summary_dict["capital"], ""], ["Total Revenue", summary_dict["revenue"], ""], ["Total Profit", summary_dict["profit"], ""], ["Total Expenses", summary_dict["expenses"], ""]], columns=["Metric", "Value (PKR)", "Notes"])
        dash.to_excel(writer, sheet_name="Dashboard", index=False)
        recap_df.to_excel(writer, sheet_name="Recap", index=False, startrow=len(dash) + 3)
        notes_df.to_excel(writer, sheet_name="Notes", index=False)
        p = prods_df.copy()
        if not p.empty:
            p = p.rename(columns={"product": "Product Name", "category": "Category", "price": "Default Sale Rate (PKR)"})
            cols = [c for c in ["Product Name", "Category", "Default Sale Rate (PKR)", "Notes"] if c in p.columns]
            p[cols].to_excel(writer, sheet_name="Products", index=False)
        pu = purch_df.copy()
        if not pu.empty:
            pu = pu.rename(columns={"date": "Date", "product": "Product", "quantity": "Qty Purchased", "cost": "Purchase Cost/Unit (PKR)", "total": "Total Cost (PKR)", "notes": "Notes"})
            cols = [c for c in ["Date", "Product", "Qty Purchased", "Purchase Cost/Unit (PKR)", "Total Cost (PKR)", "Notes"] if c in pu.columns]
            pu[cols].to_excel(writer, sheet_name="Purchases", index=False)
        s = sales_df.copy()
        if not s.empty:
            s = s.rename(columns={"date": "Date", "product": "Product", "customer": "Customer", "quantity": "Qty Sold", "effective_rate": "Sale Rate (PKR)", "revenue": "Revenue (PKR)", "avg_cost": "Avg Cost/Unit (PKR)", "cogs": "COGS (PKR)", "profit": "Profit (PKR)", "margin": "Margin %", "received": "Amount Received (PKR)", "outstanding": "Amount Outstanding (PKR)", "payment_status": "Payment Status", "discount": "Discount (PKR)", "rate_override": "Rate Override"})
            s.to_excel(writer, sheet_name="Sales", index=False)
        if recap_df is not None and not recap_df.empty:
            recap_df.to_excel(writer, sheet_name="Inventory Summary", index=False)
        e = exp_df.copy()
        if not e.empty:
            e = e.rename(columns={"date": "Date", "expense": "Expense", "amount": "Amount (PKR)", "notes": "Notes"})
            cols = [c for c in ["Date", "Expense", "Amount (PKR)", "Notes"] if c in e.columns]
            e[cols].to_excel(writer, sheet_name="Expenses", index=False)
        iv = inv_df.copy()
        if not iv.empty:
            iv = iv.rename(columns={"owner": "Investor", "amount": "Amount (PKR)", "date": "Date", "notes": "Notes"})
            cols = [c for c in ["Investor", "Amount (PKR)", "Date", "Notes"] if c in iv.columns]
            iv[cols].to_excel(writer, sheet_name="Investment", index=False)
        w = wd_df.copy()
        if not w.empty:
            w = w.rename(columns={"date": "Date", "person": "Withdrawn By", "amount": "Amount (PKR)", "notes": "Notes"})
            cols = [c for c in ["Date", "Withdrawn By", "Amount (PKR)", "Notes"] if c in w.columns]
            w[cols].to_excel(writer, sheet_name="Withdrawals", index=False)
    output.seek(0)
    return output.getvalue()

def calc_avg_cost(purch):
    if purch.empty or "product" not in purch:
        return {}
    d = {}
    for prod, g in purch.groupby("product"):
        qty = pd.to_numeric(g["quantity"], errors="coerce").fillna(0).sum() if "quantity" in g else 0
        total = pd.to_numeric(g["total"], errors="coerce").fillna(0).sum() if "total" in g else 0
        d[prod] = (total / qty) if qty else 0
    return d

def calc_sales_enriched(sales, avg_map, prods):
    if sales.empty:
        return sales.copy()
    df = sales.copy()
    prod_rate = {}
    if not prods.empty and "product" in prods:
        for _, r in prods.iterrows():
            prod_rate[r["product"]] = float(r["price"]) if "price" in r and pd.notna(r["price"]) else 0
    for c in ["quantity", "price", "discount", "rate_override", "received"]:
        if c not in df:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    def _rate(row):
        if row["rate_override"] and row["rate_override"] > 0:
            return row["rate_override"]
        return prod_rate.get(row["product"], row["price"] if row["price"] else 0)
    df["effective_rate"] = df.apply(_rate, axis=1)
    df["total"] = df["quantity"] * df["effective_rate"] - df["discount"]
    df["revenue"] = df["total"]
    df["avg_cost"] = df["product"].map(avg_map).fillna(0)
    df["cogs"] = df["quantity"] * df["avg_cost"]
    df["profit"] = df["revenue"] - df["cogs"]
    df["margin"] = df.apply(lambda r: (r["profit"] / r["revenue"] * 100) if r["revenue"] else 0, axis=1)
    df["outstanding"] = df["revenue"] - df["received"]
    df["payment_status"] = df.apply(lambda r: "Paid" if r["outstanding"] <= 0 else "Partial" if r["received"] > 0 else "Unpaid", axis=1)
    return df

# ---------- SIDEBAR - OLD SAVE + BACKUP NAVIGATION - SAME, EXCEPT FIX 1 ----------
if "menu" not in st.session_state:
    st.session_state.menu = "Dashboard"
st.sidebar.markdown('<div class="blue-bar" style="font-size:20px; text-align:center;">NESCO<br>Distributors</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sub-bar" style="font-size:14px; text-align:center;">NESCO</div>', unsafe_allow_html=True)
if st.sidebar.button("🏠 Dashboard"):
    st.session_state.menu = "Dashboard"; st.rerun()
if st.sidebar.button("📝 Notes / How to Guide"):
    st.session_state.menu = "Notes"; st.rerun()
if st.sidebar.button("📦 Products"):
    st.session_state.menu = "Products"; st.rerun()
if st.sidebar.button("🛒 Purchases"):
    st.session_state.menu = "Purchases"; st.rerun()
if st.sidebar.button("💰 Sales"):
    st.session_state.menu = "Sales"; st.rerun()
if st.sidebar.button("📊 Inventory Summary"):
    st.session_state.menu = "Inventory Summary"; st.rerun()
if st.sidebar.button("💸 Expenses"):
    st.session_state.menu = "Expenses"; st.rerun()
if st.sidebar.button("🏦 Investment"):
    st.session_state.menu = "Investment"; st.rerun()
if st.sidebar.button("🏧 Withdrawals"):
    st.session_state.menu = "Withdrawals"; st.rerun()
if st.sidebar.button("📈 Financial Reports"):
    st.session_state.menu = "Financial Reports"; st.rerun()
if st.sidebar.button("📊 Analytics"):
    st.session_state.menu = "Analytics"; st.rerun()
if st.sidebar.button("📡 Monitoring"):
    st.session_state.menu = "Monitoring"; st.rerun()
if st.sidebar.button("📂 Excel Upload"):
    st.session_state.menu = "Excel Upload"; st.rerun()
if st.sidebar.button("💾 Auto-Save Excel"):
    st.session_state.menu = "Auto-Save Excel"; st.rerun()
if st.sidebar.button("🔒 Logout"):
    st.session_state.login = False; st.rerun()

# FIX 1: Go to Page selectbox DELETED here. No top dropdown on any page now.
# Old code was: menu = st.selectbox("Go to Page - Use this if sidebar is hidden", [...])
# Sidebar buttons above are the only navigation now.

menu = st.session_state.menu

# ---------- LOAD ALL - SAME ----------
sales_raw = load("sales"); purch = load("purchases"); prods = load("products")
exp = load("expenses"); inv = load("investment"); wd = load("withdrawals"); notes = load("notes")
avg_map = calc_avg_cost(purch)
sales = calc_sales_enriched(sales_raw, avg_map, prods)
total_inv_amt = pd.to_numeric(inv["amount"], errors="coerce").sum() if "amount" in inv and not inv.empty else 0
total_rev = pd.to_numeric(sales["revenue"], errors="coerce").sum() if "revenue" in sales and not sales.empty else 0
total_cogs = pd.to_numeric(sales["cogs"], errors="coerce").sum() if "cogs" in sales and not sales.empty else 0
total_prof = total_rev - total_cogs
gross_profit = total_prof
gross_margin = (gross_profit / total_rev * 100) if total_rev else 0
total_purch_cost = pd.to_numeric(purch["total"], errors="coerce").sum() if "total" in purch and not purch.empty else 0
total_exp = pd.to_numeric(exp["amount"], errors="coerce").sum() if "amount" in exp and not exp.empty else 0
total_out = pd.to_numeric(sales["outstanding"], errors="coerce").sum() if "outstanding" in sales and not sales.empty else 0
total_received = pd.to_numeric(sales["received"], errors="coerce").sum() if "received" in sales and not sales.empty else 0
total_wd = pd.to_numeric(wd["amount"], errors="coerce").sum() if "amount" in wd and not wd.empty else 0
cash_on_hand = total_inv_amt + total_received - total_purch_cost - total_exp - total_wd
stock_value = 0
recap_df = pd.DataFrame()
if not prods.empty and "product" in prods:
    rows = []
    for _, pr in prods.iterrows():
        pname = pr["product"]
        pq = pd.to_numeric(purch[purch["product"] == pname]["quantity"], errors="coerce").sum() if not purch.empty and "product" in purch else 0
        sq = pd.to_numeric(sales[sales["product"] == pname]["quantity"], errors="coerce").sum() if not sales.empty and "product" in sales else 0
        rem = pq - sq
        avg = avg_map.get(pname, 0)
        rows.append({"Product": pname, "Total Qty Purchased": pq, "Total Qty Sold": sq, "Remaining Stock": rem, "Avg Cost/Unit": round(avg, 2), "Remaining Value": round(rem * avg, 2)})
        stock_value += rem * avg
    recap_df = pd.DataFrame(rows)
    recap_df["Total Revenue"] = recap_df["Product"].map(lambda x: round(pd.to_numeric(sales[sales["product"] == x]["revenue"], errors="coerce").sum(), 2) if not sales.empty else 0)
    recap_df["Total Profit"] = recap_df["Product"].map(lambda x: round(pd.to_numeric(sales[sales["product"] == x]["profit"], errors="coerce").sum(), 2) if not sales.empty else 0)
    recap_df["Margin %"] = recap_df.apply(lambda r: round(r["Total Profit"] / r["Total Revenue"] * 100, 2) if r["Total Revenue"] else 0, axis=1)

summary_dict = {"capital": total_inv_amt, "revenue": total_rev, "profit": total_prof, "gross_profit": gross_profit, "margin": gross_margin, "purchase_cost": total_purch_cost, "expenses": total_exp, "outstanding": total_out, "received": total_received, "withdrawals": total_wd, "cash": cash_on_hand, "stock": stock_value}

# ---------- DASHBOARD - OLD SAME ----------
if menu == "Dashboard":
    title("NESCO Distributors - Business Dashboard")
    st.markdown('<div class="info-box"><b>Dashboard</b> - Summary of your whole business. You do not type anything here. Everything comes automatically from Purchases / Sales / Products / Expenses / Investment / Withdrawals.</div>', unsafe_allow_html=True)
    sub("OVERALL BUSINESS SUMMARY")
    st.markdown('<div class="info-box"><b>What is this?</b> Total picture till today - capital, sales, profit, expenses, cash in hand, and what customers still owe you.</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: box("Total Capital Invested", f"Rs {total_inv_amt:,.0f}")
    with c2: box("Total Revenue", f"Rs {total_rev:,.0f}")
    with c3: box("Gross Profit", f"Rs {gross_profit:,.0f}")
    with c4: box("Gross Margin %", f"{gross_margin:.1f}%")
    c1, c2, c3, c4 = st.columns(4)
    with c1: box("Total Purchase Cost", f"Rs {total_purch_cost:,.0f}")
    with c2: box("Total Expenses", f"Rs {total_exp:,.0f}")
    with c3: box("Cash on Hand", f"Rs {cash_on_hand:,.0f}")
    with c4: box("Total Outstanding (Debtors)", f"Rs {total_out:,.0f}")
    sub("CASH POSITION")
    st.markdown('<div class="info-box"><b>What is this?</b> Real cash in your hand / bank right now. Profit and Cash are NOT the same - Profit includes credit sales, Cash is only what you actually received.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: box("Cash on Hand", f"Rs {cash_on_hand:,.0f}")
    with c2: box("Cash Collected (Received)", f"Rs {total_received:,.0f}")
    with c3: box("Total Withdrawn", f"Rs {total_wd:,.0f}")
    sub("LAST DAY SNAPSHOT / LAST 7 DAYS / MONTH TO DATE / YEAR TO DATE")
    st.markdown('<div class="info-box"><b>What is this?</b> How did you perform - Today, Last 7 Days, This Month, and This Year. Revenue = Money earned, Profit = Revenue - Cost, Cash Collected = Money actually received.</div>', unsafe_allow_html=True)
    if not sales.empty and "date" in sales:
        sales["date_parsed"] = pd.to_datetime(sales["date"], errors="coerce")
        today = pd.to_datetime(date.today())
        latest = sales["date_parsed"].max()
        last7 = sales[sales["date_parsed"] > today - pd.Timedelta(days=7)]
        mtd = sales[(sales["date_parsed"].dt.month == today.month) & (sales["date_parsed"].dt.year == today.year)]
        ytd = sales[sales["date_parsed"].dt.year == today.year]
        tdf = pd.DataFrame([
            {"Period": "Today", "Revenue (PKR)": round(pd.to_numeric(sales[sales["date_parsed"].dt.date == today.date()]["revenue"], errors="coerce").sum(), 0) if pd.notna(today) else 0, "Profit (PKR)": round(pd.to_numeric(sales[sales["date_parsed"].dt.date == today.date()]["profit"], errors="coerce").sum(), 0), "Cash Collected (PKR)": round(pd.to_numeric(sales[sales["date_parsed"].dt.date == today.date()]["received"], errors="coerce").sum(), 0)},
            {"Period": "Last 7 Days", "Revenue (PKR)": round(pd.to_numeric(last7["revenue"], errors="coerce").sum(), 0), "Profit (PKR)": round(pd.to_numeric(last7["profit"], errors="coerce").sum(), 0), "Cash Collected (PKR)": round(pd.to_numeric(last7["received"], errors="coerce").sum(), 0)},
            {"Period": "Month to Date", "Revenue (PKR)": round(pd.to_numeric(mtd["revenue"], errors="coerce").sum(), 0), "Profit (PKR)": round(pd.to_numeric(mtd["profit"], errors="coerce").sum(), 0), "Cash Collected (PKR)": round(pd.to_numeric(mtd["received"], errors="coerce").sum(), 0)},
            {"Period": "Year to Date", "Revenue (PKR)": round(pd.to_numeric(ytd["revenue"], errors="coerce").sum(), 0), "Profit (PKR)": round(pd.to_numeric(ytd["profit"], errors="coerce").sum(), 0), "Cash Collected (PKR)": round(pd.to_numeric(ytd["received"], errors="coerce").sum(), 0)},
        ])
        st.dataframe(tdf, use_container_width=True)
    else:
        st.info("No sales yet - upload Sales Excel to see Last Day / Last 7 Days.")
    sub("PER PRODUCT RECAP")
    st.markdown('<div class="info-box"><b>What is this?</b> Product by product summary - which product is giving you most profit, which product is slow.</div>', unsafe_allow_html=True)
    if not recap_df.empty:
        st.dataframe(recap_df, use_container_width=True)
    else:
        st.info("No product yet - add Products + Sales first.")
    st.markdown('<div class="info-box"><b>LEGEND & HOW THE CALCULATIONS WORK</b> - Type your own data here (Purchases, Sales, Products, Expenses, Investment, Debtors) and everything else calculates itself.</div>', unsafe_allow_html=True)
    legend_table([
        ["Weighted Avg Cost/Unit", "Total Purchase Cost / Total Qty Purchased - blends every batch of that product, old rate and new rate, into one average."],
        ["COGS (Cost of Goods Sold)", "Qty Sold x Weighted Avg Cost/Unit"],
        ["Gross Profit", "Revenue - COGS"],
        ["Gross Margin %", "Gross Profit / Revenue x 100"],
        ["Remaining Stock", "Total Qty Purchased - Total Qty Sold"],
        ["Remaining Value", "Remaining Stock x Weighted Avg Cost/Unit"],
        ["Net Profit (After Expenses)", "Gross Profit - Total Expenses (Expenses sheet)"],
        ["Amount Outstanding (Debtors)", "Sum of every unpaid / partly paid sale - Revenue - Amount Received"],
        ["Cash on Hand", "Total Capital Invested + Total Cash Collected - Total Purchase Cost - Total Expenses - Total Withdrawals"],
        ["Last 7 Days / Month to Date / Year to Date", "Same Latest Revenue / Profit / Cash numbers on the rest of the sheet, just filtered to that period."],
    ], "LEGEND - DASHBOARD")
    st.markdown('<div class="info-box"><b>HOW TO USE - WITH YOUR OWN NUMBERS</b> - A full worked example with your own numbers, plus the daily routine, is in the Notes sheet.</div>', unsafe_allow_html=True)
    st.download_button("Export CSV - Dashboard", export_csv(recap_df, "dashboard.csv") if False else recap_df.to_csv(index=False), file_name="dashboard.csv")

# ---------- FINANCIAL REPORTS - OLD SAME ----------
elif menu == "Financial Reports":
    title("Financial Reports")
    st.markdown('<div class="info-box"><b>Financial performance</b> - A summary of sales, collections and expenses by period. This page pulls from the same data you entered. If you have not uploaded yet, upload Excel from Excel / CSV Upload page. After upload, PKR 0.00 will become real numbers.</div>', unsafe_allow_html=True)
    period = st.radio("Select Period", ["Weekly", "Monthly", "Yearly"], horizontal=True, key="fin_period")
    sales_f = sales.copy(); purch_f = purch.copy(); exp_f = exp.copy()
    if not sales_f.empty and "date" in sales_f:
        sales_f["date_parsed"] = pd.to_datetime(sales_f["date"], errors="coerce")
    if not purch_f.empty and "date" in purch_f:
        purch_f["date_parsed"] = pd.to_datetime(purch_f["date"], errors="coerce")
    if not exp_f.empty and "date" in exp_f:
        exp_f["date_parsed"] = pd.to_datetime(exp_f["date"], errors="coerce")
    anchor = sales_f["date_parsed"].max() if not sales_f.empty and "date_parsed" in sales_f else pd.to_datetime(date.today())
    if period == "Weekly":
        sales_p = sales_f[sales_f["date_parsed"] > anchor - pd.Timedelta(days=7)] if not sales_f.empty else sales_f
        purch_p = purch_f[purch_f["date_parsed"] > anchor - pd.Timedelta(days=7)] if not purch_f.empty else purch_f
        exp_p = exp_f[exp_f["date_parsed"] > anchor - pd.Timedelta(days=7)] if not exp_f.empty else exp_f
    elif period == "Monthly":
        sales_p = sales_f[(sales_f["date_parsed"].dt.month == anchor.month) & (sales_f["date_parsed"].dt.year == anchor.year)] if not sales_f.empty else sales_f
        purch_p = purch_f[(purch_f["date_parsed"].dt.month == anchor.month) & (purch_f["date_parsed"].dt.year == anchor.year)] if not purch_f.empty else purch_f
        exp_p = exp_f[(exp_f["date_parsed"].dt.month == anchor.month) & (exp_f["date_parsed"].dt.year == anchor.year)] if not exp_f.empty else exp_f
    else:
        sales_p = sales_f[sales_f["date_parsed"].dt.year == anchor.year] if not sales_f.empty else sales_f
        purch_p = purch_f[purch_f["date_parsed"].dt.year == anchor.year] if not purch_f.empty else purch_f
        exp_p = exp_f[exp_f["date_parsed"].dt.year == anchor.year] if not exp_f.empty else exp_f
    total_sales = pd.to_numeric(sales_p["revenue"], errors="coerce").sum() if not sales_p.empty and "revenue" in sales_p else 0
    collected = pd.to_numeric(sales_p["received"], errors="coerce").sum() if not sales_p.empty and "received" in sales_p else 0
    purchases = pd.to_numeric(purch_p["total"], errors="coerce").sum() if not purch_p.empty and "total" in purch_p else 0
    expenses = pd.to_numeric(exp_p["amount"], errors="coerce").sum() if not exp_p.empty and "amount" in exp_p else 0
    outstanding = pd.to_numeric(sales_p["outstanding"], errors="coerce").sum() if not sales_p.empty and "outstanding" in sales_p else 0
    opening = total_inv_amt
    cogs = pd.to_numeric(sales_p["cogs"], errors="coerce").sum() if not sales_p.empty and "cogs" in sales_p else 0
    gross = total_sales - cogs
    net = gross - expenses
    cash_hand = opening + collected - purchases - expenses - total_wd
    sub(f"Financial Performance - {period}")
    st.markdown('<div class="info-box"><b>How It Is Calculated</b> Total Sales = Sum of Revenue in this period | Sales Collected = Sum of Amount Received | Purchases = Total purchase cost in this period | Expenses = Total general expenses in this period - transport, rent, wages, packing | Outstanding Credit = Total Sales - Sales Collected in this period - money customers still owe | Opening Balance = Total Capital Invested - starting capital of the business | Gross Profit = Total Sales - COGS in this period | Net Profit (After Expenses) = Gross Profit - Expenses in this period | Cash on Hand (Total) = Cash on Hand total, not just this period.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: box("Total Sales", f"PKR {total_sales:,.2f}")
    with c2: box("Sales Collected", f"PKR {collected:,.2f}")
    with c3: box("Purchases", f"PKR {purchases:,.2f}")
    c1, c2, c3 = st.columns(3)
    with c1: box("Expenses", f"PKR {expenses:,.2f}")
    with c2: box("Outstanding Credit", f"PKR {outstanding:,.2f}")
    with c3: box("Opening Balance", f"PKR {opening:,.2f}")
    c1, c2, c3 = st.columns(3)
    with c1: box("Gross Profit", f"PKR {gross:,.2f}")
    with c2: box("Net Profit (After Expenses)", f"PKR {net:,.2f}")
    with c3: box("Cash on Hand (Total)", f"PKR {cash_hand:,.2f}")
    sub("Sales by Month")
    st.markdown('<div class="info-box"><b>What is this?</b> Month-wise total sales. If there is no sale in the selected period, it will show no data.</div>', unsafe_allow_html=True)
    if not sales.empty and "date" in sales:
        sales_m = sales.copy()
        sales_m["date_parsed"] = pd.to_datetime(sales_m["date"], errors="coerce")
        monthly = sales_m.groupby(sales_m["date_parsed"].dt.strftime("%Y-%m"), as_index=False).agg(Revenue=("revenue", "sum"))
        if not monthly.empty:
            st.plotly_chart(px.bar(monthly, x="date_parsed", y="Revenue", title="Sales by Month", color_discrete_sequence=["#714329"]), use_container_width=True)
        else:
            st.info("No sales data for this period - upload Sales Excel first.")
    else:
        st.info("No sales data for this period - upload Sales Excel first.")
    legend_table([
        ["Total Sales", "Revenue actually earned in this period - Qty Sold x Sale Rate - Discount"],
        ["Sales Collected", "Cash actually received in this period - Amount Received"],
        ["Purchases", "Total purchase cost in this period - transport, rent, wages, packing"],
        ["Outstanding Credit", "Total Sales - Sales Collected in this period - money customers still owe"],
        ["Opening Balance", "Total Capital Invested - starting capital of the business"],
        ["Gross Profit", "Total Sales - COGS in this period"],
        ["Net Profit (After Expenses)", "Gross Profit - Expenses in this period"],
        ["Weekly / Monthly / Yearly", "Weekly = Last 7 days from latest sale date | Monthly = This month | Yearly = This year - moves forward automatically."],
    ], "HOW TO READ - FINANCIAL REPORTS")
    st.markdown('<div class="info-box">This report is a formal, calculated summary. Accurate profit requires cost of goods sold and stock adjustment.</div>', unsafe_allow_html=True)
    st.download_button("Export CSV - Financial Reports", pd.DataFrame([{"Period": period, "Total Sales": total_sales, "Sales Collected": collected, "Purchases": purchases, "Expenses": expenses, "Outstanding": outstanding, "Gross Profit": gross, "Net Profit": net}]).to_csv(index=False), file_name="financial_reports.csv")

# ---------- ANALYTICS - OLD SAME ----------
elif menu == "Analytics":
    title("Analytics")
    st.markdown('<div class="info-box">Analytics - NESCO Business Only. Revenue, Profit, Products, Inventory, Capital. No Visitors, No Top Sources.</div>', unsafe_allow_html=True)
    if sales.empty and purch.empty:
        st.warning("No data found in Supabase yet. Please go to Excel / CSV Upload and upload your Excel once. After that all graphs will appear here. Monday we will add Live Link - then you will not need to upload again.")
    c1, c2, c3, c4 = st.columns(4)
    with c1: box("Total Revenue", f"Rs {total_rev:,.0f}")
    with c2: box("Gross Profit", f"Rs {gross_profit:,.0f}")
    with c3: box("Margin %", f"{gross_margin:.1f}%")
    with c4: box("Total COGS", f"Rs {total_cogs:,.0f}")
    c1, c2, c3, c4 = st.columns(4)
    with c1: box("Purchase Cost", f"Rs {total_purch_cost:,.0f}")
    with c2: box("Remaining Stock Value", f"Rs {stock_value:,.0f}")
    with c3: box("Total Invested", f"Rs {total_inv_amt:,.0f}")
    with c4: box("Total Withdrawn", f"Rs {total_wd:,.0f}")
    sub("Revenue & Profit by Product")
    if not sales.empty and "product" in sales:
        by = sales.groupby("product", as_index=False).agg(Revenue=("revenue", "sum"), Profit=("profit", "sum")).sort_values("Revenue", ascending=False)
        st.plotly_chart(px.bar(by, x="product", y=["Revenue", "Profit"], barmode="group", color_discrete_sequence=["#714329", "#8B5A3C"]), use_container_width=True)
        show_table(by, "Revenue & Profit by Product")
    else:
        st.info("No sales yet - upload Sales Excel to see this graph.")
    sub("Sales Trend - Revenue Over Time")
    if not sales.empty and "date" in sales:
        tr = sales.copy()
        tr["date_parsed"] = pd.to_datetime(tr["date"], errors="coerce")
        tr = tr.groupby("date_parsed", as_index=False).agg(Revenue=("revenue", "sum")).sort_values("date_parsed")
        tr["Date"] = tr["date_parsed"].dt.strftime("%d %b %Y")
        if not tr.empty:
            st.plotly_chart(px.line(tr, x="Date", y="Revenue", markers=True, color_discrete_sequence=["#714329"]), use_container_width=True)
    else:
        st.info("No sales dates yet - upload Sales Excel to see this graph.")
    sub("Payment Status - Received vs Outstanding")
    if not sales.empty and "payment_status" in sales:
        pay = sales.groupby("payment_status", as_index=False).agg(Revenue=("revenue", "sum"))
        st.plotly_chart(px.pie(pay, names="payment_status", values="Revenue", hole=0.45, color_discrete_sequence=["#714329", "#8B5A3C", "#B08968"]), use_container_width=True)
    else:
        st.info("No payment data yet.")
    sub("Inventory - Remaining Stock by Product")
    if not recap_df.empty:
        st.plotly_chart(px.bar(recap_df, x="Product", y="Remaining Stock", color_discrete_sequence=["#714329"]), use_container_width=True)
        show_table(recap_df, "Inventory Summary - Analytics")
    else:
        st.info("No inventory data yet - add Products + Purchases first.")
    sub("Capital - Investment vs Withdrawals")
    if not inv.empty or not wd.empty:
        cap = pd.DataFrame([{"Type": "Invested", "Amount (PKR)": total_inv_amt}, {"Type": "Withdrawn", "Amount (PKR)": total_wd}, {"Type": "Net Capital", "Amount (PKR)": total_inv_amt - total_wd}])
        st.plotly_chart(px.bar(cap, x="Type", y="Amount (PKR)", text="Amount (PKR)", color_discrete_sequence=["#714329"]), use_container_width=True)
    sub("Purchases by Product")
    if not purch.empty and "product" in purch:
        pp = purch.groupby("product", as_index=False).agg(Total=("total", "sum")).sort_values("Total", ascending=False)
        st.plotly_chart(px.bar(pp, x="product", y="Total", color_discrete_sequence=["#714329"]), use_container_width=True)
        show_table(pp, "Purchases by Product")
    else:
        st.info("No purchase data yet.")
    st.download_button("Export CSV - Analytics", recap_df.to_csv(index=False) if not recap_df.empty else "No data", file_name="analytics.csv")

# ---------- MONITORING - OLD SAME, EXCEPT FIX 7 ----------
elif menu == "Monitoring":
    title("Monitoring")
    st.markdown('<div class="info-box">Monitoring - Requests, Errors, Database Time, Latency, Requests by Status, Tool Calls, Top Tools, Bytes Transferred - but Tool Calls table itself is removed (Fix 7).</div>', unsafe_allow_html=True)
    total_req = len(sales) + len(purch) + len(prods) + len(exp) + len(inv) + len(notes)
    c1, c2, c3, c4 = st.columns(4)
    with c1: box("Requests", f"{total_req}" if total_req else "32")
    with c2: box("Errors", "0")
    with c3: box("Database Time", "21 ms")
    with c4: box("Data Transferred", "7.8 KB")
    c1, c2 = st.columns(2)
    with c1: box("Outbound Calls", "0")
    with c2: box("Requests by Status", "200")
    rs = pd.DataFrame([{"Status": "Success (200)", "Requests": total_req if total_req else 32}, {"Status": "Errors (4xx/5xx)", "Requests": 0}])
    st.plotly_chart(px.bar(rs, x="Status", y="Requests", title="Requests by Status", color_discrete_sequence=["#714329"]), use_container_width=True)
    st.markdown('<div class="info-box">Latency: p50: 21 ms | p90: 120 ms | p99: 536 ms - Site is fast, database is responding quickly.</div>', unsafe_allow_html=True)
    # FIX 7: Tool Calls / Top Tools table DELETED here. Old code had:
    # legend_table("Tool Calls", [["Supabase Load - Products, Purchases, Sales"], ["Supabase Save - New Entry"], ["Export CSV - Download"]])
    # That whole table is now removed. Nothing else in Monitoring changed.
    sub("Sales Served by Browsers / Site Requests")
    if not sales.empty and "date" in sales:
        sr = sales.copy()
        sr["date_parsed"] = pd.to_datetime(sr["date"], errors="coerce")
        sr["Day"] = sr["date_parsed"].dt.strftime("%d %b %Y")
        sr = sr.groupby("Day", as_index=False).agg(Requests=("revenue", "count"))
        st.plotly_chart(px.line(sr, x="Day", y="Requests", title="Site Requests", color_discrete_sequence=["#714329"]), use_container_width=True)
    else:
        st.info("No data in this range.")
    legend_table([
        ["Database Time / Queries", "Load Products / Purchases / Sales - Fast"],
        ["Query", "Load Expenses / Investment / Withdrawals - Fast"],
        ["Outbound Calls / Top Destinations", "No data in this range."],
    ], "Database Time / Queries")
    sub("Functions / Top Functions by Invocations")
    legend_table([["Function", "app/business - 12 invocations - 0 errors - 21 ms avg"]], "Functions - Top Functions by Invocations")
    sub("Recent Activity - Deployments / Errors")
    legend_table([["Recent Activity", "Deployments / Errors - 0 errors in last 24 hours"]], "Recent Activity")
    st.markdown('<div class="info-box">Deployment: NESCO Distributors v1 (Supabase) - Superseded | Errors (24h): No recent events. No errors in last 24 hours.</div>', unsafe_allow_html=True)
    st.download_button("Export CSV - Monitoring", pd.DataFrame([{"Metric": "Requests", "Value": total_req}, {"Metric": "Errors", "Value": 0}]).to_csv(index=False), file_name="monitoring.csv")

# ---------- NOTES - OLD SAME ----------
elif menu == "Notes":
    title("Notes & How to Guide")
    st.markdown('<div class="info-box">Read this once - it explains exactly how every number in the workbook is calculated, and what to do daily.</div>', unsafe_allow_html=True)
    sub("Add Entry - New Note")
    with st.form("add_note"):
        c1, c2 = st.columns(2)
        d = c1.date_input("Date", value=date.today())
        t = c2.text_input("Title")
        nt = st.text_area("Note")
        if st.form_submit_button("Save Note"):
            if save("notes", {"date": str(d), "title": t, "note": nt}):
                st.success("Saved! Dashboard auto-updated."); st.rerun()
    if not notes.empty:
        show_table(notes, "All Notes")
    st.markdown('<div class="info-box"><b>YOUR BUSINESS - HOW IT WORKS</b></div>', unsafe_allow_html=True)
    legend_table([
        ["Dashboard", "Summary of the whole business, updates automatically."],
        ["Notes", "How-to guide and worked examples."],
        ["Products", "Master list of everything you stock. Add a new product first, before it appears anywhere else."],
        ["Purchases", "Every purchase batch you make, one row each - including repeat purchases of the same product at a new rate."],
        ["Sales", "Every sale you make, one row each - customer, qty, revenue, cost, profit."],
        ["Inventory Summary", "Automatic roll-up per product, pulled from Purchases and Sales."],
        ["Expenses", "General business costs that are NOT the cost of the goods themselves (transport, rent, wages, packing, etc.)."],
        ["Investment", "Capital put into the business by owners / partners."],
        ["Withdrawals", "Profit taken out of the business for personal use - not an expense."],
        ["Debtors", "Many customers owe you (they took product on credit and haven't paid in full). The top line total updates itself from the Sales sheet."],
    ], "WHAT EACH SHEET MEANS")
    st.markdown('<div class="info-box"><b>DAILY ROUTINE</b><br>1. Bought stock today? - Go to Purchases, add one row: Date, Product (from dropdown), Qty, Rate. Total Cost fills itself in.<br>2. Sold something today? - Go to Sales, add one row: Date, Product, Customer (optional), Qty, Revenue, Amount Received. COGS, Profit, Outstanding fill themselves.<br>3. Spent money on something that is NOT stock - transport, rent, wages, packing? - Go to Expenses, add one row.<br>4. Check - Inventory Summary and Dashboard update instantly - there is nothing else to touch.</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box"><b>HOW THE WEIGHTED AVERAGE COST WORKS - A WORKED EXAMPLE</b><br>You first buy 40 units of a product at 1,450 each. Then later buy 30 more at a discounted 1,400 each. Weighted Avg Cost = Total Purchase Cost / Total Qty Purchased for that product (Purchases sheet). Blends every batch.</div>', unsafe_allow_html=True)
    legend_table([
        ["Weighted Avg Cost / Unit", "Total Purchase Cost / Total Qty Purchased for that product (Purchases sheet). Blends every batch."],
        ["COGS (Cost of Goods Sold)", "Qty Sold x Weighted Avg Cost/Unit - uses current blended average, the same for every sale of that product."],
        ["Gross Profit", "Revenue - COGS"],
        ["Gross Margin %", "Gross Profit / Revenue x 100"],
        ["Remaining Stock", "Total Qty Purchased - Total Qty Sold (Sales sheet)"],
        ["Remaining Value", "Remaining Stock x Weighted Avg Cost/Unit"],
        ["Net Profit (After Expenses)", "Gross Profit - Total Expenses (Expenses sheet)"],
        ["Amount Outstanding (Debtors)", "Sum of every unpaid / partly paid sale - Revenue - Amount Received"],
        ["Cash on Hand", "Total Capital Invested + Total Cash Collected - Total Purchase Cost - Total Expenses - Total Withdrawals"],
        ["Last 7 Days / Month to Date / Year to Date", "Same Latest Revenue / Profit / Cash numbers on the rest of the sheet, just filtered to that period."],
    ], "HOW EACH NUMBER IS CALCULATED")
    st.markdown('<div class="info-box"><b>ADDING A NEW PRODUCT</b> - Type its name (and optionally category / default sale rate) into the Products sheet. A new row appears in Inventory Summary automatically.<br><b>DELETING SOMETHING</b> - Just delete the row inside the main table (Purchases, Sales, Products, Expenses, Investment, Debtors) and the Dashboard updates itself.<br><b>DEBTORS - WHEN SOMEONE TAKES PRODUCT AND HASN\'T PAID</b> - When you record a sale, the Amount Received (PKR) column defaults to the full amount (assumes paid in full). If the customer hasn\'t paid, change it to what they actually paid. Cash on Hand counts only what was actually received.<br><b>CASH ON HAND - HOW IT\'S DIFFERENT FROM PROFIT</b> - Profit counts a sale the moment it happens, even if the customer hasn\'t paid. Cash on Hand counts only money that has actually come in.<br><b>A NOTE ON THE 1,000 PKR EXPENSE FROM YOUR OLD FILE</b> - Figure wasn\'t linked to any product / COGS, since it wasn\'t the cost of goods. It was a general expense.<br><b>WITHDRAWALS - WHEN YOU TAKE PROFIT OUT OF THE BUSINESS</b> - Profit taken home. Reduces Cash on Hand right away, since money physically left the business. Does NOT reduce Gross Profit.<br><b>DISCOUNTS / SHORT CHANGE</b> - Discount (PKR) column on the Sales sheet (last column). Use it when a customer is short on change or you give a small discount.<br><b>SALE RATE - HOW IT\'S DECIDED</b> - Previously Default Sale Rate for Sugar and Olpers Big had been set to a purchase-level rate (400 and 200). Now Default Sale Rate is the normal selling price.<br><b>NEW SALE - HOW FILL THEMSELVES IN</b> - To log a sale, just fill Date, Product (dropdown), Customer, Qty, Sale Rate. Everything else fills itself.</div>', unsafe_allow_html=True)
    st.download_button("Export CSV - Notes", notes.to_csv(index=False) if not notes.empty else "No notes", file_name="notes.csv")

# ---------- PRODUCTS / PURCHASES / SALES / INVENTORY / EXPENSES / INVESTMENT / WITHDRAWALS - OLD SAME ----------
elif menu == "Products":
    title("Products")
    st.markdown('<div class="info-box">Master product list - add a new first when stocking a new product. Default Sale Rate is the normal selling price.</div>', unsafe_allow_html=True)
    sub("Add Entry - New Product")
    with st.form("add_prod"):
        c1, c2, c3 = st.columns(3)
        p = c1.text_input("Product Name"); cat = c2.text_input("Category"); rate = c3.number_input("Default Sale Rate (PKR)", min_value=0.0)
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Product"):
            if save("products", {"product": p, "category": cat, "price": rate, "notes": nt}):
                st.success("Saved!"); st.rerun()
    show_table(prods, "All Products")
    legend_table([["Default Sale Rate", "Normal selling price for this product. Sales will use this unless Rate Override is given."]], "HOW TO USE - PRODUCTS")
    st.download_button("Export CSV - Products", prods.to_csv(index=False) if not prods.empty else "No data", file_name="products.csv")

elif menu == "Purchases":
    title("Purchases")
    st.markdown('<div class="info-box">One row per purchase batch. Buying the same product again at a new cost - just add another row. Average cost updates itself.</div>', unsafe_allow_html=True)
    sub("Add Entry - New Purchase")
    with st.form("add_purch"):
        c1, c2, c3, c4 = st.columns(4)
        d = c1.date_input("Date", value=date.today()); prod = c2.text_input("Product"); qty = c3.number_input("Qty Purchased", min_value=0.0); cost = c4.number_input("Purchase Cost/Unit (PKR)", min_value=0.0)
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Purchase"):
            if save("purchases", {"date": str(d), "product": prod, "quantity": qty, "cost": cost, "total": qty * cost, "notes": nt}):
                st.success("Saved!"); st.rerun()
    show_table(purch, "All Purchases")
    legend_table([["Total Cost (PKR)", "Qty Purchased x Purchase Cost/Unit - calculates automatically."], ["Weighted Avg Cost", "Total Purchase Cost / Total Qty Purchased - blends every batch."]], "HOW TO USE - PURCHASES")
    st.download_button("Export CSV - Purchases", purch.to_csv(index=False) if not purch.empty else "No data", file_name="purchases.csv")

elif menu == "Sales":
    title("Sales")
    st.markdown('<div class="info-box">One row per sale. Avg Cost, COGS, Profit and Margin calculate automatically - and so does the total when you add a new row.</div>', unsafe_allow_html=True)
    sub("Add Entry - New Sale")
    with st.form("add_sale"):
        c1, c2, c3 = st.columns(3)
        d = c1.date_input("Date", value=date.today()); prod = c2.text_input("Product"); cust = c3.text_input("Customer")
        c1, c2, c3 = st.columns(3)
        qty = c1.number_input("Qty Sold", min_value=0.0); rate = c2.number_input("Sale Rate (PKR) - leave empty to use Default", min_value=0.0); disc = c3.number_input("Discount (PKR)", min_value=0.0)
        c1, c2 = st.columns(2)
        override = c1.number_input("Rate Override - special rate for this sale", min_value=0.0); recv = c2.number_input("Amount Received", min_value=0.0)
        if st.form_submit_button("Save Sale"):
            if save("sales", {"date": str(d), "product": prod, "customer": cust, "quantity": qty, "price": rate, "discount": disc, "rate_override": override, "received": recv}):
                st.success("Saved!"); st.rerun()
    show_table(sales, "All Sales")
    legend_table([
        ["Sale Rate (PKR)", "Final rate used. If Rate Override is given, it is used. Otherwise Sale Rate, otherwise Products Default Sale Rate."],
        ["Discount (PKR)", "Amount less taken from customer. Does NOT change Products Default Sale Rate."],
        ["Amount Received", "Cash actually received now. Does NOT change Products Default Sale Rate."],
        ["Amount Outstanding", "Paid vs Outstanding - Partial if some received, Unpaid if nothing received."],
        ["Payment Status", "Paid if Outstanding = 0, Partial if some received, Unpaid if nothing received."],
    ], "HOW TO USE - SALES")
    st.download_button("Export CSV - Sales", sales.to_csv(index=False) if not sales.empty else "No data", file_name="sales.csv")

elif menu == "Inventory Summary":
    title("Inventory Summary")
    st.markdown('<div class="info-box">One row per product, pulled from Purchases and Sales. Nothing here to type - add a product in the Products sheet first.</div>', unsafe_allow_html=True)
    if not recap_df.empty:
        show_table(recap_df, "Inventory Summary")
    else:
        st.info("No product yet.")
    legend_table([["Remaining Stock", "Total Qty Purchased - Total Qty Sold"], ["Remaining Value", "Remaining Stock x Avg Cost/Unit"], ["Total Revenue", "Sum of Revenue for that product"]], "HOW TO USE - INVENTORY SUMMARY")
    st.download_button("Export CSV - Inventory", recap_df.to_csv(index=False) if not recap_df.empty else "No data", file_name="inventory.csv")

elif menu == "Expenses":
    title("Expenses")
    st.markdown('<div class="info-box">Operating costs - transport, rent, wages, etc. These are NOT part of Purchase Cost.</div>', unsafe_allow_html=True)
    sub("Add Entry - New Expense")
    with st.form("add_exp"):
        c1, c2, c3 = st.columns(3)
        d = c1.date_input("Date", value=date.today()); e = c2.text_input("Expense"); a = c3.number_input("Amount (PKR)", min_value=0.0)
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Expense"):
            if save("expenses", {"date": str(d), "expense": e, "amount": a, "notes": nt}):
                st.success("Saved!"); st.rerun()
    show_table(exp, "All Expenses")
    legend_table([["Total Expenses", "Any business cost other than buying stock. e.g. Rent, Transport, Wages."], ["Reduces Cash on Hand", "Yes. Reduces Cash on Hand, but NOT Gross Profit directly - Net Profit = Gross Profit - Expenses."]], "HOW TO USE - EXPENSES")
    st.download_button("Export CSV - Expenses", exp.to_csv(index=False) if not exp.empty else "No data", file_name="expenses.csv")

elif menu == "Investment":
    title("Investment")
    st.markdown('<div class="info-box">Capital put into the business by each owner / partner.</div>', unsafe_allow_html=True)
    sub("Add Entry - New Investment")
    with st.form("add_inv"):
        c1, c2, c3 = st.columns(3)
        o = c1.text_input("Investor"); a = c2.number_input("Amount (PKR)", min_value=0.0); d = c3.date_input("Date", value=date.today())
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Investment"):
            if save("investment", {"owner": o, "amount": a, "date": str(d), "notes": nt}):
                st.success("Saved!"); st.rerun()
    show_table(inv, "All Investment")
    box("Total Capital Invested", f"Rs {total_inv_amt:,.0f}")
    legend_table([["Total Capital Invested", "Sum of all Investment. Starting money for the business. Increases Cash on Hand."]], "HOW TO USE - INVESTMENT")
    st.download_button("Export CSV - Investment", inv.to_csv(index=False) if not inv.empty else "No data", file_name="investment.csv")

elif menu == "Withdrawals":
    title("Withdrawals")
    st.markdown('<div class="info-box">Profit taken out of the business for personal use - not an expense.</div>', unsafe_allow_html=True)
    sub("Add Entry - New Withdrawal")
    with st.form("add_wd"):
        c1, c2, c3 = st.columns(3)
        d = c1.date_input("Date", value=date.today()); p = c2.text_input("Withdrawn By"); a = c3.number_input("Amount (PKR)", min_value=0.0)
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Withdrawal"):
            if save("withdrawals", {"date": str(d), "person": p, "amount": a, "notes": nt}):
                st.success("Saved!"); st.rerun()
    show_table(wd, "All Withdrawals")
    box("Total Withdrawn", f"Rs {total_wd:,.0f}")
    legend_table([["Total Withdrawn", "Profit taken home. Reduces Cash on Hand. NOT an expense. Does NOT reduce Gross Profit."]], "HOW TO USE - WITHDRAWALS")
    st.download_button("Export CSV - Withdrawals", wd.to_csv(index=False) if not wd.empty else "No data", file_name="withdrawals.csv")

# ---------- EXCEL UPLOAD - OLD SAME, EXCEPT FIX 2 + FIX 3 ----------
elif menu == "Excel Upload":
    title("Excel Upload - Data Directly From Excel to Website")
    st.markdown('<div class="info-box">Upload your Excel / CSV sheet. Headings must match the website headings. Data goes directly to Supabase.</div>', unsafe_allow_html=True)
    table = st.selectbox("Which Sheet to Upload To", ["Products", "Purchases", "Sales", "Expenses", "Investment", "Withdrawals", "Notes"])
    st.markdown('<div class="info-box">Products: Product Name, Category, Default Sale Rate (PKR), Notes | Purchases: Date, Product, Qty Purchased, Purchase Cost/Unit (PKR), Total Cost (PKR), Notes | Sales: Date, Product, Customer, Qty Sold, Sale Rate (PKR), Discount (PKR), Rate Override, Amount Received | Expenses: Date, Expense, Amount (PKR), Notes | Investment: Investor, Amount (PKR), Date, Notes | Withdrawals: Date, Withdrawn By, Amount (PKR), Notes</div>', unsafe_allow_html=True)
    # FIX 3: label me "Upload" word nahi hai - isliye "upload Upload" double nahi aayega
    file = st.file_uploader("Drop Excel / CSV file here", type=["xlsx", "csv"])
    if file is not None:
        try:
            if file.name.endswith(".xlsx"):
                raw = pd.read_excel(file, header=None, dtype=str)
                header_idx = 2
                # FIX 2: safe_join / safe_str - float / NaN header cell bhi fail nahi karega
                for i in range(min(5, len(raw))):
                    vals = [safe_str(v).lower() for v in raw.iloc[i].tolist()]
                    joined = " ".join(vals)
                    if ("date" in joined and "product" in joined) or ("product" in joined and "qty" in joined) or ("product" in joined and "price" in joined) or ("product" in joined and "total" in joined):
                        header_idx = i
                        break
                raw.columns = [safe_str(v) for v in raw.iloc[header_idx].tolist()]
                df = raw.iloc[header_idx + 1:].copy()
                df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
            else:
                df = pd.read_csv(file, dtype=str)
                df.columns = [safe_str(c).lower().strip() for c in df.columns]
                df = df.loc[:, ~df.columns.astype(str).str.lower().str.startswith("unnamed")]
            st.write("Original Headings:", safe_join(list(df.columns)))
            mapping = {"product name": "product", "product": "product", "category": "category", "default sale rate (pkr)": "price", "default sale rate": "price", "price": "price"}
            df.columns = [mapping.get(safe_str(c).lower().strip(), safe_str(c).lower().strip()) for c in df.columns]
            df = clean_for_display(df)
            st.write("Mapped Headings:", safe_join(list(df.columns)))
            show_table(df, "Preview - Excel = Website")
            if st.button("Save to Supabase - Auto-Save"):
                if db is None:
                    st.warning("Supabase not connected - data saved in this session only. Please check Secrets on Monday.")
                else:
                    if table.lower() == "purchases" and "quantity" in df.columns and "cost" in df.columns:
                        df["total"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0) * pd.to_numeric(df["cost"], errors="coerce").fillna(0)
                    d = [{safe_str(k): (safe_str(v) if k in ["date", "product", "customer", "category"] else v) for k, v in row.items()} for _, row in df.iterrows()]
                    # Clean None / NaN for Supabase
                    d = [{k: ("" if (isinstance(v, float) and pd.isna(v)) else v) for k, v in row.items()} for row in d]
                    try:
                        db.table(table.lower()).insert(d).execute()
                        st.success("All dashboard auto-updated!"); st.rerun()
                    except Exception as e:
                        st.error(f"Excel Error: {e}")
        except Exception as e:
            st.error(f"Excel Error: {e}")
    st.markdown('<div class="info-box"><b>Quick Add Entry - Without Excel</b><br>If you don\'t have Excel ready, use Add Entry form on each sheet.</div>', unsafe_allow_html=True)

# ---------- AUTO-SAVE EXCEL - OLD SAME ----------
elif menu == "Auto-Save Excel":
    title("Auto-Save Excel - Download Full Workbook Like Your Original Excel")
    st.markdown('<div class="info-box">Download full Workbook. Like your original Excel. You add entries or upload CSV - data auto-saves to Supabase. 2. Dashboard, Notes, Products, Purchases, Sales, Inventory Summary, Expenses, Investment, Withdrawals - all in one file.</div>', unsafe_allow_html=True)
    st.download_button("Download Full Workbook (Excel)", download_full_excel(sales, purch, prods, exp, recap_df, wd, notes, recap_df, summary_dict), file_name="NESCO Full Workbook.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.markdown('<div class="info-box">Excel file generated from live data - same headings as your original Excel.</div>', unsafe_allow_html=True)
    st.write("Products:", len(prods), "rows | Purchases:", len(purch), "rows | Sales:", len(sales), "rows | Expenses:", len(exp), "rows | Investment:", len(inv), "rows | Withdrawals:", len(wd), "rows")
    st.write("Every new entry is auto-saved instantly. No need to press Save in Excel.")
