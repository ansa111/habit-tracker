from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (StringProperty, BooleanProperty, 
                           NumericProperty, ListProperty, ObjectProperty)
from kivy.clock import Clock
from kivy.metrics import dp
from datetime import datetime, timedelta
import sqlite3
import requests
import json
import os
from plyer import notification
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineAvatarIconListItem, ILeftBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
Window.size = (400, 700)

KV = '''
#:import hex kivy.utils.get_color_from_hex
#:import Clock kivy.clock.Clock

<HabitItem>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(70)
    padding: dp(10)
    spacing: dp(15)
    md_bg_color: app.theme_cls.bg_dark if root.completed else app.theme_cls.bg_normal
    radius: dp(10)
    
    MDCheckbox:
        id: chk
        active: root.completed
        on_active: app.toggle_habit(root.habit_id, self.active)
        size_hint: None, None
        size: dp(40), dp(40)
    
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(5)
        
        MDLabel:
            text: root.habit_text
            font_style: 'Subtitle1'
            theme_text_color: 'Primary'
            adaptive_height: True
        
        MDBoxLayout:
            size_hint_y: None
            height: dp(24)
            spacing: dp(10)
            
            MDIcon:
                icon: root.mood_icon
                size_hint: None, None
                size: dp(20), dp(20)
                theme_text_color: 'Secondary'
            
            MDIcon:
                icon: root.weather_icon
                size_hint: None, None
                size: dp(20), dp(20)
                theme_text_color: 'Secondary'
            
            MDLabel:
                text: root.formatted_date
                font_style: 'Caption'
                theme_text_color: 'Secondary'
                size_hint_x: 0.6
    
    MDIconButton:
        icon: 'delete'
        size_hint: None, None
        size: dp(40), dp(40)
        pos_hint: {'center_y': 0.5}
        on_release: app.delete_habit(root.habit_id)
        theme_text_color: "Error"

MDScreen:
    md_bg_color: app.theme_cls.bg_normal
    
    MDBoxLayout:
        orientation: 'vertical'
        spacing: dp(10)
        padding: dp(15)
        
        # Header
        MDBoxLayout:
            size_hint_y: None
            height: dp(60)
            spacing: dp(10)
            
            MDLabel:
                text: "Habit Tracker"
                font_style: 'H4'
                theme_text_color: 'Primary'
                bold: True
                size_hint_x: 0.6
            
            MDRaisedButton:
                id: theme_btn
                text: "DARK" if app.theme_cls.theme_style == 'Light' else "LIGHT"
                on_release: app.switch_theme()
                size_hint_x: None
                width: dp(80)
            
            MDRaisedButton:
                text: "REPORT"
                on_release: app.show_report()
                size_hint_x: None
                width: dp(80)
        
        # Stats Dashboard
        ScrollView:
            size_hint_y: None
            height: dp(120)
            do_scroll_x: True
            do_scroll_y: False
            
            MDBoxLayout:
                id: stats_container
                size_hint_x: None
                width: self.minimum_width
                spacing: dp(10)
                padding: dp(5)
        
        # New Habit Input
        MDCard:
            size_hint_y: None
            height: dp(180)
            radius: dp(15)
            padding: dp(15)
            spacing: dp(10)
            
            MDTextField:
                id: habit_input
                hint_text: "What habit did you do today?"
                mode: "rectangle"
                size_hint_y: None
                height: dp(48)
            
            MDBoxLayout:
                size_hint_y: None
                height: dp(48)
                spacing: dp(10)
                
                MDCheckbox:
                    id: completed_check
                    size_hint: None, None
                    size: dp(40), dp(40)
                    active: True
                
                MDLabel:
                    text: "Completed"
                    size_hint_x: None
                    width: dp(100)
                
                Spinner:
                    id: mood_spinner
                    text: "neutral"
                    values: ["happy", "neutral", "tired", "stressed"]
                    size_hint_x: 0.5
            
            MDRaisedButton:
                text: "ADD HABIT"
                on_release: app.add_habit()
                pos_hint: {'center_x': 0.5}
        
        # Habits List with Pagination Controls
        BoxLayout:
            orientation: 'vertical'
            spacing: dp(10)
            
            ScrollView:
                MDBoxLayout:
                    id: habits_container
                    orientation: 'vertical'
                    spacing: dp(10)
                    size_hint_y: None
                    height: self.minimum_height
            
            MDBoxLayout:
                size_hint_y: None
                height: dp(50)
                spacing: dp(10)
                padding: dp(5)
                
                MDRaisedButton:
                    text: "Previous"
                    on_release: app.prev_page()
                    disabled: app.current_page == 0
                    size_hint_x: 0.5
                
                MDLabel:
                    text: f"Page {app.current_page + 1}"
                    halign: 'center'
                    size_hint_x: 0.2
                
                MDRaisedButton:
                    text: "Next"
                    on_release: app.next_page()
                    disabled: app.is_last_page
                    size_hint_x: 0.5
'''

