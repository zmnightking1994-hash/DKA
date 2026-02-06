import streamlit as st
from fpdf import FPDF
import io

# إعدادات الصفحة
st.set_page_config(page_title="BSPED DKA Calculator", layout="wide")

# دالة لإنشاء ملف PDF
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # العنوان
    pdf.cell(200, 10, txt="DKA Management Summary (BSPED 2024)", ln=True, align='C')
    pdf.ln(10)
    
    # بيانات المريض
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Patient Weight: {data['weight']} kg", ln=True)
    pdf.cell(200, 10, txt=f"Initial pH: {data['ph']}", ln=True)
    pdf.cell(200, 10, txt=f"Severity: {data['severity']}", ln=True)
    pdf.ln(5)
    
    # الحسابات
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Fluid Management Plan:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"- Hydration Rate (Immaha): {data['hydration_rate']:.1f} ml/hr", ln=True)
    pdf.cell(200, 10, txt=f"- Deficit Correction Rate: {data['deficit_rate']:.1f} ml/hr", ln=True)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(200, 10, txt=f"- TOTAL HOURLY RATE: {data['total_rate']:.1f} ml/hr", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # الأنسولين
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Insulin Therapy:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"- Start insulin at: {data['insulin_rate']:.2f} Units/hr", ln=True)
    pdf.cell(200, 10, txt="- Note: Start 1-2 hours after fluids.", ln=True)
    
    return pdf.output()

st.title("🩺 تطبيق التدبير المثالي للحماض الكيتوني السكري (DKA)")
st.subheader("بناءً على تحديثات BSPED 2024 للأطفال")

# --- القائمة الجانبية ---
with st.sidebar:
    st.header("بيانات المريض")
    weight = st.number_input("الوزن (كجم)", min_value=1.0, max_value=150.0, value=20.0)
    ph = st.number_input("قيمة الـ pH", min_value=6.7, max_value=7.5, value=7.1, step=0.01)
    bolus_given = st.number_input("سوائل الإنعاش المعطاة (ml)", min_value=0, value=0)
    insulin_dose = st.select_slider("معدل الأنسولين (Units/kg/hr)", options=[0.05, 0.1], value=0.1)

# --- الحسابات المنطقية ---
if ph < 7.1:
    dehydration_percent, severity = 10.0, "Severe (شديد)"
elif ph < 7.2:
    dehydration_percent, severity = 5.0, "Moderate (متوسط)"
else:
    dehydration_percent, severity = 5.0, "Mild (خفيف)"

# حساب الإماهة (Maintenance)
def calc_hydration(w):
    if w <= 10: return w * 2
    elif w <= 20: return 20 + (w - 10) * 0.5
    else: return min(25 + (w - 20) * 0.2, 80)

hydration_rate = calc_hydration(weight)
total_deficit_vol = dehydration_percent * weight * 10
hourly_deficit_rate = (total_deficit_vol - bolus_given) / 48
total_hourly_rate = hydration_rate + hourly_deficit_rate

# --- عرض النتائج في التطبيق ---
col1, col2 = st.columns(2)
with col1:
    st.info(f"**التصنيف:** {severity}")
    st.metric("المعدل الكلي للجريان", f"{total_hourly_rate:.1f} ml/hr")

with col2:
    st.success("**تفاصيل السوائل**")
    st.write(f"💧 سوائل الإماهة: {hydration_rate:.1f} ml/hr")
    st.write(f"📉 تعويض العجز: {hourly_deficit_rate:.1f} ml/hr")

# --- تجهيز بيانات PDF ---
pdf_data = {
    "weight": weight,
    "ph": ph,
    "severity": severity,
    "hydration_rate": hydration_rate,
    "deficit_rate": hourly_deficit_rate,
    "total_rate": total_hourly_rate,
    "insulin_rate": weight * insulin_dose
}

# --- زر التحميل ---
pdf_file = create_pdf(pdf_data)
st.sidebar.download_button(
    label="📄 تحميل التقرير (PDF)",
    data=pdf_file,
    file_name=f"DKA_Report_{weight}kg.pdf",
    mime="application/pdf"
)

st.markdown("""
---
### 🧪 نوع المحلول والتوصيات:
* المحلول: **Plasma-Lyte 148** أو **NaCl 0.9%** مع **40 mmol/L** بوتاسيوم.
* عند انخفاض السكر لـ **14 mmol/L**: أضف **5% جلوكوز** للمحلول.
""")
