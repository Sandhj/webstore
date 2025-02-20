from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)
DATABASE = 'database.db'

# Fungsi untuk membuat tabel jika belum ada
def create_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            balance REAL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Route untuk halaman utama (login)
@app.route('/')
def login_page():
    # Jika pengguna sudah login, arahkan ke dashboard
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html')

# Route untuk halaman registrasi
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simpan data ke database (password disimpan dalam plain text)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login_page'))
        except sqlite3.IntegrityError:
            flash('Username sudah terdaftar!', 'error')
        finally:
            conn.close()

    return render_template('register.html')

# Route untuk proses login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user and user[1] == password:  # Periksa password (plain text)
        # Set session
        session['username'] = user[0]
        flash('Login berhasil!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Username atau password salah!', 'error')
        return redirect(url_for('login_page'))

# Route untuk dashboard
@app.route('/dashboard')
def dashboard():
    # Cek apakah pengguna sudah login
    if 'username' not in session:
        flash('Anda harus login terlebih dahulu!', 'error')
        return redirect(url_for('login_page'))

    # Ambil data pengguna dari database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (session['username'],))
    user = cursor.fetchone()
    conn.close()

    if user:
        return render_template('dashboard.html', username=user[0], balance=user[2])
    else:
        return redirect(url_for('login_page'))

# Route untuk logout
@app.route('/logout')
def logout():
    # Hapus session
    session.pop('username', None)
    flash('Anda telah logout!', 'info')
    return redirect(url_for('login_page'))


#----------- ADD & DELETE SERVER ------------
# Lokasi file server.json
SERVER_FILE = "server.json"

def load_servers():
    """Load servers from the JSON file. Jika file tidak ada, buat file baru dengan list kosong."""
    if not os.path.exists(SERVER_FILE):
        # Jika file tidak ada, buat file baru dengan list kosong
        with open(SERVER_FILE, "w") as file:
            json.dump([], file, indent=4)
        return []
    
    # Jika file ada, baca dan kembalikan datanya
    with open(SERVER_FILE, "r") as file:
        return json.load(file)

def save_servers(servers):
    """Save servers to the JSON file."""
    with open(SERVER_FILE, "w") as file:
        json.dump(servers, file, indent=4)

@app.route('/add_server_temp')
def add_server_temp():
    """Halaman Form untuk menambah server."""
    return render_template('add_server.html')

@app.route('/add_server', methods=['POST'])
def add_server():
    try:
        # Ambil data dari form
        name = request.form['name']
        hostname = request.form['hostname']
        username = request.form['username']
        password = request.form['password']

        # Validasi input (contoh: semua field harus diisi)
        if not all([name, hostname, username, password]):
            flash("Semua field harus diisi!", "error")
            return redirect(url_for('home'))

        # Buat data server baru
        new_server = {
            "name": name,
            "hostname": hostname,
            "username": username,
            "password": password
        }

        # Load server list dan tambahkan server baru
        servers = load_servers()
        servers.append(new_server)
        save_servers(servers)

        flash("Server berhasil ditambahkan!", "success")
        return redirect(url_for('add_server_temp'))

    except Exception as e:
        flash(f"Terjadi kesalahan: {e}", "error")
        return redirect(url_for('add_server_temp'))

@app.route('/delete_server', methods=['GET', 'POST'])
def delete_server():
    if request.method == 'GET':
        # Menampilkan daftar server
        servers = load_servers()
        return render_template('delete_server.html', servers=servers)

    elif request.method == 'POST':
        # Menghapus server berdasarkan nama
        name_to_delete = request.form['name']
        servers = load_servers()
        updated_servers = [server for server in servers if server['name'] != name_to_delete]

        if len(servers) == len(updated_servers):
            flash(f"Server dengan nama '{name_to_delete}' tidak ditemukan!", "error")
        else:
            save_servers(updated_servers)
            flash(f"Server '{name_to_delete}' berhasil dihapus!", "success")
        
        return redirect(url_for('delete_server'))


if __name__ == '__main__':
    create_table()
    app.run(host='0.0.0.0', port=5009)