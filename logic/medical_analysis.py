# =============================================================================
# logic/medical_analysis.py
# =============================================================================
"""
Orvosi elemzés és triage döntések.
"""
import re
from core import ALTERNATIVE_TIPS

def triage_decision(data):
    """Triage döntés a betegadatok alapján."""
    symptoms = data.get("symptoms", [])
    severity = data.get("severity", "")
    duration = data.get("duration", "")
    
    # Biztonságosabb regex kezelés
    duration_days = 0
    if duration:
        match = re.search(r"\d+", duration)
        if match:
            try:
                duration_days = int(match.group())
            except ValueError:
                duration_days = 0

    # Sürgős esetek
    if "mellkasi fájdalom" in symptoms or "légszomj" in symptoms:
        return "🔴 A tünetei alapján azonnali egészségügyi ellátás javasolt."
    
    # Közepes sürgősség
    elif severity == "súlyos" or ("láz" in symptoms and "torokfájás" in symptoms and duration_days > 3):
        return "🟡 Javasolt orvossal konzultálnia."
    
    # Enyhe esetek
    else:
        return "🔵 A tünetei alapján valószínűleg elegendő lehet az otthoni megfigyelés."

def alternative_recommendations(symptoms):
    """Alternatív terápiás javaslatok a tünetek alapján."""
    if not symptoms:
        return "Nincs elegendő tünet az alternatív javaslatok megadásához."
    
    tips = []
    for symptom in symptoms:
        if symptom in ALTERNATIVE_TIPS:
            tips.append(f"**{symptom.title()}:** {ALTERNATIVE_TIPS[symptom]}")
    
    return "\n".join(tips) if tips else "Nincs specifikus alternatív javaslat ezekre a tünetekre."

def assess_symptom_severity(symptoms, severity, duration):
    """Tünetek súlyosságának értékelése."""
    risk_factors = []
    
    # Magas kockázatú tünetek
    high_risk_symptoms = ["mellkasi fájdalom", "légszomj", "eszméletvesztés", "erős fejfájás"]
    for symptom in high_risk_symptoms:
        if symptom in symptoms:
            risk_factors.append(f"Magas kockázatú tünet: {symptom}")
    
    # Súlyosság értékelése
    if severity == "súlyos":
        risk_factors.append("Páciens súlyosnak ítéli a tüneteket")
    
    # Időtartam értékelése
    if duration and "hét" in duration.lower():
        risk_factors.append("Tünetek egy hete vagy hosszabb ideje tartanak")
    
    return risk_factors

def generate_medical_summary(patient_data, diagnosis, triage_level, alt_therapy, gpt_alt_therapy, specialist_advice):
    """Teljes orvosi összefoglaló generálása."""
    summary = {
        "patient_info": {
            "age": patient_data.get("age"),
            "gender": patient_data.get("gender"),
            "symptoms": patient_data.get("symptoms", []),
            "duration": patient_data.get("duration"),
            "severity": patient_data.get("severity"),
            "existing_conditions": patient_data.get("existing_conditions", []),
            "medications": patient_data.get("medications", [])
        },
        "medical_assessment": {
            "triage_level": triage_level,
            "diagnosis": diagnosis,
            "alternative_therapy": alt_therapy,
            "gpt_alternative_therapy": gpt_alt_therapy,
            "specialist_advice": specialist_advice
        },
        "risk_assessment": assess_symptom_severity(
            patient_data.get("symptoms", []),
            patient_data.get("severity"),
            patient_data.get("duration")
        )
    }
    
    return summary