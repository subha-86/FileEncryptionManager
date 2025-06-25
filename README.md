# FileEncryptionManager


**FileEncryptionManager** is a robust, cross-platform desktop application for secure file and folder encryption. Built using Python, PyQt5, and the `cryptography` library, it offers a comprehensive GUI-based solution for data protection, secure storage, and file integrity verification.

## Overview

This tool enables users to:

- Encrypt individual files or entire folders using AES symmetric encryption.
- Securely store and track file versions with tamper detection.
- Manage file metadata and perform version-controlled decryption.
- Shred original files after encryption to ensure irreversible deletion.
- Search encrypted files by metadata.
- Use a master password for access control.
- Preview decrypted file content in a secure sandbox.

---

## Key Features

| Feature                        | Description                                          |
|-------------------------------|------------------------------------------------------|
|    **Master Password Login**  | Secures app access with hashed master credentials.   |
|  **File/Folder Encryption**  | Encrypts data using AES via the Fernet mechanism.   |
| **Strong Password Generator** | Suggests cryptographically strong passwords.        |
|  **Metadata-Based Search**  | Locates files through versioned encryption metadata.|
|  **Version Management**     | Maintains and decrypts specific file versions.       |
|  **Secure Shredding**        | Deletes original files post-encryption securely.     |
|  **Light/Dark Mode UI**      | Switch between accessibility themes.                |

---

## Installation

### Prerequisites

- Python 3.7+
- pip (Python package manager)

### Clone and Setup

```bash
git clone https://github.com/subha-86/FileEncryptionManager.git
cd FileEncryptionManager
pip install -r requirements.txt
