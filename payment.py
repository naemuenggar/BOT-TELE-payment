import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# ===== CONFIG =====
TOKEN = ""  # Ganti token bot
ADMIN_IDS = []  # Ganti ID Telegram admin
STORE_NAME = "Toko"
ADMIN_USERNAME = "admin_username"  # Ganti dengan username Telegram admin (tanpa @)
DATA_FILE = "transactions.json"
PRODUCTS_FILE = "products.json"
QRIS_IMAGE = "qris.png"  # File gambar QRIS

# ===== PAYMENT METHODS =====
PAYMENT_METHODS = {
    "qris": "📱 QRIS",
}

# ===== DATABASE SIMPLE (JSON) =====
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"transactions": [], "counter": 0}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            return json.load(f)
    return {
        "Paket Basic": {"price": 50000, "desc": "Bot setup + training"},
        "Paket Premium": {"price": 150000, "desc": "Bot + maintenance 1 bulan"},
        "Paket Reseller": {"price": 500000, "desc": "Source code + unlimited client"},
        "Custom Bot": {"price": 300000, "desc": "Bot custom sesuai request"},
    }

def save_products(products):
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, indent=2)

# ===== KEYBOARD =====
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🛒 Beli Produk", callback_data="buy")],
        [InlineKeyboardButton("📋 Cek Pesanan", callback_data="check_order")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq"), InlineKeyboardButton("💳 Pembayaran", callback_data="payment_methods")],
        [InlineKeyboardButton("📞 Contact Admin", callback_data="contact")],
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Lihat Transaksi", callback_data="admin_transactions")],
        [InlineKeyboardButton("✅ Konfirmasi Pembayaran", callback_data="admin_confirm")],
        [InlineKeyboardButton("📦 Kelola Produk", callback_data="admin_products")],
    ]
    return InlineKeyboardMarkup(keyboard)

