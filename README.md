# 🚀 Habit Tracker

*A clean, mobile-friendly habit tracker with streaks and analytics*

## 🔥 Features
| Feature          | Description                                  |
|------------------|----------------------------------------------|
| **📝 Log Habits** | Add habits with mood/weather tracking        |
| **✅ Completion**| Toggle checkmarks for completed habits       |
| **📊 Stats**     | Streaks (current/longest) & completion rates |
| **🌓 Themes**    | Dark/light mode toggle                       |
| **🔔 Notify**    | Desktop reminders                            |

## 🛠️ Quick Start
```bash
# Clone & run the mobile app
git clone https://github.com/ansa111/habit-tracker
cd habit-tracker
pip install -r requirements.txt
python mobile_fixed.py

📱 Mobile UI Guide
Add Habit: Type in the input box → Tap "ADD"

Complete: Check the circle ✔️

Delete: Tap the 🗑️ icon

Switch Theme: Use the 🌓 button

🌦️ Weather Setup
Get a free API key from OpenWeatherMap

Create .env file:

env
WEATHER_API_KEY=your_key_here
📜 CLI Commands
bash
# Log a completed habit with mood
python habittracker.py --habit "Yoga" --completed --mood happy

# Generate weekly report
python habittracker.py --report
🤝 Contribute
Report bugs via Issues

Submit PRs for new features!

MIT © Ansa111
Icons by KivyMD | Weather by OpenWeatherMap
