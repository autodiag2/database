import tkinter as tk
from tkinter import ttk, font
from manager.tab.browser import BrowserTab
from manager.tab.configure import ConfigureTab
from manager.tab.generate import GenerateTab
from manager.tab.query import QueryTab

def window_ensure_show_and_focus(root):
    root.lift()
    root.focus_force()
    root.attributes("-topmost", True)
    root.after(0, lambda: root.attributes("-topmost", False))

def main():
    root = tk.Tk()
    root.title("Data Manager")
    root.geometry("950x700")
    window_ensure_show_and_focus(root)

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    base_font = font.nametofont("TkDefaultFont")
    tab_font = base_font.copy()
    tab_font.configure(weight="normal")
    tab_sel_font = base_font.copy()
    tab_sel_font.configure(weight="bold")

    style.configure(
        "Tab.TButton",
        padding=(10, 4),
        relief="flat",
        borderwidth=1,
        font=tab_font,
        anchor="center",
        focusthickness=0,
        focuscolor="",
    )
    style.map(
        "Tab.TButton",
        relief=[("pressed", "sunken"), ("active", "groove")],
    )

    style.configure(
        "TabSelected.TButton",
        padding=(10, 4),
        relief="sunken",
        borderwidth=1,
        font=tab_sel_font,
        anchor="center",
        focusthickness=0,
        focuscolor="",
    )
    style.map(
        "TabSelected.TButton",
        relief=[("pressed", "sunken"), ("active", "sunken")],
    )

    top_frame = tk.Frame(root)
    top_frame.pack(side="top", fill="x", padx=10, pady=5)

    switch_frame = tk.Frame(top_frame)
    switch_frame.pack(side="left")

    sep = ttk.Separator(root, orient="horizontal")
    sep.pack(side="top", fill="x")

    content_frame = tk.Frame(root)
    content_frame.pack(fill="both", expand=True)

    configure_tab = ConfigureTab(content_frame)
    browser_tab = BrowserTab(content_frame, configure_tab.path_entry)
    generate_tab = GenerateTab(content_frame, configure_tab.path_entry)
    query_tab = QueryTab(content_frame, configure_tab.path_entry)

    tabs = (configure_tab, browser_tab, query_tab, generate_tab)
    for tab in tabs:
        tab.place(relx=0, rely=0, relwidth=1, relheight=1)

    tab_buttons = {}

    def show_tab(t):
        for tab in tabs:
            tab.lower()
        t.lift()
        for key, b in tab_buttons.items():
            b.configure(style="TabSelected.TButton" if key is t else "Tab.TButton")

    tab_buttons[configure_tab] = ttk.Button(
        switch_frame, text="Configure", style="Tab.TButton", command=lambda: show_tab(configure_tab)
    )
    tab_buttons[browser_tab] = ttk.Button(
        switch_frame, text="Browser", style="Tab.TButton", command=lambda: show_tab(browser_tab)
    )
    tab_buttons[query_tab] = ttk.Button(
        switch_frame, text="Query", style="Tab.TButton", command=lambda: show_tab(query_tab)
    )
    tab_buttons[generate_tab] = ttk.Button(
        switch_frame, text="Generate", style="Tab.TButton", command=lambda: show_tab(generate_tab)
    )

    for b in (tab_buttons[configure_tab], tab_buttons[browser_tab], tab_buttons[query_tab], tab_buttons[generate_tab]):
        b.pack(side="left", padx=0, pady=0, ipady=0, ipadx=0)

    show_tab(configure_tab)
    root.mainloop()

if __name__ == "__main__":
    main()
