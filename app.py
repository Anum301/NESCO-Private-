import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

st.set_page_config(page_title="NESCO - Private", layout="wide")

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔒 NESCO - Private")
    st.write("Sirf authorized person ke liye hai.")
    pw = st.text_input("Password likhein", type="password")
    if st.button("Login"):
        if pw == st.secrets.get("APP_PASSWORD", "Nesco123"):
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Ghalat password!")
    st.stop()

@st.cache_resource
def get_db():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        return None

db = get_db()

def load(table):
    if db is None: return pd.DataFrame()
    try:
        res = db.table(table).select("*").order("id", desc=True).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def save(table, data):
    try:
        db.table(table).insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

st.sidebar.title("💙 NESCO")
menu = st.sidebar.radio("Menu", ["Business Overview", "Sales + Debtors", "Purchases", "Products & Stock", "Inventory Summary", "Expenses", "Investment", "Withdrawals", "Reports & Graphs", "Notes", "Excel Upload"])
st.sidebar.success("Private Mode: ON 🔒")
if st.sidebar.button("Logout"):
    st.session_state.login = False
    st.rerun()

sales = load("sales"); purch = load("purchases"); prods = load("products")
exps = load("expenses"); inv = load("investment"); wd = load("withdrawals"); notes = load("notes")

if menu == "Business Overview":
    st.title("Business Overview")
    total_sales = sales["total"].sum() if "total" in sales else 0
    total_out = sales["outstanding"].sum() if "outstanding" in sales else 0
    total_exp = exps["amount"].sum() if "amount" in exps else 0
    total_inv = inv["amount"].sum() if "amount" in inv else 0
    total_wd = wd["amount"].sum() if "amount" in wd else 0
    profit = total_sales - total_exp
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Sales", f"Rs {total_sales:,.0f}")
    c2.metric("Udhaar / Outstanding", f"Rs {total_out:,.0f}")
    c3.metric("Profit", f"Rs {profit:,.0f}")
    c4.metric("Total Investment", f"Rs {total_inv:,.0f}")
    c1,c2 = st.columns(2)
    c1.metric("Total Expenses", f"Rs {total_exp:,.0f}")
    c2.metric("Total Withdrawals", f"Rs {total_wd:,.0f}")

