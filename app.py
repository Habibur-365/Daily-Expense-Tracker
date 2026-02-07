import streamlit as st
import pandas as pd
import os

# ===============================
# Bangladesh Money Formatter
# ===============================
def bd_money(x):
    try:
        x = float(x)
    except:
        return x
    sign = "-" if x < 0 else ""
    x = abs(x)
    integer, dec = f"{x:.2f}".split(".")
    if len(integer) > 3:
        last3 = integer[-3:]
        rest = integer[:-3]
        rest = ",".join([rest[max(i-2,0):i] for i in range(len(rest),0,-2)][::-1])
        integer = rest + "," + last3
    return f"৳ {sign}{integer}.{dec}"

# ===============================
# CONFIG
# ===============================
DATA_FILE = "finance.csv"
RECYCLE_FILE = "recyclebin.csv"
USER_FILE = "users.csv"
NEW_PASSWORD = "Habibur@98"
COLS = ["ID", "তারিখ", "বিবরণ", "ধরণ", "পরিমাণ/সংখ্যা", "দর", "মোট টাকা", "মাধ্যম", "মন্তব্য"]

# ===============================
# INIT FILES
# ===============================
if not os.path.exists(USER_FILE):
    pd.DataFrame([{"username":"admin", "password":NEW_PASSWORD}]).to_csv(USER_FILE, index=False)

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLS).to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

if not os.path.exists(RECYCLE_FILE):
    pd.DataFrame(columns=COLS).to_csv(RECYCLE_FILE, index=False, encoding='utf-8-sig')

# ===============================
# LOGIN
# ===============================
if "login" not in st.session_state:
    st.session_state.login = False

def login_page():
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        users = pd.read_csv(USER_FILE, dtype=str)
        if ((users["username"] == u.strip()) & (users["password"] == p.strip())).any():
            st.session_state.login = True
            st.rerun()
        else:
            st.error("❌ Username বা Password ভুল")

if not st.session_state.login:
    login_page()
    st.stop()

# ===============================
# LOAD & CLEAN DATA
# ===============================
df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
rb_df = pd.read_csv(RECYCLE_FILE, encoding='utf-8-sig')

# Data Type Enforcement (ভবিষ্যতের এরর এড়ানোর জন্য)
def clean_df(target_df):
    for col in COLS:
        if col not in target_df.columns:
            target_df[col] = 0.0 if col in ["পরিমাণ/সংখ্যা", "দর", "মোট টাকা"] else ""
    
    # টাইপ কাস্টিং
    target_df["ID"] = pd.to_numeric(target_df["ID"], errors="coerce").fillna(0).astype(int)
    target_df["পরিমাণ/সংখ্যা"] = pd.to_numeric(target_df["পরিমাণ/সংখ্যা"], errors="coerce").fillna(0.0).astype(float)
    target_df["দর"] = pd.to_numeric(target_df["দর"], errors="coerce").fillna(0.0).astype(float)
    target_df["মোট টাকা"] = pd.to_numeric(target_df["মোট টাকা"], errors="coerce").fillna(0.0).astype(float)
    return target_df

df = clean_df(df)
rb_df = clean_df(rb_df)

# ===============================
# UI SETUP
# ===============================
st.set_page_config("দৈনিক জমা খরচ", layout="wide")
st.title("📊 দৈনিক জমা-খরচ হিসাব")

# ===============================
# SIDEBAR ENTRY / EDIT
# ===============================
st.sidebar.header("➕ নতুন এন্ট্রি / ✏️ এডিট")
options = ["নতুন এন্ট্রি"] + (df["ID"].tolist() if not df.empty else [])
selected = st.sidebar.selectbox("আইডি নির্বাচন করুন", options)

is_edit = selected != "নতুন এন্ট্রি"

if is_edit:
    r = df[df["ID"] == selected].iloc[0]
    d, t, desc_v = pd.to_datetime(r["তারিখ"]).date(), r["ধরণ"], r["বিবরণ"]
    qty_v, rate_v, method_v, note_v = r["পরিমাণ/সংখ্যা"], r["দর"], r["মাধ্যম"], r["মন্তব্য"]
else:
    d, t, desc_v, qty_v, rate_v, method_v, note_v = (
        pd.Timestamp.now().date(), "ব্যয় (খরচ)", "", 1.0, 0.0, "নগদ", ""
    )

