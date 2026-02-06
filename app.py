import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="BSPED DKA Manager", layout="wide")

# --- دالة إنشاء ملف PDF باللغة الإنجليزية (لضمان التوافق مع المكتبة) ---
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # الترويسة
    pdf.cell(200, 10, txt="DKA Management Report (BSPED 2024)", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # بيانات المريض
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Patient Information:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(100, 10, txt=f"Weight: {data['weight']} kg", ln=False)
    pdf.cell(100, 10, txt=f"Initial pH: {data['ph']}", ln=True)
    pdf.cell(100, 10, txt=f"Severity: {data['severity']}", ln=True)
    pdf.ln(5)
    
    # خطة السوائل
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Fluid Management Plan:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"- Hydration Rate (Immaha): {data['hydration_rate']:.1f} ml/hr", ln=True)
    pdf.cell(200, 10, txt=f"- Deficit Correction (48h): {data['deficit_rate']:.1f} ml/hr", ln=True)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(200, 10, txt=f"TOTAL FLUID RATE: {data['total_rate']:.1f} ml/hr", ln=True, fill=True)
    pdf.ln(5)
    
    # الأنسولين ونوع المحلول
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Therapy Details:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"- Insulin Infusion Rate: {data['insulin_rate']:.2f} Units/hr", ln=True)
    pdf.cell(200, 10, txt=f"- Current BG Recommendation: {data['bg_advice']}", ln=True)
    pdf.ln(10)
    
    # ملاحظات قانونية
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 5, txt="Disclaimer: This report is a clinical decision aid based on BSPED guidelines. Clinical judgment by the attending physician is paramount.")
    
    return pdf.output()

# --- واجهة التطبيق الرئيسية ---
st.title("🩺 تطبيق التدبير المثالي للحماض الكيتوني السكري (DKA)")
st.markdown("##### مستوحى من دليل جمعية BSPED 2021/2024 للأطفال والمراهقين")

# --- القائمة الجانبية للمدخلات ---
with st.sidebar:
    st.header("📥 إدخال البيانات")
    weight = st.number_input("الوزن (كجم)", min_value=1.0, max_value=150.0, value=20.0, step=0.1)
    ph = st.number_input("قيمة الـ pH الأولي", min_value=6.7, max_value=7.5, value=7.1, step=0.01)
    current_bg = st.number_input("مستوى السكر الحالي (mmol/L)", min_value=0.0, value=20.0, step=0.1)
    bolus_given = st.number_input("سوائل الإنعاش المعطاة سابقاً (ml)", min_value=0, value=0, help="أي سوائل وريدية سريعة أُعطيت قبل البدء بالبروتوكول")
    
    st.divider()
    insulin_option = st.select_slider("معدل الأنسولين (Units/kg/hr)", options=[0.05, 0.1], value=0.1)
    
    st.info("💡 يتم تعويض العجز على مدار 48 ساعة حسب توصيات BSPED.")

# --- منطق الحسابات الطبية ---

# 1. تحديد الشدة والجفاف
if ph < 7.1:
    dehydration, severity = 10.0, "Severe (شديد)"
elif ph < 7.2:
    dehydration, severity = 5.0, "Moderate (متوسط)"
else:
    dehydration, severity = 5.0, "Mild (خفيف)"

# 2. حساب سوائل الإماهة (Maintenance) - قاعدة BSPED 2/0.5/0.2
def calc_hydration(w):
    if w <= 10:
        rate = w * 2
    elif w <= 20:
        rate = 20 + (w - 10) * 0.5
    else:
        rate = 25 + (w - 20) * 0.2
    return min(rate, 80) # الحد الأقصى للإماهة 80 مل/ساعة

hydration_rate = calc_hydration(weight)

# 3. حساب العجز (Deficit)
total_deficit_vol = dehydration * weight * 10
hourly_deficit_rate = (total_deficit_vol - bolus_given) / 48

# 4. المجموع الكلي
total_hourly_rate = hydration_rate + hourly_deficit_rate
insulin_hourly = weight * insulin_option

# --- عرض النتائج في الواجهة ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("شدة الحالة", severity)
    st.metric("نسبة الجفاف", f"{dehydration}%")

with col2:
    st.metric("سوائل الإماهة", f"{hydration_rate:.1f} ml/hr")
    st.metric("تعويض العجز", f"{hourly_deficit_rate:.1f} ml/hr")

with col3:
    st.success("المعدل الكلي للجريان")
    st.title(f"{total_hourly_rate:.1f}")
    st.caption("مل/ساعة (ml/hr)")

st.divider()

# --- منطق الجلوكوز المتغير وتوصية المحلول ---
st.subheader("🧪 نوع المحلول والتوصيات الحالية")
bg_advice = ""
if current_bg > 14:
    bg_advice = "NaCl 0.9% or Plasma-Lyte 148 (No Glucose)"
    st.info(f"**المحلول المطلوب:** Plasma-Lyte 148 أو NaCl 0.9% **بدون جلوكوز** + 40 mmol/L بوتاسيوم.")
elif 6 <= current_bg <= 14:
    bg_advice = "Add 5% Glucose to fluids"
    st.warning(f"**المحلول المطلوب:** أضف **5% جلوكوز** للمحلول الوريدي الحالي + 40 mmol/L بوتاسيوم.")
else:
    bg_advice = "Add 10% Glucose (Risk of Hypo)"
    st.error(f"**تحذير:** مستوى السكر منخفض! استخدم **10% جلوكوز** وراجع بروتوكول الهبوط.")

# --- جرعة الأنسولين ---
st.write(f"💉 **معدل تسريب الأنسولين:** {insulin_hourly:.2f} Units/hr (يبدأ بعد 1-2 ساعة من السوائل)")

st.divider()

# --- قسم مراقبة وذمة الدماغ (Cerebral Oedema Checklist) ---
with st.expander("🚨 قائمة مراقبة وذمة الدماغ (تحقق كل ساعة)"):
    st.write("إذا ظهرت أي من العلامات التالية، اتصل بالاستشاري فوراً وفكر في المانيتول:")
    st.checkbox("صداع شديد أو متزايد")
    st.checkbox("تدهور في مستوى الوعي (GCS)")
    st.checkbox("انخفاض نبض القلب (Bradycardia < 60 bpm)")
    st.checkbox("ارتفاع ضغط الدم المفاجئ")
    st.checkbox("تغير في استجابة الحدقات أو رؤية مزدوجة")

# --- استخراج التقرير ---
pdf_data = {
    "weight": weight,
    "ph": ph,
    "severity": severity,
    "hydration_rate": hydration_rate,
    "deficit_rate": hourly_deficit_rate,
    "total_rate": total_hourly_rate,
    "insulin_rate": insulin_hourly,
    "bg_advice": bg_advice
}

pdf_file = create_pdf(pdf_data)

st.sidebar.divider()
st.sidebar.download_button(
    label="📄 تحميل تقرير PDF للطباعة",
    data=pdf_file,
    file_name=f"DKA_Plan_{weight}kg.pdf",
    mime="application/pdf"
)

# إخلاء مسؤولية
st.caption("إخلاء مسؤولية: هذا التطبيق أداة مساعدة فقط. يجب مراجعة القرارات الطبية من قبل طبيب مختص بناءً على الحالة السريرية.")
