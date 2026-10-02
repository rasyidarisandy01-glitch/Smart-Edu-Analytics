"""Pandas-only data preparation and analytics helpers."""

import pandas as pd

from config import KKM, MONTH_ORDER


def display_value(value, empty_text='Tidak tersedia'):
    if value is None or pd.isna(value):
        return empty_text
    text = str(value).strip()
    return text if text else empty_text


def prepare_uploaded_dataframe(dataframe):
    prepared = dataframe.copy()
    text_columns = [
        'Nama Siswa', 'Kelas', 'Mata Pelajaran', 'Bulan', 'Topik'
    ]
    for column in text_columns:
        prepared[column] = (
            prepared[column].astype('string').str.strip().replace('', pd.NA)
        )
    prepared['Bulan'] = prepared['Bulan'].str.title()
    prepared['Nilai'] = pd.to_numeric(prepared['Nilai'], errors='coerce')

    rows_without_identity = int(
        prepared[['Nama Siswa', 'Kelas']].isna().any(axis=1).sum()
    )
    prepared = prepared.dropna(
        subset=['Nama Siswa', 'Kelas']
    ).copy()
    invalid_scores = int(prepared['Nilai'].isna().sum())
    return prepared, rows_without_identity, invalid_scores


def ordered_months(values):
    known_months = values.where(values.isin(MONTH_ORDER))
    return pd.Categorical(known_months, categories=MONTH_ORDER, ordered=True)


def get_unique_classes(dataframe):
    return sorted(dataframe['Kelas'].dropna().unique(), key=str)


def get_students_for_class(dataframe, selected_class):
    class_data = dataframe.loc[dataframe['Kelas'] == selected_class]
    return sorted(class_data['Nama Siswa'].dropna().unique(), key=str)


def get_subjects_for_student(class_data, student_name):
    subjects = (
        class_data.loc[
            class_data['Nama Siswa'] == student_name, 'Mata Pelajaran'
        ]
        .astype('string')
        .str.strip()
        .dropna()
    )
    return sorted(subjects[subjects != ''].unique().tolist(), key=str)


def filter_student_subject(class_data, student_name, subject):
    if subject is None:
        return class_data.iloc[0:0].copy()
    subject_values = class_data['Mata Pelajaran'].astype('string').str.strip()
    return class_data.loc[
        (class_data['Nama Siswa'] == student_name)
        & (subject_values == subject)
    ].copy()


def prepare_class_subject_data(dataframe, selected_class):
    class_data = dataframe.loc[dataframe['Kelas'] == selected_class].copy()
    class_data['Mata Pelajaran'] = (
        class_data['Mata Pelajaran']
        .astype('string')
        .str.strip()
        .replace('', pd.NA)
    )
    return class_data


def get_unique_subjects(class_data):
    return sorted(
        class_data['Mata Pelajaran'].dropna().unique().tolist(),
        key=str
    )


def filter_subjects(class_data, selected_subjects, all_subjects_option):
    if all_subjects_option in selected_subjects:
        return class_data.copy()
    return class_data.loc[
        class_data['Mata Pelajaran'].isin(selected_subjects)
    ].copy()


def build_student_data_summary(student_name, student_data):
    valid_scores = student_data.dropna(subset=['Nilai'])
    valid_month_scores = student_data.dropna(subset=['Bulan', 'Nilai'])
    monthly_averages = (
        valid_month_scores.groupby('Bulan', observed=True)['Nilai']
        .mean()
        .dropna()
    )
    subjects = sorted(
        student_data['Mata Pelajaran'].dropna().astype(str).unique()
    )
    month_range = (
        f'{monthly_averages.index[0]} sampai {monthly_averages.index[-1]}'
        if not monthly_averages.empty else 'Tidak tersedia'
    )

    if len(monthly_averages) >= 2:
        start_score = monthly_averages.iloc[0]
        end_score = monthly_averages.iloc[-1]
        trend = (
            'Naik' if end_score > start_score else
            'Turun' if end_score < start_score else
            'Stabil'
        )
    else:
        trend = 'Stabil'

    if valid_scores.empty:
        average_text = highest_text = lowest_text = 'Tidak tersedia'
    else:
        average_text = f"{valid_scores['Nilai'].mean():.2f}"
        highest_text = f"{valid_scores['Nilai'].max():.2f}"
        lowest_text = f"{valid_scores['Nilai'].min():.2f}"

    summary = f"""
Data nilai siswa {student_name}:
- Mata Pelajaran: {', '.join(subjects) if subjects else 'Tidak tersedia'}
- Jumlah rekaman: {len(student_data)}
- Rentang bulan: {month_range}
- Nilai rata-rata: {average_text}
- Nilai tertinggi: {highest_text}
- Nilai terendah: {lowest_text}
- Tren terakhir: {trend}

Detail nilai per bulan:
"""
    for _, row in student_data.iterrows():
        summary += (
            f"- {display_value(row.get('Bulan'))}: "
            f"{display_value(row.get('Nilai'))} "
            f"({display_value(row.get('Mata Pelajaran'))} - "
            f"{display_value(row.get('Topik'))})\n"
        )
    return summary


