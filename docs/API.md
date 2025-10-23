# API Documentation

This document describes all API endpoints for the Phantom Wallet Attendance System.

## Base URL

All API endpoints are relative to the application root (e.g., `https://your-domain.ngrok.io/`).

## Authentication

The system uses cryptographic signatures for authentication. No traditional API keys are required.

## Endpoints

### GET /

**Description**: Home page with dynamic QR code display.

**Response**: HTML page with QR code and system information.

**Example**:
```bash
curl -X GET "https://your-domain.ngrok.io/"
```

### GET /qr

**Description**: Generates and returns the current QR code image.

**Response**: PNG image of the QR code.

**Headers**:
- Content-Type: image/png

**Example**:
```bash
curl -X GET "https://your-domain.ngrok.io/qr" -o qr.png
```

### GET /register

**Description**: Employee registration page.

**Response**: HTML registration form.

**Example**:
```bash
curl -X GET "https://your-domain.ngrok.io/register"
```

### GET /scan

**Description**: QR code scanner page for marking attendance.

**Response**: HTML page with QR scanner interface.

**Example**:
```bash
curl -X GET "https://your-domain.ngrok.io/scan"
```

### GET /attendance

**Description**: Attendance records viewing page.

**Response**: HTML page with attendance table and filters.

**Example**:
```bash
curl -X GET "https://your-domain.ngrok.io/attendance"
```

### POST /api/register

**Description**: Register a new employee and generate cryptographic key pair.

**Request Body**:
```json
{
  "emp_id": "EMP001",
  "name": "John Doe",
  "email": "john@example.com",
  "department": "Engineering"
}
```

**Response** (Success):
```json
{
  "success": true,
  "message": "Employee John Doe registered successfully",
  "emp_id": "EMP001",
  "public_key": "Base58-encoded-public-key",
  "private_key": "Base58-encoded-private-key"
}
```

**Response** (Error):
```json
{
  "success": false,
  "message": "Employee EMP001 already registered"
}
```

**Status Codes**:
- 200: Success
- 400: Invalid request data

### POST /api/attendance

**Description**: Mark attendance or check-out using QR code and cryptographic signature.

**Request Body**:
```json
{
  "server_qr": {
    "message": "attendance:timestamp:public_key",
    "signature": "Base58-signature",
    "timestamp": 1234567890,
    "server_public_key": "Base58-server-public-key"
  },
  "public_key": "Base58-employee-public-key",
  "employee_signature": "Base58-employee-signature",
  "confirm_checkout": false  // Optional, for check-out confirmation
}
```

**Response** (Check-in Success):
```json
{
  "success": true,
  "message": "Check-in successful",
  "employee_name": "John Doe",
  "action": "check-in",
  "in_time": "14:30:25",
  "status": "Present"
}
```

**Response** (Check-out Success):
```json
{
  "success": true,
  "message": "Check-out successful",
  "employee_name": "John Doe",
  "action": "check-out",
  "in_time": "09:00:00",
  "out_time": "17:30:25",
  "status": "Present"
}
```

**Response** (Check-out Confirmation Required):
```json
{
  "success": false,
  "message": "Confirm check-out",
  "employee_name": "John Doe",
  "in_time": "09:00:00",
  "out_time": "17:30:25",
  "status": "Pending Check-out"
}
```

**Response** (Already Checked Out):
```json
{
  "success": false,
  "message": "Already checked out today",
  "employee_name": "John Doe",
  "in_time": "09:00:00",
  "out_time": "17:30:25",
  "status": "Already Present"
}
```

**Response** (Error Examples):
```json
{
  "success": false,
  "message": "Invalid QR code signature"
}
```

```json
{
  "success": false,
  "message": "QR code expired (age: 45s)"
}
```

```json
{
  "success": false,
  "message": "QR code already used recently"
}
```

**Status Codes**:
- 200: Success or confirmation required
- 400: Invalid request or verification failed

### GET /api/attendance

**Description**: Retrieve all attendance records.

**Response**:
```json
{
  "success": true,
  "records": [
    {
      "emp_id": "EMP001",
      "employee_name": "John Doe",
      "date": "2025-10-22",
      "in_time": "09:00:00",
      "in_timestamp": "2025-10-22T09:00:00.123456",
      "out_time": "17:30:00",
      "out_timestamp": "2025-10-22T17:30:00.654321",
      "status": "Present",
      "qr_timestamp": 1234567890,
      "verified": true
    }
  ]
}
```

**Status Codes**:
- 200: Success

## Error Handling

All API responses include a `success` field indicating the outcome:

- `true`: Operation successful
- `false`: Error occurred or confirmation required

Error messages are descriptive and indicate the specific issue (e.g., "Invalid employee signature", "QR code expired").

## Security Notes

- All attendance marking requires valid cryptographic signatures
- QR codes expire after 30 seconds
- Replay attacks are prevented with time windows
- Employee private keys never leave the client device
- Server validates all signatures before processing

## Rate Limiting

The system implements basic rate limiting through QR code time windows and replay prevention mechanisms. No additional rate limiting is configured at the API level.

## Data Formats

- **Timestamps**: ISO 8601 format (e.g., "2025-10-22T14:30:25.123456")
- **Times**: HH:MM:SS format (e.g., "14:30:25")
- **Keys**: Base58 encoded strings
- **Signatures**: Base58 encoded Ed25519 signatures