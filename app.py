import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import shutil
import tkinter.font as tkfont
from datetime import datetime
from tkinter import ttk


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
        self.update_file_list(self.current_directory)

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
                self.update_file_list(new_folder)
        elif selected_name == "⬆️ Go Up to Parent Folder":
            parent_directory = os.path.dirname(self.current_directory)
            self.update_file_list(parent_directory)
        else:  # If it's a file, open it with the default program
            if os.path.isfile(item_path): #f1
                try:
                    if sys.platform == "linux" or sys.platform == "linux2":
                        subprocess.run(["xdg-open", item_path])
                    elif sys.platform == "darwin":
                        subprocess.run(["open", item_path])
                    elif sys.platform == "win32":
                        subprocess.run(["start", item_path], shell=True)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open the file: {str(e)}")

    def update_breadcrumbs(self):
        """Update breadcrumb navigation based on the current directory"""
        for widget in self.breadcrumb_frame.winfo_children():
            widget.destroy()

        # Split current directory into parts
        parts = self.current_directory.split(os.sep)
        if parts[0] == "":
            parts[0] = "/"

        # Create a clickable breadcrumb for each part
        path = ""
        for i, part in enumerate(parts):
            if i > 0:
                tk.Label(self.breadcrumb_frame, text=">", font=self.font, bg="#f0f0f0", fg="#555").pack(side="left")
            path = os.path.join(path, part)
            button = tk.Button(
                self.breadcrumb_frame,
                text=part,
                font=self.font,
                bg="#f0f0f0",
                fg="#007BFF",
                relief="flat",
                command=lambda p=path: self.update_file_list(p),
            )
            button.pack(side="left")

    def load_directory(self):
        """Load files and directories from a selected folder"""
        folder_path = filedialog.askdirectory(initialdir=self.current_directory, title="Select Directory")
        if folder_path:
            self.current_directory = folder_path  # Update the current directory
            self.update_file_list(folder_path)

    def update_file_list(self, folder_path):
        """Update the file list to show only contents of the selected folder, hiding invisible files"""
        self.current_directory = folder_path
        self.treeview.delete(*self.treeview.get_children())

        try:
            # Update breadcrumbs
            self.update_breadcrumbs()

            # Add "Go Up" option as the first item in the list
            self.treeview.insert("", "end", text="⬆️ Go Up to Parent Folder", values=("⬆️ Go Up to Parent Folder", "", ""))

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
                size = ''
                date_modified = self.get_last_modified_date(os.path.join(folder_path, directory))
                # Add directory row to treeview
                self.treeview.insert("", "end", text=directory, values=("📁 " + directory, "0 KB", date_modified))
            for file in files:
                size = self.get_file_size(os.path.join(folder_path, file))
                date_modified = self.get_last_modified_date(os.path.join(folder_path, file))
                # Add file row to treeview
                self.treeview.insert("", "end", text=file, values=("📄 " + file, size, date_modified))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to list files: {str(e)}")

    def get_file_size(self, file_path):
        """Get the size of a file in a human-readable format"""
        size = os.path.getsize(file_path)
        return f"{size // 1024} KB" if size < 1048576 else f"{size // 1048576} MB"

    def get_last_modified_date(self, file_path):
        """Get the last modified date of a file or directory"""
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp).strftime('%d.%m.%y')

    def create_folder(self):
        """Create a new folder in the selected directory"""
        folder_name = simpledialog.askstring("New Folder", "Enter folder name:")
        if folder_name:
            new_folder_path = os.path.join(self.current_directory, folder_name)
            try:
                os.makedirs(new_folder_path)
                self.update_file_list(self.current_directory)
                messagebox.showinfo("Folder Created", f"Folder '{folder_name}' created successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create folder: {str(e)}")

    def upload_file(self):
        """Upload a file to the selected directory"""
        file_path = filedialog.askopenfilename(initialdir=self.current_directory, title="Select File to Upload")
        if file_path:
            try:
                dest_path = os.path.join(self.current_directory, os.path.basename(file_path))
                shutil.copy(file_path, dest_path)
                self.update_file_list(self.current_directory)
                messagebox.showinfo("File Uploaded", f"File '{os.path.basename(file_path)}' uploaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload file: {str(e)}")

    def delete_item(self):
        """Delete selected file or folder"""
        selected_item = self.treeview.focus()
        selected_name = self.treeview.item(selected_item)["values"][0]
        if selected_name.startswith("📁"):
            folder_name = selected_name.strip("📁 ").strip()
            try:
                shutil.rmtree(os.path.join(self.current_directory, folder_name))
                self.update_file_list(self.current_directory)
                messagebox.showinfo("Folder Deleted", f"Folder '{folder_name}' deleted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete folder: {str(e)}")
        elif selected_name.startswith("📄"):
            file_name = selected_name.strip("📄 ").strip()
            try:
                os.remove(os.path.join(self.current_directory, file_name))
                self.update_file_list(self.current_directory)
                messagebox.showinfo("File Deleted", f"File '{file_name}' deleted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {str(e)}")

    def open_item(self):
        """Open selected item (file/folder)"""
        selected_item = self.treeview.focus()
        selected_name = self.treeview.item(selected_item)["values"][0]
        if selected_name.startswith("📁"):
            folder_name = selected_name.strip("📁 ").strip()
            new_folder = os.path.join(self.current_directory, folder_name)
            if os.path.isdir(new_folder):
                self.update_file_list(new_folder)

    def rename_item(self):
        """Rename selected item"""
        selected_item = self.treeview.focus()
        selected_name = self.treeview.item(selected_item)["values"][0]
        new_name = simpledialog.askstring("Rename", f"Enter new name for '{selected_name}':")
        if new_name:
            old_path = os.path.join(self.current_directory, selected_name.strip("📁 📄 ").strip())
            new_path = os.path.join(self.current_directory, new_name)
            try:
                os.rename(old_path, new_path)
                self.update_file_list(self.current_directory)
                messagebox.showinfo("Item Renamed", f"Item renamed to '{new_name}'.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename item: {str(e)}")


    def show_properties(self):
        """Show properties of the selected item"""
        selected_item = self.treeview.focus()
        selected_name = self.treeview.item(selected_item)["values"][0]
        selected_name_view = selected_name.strip('📁 📄 ')#f2

        print(selceted_name_view)
        
        item_path = os.path.join(self.current_directory, selected_name.strip('📁 📄 '))
        file_path = item_path
        timestamp = os.path.getmtime(file_path)
        item_last_change = datetime.fromtimestamp(timestamp).strftime('%d.%m.%y')
        item_size_os = os.path.getsize(file_path)
        item_size = f"{item_size_os // 1024} KB" if item_size_os < 1048576 else f"{item_size_os // 1048576} MB"
        properties = f"Name: {selected_name}\nPath: {item_path}\nSize: {item_size}\nLast Change: {item_last_change}"
        messagebox.showinfo("Item Properties", properties)

    def show_context_menu(self, event):
        """Show context menu on right-click"""
        self.context_menu.post(event.x_root, event.y_root)


if __name__ == "__main__":
    root = tk.Tk()
    app = FileManagerApp(root)
    root.mainloop()
