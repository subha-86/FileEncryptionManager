# Secure File Vault - Pro Version

import sys
import os
import hashlib
import json
import base64
import datetime
import bcrypt
import secrets
import string
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QFileDialog, QMessageBox, QCheckBox, QComboBox, QInputDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from cryptography.fernet import Fernet

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENC_DIR = os.path.join(BASE_DIR, "encrypted_files")
META_FILE = os.path.join(BASE_DIR, "metadata.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

os.makedirs(ENC_DIR, exist_ok=True)

# Utilities
def get_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()

def generate_key_from_password(password: str) -> bytes:
    key = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(key[:32])

def generate_strong_password(length=16):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def shred_file(path):
    try:
        length = os.path.getsize(path)
        with open(path, 'wb') as f:
            f.write(os.urandom(length))
        os.remove(path)
    except Exception as e:
        print(f"Shred failed: {e}")

# Metadata

def load_metadata():
    if os.path.exists(META_FILE):
        with open(META_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    with open(META_FILE, 'w') as f:
        json.dump(metadata, f, indent=4)

# Config

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# File Logic

def encrypt_file(file_path, password, output_dir, shred=False):
    key = generate_key_from_password(password)
    fernet = Fernet(key)

    with open(file_path, 'rb') as f:
        data = f.read()

    encrypted_data = fernet.encrypt(data)
    file_name = os.path.basename(file_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    enc_file_name = f"{file_name}_{timestamp}.enc"
    enc_file_path = os.path.join(output_dir, enc_file_name)

    with open(enc_file_path, 'wb') as f:
        f.write(encrypted_data)

    file_hash = get_sha256(file_path)
    metadata = load_metadata()
    if file_name not in metadata:
        metadata[file_name] = {}
    metadata[file_name][timestamp] = {
        'encrypted_file': enc_file_path,
        'sha256': file_hash,
        'timestamp': datetime.datetime.now().isoformat()
    }
    save_metadata(metadata)

    if shred:
        shred_file(file_path)

    return enc_file_path

def find_file_in_metadata(enc_filename):
    metadata = load_metadata()
    for original_name, versions in metadata.items():
        if isinstance(versions, dict):
            for timestamp, details in versions.items():
                if isinstance(details, dict) and enc_filename == os.path.basename(details.get('encrypted_file', '')):
                    return original_name, timestamp
    return None, None

def decrypt_file(file_name, password, version=None, preview_only=False):
    metadata = load_metadata()
    if file_name not in metadata:
        raise ValueError("File not found in metadata.")

    if not version:
        version = sorted(metadata[file_name].keys())[-1]  # Latest version

    enc_path = metadata[file_name][version]['encrypted_file']
    key = generate_key_from_password(password)
    fernet = Fernet(key)

    with open(enc_path, 'rb') as f:
        encrypted_data = f.read()

    decrypted_data = fernet.decrypt(encrypted_data)
    if preview_only:
        return decrypted_data.decode(errors='ignore')

    output_path = os.path.join(BASE_DIR, f"decrypted_{file_name}")
    with open(output_path, 'wb') as f:
        f.write(decrypted_data)

    new_hash = get_sha256(output_path)
    if new_hash != metadata[file_name][version]['sha256']:
        raise ValueError("File hash mismatch! Possible tampering.")

    return output_path

# GUI Class

class SecureStorageApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secure File Vault - Pro")
        self.setGeometry(100, 100, 650, 500)
        self.setStyleSheet("background-color: #2b2b3a; color: white;")
        self.output_dir = ENC_DIR
        self.authenticate()

    def authenticate(self):
        config = load_config()
        if 'master_hash' not in config:
            pwd, ok = QInputDialog.getText(self, "Set Master Password", "Create master password:", QLineEdit.Password)
            if ok and pwd:
                hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
                save_config({'master_hash': hashed})
            else:
                sys.exit()
        else:
            for _ in range(3):
                pwd, ok = QInputDialog.getText(self, "Login", "Enter master password:", QLineEdit.Password)
                if ok and pwd and bcrypt.checkpw(pwd.encode(), config['master_hash'].encode()):
                    self.init_ui()
                    return
            QMessageBox.critical(self, "Access Denied", "Incorrect password.")
            sys.exit()

    def init_ui(self):
        layout = QVBoxLayout()

        self.title = QLabel("Secure File Vault")
        self.title.setFont(QFont('Arial', 18, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select files or folders...")
        self.path_input.setReadOnly(True)

        browse_btn = QPushButton("Browse Files")
        browse_btn.clicked.connect(self.browse_files)

        browse_folder_btn = QPushButton("Encrypt Folder")
        browse_folder_btn.clicked.connect(self.encrypt_folder)

        gen_pwd_btn = QPushButton("Generate Password")
        gen_pwd_btn.clicked.connect(self.generate_password)

        self.output_btn = QPushButton("Output Folder")
        self.output_btn.clicked.connect(self.select_output_dir)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm password")
        self.confirm_input.setEchoMode(QLineEdit.Password)

        self.shred_checkbox = QCheckBox("Shred Original File")
        self.preview_checkbox = QCheckBox("Preview on Decrypt")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search metadata filename")
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search_file_metadata)

        encrypt_btn = QPushButton("Encrypt Files")
        encrypt_btn.clicked.connect(self.encrypt_action)

        decrypt_btn = QPushButton("Decrypt File")
        decrypt_btn.clicked.connect(self.decrypt_action)

        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Dark Mode", "Light Mode"])
        self.theme_selector.currentTextChanged.connect(self.toggle_theme)

        layout.addWidget(self.title)
        layout.addWidget(self.path_input)
        layout.addWidget(browse_btn)
        layout.addWidget(browse_folder_btn)
        layout.addWidget(self.output_btn)
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_input)
        layout.addWidget(gen_pwd_btn)
        layout.addWidget(self.shred_checkbox)
        layout.addWidget(self.preview_checkbox)
        layout.addWidget(QLabel("\nMetadata Search"))
        layout.addWidget(self.search_input)
        layout.addWidget(search_btn)
        layout.addWidget(encrypt_btn)
        layout.addWidget(decrypt_btn)
        layout.addWidget(self.theme_selector)

        self.setLayout(layout)

    def browse_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if paths:
            self.path_input.setText("; ".join(paths))

    def encrypt_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        pwd = self.password_input.text()
        confirm = self.confirm_input.text()
        if pwd != confirm:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match")
            return
        for root, _, files in os.walk(folder):
            for file in files:
                full_path = os.path.join(root, file)
                try:
                    encrypt_file(full_path, pwd, self.output_dir, self.shred_checkbox.isChecked())
                except Exception as e:
                    print(f"Failed: {e}")
        QMessageBox.information(self, "Done", "Folder encrypted.")

    def generate_password(self):
        pwd = generate_strong_password()
        self.password_input.setText(pwd)
        self.confirm_input.setText(pwd)
        QMessageBox.information(self, "Password", pwd)

    def select_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if directory:
            self.output_dir = directory

    def encrypt_action(self):
        files = self.path_input.text().split('; ')
        pwd = self.password_input.text()
        confirm = self.confirm_input.text()
        if pwd != confirm:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match")
            return
        for f in files:
            try:
                enc_path = encrypt_file(f, pwd, self.output_dir, self.shred_checkbox.isChecked())
                QMessageBox.information(self, "Encrypted", f"Stored at: {enc_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def decrypt_action(self):
        enc_file = os.path.basename(self.path_input.text().split('; ')[0])
        pwd = self.password_input.text()
        file_name, version = find_file_in_metadata(enc_file)
        if not file_name:
            QMessageBox.critical(self, "Error", "File not found in metadata")
            return
        try:
            if self.preview_checkbox.isChecked():
                content = decrypt_file(file_name, pwd, version, preview_only=True)
                QMessageBox.information(self, "Preview", content[:1000])
            else:
                dec_path = decrypt_file(file_name, pwd, version)
                QMessageBox.information(self, "Decrypted", f"Saved at: {dec_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def search_file_metadata(self):
        name = self.search_input.text().strip()
        metadata = load_metadata()
        result = metadata.get(name)
        if result:
            QMessageBox.information(self, "Found", json.dumps(result, indent=4))
        else:
            QMessageBox.warning(self, "Not Found", "File not in metadata.")

    def toggle_theme(self, mode):
        if mode == "Light Mode":
            self.setStyleSheet("background-color: white; color: black;")
        else:
            self.setStyleSheet("background-color: #2b2b3a; color: white;")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SecureStorageApp()
    window.show()
    sys.exit(app.exec_())
