## Smart Edu Analytics: Platform Analisis Nilai Siswa Berbasis Dual-Mode AI
Smart Edu Analytics adalah platform analitik akademik inovatif yang dirancang untuk mengotomatisasi evaluasi nilai siswa bagi guru. Dibangun dengan memprioritaskan stabilitas (Minimum Viable Product/MVP) dan keamanan privasi, platform ini secara instan mengubah data nilai mentah (Excel/CSV) menjadi wawasan pedagogik visual dan laporan PDF.

Proyek ini mengatasi masalah beban kerja administratif guru—yang rata-rata menghabiskan 11 jam per minggu untuk rekapitulasi nilai—dengan memangkas waktu pemrosesan menjadi di bawah 30 detik per kelas.

# Fitur Unggulan
Dual-Mode AI (Hybrid): Sistem asisten cerdas (Edu-Chat) yang fleksibel. Dapat berjalan di Cloud menggunakan Google Gemini API (untuk performa maksimal) atau secara lokal/Offline menggunakan Ollama (untuk sekolah dengan kendala internet atau kebijakan privasi ketat).

Smart Context Injection (RAG-Lite): AI dirancang 100% bebas dari halusinasi data. AI secara ketat diinstruksikan untuk hanya memberikan analisis, wawasan, dan saran pedagogik berdasarkan angka riil yang diunggah oleh guru.

Sistem Otorisasi Multi-Peran (RBAC-Lite):

Guru (Eksekutor): Dapat mengunggah data, melihat analisis kelas, berinteraksi dengan Edu-Chat, dan mencetak laporan individu.

Kepala Sekolah (Pemantau): Memiliki akses Read-Only ke Dasbor Eksekutif untuk memantau performa sekolah secara menyeluruh tanpa risiko mengubah data.

Orang Tua (Privat): Jalur login khusus berbasis NISN (tanpa password) untuk mengakses grafik perkembangan nilai eksklusif milik anaknya saja, menjaga privasi antar siswa.

Visualisasi Data Interaktif: Menyajikan metrik komprehensif melalui Radar Chart kompetensi, grafik Line Chart pergerakan bulanan, dan deteksi Focus Area secara otomatis.

Generator PDF Siap Cetak (Massal & Individu): Mengekspor hasil analisis visual dan narasi rekomendasi AI ke dalam format dokumen resmi sekolah dengan sekali klik (termasuk fitur pembuatan ZIP massal untuk satu kelas).

Academic Early Warning System: Secara proaktif menyoroti siswa yang rata-rata nilainya berada di bawah KKM atau mengalami penurunan drastis pada dua bulan berurutan, membantu guru mengambil tindakan preventif (misalnya remedial atau konseling BK).

# Teknologi yang Digunakan (Pendekatan STEAM)
Proyek ini dikembangkan secara efisien menggunakan tumpukan teknologi Open-Source (Biaya Operasional Rp 0):

Bahasa Utama: Python 3.10+

Frontend & State Management: Streamlit (dengan Custom CSS Glassmorphism & Mock Database in-memory)

Pemrosesan Data & Matematika: Pandas

Visualisasi: Plotly Express & Graph Objects

Mesin AI (Cloud): Google Gemini API (gemini-1.5-flash dll.)

Mesin AI (Offline): Ollama (gemma4:e2b dll.)

Dokumen (Seni & Rekayasa): FPDF (Pembuat Laporan PDF), Matplotlib (Render grafik statis), Zipfile

# Cara Instalasi & Menjalankan Aplikasi Lokal
Ikuti langkah-langkah berikut untuk menjalankan Smart Edu Analytics di komputer Anda:

1. Kloning Repositori
Bash
git clone https://github.com/username-anda/smart-edu-analytics.git
cd smart-edu-analytics
2. Buat Virtual Environment (Opsional tapi disarankan)
Bash
python -m venv venv
- Untuk Windows:
venv\Scripts\activate
- Untuk Mac/Linux:
source venv/bin/activate
3. Instal Dependensi
Pastikan Anda menginstal seluruh pustaka yang diperlukan:

Bash
pip install streamlit pandas plotly requests fpdf2 matplotlib google-generativeai openpyxl
4. Konfigurasi Kosmetik UI (Opsional)
Untuk tampilan level Enterprise, pastikan file konfigurasi tema berada pada jalurnya:

Buat folder .streamlit dan pastikan file .streamlit/config.toml berisi pengaturan primary color dan dark mode.

Pastikan file background (contoh: bg_login.jpg) berada di direktori akar yang sama dengan app.py.

5. Jalankan Aplikasi
Bash
streamlit run app.py
Aplikasi akan otomatis terbuka di browser melalui http://localhost:8501.

# Panduan Penggunaan (Alur Demo)
Sistem ini didesain menggunakan manajemen memori sementara (session state) untuk presentasi live-demo yang stabil. Sangat disarankan menjalankan alur ini di SATU tab browser yang sama.

Fase 1 (Guru):

Login menggunakan tab Login Staf Sekolah. (Contoh demo kredensial: Username guru_ipa, Password 123).

Unduh templat Excel yang disediakan atau gunakan Data_Nilai_Multi_Subject_Ekstrem.xlsx (dari skrip generate_excel.py).

Unggah (Upload) file tersebut.

Buka tab Class Analytics untuk melihat ringkasan rata-rata kelas.

Buka tab Analisis Individu, pilih siswa spesifik, buat (generate) wawasan AI, dan unduh laporan PDF.

Tekan Logout.

Fase 2 (Kepala Sekolah):

Login dengan kredensial Kepsek (Contoh demo: Username kepsek, Password 123).

Anda akan melihat grafik dasbor data yang sama, tetapi fitur Chat AI dan unggah akan dikunci (Read-Only).

Tekan Logout.

Fase 3 (Orang Tua):

Di halaman login, pilih tab Cek Rapor Siswa (Wali Murid).

Masukkan NISN anak (Contoh demo: 12345).

Sistem akan langsung menampilkan Radar Chart dan tren nilai khusus untuk anak tersebut tanpa membocorkan data siswa lain.

# Pengembangan ke Depan (Roadmap)
Smart Edu Analytics versi saat ini adalah bentuk Minimum Viable Product (MVP). Untuk penyebaran skala penuh di institusi pendidikan, direkomendasikan untuk:

Mengganti in-memory dictionary (Mock Database) dengan API ke database relasional sungguhan (seperti MySQL, PostgreSQL, atau integrasi langsung ke sistem Dapodik).

Menerapkan Parental AI Assistant yang secara spesifik dirancang untuk memberikan saran pengasuhan berbasis data (Data-driven parenting) bagi orang tua di rumah.

Membangun manajemen kredensial (Hashing/JWT) untuk otentikasi level produksi.

# Lisensi & Atribusi
Proyek ini dibangun untuk tujuan edukasi dan inovasi akademik. Seluruh komponen bersumber dari teknologi open-source.

Dikembangkan oleh: [team_name / my_name]