"""Shared application configuration and AI prompt templates."""

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
GEMINI_MODELS = [
    'gemini-3.6-flash',
    'gemini-3.5-flash-lite',
    'gemini-3.5-flash',
    'gemini-3.0-pro',
    'gemini-2.5-pro',
    'gemini-2.0-flash',
    'gemini-1.5-pro',
    'gemini-1.5-flash'
]
AI_REPORT_DELIMITER = '===BATAS_PDF==='
ALL_SUBJECTS_OPTION = 'Semua Mata Pelajaran'

AI_REPORT_PROMPT_TEMPLATE = """\
Berdasarkan data nilai siswa berikut:

{data_summary}

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
