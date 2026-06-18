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


# إنشاء ملف الإكسيل بالأعمدة الجديدة لو لم يكن موجوداً

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

        # تحويل القيم الفارغة والنصوص التي تحتوي على مسافات فقط إلى NaN للحذف الحقيقي

        df = df.replace(r'^\s*$', pd.NA, regex=True)

        # حذف أي سطر يكون فيه الخط الرئيسي أو الفرعي فارغاً تماماً لتنظيف الـ Dropdown

        df = df.dropna(subset=["الخط الرئيسي", "الخط الفرعي"], how="any")

        # التأكد من حذف السطور الوهمية التي تحتوي على خطوط رئيسية فارغة

        df = df[df["الخط الرئيسي"].astype(str).str.strip() != ""]

        df = df[df["الخط الرئيسي"].astype(str) != "None"]

        df = df[df["الخط الرئيسي"].astype(str) != "<NA>"]

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

    .noti-badge {

        background-color: #ff4b4b;

        color: white;

        border-radius: 50%;

        padding: 2px 8px;

        font-size: 0.8rem;

        margin-right: 5px;

        vertical-align: super;

    }

    </style>

    <meta name="apple-mobile-web-app-capable" content="yes">

    <meta name="mobile-web-app-capable" content="yes">

    """, unsafe_allow_html=True)


# العنوان الرئيسي متمركز في المنتصف

st.markdown("<h1 class='centered-title'>📱 Quota Management</h1>", unsafe_allow_html=True)


# تحميل البيانات الحالية

df_data = load_data()


# فحص ذكي لملء وتأمين الأعمدة في الملف القديم إن وجدت

if not df_data.empty:

    if "الشهر" not in df_data.columns: df_data.insert(0, "الشهر", "")

    if "Ana Vodafone Password" not in df_data.columns: df_data.insert(2, "Ana Vodafone Password", "")

    if "سعر الباقة" not in df_data.columns: df_data["سعر الباقة"] = 0.0

    if "حالة الدفع" not in df_data.columns: df_data["حالة الدفع"] = False

    df_data["حالة الدفع"] = df_data["حالة الدفع"].fillna(False).astype(bool)


# قاموس لتخصيص واختصار أسماء الأعمدة المعروضة للمستخدم لتصبح خفيفة ومريحة

SHORT_COLUMNS = {

    "الشهر": "الشهر",

    "الخط الرئيسي": "الرئيسي",

    "Ana Vodafone Password": "الباسورد",

    "إجمالي جيجات الباقة": "إجمالي جيجا",

    "إجمالي دقائق الباقة": "إجمالي دقائق",

    "الخط الفرعي": "الفرعي",

    "الحصة المحددة (جيجا)": "جيجا",

    "الحصة المحددة (دقائق)": "دقائق",

    "سعر الباقة": "السعر",

    "حالة الدفع": "الدفع"

}


# --- الحساب التلقائي للخطوط غير المكتملة للشهر الحالي ---

current_year = datetime.now().year

months_list = [f"{m:02d}-{current_year}" for m in range(1, 13)]

current_month_str = f"{datetime.now().month:02d}-{current_year}"


incomplete_lines = []

if not df_data.empty:

    df_month = df_data[df_data["الشهر"].astype(str) == current_month_str]

    df_month = df_month.dropna(subset=["الخط الرئيسي"])

    unique_mains = df_month["الخط الرئيسي"].unique()

    

    for main in unique_mains:

        if str(main).strip() == "" or str(main) == "nan" or str(main) == "None":

            continue

        df_sub = df_month[df_month["الخط الرئيسي"] == main]

        df_sub_valid = df_sub[df_sub["الخط الفرعي"].notna()]

        

        sub_count = len(df_sub_valid)

        allocated_gb = df_sub_valid["الحصة المحددة (جيجا)"].sum()

        allocated_mins = df_sub_valid["الحصة المحددة (دقائق)"].sum()

        

        rem_gb = FIXED_GB - allocated_gb

        rem_mins = FIXED_MINS - allocated_mins

        

        if rem_gb > 0 or rem_mins > 0 or sub_count < MAX_SUB_LINES:

            incomplete_lines.append({

                "الخط الرئيسي": main,

                "الخطوط الفرعية الحالية": sub_count,

                "المتبقي (جيجا)": rem_gb if rem_gb > 0 else 0.0,

                "المتبقي (دقائق)": rem_mins if rem_mins > 0 else 0,

                "سبب التنبيه": "⚠️ نقص خطوط وباقة" if (sub_count < MAX_SUB_LINES and (rem_gb > 0 or rem_mins > 0)) else ("📞 الفرعي أقل من 3" if sub_count < MAX_SUB_LINES else "📉 عجز بالباقة")

            })


noti_count = len(incomplete_lines)

noti_label = f"🔔 التنبيهات ({noti_count})" if noti_count == 0 else f"🔔 التنبيهات"


# --- إنشاء التبويبات الثلاثة ---

tab1, tab2, tab3 = st.tabs(["📊 إدارة الخطوط", "🗂️ البيانات", noti_label])


# ==========================================

# التاب الأول: إضافة البيانات والبحث والتحصيل

# ==========================================

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

        filtered_df = df_data[

            df_search["الخط الرئيسي"].str.contains(search_query, na=False) |

            df_search["الخط الفرعي"].str.contains(search_query, na=False)

        ]

        if not filtered_df.empty:

            st.write("📂 نتائج البحث:")

            st.dataframe(filtered_df.rename(columns=SHORT_COLUMNS), use_container_width=True, hide_index=True)

        else:

            st.warning("لا توجد نتائج مطابقة للبحث.")

            

    st.write("---")


    # --- إدارة واختيار الخطوط الرئيسية (تنظيف صارم للقائمة المنسدلة) ---

    st.markdown("### 🏢 اختيار الخط الرئيسي")

    df_clean_dropdown = df_data.dropna(subset=["الخط الرئيسي", "الخط الفرعي"])

    df_clean_dropdown = df_clean_dropdown[df_clean_dropdown["الخط الرئيسي"].astype(str).str.strip() != ""]

    existing_mains = df_clean_dropdown["الخط الرئيسي"].unique().tolist()

    existing_mains = [str(int(m)) if isinstance(m, float) and m.is_integer() else str(m) for m in existing_mains]


    options = ["-- اختر خط رئيسي --"] + existing_mains + ["➕ إضافة خط رئيسي جديد..."]

    selected_option = st.selectbox("حدد الخط الرئيسي الذي تريدين عرض بياناته أو تعديلها:", options)


    selected_main_line = ""

    voda_password = ""

    main_gb = FIXED_GB

    main_mins = FIXED_MINS


    if selected_option == "➕ إضافة خط رئيسي جديد...":

        col_new1, col_new2, col_new3 = st.columns(3)

        with col_new1:

            selected_main_line = st.text_input("رقم الخط الرئيسي الجديد:")

        with col_new2:

            voda_password = st.text_input("Ana Vodafone Password:", type="password", help="اكتب الباسورد الخاص بالخط لحفظه آلياً")

        with col_new3:

            st.text_input("إجمالي جيجابايت الباقة (ثابتة)", value=f"{FIXED_GB} جيجا", disabled=True)

            

    elif selected_option != "-- اختر خط رئيسي --":

        selected_main_line = selected_option

        line_data_saved = df_data[df_data["الخط الرئيسي"].astype(str) == selected_main_line]

        saved_password = str(line_data_saved.iloc[0]["Ana Vodafone Password"]) if "Ana Vodafone Password" in df_data.columns and not line_data_saved.empty else ""

        if saved_password == "nan" or saved_password == "None": saved_password = ""


        col_info1, col_info2, col_info3 = st.columns(3)

        with col_info1:

            st.info(f"📍 **الخط الرئيسي:** {selected_main_line} | **الشهر:** {selected_month}")

        with col_info2:

            voda_password = st.text_input("Ana Vodafone Password:", value=saved_password, type="password")

        with col_info3:

            st.text_input("إجمالي جيجابايت الباقة (ثابتة)", value=f"{FIXED_GB} جيجا", disabled=True)


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


        st.write("#### ✏️ إضافة خطوط فرعية جديدة")

        

        state_key = f"count_{selected_main_line}_{selected_month}"

        if state_key not in st.session_state:

            st.session_state[state_key] = max(len(df_current_sub), 1)

            

        existing_subs = df_current_sub.to_dict('records')

        sub_lines_data = []

        

        input_total_gb = 0.0

        input_total_mins = 0

        

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

                    "Ana Vodafone Password": voda_password,

                    "إجمالي جيجات الباقة": main_gb,

                    "إجمالي دقائق الباقة": main_mins,

                    "الخط الفرعي": sub_num,

                    "الحصة المحددة (جيجا)": alloc_gb,

                    "الحصة المحددة (دقائق)": alloc_mins,

                    "سعر الباقة": price,

                    "حالة الدفع": paid

                })

                input_total_gb += alloc_gb

                input_total_mins += alloc_mins

                

        if st.button("➕ إضافة خط فرعي جديد لهذا الخط والشهر"):

            if st.session_state[state_key] >= MAX_SUB_LINES:

                st.warning(f"⚠️ غير مسموح بإضافة حقول جديدة! الحد الأقصى هو {MAX_SUB_LINES} خطوط فرعية فقط للخط الرئيسي الواحد.")

            else:

                st.session_state[state_key] += 1

                st.rerun()

            

        st.write("")

        

        if input_total_gb > FIXED_GB or input_total_mins > FIXED_MINS:

            st.error(f"⚠️ لا يمكن الحفظ! مجموع الحصص المدخلة تجاوز السعة القصوى المحددة للخط الرئيسي. "

                     f"(المدخل حالياً: {input_total_gb} جيجا من {FIXED_GB} | {input_total_mins} دقيقة من {FIXED_MINS})")

            st.button("💾 حفظ البيانات المضافة", type="primary", disabled=True)

        elif len(sub_lines_data) > MAX_SUB_LINES:

            st.error(f"⚠️ لا يمكن الحفظ! تجاوزتِ الحد الأقصى للخطوط الفرعية المسموحة ({MAX_SUB_LINES} خطوط كحد أقصى).")

            st.button("💾 حفظ البيانات المضافة", type="primary", disabled=True)

        else:

            if st.button("💾 حفظ البيانات المضافة", type="primary"):

                df_clean = df_data[

                    ~((df_data["الخط الرئيسي"].astype(str) == selected_main_line) & 

                      (df_data["الشهر"].astype(str) == selected_month))

                ]

                new_df = pd.concat([df_clean, pd.DataFrame(sub_lines_data)], ignore_index=True)

                new_df.loc[new_df["الخط الرئيسي"].astype(str) == selected_main_line, "Ana Vodafone Password"] = voda_password

                save_data(new_df)

                st.success("تم حفظ البيانات وتحديث قائمة الخطوط بنجاح!")

                st.rerun()


# ==========================================

# التاب الثاني: التعديل والحذف المباشر (ترتيب بصري، فواصل، وتنظيف صارم)

# ==========================================

with tab2:

    st.markdown("### 🗂️ لوحة التحكم الشاملة (تعديل وحذف مباشر)")

    

    if not df_data.empty:

        st.info("💡 يمكنك التعديل مباشرة بالضغط المزدوج. لحذف خط بالكامل: امسحي رقم الخط الرئيسي أو الفرعي واضغطي حفظ، أو حددي السطر واضغطي Delete.")

        

        # ترتيب البيانات بناءً على الشهر ثم الخط الرئيسي لضمان تجمعهم معاً

        df_sorted = df_data.sort_values(by=["الشهر", "الخط الرئيسي"]).reset_index(drop=True)

        

        # --- خوارزمية حقن السطور الفاصلة بصرياً ---

        visually_separated_records = []

        last_main_line = None

        last_month = None

        

        for idx, row in df_sorted.iterrows():

            current_main = str(row["الخط الرئيسي"]).strip()

            current_m = str(row["الشهر"]).strip()

            

            # إذا تغير الخط الرئيسي أو الشهر، نقوم بوضع سطر فاصل رمادي رمزي ومميز بمجرد النظر

            if last_main_line is not None and (current_main != last_main_line or current_m != last_month):

                # سطر فاصل وهمي

                visually_separated_records.append({

                    "الشهر": "---", "الخط الرئيسي": "👇 الخط التالي 👇", "Ana Vodafone Password": "---",

                    "إجمالي جيجات الباقة": 0, "إجمالي دقائق الباقة": 0, "الخط الفرعي": "-----------------",

                    "الحصة المحددة (جيجا)": 0, "الحصة المحددة (دقائق)": 0, "سعر الباقة": 0, "حالة الدفع": False

                })

            

            visually_separated_records.append(row.to_dict())

            last_main_line = current_main

            last_month = current_m

            

        df_visual = pd.DataFrame(visually_separated_records)

        

        # تحويل الأعمدة في الجدول إلى الأسماء المختصرة المريحة للعين

        df_display = df_visual.rename(columns=SHORT_COLUMNS)

        

        edited_display_df = st.data_editor(

            df_display,

            use_container_width=True,

            num_rows="dynamic",

            hide_index=True,

            column_config={

                "الدفع": st.column_config.CheckboxColumn("الدفع", help="تحديد هل تم الدفع أم لا"),

                "الباسورد": st.column_config.TextColumn("الباسورد", help="كلمة المرور الخاصة بحساب أنا فودافون")

            }

        )

        

        # إعادة الأسماء للأصلية في الخلفية لعمل الـ Validation والحفظ بالإكسيل بشكل صحيح

        INV_SHORT_COLUMNS = {v: k for k, v in SHORT_COLUMNS.items()}

        edited_df = edited_display_df.rename(columns=INV_SHORT_COLUMNS)

        

        validation_passed = True

        error_message = ""

        

        if not edited_df.empty:

            # فلترة وإزالة السطور الفاصلة الوهمية قبل الفحص والحفظ في الإكسيل

            edited_df = edited_df[edited_df["الخط الرئيسي"].astype(str) != "👇 الخط التالي 👇"]

            edited_df = edited_df[edited_df["الشهر"].astype(str) != "---"]

            

            # استبدال الفراغات بقيم نان حقيقية لتنظيفها تماماً وحذفها من الملف والقوائم

            edited_df = edited_df.replace(r'^\s*$', pd.NA, regex=True)

            edited_df = edited_df.dropna(subset=["الخط الرئيسي", "الخط الفرعي"], how="any")

            edited_df = edited_df[edited_df["الخط الرئيسي"].astype(str).str.strip() != ""]

            

            if not edited_df.empty:

                grouped = edited_df.groupby(["الشهر", "الخط الرئيسي"]).agg({

                    "الحصة المحددة (جيجا)": "sum",

                    "الحصة المحددة (دقائق)": "sum",

                    "الخط الفرعي": "count"

                }).reset_index()

                

                for index, row in grouped.iterrows():

                    if row["الحصة المحددة (جيجا)"] > FIXED_GB or row["الحصة المحددة (دقائق)"] > FIXED_MINS:

                        validation_passed = False

                        error_message = f"⚠️ خطأ في التعديل: الخط الرئيسي ({row['الخط الرئيسي']}) في شهر ({row['الشهر']}) تخطى السعة المحددة للـباقة!"

                        break

                    if row["الخط الفرعي"] > MAX_SUB_LINES:

                        validation_passed = False

                        error_message = f"⚠️ خطأ في التعديل: الخط الرئيسي ({row['الخط الرئيسي']}) في شهر ({row['الشهر']}) تخطى الحد الأقصى المسموح للأعداد ({row['الخط الفرعي']} خطوط فرعية)!"

                        break


        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])

        with col_btn1:

            if not validation_passed:

                st.error(error_message)

                st.button("💾 حفظ التعديلات", type="primary", key="save_editor", disabled=True)

            else:

                if st.button("💾 حفظ التعديلات ", type="primary", key="save_editor"):

                    save_data(edited_df)

                    st.success("تم تحديث البيانات بنجاح !")

                    st.rerun()

        with col_btn2:

            if st.button("🔄 تحديث الجدول"):

                st.rerun()

        with col_btn3:

            try:

                with open(EXCEL_FILE, "rb") as f:

                    st.download_button(

                        label="📥 تحميل نسخة Excel احتياطية",

                        data=f,

                        file_name=f"Quota_Backup_{selected_month}.xlsx",

                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                    )

            except:

                pass

                

        st.write("---")

        # حساب المجموع الفعلي للتحصيلات باستثناء السطور الفاصلة

        if not edited_df.empty:

            actual_collected = edited_df[edited_df['حالة الدفع'] == True]['سعر الباقة'].sum()

        else:

            actual_collected = 0.0

        st.success(f"إلاجمالي: **{actual_collected} ج.م**")

    else:

        st.info("لا توجد بيانات مسجلة في ملف الإكسيل حتى الآن.")


# ==========================================

# التاب الثالث: نظام التنبيهات المطور

# ==========================================

with tab3:

    st.markdown(f"### 🔔 التنبيهات والخطوط غير المكتملة لشهر ({current_month_str})")

    st.markdown(f"مجموع الخطوط التي تتطلب مراجعة حالياً: <span class='noti-badge'>{noti_count}</span>", unsafe_allow_html=True)

    st.write(f"الجدول التالي يوضح الخطوط الرئيسية التي بها عجز في التوزيع أو التي تحتوي على **أقل من {MAX_SUB_LINES} خطوط فرعية**:")

    

    if incomplete_lines:

        df_incomplete = pd.DataFrame(incomplete_lines)

        st.dataframe(df_incomplete, use_container_width=True, hide_index=True)

    else:

        st.success("🎉 ممتاز! جميع الخطوط الرئيسية مكتملة بنسبة 100% وتحتوي على 3 خطوط فرعية وموزعة بالكامل.")



