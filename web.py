from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from firebase_admin import credentials, db, auth as firebase_auth
import os
import requests
import json
from datetime import datetime
import firebase_admin

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Firebase configuration
FIREBASE_DB_URL = "https://kahseng-9092f-default-rtdb.firebaseio.com"

cred = credentials.Certificate("serviceAccountKey.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        "databaseURL": FIREBASE_DB_URL
    })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/main')
def main():
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('main.html', user_email=session['user'])

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    id_token = data.get('idToken')   # frontend must send this

    try:
        decoded = firebase_auth.verify_id_token(id_token)
        uid = decoded['uid']
        email = decoded.get('email', uid)

        session['uid'] = uid
        session['user'] = email

        return jsonify({'success': True, 'message': 'Login successful', 'redirect': '/main'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    
@app.route('/signup', methods=['POST'])
def signup():
    # This endpoint would typically create a new user in Firebase
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirmPassword')
    
    # Basic validation
    if not email or not password or not confirm_password:
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'})
    
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'})
    
    # In a real implementation, you would create the user in Firebase here
    session['user'] = email
    return jsonify({'success': True, 'message': 'Sign up successful', 'redirect': '/main'})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/check_session')
def check_session():
    if 'user' in session:
        return jsonify({'logged_in': True, 'user': session['user']})
    return jsonify({'logged_in': False})

@app.route('/get_food_data')
def get_food_data():
    try:
        if 'uid' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        uid = session['uid']   # dynamic per user
        ref = db.reference(f"users/{uid}/food_detections")
        food_data = ref.get()

        if not food_data:
            return jsonify({'success': False, 'message': 'No data found'})

        return jsonify({'success': True, 'data': food_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    app.run(debug=True)