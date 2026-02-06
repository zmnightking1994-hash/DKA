import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="BSPED DKA Manager", layout="wide", page_icon="🩺")

# --- دالة إنشاء ملف PDF ---
class DKA_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'DKA Management Plan (BSPED 2021/2024)', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        self.ln(10)

def create_pdf(data):
    pdf = DKA_PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # بيانات المريض
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, "Patient Assessment", 1, 1, 'L', fill=True)
    pdf.cell(95, 10, f"Weight: {data['weight']} kg", 1)
    pdf.cell(95, 10, f"Initial pH: {data['ph']}", 1, 1)
    pdf.cell(95, 10, f"Severity: {data['severity']}", 1)
    pdf.cell(95, 10, f"Dehydration: {data['dehydration']}%", 1, 1)
    pdf.ln(5)

    # حسابات السوائل
    pdf.cell(0, 10, "Fluid Calculations (ml/hr)", 1, 1, 'L', fill=True)
    pdf.cell(95, 10, f"Hydration Rate (Immaha):", 1)
    pdf.cell(95, 10, f"{data['hydration_rate']:.2f} ml/hr", 1, 1)
    pdf.cell(95, 10, f"Deficit Rate (over 48h):", 1)
    pdf.cell(95, 10, f"{data['deficit_rate']:.2f} ml/hr", 1, 1)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(95, 10, f"TOTAL HOURLY RATE:", 1)
    pdf.cell(95, 10, f"{data['total_rate']:.2f} ml/hr", 1, 1)
    pdf.ln(5)

    # الأنسولين والمحاليل
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Therapy Recommendations", 1, 1, 'L', fill=True)
    pdf.cell(0, 10, f"Insulin Rate: {data['insulin_rate']:.2f} Units/hr", 1, 1)
    pdf.multi_cell(0, 10, f"Current Fluid Choice: {data['fluid_choice']}", 1)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 5, "Medical Disclaimer: This document is a clinical aid. Final decisions must be made by a qualified clinician based on bedside assessment.")
    
    return pdf.output()

# --- واجهة التطبيق ---
st.title("🩺 مساعد تدبير الحماض الكيتوني السكري للأطفال")
st.markdown("##### تطبيق تفاعلي مبني على بروتوكول BSPED 2024")

# --- المدخلات ---
with st.sidebar:
    st.header("📊 بيانات المريض")
    weight = st.number_input("الوزن (كجم)", min_value=1.0, max_value=150.0, value=20.0)
    ph = st.number_input("قيمة الـ pH الأولي", min_value=6.7, max_value=7.5, value=7.1, step=0.01)
    current_bg = st.number_input("الجلوكوز الحالي (mmol/L)", min_value=0.0, value=20.0, step=0.1)
    bolus_given = st.number_input("سوائل الإنعاش المعطاة (ml)", min_value=0, value=0)
    
    st.divider()
    insulin_dose = st.select_slider("معدل الأنسولين (Units/kg/hr)", options=[0.05, 0.1], value=0.1)

# --- المنطق الحسابي (BSPED Logic) ---

# 1. تحديد الجفاف والشدة
if ph < 7.1:
    dehydration, severity = 10, "Severe (شديد)"
elif ph < 7.2:
    dehydration, severity = 5, "Moderate (متوسط)"
else:
    dehydration, severity = 5, "Mild (خفيف)"

# 2. حساب سوائل الإماهة (Maintenance) - قاعدة 2/0.5/0.2
def calculate_hydration(w):
    if w <= 10:
        rate = w * 2
    elif w <= 20:
        rate = 20 + (w - 10) * 0.5
    else:
        rate = 25 + (w - 20) * 0.2
    return min(rate, 80) # الحد الأقصى للإماهة 80 مل/ساعة

hydration_rate = calculate_hydration(weight)

# 3. حساب العجز (Deficit) على 48 ساعة
total_deficit_vol = (dehydration * weight * 10) - bolus_given
deficit_hourly_rate = total_deficit_vol / 48

# 4. المجموع الكلي
total_hourly_rate = hydration_rate + deficit_hourly_rate
insulin_rate = weight * insulin_dose

# --- عرض النتائج ---
c1, c2 = st.columns(2)

with c1:
    st.info(f"**تصنيف الحالة:** {severity}")
    st.metric("المعدل الكلي للسوائل الوريدية", f"{total_hourly_rate:.2f} ml/hr")
    st.write(f"💧 سوائل الإماهة: {hydration_rate:.2f} ml/hr")
    st.write(f"📉 تعويض العجز: {deficit_hourly_rate:.2f} ml/hr")

with c2:
    st.warning("🧪 نوع المحلول والتوصيات")
    fluid_advice = ""
    if current_bg > 14:
        fluid_advice = "0.9% NaCl or Plasma-Lyte 148 + 40mmol/L KCL"
        st.write("✅ استخدم محلول **بدون جلوكوز**")
    elif 6 <= current_bg <= 14:
        fluid_advice = "0.9% NaCl or Plasma-Lyte 148 + 5% Glucose + 40mmol/L KCL"
        st.write("⚠️ أضف **5% جلوكوز** للمحلول")
    else:
        fluid_advice = "0.9% NaCl or Plasma-Lyte 148 + 10% Glucose + 40mmol/L KCL"
        st.error("🚨 خطر: استخدم **10% جلوكوز**")
    
    st.metric("جرعة الأنسولين", f"{insulin_rate:.2f} Units/hr")

st.divider()

# --- قوائم المراقبة ---
col_m1, col_m2 = st.columns(2)

with col_m1:
    st.subheader("🚨 علامات وذمة الدماغ")
    st.checkbox("صداع حاد أو متزايد")
    st.checkbox("تباطؤ نبض القلب (Bradycardia)")
    st.checkbox("تدهور مستوى الوعي (GCS)")
    st.checkbox("قيء متكرر غير مرتبط بالحموضة")

with col_m2:
    st.subheader("✅ معايير التحسن (Resolution)")
    st.checkbox("الـ pH > 7.3")
    st.checkbox("الكيتونات في الدم < 1.0 mmol/L")
    st.checkbox("الطفل قادر على الأكل والشرب")

# --- توليد وتحميل التقرير ---
report_data = {
    "weight": weight,
    "ph": ph,
    "severity": severity,
    "dehydration": dehydration,
    "hydration_rate": hydration_rate,
    "deficit_rate": deficit_hourly_rate,
    "total_rate": total_hourly_rate,
    "insulin_rate": insulin_rate,
    "fluid_choice": fluid_advice
}

if st.button("توليد تقرير PDF"):
    pdf_output = create_pdf(report_data)
    st.download_button(
        label="📥 تحميل التقرير الآن",
        data=pdf_output,
        file_name=f"DKA_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )

st.divider()
st.caption("ملاحظة: هذا التطبيق للاستخدام الاسترشادي فقط. المرجع النهائي هو دليل BSPED المعتمد في مستشفاكم.")
