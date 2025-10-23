# Development Guide

This guide provides information for developers who want to contribute to or extend the Phantom Wallet Attendance System.

## Development Setup

### Prerequisites

- **Python 3.8+**: Required for Flask and cryptographic operations
- **pip**: Python package manager
- **Git**: Version control
- **ngrok**: For public access during development (optional)
- **Modern Web Browser**: For testing the web interface

### Environment Setup

1. **Clone the Repository**:
```bash
git clone <repository-url>
cd phantom_wallet_attendance
```

2. **Create Virtual Environment** (Recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set Environment Variables** (Optional):
```bash
export NGROK_AUTH_TOKEN="your-ngrok-token"
```

5. **Run the Application**:
```bash
python app.py
```

6. **Access the Application**:
   - Local: http://localhost:5000
   - Public (with ngrok): Check console output for ngrok URL

## Project Structure

```
phantom_wallet_attendance/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── run.sh                # Shell script for running
├── setup.sh              # Setup script
├── data/                 # Data storage
│   ├── employees.json    # Employee records
│   └── attendance.json   # Attendance logs
├── keys/                 # Server keys (auto-generated)
├── backups/              # Backup files (auto-generated)
└── docs/                 # Documentation
    ├── README.md         # Project overview
    ├── API.md            # API documentation
    ├── SECURITY.md       # Security features
    ├── ARCHITECTURE.md   # System design
    ├── USER_GUIDE.md     # User manual
    └── DEVELOPMENT.md    # This file
```

## Code Organization

### Main Application (`app.py`)

#### Key Sections

1. **Configuration** (Lines 15-33):
   - Directory setup
   - Constants (intervals, grace periods)
   - ngrok configuration

2. **Data Management** (Lines 42-71):
   - JSON file operations
   - Employee and attendance data handling

3. **Cryptography** (Lines 73-120):
   - Ed25519 key generation
   - Message signing and verification

4. **QR Code Generation** (Lines 163-196):
   - Dynamic QR code creation
   - Time-based content generation

5. **Web Interface** (Lines 198-1233):
   - HTML templates for all pages
   - JavaScript for client-side operations

6. **Flask Routes** (Lines 1235-1426):
   - HTTP endpoints
   - API handlers

#### Important Functions

- `generate_ed25519_keypair()`: Creates cryptographic key pairs
- `sign_message()` / `verify_signature()`: Cryptographic operations
- `generate_qr_data()`: Creates QR code content
- `load_attendance()` / `save_attendance()`: Data persistence
- `api_attendance()`: Main attendance processing logic

## Development Workflow

### Making Changes

1. **Create Feature Branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Implement Changes**:
   - Follow existing code style
   - Add comments for complex logic
   - Update documentation if needed

3. **Test Thoroughly**:
   - Test all user flows
   - Verify cryptographic operations
   - Check error handling

4. **Update Documentation**:
   - Update README for new features
   - Add API documentation for new endpoints
   - Update user guide if UI changes

5. **Submit Changes**:
```bash
git add .
git commit -m "Add feature description"
git push origin feature/your-feature-name
```

### Code Style

- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use modern ES6+ syntax
- **HTML/CSS**: Semantic markup with responsive design
- **Comments**: Add docstrings for functions and complex logic
- **Naming**: Use descriptive names (snake_case for Python, camelCase for JS)

## Testing

### Manual Testing Checklist

#### Registration
- [ ] New employee registration works
- [ ] Key pair generation produces valid keys
- [ ] Duplicate employee ID is rejected
- [ ] All fields are validated

#### QR Code System
- [ ] QR codes generate correctly
- [ ] QR codes update every 10 seconds
- [ ] QR codes display properly in browser
- [ ] QR codes contain correct data

#### Attendance Scanning
- [ ] Camera access works
- [ ] QR scanning detects codes correctly
- [ ] Private key validation works
- [ ] Signature verification succeeds
- [ ] Check-in records are created
- [ ] Check-out confirmation appears
- [ ] Check-out updates records correctly

#### Security Features
- [ ] Invalid signatures are rejected
- [ ] Expired QR codes are rejected
- [ ] Replay attacks are prevented
- [ ] Time validation works correctly

#### Data Management
- [ ] Attendance records are saved correctly
- [ ] Employee data persists
- [ ] Backup files are created
- [ ] Data integrity is maintained

### Automated Testing

Currently, the project uses manual testing. Consider adding:

- **Unit Tests**: For cryptographic functions
- **Integration Tests**: For API endpoints
- **End-to-End Tests**: For complete user flows

**Recommended Testing Tools**:
- **pytest**: For Python unit tests
- **Selenium**: For browser automation
- **Postman**: For API testing

## Debugging

### Common Issues

#### Cryptographic Errors
- **"Invalid signature"**: Check key formats and message content
- **"Key derivation failed"**: Verify private key length (64 bytes)
- **"Base58 decode error"**: Check for invalid characters in keys

#### QR Code Issues
- **"QR not detected"**: Check camera permissions and lighting
- **"Invalid QR format"**: Verify QR generation and display
- **"QR expired"**: Check system clock synchronization

#### Network Problems
- **"Connection refused"**: Verify Flask server is running
- **"ngrok tunnel failed"**: Check ngrok token and internet connection
- **"CORS errors"**: Check browser console for cross-origin issues

### Debug Tools

1. **Browser Developer Tools**:
   - Console for JavaScript errors
   - Network tab for API requests
   - Application tab for localStorage inspection

2. **Server Logs**:
   - Check Flask console output
   - Monitor for error messages
   - Verify attendance recording

3. **Network Analysis**:
   - Use browser network tab
   - Check request/response data
   - Verify signature contents

## Contributing Guidelines

### Code Standards

1. **Security First**: Always consider security implications
2. **Documentation**: Update docs for any changes
3. **Testing**: Test all changes thoroughly
4. **Backwards Compatibility**: Maintain compatibility when possible

### Pull Request Process

1. **Describe Changes**: Explain what was changed and why
2. **Include Tests**: Add tests for new functionality
3. **Update Documentation**: Update relevant docs
4. **Code Review**: Address any review comments

### Feature Development

1. **Plan Architecture**: Consider how changes fit into existing design
2. **Security Review**: Get security review for crypto-related changes
3. **Performance Impact**: Consider performance implications
4. **User Experience**: Ensure changes improve or maintain UX

## Deployment

### Development Deployment

1. **Local Testing**: Test on localhost:5000
2. **ngrok Tunnel**: Use for external testing
3. **Cross-Browser Testing**: Test on different browsers

### Production Deployment

1. **Server Setup**:
   - Use production WSGI server (Gunicorn)
   - Configure HTTPS
   - Set up proper firewall rules

2. **Database Migration**:
   - Consider migrating from JSON to database
   - Set up backup procedures
   - Implement data retention policies

3. **Security Hardening**:
   - Use HTTPS everywhere
   - Implement rate limiting
   - Set up monitoring and alerting

4. **Performance Optimization**:
   - Enable caching for QR codes
   - Optimize database queries
   - Consider CDN for static assets

## API Development

### Adding New Endpoints

1. **Define Route**: Add Flask route decorator
2. **Implement Logic**: Add request handling and validation
3. **Add Documentation**: Update API.md
4. **Test Thoroughly**: Verify functionality and security

### Modifying Existing Endpoints

1. **Maintain Compatibility**: Consider backwards compatibility
2. **Update Documentation**: Reflect changes in API docs
3. **Test Impact**: Verify existing functionality still works
4. **Security Review**: Check for security implications

## Security Considerations

### Development Security

1. **Key Management**:
   - Never commit private keys to version control
   - Use environment variables for sensitive data
   - Implement key rotation procedures

2. **Code Security**:
   - Review cryptographic implementations
   - Validate all inputs
   - Use secure coding practices

3. **Testing Security**:
   - Test with invalid inputs
   - Verify error handling doesn't leak information
   - Check for timing attacks

## Performance Optimization

### Current Optimizations

- QR codes cached in memory
- Efficient JSON operations
- Minimal database queries

### Potential Improvements

1. **Caching**:
   - Cache employee lookups
   - Cache recent attendance records
   - Implement Redis for session storage

2. **Database**:
   - Migrate to PostgreSQL for better performance
   - Add indexes on frequently queried fields
   - Implement connection pooling

3. **Frontend**:
   - Minimize JavaScript bundle size
   - Optimize images and assets
   - Implement lazy loading

## Monitoring and Logging

### Logging Setup

The application includes basic logging. Consider enhancing with:

1. **Structured Logging**: JSON format for better parsing
2. **Log Rotation**: Prevent log files from growing too large
3. **Security Monitoring**: Alert on suspicious activities

### Monitoring Metrics

- **Attendance Success Rate**: Track successful vs failed attendance markings
- **Performance Metrics**: Response times for API calls
- **Security Events**: Failed signature verifications, replay attempts
- **System Health**: Server uptime, error rates

## Troubleshooting

### Development Issues

**Import Errors**:
- Ensure all dependencies are installed
- Check Python version compatibility
- Verify package versions in requirements.txt

**Cryptographic Issues**:
- Verify key formats and lengths
- Check message encoding (UTF-8)
- Test with known good data

**Frontend Issues**:
- Check browser console for JavaScript errors
- Verify camera permissions
- Test on different devices/browsers

### Performance Issues

**Slow QR Generation**:
- Check server resources
- Consider caching strategies
- Optimize image generation

**Database Bottlenecks**:
- Monitor file I/O operations
- Consider database migration
- Implement data archiving

## Version Control

### Git Workflow

1. **Main Branch**: Always deployable
2. **Feature Branches**: For new development
3. **Release Branches**: For version releases
4. **Hotfix Branches**: For urgent fixes

### Commit Guidelines

- **Descriptive Messages**: Explain what and why
- **Small Commits**: Break large changes into logical commits
- **Documentation**: Include doc updates in feature commits

## License and Attribution

This project is open source. When contributing:

1. **Respect License**: Follow the project's license terms
2. **Attribute Sources**: Credit any external libraries or code
3. **Maintain Compatibility**: Ensure changes work with existing dependencies

## Getting Help

### Development Resources

1. **Documentation**: Check the docs/ folder for detailed information
2. **Code Comments**: Review inline comments for implementation details
3. **Issues**: Check existing issues for similar problems
4. **Community**: Consider opening discussions for complex problems

### Contact

For development questions or issues:
1. Check existing documentation
2. Search issues and discussions
3. Create a new issue with detailed information
4. Contact maintainers directly if needed

## Future Development

### Roadmap

1. **Enhanced Security**: Hardware security modules, multi-signature
2. **Mobile Apps**: Native iOS/Android applications
3. **Advanced Features**: Geolocation, face recognition
4. **Scalability**: Microservices, cloud deployment
5. **Analytics**: Reporting and dashboard features

### Contributing Ideas

- **Testing Framework**: Automated test suite
- **CI/CD Pipeline**: Automated deployment
- **Internationalization**: Multi-language support
- **Accessibility**: WCAG compliance
- **Performance**: Real-time optimizations

This development guide should help you understand the codebase and contribute effectively to the project.