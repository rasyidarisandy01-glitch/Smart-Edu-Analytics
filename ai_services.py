"""AI provider calls and report prompt/response handling."""

import logging
import re

import requests

from config import (
    AI_REPORT_DELIMITER,
    AI_REPORT_PROMPT_TEMPLATE,
    GEMINI_ENGINE,
    create_gemini_model,
)
from data_utils import build_student_data_summary

logger = logging.getLogger(__name__)

FALLBACK_PARENT_REPORT = (
    'Laporan khusus orang tua tidak tersedia pada respons AI ini. '
    'Silakan buat ulang analisis untuk memperoleh surat laporan akademik '
    'dan saran pendampingan belajar di rumah.'
)
OLLAMA_CHAT_ERROR_MESSAGE = (
    'Maaf, data terlalu besar atau tidak dapat diproses oleh AI Lokal. '
    'Silakan gunakan pertanyaan yang lebih spesifik atau beralih ke '
    'Mode Gemini (Cloud).'
)
OLLAMA_CHAT_LIMITATION_NOTICE = (
    '\n\n---\n'
    '⚠️ **Catatan Sistem:** *Anda menggunakan AI Lokal. Karena batas memori, '
    'AI mungkin tidak membaca seluruh data siswa (terpotong). Untuk akurasi '
    'data 100% pada seluruh kelas, gunakan Mode Gemini (Cloud) / model AI berkualitas.*'
)

_PARENT_SIGNOFF_PATTERN = re.compile(
    r'(?:^|\n)\s*(?:hormat\s+kami|salam(?:\s+hangat|\s+sejahtera)?|'
    r'dengan\s+hormat)\s*,?\s*(?:\n\s*\[[^\]\n]*\])?\s*$',
    re.IGNORECASE
)
_PARENT_NAME_PLACEHOLDER_PATTERN = re.compile(
    r'\s*\[Nama (?:Ahli Pendidikan/Guru|Guru/Wali Kelas)\]\s*$',
    re.IGNORECASE
)


def clean_parent_report(text):
    cleaned = str(text or '').replace('\r\n', '\n').replace('\r', '\n').strip()
    cleaned = re.sub(
        r'(?i)(Hormat kami|Salam hangat|Hormat saya).*',
        '',
        cleaned,
        flags=re.DOTALL
    ).strip()
    cleaned = _PARENT_SIGNOFF_PATTERN.sub('', cleaned).rstrip()
    cleaned = _PARENT_NAME_PLACEHOLDER_PATTERN.sub('', cleaned).rstrip()
    return cleaned


def call_ollama_api(prompt, model='llama2'):
    """Call a local Ollama instance and return its generated text."""
    url = 'http://localhost:11434/api/chat'
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'stream': False
    }
    response = requests.post(url, json=payload, timeout=(5, 120))
    if response.status_code == 404:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={'model': model, 'prompt': prompt, 'stream': False},
            timeout=(5, 120)
        )

    response.raise_for_status()
    result = response.json()
    if 'message' in result:
        text = result['message'].get('content', '')
    else:
        text = result.get('response', '')
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Ollama mengembalikan respons kosong atau tidak valid.')
    return text


def build_student_report_prompt(student_name, student_data):
    data_summary = build_student_data_summary(student_name, student_data)
    return AI_REPORT_PROMPT_TEMPLATE.format(
        data_summary=data_summary,
        delimiter=AI_REPORT_DELIMITER
    )


def generate_ai_response(
    engine, prompt, api_key=None, model_name=None
):
    if engine == GEMINI_ENGINE:
        if not api_key:
            raise ValueError('API Key Gemini diperlukan untuk mode Cloud')
        from config import configure_gemini

        configure_gemini(api_key)
        model = create_gemini_model(model_name)
        response = model.generate_content(
            prompt, request_options={'timeout': 120}
        )
        return response.text
    return call_ollama_api(prompt, model=model_name or 'llama2')


def generate_chat_response(
    query,
    context_data,
    ai_mode,
    api_key=None,
    model_name=None,
    local_memory_limit=3000
):
    context_text = str(context_data or '')
    is_local_ai = 'Ollama' in ai_mode
    if is_local_ai and len(context_text) > local_memory_limit:
        context_text = (
            context_text[:local_memory_limit]
            + '\n...[Data dipotong karena keterbatasan memori lokal]'
        )

    system_prompt = (
        'Anda adalah Edu-Chat, asisten konsultan pendidikan profesional untuk guru.\n'
        'Aturan menjawab:\n'
        '1. Untuk pertanyaan terkait statistik, nilai, nama siswa, atau tren kelas, '
        'Anda WAJIB menjawab HANYA berdasarkan Data Konteks berikut. Jangan '
        'mengarang data.\n'
        '2. JIKA guru meminta saran pedagogik, metode pembelajaran, atau solusi '
        'atas masalah nilai yang turun (seperti Trigonometri), JAWABLAH '
        'menggunakan pengetahuan umum Anda sebagai ahli pendidikan yang relevan '
        "dengan masalah di Data Konteks tersebut. Jangan katakan 'data tidak "
        "menyebutkannya' untuk pertanyaan berupa saran/opini."
    )
    prompt = (
        f'{system_prompt}\n\n'
        f'Data Konteks:\n{context_text}\n\n'
        f'Pertanyaan guru:\n{query}'
    )
    if ai_mode == GEMINI_ENGINE:
        if not api_key:
            raise ValueError('API Key Gemini diperlukan untuk mode Cloud.')
        from config import configure_gemini

        configure_gemini(api_key)
        model = create_gemini_model(model_name)
        response = model.generate_content(
            prompt, request_options={'timeout': 120}
        )
        text = response.text
    elif is_local_ai:
        try:
            text = call_ollama_api(prompt, model=model_name or 'llama2')
        except Exception:
            logger.exception('Gagal memperoleh jawaban Edu-Chat dari Ollama')
            return OLLAMA_CHAT_ERROR_MESSAGE
        if not isinstance(text, str) or not text.strip():
            logger.warning('Ollama mengembalikan jawaban Edu-Chat kosong')
            return OLLAMA_CHAT_ERROR_MESSAGE
    else:
        raise ValueError(f'Mode AI Edu-Chat tidak dikenal: {ai_mode}')

    if not isinstance(text, str) or not text.strip():
        raise ValueError('Edu-Chat tidak menghasilkan jawaban yang valid.')
    final_response = text.strip()
    if is_local_ai:
        final_response += OLLAMA_CHAT_LIMITATION_NOTICE
    return final_response


def split_ai_report(response_text):
    parts = response_text.split(AI_REPORT_DELIMITER, maxsplit=1)
    if len(parts) != 2:
        return response_text.strip(), FALLBACK_PARENT_REPORT, False

    teacher_report = parts[0].replace(
        'BAGIAN 1 (Untuk Guru & Sekolah)', ''
    ).strip()
    parent_report = parts[1].replace(
        'BAGIAN 2 (Untuk Orang Tua)', ''
    ).strip()
    parent_report = clean_parent_report(parent_report)
    if not teacher_report:
        teacher_report = 'Analisis untuk guru tidak tersedia pada respons AI ini.'
    if not parent_report:
        parent_report = FALLBACK_PARENT_REPORT
    return teacher_report, parent_report, True
