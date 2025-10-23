# System Architecture

This document describes the architecture and design of the Phantom Wallet Attendance System.

## Overview

The system is built as a web application using Flask (Python) with a client-side JavaScript interface. It implements a cryptographically secure attendance tracking mechanism using QR codes and digital signatures.

## System Components

### Backend (Server-Side)

#### Flask Application (`app.py`)

The main server component handles:
- HTTP request routing
- Cryptographic operations
- Data storage and retrieval
- QR code generation
- HTML template rendering

**Key Modules**:
- **Routes**: HTTP endpoints for web interface and API
- **Cryptography**: Ed25519 key generation and signature verification
- **Data Management**: JSON file operations for employees and attendance
- **QR Generation**: Dynamic QR code creation with embedded data

#### Data Storage

**Files**:
- `data/employees.json`: Employee records with public keys
- `data/attendance.json`: Attendance logs with timestamps and verification status
- `keys/server_keys.json`: Server's cryptographic key pair

**Data Structures**:

**Employee Record**:
```json
{
  "emp_id": "EMP001",
  "name": "John Doe",
  "email": "john@example.com",
  "department": "Engineering",
  "public_key": "Base58-encoded-public-key",
  "registered_at": "2025-10-22T10:00:00.123456"
}
```

**Attendance Record**:
```json
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
```

### Frontend (Client-Side)

#### Web Interface

**Pages**:
- **Home (`/`)**: Displays dynamic QR code and system status
- **Register (`/register`)**: Employee registration form
- **Scan (`/scan`)**: QR code scanner with private key input
- **Attendance (`/attendance`)**: Attendance records viewer with filters

**Technologies**:
- **HTML5**: Semantic markup with responsive design
- **CSS3**: Modern styling with gradients and animations
- **JavaScript**: QR scanning, cryptographic operations, UI interactions

#### QR Code Scanning

**Library**: html5-qrcode
- **Camera Access**: Requests camera permissions for QR scanning
- **Real-time Processing**: Continuous scanning with result handling
- **Error Handling**: Graceful handling of scanning failures

#### Cryptographic Operations (Client-Side)

**Libraries**:
- **TweetNaCl**: Ed25519 signature generation and verification
- **Base58**: Encoding/decoding for key compatibility
- **Browser Crypto**: Secure random number generation

**Key Derivation**:
```javascript
// Derive public key from private key
const keyPair = nacl.sign.keyPair.fromSecretKey(privateKeyBytes);
const publicKeyB58 = Base58.encode(keyPair.publicKey);
```

**Message Signing**:
```javascript
// Sign message with private key
const messageBytes = nacl.util.decodeUTF8(message);
const signature = nacl.sign.detached(messageBytes, privateKeyBytes);
const signatureB58 = Base58.encode(signature);
```

## System Flow

### Attendance Marking Process

1. **QR Code Generation** (Server):
   - Generate timestamp-based message
   - Sign with server private key
   - Create QR code with signed data

2. **QR Code Display** (Client):
   - Fetch QR code image from server
   - Display in web interface
   - Auto-refresh every 10 seconds

3. **Attendance Scanning** (Client):
   - Employee enters private key
   - Scans QR code with camera
   - Derives public key from private key
   - Signs QR message with private key
   - Sends signed request to server

4. **Verification** (Server):
   - Verify server signature on QR code
   - Check QR timestamp validity (±30 seconds)
   - Verify employee signature
   - Check for replay attacks
   - Record attendance with server timestamp

5. **Response** (Client):
   - Display success/error message
   - Show confirmation dialog for check-out
   - Update UI accordingly

### Check-in/Check-out Flow

1. **First Scan**: Creates attendance record with in_time
2. **Second Scan**: Shows confirmation dialog with times
3. **Confirmation**: Updates record with out_time
4. **Subsequent Scans**: Shows already checked out message

## Security Architecture

### Cryptographic Layer

**Server Side**:
- Ed25519 key pair generation and storage
- Message signing for QR codes
- Signature verification for incoming requests
- Secure random number generation

**Client Side**:
- Private key storage in browser localStorage
- Public key derivation from private key
- Message signing for authentication
- Secure handling of sensitive data

### Network Architecture

**Development**:
- Local Flask server on port 5000
- ngrok tunnel for external access
- HTTP (consider HTTPS for production)

**Production Considerations**:
- HTTPS encryption for all communications
- Firewall configuration
- Load balancing for scalability
- Monitoring and logging

