# LastPerson07x-BannerBot v3.0

Professional Telegram banner generation bot built with Aiogram 3.4 and FastAPI.

## ✨ Features

- 🎨 Professional HD banners (1080x1920)
- 📱 4 pre-built templates (your samples included)
- ✍️ Custom text overlay with professional strokes
- 🚀 Fast generation (~2 seconds)
- 👥 User tracking & statistics
- 🚫 Admin ban system
- 📊 Admin dashboard
- 🐳 Docker + Render ready
- 🗄️ MongoDB integration

## 🚀 Quick Start

### Local Development

1. **Clone repo**

```bash
git clone https://github.com/yourusername/LastPerson07x-BannerBot
cd LastPerson07x-BannerBot
```
Create environment

bash
cp .env.example .env
# Edit .env with your values
Add templates

bash
# Copy your 4 image files to templates/
cp template1.jpg template2.jpg template3.jpg template4.jpg templates/
Run with Docker

bash
docker build -t bannerbot .
docker run -p 10000:10000 --env-file .env bannerbot
Render Deployment
Fork this repository

Connect GitHub to Render

Create Web Service:

Build: docker build .

Start: python keepalive.py

Port: 10000

Set environment variables:

BOT_TOKEN

MONGO_URI

ADMIN_IDS

Deploy!

📋 Environment Variables
text
BOT_TOKEN=your_telegram_bot_token
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/bannerbot
ADMIN_IDS=123456789,987654321
PORT=10000
🎯 Admin Commands
text
/admin - View admin panel
/ban_user <id> - Ban user
/unban_user <id> - Unban user
/logs - View logs
🏗️ Project Structure
keepalive.py - FastAPI web server + bot starter

bot.py - Bot initialization

config.py - Configuration

database/mongo.py - MongoDB operations

handlers/ - Telegram interaction

services/ - Business logic

engine/ - Image generation

middlewares/ - Auth & bans

utils/ - Utilities

📊 Database Collections
users - User statistics

bans - Banned user IDs

logs - Action audit trail

🔌 External APIs
Picsum Photos (backgrounds)

Telegram Bot API

MongoDB Atlas

📝 License
Made by @LastPerson07

🤝 Support
For issues, contact @LastPerson07

text

***

## 🎯 **DEPLOYMENT CHECKLIST**

1. **Create all directories:**
```bash
mkdir -p templates assets logs database handlers services engine middlewares utils
Copy your images:

bash
cp image1.jpg templates/template1.jpg
cp image2.jpg templates/template2.jpg
cp image3.jpg templates/template3.jpg
cp image4.jpg templates/template4.jpg
Create .env file:

bash
cp .env.example .env
# Edit with your values
Test locally:

bash
docker build -t bannerbot .
docker run -p 10000:10000 --env-file .env bannerbot
Deploy to Render:

Push to GitHub

Connect Render to repo

Deploy as Web Service