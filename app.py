import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import date

st.set_page_config(page_title="NESCO Distributors - Business Dashboard", layout="wide", page_icon="💙")

# --- EXCEL JESA BLUE THEME + FINANCE BOXES ---
st.markdown("""
<style>
.stApp { background: #EAF0F6; }
h1,h2,h3 { color: #0B2F4A !important; }
.blue-bar { background: #0B2F4A; color: white !important; padding: 12px 16px; border-radius: 8px; font-weight: 800; font-size: 18px; margin: 16px 0 10px 0; }
.blue-bar * { color: white !important; }
.finance-box { background: white; border: 2px solid #0B2F4A; border-radius: 12px; padding: 14px; text-align: center; box-shadow: 0 0 18px rgba(11,47,74,0.18); }
.finance-box .label { color: #0B2F4A !important; font-size: 13px; font-weight: 700; text-transform: uppercase; }
.finance-box .value { color: #0B2F4A !important; font-size: 26px; font-weight: 900; }
.stButton>button { background: #0B2F4A !important; color: white !important; font-weight: 800 !important; border-radius: 10px !important; }
.stDownloadButton>button { background: #00A67C !important; color: white !important; font-weight: 800 !important; border-radius: 10px !important; }
section[data-testid="stSidebar"] { background: #0B2F4A !important; }
section[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if "login" not in st.session_state: st.session_state.login = False
if not st.session_state.login:
    st.markdown("<div class='blue-bar' style='text-align:center'>🔒 NESCO - Private</div>", unsafe_allow_html=True)
    st.write("Sirf authorized person ke liye hai.")
    pw = st.text_input("Password likhein", type="password")
    if st.button("Login"):
        if pw == st.secrets.get("APP_PASSWORD", "Nesco123"):
            st.session_state.login = True; st.rerun()
        else: st.error("Ghalat password!")
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

def export_csv(df, filename):
    if df is not None and not df.empty:
        st.download_button("⬇️ Export CSV", df.to_csv(index=False), filename, "text/csv")

# --- CALCULATIONS : WEIGHTED AVG COST ---
def calc_avg_cost(purch):
    # Product -> Avg Cost = Total Cost / Total Qty Purchased
    if purch.empty or "product" not in purch: return {}
    d = {}
    for prod, g in purch.groupby("product"):
        qty = pd.to_numeric(g["quantity"], errors="coerce").fillna(0).sum() if "quantity" in g else 0
        # purchases me column total ya cost*quantity
        if "total" in g: total = pd.to_numeric(g["total"], errors="coerce").fillna(0).sum()
        else: total = 0
        d[prod] = (total / qty) if qty else 0
    return d

def calc_sales_enriched(sales, avg_map, prods):
    if sales.empty: return sales.copy()
    df = sales.copy()
    # Default rate from Products
    prod_rate = {}
    if not prods.empty and "product" in prods:
        for _, r in prods.iterrows():
            # products me price ya default_sale_rate
            rate = r.get("price", r.get("default_sale_rate", 0))
            prod_rate[r["product"]] = float(rate) if pd.notna(rate) else 0
    for c in ["quantity","price","discount","rate_override","received"]:
        if c not in df: df[c] = 0
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0)
    df["rate_override"] = pd.to_numeric(df["rate_override"], errors="coerce").fillna(0)
    df["received"] = pd.to_numeric(df["received"], errors="coerce").fillna(0)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    # Effective Rate = Rate Override if >0 else Sale Rate else Product Default
    def eff_rate(row):
        if row["rate_override"] and row["rate_override"] > 0: return row["rate_override"]
        if row["price"] and row["price"] > 0: return row["price"]
        return prod_rate.get(row.get("product",""), 0)
    df["effective_rate"] = df.apply(eff_rate, axis=1)
    df["avg_cost"] = df["product"].map(avg_map).fillna(0)
    df["revenue"] = df["quantity"] * df["effective_rate"] - df["discount"]
    df["total"] = df["revenue"]  # dashboard ke liye
    df["cogs"] = df["quantity"] * df["avg_cost"]
    df["profit"] = df["revenue"] - df["cogs"]
    df["margin"] = df.apply(lambda r: (r["profit"]/r["revenue"]*100) if r["revenue"] else 0, axis=1)
    df["outstanding"] = df["revenue"] - df["received"]
    df["payment_status"] = df.apply(lambda r: "Paid" if r["outstanding"] <= 0 else ("Partial" if r["received"]>0 else "Unpaid"), axis=1)
    return df

# --- SIDEBAR = EXCEL SHEETS JAISE ---
st.sidebar.title("💙 NESCO Distributors")
menu = st.sidebar.radio("Sheets", ["Dashboard","Notes","Products","Purchases","Sales","Inventory Summary","Expenses","Investment","Withdrawals","Excel Upload"])
st.sidebar.success("Private Mode: ON 🔒")
if st.sidebar.button("Logout"): st.session_state.login = False; st.rerun()

sales_raw = load("sales"); purch = load("purchases"); prods = load("products")
exps = load("expenses"); inv = load("investment"); wd = load("withdrawals"); notes = load("notes")
avg_map = calc_avg_cost(purch)
sales = calc_sales_enriched(sales_raw, avg_map, prods)

# Totals for Dashboard
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
# Cash = Capital + Received - Purchases - Expenses - Withdrawals
cash_on_hand = total_inv_amt + total_received - total_purch_cost - total_exp - total_wd

# --- DASHBOARD ---
if menu == "Dashboard":
    st.markdown("<div class='blue-bar'>NESCO Distributors - Business Dashboard</div>", unsafe_allow_html=True)
    st.write("Summary - everything follows automatically from the Purchases, Sales, Expenses, Investment and Products sheets.")
    bar("OVERALL BUSINESS SUMMARY")
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

    bar("CASH POSITION")
    c1,c2,c3 = st.columns(3)
    with c1: box("Cash on Hand", f"Rs {cash_on_hand:,.0f}")
    with c2: box("Cash Collected (Received)", f"Rs {total_received:,.0f}")
    with c3: box("Total Withdrawn", f"Rs {total_wd:,.0f}")

    # Time filters like Excel: Latest Day, Last 7 Days, Month to Date, Year to Date
    bar("LATEST DAY SNAPSHOT / LAST 7 DAYS / MONTH TO DATE / YEAR TO DATE")
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

    bar("PER PRODUCT RECAP")
    if not sales.empty and "product" in sales:
        recap = sales.groupby("product").agg(Total_Revenue=("revenue","sum"), Total_Profit=("profit","sum"), Total_Qty_Sold=("quantity","sum")).reset_index()
        purch_g = purch.groupby("product").agg(Total_Qty_Purchased=("quantity","sum")).reset_index() if not purch.empty and "product" in purch else pd.DataFrame()
        recap = recap.merge(purch_g, on="product", how="left").fillna(0)
        recap["Remaining Stock"] = recap["Total_Qty_Purchased"] - recap["Total_Qty_Sold"]
        recap["Avg Cost/Unit"] = recap["product"].map(avg_map).fillna(0)
        recap["Remaining Value"] = recap["Remaining Stock"] * recap["Avg Cost/Unit"]
        recap["Margin %"] = recap.apply(lambda r: (r["Total_Profit"]/r["Total_Revenue"]*100) if r["Total_Revenue"] else 0, axis=1)
        st.dataframe(recap, use_container_width=True)
        export_csv(recap, "per_product_recap.csv")

    bar("LEGEND & HOW THE CALCULATIONS WORK")
    st.info("Weighted Avg Cost = Total Purchase Cost / Total Qty Purchased - har product ka alag. COGS = Qty Sold x Avg Cost. Revenue = (Qty x Final Rate) - Discount. Final Rate = Rate Override (agar diya ho) warna Default Sale Rate. Gross Profit = Revenue - COGS. Margin = Profit / Revenue. Outstanding = Revenue - Received. Cash = Capital + Received - Purchases - Expenses - Withdrawals.")

# --- NOTES ---
elif menu == "Notes":
    bar("Notes & How-To Guide")
    st.write("Is sheet me har number kaise banta hai, wo likha hai. Date alag se hai.")
    if not notes.empty and "date" in notes:
        sel = st.date_input("Filter by Date", value=None)
        dfn = notes.copy()
        if sel: dfn = dfn[dfn["date"].astype(str)==str(sel)]
        st.dataframe(dfn, use_container_width=True); export_csv(dfn, "notes.csv")
    else:
        st.dataframe(notes, use_container_width=True); export_csv(notes, "notes.csv")
    with st.form("add_note"):
        c1,c2 = st.columns(2)
        d = c1.date_input("Note Date", value=date.today()); t = c2.text_input("Title")
        n = st.text_area("Note")
        if st.form_submit_button("Save Note"):
            if save("notes", {"date": str(d), "title": t, "note": n}): st.success("Saved!"); st.rerun()

# --- PRODUCTS ---
elif menu == "Products":
    bar("Products")
    st.write("Master product list - add a new row first when stocking a new product.")
    cols = ["product","category","price","notes"] if not prods.empty else []
    st.dataframe(prods, use_container_width=True); export_csv(prods, "products.csv")
    with st.form("add_prod"):
        c1,c2,c3 = st.columns(3)
        p = c1.text_input("Product Name"); cat = c2.text_input("Category"); rate = c3.number_input("Default Sale Rate (PKR)", min_value=0.0)
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Product"):
            if save("products", {"product": p, "category": cat, "price": rate, "notes": nt}): st.success("Saved!"); st.rerun()

# --- PURCHASES ---
elif menu == "Purchases":
    bar("Purchases")
    st.write("One row per purchase batch. Buying the same product again at a new cost just add another row - average recalculates automatically.")
    st.dataframe(purch, use_container_width=True); export_csv(purch, "purchases.csv")
    with st.form("add_p"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date", value=date.today()); prod = c2.text_input("Product"); qty = c3.number_input("Qty Purchased", min_value=1, value=1)
        cost = c1.number_input("Purchase Cost/Unit (PKR)", min_value=0.0); nt = c2.text_input("Notes")
        if st.form_submit_button("Save Purchase"):
            if save("purchases", {"date": str(d), "product": prod, "quantity": qty, "cost": cost, "total": qty*cost, "notes": nt}): st.success("Saved!"); st.rerun()

# --- SALES ---
elif menu == "Sales":
    bar("Sales")
    st.write("One row per sale. Avg Cost, COGS, Profit and Margin calculate automatically - and so does the total when you enter Amount Received / Outstanding.")
    # Show exact Excel order + 2 new columns at last
    show_cols = ["date","product","customer","quantity","effective_rate","revenue","avg_cost","cogs","profit","margin","received","outstanding","payment_status","discount","rate_override"]
    disp = sales.copy()
    # Rename for display to match Excel headings
    rename = {"date":"Date","product":"Product","customer":"Customer","quantity":"Qty Sold","effective_rate":"Sale Rate (PKR)","revenue":"Revenue (PKR)","avg_cost":"Avg Cost/Unit","cogs":"COGS (PKR)","profit":"Profit (PKR)","margin":"Margin %","received":"Amount Received","outstanding":"Amount Outstanding","payment_status":"Payment Status","discount":"Discount (PKR)","rate_override":"Rate Override"}
    disp = disp[[c for c in show_cols if c in disp.columns]].rename(columns=rename)
    st.dataframe(disp, use_container_width=True); export_csv(disp, "sales.csv")
    if not disp.empty:
        st.plotly_chart(px.bar(sales, x="product", y="revenue", title="Revenue by Product", color="product"), use_container_width=True)
    with st.form("add_sale"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date", value=date.today()); prod = c2.text_input("Product"); cust = c3.text_input("Customer")
        qty = c1.number_input("Qty Sold", min_value=1, value=1)
        rate = c2.number_input("Sale Rate (PKR) - khali ho to Default chalega", min_value=0.0)
        disc = c3.number_input("Discount (PKR)", min_value=0.0)
        override = c1.number_input("Rate Override - agar special rate dena hai to yahan likhein", min_value=0.0)
        recv = c2.number_input("Amount Received", min_value=0.0)
        if st.form_submit_button("Save Sale"):
            # price = manual sale rate, rate_override separate
            if save("sales", {"date": str(d), "product": prod, "customer": cust, "quantity": qty, "price": rate, "discount": disc, "rate_override": override if override>0 else None, "received": recv}):
                st.success("Saved!"); st.rerun()

# --- INVENTORY SUMMARY ---
elif menu == "Inventory Summary":
    bar("Inventory Summary")
    st.write("One row per product, pulled from Purchases and Sales. Nothing here to type - add a product in the Products sheet and it appears here automatically.")
    if not prods.empty:
        rows=[]
        for _, pr in prods.iterrows():
            pname = pr["product"]
            pq = purch[purch["product"]==pname]["quantity"].sum() if not purch.empty and "product" in purch else 0
            sq = sales[sales["product"]==pname]["quantity"].sum() if not sales.empty and "product" in sales else 0
            avgc = avg_map.get(pname, 0)
            rem = pq - sq
            rev = sales[sales["product"]==pname]["revenue"].sum() if not sales.empty else 0
            prof = sales[sales["product"]==pname]["profit"].sum() if not sales.empty else 0
            rows.append({"Product": pname, "Total Qty Purchased": pq, "Total Qty Sold": sq, "Remaining Stock": rem, "Avg Cost/Unit": round(avgc,2), "Remaining Value": round(rem*avgc,2), "Total Revenue": round(rev,2), "Total Profit": round(prof,2), "Margin %": round((prof/rev*100) if rev else 0,2)})
        idf = pd.DataFrame(rows)
        st.dataframe(idf, use_container_width=True); export_csv(idf, "inventory_summary.csv")
    else: st.info("Abhi koi product nahi hai.")

# --- EXPENSES ---
elif menu == "Expenses":
    bar("Expenses")
    st.write("Operating costs - transport, rent, wages, etc. These are NOT part of Purchase Cost.")
    st.dataframe(exps, use_container_width=True); export_csv(exps, "expenses.csv")
    with st.form("add_exp"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date", value=date.today()); e = c2.text_input("Expense"); a = c3.number_input("Amount (PKR)", min_value=0.0)
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Expense"):
            if save("expenses", {"date": str(d), "expense": e, "amount": a, "notes": nt}): st.success("Saved!"); st.rerun()

# --- INVESTMENT ---
elif menu == "Investment":
    bar("Investment")
    st.write("Capital put into the business by each owner/partner.")
    st.dataframe(inv, use_container_width=True); export_csv(inv, "investment.csv")
    st.metric("Total Capital Invested", f"Rs {total_inv_amt:,.0f}")
    with st.form("add_inv"):
        c1,c2,c3 = st.columns(3)
        o = c1.text_input("Investor"); a = c2.number_input("Amount (PKR)", min_value=0.0); d = c3.date_input("Date", value=date.today())
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Investment"):
            if save("investment", {"owner": o, "amount": a, "date": str(d), "note": nt}): st.success("Saved!"); st.rerun()

# --- WITHDRAWALS ---
elif menu == "Withdrawals":
    bar("Withdrawals")
    st.write("Profit taken out of the business for personal use - not an expense.")
    st.dataframe(wd, use_container_width=True); export_csv(wd, "withdrawals.csv")
    st.metric("Total Withdrawn", f"Rs {total_wd:,.0f}")
    with st.form("add_wd"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date", value=date.today()); p = c2.text_input("Withdrawn By"); a = c3.number_input("Amount (PKR)", min_value=0.0)
        nt = st.text_input("Notes")
        if st.form_submit_button("Save Withdrawal"):
            if save("withdrawals", {"date": str(d), "person": p, "amount": a, "note": nt}): st.success("Saved!"); st.rerun()

# --- EXCEL UPLOAD PER SHEET ---
elif menu == "Excel Upload":
    bar("Excel Upload - Data Directly Excel se Website mein")
    st.info("Apni Excel file ka wo sheet upload karo. Headings wahi honi chahiye jo website mein hain. Data seedha Supabase mein jayega aur Dashboard khud update ho jayega.")
    table = st.selectbox("Kis Sheet mein daalna hai?", ["products","purchases","sales","expenses","investment","withdrawals","notes"])
    st.write("Expected Headings:")
    st.code({
        "products": "Product Name, Category, Default Sale Rate (PKR), Notes",
        "purchases": "Date, Product, Qty Purchased, Purchase Cost/Unit (PKR), Notes",
        "sales": "Date, Product, Customer, Qty Sold, Sale Rate (PKR), Discount (PKR), Rate Override, Amount Received",
        "expenses": "Date, Expense, Amount (PKR), Notes",
        "investment": "Investor, Amount (PKR), Date, Notes",
        "withdrawals": "Date, Withdrawn By, Amount (PKR), Notes",
        "notes": "Date, Title, Note"
    }[table])
    file = st.file_uploader("Excel / CSV yahan Drag & Drop karo", type=["xlsx","csv"])
    if file is not None:
        try:
            df = pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file)
            st.write("Original Headings:", list(df.columns))
            # Normalize headings to DB columns
            mapping = {
                "product name":"product","product":"product","category":"category","default sale rate (pkr)":"price","default sale rate":"price","sale rate (pkr)":"price","sale rate":"price","price":"price",
                "date":"date","qty purchased":"quantity","qty sold":"quantity","qty":"quantity","quantity":"quantity",
                "purchase cost/unit (pkr)":"cost","purchase cost":"cost","cost":"cost",
                "customer":"customer","amount received":"received","received":"received","discount (pkr)":"discount","discount":"discount","rate override":"rate_override",
                "expense":"expense","amount (pkr)":"amount","amount":"amount","investor":"owner","owner":"owner","withdrawn by":"person","person":"person","title":"title","note":"note","notes":"notes"
            }
            df.columns = [mapping.get(str(c).strip().lower(), str(c).strip().lower()) for c in df.columns]
            st.write("Mapped Headings:", list(df.columns))
            st.dataframe(df)
            if st.button("Supabase Mein Save Karo"):
                if table=="purchases" and "quantity" in df.columns and "cost" in df.columns:
                    df["total"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0) * pd.to_numeric(df["cost"], errors="coerce").fillna(0)
                for _, row in df.iterrows():
                    d = {k:(None if pd.isna(v) else v) for k,v in row.to_dict().items()}
                    if "date" in d and d["date"] is not None:
                        try: d["date"] = str(pd.to_datetime(d["date"]).date())
                        except: pass
                    # sales: price column se revenue auto nahi, calc dashboard me hota hai
                    db.table(table).insert(d).execute()
                st.success("Sab save ho gaya! Dashboard auto update ho jayega."); st.rerun()
        except Exception as e: st.error(f"Excel Error: {e}")
