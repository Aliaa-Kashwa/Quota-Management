import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- إعدادات الملف وقاعدة البيانات ---
EXCEL_FILE = "net_package_management.xlsx"

# الباقات الثابتة للخط الرئيسي
FIXED_GB = 50.0
FIXED_MINS = 8000

# إنشاء ملف الإكسيل بالأعمدة الجديدة لو لم يكن موجوداً
if not os.path.exists(EXCEL_FILE):
    df_empty = pd.DataFrame(columns=[
        "الشهر", "الخط الرئيسي", "إجمالي جيجات الباقة", "إجمالي دقائق الباقة", 
        "الخط الفرعي", "الحصة المحددة (جيجا)", "الحصة المحددة (دقائق)", "سعر الباقة", "حالة الدفع"
    ])
    df_empty.to_excel(EXCEL_FILE, index=False)

def load_data():
    return pd.read_excel(EXCEL_FILE)

def save_data(df):
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
    </style>
    """, unsafe_allow_html=True)

# العنوان الرئيسي متمركز في المنتصف
st.markdown("<h1 class='centered-title'>📱 Quota Management</h1>", unsafe_allow_html=True)

# تحميل البيانات الحالية
df_data = load_data()

# فحص ذكي لضمان وجود كافة الأعمدة بالصيغ الصحيحة
if not df_data.empty:
    if "الشهر" not in df_data.columns: df_data.insert(0, "الشهر", "")
    if "سعر الباقة" not in df_data.columns: df_data["سعر الباقة"] = 0.0
    if "حالة الدفع" not in df_data.columns: df_data["حالة الدفع"] = False
    df_data["حالة الدفع"] = df_data["حالة الدفع"].fillna(False).astype(bool)

# --- إنشاء التبويبات ---
tab1, tab2 = st.tabs(["📊 إدارة وتوزيع الحصص والشهور", "🗂️ عرض وتعديل وحذف البيانات الشاملة"])

# ==========================================
# التاب الأول: إضافة البيانات والبحث والتحصيل
# ==========================================
with tab1:
    col_top1, col_top2 = st.columns([1, 2])
    
    with col_top1:
        st.markdown("### 📅 اختيار الشهر الحالي")
        current_year = datetime.now().year
        months_list = [f"{m:02d}-{current_year}" for m in range(1, 13)]
        default_month_idx = datetime.now().month - 1
        selected_month = st.selectbox("حددي الشهر المستهدف للعمل عليه:", months_list, index=default_month_idx)
        
    with col_top2:
        st.markdown("### 🔍 البحث السريع")
        search_query = st.text_input("ابحثي برقم الخط الرئيسي أو الرقم الفرعي:")

    if search_query:
        df_search = df_data.fillna("").astype(str)
        filtered_df = df_data[
            df_search["الخط الرئيسي"].str.contains(search_query, na=False) |
            df_search["الخط الفرعي"].str.contains(search_query, na=False)
        ]
        if not filtered_df.empty:
            st.write("📂 نتائج البحث:")
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        else:
            st.warning("لا توجد نتائج مطابقة للبحث.")
            
    st.write("---")

    # --- إدارة واختيار الخطوط الرئيسية ---
    st.markdown("### 🏢 اختيار الخط الرئيسي")
    existing_mains = df_data["الخط الرئيسي"].dropna().unique().tolist()
    existing_mains = [str(int(m)) if isinstance(m, float) and m.is_integer() else str(m) for m in existing_mains]

    options = ["-- اختر خط رئيسي --"] + existing_mains + ["➕ إضافة خط رئيسي جديد..."]
    selected_option = st.selectbox("حدد الخط الرئيسي الذي تريدين عرض بياناته أو تعديلها:", options)

    selected_main_line = ""
    main_gb = FIXED_GB
    main_mins = FIXED_MINS

    if selected_option == "➕ إضافة خط رئيسي جديد...":
        col_new1, col_new2, col_new3 = st.columns(3)
        with col_new1:
            selected_main_line = st.text_input("رقم الخط الرئيسي الجديد:")
        with col_new2:
            st.text_input("إجمالي جيجابايت الباقة (ثابتة)", value=f"{FIXED_GB} جيجا", disabled=True)
        with col_new3:
            st.text_input("إجمالي دقائق الباقة (ثابتة)", value=f"{FIXED_MINS} دقيقة", disabled=True)
            
    elif selected_option != "-- اختر خط رئيسي --":
        selected_main_line = selected_option
        
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.info(f"📍 **الخط الرئيسي المختار:** {selected_main_line} | **الشهر:** {selected_month}")
        with col_info2:
            st.text_input("إجمالي جيجابايت الباقة (ثابتة)", value=f"{FIXED_GB} جيجا", disabled=True)
        with col_info3:
            st.text_input("إجمالي دقائق الباقة (ثابتة)", value=f"{FIXED_MINS} دقيقة", disabled=True)

# --- عرض الحصص والخطوط الفرعية ---
    if selected_main_line:
        st.write("---")
        st.subheader(f"👥 الخطوط الفرعية والمدفوعات لشهر ({selected_month})")
        
        df_current_sub = df_data[
            (df_data["الخط الرئيسي"].astype(str) == selected_main_line) & 
            (df_data["الشهر"].astype(str) == selected_month)
        ]
        df_current_sub = df_current_sub[df_current_sub["الخط الفرعي"].notna()]
        
        total_allocated_gb = df_current_sub["الحصة المحددة (جيجا)"].sum()
        total_allocated_mins = df_current_sub["الحصة المحددة (دقائق)"].sum()
        total_collected_money = df_current_sub[df_current_sub["حالة الدفع"] == True]["سعر الباقة"].sum()
        total_expected_money = df_current_sub["سعر الباقة"].sum()
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            remaining_gb = main_gb - total_allocated_gb
            st.metric("المتبقي من الجيجابايت", f"{remaining_gb} جيجا", delta=f"-{total_allocated_gb} موزع")
        with col_m2:
            remaining_mins = main_mins - total_allocated_mins
            st.metric("المتبقي من الدقائق", f"{remaining_mins} دقيقة", delta=f"-{total_allocated_mins} موزع")
        with col_m3:
            st.metric("التحصيل المالي للشهر", f"{total_collected_money} ج.م", delta=f"من إجمالي متوقع: {total_expected_money} ج.م")

        st.write("#### ✏️ إضافة حصص وخطوط فرعية جديدة")
        
        state_key = f"count_{selected_main_line}_{selected_month}"
        if state_key not in st.session_state:
            st.session_state[state_key] = max(len(df_current_sub), 1)
            
        existing_subs = df_current_sub.to_dict('records')
        sub_lines_data = []
        
        for i in range(st.session_state[state_key]):
            st.write(f"**الخط الفرعي #{i+1}**")
            col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1.5, 1])
            
            default_sub = str(existing_subs[i]["الخط الفرعي"]) if i < len(existing_subs) else ""
            if default_sub.endswith(".0"): default_sub = default_sub[:-2]
            
            default_alloc_gb = float(existing_subs[i]["الحصة المحددة (جيجا)"]) if i < len(existing_subs) else 0.0
            default_alloc_mins = int(existing_subs[i]["الحصة المحددة (دقائق)"]) if i < len(existing_subs) else 0
            default_price = float(existing_subs[i]["سعر الباقة"]) if i < len(existing_subs) else 0.0
            default_paid = bool(existing_subs[i]["حالة الدفع"]) if i < len(existing_subs) else False
            
            with col1:
                sub_num = st.text_input(f"رقم الهاتف الفرعي", value=default_sub, key=f"sub_num_{state_key}_{i}")
            with col2:
                alloc_gb = st.number_input(f"الحصة (جيجا)", min_value=0.0, value=default_alloc_gb, step=0.5, key=f"alloc_gb_{state_key}_{i}")
            with col3:
                alloc_mins = st.number_input(f"الحصة (دقائق)", min_value=0, value=default_alloc_mins, step=10, key=f"alloc_mins_{state_key}_{i}")
            with col4:
                price = st.number_input(f"سعر الباقة (ج.م)", min_value=0.0, value=default_price, step=5.0, key=f"price_{state_key}_{i}")
            with col5:
                st.write("تم الدفع؟")
                paid = st.checkbox("✔", value=default_paid, key=f"paid_{state_key}_{i}")
            
            if sub_num:
                sub_lines_data.append({
                    "الشهر": selected_month,
                    "الخط الرئيسي": selected_main_line,
                    "إجمالي جيجات الباقة": main_gb,
                    "إجمالي دقائق الباقة": main_mins,
                    "الخط الفرعي": sub_num,
                    "الحصة المحددة (جيجا)": alloc_gb,
                    "الحصة المحددة (دقائق)": alloc_mins,
                    "سعر الباقة": price,
                    "حالة الدفع": paid
                })
                
        if st.button("➕ إضافة خط فرعي جديد لهذا الخط والشهر"):
            st.session_state[state_key] += 1
            st.rerun()
            
        st.write("")
        if st.button("💾 حفظ البيانات المضافة", type="primary"):
            df_clean = df_data[
                ~((df_data["الخط الرئيسي"].astype(str) == selected_main_line) & 
                  (df_data["الشهر"].astype(str) == selected_month))
            ]
            new_df = pd.concat([df_clean, pd.DataFrame(sub_lines_data)], ignore_index=True)
            save_data(new_df)
            st.success("تم حفظ البيانات بنجاح!")
            st.rerun()

# ==========================================
# التاب الثاني: التعديل والحذف المباشر
# ==========================================
with tab2:
    st.markdown("### 🗂️ لوحة التحكم الشاملة (تعديل وحذف مباشر)")
    
    if not df_data.empty:
        st.info("💡 يمكنك التعديل مباشرة بالضغط المزدوج على أي خانة، ولحذف أي سطر: حدد السطر بالماوس واضغط على زر Delete في لوحة المفاتيح.")
        
        edited_df = st.data_editor(
            df_data,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "حالة الدفع": st.column_config.CheckboxColumn("حالة الدفع", help="تحديد هل تم الدفع أم لا")
            }
        )
        
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            if st.button("💾 حفظ كل التعديلات والحذوفات النهائية في الإكسيل", type="primary", key="save_editor"):
                save_data(edited_df)
                st.success("تم تحديث ملف الإكسيل وحفظ التغييرات الجديدة بنجاح!")
                st.rerun()
        with col_btn2:
            if st.button("🔄 تحديث الجدول"):
                st.rerun()
                
        st.write("---")
        st.success(f"إجمالي التحصيلات المالية الفعلية الكلية: **{edited_df[edited_df['حالة الدفع'] == True]['سعر الباقة'].sum()} ج.م**")
    else:
        st.info("لا توجد بيانات مسجلة في ملف الإكسيل حتى الآن.")