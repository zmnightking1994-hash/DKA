import streamlit as st

# إعدادات الصفحة
st.set_page_config(page_title="BSPED DKA Calculator", layout="wide")

st.title("🩺 تطبيق التدبير المثالي للحماض الكيتوني السكري (DKA)")
st.subheader("بناءً على تحديثات BSPED 2024 للأطفال دون 18 عاماً")

# --- القائمة الجانبية للمدخلات ---
with st.sidebar:
    st.header("بيانات المريض")
    weight = st.number_input("الوزن (كجم)", min_value=1.0, max_value=150.0, value=20.0)
    ph = st.number_input("قيمة الـ pH", min_value=6.7, max_value=7.5, value=7.1, step=0.01)
    bolus_given = st.number_input("سوائل الإنعاش المعطاة سابقاً (ml)", min_value=0, value=0)
    
    st.divider()
    insulin_dose = st.select_slider(
        "معدل الأنسولين (Units/kg/hr)",
        options=[0.05, 0.1],
        value=0.1,
        help="0.05 للأطفال الصغار جداً أو حسب حساسية الحالة"
    )

# --- المنطق الحسابي (Logic) ---

# 1. تحديد نسبة الجفاف بناءً على pH
if ph < 7.1:
    dehydration_percent = 10.0
    severity = "Severe (شديد)"
elif ph < 7.2:
    dehydration_percent = 5.0
    severity = "Moderate (متوسط)"
else:
    dehydration_percent = 5.0
    severity = "Mild (خفيف)"

# 2. حساب سوائل الإدامة (Maintenance) حسب قاعدة BSPED المعدلة
# أول 10 كجم = 2 مل/كجم/ساعة
# من 11-20 كجم = 0.5 مل/كجم/ساعة
# ما فوق 20 كجم = 0.2 مل/كجم/ساعة
def calculate_maintenance(w):
    if w <= 10:
        m = w * 2
    elif w <= 20:
        m = 20 + (w - 10) * 0.5
    else:
        m = 25 + (w - 20) * 0.2
    return min(m, 80) # الحد الأقصى 80 مل/ساعة

maintenance_rate = calculate_maintenance(weight)

# 3. حساب العجز (Deficit) وتعويضه على 48 ساعة
total_deficit_vol = dehydration_percent * weight * 10
hourly_deficit_rate = (total_deficit_vol - bolus_given) / 48

# 4. المجموع الكلي للسوائل
total_hourly_rate = maintenance_rate + hourly_deficit_rate

# --- عرض النتائج ---

col1, col2 = st.columns(2)

with col1:
    st.info(f"**تصنيف الحالة:** {severity}")
    st.metric(label="نسبة الجفاف المقدرة", value=f"{dehydration_percent}%")
    st.metric(label="إجمالي العجز (Total Deficit)", value=f"{total_deficit_vol:.1f} ml")

with col2:
    st.success("**خطة السوائل الوريدية (ml/hr)**")
    st.write(f"💧 سوائل الإدامة: **{maintenance_rate:.1f} ml/hr**")
    st.write(f"📉 تعويض العجز: **{hourly_deficit_rate:.1f} ml/hr**")
    st.divider()
    st.metric(label="المعدل الكلي للسوائل", value=f"{total_hourly_rate:.1f} ml/hr")

st.divider()

# --- قسم الأنسولين والمراقبة ---
st.warning("⚠️ **الأنسولين الوريدي**")
st.write(f"ابدأ الأنسولين بعد ساعة إلى ساعتين من بدء السوائل بمعدل: **{weight * insulin_dose:.2f} Units/hr**")

st.markdown("""
### 📋 قائمة المراقبة (Checklist):
* **نوع المحلول:** Plasma-Lyte 148 أو NaCl 0.9% مع **40 mmol/L البوتاسيوم**.
* **الغلوكوز:** أضف الغلوكوز 5% للمحلول عندما ينخفض السكر عن **14 mmol/L**.
* **المراقبة:** مراقبة علامات وذمة الدماغ (صداع، انخفاض نبض، تغير وعي) كل ساعة.
* **المختبر:** فحص الكيتونات والسكر كل ساعة، والشوارد كل 2-4 ساعات.
""")

# زر لتحميل التقرير كـ JSON (اختياري)
results = {
    "weight": weight,
    "ph": ph,
    "severity": severity,
    "hourly_fluid_rate": round(total_hourly_rate, 2),
    "insulin_rate": round(weight * insulin_dose, 2)
}
st.sidebar.download_button("تحميل ملخص الحالة (JSON)", str(results), file_name="dka_summary.json")