## Data Flow Diagram

```
Employee Device                    Server
     |                              |
     | 1. Request QR Code           |
     |----------------------------->|
     |                              |
     | 2. Display QR Code           |
     |<-----------------------------|
     |                              |
     | 3. Scan QR + Sign Message    |
     |----------------------------->|
     |                              |
     | 4. Verify Signatures         |
     |    & Record Attendance       |
     |<-----------------------------|
     |                              |
     | 5. Show Confirmation         |
     |----------------------------->|
```

## Component Interactions

### Flask Routes

- **Static Routes**: Serve HTML pages and QR images
- **API Routes**: Handle registration and attendance operations
- **Template Rendering**: Dynamic HTML generation with data

### JavaScript Components

- **QR Scanner**: Camera access and code processing
- **Crypto Functions**: Key derivation and signing
- **UI Updates**: Dynamic content updates based on responses
- **Modal Management**: Confirmation dialogs

### Data Management

- **JSON Operations**: Load/save employee and attendance data
- **Key Management**: Generate and store server keys
- **Backup System**: Automatic data backup functionality

## Scalability Considerations

### Current Limitations

- **Single Server**: No load balancing or redundancy
- **File Storage**: JSON files may not scale for large datasets
- **No Database**: Consider migrating to database for production
- **Memory Storage**: QR usage tracking stored in memory

### Potential Improvements

1. **Database Integration**:
   - PostgreSQL or MySQL for data persistence
   - Connection pooling for performance
   - Backup and recovery procedures

2. **Caching**:
   - Redis for session management
   - QR code caching to reduce generation overhead
   - Attendance record caching for faster retrieval

3. **Microservices**:
   - Separate services for QR generation and verification
   - API gateway for request routing
   - Message queues for async processing

4. **Monitoring**:
   - Application performance monitoring
   - Security event logging
   - Health checks and alerting

## Deployment Architecture

### Development Setup

```
Local Machine
├── Flask App (Port 5000)
├── ngrok Tunnel (Public URL)
└── Browser Client (Web Interface)
```

### Production Setup

```
Load Balancer
├── Web Server 1 (Flask + Gunicorn)
├── Web Server 2 (Flask + Gunicorn)
├── Database Server (PostgreSQL)
├── Cache Server (Redis)
└── Monitoring Server
```

## Error Handling

### Server-Side

- **Signature Failures**: Return appropriate error messages
- **Time Validation**: Check QR expiry and replay windows
- **Data Integrity**: Validate all inputs and handle file I/O errors
- **Logging**: Comprehensive logging for debugging and monitoring

### Client-Side

- **Camera Access**: Handle permission denials gracefully
- **Network Errors**: Retry mechanisms and offline handling
- **Key Validation**: Check key formats and lengths
- **UI Feedback**: Clear error messages and loading states

## Performance Characteristics

### Current Performance

- **QR Generation**: ~100ms per code
- **Signature Verification**: ~10ms per verification
- **Page Load**: <2 seconds for all pages
- **Database Operations**: <50ms for JSON operations

### Bottlenecks

- **File I/O**: JSON operations may slow with large datasets
- **QR Generation**: CPU intensive for frequent updates
- **Network**: ngrok tunnel adds latency
- **Client Rendering**: JavaScript crypto operations on mobile devices

## Technology Stack

### Backend

- **Language**: Python 3.8+
- **Framework**: Flask 2.0+
- **Cryptography**: cryptography, base58
- **Image Processing**: qrcode, Pillow
- **Networking**: ngrok

### Frontend

- **Language**: JavaScript (ES6+)
- **Libraries**:
  - html5-qrcode (QR scanning)
  - TweetNaCl (cryptography)
  - Base58 (encoding)
- **Styling**: CSS3 with responsive design

### Development Tools

- **Version Control**: Git
- **Documentation**: Markdown files
- **Testing**: Manual testing (consider adding automated tests)
- **Deployment**: ngrok for development, consider Docker for production

## Future Architecture Evolution

### Phase 1 (Current)
- Single server with file storage
- Basic web interface
- Manual testing

### Phase 2 (Enhanced)
- Database integration
- API improvements
- Automated testing

### Phase 3 (Enterprise)
- Microservices architecture
- Advanced security features
- Performance optimization
- Mobile applications

This architecture provides a solid foundation for a secure attendance system while allowing for future enhancements and scalability improvements.