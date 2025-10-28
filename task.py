import json
import tkinter as tk
from tkinter import messagebox, simpledialog
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

def main_gui():
    load_tasks()

    root = tk.Tk()
    root.title("Task Manager")

    #layout
    #top bar for filter controls
    topbar = tk.Frame(root)
    topbar.pack(fill="x", padx=12, pady=(12, 0))

    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True, padx=12, pady=12)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    listbox = tk.Listbox(frame, height=12, yscrollcommand=scrollbar.set)
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=listbox.yview)

    #helpers
    #make tasks start with [] or [x]
    def normalize_tasks():
        changed = False
        for i, t in enumerate(tasks):
            if not (t.startswith("[ ] ") or t.startswith("[x] ")):
                tasks[i] = "[ ] " + t
                changed = True
        if changed:
            save_tasks()

    def is_done(t: str) -> bool:
        return t.startswith("[x] ")

    def strip_prefix(t: str) -> str:
        if t.startswith("[ ] ") or t.startswith("[x] "):
            return t[4:]
        return t

    def set_tasks(i: int, done: bool, text: str):
        tasks[i] = ("[x] " if done else "[ ] ") + text

    #filtering state + mapping from visible rows -> real indices
    filter_var = tk.StringVar(value="All")  # All / Active / Done
    visible_indices = []  #indices into 'tasks' for the rows shown in the listbox

    def compute_visible():
        vis = []
        mode = filter_var.get()
        for i, t in enumerate(tasks):
            if mode == "All":
                vis.append(i)
            elif mode == "Active" and not is_done(t):
                vis.append(i)
            elif mode == "Done" and is_done(t):
                vis.append(i)
        return vis

    def refresh_list():
        nonlocal visible_indices
        visible_indices = compute_visible()
        listbox.delete(0, tk.END)
        for pos, idx in enumerate(visible_indices, start=1):
            listbox.insert(tk.END, f"{pos}. {tasks[idx]}")  #shows [ ] or [x]

    def get_selected_index():
        #translate selected row in the listbox -> index in 'tasks'
        try:
            pos = listbox.curselection()[0]
            return visible_indices[pos]
        except IndexError:
            return None

    #normalize once on startup and render / this killed me debugging
    normalize_tasks()
    refresh_list()

    #actions
    def add_task():
        task = simpledialog.askstring("Add Task", "Enter your task and time:")
        if task:
            tasks.append("[ ] " + task)  #new tasks start as not done
            save_tasks()
            refresh_list()

    def edit_task():
        idx = get_selected_index()
        if idx is None:
            messagebox.showwarning("No selection", "Please select a task to edit.")
            return
        current = tasks[idx]
        new_text = simpledialog.askstring(
            "Edit Task", "Update the task:", initialvalue=strip_prefix(current)
        )
        if new_text is not None and new_text.strip() != "":
            done = is_done(current)
            set_tasks(idx, done, new_text.strip())
            save_tasks()
            refresh_list()

    def toggle_done():
        idx = get_selected_index()
        if idx is None:
            messagebox.showwarning("No selection", "Please select a task to toggle.")
            return
        done = is_done(tasks[idx])
        text = strip_prefix(tasks[idx])
        set_tasks(idx, not done, text)
        save_tasks()
        refresh_list()

    def remove_task():
        idx = get_selected_index()
        if idx is None:
            messagebox.showwarning("No selection", "Please select a task to remove.")
            return
        task = tasks.pop(idx)
        save_tasks()
        refresh_list()
        messagebox.showinfo("Removed", f"Removed: {task}")

    #UI controls
    #filter dropdown on the top bar
    tk.Label(topbar, text="Filter:").pack(side="left")
    tk.OptionMenu(topbar, filter_var, "All", "Active", "Done",
                  command=lambda _=None: refresh_list()).pack(side="left")

    btnbar = tk.Frame(root)
    btnbar.pack(fill="x", padx=12, pady=(0, 12))

    tk.Button(btnbar, text="Add Task", command=add_task).pack(side="left")
    tk.Button(btnbar, text="Edit Task", command=edit_task).pack(side="left", padx=8)
    tk.Button(btnbar, text="Mark Done/Undone", command=toggle_done).pack(side="left")
    tk.Button(btnbar, text="Remove Task", command=remove_task).pack(side="left", padx=8)
    tk.Button(btnbar, text="Quit", command=root.destroy).pack(side="right")

    #shortcuts
    listbox.bind("<Double-Button-1>", lambda e: edit_task())
    listbox.bind("<Return>",          lambda e: (edit_task(), "break"))   #Enter edits
    listbox.bind("<space>",           lambda e: (toggle_done(), "break")) #Space toggles
    listbox.bind("<Delete>",          lambda e: (remove_task(), "break")) #Delete removes

    root.mainloop()

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
