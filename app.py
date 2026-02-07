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
# CONFIG & MULTI-BUSINESS SETUP
# ===============================
USER_FILE = "users.csv"
BIZ_LIST_FILE = "businesses.csv" 
NEW_PASSWORD = "Habibur@98"
COLS = ["ID", "তারিখ", "বিবরণ", "ধরণ", "পরিমাণ/সংখ্যা", "দর", "মোট টাকা", "মাধ্যম", "মন্তব্য"]

if not os.path.exists(USER_FILE):
    pd.DataFrame([{"username":"admin", "password":NEW_PASSWORD}]).to_csv(USER_FILE, index=False)

if not os.path.exists(BIZ_LIST_FILE):
    pd.DataFrame(["Default_Business"], columns=["biz_name"]).to_csv(BIZ_LIST_FILE, index=False)

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
        if u.strip() == "admin" and p.strip() == NEW_PASSWORD:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("❌ Username বা Password ভুল")

if not st.session_state.login:
    login_page()
    st.stop()

# ===============================
# BUSINESS SELECTION LOGIC
# ===============================
st.sidebar.title("🏢 ব্যবসা ম্যানেজমেন্ট")

biz_df = pd.read_csv(BIZ_LIST_FILE)
all_biz = biz_df["biz_name"].tolist()

selected_biz = st.sidebar.selectbox("আপনার ব্যবসা বেছে নিন", all_biz)

# --- নতুন অংশ: এডিট এবং ডিলিট অপশন ---
with st.sidebar.expander("⚙️ ব্যবসা এডিট/ডিলিট করুন"):
    edit_biz_name = st.text_input("নতুন নাম দিন", value=selected_biz)
    
    col_edit, col_del = st.columns(2)
    
    # এডিট বা রিনেম অপশন
    if col_edit.button("📝 নাম পরিবর্তন"):
        if edit_biz_name and edit_biz_name != selected_biz:
            new_biz_clean = edit_biz_name.replace(" ", "_")
            
            # CSV ফাইলে নাম পরিবর্তন
            biz_df.loc[biz_df["biz_name"] == selected_biz, "biz_name"] = new_biz_clean
            biz_df.to_csv(BIZ_LIST_FILE, index=False)
            
            # পুরনো ফাইল থাকলে রিনেম করা
            if os.path.exists(f"{selected_biz}_finance.csv"):
                os.rename(f"{selected_biz}_finance.csv", f"{new_biz_clean}_finance.csv")
            if os.path.exists(f"{selected_biz}_recyclebin.csv"):
                os.rename(f"{selected_biz}_recyclebin.csv", f"{new_biz_clean}_recyclebin.csv")
                
            st.success("নাম পরিবর্তিত হয়েছে!")
            st.rerun()

    # ডিলিট অপশন
    if col_del.button("🗑️ ব্যবসা ডিলিট"):
        if len(all_biz) > 1: # সব ব্যবসা ডিলিট করা যাবে না
            # লিস্ট থেকে বাদ দেওয়া
            biz_df = biz_df[biz_df["biz_name"] != selected_biz]
            biz_df.to_csv(BIZ_LIST_FILE, index=False)
            
            # ফাইলগুলো ডিলিট করা
            if os.path.exists(f"{selected_biz}_finance.csv"):
                os.remove(f"{selected_biz}_finance.csv")
            if os.path.exists(f"{selected_biz}_recyclebin.csv"):
                os.remove(f"{selected_biz}_recyclebin.csv")
                
            st.warning(f"{selected_biz} ডিলিট হয়েছে!")
            st.rerun()
        else:
            st.error("সব শেষ ব্যবসা ডিলিট করা যাবে না।")

# নতুন ব্যবসা যোগ করার অপশন
with st.sidebar.expander("➕ নতুন ব্যবসা যোগ করুন"):
    new_biz_name = st.text_input("ব্যবসার নাম")
    if st.button("নিশ্চিত করুন"):
        if new_biz_name and new_biz_name not in all_biz:
            new_biz_clean = new_biz_name.replace(" ", "_")
            new_row = pd.DataFrame([new_biz_clean], columns=["biz_name"])
            pd.concat([biz_df, new_row], ignore_index=True).to_csv(BIZ_LIST_FILE, index=False)
            st.success(f"{new_biz_name} তৈরি হয়েছে!")
            st.rerun()

# ডাইনামিক ফাইল পাথ সেট করা
DATA_FILE = f"{selected_biz}_finance.csv"
RECYCLE_FILE = f"{selected_biz}_recyclebin.csv"

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLS).to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
if not os.path.exists(RECYCLE_FILE):
    pd.DataFrame(columns=COLS).to_csv(RECYCLE_FILE, index=False, encoding='utf-8-sig')

# ===============================
# বাকি কোড (LOAD, CLEAN, UI, DISPLAY ইত্যাদি সব আগের মতোই)
# ===============================
df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
rb_df = pd.read_csv(RECYCLE_FILE, encoding='utf-8-sig')

def clean_df(target_df):
    for col in COLS:
        if col not in target_df.columns:
            target_df[col] = 0.0 if col in ["পরিমাণ/সংখ্যা", "দর", "মোট টাকা"] else ""
    target_df["ID"] = pd.to_numeric(target_df["ID"], errors="coerce").fillna(0).astype(int)
    target_df["পরিমাণ/সংখ্যা"] = pd.to_numeric(target_df["পরিমাণ/সংখ্যা"], errors="coerce").fillna(0.0).astype(float)
    target_df["দর"] = pd.to_numeric(target_df["দর"], errors="coerce").fillna(0.0).astype(float)
    target_df["মোট টাকা"] = pd.to_numeric(target_df["মোট টাকা"], errors="coerce").fillna(0.0).astype(float)
    return target_df

df = clean_df(df)
rb_df = clean_df(rb_df)

st.set_page_config(page_title=f"{selected_biz} - হিসাব", layout="wide")
st.title(f"📊 {selected_biz.replace('_', ' ')} - হিসাব")

st.sidebar.divider()
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
    
    other_method = st.text_input("অন্যান্য মাধ্যম (প্রয়োজনে)", "")
    f_note = st.text_area("মন্তব্য", value=note_v if is_edit else "")
    
    save = st.form_submit_button("💾 Save")

if save:
    final_method = other_method if method == "অন্যান্য" and other_method else method
    total = float(f_qty * f_rate)

    if is_edit:
        update_data = [str(f_date), f_desc, f_type, float(f_qty), float(f_rate), total, final_method, f_note]
        df.loc[df["ID"] == selected, COLS[1:]] = update_data
    else:
        new_id = int(df["ID"].max() + 1) if not df.empty else 1
        new_row = pd.DataFrame([[new_id, str(f_date), f_desc, f_type, float(f_qty), float(f_rate), total, final_method, f_note]], columns=COLS)
        df = pd.concat([df, new_row], ignore_index=True)

    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
    st.sidebar.success("✅ সেভ হয়েছে")
    st.rerun()

search = st.text_input(f"🔍 {selected_biz.replace('_', ' ')} এর তথ্য সার্চ করুন")
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

st.divider()
st.subheader(f"♻️ Recycle Bin ({selected_biz.replace('_', ' ')})")
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