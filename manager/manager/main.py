import tkinter as tk

def window_ensure_show_and_focus(root):
    root.lift()             # bring window to front
    root.focus_force()      # force keyboard focus
    root.attributes("-topmost", True)
    root.after(0, lambda: root.attributes("-topmost", False))  # optionally release always-on-top

def main():
    root = tk.Tk()
    root.title("Data Manager")
    root.geometry("950x700")
    window_ensure_show_and_focus(root)

    root.mainloop()

if __name__ == "__main__":
    main()