def get_class_early_warning(class_data, class_name, kkm=KKM):
    source = class_data.reindex(
        columns=['Nama Siswa', 'Kelas', 'Bulan', 'Topik', 'Nilai']
    ).copy()
    source['Nilai'] = pd.to_numeric(source['Nilai'], errors='coerce')
    source['Nama Siswa'] = source['Nama Siswa'].astype('string').str.strip()
    source = source.dropna(subset=['Nama Siswa'])
    source = source.loc[source['Nama Siswa'] != '']

    month_positions = {month: index for index, month in enumerate(MONTH_ORDER)}
    risk_records = []
    for student_name, records in source.groupby('Nama Siswa', sort=True):
        valid_scores = records['Nilai'].dropna()
        if valid_scores.empty:
            continue

        average = float(valid_scores.mean())
        monthly_scores = records.loc[
            records['Bulan'].notna() & records['Nilai'].notna(),
            ['Bulan', 'Nilai']
        ].copy()
        monthly_scores['Bulan'] = (
            monthly_scores['Bulan'].astype('string').str.strip()
        )
        monthly_scores = monthly_scores.loc[
            monthly_scores['Bulan'].isin(MONTH_ORDER)
        ]
        monthly_scores['Bulan'] = pd.Categorical(
            monthly_scores['Bulan'], categories=MONTH_ORDER, ordered=True
        )
        monthly_scores = (
            monthly_scores.groupby('Bulan', observed=True, as_index=False)['Nilai']
            .mean()
            .dropna(subset=['Nilai'])
            .sort_values('Bulan')
        )

        latest_trend = 'Tidak cukup data'
        sharp_decline = False
        if len(monthly_scores) >= 2:
            previous_month = str(monthly_scores.iloc[-2]['Bulan'])
            latest_month = str(monthly_scores.iloc[-1]['Bulan'])
            change = (
                float(monthly_scores.iloc[-1]['Nilai'])
                - float(monthly_scores.iloc[-2]['Nilai'])
            )
            latest_trend = (
                'Naik' if change > 0 else
                'Turun' if change < 0 else
                'Stabil'
            )
            consecutive_months = (
                month_positions[latest_month]
                == month_positions[previous_month] + 1
            )
            sharp_decline = consecutive_months and change < -10

        if average >= kkm and not sharp_decline:
            continue

        student_topics = records.loc[
            records['Topik'].notna() & records['Nilai'].notna(),
            ['Topik', 'Nilai']
        ].copy()
        student_topics['Topik'] = (
            student_topics['Topik'].astype('string').str.strip()
        )
        student_topics = student_topics.loc[
            student_topics['Topik'].notna() & (student_topics['Topik'] != '')
        ]
        topic_averages = student_topics.groupby('Topik')['Nilai'].mean().dropna()
        priority_topic = (
            str(topic_averages.idxmin()) if not topic_averages.empty else None
        )

        if average < kkm and sharp_decline:
            action = (
                f'Remedial {priority_topic} & Konseling BK; '
                'pemantauan intensif orang tua'
                if priority_topic else
                'Remedial materi prioritas & Konseling BK; '
                'pemantauan intensif orang tua'
            )
        elif average < kkm:
            action = (
                f'Remedial {priority_topic} & Konseling BK'
                if priority_topic else
                'Remedial materi prioritas & Konseling BK'
            )
        else:
            action = (
                'Perlu Pemantauan Intensif Orang Tua & '
                'koordinasi dengan Wali Kelas'
            )

        risk_records.append({
            'Nama Siswa': str(student_name),
            'Rata-rata Nilai Saat Ini': average,
            'Tren Terakhir (Naik/Turun)': latest_trend,
            'Rekomendasi Tindakan Otomatis': action,
            'Kelas': class_name,
        })

    return pd.DataFrame(risk_records, columns=[
        'Nama Siswa',
        'Rata-rata Nilai Saat Ini',
        'Tren Terakhir (Naik/Turun)',
        'Rekomendasi Tindakan Otomatis',
        'Kelas',
    ])


