import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
from datetime import datetime
import tkinter.font as tkfont

# Importiere die ausgelagerten Funktionen
from functions import *

class FileManagerApp:


    
    def __init__(self, root):
        self.root = root
        self.root.title("File Manager")
        self.root.geometry("800x500")  # Initial window size
        self.root.configure(bg="#f0f0f0")  # Background color

        # Use custom font
        self.font = tkfont.Font(family="Helvetica", size=12)

        # File data to store file paths
        self.files = []
        self.current_directory = os.path.expanduser("~")  # Default user's home directory

        # Frame for directory and folder management
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.main_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Title Label - Centered
        self.title_label = tk.Label(self.main_frame, text="File Manager", font=("Helvetica", 16), bg="#f0f0f0", fg="#333")
        self.title_label.grid(row=0, column=0, columnspan=4, pady=10, sticky="n")

        # Create Toolbar Frame
        self.toolbar_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.toolbar_frame.pack(padx=20, pady=10, fill="x")

        self.load_button = tk.Button(
            self.toolbar_frame,
            text="Load Directory",
            font=self.font,
            command=self.load_directory,
            bg="#4CAF50",
            fg="white",
            bd=0,
            highlightthickness=0,
        )
        self.load_button.pack(side="left", padx=5)

        self.create_folder_button = tk.Button(
            self.toolbar_frame,
            text="New Folder",
            font=self.font,
            command=self.create_folder,
            bg="#FF9800",
            fg="white",
            bd=0,
            highlightthickness=0,
        )
        self.create_folder_button.pack(side="left", padx=5)

        self.upload_button = tk.Button(
            self.toolbar_frame,
            text="Upload",
            font=self.font,
            command=self.upload_file,
            bg="#2196F3",
            fg="white",
            bd=0,
            highlightthickness=0,
        )
        self.upload_button.pack(side="left", padx=5)

        # Breadcrumb navigation label
        self.breadcrumb_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.breadcrumb_frame.pack(padx=20, fill="x")

        self.breadcrumb_label = tk.Label(
            self.breadcrumb_frame, text="", font=self.font, bg="#f0f0f0", fg="#555", anchor="w", justify="left", wraplength=700
        )
        self.breadcrumb_label.pack(side="left", fill="x", padx=10, pady=5)

        # Treeview to display files and directories (Excel-style table)
        self.treeview = ttk.Treeview(self.root, columns=("Name", "Size", "Last Change"), show="headings", selectmode="browse")
        self.treeview.pack(pady=20, padx=20, fill="both", expand=True)

        # Define column headings and set column widths
        self.treeview.heading("Name", text="Name", anchor="w")
        self.treeview.heading("Size", text="Size", anchor="center")
        self.treeview.heading("Last Change", text="Last Change", anchor="center")
        self.treeview.column("Name", width=300, anchor="w")
        self.treeview.column("Size", width=100, anchor="center")
        self.treeview.column("Last Change", width=120, anchor="center")

        # Initially load the user's home directory
        update_file_list_func(self, self.current_directory)

        # Bind double-click event to open folders or navigate up
        self.treeview.bind("<Double-1>", self.open_folder)

        # Right-click context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.open_item)
        self.context_menu.add_command(label="Rename", command=self.rename_item)
        self.context_menu.add_command(label="Delete", command=self.delete_item)
        self.context_menu.add_command(label="Properties", command=self.show_properties)

        self.treeview.bind("<Button-3>", self.show_context_menu)




    
    def open_folder(self, event):
        """Handle double-click to open folders or navigate up"""
        selected_item = self.treeview.focus()
        selected_name = self.treeview.item(selected_item)["values"][0]
        item_path = os.path.join(self.current_directory, selected_name.strip('📁 📄 '))
        selected_item = self.treeview.focus()
        if not selected_item:  # If no item is selected, return early
            return
        selected_name = self.treeview.item(selected_item)["values"][0]
        if selected_name.startswith("📁"):  # If it's a folder
            folder_name = selected_name.strip("📁 ").strip()
            new_folder = os.path.join(self.current_directory, folder_name)
            if os.path.isdir(new_folder):
                update_file_list_func(self, new_folder)
            if os.path.isdir(new_folder):
                # Prüfen, ob der Ordner (und seine Unterordner) leer sind
                if is_folder_empty(new_folder):
                    print('')
                    print('TEST FOLDER LEER')
                    print('')
                else:
                    print('not empty')

        elif selected_name == "⬆️ Go Up to Parent Folder":
            parent_directory = os.path.dirname(self.current_directory)
            update_file_list_func(self, parent_directory)
        else:  # If it's a file, open it with the default program
            if os.path.isfile(item_path):
                try:
                    if sys.platform == "linux" or sys.platform == "linux2":
                        subprocess.run(["xdg-open", item_path])
                    elif sys.platform == "darwin":
                        subprocess.run(["open", item_path])
                    elif sys.platform == "win32":
                        subprocess.run(["start", item_path], shell=True)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open the file: {str(e)}")



    def load_directory(self):
        """Load files and directories from a selected folder"""
        folder_path = filedialog.askdirectory(initialdir=self.current_directory, title="Select Directory")
        if folder_path:
            self.current_directory = folder_path  # Update the current directory
            update_file_list_func(self, folder_path)

    def create_folder(self):
        """Create a new folder in the selected directory"""
        folder_name = simpledialog.askstring("New Folder", "Enter folder name:")
        if folder_name:
            create_folder_func(self, folder_name)

    def upload_file(self):
        """Upload a file to the selected directory"""
        upload_file_func(self)

    def delete_item(self):
        """Delete selected file or folder"""
        delete_item_func(self)

    def open_item(self):
        """Open selected item (file/folder)"""
        open_item_func(self)

    def rename_item(self):
        """Rename selected item"""
        rename_item_func(self)

    def show_properties(self):
        """Show properties of the selected item"""
        show_properties_func(self)

    def show_context_menu(self, event):
        """Show context menu on right-click"""
        self.context_menu.post(event.x_root, event.y_root)


if __name__ == "__main__":
    root = tk.Tk()
    app = FileManagerApp(root)
    root.mainloop()
