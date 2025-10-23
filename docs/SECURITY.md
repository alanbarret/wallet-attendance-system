# Security Documentation

This document outlines the security features, threat model, and best practices for the Phantom Wallet Attendance System.

## Security Overview

The system implements multiple layers of security to ensure the integrity and authenticity of attendance records:

1. **Cryptographic Authentication**: Ed25519 digital signatures
2. **Time-Based Validation**: QR code expiry and replay prevention
3. **Server-Side Verification**: All signatures validated on server
4. **Zero-Knowledge Design**: Private keys never leave client devices

## Cryptographic Security

### Ed25519 Signatures

- **Algorithm**: Ed25519 (EdDSA over Curve25519)
- **Key Length**: 32 bytes (256 bits) for private keys, 32 bytes for public keys
- **Signature Length**: 64 bytes
- **Encoding**: Base58 for compatibility with wallet systems

### Dual Signature Verification

Every attendance transaction requires two signatures:

1. **Server Signature**: Validates the QR code authenticity
2. **Employee Signature**: Validates the employee's identity and intent

```python
# Server signs the QR message
message = f"attendance:{timestamp}:{server_public_key}"
server_signature = sign_message(server_private_key, message)

# Employee signs the same message
employee_signature = sign_message(employee_private_key, message)
```

### Signature Verification Process

1. Verify server signature on QR code
2. Check QR timestamp is within grace period (±30 seconds)
3. Verify employee signature matches their public key
4. Check for replay attacks using time windows

## Threat Model

### Protected Against

- **Replay Attacks**: QR codes cannot be reused within 5 minutes
- **Signature Forgery**: Ed25519 signatures are cryptographically secure
- **Time Manipulation**: Server-side timestamp generation
- **Man-in-the-Middle**: All data is signed and verified
- **Unauthorized Access**: Requires valid private key

### Potential Attack Vectors

- **Private Key Theft**: If an employee's private key is compromised
- **Server Compromise**: If the server private key is stolen
- **Time Synchronization**: If server clock is manipulated
- **QR Code Interception**: If QR codes are scanned by unauthorized parties

## Security Features

### QR Code Security

- **Dynamic Generation**: QR codes change every 10 seconds
- **Time-Limited Validity**: 30-second grace period for scanning
- **Unique Content**: Each QR includes timestamp and server public key
- **Signature Protection**: QR content is signed by server

### Replay Attack Prevention

- **Time Windows**: QR codes cannot be reused within 5 minutes
- **Per-Employee Tracking**: Separate tracking per employee
- **Confirmation Bypass**: Confirmation requests skip replay checks

### Data Integrity

- **Server-Side Timestamps**: All attendance times set by server
- **Immutable Records**: Attendance records include verification status
- **Audit Trail**: Full timestamp and signature information stored

## Best Practices

### For System Administrators

1. **Secure Key Storage**:
   - Server keys are stored in `keys/server_keys.json`
   - Backup keys securely and rotate regularly
   - Use strong passwords for server access

2. **Network Security**:
   - Use HTTPS in production environments
   - Monitor for unusual access patterns
   - Implement firewall rules

3. **Time Synchronization**:
   - Ensure server clock is accurate (use NTP)
   - Monitor for clock drift
   - Consider distributed time sources

### For Employees

1. **Private Key Security**:
   - Store private keys securely (encrypted storage recommended)
   - Never share private keys
   - Use secure devices for attendance marking

2. **QR Code Handling**:
   - Only scan QR codes from trusted displays
   - Verify the server public key matches
   - Report suspicious QR codes immediately

### For Developers

1. **Code Security**:
   - Review cryptographic implementations regularly
   - Use secure random number generation
   - Implement proper error handling

2. **Testing**:
   - Test signature verification thoroughly
   - Validate time window calculations
   - Check edge cases (clock changes, network issues)

## Security Considerations

### Private Key Management

- **Generation**: Keys generated using cryptographically secure random
- **Storage**: Employee private keys stored in browser localStorage (client-side only)
- **Transmission**: Private keys never sent to server
- **Recovery**: No key recovery mechanism (employees must re-register if lost)

### Network Security

- **HTTPS**: All communications should be encrypted in production
- **CORS**: Configured to allow cross-origin requests from web interface
- **Input Validation**: All inputs validated and sanitized

### Data Protection

- **Encryption at Rest**: Employee data stored in JSON files (consider encryption)
- **Access Control**: Files have appropriate permissions (readable by server only)
- **Backup Security**: Backup files should be encrypted and stored securely

## Incident Response

### If a Private Key is Compromised

1. **Immediate Actions**:
   - Instruct employee to generate new key pair
   - Revoke old public key from system
   - Investigate how compromise occurred

2. **System Updates**:
   - Update employee record with new public key
   - Invalidate old attendance records if necessary
   - Monitor for suspicious activity

### If Server is Compromised

1. **Immediate Actions**:
   - Shut down the system
   - Generate new server key pair
   - Notify all employees to re-register

2. **Recovery**:
   - Restore from secure backups
   - Verify all attendance records
   - Implement additional security measures

## Compliance

### Data Protection

- **GDPR Considerations**: System stores personal data (names, emails)
- **Right to Erasure**: Employees can request data deletion
- **Data Minimization**: Only necessary data is collected

### Audit Requirements

- **Logging**: All attendance actions are logged with timestamps
- **Verification Status**: Each record includes verification information
- **Access Logs**: Server access should be logged

## Security Testing

### Recommended Tests

1. **Signature Verification**:
   - Test with invalid signatures
   - Test with modified messages
   - Test with expired timestamps

2. **Time Validation**:
   - Test with future timestamps
   - Test with old timestamps
   - Test during clock changes

3. **Replay Prevention**:
   - Attempt to reuse QR codes
   - Test time window boundaries
   - Verify per-employee tracking

### Tools

- **Cryptographic Testing**: Use libraries like `pycryptodome` for validation
- **Network Testing**: Use tools like Wireshark for traffic analysis
- **Time Testing**: Use `freezegun` for time manipulation in tests

## Future Enhancements

### Potential Improvements

1. **Hardware Security Modules (HSM)**: Store server keys in HSM
2. **Multi-Signature**: Require multiple approvals for certain actions
3. **Blockchain Integration**: Store records on immutable ledger
4. **Biometric Authentication**: Add fingerprint/face recognition
5. **Audit Logging**: Enhanced logging with tamper detection

### Monitoring

- **Intrusion Detection**: Monitor for unusual signature verification failures
- **Performance Monitoring**: Track QR generation and verification times
- **Compliance Monitoring**: Regular security audits and penetration testing

## Contact

For security-related issues or questions, please contact the system administrators immediately. Do not post security-sensitive information in public channels.