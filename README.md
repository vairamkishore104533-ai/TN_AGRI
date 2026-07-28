# AI Agriculture Assistant for Tamil Nadu

An AI-powered smart farming platform specifically designed for farmers in Tamil Nadu. Built with Python Flask, MongoDB, and AI integration.

## Features

- 🤖 **AI Chat Assistant** - Get instant answers about farming in Tamil/English
- 🌾 **Crop Management** - Track crops, planting, and harvest cycles
- 🌤️ **Weather Insights** - Real-time weather data with AI farming advice
- 🧪 **Fertilizer Recommendation** - Personalized NPK and organic fertilizer guidance
- 🔬 **Crop Disease Detection** - Identify diseases by symptoms
- 💧 **Irrigation Planning** - Smart water management recommendations
- 📊 **Market Prices** - Current crop prices and trends in Tamil Nadu
- 🏛️ **Government Schemes** - Latest TN and central agriculture schemes
- 💰 **Expense Tracking** - Income, expenses, and profit analytics
- 📈 **Analytics Dashboard** - Visual insights with charts
- 🌐 **Tamil & English** - Full bilingual support

## Tech Stack

- **Backend:** Python, Flask, Jinja2
- **Database:** MongoDB (PyMongo)
- **Auth:** JWT + bcrypt
- **AI:** Claude API (configurable)
- **Frontend:** HTML5, CSS3, JavaScript, Chart.js

## Installation

1. Clone the repository
2. Install MongoDB and ensure it's running
3. Install Python dependencies:
```bash
pip install -r requirements.txt
```
4. Copy `.env` and configure:
   - Set your SECRET_KEY
   - Set your AI_API_KEY (Claude/OpenAI/Gemini)
   - Set your WEATHER_API_KEY (optional)
5. Run the application:
```bash
python app.py
```
6. Access at `http://localhost:5000`

## Default Admin

- Username: admin
- Password: admin123

## Project Structure

```
AI-Agriculture-Assistant/
├── app.py
├── requirements.txt
├── .env
├── templates/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── routes/
├── models/
├── services/
└── utils/
```
