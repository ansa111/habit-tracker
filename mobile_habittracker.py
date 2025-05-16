from kivymd.app import MDApp
from kivy.lang import Builder
from datetime import datetime
import sqlite3
from kivy.core.window import Window

Window.size = (360, 640)

KV = '''
MDScreen:
    ScrollView:
        MDBoxLayout:
            orientation: 'vertical'
            padding: dp(20)
            spacing: dp(15)
            size_hint_y: None
            height: self.minimum_height

            MDLabel:
                text: "Habit Tracker"
                halign: 'center'
                font_style: 'H4'
                size_hint_y: None
                height: self.texture_size[1]

            MDTextField:
                id: habit_input
                hint_text: "Enter habit"
                size_hint_y: None
                height: dp(48)

            MDRaisedButton:
                text: "ADD HABIT"
                on_release: app.add_habit()
                size_hint_y: None
                height: dp(48)
            
            MDLabel:
                id: status_label
                text: ""
                halign: 'center'
            
            MDList:
                id: habits_list
'''

class HabitTracker(MDApp):
    def build(self):
        self.init_db()
        self.theme_cls.primary_palette = "Teal"
        return Builder.load_string(KV)
    
    def init_db(self):
        self.conn = sqlite3.connect("habits.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit TEXT,
                date TEXT
            )
        """)
        self.conn.commit()
    
    def add_habit(self):
        habit = self.root.ids.habit_input.text
        if habit:
            try:
                date = datetime.now().strftime("%Y-%m-%d %H:%M")
                self.cursor.execute(
                    "INSERT INTO habits (habit, date) VALUES (?, ?)",
                    (habit, date)
                )
                self.conn.commit()
                self.root.ids.habit_input.text = ""
                self.root.ids.status_label.text = f"Added: {habit}"
                self.show_habits()
            except Exception as e:
                self.root.ids.status_label.text = f"Error: {str(e)}"
    
    def show_habits(self):
        self.root.ids.habits_list.clear_widgets()
        habits = self.cursor.execute("SELECT habit, date FROM habits ORDER BY date DESC").fetchall()
        for habit, date in habits:
            self.root.ids.habits_list.add_widget(
                MDLabel(text=f"{date}: {habit}", size_hint_y=None, height=dp(40))
            )

    def on_start(self):
        self.show_habits()

if __name__ == '__main__':
    from kivy.metrics import dp
    HabitTracker().run()