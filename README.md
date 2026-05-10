# Sistem HR & Payroll Perusahaan (PKPL26)

Sistem ini merupakan aplikasi manajemen sumber daya manusia dan penggajian yang dibangun menggunakan framework **Django** dengan basis data **SQLite**. Sistem ini dirancang untuk mensimulasikan lingkungan operasional perusahaan dengan memperhatikan standar keamanan siber (*secure coding*).


## Role & Hak Akses Pengguna
1. **Karyawan**: Pengguna internal yang bertugas melakukan absensi harian dan melihat riwayat slip gaji miliknya.
2. **Manajer**: Pengguna dengan hak akses setingkat karyawan namun dapat di-expand sesuai kebutuhan operasional tim di masa mendatang.
3. **HR (SDM)**: Administrator yang memiliki otoritas mencetak dan *meng-generate* slip gaji bulanan untuk seluruh karyawan.


## Laporan Implementasi Keamanan (Security Implementation Report)

Berikut adalah 4 detail kerentanan utama, referensi CWE yang relevan, beserta mitigasi teknis yang telah diimplementasikan:

### 1. Pencegahan Code Injection (XSS)
- **Referensi CWE**: [CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')](https://cwe.mitre.org/data/definitions/79.html)
- **Vulnerability**: Form input yang tidak divalidasi dan teks yang tidak di-*escape* dapat disisipi tag `<script>` berbahaya yang akan tereksekusi oleh browser klien.
- **Snippet Sebelum (Vulnerable)**:
  ```html
  <!-- Tampilan langsung tanpa sanitasi/escape -->
  <td>{{ slip.total_salary | safe }}</td>
  ```
- **Snippet Sesudah (Secure)**:
  ```html
  <!-- Pembatasan karakter input di klien (Allowlist) -->
  <input type="text" id="username" name="username" required pattern="[a-zA-Z0-9_]+" maxlength="50">
  
  <!-- Django Auto-escaping aktif secara default -->
  <td>{{ slip.total_salary }}</td>
  ```
- **Argumen Mitigasi**: Kami menerapkan teknik *allowlist* menggunakan atribut HTML5 `pattern` dan `maxlength` pada antarmuka pengguna guna memblokir injeksi karakter aneh secara dini. Di sisi peladen, variabel dikelola menggunakan fitur *auto-escaping* bawaan *template engine* Django, yang secara otomatis mengonversi karakter khusus HTML menjadi representasi aman (misalnya `<script>` menjadi `&lt;script&gt;`).

### 2. Mitigasi Broken Authentication (Hashing & Session)
- **Referensi CWE**: [CWE-256: Unprotected Storage of Credentials](https://cwe.mitre.org/data/definitions/256.html) & [CWE-613: Insufficient Session Expiration](https://cwe.mitre.org/data/definitions/613.html)
- **Vulnerability**: Menyimpan kata sandi dalam teks terang (*plaintext*) dan membiarkan sesi tetap hidup tanpa batas waktu sangat rentan terhadap pencurian kredensial dan *Session Hijacking*.
- **Snippet Sebelum (Vulnerable)**:
  ```python
  SESSION_EXPIRE_AT_BROWSER_CLOSE = False
  # Kata sandi disimpan menggunakan MD5 atau tidak terenkripsi
  ```
- **Snippet Sesudah (Secure)**:
  ```python
  # settings.py
  PASSWORD_HASHERS = [
      'django.contrib.auth.hashers.PBKDF2PasswordHasher',
  ]
  SESSION_EXPIRE_AT_BROWSER_CLOSE = True
  ```
- **Argumen Mitigasi**: Untuk penyimpanan kata sandi, kami mewajibkan algoritma **PBKDF2** (*Password-Based Key Derivation Function 2*) bawaan Django yang sangat tangguh terhadap serangan *brute-force* maupun *rainbow tables* karena menerapkan iterasi komputasi yang tinggi. Untuk pengelolaan sesi, masa berlaku sesi diatur agar otomatis hancur seketika saat jendela browser ditutup, mencegah pencurian sesi jika pengguna lupa *logout* di komputer publik.

### 3. Mitigasi Broken Authentication (Lockout & Least Privilege)
- **Referensi CWE**: [CWE-307: Improper Restriction of Excessive Authentication Attempts](https://cwe.mitre.org/data/definitions/307.html) & [CWE-285: Improper Authorization](https://cwe.mitre.org/data/definitions/285.html)
- **Vulnerability**: Ketiadaan batas gagal *login* memungkinkan serangan tebak sandi masif (*Credential Stuffing/Brute-force*). Akses fungsional dan berkas sistem yang tidak dibatasi juga melanggar keamanan data.
- **Snippet Sebelum (Vulnerable)**:
  ```python
  def generate_payroll(request):
      # Dieksekusi secara publik tanpa validasi status HR
  ```
- **Snippet Sesudah (Secure)**:
  ```python
  # views.py (Least Privilege via RBAC)
  @login_required
  @user_passes_test(is_hr, login_url='/login/')
  def generate_payroll(request):
      ...
      
  # settings.py (Lockout)
  AXES_FAILURE_LIMIT = 5
  AXES_LOCK_OUT_AT_FAILURE = True
  ```
- **Argumen Mitigasi**: Kami mengintegrasikan pustaka `django-axes` yang segera memblokir dan mengunci IP serta akun setelah 5 kali kegagalan masuk berturut-turut. Pada area fungsional sistem, kami menerapkan *Role-Based Access Control* (RBAC) menggunakan dekorator Django untuk memastikan fungsi krusial seperti pencetakan slip gaji hanya dapat diakses oleh peran HR. Di level sistem operasi, hak akses file *database* (`db.sqlite3`) juga dibatasi dengan izin baca-tulis eksklusif hanya untuk *owner* sistem.

### 4. Perlindungan CSRF & Pencegahan SQL Injection
- **Referensi CWE**: [CWE-352: Cross-Site Request Forgery (CSRF)](https://cwe.mitre.org/data/definitions/352.html) & [CWE-89: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')](https://cwe.mitre.org/data/definitions/89.html)
- **Vulnerability**: Endpoint modifikasi data yang tak memiliki *token* rahasia sangat mudah dieksploitasi oleh web penyerang melalui klik tersembunyi. Sementara itu, penggunaan penggabungan *string* secara langsung ke *query* SQL memicu risiko pengeksekusian kueri ilegal oleh pengguna.
- **Snippet Sebelum (Vulnerable)**:
  ```python
  # Raw Query rentan SQL Injection
  Payroll.objects.raw(f"UPDATE payroll SET total = {amount} WHERE user_id = {user_id}")
  ```
- **Snippet Sesudah (Secure)**:
  ```html
  <!-- Template Form CSRF -->
  <form method="POST" action="{% url 'generate_payroll' %}">
      {% csrf_token %}
  </form>
  ```
  ```python
  # Django ORM Parameterized Query
  Payroll.objects.update_or_create(
      employee=employee,
      month=month, year=year,
      defaults={'total_salary': total_salary}
  )
  ```
- **Argumen Mitigasi**: Server dilindungi oleh `CsrfViewMiddleware` yang secara ketat memvalidasi kepemilikan sesi melalui *tag* `{% csrf_token %}` pada seluruh permintaan metode POST/PUT/DELETE. Untuk interaksi *database*, seluruh *raw SQL* ditinggalkan dan diganti secara mutlak dengan model dan *method* agregat bawaan Django ORM (seperti `update_or_create` atau `filter`). ORM Django secara inheren memproses argumen menggunakan metode *parameterized queries* pada *driver database* yang langsung menetralkan elemen ilegal.

---

## Petunjuk Instalasi & Menjalankan Aplikasi
Aplikasi ini bersifat lintas platform dan dapat dijalankan dengan mudah pada OS Windows, macOS, maupun Linux.

### Persyaratan Minimal
- **Python** versi 3.9 ke atas
- **Pip** (Package Installer Python)

### Langkah Instalasi
1. Lakukan *clone* terhadap repositori ini ke komputer lokal Anda:
   ```bash
   git clone https://gitlab.cs.ui.ac.id/pkpl26/57-basing/pkpl26_57_basing.git
   ```
2. Arahkan direktori terminal/Command Prompt ke dalam folder proyek:
   ```bash
   cd pkpl26_57_basing
   ```
3. Buat dan aktifkan **Virtual Environment** untuk mengisolasi instalasi pustaka:
   - **Windows**: 
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - **macOS/Linux**: 
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
4. Pasang modul dependensi yang dibutuhkan (Django dan django-axes):
   ```bash
   pip install django django-axes
   ```
5. *(Opsional)* Jika *database* perlu dikonfigurasi ulang, jalankan perintah migrasi:
   ```bash
   python manage.py makemigrations payroll_app
   python manage.py migrate
   ```
6. Jalankan server HTTP lokal bawaan Django:
   ```bash
   python manage.py runserver
   ```
7. Aplikasi sudah berjalan! Buka browser pilihan Anda dan akses `http://127.0.0.1:8000`.

## Screenshot Aplikasi: tampilan antarmuka utama, fitur keamanan, dan hasil test-case
- Screenshot Halaman Login
<img width="1470" height="956" alt="Screenshot 2026-05-10 at 20 58 17" src="https://github.com/user-attachments/assets/ac9c8fd1-5f7c-4343-a2d5-70bda7391ae6" />

- Screenshot Halaman Karyawan
<img width="1470" height="956" alt="Screenshot 2026-05-10 at 21 00 07" src="https://github.com/user-attachments/assets/77e15ae6-0621-475b-b85c-8239a03b65d6" />

- Screenshot Halaman HR Admin
<img width="1470" height="956" alt="Screenshot 2026-05-10 at 21 01 21" src="https://github.com/user-attachments/assets/70cfea99-1085-4046-997e-bcac30b159f7" />

- Proteksi CSRF
<img width="1470" height="956" alt="Screenshot 2026-05-10 at 21 03 39" src="https://github.com/user-attachments/assets/7cd08e60-8e97-4ebe-a6fc-f6cc5248ed68" />

- Test-Case Brute-Force & Akun Terkunci (Setelah memasukkan kredensial yang salah 6 kali berturut turut)
<img width="2940" height="1912" alt="image" src="https://github.com/user-attachments/assets/9f570aa1-a349-4f46-9668-dcdcb70e5caa" />

- Test-Case Role-Based Access Control / Least Privilege
1. Kita masuk dengan akun karyawan
<img width="1470" height="956" alt="Screenshot 2026-05-10 at 21 00 07" src="https://github.com/user-attachments/assets/77e15ae6-0621-475b-b85c-8239a03b65d6" />
2. Ganti url HR di browser
<img width="1470" height="956" alt="Screenshot 2026-05-10 at 21 09 35" src="https://github.com/user-attachments/assets/2a0e5bb6-6b13-4741-929f-1e75055d1b20" />
3. Halaman akan langsung beralih ke halaman login
<img width="1470" height="956" alt="Screenshot 2026-05-10 at 21 09 44" src="https://github.com/user-attachments/assets/fa9cd2e2-6d3c-433d-88c4-a9f37cb3cee2" />

- Test-Case Pencegahan XSS (Cross-Site Scripting)
<img width="1470" height="956" alt="Screenshot 2026-05-10 at 21 14 44" src="https://github.com/user-attachments/assets/c3f50bc0-1328-4cae-b73f-1b924c3cd7e1" />

- Bukti Hashing Database
<img width="860" height="62" alt="Screenshot 2026-05-10 at 21 19 12" src="https://github.com/user-attachments/assets/6d2a755d-e20f-4fef-ac0d-f32ec4ef7704" />

## Link Video Demonstrasi

> 🎥 [**Tonton Video Demonstrasi Sistem (YouTube Unlisted)**](https://youtu.be/egzvJqfmO3w)
