# 🛒 Telegram Payment Gateway Bot

Bot Telegram untuk mengelola pesanan dan menerima pembayaran via **QRIS**. Bot ini dilengkapi dengan fitur katalog produk, upload bukti transfer, serta Panel Admin lengkap untuk memverifikasi pembayaran dan mengelola produk.

## ✨ Fitur Utama

### 👤 Untuk User (Pembeli)
- **Katalog Produk:** Melihat daftar produk yang tersedia beserta harganya.
- **Order & Invoice:** Membuat pesanan dan otomatis mendapatkan Invoice.
- **Pembayaran QRIS:** Menerima pembayaran menggunakan QRIS dari semua E-Wallet & Mobile Banking.
- **Upload Bukti Pembayaran:** User dapat mengirimkan foto/screenshot bukti transfer langsung ke bot.
- **Cek Status Pesanan:** Melacak riwayat dan status pesanan (Pending / Confirmed / Rejected).
- **FAQ & Bantuan:** Menu interaktif untuk melihat cara order, cara bayar, dll.

### 👮‍♂️ Untuk Admin
- **Notifikasi Real-time:** Mendapatkan notifikasi saat ada pesanan baru dan saat user mengunggah bukti pembayaran.
- **Konfirmasi Pembayaran:** Menerima atau menolak pembayaran langsung dari chat bot dengan sekali klik.
- **Manajemen Produk:** Menambah (`/addproduct`) dan menghapus (`/delproduct`) produk langsung dari Telegram.
- **Laporan Transaksi:** Melihat seluruh riwayat transaksi.
- **Laporan Pendapatan:** Cek total pendapatan (`/revenue`) dari transaksi yang berhasil.

---

## 🚀 Cara Instalasi & Penggunaan

### 1. Persiapan
Pastikan kamu sudah menginstal **Python 3.8+** di komputermu.
Clone repository ini ke komputer/server kamu:
```bash
git clone https://github.com/naemuenggar/BOT-TELE-payment.git
cd BOT-TELE-payment
```

### 2. Install Dependencies
Bot ini menggunakan library `python-telegram-bot`. Install menggunakan pip:
```bash
pip install python-telegram-bot
```

### 3. Konfigurasi Bot
Buka file `payment.py` dan ubah beberapa variabel di bagian **CONFIG**:
```python
TOKEN = "MASUKKAN_TOKEN_BOT_DARI_BOTFATHER_DI_SINI"
ADMIN_IDS = [123456789]  # Ganti dengan ID Telegram Admin (bisa lebih dari satu)
STORE_NAME = "Nama Toko Kamu"
ADMIN_USERNAME = "username_admin"  # Username admin untuk kontak bantuan (tanpa @)
```
*Catatan: Pastikan file gambar QRIS kamu sudah disiapkan dengan nama `qris.png` di folder yang sama.*

### 4. Jalankan Bot
Jalankan bot dengan perintah:
```bash
python payment.py
```
Bot sudah siap menerima pesanan! 🚀

---

## 🗄️ Database
Bot ini menggunakan penyimpanan sederhana berbasis file JSON:
- `transactions.json`: Menyimpan seluruh data riwayat transaksi user.
- `products.json`: Menyimpan data produk yang dijual.
*(File ini akan otomatis terbuat saat pertama kali bot dijalankan jika belum ada).*

---

## 📝 Lisensi
Bebas digunakan dan dimodifikasi untuk kebutuhan tokomu.
