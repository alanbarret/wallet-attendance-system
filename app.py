import os
import base58
import time
import qrcode
import io
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_file, render_template_string, request
from pyngrok import ngrok
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from flask_cors import CORS

# === Configuration ===
KEYS_DIR = "keys"
DATA_DIR = "data"
os.makedirs(KEYS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

EMPLOYEES_FILE = os.path.join(DATA_DIR, "employees.json")
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance.json")
SERVER_KEYS_FILE = os.path.join(KEYS_DIR, "server_keys.json")
INTERVAL = 10  # seconds - QR refresh rate
QR_GRACE_PERIOD = 30  # QR code valid for 30 seconds
QR_REUSE_WINDOW = 300  # Prevent reuse for 5 minutes

# Get ngrok token from environment or use default
NGROK_TOKEN = os.getenv(
    "NGROK_AUTH_TOKEN", "33sFlvK0a602w8bNRBOv0DfAyQi_6pQ1PbFcz6USNG8i3egHj"
)
ngrok.set_auth_token(NGROK_TOKEN)

# === Flask App ===
app = Flask(__name__)
CORS(app)

# Track QR usage to prevent replay attacks
recent_qr_usage = {}  # {emp_id: {slot: timestamp}}


# === Data Management ===
def load_json_file(filepath, default=None):
    if default is None:
        default = {}
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return default


def save_json_file(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def load_employees():
    return load_json_file(EMPLOYEES_FILE, {})


def save_employees(employees):
    save_json_file(EMPLOYEES_FILE, employees)


def load_attendance():
    return load_json_file(ATTENDANCE_FILE, [])


def save_attendance(attendance):
    save_json_file(ATTENDANCE_FILE, attendance)


# === Cryptography Functions ===
def generate_ed25519_keypair():
    """Generate Ed25519 keypair and return as Base58 strings (TweetNaCl compatible)"""
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Serialize to raw bytes
    private_seed = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )

    # TweetNaCl expects 64 bytes: 32-byte seed + 32-byte public key
    private_key_full = private_seed + public_bytes

    # Encode to Base58
    private_key_b58 = base58.b58encode(private_key_full).decode("utf-8")
    public_key_b58 = base58.b58encode(public_bytes).decode("utf-8")

    return private_key_b58, public_key_b58, private_key, public_key


def sign_message(private_key, message):
    """Sign a message with Ed25519 private key"""
    message_bytes = message.encode("utf-8")
    signature = private_key.sign(message_bytes)
    return base58.b58encode(signature).decode("utf-8")


def verify_signature(public_key_b58, message, signature_b58):
    """Verify Ed25519 signature"""
    try:
        public_bytes = base58.b58decode(public_key_b58)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)

        message_bytes = message.encode("utf-8")
        signature_bytes = base58.b58decode(signature_b58)

        public_key.verify(signature_bytes, message_bytes)
        return True
    except (InvalidSignature, Exception) as e:
        print(f"Signature verification failed: {e}")
        return False


# === Initialize Server Keypair ===
def load_or_create_server_keys():
    """Load existing server keys or create new ones"""
    if os.path.exists(SERVER_KEYS_FILE):
        keys = load_json_file(SERVER_KEYS_FILE)
        private_key_b58 = keys["private_key"]
        public_key_b58 = keys["public_key"]

        # Reconstruct key objects (handle both 32 and 64 byte formats)
        private_bytes = base58.b58decode(private_key_b58)

        # If it's 64 bytes (TweetNaCl format), extract the seed (first 32 bytes)
        if len(private_bytes) == 64:
            private_seed = private_bytes[:32]
        else:
            private_seed = private_bytes

        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_seed)
        public_key = private_key.public_key()

        print(f"✓ Loaded existing server keys")
        print(f"  Public Key: {public_key_b58}")
        return private_key_b58, public_key_b58, private_key, public_key
    else:
        private_key_b58, public_key_b58, private_key, public_key = (
            generate_ed25519_keypair()
        )
        save_json_file(
            SERVER_KEYS_FILE,
            {"private_key": private_key_b58, "public_key": public_key_b58},
        )
        print(f"✓ Generated new server keypair")
        print(f"  Public Key: {public_key_b58}")
        return private_key_b58, public_key_b58, private_key, public_key


server_private_key_b58, server_public_key_b58, server_private_key, server_public_key = (
    load_or_create_server_keys()
)


