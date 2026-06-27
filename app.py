import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- إعدادات الملف وقاعدة البيانات ---
EXCEL_FILE = "net_package_management.xlsx"

# الباقات والثوابت للخط الرئيسي
FIXED_GB = 50.0
FIXED_MINS = 8000
MAX_SUB_LINES = 3

# إنشاء ملف الإكسيل بالأعمدة الجديدة لو لو يكن موجوداً
if not os.path.exists(EXCEL_FILE):
    df_empty = pd.DataFrame(columns=[
        "الشهر", "الخط الرئيسي", "Ana Vodafone Password", "إجمالي جيجات الباقة", "إجمالي دقائق الباقة", 
        "الخط الفرعي", "الحصة المحددة (جيجا)", "الحصة المحددة (دقائق)", "سعر الباقة", "حالة الدفع"
    ])
    df_empty.to_excel(EXCEL_FILE, index=False)

def load_data():
    return pd.read_excel(EXCEL_FILE)

def save_data(df):
    if not df.empty:
        df = df.replace(r'^\s*$', pd.NA, regex=True)
        df = df.replace("None", pd.NA)
        df = df.replace("<NA>", pd.NA)
        df = df.replace("nan", pd.NA)
        
        df = df.dropna(subset=["الخط الرئيسي", "الخط الفرعي"], how="any")
        
        df = df[df["الخط الرئيسي"].astype(str).str.strip() != ""]
        df = df[df["الخط الفرعي"].astype(str).str.strip() != ""]
        df = df.reset_index(drop=True)
        
    df.to_excel(EXCEL_FILE, index=False)

# --- إعدادات الصفحة وجعل الاتجاه من اليمين لليسار RTL ---
st.set_page_config(page_title="Quota Management", layout="wide")