def get_class_metrics(class_data, kkm=KKM):
    values = pd.to_numeric(class_data['Nilai'], errors='coerce')
    valid_values = values.dropna()
    average = f'{valid_values.mean():.1f}' if not valid_values.empty else 'Tidak tersedia'
    student_count = int(class_data['Nama Siswa'].dropna().nunique())

    student_source = class_data.reindex(
        columns=['Nama Siswa', 'Nilai']
    ).copy()
    student_source['Nama Siswa'] = (
        student_source['Nama Siswa'].astype('string').str.strip()
    )
    student_source['Nilai'] = pd.to_numeric(
        student_source['Nilai'], errors='coerce'
    )
    student_source = student_source.dropna(subset=['Nama Siswa'])
    student_source = student_source.loc[student_source['Nama Siswa'] != '']
    student_averages = (
        student_source.dropna(subset=['Nilai'])
        .groupby('Nama Siswa')['Nilai']
        .mean()
        .dropna()
    )
    passed_count = int(student_averages.ge(kkm).sum())
    completion_rate = (
        f'{passed_count / student_count * 100:.1f}%'
        if student_count else '0.0%'
    )

    topic_data = class_data.reindex(columns=['Topik', 'Nilai']).copy()
    topic_data['Topik'] = topic_data['Topik'].astype('string').str.strip()
    topic_data['Nilai'] = pd.to_numeric(topic_data['Nilai'], errors='coerce')
    topic_data = topic_data.dropna(subset=['Topik', 'Nilai'])
    topic_data = topic_data.loc[topic_data['Topik'] != '']
    topic_averages = (
        topic_data.groupby('Topik', as_index=False)['Nilai']
        .mean()
        .dropna(subset=['Nilai'])
    )
    weakest_topic = (
        str(topic_averages.loc[topic_averages['Nilai'].idxmin(), 'Topik'])
        if not topic_averages.empty else 'Tidak tersedia'
    )

    return {
        'average': average,
        'student_count': student_count,
        'completion_rate': completion_rate,
        'weakest_topic': weakest_topic,
        'topic_averages': topic_averages,
    }


def generate_teacher_recommendation(class_df, kkm=KKM):
    if class_df is None or class_df.empty:
        return [
            'Data kelas atau mata pelajaran yang dipilih masih kosong sehingga rekomendasi berbasis hasil belum dapat dihitung.',
            'Pastikan filter kelas dan mata pelajaran sudah sesuai dengan data yang ingin ditinjau.',
            'Setelah data nilai tersedia, tinjau kembali ketuntasan, topik terlemah, dan daftar peringatan dini.',
        ]

    required_columns = {'Nama Siswa', 'Nilai'}
    if not required_columns.issubset(class_df.columns):
        return [
            'Data kelas belum memiliki kolom nama siswa dan nilai yang diperlukan untuk menyusun rekomendasi.',
            'Periksa kembali format file dan pastikan kolom wajib tersedia sebelum melakukan analisis.',
            'Setelah struktur data diperbaiki, jalankan kembali analisis untuk menentukan tindak lanjut yang sesuai.',
        ]

    scores = pd.to_numeric(class_df['Nilai'], errors='coerce')
    if scores.dropna().empty:
        return [
            'Belum ada nilai numerik yang valid pada kelas dan mata pelajaran terpilih.',
            'Periksa kembali kolom Nilai pada file sumber dan lengkapi data yang kosong atau bukan angka.',
            'Jalankan kembali analisis setelah nilai yang valid tersedia.',
        ]

    class_metrics = get_class_metrics(class_df, kkm)
    completion_rate = float(class_metrics['completion_rate'].rstrip('%'))
    recommendations = []

    if completion_rate < 50:
        recommendations.append(
            'Lakukan remedial klasikal (menyeluruh) sebelum melanjutkan ke materi berikutnya.'
        )
    elif completion_rate < 85:
        recommendations.append(
            'Terapkan metode tutor sebaya (peer-tutoring); pasangkan siswa di atas KKM dengan siswa yang masuk peringatan dini.'
        )
    else:
        recommendations.append(
            'Pertahankan capaian kelas dengan memberi pengayaan terarah bagi siswa tuntas dan dukungan individual bagi siswa yang masih membutuhkan.'
        )

    weakest_topic = class_metrics['weakest_topic']
    if weakest_topic != 'Tidak tersedia':
        recommendations.append(
            f'Materi {weakest_topic} memiliki rata-rata terendah. Pertimbangkan untuk menggunakan metode ajar yang lebih visual atau kontekstual pada topik ini.'
        )

    class_name = ''
    if 'Kelas' in class_df.columns:
        class_names = class_df['Kelas'].dropna()
        if not class_names.empty:
            class_name = str(class_names.iloc[0])
    risk_table = get_class_early_warning(class_df, class_name, kkm)
    if not risk_table.empty:
        recommendations.append(
            'Jadwalkan sesi konseling akademik untuk siswa yang berada di daftar Perlu Perhatian Kritis.'
        )

    additional_recommendations = [
        'Gunakan asesmen formatif singkat pada pertemuan berikutnya untuk mengecek dampak tindak lanjut.',
        'Dokumentasikan perkembangan hasil agar strategi pembelajaran dapat disesuaikan berdasarkan bukti.',
    ]
    for recommendation in additional_recommendations:
        if len(recommendations) >= 3:
            break
        recommendations.append(recommendation)

    return recommendations[:4]


