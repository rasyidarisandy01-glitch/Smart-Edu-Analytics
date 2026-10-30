import streamlit as st
import pandas as pd
import requests
import io
import importlib
import zipfile
import logging
import tempfile
import os
import base64

def set_background(image_file):
    """Fungsi untuk memasang gambar latar belakang lokal secara offline"""
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()
    
    css = f"""
    <style>
    /* Menggabungkan warna gelap transparan (overlay) langsung ke gambar background */
    .stApp {{
        background-image: linear-gradient(rgba(14, 17, 23, 0.7), rgba(14, 17, 23, 0.7)), url("data:image/jpeg;base64,{encoded_string}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* Membuat kontainer konten transparan agar tidak ada kotak yang terpotong */
    .block-container {{
        background-color: transparent;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    
    /* Menyembunyikan elemen bawaan Streamlit (opsional) */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# PANGGILAN FUNGSI
# set_background('bg_edu.jpg')

logger = logging.getLogger(__name__)
from config import (
    DEFAULT_OLLAMA_MODEL,
    GEMINI_ENGINE,
    GEMINI_MODELS,
    ALL_SUBJECTS_OPTION,
    KKM,
    OLLAMA_ENGINE,
    TEMPLATE_COLUMNS,
    configure_gemini,
)
# Load data helpers before services and visualizations that also depend on them.
import data_utils as _data_utils
importlib.reload(_data_utils)
build_chat_context_summary = _data_utils.build_chat_context_summary

from data_utils import (
    filter_student_subject,
    filter_subjects,
    get_class_early_warning,
    get_class_metrics,
    generate_teacher_recommendation,
    get_student_rankings,
    get_student_ranking_tables,
    get_students_for_class,
    get_subjects_for_student,
    get_unique_classes,
    get_unique_subjects,
    ordered_months as _ordered_months,
    prepare_class_subject_data,
    prepare_uploaded_dataframe,
)
from ai_services import (
    build_student_report_prompt,
    generate_ai_response,
    generate_chat_response,
    split_ai_report as _split_ai_report,
)
import pdf_generator as _pdf_generator
importlib.reload(_pdf_generator)
generate_pdf = _pdf_generator.generate_pdf
from visualizations import (
    class_monthly_trend,
    class_topic_average_bar,
    individual_monthly_trend,
    student_subject_radar,
    subject_average_bar,
    topic_average_bar,
)

ENGLISH_TO_INDONESIAN_MONTH = {
    'january': 'Januari',
    'february': 'Februari',
    'march': 'Maret',
    'april': 'April',
    'may': 'Mei',
    'june': 'Juni',
    'july': 'Juli',
    'august': 'Agustus',
    'september': 'September',
    'october': 'Oktober',
    'november': 'November',
    'december': 'Desember',
}


def _standardize_month_names(months):
    normalized_months = months.astype('string').str.strip().str.lower()
    translated_months = normalized_months.map(
        ENGLISH_TO_INDONESIAN_MONTH
    ).fillna(normalized_months)
    return translated_months.str.title()


def _select_student_for_individual_analysis(kelas, nama_siswa):
    st.session_state['individual_class_selection'] = kelas
    st.session_state['individual_student_selection'] = nama_siswa
    st.session_state['menu_tab'] = '\U0001F9D1\u200D\U0001F393 Analisis Individu'
    st.session_state['early_warning_selection_updated'] = True
    st.rerun()


def _render_edu_chat():
    if 'df' not in st.session_state or st.session_state.df is None:
        st.warning(
            'Silakan unggah dan proses data nilai terlebih dahulu di tab sebelumnya.'
        )
        st.stop()

    st.subheader('💬 Edu-Chat')
    st.caption(
        'Tanyakan tentang data nilai yang tersedia. Edu-Chat hanya menjawab '
        'berdasarkan ringkasan data konteks.'
    )

    chat_ai_mode = st.radio(
        'Pilih AI untuk Edu-Chat:',
        options=[OLLAMA_ENGINE, GEMINI_ENGINE],
        horizontal=True,
        key='edu_chat_ai_mode'
    )
    if chat_ai_mode == GEMINI_ENGINE:
        local_memory_limit = 3000
        chat_api_key = st.text_input(
            'Gemini API Key untuk Edu-Chat',
            type='password',
            key='edu_chat_gemini_api_key'
        )
        chat_model = st.selectbox(
            'Model Gemini untuk Edu-Chat',
            options=GEMINI_MODELS,
            key='edu_chat_gemini_model'
        )
    else:
        chat_api_key = None
        with st.expander(
            '⚙️ Pengaturan Lanjutan AI Lokal',
            expanded=False
        ):
            local_memory_limit = st.slider(
                'Batas Memori Konteks (Karakter)',
                min_value=1000,
                max_value=15000,
                value=3000,
                step=500,
                key='edu_chat_local_memory_limit'
            )
            st.info(
                '💡 **Info:** Semakin tinggi nilai ini, semakin banyak data '
                'siswa yang bisa dibaca AI. Namun, butuh RAM/VGA PC yang lebih '
                'tinggi. Jika AI merespons kosong/error, turunkan batas ini.'
            )
        chat_model = st.text_input(
            'Model Ollama untuk Edu-Chat',
            value=DEFAULT_OLLAMA_MODEL,
            key='edu_chat_ollama_model'
        )

    chat_history = st.session_state['chat_history']
    for message in chat_history:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    query = st.chat_input('Tanyakan sesuatu tentang data nilai...')
    if query:
        chat_history.append({'role': 'user', 'content': query})
        with st.chat_message('user'):
            st.markdown(query)
        context_dataframe = st.session_state.df
        detected_student = None
        if (
            context_dataframe is not None
            and not context_dataframe.empty
            and 'Nama Siswa' in context_dataframe.columns
        ):
            daftar_nama = (
                context_dataframe['Nama Siswa']
                .dropna()
                .astype('string')
                .str.strip()
            )
            nama_yang_ditanyakan = [
                nama for nama in daftar_nama.unique()
                if nama and nama.casefold() in query.casefold()
            ]
            if nama_yang_ditanyakan:
                detected_student = max(
                    nama_yang_ditanyakan, key=len
                )

        if detected_student:
            df_fokus = context_dataframe.loc[
                context_dataframe['Nama Siswa']
                .astype('string')
                .str.contains(
                    detected_student,
                    case=False,
                    na=False,
                    regex=False
                )
            ].copy()
            detail_columns = [
                'Nama Siswa', 'Mata Pelajaran', 'Topik', 'Bulan', 'Nilai'
            ]
            focused_csv = df_fokus.reindex(
                columns=detail_columns
            ).to_csv(index=False, na_rep='Tidak tersedia')
            focused_summary = build_chat_context_summary(
                df_fokus,
                selected_student=detected_student,
                kkm=KKM
            )
            context_data = (
                'Data Spesifik Siswa yang Ditanyakan:\n'
                f'{focused_csv}\n'
                'Ringkasan data siswa tersebut:\n'
                f'{focused_summary}'
            )
        else:
            selected_student = st.session_state.get(
                'individual_student_selection'
            )
            context_data = build_chat_context_summary(
                context_dataframe,
                selected_student=selected_student,
                kkm=KKM
            )
        try:
            with st.spinner('Edu-Chat sedang menyiapkan jawaban...'):
                response = generate_chat_response(
                    query,
                    context_data,
                    chat_ai_mode,
                    api_key=chat_api_key,
                    model_name=chat_model,
                    local_memory_limit=local_memory_limit,
                    chat_history=chat_history[:-1]
                )
            chat_history.append({'role': 'assistant', 'content': response})
            with st.chat_message('assistant'):
                st.markdown(response)
        except Exception as error:
            logger.exception('Gagal membuat respons Edu-Chat')
            error_message = str(error).lower()
            if (
                isinstance(
                    error,
                    (
                        TimeoutError,
                        requests.exceptions.Timeout,
                        requests.exceptions.ConnectionError,
                    )
                )
                or 'timeout' in error_message
                or 'deadline exceeded' in error_message
                or 'connection' in error_message
                or 'network' in error_message
            ):
                st.error(
                    'Gagal terhubung ke layanan AI. Silakan coba beberapa saat lagi '
                    'atau pastikan koneksi internet stabil (untuk mode Cloud).'
                )
            else:
                st.error(f'Gagal membuat respons Edu-Chat: {error}')


# Konfigurasi halaman
st.set_page_config(
    page_title='Smart Edu Analytics - Asisten AI Guru',
    page_icon='🎓',
    layout='wide'
)

# --- INJEKSI CUSTOM CSS UNTUK UI POLISHING ---
st.markdown("""
    <style>
    /* Hide the menu hamburger pojok kanan atas */
    #MainMenu {visibility: hidden;}
    
    /* Hide tulisan 'Made with Streamlit' di footer */
    footer {visibility: hidden;}
    
    /* tombol primer (seperti tombol AI) */
    .stButton>button[kind="primary"] {
        border-radius: 8px;
        font-weight: bold;
        background-color: #2E66F6; /* Warna biru profesional */
        border: none;
        transition: 0.3s;
    }
    
    /* tombol sekunder (seperti tombol download) */
    .stButton>button[kind="secondary"] {
        border-radius: 8px;
        transition: 0.3s;
    }
    </style>
    """, unsafe_allow_html=True)

if 'hasil_ai' not in st.session_state:
    st.session_state['hasil_ai'] = None
if 'hasil_ai_context' not in st.session_state:
    st.session_state['hasil_ai_context'] = None
if not isinstance(st.session_state.get('chat_history'), list):
    st.session_state['chat_history'] = []

LOGIN_CREDENTIALS = {
    # Demo-only credentials; replace with a proper identity provider in production.
    'guru_ipa': {'password': '123', 'role': 'Guru'},
    'kepsek': {'password': '123', 'role': 'Kepala Sekolah'},
}

if not st.session_state.get('logged_in', False):
    login_column = st.columns([1, 1.4, 1])[1]
    with login_column:
        st.title('Login Smart Edu Analytics')
        staff_login_tab, parent_login_tab = st.tabs([
            'Login Staf Sekolah',
            'Cek Rapor Siswa (Wali Murid) 🔒',
        ])
        with staff_login_tab:
            with st.form('login_form'):
                username = st.text_input('Username')
                password = st.text_input('Password', type='password')
                submitted = st.form_submit_button('Masuk')

            if submitted:
                account = LOGIN_CREDENTIALS.get(username)
                if account and password == account['password']:
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = account['role']
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.error('Username atau Password salah')
                    st.caption(
                        "Untuk demo, buka tab 'Cek Rapor Siswa (Wali Murid)' "
                        "dan masukkan NISN '12345'."
                    )

        with parent_login_tab:
            with st.form('parent_login_form'):
                nisn = st.text_input('Masukkan NISN Siswa')
                parent_submitted = st.form_submit_button('Lihat Rapor')

            if parent_submitted:
                if nisn.strip() == '12345':
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = 'Orang Tua'
                    st.session_state['nisn_aktif'] = '12345'
                    st.rerun()
                else:
                    st.error('NISN tidak ditemukan.')
    st.stop()

role = st.session_state['role']

# Judul aplikasi
if role == 'Orang Tua':
    st.title('📄 Dasbor Analitik Siswa')
else:
    st.title('🎓 Smart Edu Analytics - Dashboard Guru')
    st.markdown(
        '*Platform analisis nilai siswa yang didukung oleh AI untuk guru '
        'yang peduli*'
    )

# Sidebar untuk API Key dan konfigurasi model
with st.sidebar:
    if role == 'Guru':
        st.header('Konfigurasi AI')

        ai_engine = st.radio(
            label='Pilih Mesin AI:',
            options=[OLLAMA_ENGINE, GEMINI_ENGINE],
            horizontal=True
        )

        st.markdown('---')

        if ai_engine == OLLAMA_ENGINE:
            ollama_model = st.text_input(
                label='Model Ollama:',
                value=DEFAULT_OLLAMA_MODEL,
                help='Masukkan nama model Ollama yang tersedia (contoh: gemma4:e2b, qwen3, llama2, dll.)'
            )
            st.info(f'Model Ollama yang akan digunakan: {ollama_model}')
            api_key = None
            gemini_model = GEMINI_MODELS[0]
        else:
            api_key = st.text_input(
                label='Masukkan Gemini API Key:',
                type='password',
                help='Dapatkan API key dari https://makersuite.google.com/app/apikey'
            )
            if api_key:
                try:
                    configure_gemini(api_key)
                    st.success('API Key berhasil dikonfigurasi!')
                except Exception as e:
                    st.error(f'Gagal konfigurasi API Key: {str(e)}')
            else:
                st.info('Silakan masukkan Gemini API Key untuk menggunakan fitur AI')

            st.markdown('---')
            gemini_model = st.selectbox(
                label='Pilih Model Gemini:',
                options=GEMINI_MODELS,
                index=0
            )
            st.info(f'Model Gemini yang akan digunakan: {gemini_model}')
            ollama_model = DEFAULT_OLLAMA_MODEL

        st.markdown('---')
        st.caption(
            '⚠️ Catatan Rate Limit: Tekan tombol Generate hanya ketika '
            'diperlukan untuk menghindari quota exceeded (hanya untuk Gemini API)'
        )
        if ai_engine == OLLAMA_ENGINE:
            st.info(
                '🔒 **Privasi Lokal:** Data dikirim hanya ke layanan Ollama '
                'yang berjalan di mesin lokal Anda.'
            )
        else:
            st.warning(
                '☁️ **Pemrosesan Cloud:** Data yang dikirim ke Gemini API '
                'diproses oleh layanan Google. Pastikan penggunaan sesuai '
                'kebijakan privasi sekolah.'
            )

        with st.expander('⚙️ Pengaturan Cetak Laporan'):
            include_ai_analysis = st.checkbox(
                'Sertakan Halaman Analisis & Rekomendasi AI',
                value=True
            )
            nama_wali_kelas = st.text_input(
                'Nama Wali Kelas',
                placeholder='Masukkan nama wali kelas'
            ).strip()
            nama_kepala_sekolah = st.text_input(
                'Nama Kepala Sekolah',
                placeholder='Masukkan nama kepala sekolah'
            ).strip()
            signature_principal_upload = st.file_uploader(
                'Unggah Tanda Tangan Kepala Sekolah',
                type=['png'],
                key='signature_principal_upload'
            )
            signature_homeroom_upload = st.file_uploader(
                'Unggah Tanda Tangan Wali Kelas',
                type=['png'],
                key='signature_homeroom_upload'
            )

        def _get_signature_png(uploaded_image, label):
            if uploaded_image is None:
                return None
            image_bytes = uploaded_image.getvalue()
            if not image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
                st.error(f'{label} bukan gambar PNG yang valid.')
                return None
            return image_bytes

        tanda_tangan_kepala_sekolah = _get_signature_png(
            signature_principal_upload, 'Tanda tangan Kepala Sekolah'
        )
        tanda_tangan_wali_kelas = _get_signature_png(
            signature_homeroom_upload, 'Tanda tangan Wali Kelas'
        )
        if st.button('Logout'):
            keys_to_delete = ['logged_in', 'role', 'username']
            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    elif role == 'Kepala Sekolah':
        st.info('👁️ Mode Pemantau Eksekutif - Kepala Sekolah')
        if st.button('Logout'):
            keys_to_delete = ['logged_in', 'role', 'username']
            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    else:
        if st.button('Logout'):
            keys_to_delete = ['logged_in', 'role', 'username']
            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

if role == 'Orang Tua':
    if 'master_df' not in st.session_state:
        st.warning('Data rapor belum dipublikasikan oleh sekolah.')
        st.stop()

    master_df = st.session_state['master_df']
    if master_df.empty or 'Nama Siswa' not in master_df.columns:
        st.warning('Data rapor belum dipublikasikan oleh sekolah.')
        st.stop()

    active_nisn = str(st.session_state.get('nisn_aktif', '12345')).strip()
    nisn_column = next(
        (
            column for column in master_df.columns
            if str(column).strip().casefold() == 'nisn'
        ),
        None
    )
    if nisn_column is not None:
        normalized_nisn = (
            master_df[nisn_column]
            .astype('string')
            .str.strip()
            .str.replace(r'\.0$', '', regex=True)
        )
        student_records = master_df.loc[
            normalized_nisn == active_nisn
        ].copy()
        if student_records.empty:
            st.warning('Data rapor untuk NISN ini belum ditemukan.')
            st.stop()
    else:
        student_names = (
            master_df['Nama Siswa'].dropna().astype('string').str.strip()
        )
        if student_names.empty:
            st.warning('Data rapor belum dipublikasikan oleh sekolah.')
            st.stop()
        matched_name = next(
            (
                name for name in student_names.unique()
                if name.casefold() == 'joko wahyuni'
            ),
            str(student_names.iloc[0])
        )
        student_records = master_df.loc[
            master_df['Nama Siswa']
            .astype('string')
            .str.strip()
            == matched_name
        ].copy()

    parent_student_name = str(
        student_records['Nama Siswa'].iloc[0]
    ).strip()
    st.subheader(
        f'Selamat datang, Orang Tua/Wali dari {parent_student_name}.'
    )
    parent_student_class = (
        str(student_records['Kelas'].iloc[0])
        if 'Kelas' in student_records.columns else 'Tidak tersedia'
    )
    if 'Bulan' in student_records.columns:
        student_records['Bulan'] = _ordered_months(
            student_records['Bulan']
        )

    student_scores = pd.to_numeric(
        student_records.get('Nilai', pd.Series(dtype='float64')),
        errors='coerce'
    )
    average_score = student_scores.mean()
    average_score_display = (
        f'{average_score:.1f}' if pd.notna(average_score)
        else 'Tidak tersedia'
    )
    if 'Topik' in student_records.columns:
        topic_averages = (
            student_records.assign(_nilai_numerik=student_scores)
            .groupby('Topik', observed=True)['_nilai_numerik']
            .mean()
            .dropna()
        )
    else:
        topic_averages = pd.Series(dtype='float64')
    strongest_topic = (
        str(topic_averages.idxmax())
        if not topic_averages.empty else 'Tidak tersedia'
    )
    focus_area = (
        str(topic_averages.idxmin())
        if not topic_averages.empty else 'Tidak tersedia'
    )

    metric_columns = st.columns(3)
    metric_columns[0].metric('Rata-rata Nilai', average_score_display)
    metric_columns[1].metric('Materi Terkuat', strongest_topic)
    metric_columns[2].metric('Area Fokus', focus_area)

    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.subheader('Tren Nilai Bulanan')
        parent_trend_figure = individual_monthly_trend(student_records)
        if parent_trend_figure is None:
            st.info('Belum ada data nilai untuk ditampilkan.')
        else:
            st.plotly_chart(parent_trend_figure, use_container_width=True)

    with chart_columns[1]:
        st.subheader('Radar Kompetensi')
        parent_radar_figure = student_subject_radar(student_records)
        if parent_radar_figure is None:
            st.info('Belum ada data untuk membuat grafik radar.')
        else:
            st.plotly_chart(parent_radar_figure, use_container_width=True)

    try:
        parent_pdf = generate_pdf(
            parent_student_name,
            parent_student_class,
            student_records,
            '',
            include_ai_analysis=False
        )
        safe_student_name = ''.join(
            character if character.isalnum() or character in ' -_.' else '_'
            for character in parent_student_name
        ).strip(' .') or 'Siswa'
        st.download_button(
            label='Unduh Laporan PDF',
            data=parent_pdf,
            file_name=f'Laporan_{safe_student_name}.pdf',
            mime='application/pdf'
        )
    except Exception as pdf_error:
        logger.exception('Gagal membuat laporan PDF untuk Orang Tua')
        st.error(f'Gagal membuat laporan PDF: {pdf_error}')
    st.stop()

uploaded_file = None
if role == 'Guru':
    template_buffer = io.BytesIO()
    pd.DataFrame(columns=TEMPLATE_COLUMNS).to_excel(template_buffer, index=False)
    template_buffer.seek(0)
    st.download_button(
        label='📥 Unduh Template Excel',
        data=template_buffer.getvalue(),
        file_name='Template_Nilai_Siswa.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    uploaded_file = st.file_uploader(
        'Unggah file Excel (.xlsx) atau CSV (.csv)',
        type=['xlsx', 'csv'],
        help='File harus memiliki kolom: Nama Siswa, Kelas, Mata Pelajaran, Bulan, Topik, Nilai'
    )

# Upload berhasil
if uploaded_file is not None or st.session_state.get('df') is not None:
    if uploaded_file is not None:
        try:
            if uploaded_file.name.lower().endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
        except Exception:
            logger.exception('Format file unggahan tidak dapat dibaca')
            st.warning(
                'Format file tidak sesuai. Pastikan ada kolom Nama Siswa, Mata Pelajaran, dan Nilai.'
            )
            st.stop()
        if 'Bulan' in df.columns:
            df['Bulan'] = _standardize_month_names(df['Bulan'])
    else:
        df = st.session_state['df']

    try:
        
        essential_columns = ['Nama Siswa', 'Mata Pelajaran', 'Nilai']
        if any(col not in df.columns for col in essential_columns):
            st.warning(
                'Format file tidak sesuai. Pastikan ada kolom Nama Siswa, Mata Pelajaran, dan Nilai.'
            )
            st.stop()

        # Validasi struktur data dasar
        if df.empty:
            st.error('File Excel kosong. Silakan unggah file yang berisi data.')
            st.stop()
        
        # Tampilan 5 baris pertama data
        if role == 'Guru':
            with st.expander(
                'Pratinjau Data Mentah (5 Baris Pertama)', expanded=False
            ):
                st.dataframe(df.head(), use_container_width=True)
        
        missing_columns = [
            col for col in TEMPLATE_COLUMNS if col not in df.columns
        ]
        
        if missing_columns:
            st.error("⚠️ Format kolom tidak sesuai. Silakan gunakan template yang disediakan.")
            st.stop()
        else:
            df, rows_without_identity, invalid_scores = (
                prepare_uploaded_dataframe(df)
            )
            if rows_without_identity:
                st.warning(
                    f'{rows_without_identity} baris tanpa nama siswa atau kelas '
                    'diabaikan.'
                )
            if df.empty:
                st.error('Tidak ada baris dengan nama siswa dan kelas yang valid.')
                st.stop()
            st.session_state.df = df
            st.session_state.master_df = df.copy()

            if invalid_scores:
                st.warning(
                    f'{invalid_scores} nilai kosong atau bukan angka akan '
                    'diabaikan dalam perhitungan.'
                )

            unique_classes = get_unique_classes(df)
            if not unique_classes:
                st.error('Tidak ada data kelas yang valid dalam file.')
                st.stop()

            if role == 'Guru':
                st.success('Semua kolom yang diharapkan tersedia!')
            menu_individu = '\U0001F9D1\u200D\U0001F393 Analisis Individu'
            menu_kelas = '\U0001F4C8 Class Analytics'
            menu_chat = '💬 Edu-Chat'
            menu_options = (
                [menu_individu, menu_kelas, menu_chat]
                if role == 'Guru'
                else [menu_kelas]
            )
            if 'menu_tab' not in st.session_state:
                st.session_state['menu_tab'] = menu_options[0]
            elif st.session_state['menu_tab'] not in menu_options:
                st.session_state['menu_tab'] = menu_options[0]
            menu_tab = st.radio(
                'Pilih menu analisis:',
                options=menu_options,
                horizontal=True,
                key='menu_tab'
            )

            if menu_tab == menu_individu:
            
                # === LOGIKA PEMPROSESAN DATA ===
            
                st.subheader('Pilih Kelas dan Siswa untuk Analisis')
                kelas_terpilih = st.selectbox(
                    'Pilih Kelas:',
                    options=unique_classes,
                    key='individual_class_selection'
                )
                class_df = df[df['Kelas'] == kelas_terpilih]

                unique_students = get_students_for_class(
                    df, kelas_terpilih
                )
                if not unique_students:
                    st.error('Tidak ada data siswa yang valid untuk kelas ini.')
                    st.stop()

                if st.button('🗂️ Generate Laporan Satu Kelas (ZIP)'):
                    total_siswa = len(unique_students)
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    with tempfile.NamedTemporaryFile(
                        suffix='.zip', delete=False
                    ) as temporary_zip:
                        zip_file_path = temporary_zip.name
                    teks_ai_massal = "Analisis AI individual tidak disertakan dalam laporan massal untuk mengoptimalkan waktu pemrosesan. Untuk melihat analisis akademik AI lengkap dan rekomendasi pembelajaran, gunakan mode analisis individu."
                    max_zip_size = 100 * 1024 * 1024
                    nama_kelas_aman = ''.join(
                        karakter if karakter.isalnum() or karakter in ' -_.' else '_'
                        for karakter in str(kelas_terpilih)
                    ).strip(' .') or 'Kelas'
                    used_filenames = set()

                    try:
                        with zipfile.ZipFile(
                            zip_file_path, 'w', compression=zipfile.ZIP_DEFLATED
                        ) as zip_file:
                            for i, nama_siswa in enumerate(unique_students):
                                data_siswa = class_df[
                                    class_df['Nama Siswa'] == nama_siswa
                                ].copy()
                                data_siswa['Bulan'] = _ordered_months(
                                    data_siswa['Bulan']
                                )
                                pdf_bytes = generate_pdf(
                                    str(nama_siswa),
                                    kelas_terpilih,
                                    data_siswa,
                                    teks_ai_massal,
                                    nama_kepala_sekolah=nama_kepala_sekolah,
                                    nama_wali_kelas=nama_wali_kelas,
                                    tanda_tangan_kepala_sekolah=tanda_tangan_kepala_sekolah,
                                    tanda_tangan_wali_kelas=tanda_tangan_wali_kelas,
                                    include_ai_analysis=include_ai_analysis
                                )
                                nama_file_aman = ''.join(
                                    karakter if karakter.isalnum() or karakter in ' -_.' else '_'
                                    for karakter in str(nama_siswa)
                                ).strip(' .') or 'Siswa'
                                entry_name = f'Laporan_{nama_file_aman}.pdf'
                                suffix = 2
                                while entry_name in used_filenames:
                                    entry_name = (
                                        f'Laporan_{nama_file_aman}_{suffix}.pdf'
                                    )
                                    suffix += 1
                                used_filenames.add(entry_name)
                                zip_file.writestr(entry_name, pdf_bytes)
                                del pdf_bytes, data_siswa

                                if os.path.getsize(zip_file_path) > max_zip_size:
                                    raise ValueError(
                                        'Ukuran ZIP melebihi batas 100 MB untuk '
                                        'melindungi penggunaan memori server. '
                                        'Bagi ekspor berdasarkan kelas yang lebih kecil.'
                                    )
                                progress_bar.progress((i + 1) / total_siswa)
                                status_text.text(
                                    f'Memproses {i + 1} dari {total_siswa} siswa...'
                                )

                        if os.path.getsize(zip_file_path) > max_zip_size:
                            raise ValueError(
                                'Ukuran ZIP melebihi batas 100 MB untuk '
                                'melindungi penggunaan memori server. '
                                'Bagi ekspor berdasarkan kelas yang lebih kecil.'
                            )
                        st.success("Laporan satu kelas berhasil dibuat!")
                        with open(zip_file_path, 'rb') as zip_download:
                            st.download_button(
                                label='📥 Unduh Laporan Kelas (ZIP)',
                                data=zip_download,
                                file_name=f'Laporan_Kelas_{nama_kelas_aman}.zip',
                                mime='application/zip'
                            )
                    except ValueError as export_error:
                        st.error(str(export_error))
                    except Exception as export_error:
                        logger.exception("Gagal membuat ekspor ZIP kelas")
                        st.error(
                            f'Gagal membuat laporan ZIP kelas: {export_error}'
                        )
                    finally:
                        try:
                            os.unlink(zip_file_path)
                        except FileNotFoundError:
                            pass
                        except OSError as cleanup_error:
                            logger.warning(
                                "Tidak dapat menghapus file ZIP sementara: %s",
                                cleanup_error
                            )

                selected_student = st.selectbox(
                    'Pilih Siswa:',
                    options=unique_students,
                    help='Pilih siswa dari kelas yang telah dipilih',
                    key='individual_student_selection'
                )
                if st.session_state.get(
                    'early_warning_selection_updated', False
                ):
                    st.success(
                        'Siswa dipilih! Anda telah diarahkan ke tab '
                        'Analisis Individu.'
                    )
                    st.session_state['early_warning_selection_updated'] = False

                student_subjects = get_subjects_for_student(
                    class_df, selected_student
                )
                selected_subject = None
                if student_subjects:
                    subject_widget_key = (
                        f'individual_subject_selection_'
                        f'{kelas_terpilih}_{selected_student}'
                    )
                    selected_subject = st.selectbox(
                        'Pilih Mata Pelajaran:',
                        options=student_subjects,
                        help='Analisis hanya menggunakan nilai siswa pada mata pelajaran ini.',
                        key=subject_widget_key
                    )
                elif menu_tab == menu_kelas:
                    st.warning(
                        'Siswa ini belum memiliki mata pelajaran yang valid '
                        'untuk dianalisis.'
                    )
            
                # 2. Filtering data siswa
                if selected_student and selected_subject is not None:
                    student_df = filter_student_subject(
                        class_df, selected_student, selected_subject
                    )
                else:
                    student_df = class_df.iloc[0:0].copy()

                if (
                    selected_student
                    and selected_subject is not None
                    and not student_df.empty
                ):
                
                    student_df['Bulan'] = _ordered_months(student_df['Bulan'])
                
                    # Tampilan data siswa yang dipilih
                    with st.expander(f'Data Nilai untuk {selected_student}', expanded=False):
                        st.dataframe(student_df, use_container_width=True)
                
                    # === VISUALISASI DAN METRIK ===
                    st.subheader(f'Analisis Nilai: {selected_student}')
                
                    chart_cols = st.columns(2)
                
                    with chart_cols[0]:
                        st.write('**Tren Nilai per Bulan**')
                        trend_figure = individual_monthly_trend(student_df)
                        if trend_figure is None:
                            st.info('Belum ada data nilai untuk ditampilkan grafik')
                        else:
                            st.plotly_chart(
                                trend_figure, use_container_width=True
                            )

                    with chart_cols[1]:
                        st.write('**Radar Kompetensi Semua Mata Pelajaran**')
                        raw_student_data = st.session_state.get('df', df)
                        if (
                            raw_student_data is not None
                            and 'Nama Siswa' in raw_student_data.columns
                        ):
                            all_subjects_student_df = raw_student_data.loc[
                                raw_student_data['Nama Siswa']
                                .astype('string')
                                .str.strip()
                                == str(selected_student).strip()
                            ].copy()
                            radar_figure = student_subject_radar(
                                all_subjects_student_df
                            )
                        else:
                            radar_figure = None

                        if radar_figure is None:
                            st.info(
                                'Belum ada nilai valid lintas mata pelajaran '
                                'untuk membuat grafik radar.'
                            )
                        else:
                            st.plotly_chart(
                                radar_figure, use_container_width=True
                            )

                    st.write(
                        '**Kekuatan & Kelemahan per Topik (Focus Area)**'
                    )
                    topic_figure = topic_average_bar(student_df)
                    if topic_figure is None:
                        st.info('Belum ada data topik untuk ditampilkan')
                    else:
                        st.plotly_chart(
                            topic_figure, use_container_width=True
                        )
                
                    # === ANALISIS DENGAN AI ===
                    st.subheader('Hasil Analisis AI')
                    prompt = build_student_report_prompt(
                        selected_student, student_df
                    )

                    # Tombol untuk generate analisis AI
                    if st.button('🤖 Buat Analisis AI', type='primary'):
                        st.session_state['hasil_ai'] = None
                        st.session_state['hasil_ai_context'] = None
                        response_text = None
                    
                        # Percabangan logika berdasarkan pilihan AI
                        try:
                            if ai_engine == GEMINI_ENGINE:
                                if not api_key:
                                    st.error(
                                        '❌ API Key Gemini diperlukan untuk mode Cloud'
                                    )
                                    st.stop()
                                with st.spinner(
                                    f'Sedang menganalisis dengan Gemini AI '
                                    f'({gemini_model})...'
                                ):
                                    response_text = generate_ai_response(
                                        ai_engine,
                                        prompt,
                                        api_key=api_key,
                                        model_name=gemini_model
                                    )
                            else:
                                with st.spinner(
                                    f'Sedang menganalisis dengan Ollama AI '
                                    f'({ollama_model})...'
                                ):
                                    response_text = generate_ai_response(
                                        ai_engine,
                                        prompt,
                                        model_name=ollama_model
                                    )

                            if (
                                not isinstance(response_text, str)
                                or not response_text.strip()
                            ):
                                st.error(
                                    'AI tidak menghasilkan teks. Periksa respons atau '
                                    'kebijakan keamanan model, lalu coba lagi.'
                                )
                                response_text = None
                            else:
                                st.session_state['hasil_ai'] = response_text
                                st.session_state['hasil_ai_context'] = (
                                    str(kelas_terpilih),
                                    str(selected_student),
                                    int(pd.util.hash_pandas_object(
                                        student_df, index=True
                                    ).sum())
                                )
                    
                        except Exception as e:
                            if ai_engine == GEMINI_ENGINE:
                                error_msg = str(e)
                                if '429' in error_msg or 'Quota Exceeded' in error_msg or 'rate limit' in error_msg.lower():
                                    st.error('''
                                    ❌ **Rate Limit Tercapai (Error 429)**
                                
                                    Anda telah mencapai batas harian atau permenit untuk Gemini API. 
                                
                                    **Solusi:**
                                    1. Tunggu beberapa menit sebelum mencoba lagi
                                    2. Kurangi frekuensi menekan tombol Generate
                                    3. Periksa quota Anda di https://makersuite.google.com/app/apikey
                                    4. Pertimbangkan untuk meningkatkan limit jika diperlukan
                                    ''')
                                elif isinstance(e, (TimeoutError, requests.exceptions.Timeout)) or 'timeout' in error_msg.lower() or 'deadline exceeded' in error_msg.lower():
                                    st.error('Permintaan ke Gemini melewati batas waktu. Silakan coba lagi.')
                                elif 'connection' in error_msg.lower() or 'network' in error_msg.lower():
                                    st.error('Tidak dapat terhubung ke Gemini API. Periksa koneksi internet Anda.')
                                else:
                                    st.error(f'Terjadi kesalahat saat menghubungi Gemini API: {error_msg}')
                                st.info('Pastikan API Key Anda valid dan Generative Language API diaktifkan di Google Cloud Console')
                            elif isinstance(e, requests.exceptions.ConnectionError):
                                st.error(
                                    '❌ Tidak dapat terhubung ke Ollama. '
                                    'Pastikan Ollama sedang berjalan di '
                                    'http://localhost:11434'
                                )
                            elif isinstance(e, requests.exceptions.Timeout):
                                st.error(
                                    '❌ Timeout saat menghubungi Ollama. '
                                    'Pastikan Ollama sedang berjalan dan merespons.'
                                )
                            else:
                                st.error(f'Gagal menghubungi Ollama: {e}')
                    
                        if st.session_state['hasil_ai'] is None:
                            st.warning('Tidak ada respons dari AI. Silakan coba lagi.')
                    else:
                        st.info('Klik tombol "Buat Analisis AI" untuk menganalisis data siswa dengan AI yang dipilih')

                    current_ai_context = (
                        str(kelas_terpilih),
                        str(selected_student),
                        int(pd.util.hash_pandas_object(
                            student_df, index=True
                        ).sum())
                    )
                    if (
                        st.session_state['hasil_ai'] is not None
                        and st.session_state['hasil_ai_context'] == current_ai_context
                    ):
                        laporan_guru, laporan_orang_tua, separator_ditemukan = (
                            _split_ai_report(st.session_state['hasil_ai'])
                        )
                        if not separator_ditemukan:
                            st.warning(
                                'AI tidak menyertakan pemisah laporan. Respons '
                                'ditampilkan untuk guru; PDF menggunakan pesan '
                                'fallback untuk laporan orang tua.'
                            )

                        st.markdown(laporan_guru)

                        st.markdown('---')
                        safe_filename = selected_student.replace(
                            ' ', '_'
                        ).replace('/', '_').replace('\\', '_')
                        try:
                            pdf_guru_bytes = generate_pdf(
                                selected_student,
                                kelas_terpilih,
                                student_df,
                                laporan_guru,
                                nama_kepala_sekolah=nama_kepala_sekolah,
                                nama_wali_kelas=nama_wali_kelas,
                                tanda_tangan_kepala_sekolah=tanda_tangan_kepala_sekolah,
                                tanda_tangan_wali_kelas=tanda_tangan_wali_kelas,
                                include_ai_analysis=include_ai_analysis
                            )
                            pdf_orang_tua_bytes = generate_pdf(
                                selected_student,
                                kelas_terpilih,
                                student_df,
                                laporan_orang_tua,
                                nama_kepala_sekolah=nama_kepala_sekolah,
                                nama_wali_kelas=nama_wali_kelas,
                                tanda_tangan_kepala_sekolah=tanda_tangan_kepala_sekolah,
                                tanda_tangan_wali_kelas=tanda_tangan_wali_kelas,
                                include_ai_analysis=include_ai_analysis
                            )
                            download_col_guru, download_col_orang_tua = st.columns(2)
                            with download_col_guru:
                                st.download_button(
                                    label='Unduh Laporan (Guru)',
                                    data=pdf_guru_bytes,
                                    file_name=f'Laporan_Guru_{safe_filename}.pdf',
                                    mime='application/pdf',
                                    help=f'Unduh laporan analisis guru untuk {selected_student}'
                                )
                            with download_col_orang_tua:
                                st.download_button(
                                    label='Unduh Laporan (Orang Tua)',
                                    data=pdf_orang_tua_bytes,
                                    file_name=f'Laporan_Orang_Tua_{safe_filename}.pdf',
                                    mime='application/pdf',
                                    help=f'Unduh surat laporan untuk orang tua {selected_student}'
                                )
                        except Exception as pdf_error:
                            st.warning(
                                f'Tidak dapat menghasilkan kedua laporan PDF: '
                                f'{pdf_error}. Pastikan Anda telah menginstall fpdf2.'
                            )
                

            elif menu_tab == menu_kelas:
                st.subheader('Class Analytics')
                kelas_analytics = st.selectbox(
                    'Pilih Kelas untuk Class Analytics:',
                    options=unique_classes,
                    key='class_analytics_kelas'
                )
                class_df_all_subjects = prepare_class_subject_data(
                    df, kelas_analytics
                )
                subject_options = get_unique_subjects(
                    class_df_all_subjects
                )
                all_subjects_option = ALL_SUBJECTS_OPTION
                subject_widget_key = 'class_analytics_subjects'
                current_subject_selection = st.session_state.get(
                    subject_widget_key, [all_subjects_option]
                )
                if (
                    isinstance(current_subject_selection, list)
                    and all_subjects_option not in current_subject_selection
                    and not set(current_subject_selection).issubset(
                        subject_options
                    )
                ):
                    st.session_state[subject_widget_key] = [
                        all_subjects_option
                    ]
                selected_subjects = st.multiselect(
                    'Filter Mata Pelajaran:',
                    options=[all_subjects_option, *subject_options],
                    default=[all_subjects_option],
                    key=subject_widget_key
                )
                class_df = filter_subjects(
                    class_df_all_subjects,
                    selected_subjects,
                    all_subjects_option
                )
                class_df['Nilai'] = pd.to_numeric(
                    class_df['Nilai'], errors='coerce'
                )
                if not selected_subjects:
                    st.info(
                        'Pilih minimal satu mata pelajaran atau pilih '
                        '"Semua Mata Pelajaran".'
                    )

                st.markdown('---')
                st.subheader('🚨 Academic Early Warning')
                st.caption(
                    'Siswa ditandai jika rata-rata nilai di bawah KKM 70 atau '
                    'nilai rata-rata turun lebih dari 10 poin pada dua bulan '
                    'kalender berurutan terakhir.'
                )

                risk_table = get_class_early_warning(
                    class_df, kelas_analytics, KKM
                )
                jumlah_siswa_berisiko = len(risk_table)
                warning_col, action_col = st.columns([1, 2])
                with warning_col:
                    st.metric(
                        'Perlu Perhatian Kritis',
                        jumlah_siswa_berisiko
                    )
                with action_col:
                    if jumlah_siswa_berisiko:
                        st.error(
                            f'{jumlah_siswa_berisiko} siswa memerlukan '
                            'perhatian kritis.'
                        )
                    else:
                        st.success(
                            'Tidak ada siswa yang memenuhi kriteria risiko kritis.'
                        )

                if risk_table.empty:
                    st.info(
                        'Belum ada siswa berisiko berdasarkan nilai dan tren '
                        'bulanan yang tersedia.'
                    )
                else:
                    st.dataframe(
                        risk_table.drop(columns=['Kelas']).style.format(
                            {'Rata-rata Nilai Saat Ini': '{:.1f}'}
                        ),
                        use_container_width=True,
                        hide_index=True
                    )
                    if role == 'Guru':
                        st.caption(
                            'Gunakan tombol aksi untuk mengisi pilihan kelas '
                            'dan siswa pada tab Analisis Individu. Buka tab '
                            'tersebut untuk melanjutkan analisis.'
                        )
                        for row_index, risk_row in risk_table.reset_index(
                            drop=True
                        ).iterrows():
                            action_cols = st.columns([2, 1])
                            with action_cols[0]:
                                st.write(risk_row['Nama Siswa'])
                            with action_cols[1]:
                                st.button(
                                    'Pilih Siswa Ini untuk Analisis',
                                    key=(
                                        'early_warning_select_'
                                        f'{row_index}_{kelas_analytics}'
                                    ),
                                    on_click=_select_student_for_individual_analysis,
                                    args=(
                                        risk_row['Kelas'],
                                        risk_row['Nama Siswa']
                                    )
                                )

                if role == 'Guru':
                    teacher_recommendations = generate_teacher_recommendation(
                        class_df, KKM
                    )
                    with st.expander(
                        '🛠️ Rekomendasi Tindak Lanjut (RTL) Guru',
                        expanded=True
                    ):
                        st.markdown('\n'.join(
                            f'- {recommendation}'
                            for recommendation in teacher_recommendations
                        ))


                class_metrics = get_class_metrics(class_df, KKM)
                rata_rata_kelas = class_metrics['average']
                jumlah_siswa_kelas = class_metrics['student_count']
                persentase_ketuntasan = class_metrics['completion_rate']
                topik_terlemah = class_metrics['weakest_topic']
                topic_class_data = class_metrics['topic_averages']

                metric_cols = st.columns(4)
                metric_cols[0].metric('Rata-rata Nilai Kelas', rata_rata_kelas)
                metric_cols[1].metric('Jumlah Siswa', jumlah_siswa_kelas)
                metric_cols[2].metric('Topik Terlemah', topik_terlemah)
                metric_cols[3].metric(
                    'Persentase Ketuntasan',
                    persentase_ketuntasan,
                    help='Persentase siswa dengan nilai rata-rata >= KKM (70)'
                )

                chart_cols = st.columns(2)
                with chart_cols[0]:
                    st.write('**Tren Rata-rata Nilai Kelas per Bulan**')
                    monthly_fig = class_monthly_trend(class_df)
                    if monthly_fig is None:
                        st.info('Belum ada data bulanan valid untuk kelas ini.')
                    else:
                        st.plotly_chart(monthly_fig, use_container_width=True)

                with chart_cols[1]:
                    st.write('**Rata-rata Nilai per Topik Materi**')
                    topic_fig = class_topic_average_bar(topic_class_data)
                    if topic_fig is None:
                        st.info('Belum ada data topik dengan nilai valid untuk kelas ini.')
                    else:
                        st.plotly_chart(topic_fig, use_container_width=True)

                st.write('**Perbandingan Rata-rata Nilai Antar-Mata Pelajaran**')
                subject_fig = subject_average_bar(class_df)
                if subject_fig is None:
                    st.info(
                        'Belum ada nilai valid untuk dibandingkan antar-mata pelajaran.'
                    )
                else:
                    st.plotly_chart(subject_fig, use_container_width=True)

                table_cols = st.columns(2)
                with table_cols[0]:
                    st.write('**Top 5 Siswa dengan Rata-rata Tertinggi**')
                with table_cols[1]:
                    st.write('**Siswa Perlu Perhatian Ekstra**')
                    st.caption('Bottom 5 siswa dengan rata-rata nilai terendah.')

                student_rankings = get_student_rankings(class_df)
                student_count_with_scores = len(student_rankings)
                if student_count_with_scores < 10:
                    st.caption(
                        f'Kelas ini memiliki {student_count_with_scores} siswa dengan nilai valid; '
                        'daftar Top 5 dan Bottom 5 dapat berisi siswa yang sama.'
                    )

                if student_rankings.empty:
                    with table_cols[0]:
                        st.info('Belum ada nilai siswa yang valid untuk dirangking.')
                    with table_cols[1]:
                        st.info('Belum ada nilai siswa yang valid untuk dirangking.')
                else:
                    top_students, bottom_students = get_student_ranking_tables(
                        student_rankings
                    )
                    with table_cols[0]:
                        st.dataframe(
                            top_students.style.format({'Rata-rata Nilai': '{:.1f}'}),
                            use_container_width=True,
                            hide_index=True
                        )
                    with table_cols[1]:
                        st.dataframe(
                            bottom_students.style.format({'Rata-rata Nilai': '{:.1f}'}),
                            use_container_width=True,
                            hide_index=True
                        )
            else:
                _render_edu_chat()

    except Exception as e:
        st.error(f'Terjadi kesalahan saat memproses file: {str(e)}')

else:
    if role == 'Guru':
        st.info('Silakan unggah file Excel nilai siswa untuk memulai analisis')

        with st.expander(
            'Contoh Struktur File Excel yang Diinginkan', expanded=True
        ):
            example_data = {
                'Nama Siswa': ['Budi Santoso', 'Budi Santoso', 'Budi Santoso', 'Ani Lestari', 'Ani Lestari'],
                'Kelas': ['X IPA 1', 'X IPA 1', 'X IPA 1', 'X IPA 2', 'X IPA 2'],
                'Mata Pelajaran': ['Matematika', 'Matematika', 'Fisika', 'Bahasa Indonesia', 'Bahasa Indonesia'],
                'Bulan': ['Januari', 'Februari', 'Maret', 'April', 'Mei'],
                'Topik': ['Aljabar', 'Peluang', 'Geometri', 'Sastra', 'Tata Bahasa'],
                'Nilai': [85, 90, 78, 92, 88]
            }
            example_df = pd.DataFrame(example_data)
            st.dataframe(example_df, use_container_width=True)
        _render_edu_chat()
    else:
        st.info(
            'Belum ada data analitik. Silakan minta Guru mengunggah dan '
            'memproses data terlebih dahulu.'
        )

# Footer
st.markdown('---')
st.caption('Smart Edu Analytics - Asisten AI Guru | Dibangun dengan Streamlit, Pandas, Plotly, dan Google Gemini AI')
