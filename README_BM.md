# AIRA SIGNTECH All-in-One V4.4 — Smart Response & UI Refinement

Pakej lengkap berasaskan ZIP V4.3 pengguna. Satu fail Python, aset AIRA asal, RAG SQLite dan Gemini/Groq. Tiada patch tambahan diperlukan.

## Windows
1. Hentikan Streamlit lama (Ctrl+C). Ekstrak ZIP ke PyMaskot.
2. Salin folder `.streamlit` dari pemasangan lama secara setempat sahaja. Gunakan API key yang masih sah; jangan kongsi secrets.toml atau muat naik ke GitHub. Jika pernah terdedah, batalkan dan jana semula kunci. Tetapkan AIRA_ADMIN_TOKEN sekurang-kurangnya 24 aksara untuk akses admin.
3. Buka PowerShell dalam folder V4.4.
4. `python -m pip install -r requirements.txt`
5. `python -m streamlit run SIGNTECH_AIRA_ALL_IN_ONE.py --server.port 8501`
6. Buka http://127.0.0.1:8501 dan tekan Ctrl+F5.

## Perubahan
- CSS borang Registration dan Trainer: input, dropdown, textarea, upload, nama fail dan placeholder. CSS menyasarkan elemen Streamlit; versi frontend mungkin mempengaruhi hasil paparan.
- Cache bacaan CSV awam selama 5 minit; buang dua rerun berlebihan untuk Details/Syllabus. CSS mengurangkan kesan pudar elemen stale; rerun Streamlit masih berlaku dan kandungan lama boleh kekal seketika. Jangan anggap permohonan berjaya sebelum mesej pengesahan.
- Katalog Python/AI/Power BI dan kategori lain, deduplikasi akhiran tarikh dalam kurungan, cadangan pemula, tarikh yang disenaraikan, pendaftaran dan WhatsApp tanpa API. Jika katalog belum disegerakkan, hanya senarai sandaran dalam kod website digunakan dan dilabel.
- RAG mengambil sehingga tujuh petikan; konteks soalan susulan terhad kepada tiga soalan pengguna yang melepasi penapis. Maklumat peribadi jangan dimasukkan ke chat; penapis bukan jaminan pengesanan semua data sulit.
- Gemini/Groq dan had kuota dikekalkan; diagnostik pentadbir tidak mencetak kunci atau badan ralat API. Admin: http://127.0.0.1:8501/?aira_admin=1. Masukkan token dan klik Test Gemini + Groq untuk menguji kedua-duanya (menggunakan kuota). Sync Now tersedia. Auto Sync 30 minit ketika aplikasi aktif.
- WhatsApp rasmi dengan mesej automatik BM. Animasi, poster dan fungsi asal website dikekalkan; fungsi FTP masih memerlukan konfigurasi storan/kelayakan yang sah. Tiada token, API key, data peserta atau pangkalan data lama disertakan.

## Streamlit Cloud
Gunakan SIGNTECH_AIRA_ALL_IN_ONE.py sebagai entrypoint dan masukkan konfigurasi di Manage app > Settings > Secrets. Jangan aktifkan billing semata-mata untuk ujian. Model lalai diwarisi daripada V4.3 dan boleh ditukar melalui Secrets mengikut ketersediaan akaun. Data SQLite setempat di Cloud bukan storan kekal.

## Ujian
`python SIGNTECH_AIRA_ALL_IN_ONE.py --check` menguji struktur offline. Semakan tambahan lulus untuk katalog kategori BM/EN, deduplikasi tarikh, cadangan pemula, sapaan, pendaftaran, tarikh contoh, fallback Gemini ke Groq simulasi dan penapis pengulangan. Sintaks JS lulus. Google Sheets sebenar, API sebenar, penghantaran borang dan kesan visual browser tidak diuji dalam persekitaran binaan (Streamlit tidak dipasang). Uji pada komputer pengguna sebelum deployment.
