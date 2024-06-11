from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import pickle
import numpy as np

app = Flask(__name__)
app.secret_key = 'xyzsdfg'

# Konfigurasi SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model untuk Tabel User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Model untuk Tabel KualitasAir
class KualitasAir(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ph = db.Column(db.Float, nullable=False)
    solids = db.Column(db.Float, nullable=False)
    conductivity = db.Column(db.Float, nullable=False)

# Route untuk halaman login
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    mesage = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form:
        name = request.form['name']
        password = request.form['password']
        
        # Cek apakah akun adalah akun pengguna biasa
        user = User.query.filter_by(nama=name, password=password).first()
        if user:
            session['loggedin'] = True
            session['userid'] = user.id
            session['name'] = user.nama
            mesage = 'Logged in successfully!'
            return render_template('user.html', mesage=mesage)

        mesage = 'Please enter correct name / password!'
    return render_template('login.html', mesage=mesage)

# Route untuk logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('name', None)
    return redirect(url_for('login'))

# Route untuk halaman registrasi
@app.route('/register', methods=['GET', 'POST'])
def register():
    mesage = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form:
        name = request.form['name']
        password = request.form['password']
        
        # Cek apakah nama pengguna sudah ada
        user_exists = User.query.filter_by(nama=name).first()
        if user_exists:
            mesage = 'User account already exists!'
        else:
            new_user = User(nama=name, password=password)
            db.session.add(new_user)
            db.session.commit()
            mesage = 'User account registered successfully!'
    elif request.method == 'POST':
        mesage = 'Please fill out the form!'
    return render_template('register.html', mesage=mesage)

# Muat model SVM dari file
with open('svm_model.pkl', 'rb') as model_file:
    svm_model = pickle.load(model_file)

# Route untuk halaman pengujian
@app.route('/testing', methods=['GET', 'POST'])
def testing():
    prediction_text = ''
    if request.method == 'POST':
        ph = request.form['ph']
        solids = request.form['solids']
        conductivity = request.form['conductivity']
        
        # Simpan data ke dalam basis data SQLite
        new_data = KualitasAir(ph=ph, solids=solids, conductivity=conductivity)
        db.session.add(new_data)
        db.session.commit()
        
        # Siapkan data untuk prediksi
        input_data = np.array([[ph, solids, conductivity]], dtype=float)
        
        # Lakukan prediksi dengan model SVM
        prediction = svm_model.predict(input_data)

        # Interpretasi hasil prediksi
        if prediction[0] == 1:
            prediction_result = "Air dapat diminum."
        else:
            prediction_result = "Air tidak dapat diminum."
        
        prediction_text = f"Prediksi: {prediction_result}"
    
    return render_template('testing.html', prediction_text=prediction_text)

# Route untuk halaman pengguna
@app.route('/user')
def user():
    if 'loggedin' in session and session['loggedin']:
        return render_template('user.html', name=session.get('name'))
    else:
        return redirect(url_for('login'))

if __name__ == "__main__":
    # Buat semua tabel
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
