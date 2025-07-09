# 📋 Repository Summary - Code du Travail Neo

## 🎯 Repository Overview

This repository contains comprehensive specifications for building a modern, scalable AI system architecture based on the original Code du Travail project. The system is designed as three independent microservices that can be deployed separately on Infomaniak cloud infrastructure.

## 📁 Repository Structure

```
Code-du-Travail-Neo/
├── README.md                              # Main repository documentation
├── LICENSE                                # MIT License
├── .gitignore                             # Git ignore rules
├── DEPLOYMENT_GUIDE.md                    # Step-by-step deployment guide
├── REPOSITORY_SUMMARY.md                  # This file
├── init_repo.sh                           # Git repository initialization script
├── 01_MAIN_SYSTEM_SPECIFICATION.txt       # Main AI Core System specification
├── 02_TELEGRAM_SERVICE_SPECIFICATION.txt  # Telegram Service specification
└── 03_MAIL_SERVICE_SPECIFICATION.txt      # Mail Service specification
```

## 🏗️ System Architecture

### Three Independent Microservices

1. **🤖 Main AI Core System** (`01_MAIN_SYSTEM_SPECIFICATION.txt`)
   - **Purpose**: Central API for running various AI models
   - **Server**: VPS Pro 4-8 (4-8 vCPUs, 16-32 GB RAM, 100-200 GB SSD)
   - **Domain**: ai-api.cryptomaltese.com
   - **Features**: Model management, REST API, caching, authentication

2. **📱 Telegram Service** (`02_TELEGRAM_SERVICE_SPECIFICATION.txt`)
   - **Purpose**: Telegram bot for AI-powered chat
   - **Server**: VPS Pro 2-4 (2-4 vCPUs, 4-8 GB RAM, 50-100 GB SSD)
   - **Domain**: telegram.cryptomaltese.com
   - **Features**: Bot commands, session management, rate limiting

3. **📧 Mail Service** (`03_MAIL_SERVICE_SPECIFICATION.txt`)
   - **Purpose**: Email processing with AI responses
   - **Server**: VPS Pro 4-8 (4-8 vCPUs, 8-16 GB RAM, 100-200 GB SSD)
   - **Domain**: mail.cryptomaltese.com
   - **Features**: IMAP/SMTP, templates, spam filtering

## 🚀 Quick Start

### 1. Initialize Git Repository

```bash
cd Code-du-Travail-Neo
chmod +x init_repo.sh
./init_repo.sh
```

### 2. Set Up Remote Repository

```bash
# Replace with your actual repository URL
git remote add origin https://github.com/your-username/Code-du-Travail-Neo.git
git branch -M main
git push -u origin main
```

### 3. Review Specifications

- Read `01_MAIN_SYSTEM_SPECIFICATION.txt` for the AI core system
- Read `02_TELEGRAM_SERVICE_SPECIFICATION.txt` for the Telegram bot
- Read `03_MAIL_SERVICE_SPECIFICATION.txt` for the email service

### 4. Follow Deployment Guide

- Read `DEPLOYMENT_GUIDE.md` for detailed deployment instructions
- Start with Phase 1 (Main AI Core System)
- Deploy services in the recommended order

## 📋 Specifications Overview

### Main AI Core System
- **Model Support**: GGUF, SafeTensor, ONNX, LoRA adapters
- **API Endpoints**: `/api/v1/generate`, `/api/v1/chat`, `/api/v1/models`
- **Technology Stack**: FastAPI, Redis, Docker, Nginx
- **Key Features**: Model switching, caching, authentication, monitoring

### Telegram Service
- **Bot Commands**: `/start`, `/help`, `/status`, `/reset`, `/models`
- **Technology Stack**: python-telegram-bot, FastAPI, PostgreSQL, Redis
- **Key Features**: User sessions, conversation history, rate limiting

### Mail Service
- **Email Support**: IMAP/SMTP, HTML templates, attachments, threading
- **Technology Stack**: aioimaplib, aiosmtplib, Jinja2, PostgreSQL, Redis
- **Key Features**: Spam filtering, professional formatting, queue management

## 🌐 Domain Configuration

### DNS Records for cryptomaltese.com

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

## 📊 Deployment Phases

### Phase 1: Main AI Core System (Priority: HIGH)
- Foundation for all other services
- Deploy first to establish the API infrastructure
- Test model loading and API endpoints

### Phase 2: Telegram Service (Priority: MEDIUM)
- Lightweight service, easy to test
- Requires Main AI Core System to be operational
- Test bot commands and AI integration

### Phase 3: Mail Service (Priority: MEDIUM)
- Complex service, requires email infrastructure
- Requires Main AI Core System to be operational
- Test email processing and AI responses

## 🔒 Security Features

- **API Key Authentication**: Secure access to AI core system
- **Rate Limiting**: Prevent abuse and manage costs
- **SSL/TLS**: Encrypted communications
- **Input Validation**: Sanitize all user inputs
- **Data Privacy**: GDPR compliance and data retention policies

## 📈 Scalability Considerations

- **Horizontal Scaling**: Multiple service instances
- **Load Balancing**: Distribute traffic across instances
- **Caching**: Redis-based response caching
- **Queue Management**: Asynchronous processing

## 🧪 Testing Strategy

- **Unit Tests**: Individual component testing
- **Integration Tests**: Service-to-service communication
- **Load Testing**: Performance under high traffic
- **Security Tests**: Vulnerability assessment

## 📞 Support and Documentation

- **Specification Files**: Detailed technical requirements
- **Deployment Guide**: Step-by-step deployment instructions
- **Troubleshooting**: Common issues and solutions
- **Monitoring**: Health checks and performance metrics

## 🎯 Success Criteria

1. **Performance**: API response time < 2-3 seconds
2. **Reliability**: 99.9% uptime with proper monitoring
3. **Scalability**: Support for 1000+ concurrent users
4. **Security**: No security vulnerabilities in production
5. **Monitoring**: Complete observability of system health

## 🔗 Related Projects

- **Original Code du Travail**: [Repository](https://github.com/Pyzeur-ColonyLab/Code-du-Travail)
- **Infomaniak Cloud**: [Documentation](https://www.infomaniak.com/fr/support/faq/admin2/public-cloud)
- **Docker Mailserver**: [Documentation](https://docker-mailserver.github.io/docker-mailserver/)

---

**Built with ❤️ by ColonyLab**

*This repository contains specifications for coding agents to build a modern AI system architecture.* 