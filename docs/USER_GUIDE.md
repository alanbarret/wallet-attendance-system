# User Guide

This guide explains how to use the Phantom Wallet Attendance System for both employees and administrators.

## Getting Started

### For New Users

1. **Access the System**: Open your web browser and go to the provided system URL
2. **Register**: If you're a new employee, register first to get your wallet keys
3. **Mark Attendance**: Use the scanner page to mark your attendance with QR codes

## Employee Guide

### Registration Process

1. **Visit Registration Page**: Click on "Register Employee" or go to `/register`
2. **Fill the Form**:
   - Enter your Employee ID (e.g., EMP001)
   - Enter your full name
   - Provide your email (optional)
   - Select your department (optional)

3. **Generate Keys**: Click "Register & Generate Keys"
4. **Save Your Keys**:
   - **Public Key**: Safe to share (copy and save)
   - **Private Key**: Keep secret! (copy and save securely)
   - Use the "Save to Device" button for convenience

5. **Important**: Store your private key securely. If lost, you'll need to re-register.

### Daily Attendance

#### Check-in Process

1. **Visit the Home Page**: Go to the main page to see the QR code
2. **Go to Scanner**: Click "Scan for Attendance" or visit `/scan`
3. **Enter Private Key**:
   - Paste your private key in the text area
   - Or use "Load Saved Key" if you saved it to the device
4. **Scan QR Code**:
   - Allow camera access when prompted
   - Point your camera at the QR code on the display
   - The system will automatically detect and process it

5. **Confirmation**: You'll see a success message with your check-in time

#### Check-out Process

1. **Scan Again**: When ready to leave, scan the QR code again
2. **Confirmation Dialog**: A popup will appear showing your login time and proposed logout time
3. **Confirm**: Click "Confirm" to complete check-out, or "Cancel" to dismiss
4. **Success**: You'll see confirmation with both in and out times

### Viewing Your Records

1. **Attendance Page**: Visit the attendance records page
2. **Filter Options**: Use date, employee ID, or status filters
3. **Your Records**: Look for your Employee ID in the table

### Security Tips for Employees

- **Protect Your Private Key**: Never share it with anyone
- **Secure Storage**: Save it in an encrypted password manager
- **Device Security**: Use the "Save to Device" feature on trusted devices only
- **QR Code Verification**: Only scan QR codes from official displays
- **Logout**: Always confirm check-out to ensure accurate records

## Administrator Guide

### System Management

#### Employee Registration

1. **Access Registration**: Use the registration page to add new employees
2. **Key Distribution**: Provide employees with their public and private keys securely
3. **Record Keeping**: Maintain a secure record of employee keys (encrypted)

#### Viewing Attendance Records

1. **Attendance Dashboard**: Visit `/attendance` to view all records
2. **Filtering**: Use filters to find specific records:
   - Filter by date
   - Filter by employee ID
   - Filter by status (Present/Late)

3. **Data Export**: Records are stored in JSON format for easy export
4. **Verification Status**: Check the "Verification" column for signature validation

#### System Monitoring

1. **QR Code Display**: Monitor the home page for proper QR generation
2. **Server Logs**: Check console output for system status
3. **Network Access**: Ensure ngrok tunnel is working for external access

### Troubleshooting

#### Common Employee Issues

**"Invalid private key" error**:
- Verify the key is 88 characters long
- Check for copy-paste errors (extra spaces)
- Re-register if key is lost

**"QR code expired" error**:
- QR codes are valid for only 30 seconds
- Try scanning again with a fresh QR code
- Check your device clock is accurate

**"Already used" error**:
- QR codes cannot be reused within 5 minutes
- Wait a few minutes and try again
- This prevents replay attacks

**Camera not working**:
- Allow camera permissions in browser
- Try a different browser (Chrome recommended)
- Check device camera is functional

#### System Issues

**QR code not updating**:
- Check server console for errors
- Verify ngrok connection
- Restart the server if necessary

**Registration failing**:
- Check employee ID is unique
- Verify all required fields are filled
- Check server logs for errors

**Attendance not recording**:
- Verify QR code is current (check timestamp)
- Ensure private key is correct
- Check network connectivity

### Best Practices

#### For Employees

1. **Daily Routine**:
   - Check-in when you arrive at work
   - Check-out when you leave
   - Verify confirmation messages

2. **Key Management**:
   - Save private key in multiple secure locations
   - Use device storage feature for convenience
   - Never email or message your private key

3. **Security Awareness**:
   - Only use trusted devices
   - Be aware of shoulder surfing when entering keys
   - Report any suspicious activity

#### For Administrators

1. **System Maintenance**:
   - Monitor server logs regularly
   - Keep backups of employee data
   - Update system when new versions are available

2. **Security Management**:
   - Rotate server keys periodically
   - Monitor for unusual access patterns
   - Ensure HTTPS in production environments

3. **User Support**:
   - Train employees on proper usage
   - Provide clear instructions for key management
   - Have procedures for lost keys

## Frequently Asked Questions

### What is a private key?

Your private key is like a digital signature that proves your identity. It's unique to you and must be kept secret. The system uses it to verify that attendance markings are authentic.

### Can I mark attendance without the QR code?

No, the QR code contains security information that must be scanned. This prevents unauthorized attendance marking.

### What if I lose my private key?

You'll need to re-register with your administrator. They can generate a new key pair for you.

### Why do I need to confirm check-out?

The confirmation prevents accidental check-outs and ensures you have a chance to review your times before finalizing.

### Is my data secure?

Yes, the system uses cryptographic signatures and secure timestamps. Your private key never leaves your device, and all data is verified on the server.

### Can I check attendance from my phone?

Yes, the system works on mobile browsers. However, camera access and QR scanning work best on devices with good cameras.

## Support

### Getting Help

1. **Check Documentation**: Review this guide and the security documentation
2. **Contact Administrator**: Reach out to your system administrator for issues
3. **Technical Support**: For system problems, check server logs and restart if needed

### Emergency Procedures

**Lost Private Key**:
1. Contact your administrator immediately
2. Re-register to get new keys
3. Previous attendance records remain valid

**System Outage**:
1. Manual attendance tracking may be required
2. Records can be entered retroactively if needed
3. Check server status and network connectivity

## Updates and Changes

- Check the system regularly for updates
- New features may be added over time
- Security improvements are implemented automatically
- Always use the latest version for best security

This system is designed to be secure, user-friendly, and reliable for daily attendance tracking.