def get_class_monthly_averages(class_data):
    monthly = class_data.reindex(columns=['Bulan', 'Nilai']).copy()
    monthly['Bulan'] = monthly['Bulan'].astype('string').str.strip()
    monthly['Nilai'] = pd.to_numeric(monthly['Nilai'], errors='coerce')
    monthly = monthly.loc[monthly['Bulan'].isin(MONTH_ORDER)].dropna(
        subset=['Nilai']
    )
    if monthly.empty:
        return monthly
    monthly['Bulan'] = pd.Categorical(
        monthly['Bulan'], categories=MONTH_ORDER, ordered=True
    )
    return (
        monthly.groupby('Bulan', observed=True, as_index=False)['Nilai']
        .mean()
        .dropna(subset=['Nilai'])
        .sort_values('Bulan')
    )


def get_student_rankings(class_data):
    students = class_data.reindex(
        columns=['Nama Siswa', 'Nilai']
    ).copy()
    students['Nama Siswa'] = (
        students['Nama Siswa'].astype('string').str.strip()
    )
    students['Nilai'] = pd.to_numeric(students['Nilai'], errors='coerce')
    students = students.dropna(subset=['Nama Siswa', 'Nilai'])
    students = students.loc[students['Nama Siswa'] != '']
    return (
        students.groupby('Nama Siswa', as_index=False)['Nilai']
        .mean()
        .dropna(subset=['Nilai'])
    )


def get_student_ranking_tables(student_rankings, limit=5):
    columns = ['Nama Siswa', 'Nilai']
    if not set(columns).issubset(student_rankings.columns):
        empty = pd.DataFrame(columns=['Siswa', 'Rata-rata Nilai'])
        return empty.copy(), empty.copy()

    top_students = (
        student_rankings.sort_values(
            ['Nilai', 'Nama Siswa'], ascending=[False, True]
        )
        .head(limit)
        .rename(columns={
            'Nama Siswa': 'Siswa',
            'Nilai': 'Rata-rata Nilai'
        })
        .reset_index(drop=True)
    )
    bottom_students = (
        student_rankings.sort_values(
            ['Nilai', 'Nama Siswa'], ascending=[True, True]
        )
        .head(limit)
        .rename(columns={
            'Nama Siswa': 'Siswa',
            'Nilai': 'Rata-rata Nilai'
        })
        .reset_index(drop=True)
    )
    return top_students, bottom_students


def get_subject_averages(class_data):
    subjects = class_data.reindex(
        columns=['Mata Pelajaran', 'Nilai']
    ).copy()
    subjects['Mata Pelajaran'] = (
        subjects['Mata Pelajaran'].astype('string').str.strip()
    )
    subjects['Nilai'] = pd.to_numeric(subjects['Nilai'], errors='coerce')
    subjects = subjects.dropna(subset=['Mata Pelajaran', 'Nilai'])
    subjects = subjects.loc[subjects['Mata Pelajaran'] != '']
    return (
        subjects.groupby('Mata Pelajaran', as_index=False)['Nilai']
        .mean()
        .dropna(subset=['Nilai'])
        .sort_values('Mata Pelajaran')
    )


