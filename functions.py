import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from datetime import datetime


    
def is_folder_empty(folder_path):
    """Prüft rekursiv, ob ein Ordner und seine Unterordner komplett leer sind."""
    for root, dirs, files in os.walk(folder_path):
        if files or dirs:  # Falls eine Datei oder ein Unterordner existiert
            return False
    return True


import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog

def is_folder_empty(folder_path):
    """Überprüft rekursiv, ob ein Ordner und seine Unterordner leer sind."""
    for root, _, files in os.walk(folder_path):
        if files:  # Sobald eine Datei gefunden wird, ist der Ordner nicht leer
            return False
    return True

def update_file_list_func(app, folder_path):
    """Update the file list to show only contents of the selected folder, hiding invisible files"""
    app.current_directory = folder_path
    app.treeview.delete(*app.treeview.get_children())

    try:
        # Update breadcrumbs
        update_breadcrumbs_func(app)

        # Add "Go Up" option as the first item in the list
        app.treeview.insert("", "end", text="⬆️ Go Up to Parent Folder", values=("⬆️ Go Up to Parent Folder", "", ""))

        # Separate directories and files
        directories = []
        files = []
        for item in os.listdir(folder_path):
            if item.startswith('.'):  # Skip hidden files and directories
                continue
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                directories.append(item)
            else:
                files.append(item)

        # Sort directories and files alphabetically
        directories.sort()
        files.sort()

        # Add directories to the treeview with emoji icons, followed by files
        for directory in directories:
            dir_path = os.path.join(folder_path, directory)
            size = ''
            date_modified = get_last_modified_date_func(dir_path)
            # Prüfen, ob dieser Ordner und seine Unterordner leer sind
            if is_folder_empty(dir_path):
                is_empty_text = " (empty folder)"
            else:
                is_empty_text = ""
            app.treeview.insert("", "end", text=directory, values=(f"📁 " + directory + is_empty_text, "0 KB", date_modified))
            


        for file in files:
            size = get_file_size_func(os.path.join(folder_path, file))
            date_modified = get_last_modified_date_func(os.path.join(folder_path, file))
            app.treeview.insert("", "end", text=file, values=("📄 " + file, size, date_modified))

    except Exception as e:
        messagebox.showerror("Error", f"Failed to list files: {str(e)}")

def get_file_size_func(file_path):
    """Get the size of a file in a human-readable format"""
    size = os.path.getsize(file_path)
    return f"{size // 1024} KB" if size < 1048576 else f"{size // 1048576} MB"

def get_last_modified_date_func(file_path):
    """Get the last modified date of a file or directory"""
    timestamp = os.path.getmtime(file_path)
    return datetime.fromtimestamp(timestamp).strftime('%d.%m.%y')

def create_folder_func(app, folder_name):
    """Create a new folder in the selected directory"""
    new_folder_path = os.path.join(app.current_directory, folder_name)
    try:
        os.makedirs(new_folder_path)
        update_file_list_func(app, app.current_directory)
        messagebox.showinfo("Folder Created", f"Folder '{folder_name}' created successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create folder: {str(e)}")

def upload_file_func(app):
    """Upload a file to the selected directory"""
    file_path = filedialog.askopenfilename(initialdir=app.current_directory, title="Select File to Upload")
    if file_path:
        try:
            dest_path = os.path.join(app.current_directory, os.path.basename(file_path))
            shutil.copy(file_path, dest_path)
            update_file_list_func(app, app.current_directory)
            messagebox.showinfo("File Uploaded", f"File '{os.path.basename(file_path)}' uploaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload file: {str(e)}")

def delete_item_func(app):
    """Delete selected file or folder"""
    selected_item = app.treeview.focus()
    selected_name = app.treeview.item(selected_item)["values"][0]
    if selected_name.startswith("📁"):
        folder_name = selected_name.strip("📁 ").strip()
        try:
            shutil.rmtree(os.path.join(app.current_directory, folder_name))
            update_file_list_func(app, app.current_directory)
            messagebox.showinfo("Folder Deleted", f"Folder '{folder_name}' deleted successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete folder: {str(e)}")
    elif selected_name.startswith("📄"):
        file_name = selected_name.strip("📄 ").strip()
        try:
            os.remove(os.path.join(app.current_directory, file_name))
            update_file_list_func(app, app.current_directory)
            messagebox.showinfo("File Deleted", f"File '{file_name}' deleted successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete file: {str(e)}")

def open_item_func(app):
    """Open selected item (file/folder)"""
    selected_item = app.treeview.focus()
    selected_name = app.treeview.item(selected_item)["values"][0]
    if selected_name.startswith("📁"):
        folder_name = selected_name.strip("📁 ").strip()
        new_folder = os.path.join(app.current_directory, folder_name)
        if os.path.isdir(new_folder):
            update_file_list_func(app, new_folder)

def rename_item_func(app):
    """Rename selected item"""
    selected_item = app.treeview.focus()
    selected_name = app.treeview.item(selected_item)["values"][0]
    new_name = simpledialog.askstring("Rename", f"Enter new name for '{selected_name}':")
    if new_name:
        old_path = os.path.join(app.current_directory, selected_name.strip("📁 📄 ").strip())
        new_path = os.path.join(app.current_directory, new_name)
        try:
            os.rename(old_path, new_path)
            update_file_list_func(app, app.current_directory)
            messagebox.showinfo("Item Renamed", f"Item renamed to '{new_name}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename item: {str(e)}")

def show_properties_func(app):
    """Show properties of the selected item"""
    selected_item = app.treeview.focus()
    selected_name = app.treeview.item(selected_item)["values"][0]
    selected_name_view = selected_name.strip('📁 📄 ')  #f2

    item_path = os.path.join(app.current_directory, selected_name.strip('📁 📄 '))
    file_path = item_path
    timestamp = os.path.getmtime(file_path)
    item_last_change = datetime.fromtimestamp(timestamp).strftime('%d.%m.%y')
    item_size_os = os.path.getsize(file_path)
    item_size = f"{item_size_os // 1024} KB" if item_size_os < 1048576 else f"{item_size_os // 1048576} MB"
    properties = f"Name: {selected_name}\nPath: {item_path}\nSize: {item_size}\nLast Change: {item_last_change}"
    messagebox.showinfo("Item Properties", properties)

def update_breadcrumbs_func(app):
    """Update breadcrumb navigation based on the current directory"""
    for widget in app.breadcrumb_frame.winfo_children():
        widget.destroy()

    # Split current directory into parts
    parts = app.current_directory.split(os.sep)
    if parts[0] == "":
        parts[0] = "/"

    # Create a clickable breadcrumb for each part
    path = ""
    for i, part in enumerate(parts):
        if i > 0:
            tk.Label(app.breadcrumb_frame, text=">", font=app.font, bg="#f0f0f0", fg="#555").pack(side="left")
        path = os.path.join(path, part)
        button = tk.Button(
            app.breadcrumb_frame,
            text=part,
            font=app.font,
            bg="#f0f0f0",
            fg="#007BFF",
            relief="flat",
            command=lambda p=path: update_file_list_func(app, p),
        )
        button.pack(side="left")
