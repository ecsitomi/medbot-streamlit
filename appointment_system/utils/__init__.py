# =============================================================================
# appointment_system/utils/__init__.py
# =============================================================================
"""
Segéd funkciók
"""

def format_phone_number(phone: str) -> str:
    """Telefonszám formázása"""
    # Alapvető formázás
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    if len(clean_phone) == 11 and clean_phone.startswith('36'):
        return f"+{clean_phone[:2]} {clean_phone[2:4]} {clean_phone[4:7]} {clean_phone[7:]}"
    elif len(clean_phone) == 9:
        return f"+36 {clean_phone[:2]} {clean_phone[2:5]} {clean_phone[5:]}"
    
    return phone

def generate_reference_number() -> str:
    """Referencia szám generálása"""
    import random
    import string
    
    # APT-YYYYMMDD-XXXX formátum
    from datetime import datetime
    
    today = datetime.now().strftime("%Y%m%d")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    return f"APT-{today}-{random_suffix}"

def validate_email(email: str) -> bool:
    """Email cím validálása"""
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Telefonszám validálása"""
    import re
    
    # Magyar telefonszám formátumok
    patterns = [
        r'^\+36\s?\d{2}\s?\d{3}\s?\d{4}$',  # +36 30 123 4567
        r'^06\s?\d{2}\s?\d{3}\s?\d{4}$',    # 06 30 123 4567
        r'^\d{2}\s?\d{3}\s?\d{4}$'          # 30 123 4567
    ]
    
    for pattern in patterns:
        if re.match(pattern, phone.strip()):
            return True
    
    return False