import click
import sqlite3
from datetime import datetime
import requests
import os
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

# Initialize database
conn = sqlite3.connect("habits.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit TEXT,
        completed BOOLEAN,
        date TEXT,
        weather TEXT,
        mood TEXT
    )
""")
conn.commit()

def get_weather(city="Berlin"):
    """Fetch weather data with robust error handling"""
    API_KEY = "290895ce430b9d6907ba3226a33e4130"
    if not API_KEY:
        click.echo("⚠️ Weather disabled: No API key provided", err=True)
        return "unavailable"

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        desc = data['weather'][0]['description']
        temp = data['main']['temp']
        return f"{desc} ({temp}°C)"
    except requests.exceptions.RequestException as e:
        click.echo(f"⚠️ Weather error: {str(e)}", err=True)
        return "unavailable"

def export_data(format_type):
    """Export habit data to CSV or JSON"""
    data = conn.execute("SELECT * FROM habits").fetchall()
    
    if format_type == "csv":
        import csv
        with open('habits_export.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'habit', 'completed', 'date', 'weather', 'mood'])
            writer.writerows(data)
        click.echo(f"📤 Data exported to habits_export.csv")
    
    elif format_type == "json":
        import json
        export = [dict(zip(['id', 'habit', 'completed', 'date', 'weather', 'mood'], row)) 
                 for row in data]
        with open('habits_export.json', 'w') as f:
            json.dump(export, f, indent=2)
        click.echo(f"📤 Data exported to habits_export.json")
    
    else:
        click.echo("❌ Invalid format. Use 'csv' or 'json'", err=True)

def generate_report():
    """Generate a weekly habit report with streaks"""
    data = conn.execute("""
        SELECT date, habit, completed, mood 
        FROM habits 
        WHERE date >= date('now', '-7 days')
        ORDER BY date
    """).fetchall()
    
    if not data:
        click.echo("\nNo data from the past 7 days")
        return

    # Streak calculation
    streaks = conn.execute("""
        WITH streaks AS (
            SELECT date, 
                   date(date, '-' || ROW_NUMBER() OVER (ORDER BY date) || ' days') as streak_group
            FROM habits 
            WHERE completed = 1
            GROUP BY date
        )
        SELECT streak_group, COUNT(*) as streak_length
        FROM streaks
        GROUP BY streak_group
        ORDER BY streak_length DESC
        LIMIT 1
    """).fetchone()

    click.echo("\n📈 WEEKLY HABIT REPORT")
    click.echo("="*40)
    
    # Completion rate
    completed = sum(1 for row in data if row[2])
    click.echo(f"✅ Completion Rate: {completed}/{len(data)} ({completed/len(data):.0%})")
    
    # Mood stats
    moods = [row[3] for row in data if row[3] != "neutral"]
    if moods:
        click.echo(f"😊 Most Common Mood: {max(set(moods), key=moods.count)}")
    
    # Habit frequency
    habits = [row[1] for row in data]
    click.echo(f"🔁 Most Frequent Habit: {max(set(habits), key=habits.count)}")
    
    # Streak info
    if streaks and streaks[1] > 1:
        click.echo(f"🔥 Longest Streak: {streaks[1]} days")
    
    click.echo("="*40)

def show_visualization():
    """Show visualization if matplotlib is available"""
    if plt is None:
        click.echo("\n📊 Install matplotlib for visual reports: 'pip install matplotlib'")
        return
    
    data = conn.execute("""
        SELECT date, COUNT(*) as count 
        FROM habits 
        WHERE completed = 1
        GROUP BY date
        ORDER BY date
    """).fetchall()
    
    if not data:
        click.echo("No completion data to visualize")
        return
    
    dates = [row[0] for row in data]
    counts = [row[1] for row in data]
    
    plt.figure(figsize=(10, 4))
    plt.bar(dates, counts, color='skyblue')
    plt.title("Habit Completions This Week")
    plt.xlabel("Date")
    plt.ylabel("Completed Habits")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("report.png")
    click.echo("📊 Visualization saved as report.png")
    plt.close()

@click.command()
@click.option("--habit", help="Name of the habit")
@click.option("--completed", is_flag=True, help="Mark habit as completed")
@click.option("--mood", default="neutral",
              type=click.Choice(["happy", "neutral", "tired", "stressed"]),
              help="Your current mood")
@click.option("--skip-weather", is_flag=True, help="Skip weather API check")
@click.option("--report", is_flag=True, help="Generate weekly report")
@click.option("--export", 
              type=click.Choice(["csv", "json"]),
              help="Export data to CSV or JSON")
def log_habit(habit, completed, mood, skip_weather, report, export):
    """Main function to log habits with advanced tracking"""
    if export:
        export_data(export)
        return
        
    if report:
        generate_report()
        show_visualization()
        return

    try:
        date = datetime.now().strftime("%Y-%m-%d")
        weather = "disabled" if skip_weather else get_weather()
        
        if weather != "unavailable" and "rain" in weather.lower() and "walk" in habit.lower():
            click.echo(f"\n⛈️ Weather Alert: {weather} - Consider indoor exercise!")
        
        cursor.execute(
            "INSERT INTO habits (habit, completed, date, weather, mood) VALUES (?, ?, ?, ?, ?)",
            (habit, completed, date, weather, mood)
        )
        conn.commit()
        
        if mood != "neutral":
            cursor.execute(
                "SELECT COUNT(*) FROM habits WHERE mood = ? AND completed = ?",
                (mood, completed)
            )
            count = cursor.fetchone()[0]
            click.echo(f"\n📊 Mood Insight: When {mood}, you've {'completed' if completed else 'skipped'} this habit {count} times")
        
        click.echo(f"\n✅ Logged: {habit}")
        click.echo(f"   ├─ Status: {'Completed' if completed else 'Skipped'}")
        click.echo(f"   ├─ Mood: {mood}")
        click.echo(f"   └─ Weather: {weather}")
        
    except sqlite3.Error as e:
        click.echo(f"❌ Database error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)

if __name__ == "__main__":
    print("\n" + "="*40)
    print("HABIT TRACKER v1.4".center(40))
    print("="*40)
    log_habit()