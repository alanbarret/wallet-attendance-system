# Wallet Attendance System

A cryptographically secure attendance management system using Ed25519 signatures and QR codes for tamper-proof time tracking.

![System Flowchart](flowchart.svg)

## Overview

This system provides a secure, decentralized attendance tracking solution where employees use their cryptographic wallet keys to mark attendance via QR code scanning. The system ensures authenticity through dual signature verification and prevents replay attacks.

## Features

- 🔐 **Cryptographic Security**: Ed25519 signature verification
- 📱 **QR Code Authentication**: Dynamic QR codes with time-based expiry
- 🛡️ **Replay Attack Prevention**: Time windows and usage tracking
- 👥 **Employee Management**: Registration with key pair generation
- 📊 **Attendance Records**: Detailed logs with verification status
- 🌐 **Web Interface**: Responsive web UI for all operations

## Security Features

- Dual signature verification (server + employee)
- Time-based QR code expiry (30 seconds)
- Replay attack prevention (5-minute reuse window)
- Server-side timestamp generation
- Zero-knowledge authentication

## Installation

### Prerequisites

- Python 3.8+
- Flask
- Cryptography libraries
- ngrok (for public access)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd phantom_wallet_attendance
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export NGROK_AUTH_TOKEN="your-ngrok-token"
```

4. Run the application:
```bash
python app.py
```

5. Access the system at the provided ngrok URL

## Usage

### For Administrators

1. **Employee Registration**: Use the registration page to create employee accounts and generate key pairs
2. **View Attendance**: Access the attendance records page to view all logs
3. **Monitor Security**: Check verification status and timestamps

### For Employees

1. **Get QR Code**: Visit the home page to see the dynamic QR code
2. **Mark Attendance**: Use the scanner page with your private key
3. **Check Status**: View confirmation messages for check-in/check-out

## Project Structure

```
phantom_wallet_attendance/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── data/                  # Data storage
│   ├── employees.json     # Employee records
│   └── attendance.json    # Attendance logs
├── keys/                  # Server keys (generated)
├── docs/                  # Documentation
└── backups/               # Backup files
```

## API Endpoints

- `GET /` - Home page with QR code
- `GET /qr` - QR code image
- `GET /register` - Employee registration page
- `GET /scan` - QR scanner page
- `GET /attendance` - Attendance records page
- `POST /api/register` - Register new employee
- `POST /api/attendance` - Mark attendance/check-out
- `GET /api/attendance` - Retrieve attendance records

## Configuration

Key configuration parameters in `app.py`:

- `INTERVAL`: QR refresh rate (10 seconds)
- `QR_GRACE_PERIOD`: QR validity window (30 seconds)
- `QR_REUSE_WINDOW`: Replay prevention (300 seconds)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues or questions, please create an issue in the repository or contact the development team.

## Security Considerations

- Private keys should be stored securely by employees
- Server keys are generated and stored locally
- All communications should be over HTTPS in production
- Regular key rotation is recommended

## Changelog

### v1.0.0
- Initial release with basic attendance tracking
- Cryptographic signature verification
- QR code authentication
- Web interface

### v1.1.0
- Added check-in/check-out functionality
- Confirmation dialogs for check-out
- Enhanced security features
- Improved UI/UX