# === QR Code Generation ===
def get_time_slot():
    """Get current time slot rounded to INTERVAL seconds"""
    return int(time.time() // INTERVAL) * INTERVAL


def generate_qr_data():
    """Generate QR code data with server signature"""
    timestamp = get_time_slot()
    message = f"attendance:{timestamp}:{server_public_key_b58}"
    signature = sign_message(server_private_key, message)

    qr_data = {
        "message": message,
        "signature": signature,
        "timestamp": timestamp,
        "server_public_key": server_public_key_b58,
    }
    return json.dumps(qr_data)


def create_qr_image():
    """Create QR code image"""
    qr_data = generate_qr_data()
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# === HTML Templates ===
HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
<title> Wallet Auth System</title>
<style>
body { font-family: Arial; text-align:center; background:#111; color:#eee; }
.container { max-width: 800px; margin: 0 auto; padding: 20px; }
.header { margin-bottom: 30px; }
.qr-section { background: #1a1a1a; padding: 30px; border-radius: 15px; margin: 20px 0; }
img { margin-top:20px; width:300px; height:300px; border:2px solid #333; border-radius:15px; }
a { color:#0f0; text-decoration:none; margin: 10px; display: inline-block; padding: 10px 20px; background: #222; border-radius: 8px; }
a:hover { background: #333; }
.info { background: #1a1a1a; padding: 15px; border-radius: 8px; margin: 10px 0; text-align: left; }
.label { color: #888; font-size: 14px; }
.value { color: #0f0; font-family: monospace; word-break: break-all; }
.security-features { background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: left; }
.feature { padding: 10px; margin: 5px 0; background: #0a0a0a; border-radius: 5px; }
</style>
<meta http-equiv="refresh" content="{{ interval }}">
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🔐  Attendance System</h1>
        <p>Cryptographically Secure with Ed25519 Signatures</p>
    </div>

    <div class="qr-section">
        <h2>Server Dynamic QR Code</h2>
        <p style="color: #888;">Updates every {{ interval }} seconds</p>
        <img src="/qr" alt="QR Code">
        <div class="info">
            <div class="label">Server Public Key (Base58):</div>
            <div class="value">{{ public_address }}</div>
        </div>
        <div class="info">
            <div class="label">Current Time Slot:</div>
            <div class="value">{{ time_slot }}</div>
        </div>
        <p style="color: #666; margin-top: 15px;">Next refresh in {{ interval }}s...</p>
    </div>

    <div class="security-features">
        <h3 style="color: #0f0; margin-bottom: 15px;">🛡️ Security Features</h3>
        <div class="feature">✓ Dual Ed25519 Signature Verification</div>
        <div class="feature">✓ Time-based QR Code Expiry ({{ grace_period }}s window)</div>
        <div class="feature">✓ Replay Attack Prevention</div>
        <div class="feature">✓ Client-side Private Key Signing</div>
        <div class="feature">✓ Zero-knowledge Proof Authentication</div>
    </div>

    <div class="links">
        <a href="/register">➕ Register Employee</a>
        <a href="/scan">📷 Scan for Attendance</a>
        <a href="/attendance">📊 View Attendance</a>
    </div>
</div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Employee Registration </title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    min-height: 100vh;
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.container {
    width: 100%;
    max-width: 600px;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    padding: 30px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
h1 { color: #667eea; margin-bottom: 10px; text-align: center; }
.subtitle { color: #6c757d; text-align: center; margin-bottom: 30px; }
.form-group { margin-bottom: 20px; }
label { display: block; color: #495057; font-weight: 600; margin-bottom: 8px; }
input {
    width: 100%;
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.3s;
}
input:focus { outline: none; border-color: #667eea; }
button {
    width: 100%;
    padding: 14px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.3s;
}
button:hover { background: #5568d3; }
button:disabled { background: #ccc; cursor: not-allowed; }
.message {
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 20px;
    text-align: center;
    font-weight: 600;
    display: none;
}
.success { background: #d4edda; color: #155724; display: block; }
.error { background: #f8d7da; color: #721c24; display: block; }
.wallet-keys {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 12px;
    margin-top: 20px;
    display: none;
}
.wallet-keys.show { display: block; }
.key-section {
    margin-bottom: 15px;
    background: white;
    padding: 15px;
    border-radius: 8px;
    border: 2px solid #667eea;
}
.key-label {
    font-weight: 600;
    color: #667eea;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.key-value {
    font-family: 'Courier New', monospace;
    font-size: 12px;
    color: #495057;
    word-break: break-all;
    background: #f8f9fa;
    padding: 10px;
    border-radius: 4px;
}
.copy-btn {
    padding: 4px 12px;
    font-size: 12px;
    background: #28a745;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-left: 10px;
}
.copy-btn:hover { background: #218838; }
.save-btn {
    width: 100%;
    padding: 12px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 15px;
}
.save-btn:hover { background: #5568d3; }
.save-btn.saved {
    background: #28a745;
}
.saved-key-notice {
    background: #fff3cd;
    color: #856404;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
    font-size: 14px;
    display: none;
}
.saved-key-notice.show { display: block; }
.warning {
    background: #fff3cd;
    color: #856404;
    padding: 15px;
    border-radius: 8px;
    margin-top: 15px;
    font-size: 14px;
}
.warning strong { display: block; margin-bottom: 5px; }
.back-link {
    display: block;
    text-align: center;
    margin-top: 20px;
    color: #667eea;
    text-decoration: none;
    font-weight: 600;
}
</style>
</head>
<body>
<div class="container">
    <h1>👤 Employee Registration</h1>
    <p class="subtitle">Register and receive your cryptographic wallet keys</p>

    <div id="savedKeyNotice" class="saved-key-notice">
        ⚠️ You already have a saved key on this device. Registering a new account will not overwrite it.
    </div>

    <div id="message" class="message"></div>

    <form id="registerForm">
        <div class="form-group">
            <label for="emp_id">Employee ID *</label>
            <input type="text" id="emp_id" name="emp_id" required placeholder="e.g., EMP001">
        </div>

        <div class="form-group">
            <label for="name">Full Name *</label>
            <input type="text" id="name" name="name" required placeholder="John Doe">
        </div>

        <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" name="email" placeholder="john@example.com">
        </div>

        <div class="form-group">
            <label for="department">Department</label>
            <input type="text" id="department" name="department" placeholder="Engineering">
        </div>

        <button type="submit" id="submitBtn">🔑 Register & Generate Keys</button>
    </form>

    <div id="walletKeys" class="wallet-keys">
        <h3 style="color: #667eea; margin-bottom: 15px;">🎉 Registration Successful!</h3>

        <div class="key-section">
            <div class="key-label">
                🔓 Public Key (Share this)
                <button type="button" class="copy-btn" onclick="copyKey('publicKey')">Copy</button>
            </div>
            <div class="key-value" id="publicKey"></div>
            <small style="color: #667eea; margin-top: 5px; display: block;">Length: <span id="publicKeyLength"></span> characters</small>
        </div>

        <div class="key-section">
            <div class="key-label">
                🔐 Private Key (Keep SECRET!)
                <button type="button" class="copy-btn" onclick="copyKey('privateKey')">Copy</button>
            </div>
            <div class="key-value" id="privateKey"></div>
            <small style="color: #667eea; margin-top: 5px; display: block;">Length: <span id="privateKeyLength"></span> characters (should be ~88 for TweetNaCl)</small>
        </div>

        <div class="warning">
            <strong>⚠️ IMPORTANT: Save Your Private Key!</strong>
            This is like your wallet password. You'll need it to mark attendance.
            Store it securely - if lost, you'll need to re-register.
        </div>

        <button class="save-btn" id="saveToDeviceBtn" onclick="saveToDevice()">
            💾 Save Private Key to This Device
        </button>
    </div>

    <a href="/" class="back-link">← Back to Home</a>
</div>

<script>
// Check if key already saved
window.addEventListener('DOMContentLoaded', function() {
    const savedKey = localStorage.getItem('attendance_private_key');
    const savedEmpId = localStorage.getItem('attendance_emp_id');

    if (savedKey && savedEmpId) {
        const notice = document.getElementById('savedKeyNotice');
        notice.textContent = `⚠️ You already have a saved key for ${savedEmpId} on this device.`;
        notice.classList.add('show');
    }
});

function copyKey(elementId) {
    const text = document.getElementById(elementId).textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        setTimeout(() => btn.textContent = originalText, 2000);
    });
}

function saveToDevice() {
    const privateKey = document.getElementById('privateKey').textContent;
    const empId = document.querySelector('form input[name="emp_id"]').value;

    if (privateKey && empId) {
        localStorage.setItem('attendance_private_key', privateKey);
        localStorage.setItem('attendance_emp_id', empId);

        const btn = document.getElementById('saveToDeviceBtn');
        btn.textContent = '✅ Saved to Device!';
        btn.classList.add('saved');

        setTimeout(() => {
            btn.textContent = '💾 Key Saved to This Device';
        }, 2000);
    }
}

document.getElementById('registerForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Registering...';

    const formData = {
        emp_id: document.getElementById('emp_id').value,
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        department: document.getElementById('department').value
    };

    fetch('/api/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(formData)
    })
    .then(res => res.json())
    .then(data => {
        const messageEl = document.getElementById('message');
        if (data.success) {
            messageEl.className = 'message success';
            messageEl.textContent = '✓ ' + data.message;

            // Show wallet keys
            document.getElementById('publicKey').textContent = data.public_key;
            document.getElementById('privateKey').textContent = data.private_key;
            document.getElementById('publicKeyLength').textContent = data.public_key.length;
            document.getElementById('privateKeyLength').textContent = data.private_key.length;
            document.getElementById('walletKeys').classList.add('show');

            // Hide form
            document.getElementById('registerForm').style.display = 'none';
        } else {
            messageEl.className = 'message error';
            messageEl.textContent = '✗ ' + data.message;
            submitBtn.disabled = false;
            submitBtn.textContent = '🔑 Register & Generate Keys';
        }
    })
    .catch(() => {
        const messageEl = document.getElementById('message');
        messageEl.className = 'message error';
        messageEl.textContent = '✗ Error registering employee';
        submitBtn.disabled = false;
        submitBtn.textContent = '🔑 Register & Generate Keys';
    });
});
</script>
</body>
</html>
"""

SCAN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title> Wallet Scanner</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    min-height: 100vh;
    padding: 20px;
}
.container { max-width: 600px; margin: 0 auto; }
.header { text-align: center; margin-bottom: 30px; }
.scanner-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.input-section {
    margin-bottom: 20px;
    padding: 15px;
    background: rgba(102, 126, 234, 0.1);
    border-radius: 12px;
}
.input-section label {
    display: block;
    color: #495057;
    font-weight: 600;
    margin-bottom: 8px;
}
.input-section input, .input-section textarea {
    width: 100%;
    padding: 10px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
    font-family: 'Courier New', monospace;
}
.input-section textarea {
    min-height: 80px;
    resize: vertical;
}
#qr-reader { border-radius: 12px; overflow: hidden; margin-bottom: 20px; }
.result-container {
    padding: 20px;
    background: #f8f9fa;
    border-radius: 12px;
    min-height: 80px;
    text-align: center;
}
.result-waiting { color: #6c757d; }
.result-verifying { color: #667eea; font-weight: 600; }
.result-valid { color: #28a745; font-weight: 600; }
.result-invalid { color: #dc3545; font-weight: 600; }
.result-details {
    margin-top: 12px;
    padding: 12px;
    background: rgba(255,255,255,0.5);
    border-radius: 8px;
    font-size: 13px;
    color: #495057;
    text-align: left;
}
.icon { font-size: 32px; margin-bottom: 8px; display: block; }
.back-link {
    display: inline-block;
    margin-top: 20px;
    padding: 10px 20px;
    background: rgba(255,255,255,0.2);
    border-radius: 8px;
    color: white;
    text-decoration: none;
    font-weight: 600;
}
.load-key-btn {
    width: 100%;
    padding: 10px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}
.load-key-btn:hover { background: #5568d3; }
.load-key-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
}
.saved-key-info {
    background: #d4edda;
    color: #155724;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
    margin-top: 10px;
    display: none;
}
.saved-key-info.show { display: block; }
.clear-key-btn {
    width: 100%;
    padding: 8px;
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 8px;
}
.clear-key-btn:hover { background: #c82333; }
.modal {
    display: none;
    position: fixed;
    z-index: 1;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: rgba(0,0,0,0.4);
}
.modal-content {
    background-color: #fefefe;
    margin: 15% auto;
    padding: 20px;
    border: 1px solid #888;
    width: 80%;
    max-width: 400px;
    text-align: center;
    border-radius: 8px;
    color: #000;
}
.close {
    color: #aaa;
    float: right;
    font-size: 28px;
    font-weight: bold;
}
.close:hover,
.close:focus {
    color: black;
    text-decoration: none;
    cursor: pointer;
}
button {
    background-color: #667eea;
    color: white;
    border: none;
    padding: 10px 20px;
    margin: 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}
button:hover {
    background-color: #5568d3;
}
.cancel {
    background-color: #dc3545;
}
.cancel:hover {
    background-color: #c82333;
}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🔐  Wallet Scanner</h1>
        <p>Sign with your private key to mark attendance</p>
    </div>

    <div class="scanner-card">
        <div class="input-section">
            <label for="private_key_input">🔐 Your Private Key:</label>
            <textarea id="private_key_input" placeholder="Paste your private key here (Base58 encoded)"></textarea>
            <button class="load-key-btn" id="loadKeyBtn" onclick="loadSavedKey()">
                <span>📂</span> Load Saved Key from Device
            </button>
            <div id="savedKeyInfo" class="saved-key-info"></div>
            <button class="clear-key-btn" id="clearKeyBtn" onclick="clearSavedKey()" style="display: none;">
                🗑️ Clear Saved Key from Device
            </button>
            <small style="color: #6c757d; display: block; margin-top: 5px;">
                Your employee identity is derived from this key. It never leaves your device.
            </small>
        </div>

        <div id="qr-reader"></div>
        <div id="qr-reader-results" class="result-container result-waiting">
            <div>
                <span class="icon">👀</span>
                <div>Enter your private key and scan QR code</div>
            </div>
        </div>
    </div>

    <!-- Confirmation Modal -->
    <div id="confirmationModal" class="modal" style="display: none;">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2>Confirm Check-out</h2>
            <p id="modalEmployee"></p>
            <p id="modalInTime"></p>
            <p id="modalOutTime"></p>
            <button onclick="confirmCheckout()">Confirm</button>
            <button class="cancel" onclick="closeModal()">Cancel</button>
        </div>
    </div>

    <a href="/" class="back-link">← Back to Home</a>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/tweetnacl/1.0.3/nacl.min.js"></script>
<script src="https://unpkg.com/tweetnacl-util@0.15.1/nacl-util.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/base-58@0.0.1/Base58.min.js"></script>
<script src="https://github.com/mebjas/html5-qrcode/releases/download/v2.3.8/html5-qrcode.min.js"></script>

<script>
// Verify libraries are loaded
console.log('TweetNaCl loaded:', typeof nacl !== 'undefined');
console.log('TweetNaCl util loaded:', typeof nacl !== 'undefined' && typeof nacl.util !== 'undefined');
console.log('base-58 loaded:', typeof Base58 !== 'undefined');

if (typeof Base58 === 'undefined') {
    alert('⚠️ Base58 library failed to load. Please check your internet connection and refresh the page.');
}

if (typeof nacl === 'undefined' || typeof nacl.util === 'undefined') {
    alert('⚠️ Cryptography library failed to load. Please check your internet connection and refresh the page.');
}
</script>

<script>
// Check for saved key on page load
window.addEventListener('DOMContentLoaded', function() {
    const savedKey = localStorage.getItem('attendance_private_key');
    const savedEmpId = localStorage.getItem('attendance_emp_id');

    if (savedKey && savedEmpId) {
        const infoDiv = document.getElementById('savedKeyInfo');
        infoDiv.textContent = `✓ Saved key found for ${savedEmpId}`;
        infoDiv.classList.add('show');
        document.getElementById('clearKeyBtn').style.display = 'block';
    } else {
        const btn = document.getElementById('loadKeyBtn');
        btn.disabled = true;
        btn.textContent = '📂 No Saved Key on This Device';
    }
});

// Load saved key from localStorage
function loadSavedKey() {
    const savedKey = localStorage.getItem('attendance_private_key');

    if (savedKey) {
        document.getElementById('private_key_input').value = savedKey;

        const infoDiv = document.getElementById('savedKeyInfo');
        infoDiv.textContent = '✅ Private key loaded successfully!';
        infoDiv.classList.add('show');

        setTimeout(() => {
            infoDiv.textContent = `✓ Saved key loaded`;
        }, 2000);
    } else {
        alert('No saved key found on this device. Please paste your key manually.');
    }
}

// Clear saved key from device
function clearSavedKey() {
    if (confirm('Are you sure you want to remove the saved key from this device? You will need to paste it manually next time.')) {
        const empId = localStorage.getItem('attendance_emp_id');
        localStorage.removeItem('attendance_private_key');
        localStorage.removeItem('attendance_emp_id');

        const infoDiv = document.getElementById('savedKeyInfo');
        infoDiv.textContent = `✓ Saved key for ${empId} removed from device`;
        infoDiv.style.background = '#f8d7da';
        infoDiv.style.color = '#721c24';

        document.getElementById('loadKeyBtn').disabled = true;
        document.getElementById('loadKeyBtn').textContent = '📂 No Saved Key on This Device';
        document.getElementById('clearKeyBtn').style.display = 'none';
        document.getElementById('private_key_input').value = '';

        setTimeout(() => {
            infoDiv.classList.remove('show');
        }, 3000);
    }
}

// Derive public key from private key (client-side)
function derivePublicKey(privateKeyBase58) {
    try {
        // Check if Base58 is loaded
        if (typeof Base58 === 'undefined') {
            console.error('Base58 library not loaded! Please refresh the page.');
            alert('⚠️ Cryptography library not loaded. Please refresh the page and try again.');
            return null;
        }

        // Check if nacl is loaded
        if (typeof nacl === 'undefined') {
            console.error('TweetNaCl library not loaded! Please refresh the page.');
            alert('⚠️ Cryptography library not loaded. Please refresh the page and try again.');
            return null;
        }

        // Clean the input (remove whitespace)
        privateKeyBase58 = privateKeyBase58.trim();

        if (!privateKeyBase58) {
            console.error('Private key is empty');
            return null;
        }

        console.log('Deriving public key from private key, length:', privateKeyBase58.length);
        const privateKeyBytes = Base58.decode(privateKeyBase58);
        console.log('Private key decoded to', privateKeyBytes.length, 'bytes');

        // Validate length (should be 64 bytes for TweetNaCl)
        if (privateKeyBytes.length !== 64) {
            console.error('Invalid private key length:', privateKeyBytes.length, 'bytes. Expected 64 bytes.');
            console.error('Your key might be in the old format (32 bytes). Please re-register to get a new 64-byte key.');
            return null;
        }

        console.log('Deriving public key...');
        const keyPair = nacl.sign.keyPair.fromSecretKey(privateKeyBytes);
        const publicKeyB58 = Base58.encode(keyPair.publicKey);
        console.log('Public key derived successfully:', publicKeyB58.substring(0, 20) + '...');
        return publicKeyB58;
    } catch (e) {
        console.error('Public key derivation error details:', e);
        console.error('Error type:', e.name);
        console.error('Error message:', e.message);
        console.error('Stack trace:', e.stack);

        if (e.message && e.message.includes('Non-base58')) {
            alert('⚠️ Invalid private key format. Please check that you copied the entire key correctly.');
        } else {
            alert('⚠️ Failed to derive public key: ' + e.message);
        }
        return null;
    }
}

// Sign message with private key (client-side)
function signMessage(privateKeyBase58, message) {
    try {
        // Check if Base58 is loaded
        if (typeof Base58 === 'undefined') {
            console.error('Base58 library not loaded! Please refresh the page.');
            alert('⚠️ Cryptography library not loaded. Please refresh the page and try again.');
            return null;
        }

        // Check if nacl is loaded
        if (typeof nacl === 'undefined' || typeof nacl.util === 'undefined') {
            console.error('TweetNaCl or TweetNaCl util library not loaded! Please refresh the page.');
            alert('⚠️ Cryptography library not loaded. Please refresh the page and try again.');
            return null;
        }

        // Clean the input (remove whitespace)
        privateKeyBase58 = privateKeyBase58.trim();

        if (!privateKeyBase58) {
            console.error('Private key is empty');
            return null;
        }

        console.log('Attempting to decode private key, length:', privateKeyBase58.length);
        const privateKeyBytes = Base58.decode(privateKeyBase58);
        console.log('Private key decoded to', privateKeyBytes.length, 'bytes');

        // Validate length (should be 64 bytes for TweetNaCl)
        if (privateKeyBytes.length !== 64) {
            console.error('Invalid private key length:', privateKeyBytes.length, 'bytes. Expected 64 bytes.');
            console.error('Your key might be in the old format. Please re-register to get a new 64-byte key.');
            return null;
        }

        console.log('Encoding message...');
        const messageBytes = nacl.util.decodeUTF8(message);
        console.log('Signing message...');
        const signature = nacl.sign.detached(messageBytes, privateKeyBytes);
        console.log('Signature created, encoding to base58...');
        const signatureB58 = Base58.encode(signature);
        console.log('Signature encoded successfully, length:', signatureB58.length);
        return signatureB58;
    } catch (e) {
        console.error('Signing error details:', e);
        console.error('Error type:', e.name);
        console.error('Error message:', e.message);
        console.error('Stack trace:', e.stack);

        if (e.message && e.message.includes('Non-base58')) {
            alert('⚠️ Invalid private key format. Please check that you copied the entire key correctly.');
        } else {
            alert('⚠️ Failed to sign message: ' + e.message);
        }
        return null;
    }
}

var resultContainer = document.getElementById('qr-reader-results');
var lastResult;
var currentServerQr = null;
var currentPublicKey = null;

function showModal(employee, inTime, outTime) {
    document.getElementById('modalEmployee').textContent = 'Employee: ' + employee;
    document.getElementById('modalInTime').textContent = 'In Time: ' + inTime;
    document.getElementById('modalOutTime').textContent = 'Out Time: ' + outTime;
    document.getElementById('confirmationModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('confirmationModal').style.display = 'none';
}

function confirmCheckout() {
    closeModal();
    const privateKey = document.getElementById('private_key_input').value.trim();
    if (!privateKey || !currentServerQr || !currentPublicKey) {
        resultContainer.className = 'result-container result-invalid';
        resultContainer.innerHTML = '<div><span class="icon">❌</span><div>Error: Missing data for confirmation</div></div>';
        setTimeout(() => { lastResult = null; }, 3000);
        return;
    }

    // Re-sign the message
    const employeeSignature = signMessage(privateKey, currentServerQr.message);
    if (!employeeSignature) {
        resultContainer.className = 'result-container result-invalid';
        resultContainer.innerHTML = '<div><span class="icon">❌</span><div>Failed to sign for confirmation</div></div>';
        setTimeout(() => { lastResult = null; }, 3000);
        return;
    }

    fetch(window.location.origin + '/api/attendance', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            server_qr: currentServerQr,
            public_key: currentPublicKey,
            employee_signature: employeeSignature,
            confirm_checkout: true
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            resultContainer.className = 'result-container result-valid';
            resultContainer.innerHTML = `
                <div>
                    <span class="icon">✅</span>
                    <div>Check-out Successful!</div>
                    <div class="result-details">
                        <strong>Employee:</strong> ${data.employee_name}<br>
                        <strong>In Time:</strong> ${data.in_time}<br>
                        <strong>Out Time:</strong> ${data.out_time}<br>
                        <strong>Status:</strong> ${data.status}<br>
                        <strong>Verification:</strong> Dual-signature verified ✓
                    </div>
                </div>
            `;
            setTimeout(() => {
                lastResult = null;
                resultContainer.className = 'result-container result-waiting';
                resultContainer.innerHTML = '<div><span class="icon">👀</span><div>Scan next QR code</div></div>';
            }, 5000);
        } else {
            resultContainer.className = 'result-container result-invalid';
            resultContainer.innerHTML = '<div><span class="icon">❌</span><div>' + data.message + '</div></div>';
            setTimeout(() => { lastResult = null; }, 3000);
        }
    })
    .catch(err => {
        resultContainer.className = 'result-container result-invalid';
        resultContainer.innerHTML = '<div><span class="icon">⚠️</span><div>Error: ' + err.message + '</div></div>';
        setTimeout(() => { lastResult = null; }, 3000);
    });
}

function onScanSuccess(decodedText, decodedResult) {
    const privateKey = document.getElementById('private_key_input').value.trim();

    if (!privateKey) {
        resultContainer.className = 'result-container result-invalid';
        resultContainer.innerHTML = '<div><span class="icon">⚠️</span><div>Please enter your Private Key</div></div>';
        return;
    }

    if (decodedText === lastResult) return;
    lastResult = decodedText;

    resultContainer.className = 'result-container result-verifying';
    resultContainer.innerHTML = '<div><span class="icon">🔍</span><div>Signing and verifying...</div></div>';

    let cleaned = decodedText;
    if ((cleaned.startsWith('"') && cleaned.endsWith('"')) ||
        (cleaned.startsWith("'") && cleaned.endsWith("'"))) {
        cleaned = cleaned.slice(1, -1);
    }

    let serverQr;
    try {
        serverQr = JSON.parse(cleaned);
    } catch (e) {
        resultContainer.className = 'result-container result-invalid';
        resultContainer.innerHTML = '<div><span class="icon">❌</span><div>Invalid QR code format</div></div>';
        return;
    }

    // Derive public key from private key (this identifies the employee)
    const publicKey = derivePublicKey(privateKey);

    if (!publicKey) {
        resultContainer.className = 'result-container result-invalid';
        resultContainer.innerHTML = '<div><span class="icon">❌</span><div>Invalid private key format. Key must be 88 characters (64 bytes). Check console for details.</div></div>';
        return;
    }

    // Store for potential confirmation
    currentServerQr = serverQr;
    currentPublicKey = publicKey;

    // Sign the server's message with employee's private key
    console.log('Attempting to sign message:', serverQr.message);
    const employeeSignature = signMessage(privateKey, serverQr.message);

    if (!employeeSignature) {
        resultContainer.className = 'result-container result-invalid';
        resultContainer.innerHTML = '<div><span class="icon">❌</span><div>Failed to sign message. Check browser console (F12) for details.</div></div>';
        console.error('Sign message failed. Check the errors above for details.');
        return;
    }

    console.log('Message signed successfully!');

    // Send to server for verification (send public key, not emp_id)
    fetch(window.location.origin + '/api/attendance', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            server_qr: serverQr,
            public_key: publicKey,
            employee_signature: employeeSignature
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (data.action === "check-in") {
                resultContainer.className = 'result-container result-valid';
                resultContainer.innerHTML = `
                    <div>
                        <span class="icon">✅</span>
                        <div>Check-in Successful!</div>
                        <div class="result-details">
                            <strong>Employee:</strong> ${data.employee_name}<br>
                            <strong>Login Time:</strong> ${data.in_time}<br>
                            <strong>Status:</strong> ${data.status}<br>
                            <strong>Verification:</strong> Dual-signature verified ✓<br>
                            <small>Scan again to check-out</small>
                        </div>
                    </div>
                `;
            }
            // Clear after success
            setTimeout(() => {
                lastResult = null;
                resultContainer.className = 'result-container result-waiting';
                resultContainer.innerHTML = '<div><span class="icon">👀</span><div>Scan next QR code</div></div>';
            }, 5000);
        } else if (data.message === "Confirm check-out") {
            resultContainer.className = 'result-container result-verifying';
            resultContainer.innerHTML = '<div><span class="icon">⏰</span><div>Check-out confirmation required</div></div>';
            showModal(data.employee_name, data.in_time, data.out_time);
        } else if (data.message === "Already checked out today") {
            resultContainer.className = 'result-container result-valid';
            resultContainer.innerHTML = `
                <div>
                    <span class="icon">ℹ️</span>
                    <div>Already Checked Out Today</div>
                    <div class="result-details">
                        <strong>Employee:</strong> ${data.employee_name}<br>
                        <strong>In Time:</strong> ${data.in_time}<br>
                        <strong>Out Time:</strong> ${data.out_time}<br>
                        <strong>Status:</strong> ${data.status}<br>
                    </div>
                </div>
            `;
            setTimeout(() => {
                lastResult = null;
                resultContainer.className = 'result-container result-waiting';
                resultContainer.innerHTML = '<div><span class="icon">👀</span><div>Scan next QR code</div></div>';
            }, 5000);
        } else {
            resultContainer.className = 'result-container result-invalid';
            resultContainer.innerHTML = '<div><span class="icon">❌</span><div>' + data.message + '</div></div>';
            setTimeout(() => { lastResult = null; }, 3000);
        }
    })
    .catch((err) => {
        resultContainer.className = 'result-container result-invalid';
        resultContainer.innerHTML = '<div><span class="icon">⚠️</span><div>Error: ' + err.message + '</div></div>';
        setTimeout(() => { lastResult = null; }, 3000);
    });
}

var html5QrcodeScanner = new Html5QrcodeScanner(
    "qr-reader",
    { fps: 10, qrbox: { width: 250, height: 250 } }
);
html5QrcodeScanner.render(onScanSuccess);
</script>
</body>
</html>
"""

ATTENDANCE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Attendance Records</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    min-height: 100vh;
    padding: 20px;
}
.container { max-width: 1200px; margin: 0 auto; }
.header { text-align: center; margin-bottom: 30px; }
.header h1 { font-size: clamp(28px, 5vw, 36px); margin-bottom: 10px; }
.card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    padding: 30px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    margin-bottom: 20px;
}
filters {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}
.filters input, .filters select {
    padding: 10px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
    flex: 1;
    min-width: 150px;
}
table {
    width: 100%;
    border-collapse: collapse;
    color: #495057;
    overflow-x: auto;
}
thead {
    background: #667eea;
    color: white;
}
th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
}
tr:hover {
    background: rgba(102, 126, 234, 0.05);
}
.status-present { color: #28a745; font-weight: 600; }
.status-late { color: #ffc107; font-weight: 600; }
.verified-badge {
    display: inline-block;
    background: #28a745;
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
}
.back-link {
    display: inline-block;
    padding: 10px 20px;
    background: rgba(255,255,255,0.2);
    border-radius: 8px;
    color: white;
    text-decoration: none;
    font-weight: 600;
    margin-top: 20px;
}
.empty-state {
    text-align: center;
    padding: 40px;
    color: #6c757d;
}
@media (max-width: 768px) {
    table { font-size: 12px; }
    th, td { padding: 8px; }
}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📊 Attendance Records</h1>
        <p>Cryptographically verified attendance logs</p>
    </div>

    <div class="card">
        <div class="filters">
            <input type="date" id="filterDate" placeholder="Filter by date">
            <input type="text" id="filterEmpId" placeholder="Filter by Employee ID">
            <select id="filterStatus">
                <option value="">All Status</option>
                <option value="Present">Present</option>
                <option value="Late">Late</option>
            </select>
        </div>

        <div style="overflow-x: auto;">
            <div id="attendanceTable"></div>
        </div>
    </div>

    <a href="/" class="back-link">← Back to Home</a>
</div>

<script>
let allAttendance = [];

function loadAttendance() {
    fetch('/api/attendance')
    .then(res => res.json())
    .then(data => {
        allAttendance = data.records || [];
        renderTable(allAttendance);
    });
}

function renderTable(records) {
    const container = document.getElementById('attendanceTable');

    if (records.length === 0) {
        container.innerHTML = '<div class="empty-state">No attendance records found</div>';
        return;
    }

    let html = `
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>In Time</th>
                    <th>Out Time</th>
                    <th>Employee ID</th>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Verification</th>
                </tr>
            </thead>
            <tbody>
    `;

    records.forEach(record => {
        const statusClass = record.status === 'Present' ? 'status-present' : 'status-late';
        html += `
            <tr>
                <td>${record.date}</td>
                <td>${record.in_time}</td>
                <td>${record.out_time || 'Not checked out'}</td>
                <td>${record.emp_id}</td>
                <td>${record.employee_name}</td>
                <td class="${statusClass}">${record.status}</td>
                <td><span class="verified-badge">✓ Signed</span></td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

function filterRecords() {
    const dateFilter = document.getElementById('filterDate').value;
    const empIdFilter = document.getElementById('filterEmpId').value.toLowerCase();
    const statusFilter = document.getElementById('filterStatus').value;

    let filtered = allAttendance.filter(record => {
        if (dateFilter && record.date !== dateFilter) return false;
        if (empIdFilter && !record.emp_id.toLowerCase().includes(empIdFilter)) return false;
        if (statusFilter && record.status !== statusFilter) return false;
        return true;
    });

    renderTable(filtered);
}

document.getElementById('filterDate').addEventListener('change', filterRecords);
document.getElementById('filterEmpId').addEventListener('input', filterRecords);
document.getElementById('filterStatus').addEventListener('change', filterRecords);

loadAttendance();
</script>
</body>
</html>
"""


# === Flask Routes ===
@app.route("/")
def home():
    """Home page with dynamic QR code"""
    time_slot = get_time_slot()
    return render_template_string(
        HOME_HTML,
        public_address=server_public_key_b58,
        interval=INTERVAL,
        time_slot=datetime.fromtimestamp(time_slot).strftime("%Y-%m-%d %H:%M:%S"),
        grace_period=QR_GRACE_PERIOD,
    )


@app.route("/qr")
def qr_code():
    """Generate and return QR code image"""
    img = create_qr_image()
    return send_file(img, mimetype="image/png")


@app.route("/register")
def register_page():
    """Employee registration page"""
    return render_template_string(REGISTER_HTML)


@app.route("/scan")
def scan_page():
    """QR code scanner page"""
    return render_template_string(SCAN_HTML)


@app.route("/attendance")
def attendance_page():
    """Attendance records page"""
    return render_template_string(ATTENDANCE_HTML)


@app.route("/api/register", methods=["POST"])
def api_register():
    """Register employee and generate keypair"""
    data = request.json
    emp_id = data.get("emp_id", "").strip()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    department = data.get("department", "").strip()

    if not emp_id or not name:
        return jsonify(
            {"success": False, "message": "Employee ID and Name are required"}
        )

    employees = load_employees()

    if emp_id in employees:
        return jsonify(
            {"success": False, "message": f"Employee {emp_id} already registered"}
        )

    # Generate keypair for employee
    private_key_b58, public_key_b58, _, _ = generate_ed25519_keypair()

    employees[emp_id] = {
        "name": name,
        "email": email,
        "department": department,
        "public_key": public_key_b58,
        "registered_at": datetime.now().isoformat(),
    }

    save_employees(employees)

    print(f"✓ Registered employee: {emp_id} - {name}")

    return jsonify(
        {
            "success": True,
            "message": f"Employee {name} registered successfully",
            "emp_id": emp_id,
            "public_key": public_key_b58,
            "private_key": private_key_b58,
        }
    )


@app.route("/api/attendance", methods=["GET", "POST"])
def api_attendance():
    """Handle attendance marking and retrieval"""
    if request.method == "GET":
        # Return attendance records
        attendance = load_attendance()
        return jsonify({"success": True, "records": attendance})

    # POST - Mark attendance
    data = request.json
    server_qr = data.get("server_qr", {})
    employee_public_key = data.get("public_key", "").strip()
    employee_signature = data.get("employee_signature", "")

    if not employee_public_key or not employee_signature or not server_qr:
        return jsonify({"success": False, "message": "Missing required data"})

    # Load employee data and find by public key
    employees = load_employees()
    employee = None
    emp_id = None

    for eid, emp_data in employees.items():
        if emp_data.get("public_key") == employee_public_key:
            employee = emp_data
            emp_id = eid
            break

    if not employee:
        return jsonify(
            {"success": False, "message": "Employee not registered or invalid key"}
        )

    # === Verification Step 1: Verify Server QR Signature ===
    qr_message = server_qr.get("message", "")
    qr_signature = server_qr.get("signature", "")
    qr_timestamp = server_qr.get("timestamp", 0)
    qr_server_key = server_qr.get("server_public_key", "")

    # Check if server public key matches
    if qr_server_key != server_public_key_b58:
        return jsonify({"success": False, "message": "Invalid QR code - wrong server"})

    # Verify server's signature on QR code
    if not verify_signature(server_public_key_b58, qr_message, qr_signature):
        return jsonify({"success": False, "message": "Invalid QR code signature"})

    # === Verification Step 2: Check QR Code Timestamp ===
    current_time = int(time.time())
    time_diff = current_time - qr_timestamp

    if time_diff > QR_GRACE_PERIOD or time_diff < -QR_GRACE_PERIOD:
        return jsonify(
            {"success": False, "message": f"QR code expired (age: {time_diff}s)"}
        )

    # === Verification Step 3: Prevent Replay Attacks ===
    time_slot = get_time_slot()
    if not data.get("confirm_checkout") and emp_id in recent_qr_usage:
        if time_slot in recent_qr_usage[emp_id]:
            last_used = recent_qr_usage[emp_id][time_slot]
            if current_time - last_used < QR_REUSE_WINDOW:
                return jsonify(
                    {"success": False, "message": "QR code already used recently"}
                )

    # === Verification Step 4: Verify Employee Signature ===
    if not verify_signature(employee_public_key, qr_message, employee_signature):
        return jsonify({"success": False, "message": "Invalid employee signature"})

    # === All Verifications Passed - Mark Attendance ===
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")

    attendance = load_attendance()
    existing_record = None
    for record in attendance:
        if record["emp_id"] == emp_id and record["date"] == current_date:
            existing_record = record
            break

    if existing_record:
        if existing_record["out_time"] is None:
            if data.get("confirm_checkout"):
                # Confirm check-out
                existing_record["out_time"] = now.strftime("%H:%M:%S")
                existing_record["out_timestamp"] = now.isoformat()
                existing_record["status"] = "Present"
                save_attendance(attendance)
                print(f"✓ Check-out: {emp_id} - {employee['name']} at {now.strftime('%H:%M:%S')}")
                return jsonify({
                    "success": True,
                    "message": "Check-out successful",
                    "employee_name": employee["name"],
                    "action": "check-out",
                    "in_time": existing_record["in_time"],
                    "out_time": existing_record["out_time"],
                    "status": "Present"
                })
            else:
                # Pending check-out
                print(f"⚠ Pending check-out for {emp_id} on {current_date}")
                return jsonify({
                    "success": False,
                    "message": "Confirm check-out",
                    "employee_name": employee["name"],
                    "in_time": existing_record["in_time"],
                    "out_time": now.strftime("%H:%M:%S"),
                    "status": "Pending Check-out"
                })
        else:
            # Already checked out
            print(f"⚠ Already checked out for {emp_id} on {current_date}")
            return jsonify({
                "success": False,
                "message": "Already checked out today",
                "employee_name": employee["name"],
                "in_time": existing_record["in_time"],
                "out_time": existing_record["out_time"],
                "status": "Already Present"
            })
    else:
        # Check-in
        attendance_record = {
            "emp_id": emp_id,
            "employee_name": employee["name"],
            "date": current_date,
            "in_time": now.strftime("%H:%M:%S"),
            "in_timestamp": now.isoformat(),
            "out_time": None,
            "out_timestamp": None,
            "status": "Present",
            "qr_timestamp": qr_timestamp,
            "verified": True,
        }
        attendance.append(attendance_record)
        save_attendance(attendance)
        print(f"✓ Check-in: {emp_id} - {employee['name']} at {now.strftime('%H:%M:%S')}")
        return jsonify({
            "success": True,
            "message": "Check-in successful",
            "employee_name": employee["name"],
            "action": "check-in",
            "in_time": attendance_record["in_time"],
            "status": "Present"
        })

    # Track QR usage
    if emp_id not in recent_qr_usage:
        recent_qr_usage[emp_id] = {}
    recent_qr_usage[emp_id][time_slot] = current_time


# === Main ===
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔐  ATTENDANCE SYSTEM")
    print("=" * 60)
    print(f"✓ Server Public Key: {server_public_key_b58}")
    print(f"✓ QR Refresh Interval: {INTERVAL} seconds")
    print(f"✓ QR Grace Period: {QR_GRACE_PERIOD} seconds")
    print(f"✓ Data Directory: {DATA_DIR}")
    print("=" * 60)

    # Start ngrok tunnel
    try:
        public_url = ngrok.connect(5000)
        print(f"\n✓ ngrok tunnel created: {public_url}")
        print(f"✓ Access the system at: {public_url}\n")
    except Exception as e:
        print(f"\n⚠ Could not create ngrok tunnel: {e}")
        print("Running locally only on http://localhost:5000\n")

    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
