import json
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QInputDialog, QMessageBox,
    QLabel, QComboBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

tasks = []
DATA_FILE = Path("schedule.json")

def load_tasks():
    global tasks
    if DATA_FILE.exists():
        try:
            tasks = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if not isinstance(tasks, list):
                tasks = []
        except Exception:
            print("Warning: Couldn't read schedule.json; starting with an empty schedule.")
            tasks = []
    else:
        tasks = []

def save_tasks():
    try:
        DATA_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Error saving tasks: {e}")

class TaskManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.visible_indices = []
        self.init_ui()
        self.normalize_tasks()
        self.refresh_list()

    def init_ui(self):
        self.setWindowTitle("Task Manager")
        self.setMinimumSize(600, 500)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #a2e8b8;
            }
            QListWidget {
                background-color: #e8d4f5;
                border: 1px solid #c8a8e0;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                color: #4a4a4a;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dcc8ed;
            }
            QListWidget::item:selected {
                background-color: #d4b5f0;
                color: #5d3a7a;
            }
            QListWidget::item:hover {
                background-color: #f2e8fa;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
            QPushButton#removeBtn {
                background-color: #d32f2f;
            }
            QPushButton#removeBtn:hover {
                background-color: #c62828;
            }
            QPushButton#quitBtn {
                background-color: #757575;
            }
            QPushButton#quitBtn:hover {
                background-color: #616161;
            }
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #c8a8e0;
                border-radius: 6px;
                background-color: #e8d4f5;
                min-width: 100px;
                color: #4a4a4a;
            }
            QComboBox:hover {
                border: 1px solid #b491d1;
            }
            QComboBox::drop-down {
                border: none;
            }
            QLabel {
                color: #424242;
                font-weight: bold;
            }
        """)

        #Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        #Title
        title_label = QLabel("📋 Task Manager")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1976d2; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        #Filter bar
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("font-weight: bold; color: #616161;")
        filter_layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Active", "Done"])
        self.filter_combo.currentTextChanged.connect(self.refresh_list)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        
        main_layout.addLayout(filter_layout)

        #Task list
        self.task_list = QListWidget()
        self.task_list.itemDoubleClicked.connect(self.edit_task)
        main_layout.addWidget(self.task_list)

        #Button bar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        add_btn = QPushButton("➕ Add Task")
        add_btn.clicked.connect(self.add_task)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Edit Task")
        edit_btn.clicked.connect(self.edit_task)
        button_layout.addWidget(edit_btn)

        toggle_btn = QPushButton("✓ Toggle Done")
        toggle_btn.clicked.connect(self.toggle_done)
        button_layout.addWidget(toggle_btn)

        remove_btn = QPushButton("🗑️ Remove")
        remove_btn.setObjectName("removeBtn")
        remove_btn.clicked.connect(self.remove_task)
        button_layout.addWidget(remove_btn)

        button_layout.addStretch()

        quit_btn = QPushButton("Exit")
        quit_btn.setObjectName("quitBtn")
        quit_btn.clicked.connect(self.close)
        button_layout.addWidget(quit_btn)

        main_layout.addLayout(button_layout)

        #Keyboard shortcuts
        self.task_list.keyPressEvent = self.handle_key_press

    def handle_key_press(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.edit_task()
        elif event.key() == Qt.Key_Space:
            self.toggle_done()
            event.accept()
        elif event.key() == Qt.Key_Delete:
            self.remove_task()
        else:
            QListWidget.keyPressEvent(self.task_list, event)

    def normalize_tasks(self):
        """Ensure all tasks have [ ] or [x] prefix"""
        changed = False
        for i, t in enumerate(tasks):
            if not (t.startswith("[ ] ") or t.startswith("[x] ")):
                tasks[i] = "[ ] " + t
                changed = True
        if changed:
            save_tasks()

    def is_done(self, t: str) -> bool:
        return t.startswith("[x] ")

    def strip_prefix(self, t: str) -> str:
        if t.startswith("[ ] ") or t.startswith("[x] "):
            return t[4:]
        return t

    def set_task(self, i: int, done: bool, text: str):
        tasks[i] = ("[x] " if done else "[ ] ") + text

    def compute_visible(self):
        """Calculate which tasks should be visible based on filter"""
        vis = []
        mode = self.filter_combo.currentText()
        for i, t in enumerate(tasks):
            if mode == "All":
                vis.append(i)
            elif mode == "Active" and not self.is_done(t):
                vis.append(i)
            elif mode == "Done" and self.is_done(t):
                vis.append(i)
        return vis

    def refresh_list(self):
        """Refresh the task list display"""
        self.visible_indices = self.compute_visible()
        self.task_list.clear()
        for pos, idx in enumerate(self.visible_indices, start=1):
            task_text = tasks[idx]
            #Visual styling for completed tasks
            if self.is_done(task_text):
                display_text = f"{pos}. {task_text}"
                item = QListWidgetItem(display_text)
                item.setForeground(Qt.gray)
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
            else:
                display_text = f"{pos}. {task_text}"
                item = QListWidgetItem(display_text)
            self.task_list.addItem(item)

    def get_selected_index(self):
        """Get the actual task index from the selected list item"""
        current_row = self.task_list.currentRow()
        if current_row >= 0 and current_row < len(self.visible_indices):
            return self.visible_indices[current_row]
        return None

    def add_task(self):
        """Add a new task"""
        text, ok = QInputDialog.getText(
            self, "Add Task", "Enter your task and time:"
        )
        if ok and text.strip():
            tasks.append("[ ] " + text.strip())
            save_tasks()
            self.refresh_list()

    def edit_task(self):
        """Edit the selected task"""
        idx = self.get_selected_index()
        if idx is None:
            QMessageBox.warning(self, "No Selection", "Please select a task to edit.")
            return
        
        current = tasks[idx]
        text, ok = QInputDialog.getText(
            self, "Edit Task", "Update the task:",
            text=self.strip_prefix(current)
        )
        if ok and text.strip():
            done = self.is_done(current)
            self.set_task(idx, done, text.strip())
            save_tasks()
            self.refresh_list()

    def toggle_done(self):
        """Toggle the done status of the selected task"""
        idx = self.get_selected_index()
        if idx is None:
            QMessageBox.warning(self, "No Selection", "Please select a task to toggle.")
            return
        
        done = self.is_done(tasks[idx])
        text = self.strip_prefix(tasks[idx])
        self.set_task(idx, not done, text)
        save_tasks()
        self.refresh_list()

    def remove_task(self):
        """Remove the selected task"""
        idx = self.get_selected_index()
        if idx is None:
            QMessageBox.warning(self, "No Selection", "Please select a task to remove.")
            return
        
        task = tasks[idx]
        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Remove task: {self.strip_prefix(task)}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            tasks.pop(idx)
            save_tasks()
            self.refresh_list()

def main_gui():
    """Launch the Qt GUI"""
    load_tasks()
    app = QApplication(sys.argv)
    window = TaskManagerWindow()
    window.show()
    sys.exit(app.exec())

#Console-based functions 
def get_setup_option():
    while True:
        try:
            setup = int(input("Hello user, enter 1 if you need to set up your schedule, "
                              "enter 2 if your schedule is already created: "))
            if setup in (1, 2):
                return setup
            else:
                print("Invalid input. Please enter 1 or 2.")
        except ValueError:
            print("Please enter a valid number.")

def setup_schedule():
    try:
        num_inputs = int(input("Enter the number of tasks you would like in your schedule: "))
        for i in range(num_inputs):
            task = input(f"Enter task {i + 1} and the time you want to complete it: ")
            tasks.append(task)
        save_tasks()
    except ValueError:
        print("Invalid input. Please enter a number.")

def get_user_choice():
    while True:
        try:
            choice = int(input(
                "Welcome back user. Enter 1 to view your current schedule, "
                "2 to input new tasks, 3 to remove tasks, or 4 to exit: "
            ))
            if 1 <= choice <= 4:
                return choice
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
        except ValueError:
            print("Please enter a valid number.")

def view_schedule():
    if tasks:
        print("\nSchedule:")
        for i, task in enumerate(tasks, start=1):
            print(f"{i}. {task}")
    else:
        print("No schedule available.")

def add_tasks():
    try:
        num_tasks = int(input("Enter the number of tasks you want to add: "))
        for _ in range(num_tasks):
            task = input(f"Enter task {len(tasks) + 1} and the time you want to complete it: ")
            tasks.append(task)
        save_tasks()
    except ValueError:
        print("Invalid input. Please enter a number.")

def remove_tasks():
    if tasks:
        view_schedule()
        try:
            index = int(input("Enter the task number you want to remove: "))
            if 1 <= index <= len(tasks):
                removed = tasks.pop(index - 1)
                save_tasks()
                print(f"Task '{removed}' removed successfully.")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid number.")
    else:
        print("No tasks to remove.")

def main():
    load_tasks()
    setup = get_setup_option()
    if setup == 1 and not tasks:
        setup_schedule()

    while True:
        choice = get_user_choice()
        if choice == 1:
            view_schedule()
        elif choice == 2:
            add_tasks()
            view_schedule()
        elif choice == 3:
            remove_tasks()
            view_schedule()
        elif choice == 4:
            print("Goodbye!")
            break

if __name__ == "__main__":
    USE_GUI = True
    if USE_GUI:
        main_gui()
    else:
        main()
