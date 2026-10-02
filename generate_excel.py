import pandas as pd
import random

# Set seed agar hasil konsisten setiap kali di-run
random.seed(42)

mapel_list = ['Matematika', 'Fisika', 'Kimia', 'Bahasa Indonesia']

# Daftar topik per mata pelajaran
bulan_topik = {
    'Matematika': [('Agustus', 'Aljabar'), ('September', 'Matriks'), ('Oktober', 'Geometri'), ('November', 'Trigonometri')],
    'Fisika': [('Agustus', 'Kinematika'), ('September', 'Dinamika'), ('Oktober', 'Usaha & Energi'), ('November', 'Momentum')],
    'Kimia': [('Agustus', 'Struktur Atom'), ('September', 'Sistem Periodik'), ('Oktober', 'Ikatan Kimia'), ('November', 'Stoikiometri')],
    'Bahasa Indonesia': [('Agustus', 'Laporan Observasi'), ('September', 'Hikayat'), ('Oktober', 'Negosiasi'), ('November', 'Debat')]
}

nama_depan = ['Budi', 'Ani', 'Siti', 'Agus', 'Dewi', 'Joko', 'Ayu', 'Rudi', 'Dina', 'Eko',
              'Rina', 'Fajar', 'Maya', 'Hendra', 'Nur', 'Gilang', 'Putri', 'Aditya', 'Sari', 'Bayu',
              'Rizky', 'Indah', 'Kusuma', 'Ahmad', 'Wati', 'Dimas', 'Lestari', 'Irfan', 'Sri', 'Dedi']
nama_belakang = ['Santoso', 'Wijaya', 'Pratama', 'Sari', 'Kurniawan', 'Wahyuni', 'Setiawan', 'Lestari', 'Hidayat', 'Putri']

# Generate 20 siswa unik untuk Kelas X IPA 1
siswa_kelas_1 = []
while len(siswa_kelas_1) < 20:
    nama = f"{random.choice(nama_depan)} {random.choice(nama_belakang)}"
    if nama not in siswa_kelas_1:
        siswa_kelas_1.append(nama)

# Generate 20 siswa unik untuk Kelas X IPA 2
siswa_kelas_2 = []
while len(siswa_kelas_2) < 20:
    nama = f"{random.choice(nama_depan)} {random.choice(nama_belakang)}"
    if nama not in siswa_kelas_2 and nama not in siswa_kelas_1:
        siswa_kelas_2.append(nama)

data = []

# Masukkan data untuk X IPA 1
for nama in siswa_kelas_1:
    for mapel in mapel_list:
        # Berikan profil nilai acak per siswa per mapel
        profil = random.choice(['terjun_bebas', 'naik_drastis', 'rollercoaster', 'stabil_rendah', 'stabil_tinggi'])
        for bulan, topik in bulan_topik[mapel]:
            if profil == 'terjun_bebas':
                nilai = random.choice([random.randint(80, 95), random.randint(60, 75), random.randint(40, 55), random.randint(20, 35)])
            elif profil == 'naik_drastis':
                nilai = random.choice([random.randint(25, 40), random.randint(50, 65), random.randint(70, 85), random.randint(88, 100)])
            elif profil == 'rollercoaster':
                nilai = random.choice([random.randint(75, 90), random.randint(30, 45), random.randint(80, 95), random.randint(28, 45)])
            elif profil == 'stabil_rendah':
                nilai = random.randint(30, 65)
            else:
                nilai = random.randint(75, 98)
            data.append([nama, 'X IPA 1', mapel, bulan, topik, nilai])

# Masukkan data untuk X IPA 2
for nama in siswa_kelas_2:
    for mapel in mapel_list:
        profil = random.choice(['terjun_bebas', 'naik_drastis', 'rollercoaster', 'stabil_rendah', 'stabil_tinggi'])
        for bulan, topik in bulan_topik[mapel]:
            if profil == 'terjun_bebas':
                nilai = random.choice([random.randint(80, 95), random.randint(60, 75), random.randint(40, 55), random.randint(20, 35)])
            elif profil == 'naik_drastis':
                nilai = random.choice([random.randint(25, 40), random.randint(50, 65), random.randint(70, 85), random.randint(88, 100)])
            elif profil == 'rollercoaster':
                nilai = random.choice([random.randint(75, 90), random.randint(30, 45), random.randint(80, 95), random.randint(28, 45)])
            elif profil == 'stabil_rendah':
                nilai = random.randint(30, 65)
            else:
                nilai = random.randint(75, 98)
            data.append([nama, 'X IPA 2', mapel, bulan, topik, nilai])

# Simpan ke file Excel baru
df = pd.DataFrame(data, columns=['Nama Siswa', 'Kelas', 'Mata Pelajaran', 'Bulan', 'Topik', 'Nilai'])
nama_file = 'Data_Nilai_Multi_Subject_Ekstrem.xlsx'
df.to_excel(nama_file, index=False)

print(f"✅ File {nama_file} berhasil dibuat dengan 2 kelas, 4 mata pelajaran, dan total {len(df)} baris data!")