class HabitItem(BoxLayout):
    habit_id = StringProperty()
    habit_text = StringProperty()
    completed = BooleanProperty()
    weather = StringProperty()
    mood = StringProperty()
    date = StringProperty()
    
    @property
    def mood_icon(self):
        return {
            'happy': 'emoticon-happy-outline',
            'neutral': 'emoticon-neutral-outline',
            'tired': 'emoticon-tired-outline',
            'stressed': 'emoticon-angry-outline'
        }.get(self.mood, 'emoticon-neutral-outline')
    
    @property
    def weather_icon(self):
        if not self.weather:
            return 'weather-sunny'
        if 'rain' in self.weather.lower():
            return 'weather-pouring'
        elif 'cloud' in self.weather.lower():
            return 'weather-partly-cloudy'
        return 'weather-sunny'
    
    @property
    def formatted_date(self):
        try:
            dt = datetime.strptime(self.date, "%Y-%m-%d %H:%M")
            return dt.strftime("%b %d, %H:%M")
        except:
            return self.date

class HabitTracker(MDApp):
    streaks = ListProperty([0, 0, 0])  # [current, best, total]
    current_page = NumericProperty(0)
    habits_per_page = NumericProperty(10)
    is_last_page = BooleanProperty(False)
    
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.material_style = "M3"
        self.init_db()
        return Builder.load_string(KV)
    
    def on_start(self):
        self.load_habits()
        self.update_stats()
        Clock.schedule_once(self.setup_ui, 0.5)
    
    def setup_ui(self, dt):
        self.update_weather()
    
    def init_db(self):
        self.conn = sqlite3.connect("habits.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit TEXT,
                completed BOOLEAN,
                date TEXT,
                weather TEXT,
                mood TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        self.conn.commit()
    
    def add_habit(self):
        habit = self.root.ids.habit_input.text.strip()
        if habit:
            try:
                date = datetime.now().strftime("%Y-%m-%d %H:%M")
                completed = self.root.ids.completed_check.active
                mood = self.root.ids.mood_spinner.text
                weather = self.update_weather()
                
                self.cursor.execute(
                    "INSERT INTO habits VALUES (NULL, ?, ?, ?, ?, ?)",
                    (habit, completed, date, weather, mood)
                )
                self.conn.commit()
                
                self.root.ids.habit_input.text = ""
                self.current_page = 0
                self.load_habits()
                self.update_stats()
                
                self.show_notification(
                    "Habit Added",
                    f"'{habit}' logged successfully!"
                )
            except Exception as e:
                print(f"Database error: {e}")
                self.show_notification(
                    "Error",
                    f"Failed to add habit: {str(e)}"
                )
    
    def delete_habit(self, habit_id):
        try:
            self.cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
            self.conn.commit()
            self.load_habits()
            self.update_stats()
        except Exception as e:
            print(f"Error deleting habit: {e}")
            self.show_notification(
                "Error",
                f"Failed to delete habit: {str(e)}"
            )
    
    def toggle_habit(self, habit_id, completed):
        try:
            self.cursor.execute(
                "UPDATE habits SET completed = ? WHERE id = ?",
                (completed, habit_id)
            )
            self.conn.commit()
            self.update_stats()
        except Exception as e:
            print(f"Error toggling habit: {e}")
    
    def load_habits(self):
        container = self.root.ids.habits_container
        container.clear_widgets()
        
        offset = self.current_page * self.habits_per_page
        habits = self.cursor.execute('''
            SELECT id, habit, completed, weather, mood, date 
            FROM habits 
            ORDER BY date DESC
            LIMIT ? OFFSET ?
        ''', (self.habits_per_page + 1, offset)).fetchall()
        
        if len(habits) <= self.habits_per_page:
            self.is_last_page = True
        else:
            self.is_last_page = False
            habits = habits[:-1]
        
        for habit in habits:
            container.add_widget(HabitItem(
                habit_id=str(habit[0]),
                habit_text=habit[1],
                completed=bool(habit[2]),
                weather=habit[3],
                mood=habit[4],
                date=habit[5]
            ))
    
    def next_page(self):
        self.current_page += 1
        self.load_habits()
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_habits()
    
    def update_stats(self):
        self.calculate_streaks()
        container = self.root.ids.stats_container
        container.clear_widgets()
        
        try:
            total = self.cursor.execute(
                "SELECT COUNT(*) FROM habits").fetchone()[0]
            
            completed = self.cursor.execute(
                "SELECT COUNT(*) FROM habits WHERE completed = 1").fetchone()[0]
            rate = f"{completed/total:.0%}" if total > 0 else "0%"
            
            stats = [
                ("Total", str(total)),
                ("Completed", f"{completed} ({rate})"),
                ("Current Streak", f"{self.streaks[0]} days"),
                ("Best Streak", f"{self.streaks[1]} days")
            ]
            
            for title, value in stats:
                card = MDCard(
                    size_hint=(None, None),
                    size=(dp(120), dp(100)),
                    radius=dp(15),
                    orientation='vertical',
                    padding=dp(10),
                    spacing=dp(5)
                )
                card.add_widget(MDLabel(
                    text=title,
                    font_style='Caption',
                    halign='center',
                    theme_text_color='Secondary'
                ))
                card.add_widget(MDLabel(
                    text=value,
                    font_style='H6',
                    halign='center',
                    theme_text_color='Primary'
                ))
                container.add_widget(card)
        except Exception as e:
            print(f"Error updating stats: {e}")
    
    def calculate_streaks(self):
        try:
            dates = [row[0] for row in self.cursor.execute(
                "SELECT DISTINCT date FROM habits WHERE completed = 1 ORDER BY date"
            ).fetchall()]
            
            current_streak = 0
            best_streak = 0
            prev_date = None
            
            for date_str in sorted(dates, reverse=True):
                try:
                    current_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M").date()
                    if prev_date is None:
                        prev_date = current_date
                        current_streak = 1
                    else:
                        if (prev_date - current_date).days == 1:
                            current_streak += 1
                        else:
                            best_streak = max(best_streak, current_streak)
                            current_streak = 1
                        prev_date = current_date
                except:
                    continue
            
            best_streak = max(best_streak, current_streak)
            self.streaks = [current_streak, best_streak, len(dates)]
        except Exception as e:
            print(f"Error calculating streaks: {e}")
    
    def update_weather(self):
        try:
            api_key = os.getenv('WEATHER_API_KEY')
            if not api_key or api_key == "your_api_key_here":
                return "Set API key in .env file"
            
            url = f"http://api.openweathermap.org/data/2.5/weather?q=Berlin&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if response.status_code == 200:
                weather = f"{data['weather'][0]['description']} ({data['main']['temp']}°C)"
                return weather
            else:
                return f"Weather error: {data.get('message', 'Unknown')}"
        except Exception as e:
            print(f"Weather error: {e}")
            return "Weather unavailable"
    
    def show_notification(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                timeout=10
            )
        except Exception as e:
            print(f"Notification error: {e}")
    
    def switch_theme(self):
        self.theme_cls.theme_style = (
            "Dark" if self.theme_cls.theme_style == "Light" else "Light"
        )
        self.root.ids.theme_btn.text = (
            "DARK" if self.theme_cls.theme_style == "Light" else "LIGHT"
        )
    
    def show_report(self):
        self.show_notification(
            "Report",
            "Report feature will be implemented soon!"
        )

if __name__ == '__main__':
    HabitTracker().run()