import os
import string
import random
from flask import Flask, request, redirect, jsonify, render_template, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "kunci_rahasia_untuk_flash_message" # Diperlukan untuk notifikasi

# Konfigurasi Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///urls.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class URLMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    long_url = db.Column(db.String(500), nullable=False)
    short_slug = db.Column(db.String(50), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)

def generate_random_slug(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# --- ROUTES ---

# 1. Halaman Utama (Visualisasi)
@app.route('/')
def index():
    all_urls = URLMapping.query.order_by(URLMapping.id.desc()).all()
    return render_template('index.html', urls=all_urls)

# 2. Proses Pemendekan URL (Handle Form & JSON)
@app.route('/shorten', methods=['POST'])
def shorten_url():
    # Mendukung data dari Form HTML atau JSON API
    if request.is_json:
        data = request.get_json()
        long_url = data.get('url')
        custom_slug = data.get('alias')
    else:
        long_url = request.form.get('url')
        custom_slug = request.form.get('alias')

    if not long_url:
        if request.is_json: return jsonify({"error": "URL wajib diisi"}), 400
        flash("URL asal wajib diisi!")
        return redirect('/')

    slug = custom_slug if custom_slug else generate_random_slug()

    if URLMapping.query.filter_by(short_slug=slug).first():
        if request.is_json: return jsonify({"error": "Alias sudah digunakan"}), 400
        flash("Alias sudah digunakan, silakan pilih yang lain.")
        return redirect('/')

    new_mapping = URLMapping(long_url=long_url, short_slug=slug)
    db.session.add(new_mapping)
    db.session.commit()

    short_url = f"{request.host_url}{slug}"
    
    if request.is_json:
        return jsonify({"short_url": short_url, "alias": slug}), 201
    
    all_urls = URLMapping.query.order_by(URLMapping.id.desc()).all()
    short_url = f"{request.host_url}{slug}"
    return render_template('index.html', short_url=short_url, urls=all_urls)


# 3. Redirect (GET)
@app.route('/<slug>')
def redirect_to_url(slug):
    mapping = URLMapping.query.filter_by(short_slug=slug).first_or_404()
    mapping.clicks += 1
    db.session.commit()
    return redirect(mapping.long_url)

# 4. Health Check (Syarat Tugas) 
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "url-shortener"}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)