elif menu == "Sales + Debtors":
    st.title("Sales + Debtors")
    search = st.text_input("Search Customer / Product")
    df = sales.copy()
    if search and not df.empty:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)]
    st.dataframe(df, use_container_width=True)
    if not df.empty:
        st.download_button("Is Page ka CSV Download", df.to_csv(index=False), "sales.csv")
    with st.form("add_sale"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date"); cust = c2.text_input("Customer"); prod = c3.text_input("Product")
        qty = c1.number_input("Qty", min_value=1, value=1); price = c2.number_input("Price", min_value=0.0); recv = c3.number_input("Received", min_value=0.0)
        if st.form_submit_button("Save Sale"):
            total = qty*price
            if save("sales", {"date": str(d), "customer": cust, "product": prod, "quantity": qty, "price": price, "total": total, "received": recv, "outstanding": total-recv}):
                st.success("Saved!"); st.rerun()

elif menu == "Purchases":
    st.title("Purchases")
    st.dataframe(purch, use_container_width=True)
    if not purch.empty: st.download_button("CSV Download", purch.to_csv(index=False), "purchases.csv")
    with st.form("add_p"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date"); sup = c2.text_input("Supplier"); prod = c3.text_input("Product")
        qty = c1.number_input("Qty", min_value=1, value=1); cost = c2.number_input("Cost per unit", min_value=0.0)
        if st.form_submit_button("Save Purchase"):
            if save("purchases", {"date": str(d), "supplier": sup, "product": prod, "quantity": qty, "cost": cost, "total": qty*cost}):
                st.success("Saved!"); st.rerun()

elif menu == "Products & Stock":
    st.title("Products & Stock")
    if not prods.empty:
        def color_stock(row):
            return ["background-color: #ffcccc" if row["stock"] < 10 else "" for _ in row]
        st.dataframe(prods.style.apply(color_stock, axis=1), use_container_width=True)
        st.warning("Red wali line = LOW STOCK! Stock 10 se kam hai.")
        st.download_button("CSV Download", prods.to_csv(index=False), "products.csv")
    with st.form("add_prod"):
        c1,c2,c3,c4 = st.columns(4)
        p = c1.text_input("Product"); cat = c2.text_input("Category"); pr = c3.number_input("Price", min_value=0.0); stk = c4.number_input("Stock", min_value=0, value=0)
        if st.form_submit_button("Save Product"):
            if save("products", {"product": p, "category": cat, "price": pr, "stock": stk}):
                st.success("Saved!"); st.rerun()

elif menu == "Inventory Summary":
    st.title("Inventory Summary")
    if not prods.empty and "stock" in prods and "price" in prods:
        prods["value"] = prods["stock"] * prods["price"]
        st.metric("Total Stock Value", f"Rs {prods['value'].sum():,.0f}")
        st.metric("Total Items in Stock", f"{prods['stock'].sum():,.0f}")
        st.dataframe(prods, use_container_width=True)
        st.download_button("CSV Download", prods.to_csv(index=False), "inventory.csv")
    else:
        st.info("Abhi koi product nahi hai.")

elif menu == "Expenses":
    st.title("Expenses")
    st.dataframe(exps, use_container_width=True)
    if not exps.empty: st.download_button("CSV Download", exps.to_csv(index=False), "expenses.csv")
    with st.form("add_exp"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date"); e = c2.text_input("Expense"); a = c3.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Save Expense"):
            if save("expenses", {"date": str(d), "expense": e, "amount": a}):
                st.success("Saved!"); st.rerun()

elif menu == "Investment":
    st.title("Investment")
    st.dataframe(inv, use_container_width=True)
    if not inv.empty: st.download_button("CSV Download", inv.to_csv(index=False), "investment.csv")
    with st.form("add_inv"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date"); o = c2.text_input("Owner"); a = c3.number_input("Amount", min_value=0.0)
        nt = st.text_input("Note")
        if st.form_submit_button("Save Investment"):
            if save("investment", {"date": str(d), "owner": o, "amount": a, "note": nt}):
                st.success("Saved!"); st.rerun()

elif menu == "Withdrawals":
    st.title("Withdrawals")
    st.dataframe(wd, use_container_width=True)
    if not wd.empty: st.download_button("CSV Download", wd.to_csv(index=False), "withdrawals.csv")
    with st.form("add_wd"):
        c1,c2,c3 = st.columns(3)
        d = c1.date_input("Date"); p = c2.text_input("Person"); a = c3.number_input("Amount", min_value=0.0)
        nt = st.text_input("Note")
        if st.form_submit_button("Save Withdrawal"):
            if save("withdrawals", {"date": str(d), "person": p, "amount": a, "note": nt}):
                st.success("Saved!"); st.rerun()

elif menu == "Reports & Graphs":
    st.title("Reports & Graphs")
    if not sales.empty and "total" in sales:
        fig = px.bar(sales, x="product", y="total", title="Sales by Product", color="product")
        st.plotly_chart(fig, use_container_width=True)
    if not exps.empty:
        fig2 = px.pie(exps, names="expense", values="amount", title="Expenses Breakdown")
        st.plotly_chart(fig2, use_container_width=True)
    if not prods.empty:
        fig3 = px.bar(prods, x="product", y="stock", title="Stock Level", color="product")
        st.plotly_chart(fig3, use_container_width=True)

elif menu == "Notes":
    st.title("Notes / How-To")
    st.dataframe(notes, use_container_width=True)
    with st.form("add_note"):
        t = st.text_input("Title"); n = st.text_area("Note")
        if st.form_submit_button("Save Note"):
            if save("notes", {"title": t, "note": n}):
                st.success("Saved!"); st.rerun()

elif menu == "Excel Upload":
    st.title("Excel Upload")
    st.write("Excel mein columns ka naam aisa rakho: customer, product, quantity, price, received ya product, category, price, stock")
    table = st.selectbox("Kis Table mein daalna hai?", ["sales", "purchases", "products", "expenses", "investment", "withdrawals"])
    file = st.file_uploader("Excel File Upload Karo", type=["xlsx", "csv"])
    if file is not None:
        try:
            df = pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file)
            st.dataframe(df)
            if st.button("Supabase Mein Save Karo"):
                if table == "sales" and "quantity" in df.columns and "price" in df.columns:
                    df["total"] = df["quantity"] * df["price"]
                    if "received" in df.columns:
                        df["outstanding"] = df["total"] - df["received"]
                for _, row in df.iterrows():
                    d = row.to_dict()
                    d = {k: (None if pd.isna(v) else v) for k,v in d.items()}
                    if "date" in d and d["date"] is not None:
                        d["date"] = str(pd.to_datetime(d["date"]).date())
                    db.table(table).insert(d).execute()
                st.success("Sab save ho gaya!"); st.rerun()
        except Exception as e:
            st.error(f"Excel Error: {e}")