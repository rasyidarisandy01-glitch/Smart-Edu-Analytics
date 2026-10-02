"""PDF report rendering and export helpers."""

import logging
import os
import tempfile
from io import BytesIO

import pandas as pd
from fpdf import FPDF

from config import MONTH_ORDER
from data_utils import display_value

logger = logging.getLogger(__name__)


def _pdf_safe_text(value):
    text = display_value(value, '').replace('\r\n', '\n').replace('\r', '\n')
    text = ''.join(
        character if character == '\n' or ord(character) >= 32 else ' '
        for character in text
    )
    return text.encode('latin-1', errors='replace').decode('latin-1')


def create_matplotlib_figure(dataframe_nilai):
    """Render the PDF trend image from report data."""
    import matplotlib
    matplotlib.use('Agg', force=True)
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots(figsize=(10, 4))
    try:
        graph_data = dataframe_nilai.reindex(
            columns=['Bulan', 'Nilai']
        ).copy()
        graph_data['Nilai'] = pd.to_numeric(
            graph_data['Nilai'], errors='coerce'
        )
        graph_data['Bulan'] = (
            graph_data['Bulan'].astype('string').str.strip()
        )
        graph_data = graph_data.dropna(subset=['Bulan', 'Nilai'])
        graph_data = graph_data.groupby(
            'Bulan', as_index=False
        )['Nilai'].mean()
        month_order = {
            month: index for index, month in enumerate(MONTH_ORDER)
        }
        graph_data['_urutan'] = graph_data['Bulan'].map(
            lambda month: (
                month_order.get(month, len(MONTH_ORDER)), str(month)
            )
        )
        graph_data = graph_data.sort_values('_urutan')

        if graph_data.empty:
            axis.text(
                0.5, 0.5, 'Tidak ada data nilai bulanan yang valid',
                horizontalalignment='center', verticalalignment='center',
                transform=axis.transAxes, fontsize=14,
                bbox=dict(
                    boxstyle='round,pad=0.3', facecolor='lightgray'
                )
            )
            axis.set_title('Tren Nilai', fontsize=14, fontweight='bold')
        else:
            axis.plot(
                graph_data['Bulan'].astype(str),
                graph_data['Nilai'],
                marker='o', linewidth=2, markersize=8, color='#2E8B57'
            )
            student_names = (
                dataframe_nilai['Nama Siswa'].dropna()
                if 'Nama Siswa' in dataframe_nilai.columns
                else pd.Series(dtype='string')
            )
            student_name = (
                display_value(student_names.iloc[0], 'Siswa')
                if not student_names.empty else 'Siswa'
            )
            axis.set_title(
                f'Tren Nilai {student_name}', fontsize=14,
                fontweight='bold'
            )
            axis.set_xlabel('Bulan', fontsize=12)
            axis.set_ylabel('Nilai', fontsize=12)
            axis.grid(True, linestyle='--', alpha=0.7)
            plt.setp(axis.get_xticklabels(), rotation=45)
        figure.tight_layout()
        return figure
    except Exception:
        plt.close(figure)
        raise


