from django.shortcuts import render, redirect
import csv
import pandas as pd
import folium
from folium import Icon
from itertools import groupby
from operator import itemgetter
from django.conf import settings
import os
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

# Path file CSV dan GeoJSON
CSV_FILE_PATH = 'data/data_titik_pekanbaru.csv'
GEOJSON_FILE_PATH = 'data/Tampan.json'
GEOJSON_FILE_PATH = 'data/Payung Sekaki.json'
GEOJSON_FILE_PATH = 'data/Lima Puluh.json'
GEOJSON_FILE_PATH = 'data/Marpoyan Damai.json'
GEOJSON_FILE_PATH = 'data/Pekanbaru Kota.json'
GEOJSON_FILE_PATH = 'data/Rumbai Pesisir.json'
GEOJSON_FILE_PATH = 'data/Rumbai.json'
GEOJSON_FILE_PATH = 'data/Sail.json'
GEOJSON_FILE_PATH = 'data/Senapelan.json'
GEOJSON_FILE_PATH = 'data/Sukajadi.json'
GEOJSON_FILE_PATH = 'data/Bukit Raya.json'
GEOJSON_FILE_PATH = 'data/Tenayan Raya.json'


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

    # Fungsi untuk menentukan warna wilayah berdasarkan distrik
    def get_color(district):
        colors = {
            "Tampan": "#FF5733",  # Merah-oranye
            "Payung Sekaki": "#33FF57",  # Hijau
            "Bukit Raya": "#FFC300",  # Kuning
            "Lima Puluh": "#DAF7A6",  # Hijau pucat
            "Marpoyan Damai": "#C70039",  # Merah gelap
            "Pekanbaru Kota": "#900C3F",  # Merah marun
            "Rumbai Pesisir": "#581845",  # Ungu tua
            "Rumbai": "#8E44AD",  # Ungu cerah
            "Sail": "#2980B9",  # Biru cerah
            "Senapelan": "#1ABC9C",  # Toska
            "Sukajadi": "#E67E22",  # Oranye terang
            "Tenayan Raya": "#34495E",  # Abu-abu gelap
        }
        return colors.get(district, "#3388FF")  # Default biru jika distrik tidak ditemukan

    # Daftar file GeoJSON
    geojson_files = [
        ('data/Tampan.json', "Wilayah Tampan"),
        ('data/Payung Sekaki.json', "Wilayah Payung Sekaki"),
        ('data/Bukit Raya.json', "Wilayah Bukit Raya"),
        ('data/Lima Puluh.json', "Wilayah Lima Puluh"),
        ('data/Marpoyan Damai.json', "Wilayah Marpoyan Damai"),
        ('data/Pekanbaru Kota.json', "Wilayah Pekanbaru Kota"),
        ('data/Rumbai Pesisir.json', "Wilayah Rumbai Pesisir"),
        ('data/Rumbai.json', "Wilayah Rumbai"),
        ('data/Sail.json', "Wilayah Sail"),
        ('data/Senapelan.json', "Wilayah Senapelan"),
        ('data/Sukajadi.json', "Wilayah Sukajadi"),
        ('data/Tenayan Raya.json', "Wilayah Tenayan Raya"),
    ]

    # Menambahkan Setiap GeoJSON ke Layer
    for file_path, layer_name in geojson_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                geojson_data = f.read()
            geojson_layer = folium.FeatureGroup(name=layer_name)
            folium.GeoJson(
                geojson_data,
                name=f"{layer_name} Layer",
                style_function=lambda feature: {
                    'fillColor': get_color(feature['properties'].get('district', 'Unknown')),
                    'color': 'black',  # Border hitam
                    'weight': 0.2,  # Ketebalan border
                    'fillOpacity': 0.2,  # Transparansi isi
                },
                tooltip=folium.GeoJsonTooltip(fields=["province", "district"], aliases=["Province:", "District:"]),
            ).add_to(geojson_layer)
            geojson_layer.add_to(map_pku)
        except FileNotFoundError:
            print(f"File not found: {file_path}")

    # Menambahkan Layer Control
    folium.LayerControl().add_to(map_pku)

    # Konversi Peta ke Format HTML
    map_html = map_pku._repr_html_()
    return render(request, 'map_app/map.html', {
        'map': map_html,
        'data_grouped': data_grouped,
        'search_query': search_query,
        'user_authenticated': request.user.is_authenticated  # Tambahkan ini
    })


