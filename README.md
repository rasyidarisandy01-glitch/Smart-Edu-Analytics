# Smart Edu Analytics - Asisten AI Guru

Platform analisis nilai siswa yang didukung oleh AI untuk membantu guru mengevaluasi hasil belajar siswa dengan objektif sekaligus memberikan umpan balik yang menjaga kesehatan mental dan motivasi belajar siswa.

## Fitur Utama

- **Analisis Nilai Siswa**: Upload file Excel nilai siswa dan dapatkan analisis komprehensif
- **Dukungan Dual AI**: 
  - **Ollama (Lokal)**: AI yang berjalan di komputer Anda tanpa kuota atau biaya
  - **Gemini API (Cloud)**: AI dari Google dengan performa tinggi (butuh internet dan API key)
- **Edu-Chat**: Ajukan pertanyaan terkait nilai siswa dengan konteks berdasarkan data yang diunggah; riwayat percakapan dipertahankan saat berpindah menu
- **Visualisasi Interaktif**: Grafik perkembangan nilai siswa menggunakan Plotly
- **Export Laporan**: 
  - Unduh hasil analisis dalam format teks (TXT)
  - Unduh laporan lengkap dalam format PDF dengan tabel dan grafik
- **Desain Responsif**: Antarmuka yang bersih dan mudah digunakan

## Cara Menggunakan

### 1. Persyaratan Sistem
Pastikan Anda telah menginstall:
- Python 3.7+
- Paket Python yang diperlukan (lihat bagian Instalasi di bawah)

### 2. Instalasi
```bash
# Install paket yang diperlukan
pip install streamlit pandas plotly google-generativeai requests fpdf2 matplotlib

# Untuk fitur AI Lokal (Ollama):
# 1. Download dan install Ollama dari https://ollama.com/
# 2. Jalankan Ollama: ollama serve
# 3. Pull model yang diinginkan (default: gemma4:e2b):
#    ollama pull gemma4:e2b
# Jika belum punya model AI, bisa di download dari situs https://ollama.com/search

# Untuk fitr AI Cloud (Gemini API):
# 1. Dapatkan API key dari https://makersuite.google.com/app/apikey
# 2. Masukkan API key di sidebar aplikasi
```

### 3. Menjalankan Aplikasi
```bash
# Navigasi ke direktori proyek
cd path/to/smart_edu_analytics

# Jalankan aplikasi
streamlit run app.py
```

### 4. Menggunakan Aplikasi
1. Buka browser dan navigasi ke `http://localhost:8501`
2. Upload file Excel nilai siswa dengan kolom:
   - Nama Siswa
   - Mata Pelajaran
   - Bulan
   - Topik
   - Nilai
3. Pilih siswa yang ingin dianalisis dari dropdown
4. Pilih mesin AI yang diinginkan di sidebar:
   - **Ollama (Lokal)**: Tidak butuh API key, tapi pastikan Ollama berjalan
   - **Gemini API (Cloud)**: Butuh API key Google Gemini yang valid
5. Klik tombol "🤖 Buat Analisis AI"
6. Tunggu proses analisis selesai
7. Hasil analisis akan ditampilkan bersama dengan grafik
8. Unduh laporan:
   - 📥 **Unduh Laporan Analisis (Teks)**: Hasil analisis dalam format teks
   - 📄 **Unduh Laporan PDF Lengkap**: Laporan lengkap dengan tabel, grafik, dan teks

## Struktur File

```
smart_edu_analytics/
├── app.py              # Entry point dan antarmuka Streamlit
├── config.py           # Konstanta, konfigurasi AI, dan template prompt
├── data_utils.py       # Persiapan data dan analitik berbasis Pandas
├── visualizations.py   # Factory grafik Plotly
├── pdf_generator.py    # Pembuatan dan ekspor laporan PDF
├── ai_services.py      # Integrasi provider AI dan pemrosesan respons
├── logo.png            # Logo sekolah (opsional untuk laporan PDF)
└── README.md           # File ini
```

## Konfigurasi AI

### Ollama (Lokal)
- Model default: `gemma4:e2b` (bisa diubah di sidebar)
- Tidak memerlukan API key
- Berjalan sepenuhnya di komputer lokal Anda
- Cocok untuk privasi data dan tanpa biaya penggunaan

### Gemini API (Cloud)
- Memerlukan API key Google Gemini yang valid
- Model yang tersedia:
  - gemini-3.6-flash (default)
  - gemini-3.5-flash-lite
  - gemini-3.5-flash
  - gemini-3.0-pro
  - gemini-2.5-pro
  - gemini-1.5-pro
  - gemini-1.5-flash
- Memerlukan koneksi internet
- Mendapatkan kuota harian dari Google (lihat https://makersuite.google.com untuk detail)

## Format File Excel yang Didukung

File Excel harus memiliki kolom berikut:

| Nama Siswa | Mata Pelajaran | Bulan | Topik | Nilai |
|------------|----------------|-------|-------|-------|
| Budi Santoso | Matematika | Januari | Aljabar | 85 |
| Budi Santoso | Matematika | Februari | Peluang | 90 |
| ... | ... | ... | ... | ... |

**Catatan**: 
- Kolom "Bulan" harus menggunakan nama bulan lengkap (Januari, Februari, etc.)
- Nilai harus dalam format angka
- File harus dalam format .xlsx

## Hasil Analisis

Setelah analisis selesai, Anda akan mendapatkan:

1. **Visualisasi Interaktif**: Grafik garis yang menunjukkan perkembangan nilai dari waktu ke waktu
2. **Metrik Statistik**: Nilai rata-rata, tertinggi, terendah, dan terakhir
3. **Analisis AI**: 
   - Sorotan prestasi (mata pelajaran dengan nilai tertinggi)
   - Area pengembangan (mata pelajaran yang perlu perhatian)
   - Rencana tindak lanjut (3 langkah konkret)
   - Pesan motivasi untuk siswa
4. **Opsi Unduh**:
   - Format teks untuk catatan cepat
   - Format PDF lengkap untuk dokumentasi dan distribusi

## Privasi dan Keamanan

- **Ollama (Lokal)**: Data tidak pernah meninggalkan komputer Anda
- **Gemini API (Cloud)**: Data dikirim ke server Google untuk diproses (pastikan Anda memahami kebijakan privasi Google)
- File Excel yang diupload hanya disimpan di memori selama sesi aktif dan tidak disimpan permanen

## Tips Penggunaan

1. Untuk hasil terbaik, gunakan data yang lengkap dan konsisten
2. Pastikan nama bulan ditulis lengkap dan sesuai standar (Januari, Februari, etc.)
3. Jika menggunakan Ollama, pastikan layanan Ollama berjalan di background
4. Untuk Gemini API, perhatikan kuota harian Anda untuk menghindari masalah rate limit
5. Laporan PDF cocok untuk distribusi kepada orang tua atau dokumentasi sekolah

## Pengembangan Lanjutan

Jika Anda ingin mengembangkan aplikasi ini lebih lanjut, beberapa area yang bisa ditingkatkan:

- Penambahan jenis visualisasi lain (bar chart, heatmap, etc.)
- Integrasi dengan sistem sekolah atau LMS
- Penambahan fitur perbandingan antar siswa atau antar kelas
- Ekspor ke format lain seperti Word atau HTML
- Implementasi sistem login dan manajemen pengguna

## Lisensi

Proyek ini dikembangkan untuk tujuan edukational dan boleh digunakan serta dimodifikasi secara bebas.

---
*Smart Edu Analytics - Asisten AI Guru | Dibangun dengan Streamlit, Pandas, Plotly, dan Google Gemini AI*
