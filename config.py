"""Shared application configuration and AI prompt templates."""

import os

import google.generativeai as genai

KKM = 70
MONTH_ORDER = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]

TEMPLATE_COLUMNS = [
    'Nama Siswa', 'Kelas', 'Mata Pelajaran', 'Bulan', 'Topik', 'Nilai'
]

OLLAMA_ENGINE = 'Ollama (Lokal - Tanpa Kuota)'
GEMINI_ENGINE = 'Gemini API (Cloud - Butuh Internet)'
DEFAULT_OLLAMA_MODEL = 'gemma4:e2b'
DEFAULT_OLLAMA_HOST = 'http://localhost:11434'


def get_default_ollama_host():
    """Resolve Ollama base URL from Streamlit secrets, env, or localhost."""
    secret_host = None
    try:
        import streamlit as st
        secret_host = st.secrets.get('OLLAMA_HOST')
    except Exception:
        secret_host = None

    host = secret_host or os.getenv('OLLAMA_HOST') or DEFAULT_OLLAMA_HOST
    return str(host).strip().rstrip('/')


GEMINI_MODELS = [
    'gemini-3.8-flash',
    'gemini-3.6-flash',
    'gemini-3.5-flash-lite',
    'gemini-3.1-pro',
    'gemini-3.1-flash-lite',
]
_AVAILABLE_MODELS_CACHE = {}
AI_REPORT_DELIMITER = '===BATAS_PDF==='
ALL_SUBJECTS_OPTION = 'Semua Mata Pelajaran'

AI_REPORT_PROMPT_TEMPLATE = """\
Berdasarkan data nilai siswa berikut:

{data_summary}

Tanggal analisis saat ini: {analysis_date}.
Tuliskan tanggal analisis dengan format DD Bulan YYYY. JANGAN gunakan teks
placeholder [Tanggal Hari Ini]. Gunakan tanda hubung biasa (-) untuk rentang
waktu dan hindari karakter spesial.

INFORMASI KRUSIAL TENTANG STANDAR NILAI:
Asumsikan Kriteria Ketuntasan Minimal (KKM) adalah 70. Jika nilai rata-rata atau nilai keseluruhan siswa berada jauh di bawah KKM (misalnya rentang 10 - 50), JANGAN PERNAH menggunakan frasa pujian palsu seperti "pencapaian yang baik", "potensi besar", atau "usaha yang baik". Bersikaplah realistis, objektif, dan nyatakan bahwa siswa berada dalam kondisi akademik yang kritis/membutuhkan intervensi segera.

Berdasarkan data nilai siswa ini, buatkan DUA laporan terpisah dalam satu balasan.

**BAGIAN 1 (Untuk Guru & Sekolah):**
Berisi analisis tren, *focus area* (kelemahan/kekuatan materi), dan rekomendasi strategi pedagogik untuk dianalisis oleh Guru BK/Wali Kelas. Gunakan bahasa profesional layaknya sedang rapat dan kamu sedang memberikan hasil analisismu.

Tuliskan `{delimiter}` di baris baru sebagai pemisah.

**BAGIAN 2 (Untuk Orang Tua):**
Berisi surat laporan perkembangan akademik yang hangat dan memotivasi. Hindari bahasa teknis/AI. Berikan focus area (kelemahan/kekuatan materi). Berikan saran kepada orang tua untuk meningkatkan kekuatan akademik anak. Fokus pada apresiasi pencapaian dan berikan tips praktis gaya belajar atau pendampingan di rumah.

PENTING: DILARANG menggunakan format tabel markdown di kedua bagian.

PENTING: JANGAN pernah menuliskan salam penutup surat apa pun seperti 'Hormat kami', 'Salam hangat', atau '[Nama Ahli Pendidikan/Guru]'. Akhiri laporanmu tepat setelah poin saran terakhir.
"""


def configure_gemini(api_key):
    """Configure the Gemini SDK with the supplied user API key."""
    genai.configure(api_key=api_key)


def create_gemini_model(model_name):
    """Create a configured Gemini generative model."""
    return genai.GenerativeModel(model_name)


def get_available_gemini_models(api_key=None):
    """Retrieve available Gemini models supporting text generation.

    Caches results per API key and falls back to GEMINI_MODELS on error or missing key.
    """
    if not api_key or not str(api_key).strip():
        return GEMINI_MODELS

    cleaned_key = str(api_key).strip()
    if cleaned_key in _AVAILABLE_MODELS_CACHE:
        return _AVAILABLE_MODELS_CACHE[cleaned_key]

    try:
        configure_gemini(cleaned_key)
        fetched_models = []
        for model in genai.list_models():
            methods = getattr(model, 'supported_generation_methods', []) or []
            model_name = getattr(model, 'name', '') or ''
            if 'generateContent' in methods and 'gemini-' in model_name:
                cleaned_name = model_name.replace('models/', '', 1)
                if cleaned_name not in fetched_models:
                    fetched_models.append(cleaned_name)

        if not fetched_models:
            return GEMINI_MODELS

        primary_models = [m for m in GEMINI_MODELS if m in fetched_models]
        other_models = sorted([m for m in fetched_models if m not in primary_models])
        sorted_models = primary_models + other_models

        _AVAILABLE_MODELS_CACHE[cleaned_key] = sorted_models
        return sorted_models
    except Exception:
        return GEMINI_MODELS
