from django.shortcuts import render, redirect
import csv
import pandas as pd
import folium
from folium import Icon
from itertools import groupby
from operator import itemgetter
from django.conf import settings
import os

# Path file CSV
CSV_FILE_PATH = 'data/data_titik_pekanbaru.csv'


def map_view(request):
    # Membuat Peta Dasar
    map_pku = folium.Map(location=[0.5071, 101.4478], zoom_start=12)

    # Membaca Data Titik dari CSV
    try:
        data = pd.read_csv(CSV_FILE_PATH)
        data.reset_index(drop=True, inplace=True)  # Atur ulang index
    except FileNotFoundError:
        data = pd.DataFrame(columns=['ID', 'Nama', 'Kategori', 'Latitude', 'Longitude', 'Sumber', 'Deskripsi', 'Nama File Gambar'])

    # Tambahkan kolom ID jika tidak ada atau ada nilai NaN
    if 'ID' not in data.columns or data['ID'].isna().any():
        data['ID'] = range(1, len(data) + 1)

    # Fitur Pencarian Data
    search_query = request.GET.get('search', '').strip()
    if search_query:
        data = data[
            (data['Nama'].str.contains(search_query, case=False, na=False)) |
            (data['Kategori'].str.contains(search_query, case=False, na=False))
        ]

    # Konversi Data ke Format Dictionary
    data_dict = data.to_dict('records')

    # Fungsi untuk menentukan ikon berdasarkan kategori dan nama
    def get_icon_for_category(category, name=None):
        if category == "Halte":
            if "Utama" in name:
                return Icon(color="blue", icon="bus-alt", prefix="fa")
            else:
                return Icon(color="lightblue", icon="bus", prefix="fa")
        elif category == "Bandara":
            if "Internasional" in name:
                return Icon(color="darkgreen", icon="plane-departure", prefix="fa")
            else:
                return Icon(color="green", icon="plane", prefix="fa")
        elif category == "Sekolah":
            if "SDN" in name:
                return Icon(color="orange", icon="school", prefix="fa")
            elif "SMPN" in name:
                return Icon(color="purple", icon="chalkboard", prefix="fa")
            elif "SMKN" in name or "SMAN" in name:
                return Icon(color="blue", icon="graduation-cap", prefix="fa")
            else:
                return Icon(color="gray", icon="book", prefix="fa")
        elif category == "Taman":
            return Icon(color="green", icon="tree", prefix="fa")
        elif category == "Rumah Sakit":
            return Icon(color="red", icon="hospital", prefix="fa")
        elif category == "Pasar":
            return Icon(color="orange", icon="shopping-cart", prefix="fa")
        elif category == "Tempat Ibadah":
            if "Masjid" in name:
                return Icon(color="green", icon="mosque", prefix="fa")
            elif "Gereja" in name:
                return Icon(color="brown", icon="church", prefix="fa")
            else:
                return Icon(color="gray", icon="place-of-worship", prefix="fa")
        elif category == "Universitas":
            return Icon(color="darkblue", icon="university", prefix="fa")
        elif category == "Pusat Perbelanjaan":
            return Icon(color="pink", icon="shopping-bag", prefix="fa")
        elif category == "GOR Olahraga":
            return Icon(color="darkred", icon="futbol", prefix="fa")
        else:
            return Icon(color="gray", icon="info-sign")

    # Mengelompokkan data berdasarkan kategori
    data_grouped = {}
    if data_dict:
        for key, group in groupby(sorted(data_dict, key=itemgetter('Kategori')), key=itemgetter('Kategori')):
            data_grouped[key] = list(group)

    # Menambahkan Marker Berdasarkan Kategori
    for category, category_data in data_grouped.items():
        group = folium.FeatureGroup(name=category)
        for row in category_data:
            try:
                # Validasi Latitude dan Longitude
                latitude = float(row['Latitude'])
                longitude = float(row['Longitude'])

                # Membuat Popup HTML
                popup_html = f"""
                    <b>{row['Nama']}</b><br>
                    Kategori: {row['Kategori']}<br>
                    Latitude: {latitude}<br>
                    Longitude: {longitude}<br>
                    <p>{row.get('Deskripsi', 'Deskripsi tidak tersedia.')}</p>
                """
                if row.get('Nama File Gambar'):
                    popup_html += f"""
                    <img src="/media/{row['Nama File Gambar']}" alt="{row['Nama']}" style="width:200px; height:auto;" />
                    """

                # Menentukan ikon
                icon = get_icon_for_category(row['Kategori'], name=row['Nama'])

                # Menambahkan Marker
                folium.Marker(
                    location=[latitude, longitude],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row['Nama'],
                    icon=icon
                ).add_to(group)

            except ValueError:
                # Abaikan baris dengan data lokasi yang tidak valid
                continue

        group.add_to(map_pku)

    # Menambahkan Layer Control
    folium.LayerControl().add_to(map_pku)

    # Konversi Peta ke Format HTML
    map_html = map_pku._repr_html_()
    return render(request, 'map_app/map.html', {
        'map': map_html,
        'data_grouped': data_grouped,
        'search_query': search_query
    })



