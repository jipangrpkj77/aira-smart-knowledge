# AIRA Smart Knowledge™ V3.0 — Auto Sync + Manual Override

**Untuk SIGNTECH SOLUTION — projek ujian tempatan.** Mengekalkan visual, animasi dan fungsi chat AIRA V2.3. Menambah RAG berasaskan data awam website dan Google Sheets, tanpa perkhidmatan AI berbayar.

## Apa yang sistem buat

- Mengekstrak penerangan kursus, silibus, About dan bahagian HRD Corp daripada fail `main_12-11-2026.py` menggunakan Python AST — **fail itu tidak dilaksanakan oleh pengekstrak** dan tidak diubah.
- Mengambil hanya maklumat katalog daripada tiga Google Sheets yang dirujuk website: tajuk kursus, pilihan kursus pendaftaran dan pernyataan syarikat. **Tidak mengambil data pendaftaran peserta atau rekod FTP.**
- Menyimpan cebisan teks dalam SQLite di `knowledge/aira_knowledge.sqlite3`. Carian RAG menggunakan padanan kata BM/English sebelum jawapan diminta daripada Ollama (`qwen2.5:1.5b`).
- Melakukan **Auto Sync setiap 30 minit** apabila pelayan berjalan dan menawarkan **Sync Now** pada halaman pentadbir setempat `/admin`.
- Mengekalkan salinan data Google Sheets terakhir jika penyegerakan baharu gagal. Paparan status menunjukkan amaran dan bilangan rekod.
- Memaparkan sumber maklumat ringkas di bawah jawapan chatbot.
- Menyokong bahasa Melayu Malaysia atau English mengikut pertanyaan.

## Cara pemasangan di Windows

1. Hentikan dua PowerShell AIRA/Streamlit lama dengan `Ctrl + C` (jika sedang berjalan).
2. Ekstrak ZIP ini menjadi folder `E:\SIGNTECH SOLUTION\WEBSITE\PyMaskot\AIRA_Smart_Knowledge_V3_0`.
3. **Salin** fail `main_12-11-2026.py` daripada projek asal ke folder baharu ini di sebelah `widget_server.py`. Simpan fail asal di tempatnya; jangan ubah kandungannya.
4. Terminal pertama:

   ```powershell
   cd "E:\SIGNTECH SOLUTION\WEBSITE\PyMaskot\AIRA_Smart_Knowledge_V3_0"
   python widget_server.py
   ```

5. Buka `http://127.0.0.1:8765` untuk ujian avatar dan chat.
6. Terminal kedua:

   ```powershell
   cd "E:\SIGNTECH SOLUTION\WEBSITE\PyMaskot\AIRA_Smart_Knowledge_V3_0"
   python -m streamlit run run_site_with_aira.py --server.port 8501
   ```

7. Buka `http://localhost:8501`. Tekan `Ctrl + F5` jika browser menggunakan fail cache lama.

## Pentadbir Sync Now

1. Buka `http://127.0.0.1:8765/admin` pada komputer yang menjalankan AIRA.
2. Salin token yang dipaparkan **secara setempat** dalam terminal `widget_server.py` pada baris `ADMIN SYNC TOKEN`. Jangan kongsi token atau screenshot baris ini.
3. Masukkan token pada halaman admin dan klik **Sync Now**.
4. Semak rekod dan warnings. Jika Google Sheets tidak awam atau tiada internet, data tempatan daripada fail Python masih boleh digunakan.

**Nota:** `knowledge/.admin_token` dijana sendiri pada komputer ketika pelayan pertama kali berjalan. Jangan terbitkan fail token atau database ke web.

## Ujian yang disyorkan

- `Saya baru belajar Python. Kursus apa yang sesuai untuk saya?`
- `What Python courses does SIGNTECH offer?`
- `Bagaimana cara daftar kursus?`
- `Apakah maklumat terkini yuran kursus?` (AIRA tidak boleh mereka yuran)
- Cuba Google Sheets tidak boleh diakses, kemudian pastikan chat masih merujuk kepada kandungan website terakhir.

## Keselamatan dan had

- Tidak mengubah atau menyertakan fail `main_12-11-2026.py` dalam ZIP. Fail itu masih mengandungi kelayakan FTP asal; **tukar kata laluan FTP sebelum penerbitan** dan pindahkan kelayakan ke environment variables/secrets manager.
- Hanya sumber awam pilihan digunakan; teks poster berbentuk imej, gambar testimoni dan data pendaftaran sebenar **tidak dibaca**. Untuk kandungan poster, sediakan teks rasmi dalam katalog Google Sheets.
- Tiada pengindeksan rawak ke semua fail, helaian peribadi atau laman yang tidak diluluskan.
- Pelayan Python mendengar pada `127.0.0.1` sahaja. Ini prototaip pembangunan; jangan terbitkan port 8765 ke internet tanpa HTTPS, autentikasi dan reka bentuk backend selamat.
- Auto Sync berlaku hanya selagi pelayan berjalan; kemas kini Google Sheets bergantung pada capaian awam/network. RAG semasa ialah carian leksikal dalam SQLite, bukan vector embeddings. Model Ollama masih boleh membuat kesilapan; maklumat kritikal perlu disahkan.
- Integrasi widget menggunakan Streamlit iframe bridge daripada versi terdahulu; sesetengah versi/browser mungkin menyekatnya.

## Struktur utama

- `widget_server.py` — pelayan AIRA + API chat + admin Sync Now
- `knowledge_engine.py` — pengekstrak selamat, SQLite, retrieval RAG dan penyegerakan
- `web/admin.html` — panel admin setempat
- `web/embed.js`, `web/widget.css` — widget animasi dan sumber jawapan
- `run_site_with_aira.py` — pelancar halaman SIGNTECH tanpa meminda fail asal
- `assets/` — aset animasi AIRA V2.3
