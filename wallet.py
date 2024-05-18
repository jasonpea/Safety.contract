from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib #hasing docs
import json #handle json data
from web3 import Web3 #interaction with Ethereum bc

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
    db.create_all()

@app.route('/')
def index():
    return 'Hello, Flask!'

# Connect to Ganache local Ethereum node
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

#road for user reg
@app.route('/register', methods = ['GET', 'POST'])
def register():
    data = request.get_json()  # Get the JSON data from  request
    hashed_password = generate_password_hash(data['password'], method = 'sha256')  # Hash the user password
    new_user = User(username = data['username'], password = hashed_password)  # Create a new User object
    db.session.add(new_user)  # Add new user to the session
    db.session.commit()  # Commit the session to save the user to the database
    return jsonify({'message': 'registered successfully'})  # Return a success message

# Route for user login
@app.route('/login', methods = ['GET', 'POST'])
def login():
    data = request.get_json()  # Get the JSON data from the request
    user = User.query.filter_by(username = data['username']).first()  # Query the database for the user
    if user and check_password_hash(user.password, data['password']):  # Check if user exists and password is correct
        return jsonify({'message': 'login successful'})  # Return a success message
    else:
        return jsonify({'message': 'invalid credentials'}), 401  # Return an error message if credentials are invalid
    
# Route for uploading documents
@app.route('/upload', methods = ['GET', 'POST'])
def upload():
    data = request.get_json()  # Get the JSON data from the request
    user = User.query.filter_by(username = data['username']).first()  # Query the database for the user
    if not user or not check_password_hash(user.password, data['password']):  # Check if user exists and password is correct
        return jsonify({'message': 'invalid credentials'}), 401  # Return an error message if credentials are invalid
    
    document = data['document']  # Get the document from the request
    doc_hash = hashlib.sha256(document.encode()).hexdigest()  # Hash the document using SHA-256

    # Store the document hash on the Ethereum blockchain
    tx_hash = w3.eth.send_transaction({
        'to': '0xRecipientAddress',  # Replace with actual recipient address
        'from': w3.eth.accounts[0],  # Use the first account from the local node
        'data': Web3.toBytes(text=doc_hash)  # Convert the document hash to bytes
    })
    
    # Store the document hash and transaction hash in the user's record
    user.documents = json.dumps({'hash': doc_hash, 'tx_hash': tx_hash.hex()})
    db.session.commit()  # Commit the session to save changes to the database
    
    return jsonify({'message': 'document uploaded and hash stored on blockchain'})  # Return success message

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    data = request.get_json()  # Get JSON data from the request
    user = User.query.filter_by(username=data['username']).first()  # Find user by username
    if not user or not check_password_hash(user.password, data['password']):  # Check if user exists and password is correct
        return jsonify({'message': 'invalid credentials'}), 401  # Return error message for invalid credentials
    
    stored_data = json.loads(user.documents)  # Load the stored document data from the user's record
    stored_hash = stored_data['hash']  # Get the stored document hash
    tx_hash = stored_data['tx_hash']  # Get the stored transaction hash
    
    tx = w3.eth.get_transaction(tx_hash)  # Retrieve the transaction from the blockchain using the transaction hash
    blockchain_hash = Web3.toText(tx.input)  # Extract the document hash from the transaction data
    
    # Compare the stored hash with the hash retrieved from the blockchain
    if stored_hash == blockchain_hash:
        return jsonify({'message': 'document verified successfully'})  # Return success message if hashes match
    else:
        return jsonify({'message': 'document verification failed'}), 400  # Return error message if hashes don't match
if __name__ == '__main__':
    app.run(debug = False)  # Start the Flask application in debug mode
    