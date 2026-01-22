import tkinter as tk
from manager.tab.browser import BrowserTab
from manager.tab.configure import ConfigureTab

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

    top_frame = tk.Frame(root)
    top_frame.pack(side="top", fill="x", padx=10, pady=5)
    
    switch_frame = tk.Frame(top_frame)
    switch_frame.pack(side="left")
    content_frame = tk.Frame(root)
    content_frame.pack(fill="both", expand=True)

    configure_tab = ConfigureTab(content_frame)
    browser_tab = BrowserTab(content_frame, configure_tab.path_entry)
    tabs = (configure_tab,browser_tab)
    for tab in tabs:
        tab.place(relx=0, rely=0, relwidth=1, relheight=1)

    def show_tab(t):
        for tab in tabs:
            tab.lower()
        t.lift()

    tk.Button(switch_frame, text="Configure", command=lambda: show_tab(configure_tab)).pack(side="left", padx=2)
    tk.Button(switch_frame, text="Browser", command=lambda: show_tab(browser_tab)).pack(side="left", padx=2)

    show_tab(configure_tab)

    root.mainloop()

if __name__ == "__main__":
    main()