def payment_keyboard(transaction_id, product_name=None):
    keyboard = []
    for key, name in PAYMENT_METHODS.items():
        keyboard.append([InlineKeyboardButton(name, callback_data=f"pay_{transaction_id}_{key}")])
    if product_name:
        keyboard.append([InlineKeyboardButton("🔙 Kembali ke Produk", callback_data="buy")])
    else:
        keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(transaction_id):
    keyboard = [
        [
            InlineKeyboardButton("✅ Konfirmasi", callback_data=f"confirm_{transaction_id}"),
            InlineKeyboardButton("❌ Tolak", callback_data=f"reject_{transaction_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_confirm_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Lihat Transaksi Pending", callback_data="admin_confirm_list")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== QRIS PAYMENT INFO =====
QRIS_INFO = {
    "name": "QRIS",
    "instruction": "Scan QR Code di atas untuk melakukan pembayaran.",
}


# ===== HANDLERS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_admin = user.id in ADMIN_IDS
    
    welcome = f"""
🛍️ *{STORE_NAME} - Payment Gateway*

Selamat datang {user.first_name}!

Silakan pilih menu di bawah:
"""
    
    keyboard = admin_menu() if is_admin else main_menu()
    await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=keyboard)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data
    is_admin = user.id in ADMIN_IDS
    
    # === BUY PRODUCT ===
    if data == "buy":
        products = load_products()
        text = "🛒 *Pilih Produk:*\n\n"
        keyboard = []
        for name, info in products.items():
            text += f"📦 *{name}*\n   💰 Rp {info['price']:,}\n   📝 {info['desc']}\n\n"
            keyboard.append([InlineKeyboardButton(f"Beli {name} - Rp {info['price']:,}", callback_data=f"order_{name}")])
        keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_main")])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # === ORDER PRODUCT ===
    elif data.startswith("order_"):
        product_name = data.replace("order_", "")
        products = load_products()
        product = products.get(product_name)
        
        if product:
            db = load_data()
            db["counter"] += 1
            transaction_id = f"INV-{db['counter']:04d}"
            
            transaction = {
                "id": transaction_id,
                "user_id": user.id,
                "username": user.username or user.first_name,
                "product": product_name,
                "price": product["price"],
                "status": "pending",
                "payment_method": "qris",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "proof": None,
            }
            db["transactions"].append(transaction)
            save_data(db)
            
            # Hapus pesan sebelumnya
            await query.message.delete()
            
            caption = (
                f"\U0001f4cb *INVOICE #{transaction_id}*\n\n"
                f"\U0001f4e6 Produk: {product_name}\n"
                f"\U0001f4b0 Harga: Rp {product['price']:,}\n"
                f"\U0001f4c5 Tanggal: {transaction['date']}\n"
                f"\U0001f4cc Status: *Menunggu Pembayaran*\n\n"
                f"\U0001f4b3 Metode: *QRIS*\n"
                f"\U0001f4dd {QRIS_INFO['instruction']}\n\n"
                f"\u26a0\ufe0f Setelah transfer, kirim bukti pembayaran (foto/screenshot) ke sini."
            )
            
            keyboard = [
                [InlineKeyboardButton("\U0001f4e4 Upload Bukti", callback_data=f"upload_{transaction_id}")],
                [InlineKeyboardButton("\U0001f519 Kembali ke Produk", callback_data="buy_fresh")],
                [InlineKeyboardButton("\U0001f519 Menu Utama", callback_data="back_main_fresh")],
            ]
            
            qris_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), QRIS_IMAGE)
            with open(qris_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            
            # Notifikasi ke admin: ada pesanan baru
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        admin_id,
                        f"\U0001f6d2 *PESANAN BARU!*\n\n"
                        f"\U0001f4cb Invoice: #{transaction_id}\n"
                        f"\U0001f464 Pembeli: @{user.username or user.first_name}\n"
                        f"\U0001f4e6 Produk: {product_name}\n"
                        f"\U0001f4b0 Harga: Rp {product['price']:,}\n"
                        f"\U0001f4c5 Waktu: {transaction['date']}\n\n"
                        f"\u23f3 Menunggu pembayaran via QRIS",
                        parse_mode="Markdown"
                    )
                except:
                    pass
    
    # === BACK FROM QRIS PHOTO MESSAGE ===
    elif data == "buy_fresh":
        # Hapus pesan foto QRIS lalu kirim daftar produk baru
        await query.message.delete()
        products = load_products()
        text = "\U0001f6d2 *Pilih Produk:*\n\n"
        keyboard = []
        for name, info in products.items():
            text += f"\U0001f4e6 *{name}*\n   \U0001f4b0 Rp {info['price']:,}\n   \U0001f4dd {info['desc']}\n\n"
            keyboard.append([InlineKeyboardButton(f"Beli {name} - Rp {info['price']:,}", callback_data=f"order_{name}")])
        keyboard.append([InlineKeyboardButton("\U0001f519 Kembali", callback_data="back_main")])
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "back_main_fresh":
        # Hapus pesan foto QRIS lalu kirim menu utama baru
        await query.message.delete()
        is_admin_user = user.id in ADMIN_IDS
        keyboard = admin_menu() if is_admin_user else main_menu()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="\U0001f6cd\ufe0f *Menu Utama*",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    # === UPLOAD BUKTI ===
    elif data.startswith("upload_"):
        transaction_id = data.replace("upload_", "")
        context.user_data["waiting_proof"] = transaction_id
        await query.message.reply_text(
            f"\U0001f4f8 *Upload Bukti Pembayaran*\n\n"
            f"\U0001f4cb Invoice: #{transaction_id}\n\n"
            f"Silakan kirim *foto/screenshot* bukti pembayaran kamu sekarang.\n"
            f"Langsung kirim gambarnya ke chat ini.",
            parse_mode="Markdown"
        )
    
    # === CHECK ORDER ===
    elif data == "check_order":
        db = load_data()
        user_transactions = [t for t in db["transactions"] if t["user_id"] == user.id]
        
        if not user_transactions:
            text = "📋 Kamu belum punya transaksi."
        else:
            text = "📋 *Pesanan Kamu:*\n\n"
            for t in user_transactions[-10:]:  # 10 terakhir
                status_emoji = {"pending": "⏳", "confirmed": "✅", "rejected": "❌"}.get(t["status"], "❓")
                text += f"{status_emoji} *{t['id']}* - {t['product']}\n   Rp {t['price']:,} | {t['date']}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="back_main")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # === PAYMENT METHODS INFO ===
    elif data == "payment_methods":
        text = "💳 *Metode Pembayaran:*\n\n"
        for key, name in PAYMENT_METHODS.items():
            text += f"✅ {name}\n"
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="back_main")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # === CONTACT ===
    elif data == "contact":
        text = f"📞 *Contact Admin*\n\nHubungi: @{ADMIN_USERNAME}"
        keyboard = [
            [InlineKeyboardButton("💬 Chat Admin", url=f"https://t.me/{ADMIN_USERNAME}")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_main")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # === FAQ MENU ===
    elif data == "faq":
        text = (
            "❓ *FAQ - Pertanyaan Umum*\n\n"
            "Pilih topik yang ingin kamu ketahui:"
        )
        keyboard = [
            [InlineKeyboardButton("🛒 Cara Order", callback_data="faq_order")],
            [InlineKeyboardButton("💳 Cara Bayar", callback_data="faq_bayar")],
            [InlineKeyboardButton("📦 Status Pesanan", callback_data="faq_status")],
            [InlineKeyboardButton("🛡️ Garansi & Refund", callback_data="faq_garansi")],
            [InlineKeyboardButton("⏰ Jam Operasional", callback_data="faq_jam")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_main")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "faq_order":
        text = (
            "🛒 *Cara Order*\n\n"
            "1\ufe0f\u20e3 Tekan *Beli Produk* di menu utama\n"
            "2\ufe0f\u20e3 Pilih produk yang kamu mau\n"
            "3\ufe0f\u20e3 Invoice otomatis dibuat\n"
            "4\ufe0f\u20e3 Scan QRIS untuk bayar\n"
            "5\ufe0f\u20e3 Upload bukti pembayaran\n"
            "6\ufe0f\u20e3 Tunggu admin konfirmasi\n"
            "7\ufe0f\u20e3 Selesai! Admin akan hubungi kamu\n\n"
            "💡 Prosesnya cepat dan mudah!"
        )
        keyboard = [
            [InlineKeyboardButton("🔙 Kembali ke FAQ", callback_data="faq")],
            [InlineKeyboardButton("🔙 Menu Utama", callback_data="back_main")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "faq_bayar":
        text = (
            "💳 *Cara Bayar*\n\n"
            "Saat ini kami hanya menerima pembayaran via:\n\n"
            "📱 *QRIS* (scan dari e-wallet / m-banking apapun)\n\n"
            "\u2705 GoPay, OVO, Dana, ShopeePay\n"
            "\u2705 BCA Mobile, Mandiri, BRI, BNI\n"
            "\u2705 Semua bank & e-wallet yang support QRIS\n\n"
            "*Langkah:*\n"
            "1. Pilih produk & buat pesanan\n"
            "2. QR Code akan muncul otomatis\n"
            "3. Scan pakai aplikasi bank / e-wallet kamu\n"
            "4. Screenshot bukti transfer\n"
            "5. Kirim screenshot ke chat ini"
        )
        keyboard = [
            [InlineKeyboardButton("🔙 Kembali ke FAQ", callback_data="faq")],
            [InlineKeyboardButton("🔙 Menu Utama", callback_data="back_main")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "faq_status":
        text = (
            "📦 *Status Pesanan*\n\n"
            "Cek status pesanan kamu lewat menu *Cek Pesanan*.\n\n"
            "\u23f3 *Pending* - Menunggu pembayaran / verifikasi\n"
            "\u2705 *Confirmed* - Pembayaran dikonfirmasi\n"
            "\u274c *Rejected* - Pembayaran ditolak\n\n"
            "💡 Setelah upload bukti, admin biasanya konfirmasi dalam beberapa menit."
        )
        keyboard = [
            [InlineKeyboardButton("🔙 Kembali ke FAQ", callback_data="faq")],
            [InlineKeyboardButton("🔙 Menu Utama", callback_data="back_main")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "faq_garansi":
        text = (
            "🛡️ *Garansi & Refund*\n\n"
            "\u2705 Semua produk bergaransi\n"
            "\u2705 Jika ada kendala, hubungi admin\n"
            "\u2705 Refund tersedia jika produk bermasalah\n\n"
            "\u26a0\ufe0f *Syarat refund:*\n"
            "\u2022 Lapor dalam 1x24 jam setelah pembelian\n"
            "\u2022 Sertakan bukti masalah (screenshot/video)\n"
            "\u2022 Produk belum digunakan / dimodifikasi\n\n"
            f"📞 Hubungi: @{ADMIN_USERNAME}"
        )
        keyboard = [
            [InlineKeyboardButton("💬 Chat Admin", url=f"https://t.me/{ADMIN_USERNAME}")],
            [InlineKeyboardButton("🔙 Kembali ke FAQ", callback_data="faq")],
            [InlineKeyboardButton("🔙 Menu Utama", callback_data="back_main")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "faq_jam":
        text = (
            "\u23f0 *Jam Operasional*\n\n"
            "\U0001f7e2 *Senin - Sabtu*\n"
            "   08.00 - 22.00 WIB\n\n"
            "\U0001f534 *Minggu*\n"
            "   10.00 - 20.00 WIB\n\n"
            "💡 Bot tetap bisa dipakai 24 jam,\n"
            "tapi konfirmasi pembayaran hanya di jam operasional.\n\n"
            f"📞 Urgent? Chat admin: @{ADMIN_USERNAME}"
        )
        keyboard = [
            [InlineKeyboardButton("🔙 Kembali ke FAQ", callback_data="faq")],
            [InlineKeyboardButton("🔙 Menu Utama", callback_data="back_main")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    # === ADMIN: VIEW TRANSACTIONS ===
    elif data == "admin_transactions" and is_admin:
        db = load_data()
        if not db["transactions"]:
            text = "📊 Belum ada transaksi."
        else:
            text = "📊 *Semua Transaksi:*\n\n"
            for t in db["transactions"][-20:]:
                status = {"pending": "⏳", "confirmed": "✅", "rejected": "❌"}.get(t["status"], "❓")
                text += f"{status} *{t['id']}* - {t['product']}\n   👤 {t['username']} | Rp {t['price']:,}\n   💳 {t.get('payment_method', '-')} | {t['date']}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # === ADMIN: CONFIRM PAYMENT ===
    elif data == "admin_confirm" and is_admin:
        db = load_data()
        pending = [t for t in db["transactions"] if t["status"] == "pending"]
        
        if not pending:
            text = "✅ Tidak ada transaksi pending."
            keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")]]
        else:
            text = "📋 *Transaksi Pending:*\n\n"
            keyboard = []
            for t in pending:
                text += f"⏳ *{t['id']}* - {t['product']}\n   👤 {t['username']} | Rp {t['price']:,}\n   💳 {t.get('payment_method', '-')}\n\n"
                keyboard.append([InlineKeyboardButton(f"Proses {t['id']}", callback_data=f"confirm_{t['id']}")])
            keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # === ADMIN: CONFIRM SPECIFIC ===
    elif data.startswith("confirm_") and is_admin:
        transaction_id = data.replace("confirm_", "")
        db = load_data()
        
        for t in db["transactions"]:
            if t["id"] == transaction_id:
                t["status"] = "confirmed"
                save_data(db)
                
                # Notifikasi ke user
                try:
                    confirm_kb_user = InlineKeyboardMarkup([
                        [InlineKeyboardButton("💬 Hubungi Admin", url=f"https://t.me/{ADMIN_USERNAME}")]
                    ])
                    await context.bot.send_message(
                        t["user_id"],
                        f"✅ *Pembayaran Dikonfirmasi!*\n\n"
                        f"📋 Invoice: #{t['id']}\n"
                        f"📦 Produk: {t['product']}\n"
                        f"💰 Harga: Rp {t['price']:,}\n\n"
                        f"Terima kasih! Hubungi admin untuk proses selanjutnya.\n"
                        f"📞 Admin: @{ADMIN_USERNAME}",
                        parse_mode="Markdown",
                        reply_markup=confirm_kb_user
                    )
                except:
                    pass
                
                keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="admin_confirm")]]
                await query.edit_message_text(
                    f"✅ Transaksi #{transaction_id} dikonfirmasi!\nUser telah dinotifikasi.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
    
    # === ADMIN: REJECT ===
    elif data.startswith("reject_") and is_admin:
        transaction_id = data.replace("reject_", "")
        db = load_data()
        
        for t in db["transactions"]:
            if t["id"] == transaction_id:
                t["status"] = "rejected"
                save_data(db)
                
                try:
                    await context.bot.send_message(
                        t["user_id"],
                        f"❌ *Pembayaran Ditolak*\n\n"
                        f"📋 Invoice: #{t['id']}\n"
                        f"Silakan hubungi admin untuk info lebih lanjut.",
                        parse_mode="Markdown"
                    )
                except:
                    pass
                
                keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="admin_confirm")]]
                await query.edit_message_text(
                    f"❌ Transaksi #{transaction_id} ditolak.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
    
    # === ADMIN: PRODUCTS ===
    elif data == "admin_products" and is_admin:
        products = load_products()
        text = "📦 *Kelola Produk:*\n\n"
        for name, info in products.items():
            text += f"📦 {name} - Rp {info['price']:,}\n   {info['desc']}\n\n"
        text += "Gunakan /addproduct untuk tambah produk"
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # === BACK BUTTONS ===
    elif data == "back_main":
        await query.edit_message_text("🛍️ *Menu Utama*", parse_mode="Markdown", reply_markup=main_menu())
    
    elif data == "admin_back" and is_admin:
        await query.edit_message_text("🔧 *Admin Panel*", parse_mode="Markdown", reply_markup=admin_menu())


async def handle_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user upload bukti pembayaran"""
    user = update.effective_user
    
    if update.message.photo:
        # Cari transaksi pending user ini
        db = load_data()
        user_pending = [t for t in db["transactions"] if t["user_id"] == user.id and t["status"] == "pending"]
        
        if user_pending:
            transaction = user_pending[-1]  # Ambil yang terbaru
            
            # Notifikasi ke admin dengan tombol konfirmasi
            confirm_kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Konfirmasi", callback_data=f"confirm_{transaction['id']}"),
                    InlineKeyboardButton("❌ Tolak", callback_data=f"reject_{transaction['id']}"),
                ]
            ])
            
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        admin_id,
                        f"📤 *BUKTI PEMBAYARAN BARU*\n\n"
                        f"📋 Invoice: #{transaction['id']}\n"
                        f"👤 User: @{user.username or user.first_name}\n"
                        f"📦 Produk: {transaction['product']}\n"
                        f"💰 Harga: Rp {transaction['price']:,}\n"
                        f"💳 Metode: {transaction.get('payment_method', '-')}",
                        parse_mode="Markdown"
                    )
                    await context.bot.forward_message(admin_id, update.message.chat_id, update.message.message_id)
                    await context.bot.send_message(
                        admin_id,
                        f"⬆️ Bukti pembayaran untuk *#{transaction['id']}*\n\n"
                        f"Pilih aksi:",
                        parse_mode="Markdown",
                        reply_markup=confirm_kb
                    )
                except:
                    pass
            
            await update.message.reply_text(
                "✅ *Bukti pembayaran diterima!*\n\n"
                "Admin akan memverifikasi pembayaran kamu.\n"
                "Tunggu notifikasi selanjutnya.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Kamu belum punya transaksi pending.")
    
    elif update.message.text and update.message.text.startswith("/"):
        pass  # Biarkan command handler lain yang handle
    else:
        # Kalau user kirim text random, tampilkan menu utama
        user = update.effective_user
        is_admin = user.id in ADMIN_IDS
        
        welcome = (
            f"\U0001f6cd\ufe0f *{STORE_NAME} - Payment Gateway*\n\n"
            f"Hai {user.first_name}!\n"
            f"Silakan pilih menu di bawah:"
        )
        keyboard = admin_menu() if is_admin else main_menu()
        await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=keyboard)


async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: tambah produk"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return
    
    # Format: /addproduct Nama Produk | Harga | Deskripsi
    args = update.message.text.replace("/addproduct ", "")
    parts = args.split("|")
    
    if len(parts) < 2:
        await update.message.reply_text("❌ Format: `/addproduct Nama | Harga | Deskripsi`", parse_mode="Markdown")
        return
    
    name = parts[0].strip()
    price = int(parts[1].strip())
    desc = parts[2].strip() if len(parts) > 2 else "-"
    
    products = load_products()
    products[name] = {"price": price, "desc": desc}
    save_products(products)
    
    await update.message.reply_text(f"✅ Produk *{name}* ditambahkan!\n💰 Rp {price:,}\n📝 {desc}", parse_mode="Markdown")


async def delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: hapus produk"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return
    
    name = update.message.text.replace("/delproduct ", "").strip()
    products = load_products()
    
    if name in products:
        del products[name]
        save_products(products)
        await update.message.reply_text(f"✅ Produk *{name}* dihapus!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Produk tidak ditemukan.")

async def revenue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: cek pendapatan"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return
    
    db = load_data()
    confirmed = [t for t in db["transactions"] if t["status"] == "confirmed"]
    total = sum(t["price"] for t in confirmed)
    
    text = (
        "\U0001f4ca *LAPORAN PENDAPATAN*\n\n"
        f"\u2705 Transaksi Berhasil: {len(confirmed)}\n"
        f"\U0001f4b0 Total Pendapatan: Rp {total:,}\n"
        f"\U0001f4c5 Periode: All time"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ===== MAIN =====
async def post_init(application):
    """Set bot commands saat startup"""
    from telegram import BotCommand, BotCommandScopeChat
    
    # Commands untuk semua user
    user_commands = [
        BotCommand("start", "\U0001f6cd\ufe0f Buka Menu Utama"),
    ]
    await application.bot.set_my_commands(user_commands)
    
    # Commands tambahan untuk admin
    admin_commands = [
        BotCommand("start", "\U0001f6cd\ufe0f Buka Admin Panel"),
        BotCommand("addproduct", "\U0001f4e6 Tambah Produk"),
        BotCommand("delproduct", "\U0001f5d1\ufe0f Hapus Produk"),
        BotCommand("revenue", "\U0001f4ca Laporan Pendapatan"),
    ]
    for admin_id in ADMIN_IDS:
        try:
            await application.bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
        except:
            pass


def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addproduct", add_product))
    app.add_handler(CommandHandler("delproduct", delete_product))
    app.add_handler(CommandHandler("revenue", revenue))
    
    # Button handler
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Bukti pembayaran (foto)
    app.add_handler(MessageHandler(filters.PHOTO, handle_proof))
    
    # Semua pesan teks selain command -> tampilkan menu
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_proof))
    
    print("=" * 50)
    print(f"\U0001f6cd\ufe0f {STORE_NAME} - Payment Gateway")
    print("\u2705 Bot siap menerima pembayaran")
    print(f"\U0001f451 Admin: {len(ADMIN_IDS)} user")
    print("\U0001f4f1 Kirim /start di Telegram")
    print("=" * 50)
    
    app.run_polling()


if __name__ == "__main__":
    # Init files
    if not os.path.exists(DATA_FILE):
        save_data({"transactions": [], "counter": 0})
    if not os.path.exists(PRODUCTS_FILE):
        save_products({
            "Paket Basic": {"price": 50000, "desc": "Bot setup + training"},
            "Paket Premium": {"price": 150000, "desc": "Bot + maintenance 1 bulan"},
            "Paket Reseller": {"price": 500000, "desc": "Source code + unlimited client"},
        })
    
    main()