def add_coordinate(request):
    if request.method == 'POST':
        # Ambil data dari form
        nama = request.POST.get('nama', '').strip()
        kategori = request.POST.get('kategori', '').strip()
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        deskripsi = request.POST.get('deskripsi', '').strip()
        gambar = request.FILES.get('gambar')

        # Validasi Input
        if not (nama and kategori and latitude and longitude):
            return render(request, 'map_app/add_coordinate.html', {'error': 'Semua field wajib diisi!'})

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return render(request, 'map_app/add_coordinate.html', {'error': 'Latitude dan Longitude harus berupa angka!'})

        # Simpan gambar ke direktori media
        gambar_path = ""
        if gambar:
            gambar_path = f"images/{gambar.name}"
            gambar_full_path = os.path.join(settings.MEDIA_ROOT, gambar_path)
            os.makedirs(os.path.dirname(gambar_full_path), exist_ok=True)
            with open(gambar_full_path, 'wb') as f:
                for chunk in gambar.chunks():
                    f.write(chunk)

        # Membaca Data untuk Menentukan ID Terakhir
        try:
            # Jika file CSV ditemukan
            data = pd.read_csv(CSV_FILE_PATH)
            data.reset_index(drop=True, inplace=True)
            if 'ID' not in data.columns or data['ID'].isna().any():  # Tambahkan kolom ID jika tidak ada
                data['ID'] = range(1, len(data) + 1)
            new_id = int(data['ID'].max()) + 1 if not data.empty else 1
        except (FileNotFoundError, pd.errors.EmptyDataError):  # Jika file CSV tidak ditemukan atau kosong
            # Mulai ID dari 1 jika CSV kosong
            new_id = 1

        # Menulis data baru ke file CSV
        with open(CSV_FILE_PATH, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Tambahkan header jika file kosong
            if os.stat(CSV_FILE_PATH).st_size == 0:
                writer.writerow(['ID', 'Nama', 'Kategori', 'Latitude', 'Longitude', 'Sumber', 'Deskripsi', 'Nama File Gambar'])
            # Tulis data baru
            writer.writerow([new_id, nama, kategori, latitude, longitude, "Manual Input", deskripsi, gambar_path])

        return redirect('map_view')

    return render(request, 'map_app/add_coordinate.html')


def edit_coordinate(request, id):
    try:
        # Membaca Data dari CSV
        data = pd.read_csv(CSV_FILE_PATH)
        data.reset_index(drop=True, inplace=True)
    except FileNotFoundError:
        return redirect('map_view')

    if request.method == 'POST':
        # Cari baris dengan ID yang cocok
        row_to_edit = data[data['ID'] == id]

        if not row_to_edit.empty:
            # Update data
            data.loc[data['ID'] == id, 'Nama'] = request.POST.get('nama', '').strip()
            data.loc[data['ID'] == id, 'Kategori'] = request.POST.get('kategori', '').strip()
            try:
                data.loc[data['ID'] == id, 'Latitude'] = float(request.POST.get('latitude', '').strip())
                data.loc[data['ID'] == id, 'Longitude'] = float(request.POST.get('longitude', '').strip())
            except ValueError:
                return render(request, 'map_app/edit_coordinate.html', {
                    'error': 'Latitude dan Longitude harus berupa angka!',
                    'row': row_to_edit.iloc[0].to_dict(),
                    'id': id
                })

            data.loc[data['ID'] == id, 'Deskripsi'] = request.POST.get('deskripsi', '').strip()

            # Update gambar jika diunggah
            gambar = request.FILES.get('gambar')
            if gambar:
                # Hapus gambar lama jika ada
                gambar_path_old = row_to_edit.iloc[0]['Nama File Gambar']
                if pd.notna(gambar_path_old) and os.path.exists(os.path.join(settings.MEDIA_ROOT, gambar_path_old)):
                    os.remove(os.path.join(settings.MEDIA_ROOT, gambar_path_old))

                # Simpan gambar baru
                gambar_path_new = f"images/{gambar.name}"
                gambar_full_path = os.path.join(settings.MEDIA_ROOT, gambar_path_new)
                os.makedirs(os.path.dirname(gambar_full_path), exist_ok=True)
                with open(gambar_full_path, 'wb') as f:
                    for chunk in gambar.chunks():
                        f.write(chunk)
                data.loc[data['ID'] == id, 'Nama File Gambar'] = gambar_path_new

            # Simpan kembali data ke file CSV
            data.to_csv(CSV_FILE_PATH, index=False)

        return redirect('map_view')

    # Ambil data baris yang akan diedit
    row = data[data['ID'] == id]
    if not row.empty:
        return render(request, 'map_app/edit_coordinate.html', {'row': row.iloc[0].to_dict(), 'id': id})

    return redirect('map_view')



def delete_coordinate(request, id):
    try:
        # Membaca Data dari CSV
        data = pd.read_csv(CSV_FILE_PATH)
        data.reset_index(drop=True, inplace=True)
    except FileNotFoundError:
        return redirect('map_view')

    if request.method == 'POST':
        # Cari baris dengan ID yang cocok
        row_to_delete = data[data['ID'] == id]

        if not row_to_delete.empty:
            # Hapus file gambar jika ada
            gambar_path = row_to_delete.iloc[0]['Nama File Gambar']
            if pd.notna(gambar_path) and os.path.exists(os.path.join(settings.MEDIA_ROOT, gambar_path)):
                os.remove(os.path.join(settings.MEDIA_ROOT, gambar_path))

            # Hapus baris dari DataFrame
            data = data[data['ID'] != id]

            # Simpan kembali ke file CSV
            data.to_csv(CSV_FILE_PATH, index=False)

        return redirect('map_view')

    # Data baris yang akan dihapus
    row = data[data['ID'] == id]
    if not row.empty:
        return render(request, 'map_app/delete_coordinate.html', {'row': row.iloc[0].to_dict()})

    return redirect('map_view')