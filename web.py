from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from firebase_admin import credentials, db
import firebase_admin
from firebase_admin import auth as firebase_auth
import os

# Make Flask look for templates in the current folder (where index.html & main.html are)
app = Flask(__name__, template_folder='.')
app.secret_key = os.urandom(24)
CORS(app)

# Firebase Admin SDK (server) configuration
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
    data = request.get_json() or {}
    id_token = data.get('idToken')
    if not id_token:
        return jsonify({'success': False, 'message': 'Missing idToken'}), 400
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        uid = decoded['uid']
        email = decoded.get('email', uid)
        session['uid'] = uid
        session['user'] = email
        return jsonify({'success': True, 'message': 'Login successful', 'redirect': '/main'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Auth failed: {e}'}), 401

# If you want a separate signup route, you can keep it, but
# the recommended flow is to just call /login with idToken after createUserWithEmailAndPassword.
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    id_token = data.get('idToken')
    if not id_token:
        return jsonify({'success': False, 'message': 'Missing idToken'}), 400
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        uid = decoded['uid']
        email = decoded.get('email', uid)
        session['uid'] = uid
        session['user'] = email
        return jsonify({'success': True, 'message': 'Sign up successful', 'redirect': '/main'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Auth failed: {e}'}), 401

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('uid', None)
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
        uid = session['uid']
        ref = db.reference(f"users/{uid}/food_detections")
        food_data = ref.get()
        if not food_data:
            return jsonify({'success': False, 'message': 'No data found'})
        return jsonify({'success': True, 'data': food_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    # Use debug only in development
    app.run(debug=True)