st.markdown("""
    <style>
    body, div, p, h1, h2, h3, h4, h5, h6 {
        direction: rtl;
        text-align: right;
    }
    .stButton button {
        width: 100%;
    }
    .centered-title {
        text-align: center;
        direction: ltr;
        margin-bottom: 2rem;
    }
    /* تنسيق الزر الذكي المحدث لـ Ana Vodafone */
    .app-link-btn {
        display: inline-block;
        width: 98%;
        text-align: center;
        color: white !important;
        padding: 10px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        margin-top: 5px;
        cursor: pointer;
        border: none;
        background-color: #e60000;
    }
    .app-link-btn:hover { background-color: #b30000; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='centered-title'>📱 Quota Management</h1>", unsafe_allow_html=True)

df_data = load_data()

if not df_data.empty:
    if "الشهر" not in df_data.columns: df_data.insert(0, "الشهر", "")
    if "Ana Vodafone Password" not in df_data.columns: df_data.insert(2, "Ana Vodafone Password", "")
    if "سعر الباقة" not in df_data.columns: df_data["سعر الباقة"] = 0.0
    if "حالة الدفع" not in df_data.columns: df_data["حالة الدفع"] = False
    df_data["حالة الدفع"] = df_data["حالة الدفع"].fillna(False).astype(bool)

SHORT_COLUMNS = {
    "الشهر": "الشهر", "الخط الرئيسي": "الرئيسي", "Ana Vodafone Password": "الباسورد",
    "إجمالي جيجات الباقة": "إجمالي جيجا", "إجمالي دقائق الباقة": "إجمالي دقائق",
    "الخط الفرعي": "الفرعي", "الحصة المحددة (جيجا)": "جيجا", "الحصة المحددة (دقائق)": "دقائق",
    "سعر الباقة": "السعر", "حالة الدفع": "الدفع"
}

current_year = datetime.now().year
months_list = [f"{m:02d}-{current_year}" for m in range(1, 13)]
current_month_str = f"{datetime.now().month:02d}-{current_year}"

incomplete_lines = []
if not df_data.empty:
    df_month = df_data[df_data["الشهر"].astype(str) == current_month_str]
    df_month = df_month.dropna(subset=["الخط الرئيسي"])
    unique_mains = df_month["الخط الرئيسي"].unique()
    
    for main in unique_mains:
        if str(main).strip() == "" or str(main) == "nan" or str(main) == "None": continue
        df_sub = df_month[df_month["الخط الرئيسي"] == main]
        df_sub_valid = df_sub[df_sub["الخط الفرعي"].notna()]
        
        sub_count = len(df_sub_valid)
        allocated_gb = df_sub_valid["الحصة المحددة (جيجا)"].sum()
        allocated_mins = df_sub_valid["الحصة المحددة (دقائق)"].sum()
        
        rem_gb = FIXED_GB - allocated_gb
        rem_mins = FIXED_MINS - allocated_mins
        
        if rem_gb > 0 or rem_mins > 0 or sub_count < MAX_SUB_LINES:
            incomplete_lines.append({
                "الخط الرئيسي": main, "الخطوط الفرعية الحالية": sub_count,
                "المتبقي (جيجا)": rem_gb if rem_gb > 0 else 0.0, "المتبقي (دقائق)": rem_mins if rem_mins > 0 else 0,
                "سبب التنبيه": "⚠️ نقص خطوط وباقة" if (sub_count < MAX_SUB_LINES and (rem_gb > 0 or rem_mins > 0)) else ("📞 الفرعي أقل من 3" if sub_count < MAX_SUB_LINES else "📉 عجز بالباقة")
            })

noti_count = len(incomplete_lines)

tab1, tab2, tab3 = st.tabs(["📊 إدارة الخطوط", "🗂️ البيانات", f"🔔 التنبيهات ({noti_count})"])

# --- التاب الأول ---
with tab1:
    col_top1, col_top2 = st.columns([1, 2])
    with col_top1:
        st.markdown("### 📅 اختيار الشهر الحالي")
        default_month_idx = datetime.now().month - 1
        selected_month = st.selectbox("حددي الشهر المستهدف للعمل عليه:", months_list, index=default_month_idx)
    with col_top2:
        st.markdown("### 🔍 البحث السريع")
        search_query = st.text_input("ابحثي برقم الخط الرئيسي أو الرقم الفرعي:")

    if search_query:
        df_search = df_data.fillna("").astype(str)
        filtered_df = df_data[df_search["الخط الرئيسي"].str.contains(search_query, na=False) | df_search["الخط الفرعي"].str.contains(search_query, na=False)]
        if not filtered_df.empty:
            st.dataframe(filtered_df.rename(columns=SHORT_COLUMNS), use_container_width=True, hide_index=True)
            
    st.write("---")
    st.markdown("### 🏢 اختيار الخط الرئيسي")
    
    df_clean_dropdown = df_data.dropna(subset=["الخط الرئيسي", "الخط الفرعي"])
    df_clean_dropdown = df_clean_dropdown[(df_clean_dropdown["الخط الرئيسي"].astype(str).str.strip() != "") & (df_clean_dropdown["الخط الرئيسي"].astype(str) != "nan")]
    existing_mains = df_clean_dropdown["الخط الرئيسي"].unique().tolist()
    existing_mains = [str(int(m)) if isinstance(m, float) and m.is_integer() else str(m) for m in existing_mains]

    options = ["-- اختر خط رئيسي --"] + existing_mains + ["➕ إضافة خط رئيسي جديد..."]
    selected_option = st.selectbox("حدد الخط الرئيسي:", options)

    selected_main_line = ""
    voda_password = ""

    if selected_option == "➕ إضافة خط رئيسي جديد...":
        col_new1, col_new2, col_new3 = st.columns(3)
        with col_new1: selected_main_line = st.text_input("رقم الخط الرئيسي الجديد:")
        with col_new2: voda_password = st.text_input("Ana Vodafone Password:")
        with col_new3: st.text_input("إجمالي جيجابايت الباقة", value=f"{FIXED_GB} جيجا", disabled=True)
    elif selected_option != "-- اختر خط رئيسي --":
        selected_main_line = selected_option
        line_data_saved = df_data[df_data["الخط الرئيسي"].astype(str) == selected_main_line]
        saved_password = str(line_data_saved.iloc[0]["Ana Vodafone Password"]) if "Ana Vodafone Password" in df_data.columns and not line_data_saved.empty else ""
        if saved_password in ["nan", "None"]: saved_password = ""

        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1: st.info(f"📍 **الخط الرئيسي:** {selected_main_line}")
        with col_info2: voda_password = st.text_input("Ana Vodafone Password:", value=saved_password)
        with col_info3: st.text_input("إجمالي جيجابايت الباقة", value=f"{FIXED_GB} جيجا", disabled=True)

        st.write("🛠️ **أدوات التحكم السريع وتطبيق Ana Vodafone:**")
        col_btn_app, col_copy_num, col_copy_pass = st.columns([2, 1, 1])
        
        with col_btn_app:
            # زر أندرويد الذكي الجديد (يحاول الفتح مباشرة عبر كود جافاسكريبت مدمج)
            st.markdown("""
                <button class="app-link-btn" onclick="openAnaVodafone()">🤖 Ana Vodafone</button>
                <script>
                function openAnaVodafone() {
                    // محاولة الفتح المباشر عبر بروتوكول الأندرويد المتقدم لإجبار النظام على الاستجابة
                    var intentUrl = "intent://apps.vodafone.com.eg/#Intent;scheme=http;package=com.vodafone.anakyt;end";
                    var fallbackUrl = "https://play.google.com/store/apps/details?id=com.vodafone.anakyt";
                    
                    var start = Date.now();
                    window.location.href = intentUrl;
                    
                    setTimeout(function() {
                        if (Date.now() - start < 2000) {
                            window.open(fallbackUrl, '_blank');
                        }
                    }, 1500);
                }
                </script>
            """, unsafe_allow_html=True)
            
        with col_copy_num:
            if st.button("📋 نسخ الرقم"):
                st.write(f'<script>navigator.clipboard.writeText("{selected_main_line}");</script>', unsafe_allow_html=True)
                st.toast("📋 تم نسخ رقم الخط الرئيسي!")
        with col_copy_pass:
            if st.button("🔑 نسخ الباسورد"):
                if voda_password:
                    st.write(f'<script>navigator.clipboard.writeText("{voda_password}");</script>', unsafe_allow_html=True)
                    st.toast("🔑 تم نسخ كلمة السر!")
                else: st.warning("لا يوجد باسوورد!")

    if selected_main_line:
        st.write("---")
        df_current_sub = df_data[(df_data["الخط الرئيسي"].astype(str) == selected_main_line) & (df_data["الشهر"].astype(str) == selected_month)]
        df_current_sub = df_current_sub[df_current_sub["الخط الفرعي"].notna()]
        
        total_allocated_gb = df_current_sub["الحصة المحددة (جيجا)"].sum()
        total_allocated_mins = df_current_sub["الحصة المحددة (دقائق)"].sum()
        total_collected_money = df_current_sub[df_current_sub["حالة الدفع"] == True]["سعر الباقة"].sum()
        total_expected_money = df_current_sub["سعر الباقة"].sum()
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: st.metric("المتبقي من الجيجابايت", f"{FIXED_GB - total_allocated_gb} جيجا")
        with col_m2: st.metric("المتبقي من الدقائق", f"{FIXED_MINS - total_allocated_mins} دقيقة")
        with col_m3: st.metric("التحصيل المالي للشهر", f"{total_collected_money} ج.م", f"من {total_expected_money}")

        state_key = f"count_{selected_main_line}_{selected_month}"
        if state_key not in st.session_state: st.session_state[state_key] = max(len(df_current_sub), 1)
            
        existing_subs = df_current_sub.to_dict('records')
        sub_lines_data = []
        input_total_gb, input_total_mins = 0.0, 0
        
        for i in range(st.session_state[state_key]):
            st.write(f"**الخط الفرعي #{i+1}**")
            col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1.5, 1])
            default_sub = str(existing_subs[i]["الخط الفرعي"]) if i < len(existing_subs) else ""
            if default_sub.endswith(".0"): default_sub = default_sub[:-2]
            
            with col1: sub_num = st.text_input(f"رقم الهاتف الفرعي", value=default_sub, key=f"sub_num_{state_key}_{i}")
            with col2: alloc_gb = st.number_input(f"الحصة (جيجا)", min_value=0.0, value=float(existing_subs[i]["الحصة المحددة (جيجا)"]) if i < len(existing_subs) else 0.0, key=f"gb_{state_key}_{i}")
            with col3: alloc_mins = st.number_input(f"الحصة (دقائق)", min_value=0, value=int(existing_subs[i]["الحصة المحددة (دقائق)"]) if i < len(existing_subs) else 0, key=f"min_{state_key}_{i}")
            with col4: price = st.number_input(f"سعر الباقة (ج.م)", min_value=0.0, value=float(existing_subs[i]["سعر الباقة"]) if i < len(existing_subs) else 0.0, key=f"pr_{state_key}_{i}")
            with col5: 
                st.write("تم الدفع؟")
                paid = st.checkbox("✔", value=bool(existing_subs[i]["حالة الدفع"]) if i < len(existing_subs) else False, key=f"pd_{state_key}_{i}")
            
            if sub_num and str(sub_num).strip() != "":
                sub_lines_data.append({"الشهر": selected_month, "الخط الرئيسي": selected_main_line, "Ana Vodafone Password": voda_password, "إجمالي جيجات الباقة": FIXED_GB, "إجمالي دقائق الباقة": FIXED_MINS, "الخط الفرعي": sub_num, "الحصة المحددة (جيجا)": alloc_gb, "الحصة المحددة (دقائق)": alloc_mins, "سعر الباقة": price, "حالة الدفع": paid})
                input_total_gb += alloc_gb
                input_total_mins += alloc_mins
                
        if st.button("➕ إضافة خط فرعي جديد"):
            if st.session_state[state_key] < MAX_SUB_LINES:
                st.session_state[state_key] += 1
                st.rerun()
            else: st.warning(f"الحد الأقصى {MAX_SUB_LINES} خطوط.")
            
        if input_total_gb > FIXED_GB or input_total_mins > FIXED_MINS or len(sub_lines_data) > MAX_SUB_LINES:
            st.error("⚠️ القيود تمنع الحفظ (تجاوز السعة أو العدد المسموح)!")
        else:
            if st.button("💾 حفظ البيانات المضافة", type="primary"):
                df_clean = df_data[~((df_data["الخط الرئيسي"].astype(str) == selected_main_line) & (df_data["الشهر"].astype(str) == selected_month))]
                new_df = pd.concat([df_clean, pd.DataFrame(sub_lines_data)], ignore_index=True)
                new_df.loc[new_df["الخط الرئيسي"].astype(str) == selected_main_line, "Ana Vodafone Password"] = voda_password
                save_data(new_df)
                st.success("تم الحفظ!")
                st.rerun()

# --- التاب الثاني ---
with tab2:
    st.markdown("### 🗂️ لوحة التحكم الشاملة")
    if not df_data.empty:
        df_sorted = df_data.sort_values(by=["الشهر", "الخط الرئيسي"]).reset_index(drop=True)
        edited_df = st.data_editor(df_sorted.rename(columns=SHORT_COLUMNS), use_container_width=True, num_rows="dynamic", hide_index=True)
        if st.button("💾 حفظ التعديلات من الجدول"):
            save_data(edited_df.rename(columns={v: k for k, v in SHORT_COLUMNS.items()}))
            st.success("تم التحديث!")
            st.rerun()

# --- التاب الثالث ---
with tab3:
    st.markdown("### 🔔 التنبيهات والخطوط غير المكتملة")
    if incomplete_lines: st.dataframe(pd.DataFrame(incomplete_lines), use_container_width=True, hide_index=True)
    else: st.success("🎉 كل الخطوط مكتملة!")