def build_chat_context_summary(
    dataframe, selected_student=None, kkm=KKM, max_detail_rows=500
):
    if dataframe is None or dataframe.empty:
        return 'Belum ada data nilai siswa yang tersedia.'

    source = dataframe.reindex(
        columns=[
            'Nama Siswa', 'Kelas', 'Mata Pelajaran', 'Topik', 'Bulan', 'Nilai'
        ]
    ).copy()
    source['Nama Siswa'] = (
        source['Nama Siswa'].astype('string').str.strip()
    )
    for column in ['Kelas', 'Mata Pelajaran', 'Topik', 'Bulan']:
        source[column] = source[column].astype('string').str.strip()
    source['Nilai'] = pd.to_numeric(source['Nilai'], errors='coerce')
    source = source.dropna(subset=['Nama Siswa'])
    source = source.loc[source['Nama Siswa'] != '']

    student_averages = (
        source.dropna(subset=['Nilai'])
        .groupby('Nama Siswa')['Nilai']
        .mean()
        .dropna()
    )
    valid_scores = source['Nilai'].dropna()
    if student_averages.empty:
        return (
            'Data nilai tersedia, tetapi tidak terdapat nilai numerik valid '
            'untuk diringkas.'
        )

    student_count = int(source['Nama Siswa'].nunique())
    passed_count = int(student_averages.ge(kkm).sum())
    completion_rate = (
        passed_count / student_count * 100 if student_count else 0
    )
    below_kkm = student_averages.loc[student_averages < kkm].sort_values()

    lines = [
        f'Jumlah siswa: {student_count}.',
        f'Rata-rata seluruh nilai: {valid_scores.mean():.1f}.',
        (
            f'Siswa mencapai KKM ({kkm}): {passed_count} dari '
            f'{student_count} ({completion_rate:.1f}%).'
        ),
    ]

    if below_kkm.empty:
        lines.append(f'Tidak ada siswa dengan rata-rata di bawah KKM {kkm}.')
    else:
        risk_students = ', '.join(
            f'{name} ({average:.1f})'
            for name, average in below_kkm.head(20).items()
        )
        lines.append(f'Siswa dengan rata-rata di bawah KKM: {risk_students}.')

    top_students = student_averages.sort_values(ascending=False).head(3)
    bottom_students = student_averages.sort_values().head(3)
    lines.append(
        'Tiga rata-rata siswa tertinggi: '
        + ', '.join(
            f'{name} ({average:.1f})'
            for name, average in top_students.items()
        )
        + '.'
    )
    lines.append(
        'Tiga rata-rata siswa terendah: '
        + ', '.join(
            f'{name} ({average:.1f})'
            for name, average in bottom_students.items()
        )
        + '.'
    )

    class_values = source['Kelas'].dropna().astype('string').str.strip()
    classes = sorted(classes for classes in class_values.unique() if classes)
    if classes:
        lines.append(f'Kelas dalam data: {", ".join(classes)}.')

    subject_values = (
        source['Mata Pelajaran'].dropna().astype('string').str.strip()
    )
    subjects = sorted(subject for subject in subject_values.unique() if subject)
    if subjects:
        lines.append(f'Mata pelajaran dalam data: {", ".join(subjects)}.')

    topic_data = source.reindex(columns=['Topik', 'Nilai']).copy()
    topic_data['Topik'] = topic_data['Topik'].astype('string').str.strip()
    topic_data = topic_data.dropna(subset=['Topik', 'Nilai'])
    topic_data = topic_data.loc[topic_data['Topik'] != '']
    topic_averages = topic_data.groupby('Topik')['Nilai'].mean().dropna()
    if not topic_averages.empty:
        weakest_topic = topic_averages.idxmin()
        lines.append(
            f'Topik dengan rata-rata terendah: {weakest_topic} '
            f'({topic_averages.loc[weakest_topic]:.1f}).'
        )

    detail_columns = [
        'Nama Siswa', 'Mata Pelajaran', 'Topik', 'Bulan', 'Nilai'
    ]
    detail_data = source.reindex(columns=detail_columns).copy()
    detail_data['_selected_student'] = (
        detail_data['Nama Siswa'].astype('string').str.casefold()
        == str(selected_student or '').strip().casefold()
    )
    detail_data = detail_data.sort_values(
        '_selected_student', ascending=False, kind='stable'
    ).drop(columns=['_selected_student'])
    included_details = detail_data.head(max(0, int(max_detail_rows)))
    lines.extend([
        '',
        'Rincian nilai siswa dalam format CSV:',
        included_details.to_csv(
            index=False,
            na_rep='Tidak tersedia',
            lineterminator='\n'
        ).rstrip(),
    ])
    if len(detail_data) > len(included_details):
        lines.append(
            f'Catatan: konteks memuat {len(included_details)} dari '
            f'{len(detail_data)} baris rincian. Baris siswa terpilih '
            'diprioritaskan.'
        )
    if selected_student:
        lines.append(f'Siswa yang sedang diprioritaskan: {selected_student}.')

    return '\n'.join(lines)