def generate_pdf(
    nama_siswa,
    kelas_terpilih,
    dataframe_nilai,
    teks_ai,
    nama_kepala_sekolah='[Nama Kepala Sekolah]',
    nama_wali_kelas='[Nama Wali Kelas]',
    *,
    tanda_tangan_kepala_sekolah=None,
    tanda_tangan_wali_kelas=None
):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    logo_path = 'logo.png'
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=25)

    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'SMA Swasta Al-Fityan Medan', ln=True, align='C')
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'YAYASAN AL-FITYAN', ln=True, align='C')
    pdf.set_font('Arial', size=10)
    pdf.cell(
        0, 6,
        'Jl. Keluarga, Link IX, Kel. Asam Kumbang, Kec. Medan Selayang, '
        'Kota Medan - Sumatera Utara',
        ln=True, align='C'
    )

    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.line(10, pdf.get_y() + 1, 200, pdf.get_y() + 1)
    pdf.set_line_width(0.2)
    pdf.ln(15)

    pdf.set_font('Arial', 'B', 16)
    pdf.cell(
        0, 10,
        _pdf_safe_text(
            f'Laporan Analisis Perkembangan Nilai Siswa: {nama_siswa}'
        ),
        ln=True, align='C'
    )
    pdf.set_font('Arial', size=10)
    pdf.cell(
        0, 6, _pdf_safe_text(f'Kelas: {kelas_terpilih}'),
        ln=True, align='C'
    )
    pdf.ln(10)

    scores = pd.to_numeric(dataframe_nilai['Nilai'], errors='coerce')
    average = scores.mean()
    average_text = f'{average:.1f}' if pd.notna(average) else 'Tidak tersedia'

    month_positions = {
        month: index for index, month in enumerate(MONTH_ORDER)
    }
    monthly_data = dataframe_nilai.loc[
        dataframe_nilai['Bulan'].notna(), ['Bulan', 'Nilai']
    ].copy()
    monthly_data['Bulan'] = monthly_data['Bulan'].astype(str)
    monthly_data['Nilai'] = pd.to_numeric(
        monthly_data['Nilai'], errors='coerce'
    )
    monthly_averages = monthly_data.groupby('Bulan')['Nilai'].mean()
    observed_months = sorted(
        monthly_averages.index,
        key=lambda month: (
            month_positions.get(month, len(MONTH_ORDER)), month
        )
    )
    period = (
        f'{observed_months[0]} - {observed_months[-1]}'
        if observed_months else 'Tidak tersedia'
    )
    valid_months = [
        month for month in observed_months
        if pd.notna(monthly_averages[month])
    ]
    if len(valid_months) >= 2:
        first_score = monthly_averages[valid_months[0]]
        last_score = monthly_averages[valid_months[-1]]
        trend = (
            'Meningkat' if last_score > first_score else
            'Menurun' if last_score < first_score else
            'Stabil'
        )
    else:
        trend = 'Stabil'

    topic_data = dataframe_nilai.reindex(columns=['Topik']).copy()
    topic_data['Nilai'] = scores
    topic_averages = topic_data.groupby(
        'Topik', observed=True
    )['Nilai'].mean().dropna()
    focus_area = (
        str(topic_averages.idxmin())
        if not topic_averages.empty else 'Tidak tersedia'
    )
    strongest_topic = (
        str(topic_averages.idxmax())
        if not topic_averages.empty else 'Tidak tersedia'
    )

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'RINGKASAN PERFORMA', ln=True)
    pdf.set_font('Arial', size=10)
    summary_rows = [
        ('Rata-rata nilai', average_text),
        ('Periode pengamatan', period),
        ('Tren', trend),
        ('Focus Area', focus_area),
        ('Materi terkuat', strongest_topic),
    ]
    for label, value in summary_rows:
        pdf.set_x(pdf.l_margin)
        pdf.cell(42, 6, label)
        pdf.cell(4, 6, ':')
        pdf.multi_cell(
            pdf.w - pdf.r_margin - pdf.get_x(),
            6,
            _pdf_safe_text(value)
        )
    pdf.ln(5)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Tabel Nilai Siswa', ln=True)
    pdf.set_font('Arial', size=10)
    column_width = pdf.w / 4.5
    pdf.cell(column_width, 8, 'Bulan', border=1)
    pdf.cell(column_width, 8, 'Mata Pelajaran', border=1)
    pdf.cell(column_width, 8, 'Topik', border=1)
    pdf.cell(column_width, 8, 'Nilai', border=1, ln=True)
    for _, row in dataframe_nilai.iterrows():
        pdf.cell(
            column_width, 8, _pdf_safe_text(row['Bulan']), border=1
        )
        pdf.cell(
            column_width, 8,
            _pdf_safe_text(row['Mata Pelajaran']), border=1
        )
        pdf.cell(
            column_width, 8, _pdf_safe_text(row['Topik']), border=1
        )
        pdf.cell(
            column_width, 8, _pdf_safe_text(row['Nilai']),
            border=1, ln=True
        )
    pdf.ln(10)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Grafik Perkembangan Nilai', ln=True)

    temp_file_path = None
    matplotlib_figure = None
    pyplot = None
    try:
        import matplotlib.pyplot as pyplot

        matplotlib_figure = create_matplotlib_figure(dataframe_nilai)
        with tempfile.NamedTemporaryFile(
            suffix='.png', delete=False
        ) as temp_file:
            temp_file_path = temp_file.name
            matplotlib_figure.savefig(
                temp_file_path, format='PNG', dpi=150,
                bbox_inches='tight'
            )
        pdf.image(temp_file_path, x=10, w=190)
    except Exception as error:
        pdf.set_font('Arial', size=9)
        pdf.multi_cell(
            0, 4,
            _pdf_safe_text(
                f'Grafik tidak dapat ditampilkan dalam PDF karena: {error}\n'
                'Silakan lihat grafik di aplikasi Streamlit.'
            )
        )
    finally:
        if matplotlib_figure is not None and pyplot is not None:
            try:
                pyplot.close(matplotlib_figure)
            except Exception:
                logger.exception('Tidak dapat menutup figure Matplotlib')
        if temp_file_path:
            try:
                os.unlink(temp_file_path)
            except FileNotFoundError:
                pass
            except OSError as cleanup_error:
                logger.warning(
                    'Tidak dapat menghapus file grafik sementara: %s',
                    cleanup_error
                )

    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Analisis dan Rekomendasi', ln=True)
    pdf.set_font('Arial', size=9)
    clean_text = str(teks_ai or '').replace('*', '').replace('#', '')
    clean_text = clean_text.replace(
        '[Nama Guru/Tim Pendidikan]',
        _pdf_safe_text(nama_wali_kelas) or '[Nama Wali Kelas]'
    )
    pdf.multi_cell(0, 4, _pdf_safe_text(clean_text))

    signature_block_height = 44
    if pdf.will_page_break(signature_block_height):
        pdf.add_page()

    column_width = (pdf.w - pdf.l_margin - pdf.r_margin) / 2
    left_x = pdf.l_margin
    right_x = pdf.l_margin + column_width
    signature_top = pdf.get_y()

    pdf.set_font('Arial', size=10)
    pdf.set_xy(left_x, signature_top)
    pdf.cell(column_width, 6, 'Mengetahui, Kepala Sekolah', align='C')
    pdf.set_xy(right_x, signature_top)
    pdf.cell(column_width, 6, 'Wali Kelas', align='C', ln=True)

    signature_image_y = signature_top + 7
    signature_image_width = 50
    signature_image_height = 28
    signature_images = (
        (tanda_tangan_kepala_sekolah, left_x),
        (tanda_tangan_wali_kelas, right_x),
    )
    for image_data, column_x in signature_images:
        if image_data:
            pdf.image(
                BytesIO(image_data),
                x=column_x + (column_width - signature_image_width) / 2,
                y=signature_image_y,
                w=signature_image_width,
                h=signature_image_height,
                keep_aspect_ratio=True
            )

    pdf.set_font('Arial', 'B', 10)
    signature_y = signature_top + 30
    pdf.set_xy(left_x, signature_y)
    pdf.cell(
        column_width, 6,
        _pdf_safe_text(nama_kepala_sekolah) or '[Nama Kepala Sekolah]',
        align='C'
    )
    pdf.set_xy(right_x, signature_y)
    pdf.cell(
        column_width, 6,
        _pdf_safe_text(nama_wali_kelas) or '[Nama Wali Kelas]',
        align='C', ln=True
    )
    return bytes(pdf.output())