@login_required
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
            data = pd.read_csv(CSV_FILE_PATH)
            data.reset_index(drop=True, inplace=True)
            if 'ID' not in data.columns or data['ID'].isna().any():
                data['ID'] = range(1, len(data) + 1)
            new_id = int(data['ID'].max()) + 1 if not data.empty else 1
        except (FileNotFoundError, pd.errors.EmptyDataError):
            new_id = 1

        # Menulis data baru ke file CSV
        with open(CSV_FILE_PATH, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if os.stat(CSV_FILE_PATH).st_size == 0:
                writer.writerow(['ID', 'Nama', 'Kategori', 'Latitude', 'Longitude', 'Sumber', 'Deskripsi', 'Nama File Gambar'])
            writer.writerow([new_id, nama, kategori, latitude, longitude, "Manual Input", deskripsi, gambar_path])

        return redirect('map_view')

    return render(request, 'map_app/add_coordinate.html')



@login_required
def edit_coordinate(request, id):
    try:
        data = pd.read_csv(CSV_FILE_PATH)
        data.reset_index(drop=True, inplace=True)
    except FileNotFoundError:
        return redirect('map_view')

    if request.method == 'POST':
        row_to_edit = data[data['ID'] == id]

        if not row_to_edit.empty:
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

            gambar = request.FILES.get('gambar')
            if gambar:
                gambar_path_old = row_to_edit.iloc[0]['Nama File Gambar']
                if pd.notna(gambar_path_old) and os.path.exists(os.path.join(settings.MEDIA_ROOT, gambar_path_old)):
                    os.remove(os.path.join(settings.MEDIA_ROOT, gambar_path_old))

                gambar_path_new = f"images/{gambar.name}"
                gambar_full_path = os.path.join(settings.MEDIA_ROOT, gambar_path_new)
                os.makedirs(os.path.dirname(gambar_full_path), exist_ok=True)
                with open(gambar_full_path, 'wb') as f:
                    for chunk in gambar.chunks():
                        f.write(chunk)
                data.loc[data['ID'] == id, 'Nama File Gambar'] = gambar_path_new

            data.to_csv(CSV_FILE_PATH, index=False)

        return redirect('map_view')

    row = data[data['ID'] == id]
    if not row.empty:
        return render(request, 'map_app/edit_coordinate.html', {'row': row.iloc[0].to_dict(), 'id': id})

    return redirect('map_view')



@login_required
def delete_coordinate(request, id):
    try:
        data = pd.read_csv(CSV_FILE_PATH)
        data.reset_index(drop=True, inplace=True)
    except FileNotFoundError:
        return redirect('map_view')

    if request.method == 'POST':
        row_to_delete = data[data['ID'] == id]

        if not row_to_delete.empty:
            gambar_path = row_to_delete.iloc[0]['Nama File Gambar']
            if pd.notna(gambar_path) and os.path.exists(os.path.join(settings.MEDIA_ROOT, gambar_path)):
                os.remove(os.path.join(settings.MEDIA_ROOT, gambar_path))

            data = data[data['ID'] != id]

            data.to_csv(CSV_FILE_PATH, index=False)

        return redirect('map_view')

    row = data[data['ID'] == id]
    if not row.empty:
        return render(request, 'map_app/delete_coordinate.html', {'row': row.iloc[0].to_dict()})

    return redirect('map_view')



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            print(f"User {user.username} berhasil login.")  # Debug
            return redirect('map_view')
        else:
            messages.error(request, 'Username atau password salah!')

    return render(request, 'map_app/login.html')




def logout_view(request):
    logout(request)
    return redirect('map_view')



def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Password tidak cocok!')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah digunakan!')
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, 'Akun berhasil dibuat! Silakan login.')
        return redirect('login')

    return render(request, 'map_app/register.html')

from django.shortcuts import render

def about_pekanbaru(request):
    return render(request, 'map_app/about.html')