with st.sidebar.form("entry_form", clear_on_submit=True):
    f_date = st.date_input("তারিখ", d)
    f_type = st.selectbox("ধরণ", ["আয় (জমা)", "ব্যয় (খরচ)"], index=0 if t == "আয় (জমা)" else 1)
    f_desc = st.text_input("বিবরণ", value=desc_v if is_edit else "")
    f_qty = st.number_input("পরিমাণ", value=float(qty_v))
    f_rate = st.number_input("দর", value=float(rate_v))
    
    method_list = ["নগদ", "ব্যাংক", "বিকাশ", "অন্যান্য"]
    m_index = method_list.index(method_v) if method_v in method_list else 0
    method = st.selectbox("মাধ্যম", method_list, index=m_index)
    
    other_method = st.text_input("অন্যান্য মাধ্যম (প্রয়োজনে)", "")
    f_note = st.text_area("মন্তব্য", value=note_v if is_edit else "")
    
    save = st.form_submit_button("💾 Save")

if save:
    final_method = other_method if method == "অন্যান্য" and other_method else method
    total = float(f_qty * f_rate)

    if is_edit:
        # FutureWarning fix: এডিট করার সময় টাইপ ঠিক রাখা
        update_data = [str(f_date), f_desc, f_type, float(f_qty), float(f_rate), total, final_method, f_note]
        df.loc[df["ID"] == selected, COLS[1:]] = update_data
    else:
        new_id = int(df["ID"].max() + 1) if not df.empty else 1
        new_row = pd.DataFrame([[new_id, str(f_date), f_desc, f_type, float(f_qty), float(f_rate), total, final_method, f_note]], columns=COLS)
        df = pd.concat([df, new_row], ignore_index=True)

    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
    st.sidebar.success("✅ সেভ হয়েছে")
    st.rerun()

# ===============================
# DISPLAY
# ===============================
search = st.text_input("🔍 তারিখ বা বিবরণ লিখে সার্চ করুন")
show = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)] if search else df

income = show[show["ধরণ"] == "আয় (জমা)"]["মোট টাকা"].sum()
expense = show[show["ধরণ"] == "ব্যয় (খরচ)"]["মোট টাকা"].sum()

c1, c2, c3 = st.columns(3)
c1.metric("🟢 মোট জমা", bd_money(income))
c2.metric("🔴 মোট খরচ", bd_money(expense))
c3.metric("💰 অবশিষ্ট টাকা", bd_money(income - expense))

display = show.copy()
display["দর"] = display["দর"].apply(bd_money)
display["মোট টাকা"] = display["মোট টাকা"].apply(bd_money)

col1, col2 = st.columns(2)
with col1:
    st.subheader("🟢 জমা")
    st.dataframe(display[display["ধরণ"] == "আয় (জমা)"].drop(columns=["ধরণ"]), hide_index=True, width='stretch')

with col2:
    st.subheader("🔴 খরচ")
    st.dataframe(display[display["ধরণ"] == "ব্যয় (খরচ)"].drop(columns=["ধরণ"]), hide_index=True, width='stretch')

# ===============================
# DELETE → RECYCLE BIN
# ===============================
st.divider()
if not df.empty:
    did = st.selectbox("ডিলিট করার আইডি নির্বাচন করুন", df["ID"])
    if st.button("❌ নিশ্চিত ডিলিট করুন"):
        row_to_delete = df[df["ID"] == did]
        rb_df = pd.concat([rb_df, row_to_delete], ignore_index=True)
        rb_df.to_csv(RECYCLE_FILE, index=False, encoding='utf-8-sig')
        df = df[df["ID"] != did]
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        st.warning("🗑️ Recycle Bin এ পাঠানো হয়েছে")
        st.rerun()

# ===============================
# RECYCLE BIN (Restore & Permanent Delete)
# ===============================
st.divider()
st.subheader("♻️ Recycle Bin")
if rb_df.empty:
    st.info("Recycle Bin খালি")
else:
    rid = st.selectbox("Recycle ID", rb_df["ID"])
    c_r1, c_r2 = st.columns(2)
    with c_r1:
        if st.button("♻️ Restore"):
            row_to_restore = rb_df[rb_df["ID"] == rid]
            df = pd.concat([df, row_to_restore], ignore_index=True)
            df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            rb_df = rb_df[rb_df["ID"] != rid]
            rb_df.to_csv(RECYCLE_FILE, index=False, encoding='utf-8-sig')
            st.success("Restore হয়েছে")
            st.rerun()
    with c_r2:
        confirm = st.checkbox("আমি নিশ্চিত Permanent Delete করবো")
        if st.button("🧹 Permanent Delete") and confirm:
            rb_df = rb_df[rb_df["ID"] != rid]
            rb_df.to_csv(RECYCLE_FILE, index=False, encoding='utf-8-sig')
            st.error("Permanent Delete সম্পন্ন")
            st.rerun()