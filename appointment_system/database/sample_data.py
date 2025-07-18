# =============================================================================
# appointment_system/database/sample_data.py
# =============================================================================
"""
Minta adatok generálása teszteléshez
"""
from datetime import time, datetime, timedelta
from typing import List
from ..models.doctor import Doctor, DoctorSpecialization, WorkingHours
from ..models.appointment import Appointment, AppointmentStatus, PatientInfo

def generate_sample_doctors() -> List[Doctor]:
    """Minta orvosok generálása"""
    
    doctors = [
        Doctor(
            id="doc_001",
            name="Kovács János",
            specialization=DoctorSpecialization.INTERNAL_MEDICINE,
            location="Budapest",
            address="1052 Budapest, Petőfi Sándor u. 12.",
            phone="+36 1 234 5678",
            email="kovacs.janos@medcenter.hu",
            working_hours=[
                WorkingHours("monday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                WorkingHours("tuesday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                WorkingHours("wednesday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                WorkingHours("thursday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                WorkingHours("friday", time(8, 0), time(14, 0)),
            ],
            rating=4.8,
            description="Tapasztalt belgyógyász, 15 éves szakmai gyakorlattal. Szívbetegségek és diabetes specialista.",
            languages=["magyar", "angol"]
        ),
        Doctor(
            id="doc_002",
            name="Nagy Éva",
            specialization=DoctorSpecialization.NEUROLOGY,
            location="Budapest",
            address="1051 Budapest, Arany János u. 8.",
            phone="+36 1 345 6789",
            email="nagy.eva@neurocenter.hu",
            working_hours=[
                WorkingHours("monday", time(9, 0), time(17, 0), time(13, 0), time(14, 0)),
                WorkingHours("tuesday", time(9, 0), time(17, 0), time(13, 0), time(14, 0)),
                WorkingHours("wednesday", time(9, 0), time(17, 0), time(13, 0), time(14, 0)),
                WorkingHours("thursday", time(9, 0), time(17, 0), time(13, 0), time(14, 0)),
            ],
            rating=4.9,
            description="Neurológus specialista, fejfájás és migrén kezelésben jártas. Sztrók rehabilitációs tapasztalattal.",
            languages=["magyar", "német"]
        ),
        Doctor(
            id="doc_003",
            name="Szabó Péter",
            specialization=DoctorSpecialization.CARDIOLOGY,
            location="Budapest",
            address="1065 Budapest, Bajcsy-Zsilinszky út 25.",
            phone="+36 1 456 7890",
            email="szabo.peter@cardio.hu",
            working_hours=[
                WorkingHours("monday", time(8, 0), time(16, 0)),
                WorkingHours("tuesday", time(8, 0), time(16, 0)),
                WorkingHours("wednesday", time(8, 0), time(16, 0)),
                WorkingHours("thursday", time(8, 0), time(16, 0)),
                WorkingHours("friday", time(8, 0), time(12, 0)),
            ],
            rating=4.7,
            description="Kardiológus, szívritmus zavarok és magas vérnyomás kezelésében specialista. Pacemaker implantáció.",
            languages=["magyar", "angol"]
        ),
        Doctor(
            id="doc_004",
            name="Takács Anna",
            specialization=DoctorSpecialization.DERMATOLOGY,
            location="Budapest",
            address="1064 Budapest, Váci út 45.",
            phone="+36 1 567 8901",
            email="takacs.anna@derma.hu",
            working_hours=[
                WorkingHours("tuesday", time(10, 0), time(18, 0), time(14, 0), time(15, 0)),
                WorkingHours("wednesday", time(10, 0), time(18, 0), time(14, 0), time(15, 0)),
                WorkingHours("thursday", time(10, 0), time(18, 0), time(14, 0), time(15, 0)),
                WorkingHours("friday", time(10, 0), time(16, 0)),
            ],
            rating=4.6,
            description="Bőrgyógyász, allergiák és bőrbetegségek kezelésében jártas. Kozmetikai dermatológia specialista.",
            languages=["magyar", "francia"]
        ),
        Doctor(
            id="doc_005",
            name="Horváth Zoltán",
            specialization=DoctorSpecialization.GENERAL_PRACTITIONER,
            location="Budapest",
            address="1053 Budapest, Kecskeméti u. 14.",
            phone="+36 1 678 9012",
            email="horvath.zoltan@haziorvos.hu",
            working_hours=[
                WorkingHours("monday", time(7, 0), time(15, 0), time(11, 0), time(12, 0)),
                WorkingHours("tuesday", time(7, 0), time(15, 0), time(11, 0), time(12, 0)),
                WorkingHours("wednesday", time(7, 0), time(15, 0), time(11, 0), time(12, 0)),
                WorkingHours("thursday", time(7, 0), time(15, 0), time(11, 0), time(12, 0)),
                WorkingHours("friday", time(7, 0), time(13, 0)),
            ],
            rating=4.5,
            description="Háziorvos, általános orvosi problémák kezelésében tapasztalt. Családi medicina specialista.",
            languages=["magyar"]
        ),
        Doctor(
            id="doc_006",
            name="Varga Klára",
            specialization=DoctorSpecialization.GYNECOLOGY,
            location="Budapest",
            address="1054 Budapest, Széchenyi rkp. 19.",
            phone="+36 1 789 0123",
            email="varga.klara@noi.hu",
            working_hours=[
                WorkingHours("monday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                WorkingHours("tuesday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                WorkingHours("wednesday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                WorkingHours("friday", time(8, 0), time(14, 0)),
            ],
            rating=4.9,
            description="Nőgyógyász, terhesség követés és női betegségek kezelésében specialista.",
            languages=["magyar", "angol"]
        ),
        Doctor(
            id="doc_007",
            name="Molnár Gábor",
            specialization=DoctorSpecialization.ORTHOPEDICS,
            location="Budapest",
            address="1062 Budapest, Andrássy út 66.",
            phone="+36 1 890 1234",
            email="molnar.gabor@ortoped.hu",
            working_hours=[
                WorkingHours("monday", time(9, 0), time(17, 0), time(13, 0), time(14, 0)),
                WorkingHours("tuesday", time(9, 0), time(17, 0), time(13, 0), time(14, 0)),
                WorkingHours("thursday", time(9, 0), time(17, 0), time(13, 0), time(14, 0)),
                WorkingHours("friday", time(9, 0), time(15, 0)),
            ],
            rating=4.8,
            description="Ortopéd sebész, ízületi problémák és sporttraumák kezelésében specialista.",
            languages=["magyar", "német"]
        ),
        Doctor(
            id="doc_008",
            name="Tóth Márta",
            specialization=DoctorSpecialization.PEDIATRICS,
            location="Budapest",
            address="1056 Budapest, Belgrád rkp. 24.",
            phone="+36 1 901 2345",
            email="toth.marta@gyerek.hu",
            working_hours=[
                WorkingHours("monday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                WorkingHours("tuesday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                WorkingHours("wednesday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                WorkingHours("thursday", time(8, 0), time(16, 0), time(12, 0), time(13, 0)),
                WorkingHours("friday", time(8, 0), time(14, 0)),
            ],
            rating=4.7,
            description="Gyermekorvos, csecsemő és gyermekgyógyászat specialista. Fejlődési problémák kezelése.",
            languages=["magyar", "angol"]
        )
    ]
    
    return doctors

def generate_sample_appointments() -> List[Appointment]:
    """Minta foglalások generálása"""
    
    appointments = []
    
    # Minta páciensek
    sample_patients = [
        PatientInfo(
            name="Kovács Anna",
            age=35,
            gender="nő",
            phone="+36 30 123 4567",
            email="kovacs.anna@email.com",
            symptoms=["fejfájás", "szédülés"],
            diagnosis="Migrén",
            medical_history=["magas vérnyomás"],
            medications=["vérnyomáscsökkentő"]
        ),
        PatientInfo(
            name="Nagy Péter",
            age=42,
            gender="férfi",
            phone="+36 30 234 5678",
            email="nagy.peter@email.com",
            symptoms=["mellkasi fájdalom", "légszomj"],
            diagnosis="Szívritmus zavar",
            medical_history=["diabetes"],
            medications=["metformin"]
        ),
        PatientInfo(
            name="Szabó Éva",
            age=28,
            gender="nő",
            phone="+36 30 345 6789",
            email="szabo.eva@email.com",
            symptoms=["kiütés", "viszketés"],
            diagnosis="Allergiás reakció",
            medical_history=[],
            medications=[]
        )
    ]
    
    # Minta foglalások generálása
    base_date = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    
    for i, patient in enumerate(sample_patients):
        appointment_date = base_date + timedelta(days=i+1)
        
        appointment = Appointment(
            id=f"sample_apt_{i+1:03d}",
            doctor_id=f"doc_{i+1:03d}",
            patient_info=patient,
            datetime=appointment_date,
            duration_minutes=30,
            status=AppointmentStatus.CONFIRMED,
            notes="Minta foglalás - Medical Chatbot rendszerből"
        )
        
        appointments.append(appointment)
    
    return appointments