import json
from pathlib import Path

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
    main()
