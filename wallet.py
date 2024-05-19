from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib #hasing docs
from web3 import Web3 #interaction with Ethereum bc
import json
import logging
from solcx import compile_source
from web3.contract import ConciseContract

# Configure logging
logging.basicConfig(level = logging.DEBUG)

#init the app
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///walet.db'

#init the sqlite database
db = SQLAlchemy(app)

#defining user
class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)  # Primary key column
    username = db.Column(db.String(80), unique = True, nullable = False)  # Unique username column
    password = db.Column(db.String(200), nullable = False)  # Password column
    documents = db.Column(db.String(500), nullable = True)  # Column to store document hashes

#create data tables
def create_tables():
    with app.app_context():
        db.create_all()
@app.route('/')
def index():
    return 'Hello, Flask!'

# Connect to Ganache local Ethereum node
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

contract_source_code = '''
'''

compiled_sol = compile_source(contract_source_code)
contract_interface = compiled_sol['<stdin>:DocumentVerifier']

# Deploy the smart contract
contract_address = None  # Update with actual deployed contract address

# Define contract instance
contract_instance = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])

# Define contract functions
def store_document_hash(doc_hash):
    tx_hash = contract_instance.functions.storeDocumentHash(doc_hash).transact()
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    return receipt

def verify_document(doc_hash):
    return contract_instance.functions.verifyDocument(doc_hash).call()

#road for user reg
@app.route('/register', methods = ['GET', 'POST'])
def register():
    # logging.debug(f"Register data: {data}")
    if request.method() == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method = 'pbkdf2:sha256')  # Hash the user password
        new_user = User(username = username, password = hashed_password)  # Create a new User object
        db.session.add(new_user)  # Add new user to the session
        db.session.commit()  # Commit the session to save the user to the database
        return redirect(url_for('login'))  # Redirect to login page after successful registration
    return render_template('register.html')

# Route for user login
@app.route('/login', methods = ['GET', 'POST'])
def login():
    # logging.debug(f"Login data: {data}")
    if request.method() == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username = username).first()  # Query the database for the user
        if user and check_password_hash(user.password, password):  # Check if user exists and password is correct
            return redirect(url_for('index'))  # Redirect to homepage after successful login
        else:
            return render_template('login.html', message='Invalid credentials')   # Render login page with error message
    return render_template('login.html')

    
# Route for uploading documents
@app.route('/upload', methods = ['GET', 'POST'])
def upload():
    # logging.debug(f"Upload data: {data}")
    if request.method == 'POST':
        data = request.form  # Get form data
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username = username).first()    

        if not user or not check_password_hash(user.password, password):  # Check if user exists and password is correct
            return jsonify({'message': 'invalid credentials'}), 401  # Return an error message if credentials are invalid

        if 'document' not in request.files:
            return jsonify({'error': 'No document provided'}), 400
    
        document = request.files['document']
    
        if document.filename == '':
            return jsonify({'error': 'No selected document'}), 400
    
        doc_hash = hashlib.sha256(document.read()).hexdigest()  

        # Store the document hash on the Ethereum blockchain
        doc_hash = hashlib.sha256(document.read()).hexdigest()

        # Store the document hash on the blockchain
        store_document_hash(doc_hash)

        # Store the document hash and transaction hash in the user's record
        user.documents = json.dumps({'hash': doc_hash})
        db.session.commit()

        return jsonify({'message': 'document uploaded and hash stored on blockchain'})
    
    return render_template('upload.html')


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    # logging.debug(f"Verify data: {data}")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        doc_hash = request.form['doc_hash']
        user = User.query.filter_by(username = username).first()  # Find user by username
        
    if not user or not check_password_hash(user.password, password):  # Check if user exists and password is correct
        return jsonify({'message': 'invalid credentials'}), 401  # Return error message for invalid credentials
    
    is_verified = verify_document(doc_hash)

    if is_verified:
        return render_template('verify.html', message='Document verified successfully')
    else:
        return render_template('verify.html', message='Document verification failed')
if __name__ == '__main__':
    create_tables()
    app.run(debug = True) 
    