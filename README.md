# 🤖 Code du Travail Neo - AI System Specifications

[![Specifications](https://img.shields.io/badge/Specifications-3%20Systems-blue.svg)](https://github.com/Pyzeur-ColonyLab/Code-du-Travail-Neo)
[![Architecture](https://img.shields.io/badge/Architecture-Microservices-green.svg)](https://github.com/Pyzeur-ColonyLab/Code-du-Travail-Neo)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Next Generation AI System Architecture** - Modular AI Core with Telegram and Email Services

This repository contains comprehensive specifications for building a modern, scalable AI system architecture based on the original Code du Travail project. The system is designed as three independent microservices that can be deployed separately on Infomaniak cloud infrastructure.

## 🏗️ System Architecture

### Three Independent Services

1. **🤖 Main AI Core System** (`01_MAIN_SYSTEM_SPECIFICATION.txt`)
   - Central API for running various AI models (GGUF, SafeTensor, etc.)
   - Model management and switching capabilities
   - REST API with authentication and rate limiting
   - Redis caching and health monitoring

2. **📱 Telegram Service** (`02_TELEGRAM_SERVICE_SPECIFICATION.txt`)
   - Lightweight Telegram bot service
   - User session management and conversation history
   - Rate limiting and spam protection
   - Professional bot commands and interface

3. **📧 Mail Service** (`03_MAIL_SERVICE_SPECIFICATION.txt`)
   - Comprehensive email processing system
   - IMAP/SMTP integration with professional templates
   - Spam filtering and attachment handling
   - Email threading and automated responses

## 🌐 Domain Configuration

### Recommended DNS Setup for cryptomaltese.com

```dns
# Main AI API
ai-api.cryptomaltese.com.      IN  A       MAIN_SERVER_IP

# Telegram Bot
telegram.cryptomaltese.com.    IN  A       TELEGRAM_SERVER_IP

# Mail Service
mail.cryptomaltese.com.        IN  A       MAIL_SERVER_IP
cryptomaltese.com.             IN  MX  10  mail.cryptomaltese.com.

# Email authentication
cryptomaltese.com.             IN  TXT     "v=spf1 mx ~all"
```

## 🚀 Deployment Strategy

### Recommended Order
1. **Main AI Core System** - Foundation for all services
2. **Telegram Service** - Lightweight, easy to test
3. **Mail Service** - Most complex, requires email infrastructure

### Server Requirements (Infomaniak)

| Service | Instance Type | CPU | RAM | Storage | Purpose |
|---------|---------------|-----|-----|---------|---------|
| Main AI | VPS Pro 4-8 | 4-8 vCPUs | 16-32 GB | 100-200 GB | AI model hosting |
| Telegram | VPS Pro 2-4 | 2-4 vCPUs | 4-8 GB | 50-100 GB | Bot service |
| Mail | VPS Pro 4-8 | 4-8 vCPUs | 8-16 GB | 100-200 GB | Email processing |

## 📋 Specifications Overview

### Main AI Core System
- **Model Support**: GGUF, SafeTensor, ONNX, LoRA adapters
- **API Endpoints**: `/api/v1/generate`, `/api/v1/chat`, `/api/v1/models`
- **Features**: Model switching, caching, authentication, monitoring
- **Technology**: FastAPI, Redis, Docker, Nginx

### Telegram Service
- **Bot Commands**: `/start`, `/help`, `/status`, `/reset`, `/models`
- **Features**: User sessions, conversation history, rate limiting
- **Technology**: python-telegram-bot, FastAPI, PostgreSQL, Redis

### Mail Service
- **Email Support**: IMAP/SMTP, HTML templates, attachments, threading
- **Features**: Spam filtering, professional formatting, queue management
- **Technology**: aioimaplib, aiosmtplib, Jinja2, PostgreSQL, Redis

## 🔧 Integration Points

All services communicate with the Main AI Core System via REST API:

```json
{
  "model": "mistral-7b-instruct",
  "prompt": "User question here",
  "max_tokens": 512,
  "temperature": 0.7,
  "stream": false
}
```

## 📊 Monitoring and Health

Each service includes:
- **Health Checks**: Service connectivity and status
- **Metrics**: Performance and usage statistics
- **Logging**: Structured logging with error tracking
- **Alerting**: Automated alerts for system issues

## 🔒 Security Features

- **API Key Authentication**: Secure access to AI core system
- **Rate Limiting**: Prevent abuse and manage costs
- **Input Validation**: Sanitize all user inputs
- **SSL/TLS**: Encrypted communications
- **Data Privacy**: GDPR compliance and data retention policies

## 🧪 Testing Strategy

- **Unit Tests**: Individual component testing
- **Integration Tests**: Service-to-service communication
- **Load Testing**: Performance under high traffic
- **Security Tests**: Vulnerability assessment

## 📈 Scalability

- **Horizontal Scaling**: Multiple service instances
- **Load Balancing**: Distribute traffic across instances
- **Caching**: Redis-based response caching
- **Queue Management**: Asynchronous processing

## 🚀 Quick Start

1. **Review Specifications**: Read the three specification files
2. **Plan Infrastructure**: Choose server configurations
3. **Setup DNS**: Configure domain records
4. **Deploy Services**: Follow deployment guides in each specification
5. **Test Integration**: Verify service communication
6. **Monitor Performance**: Set up monitoring and alerting

## 📚 Documentation

Each specification file contains:
- Detailed technical requirements
- Deployment configurations
- Environment variables
- Docker compose files
- Testing requirements
- Success criteria

## 🤝 Contributing

This repository contains specifications for coding agents. To contribute:
1. Review existing specifications
2. Suggest improvements or additional features
3. Update specifications based on implementation feedback
4. Add new service specifications as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- **Original Code du Travail**: [Repository](https://github.com/Pyzeur-ColonyLab/Code-du-Travail)
- **Infomaniak Cloud**: [Documentation](https://www.infomaniak.com/fr/support/faq/admin2/public-cloud)
- **Docker Mailserver**: [Documentation](https://docker-mailserver.github.io/docker-mailserver/)

---

**Built with ❤️ by ColonyLab** 