# =============================================================================
# logic/__init__.py
# =============================================================================
"""
Logic modul - üzleti logika és orvosi elemzések.
"""
from .data_extraction import extract_all_medical_info
from .gpt_communication import (
    generate_diagnosis, 
    generate_alt_therapy, 
    generate_specialist_advice,
    get_next_question_gpt,
    get_next_question_static
)
from .medical_analysis import (
    triage_decision, 
    alternative_recommendations, 
    assess_symptom_severity,
    generate_medical_summary
)
from .chat_processor import (
    process_chat_input_enhanced, 
    is_evaluation_complete,
    get_evaluation_status
)
from .symptom_graph import (
    get_next_reasoning_question,
    has_reasoning_questions_available
)
from .prompt_builder import build_complete_prompt

__all__ = [
    'extract_all_medical_info',
    'generate_diagnosis',
    'generate_alt_therapy', 
    'generate_specialist_advice',
    'get_next_question_gpt',
    'get_next_question_static',
    'triage_decision',
    'alternative_recommendations',
    'assess_symptom_severity',
    'generate_medical_summary',
    'process_chat_input_enhanced',
    'is_evaluation_complete',
    'get_evaluation_status'
]