import os
import platform
import subprocess
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import QDir, QDateTime, Qt, QFile, QSettings
from PyQt5.QtGui import QColor


class FileManagerLogic:
    def __init__(self, ui):
        self.ui = ui
        # Initialize and load preferences
        self.settings = QSettings("MyCompany", "AIFileManager")
        self.show_hidden = self.settings.value("show_hidden", False, type=bool)
        self.current_path = QDir.homePath()  # Initialize current_path to the home directory
        self.home_path = QDir.homePath()
        self.downloads_path = QDir.homePath() + "/Downloads"
        self.documents_path = QDir.homePath() + "/Documents"
        self.pictures_path = QDir.homePath() + "/Pictures"
        self.music_path = QDir.homePath() + "/Music"
        # Track last sort preferences and load
        sc = self.settings.value("sort_column", None)
        so = self.settings.value("sort_order", None)
        self.sort_column = int(sc) if sc is not None else None
        self.sort_order = int(so) if so is not None else None

    def load_directory(self, path):
        """Load the contents of a directory into the table."""
        # Normalize the path to avoid any duplication or invalid paths
        normalized_path = os.path.abspath(path)
        self.current_path = normalized_path  

        # Update breadcrumb in UI
        self.ui.update_breadcrumb(self.current_path)

        # Clear the file table and populate it with the directory contents
        self.ui.file_table.setRowCount(0)
        directory = QDir(normalized_path)
        directory.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
        if not self.show_hidden:
            directory.setFilter(directory.filter() & ~QDir.Hidden)

        for i, entry in enumerate(directory.entryInfoList()):
            self.ui.file_table.insertRow(i)

            # Name
            name_item = QTableWidgetItem(entry.fileName())
            name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.ui.file_table.setItem(i, 0, name_item)

            # Type
            type_item = QTableWidgetItem("Folder" if entry.isDir() else "File")
            type_item.setFlags(Qt.ItemIsEnabled)
            self.ui.file_table.setItem(i, 1, type_item)

            # Size
            size = entry.size() if not entry.isDir() else 0
            size_text = self.format_size(size) if size > 0 else ("" if not entry.isDir() else "")
            size_item = QTableWidgetItem(size_text)
            size_item.setFlags(Qt.ItemIsEnabled)
            self.ui.file_table.setItem(i, 2, size_item)

            # Permissions
            perms = entry.permissions()
            perm_str = ('r' if perms & QFile.ReadOwner else '-') + ('w' if perms & QFile.WriteOwner else '-')
            perm_str += ('x' if perms & QFile.ExeOwner else '-')
            perm_item = QTableWidgetItem(perm_str)
            perm_item.setFlags(Qt.ItemIsEnabled)
            self.ui.file_table.setItem(i, 3, perm_item)

            # Last Modified
            last_modified = QDateTime(entry.lastModified()).toString("yyyy-MM-dd HH:mm:ss")
            last_mod_item = QTableWidgetItem(last_modified)
            last_mod_item.setFlags(Qt.ItemIsEnabled)
            self.ui.file_table.setItem(i, 4, last_mod_item)

            # Empty
            empty_text = ""
            if entry.isDir() and self.is_folder_empty(entry.filePath()):
                empty_text = "Empty"
            empty_item = QTableWidgetItem(empty_text)
            empty_item.setFlags(Qt.ItemIsEnabled)
            self.ui.file_table.setItem(i, 5, empty_item)

            # Highlight empty folders
            if entry.isDir() and empty_text:
                for col in range(6):
                    item = self.ui.file_table.item(i, col)
                    item.setBackground(QColor(255, 200, 200))
                    item.setForeground(QColor(0, 0, 0))

        # Reapply last sort if any
        if self.sort_column is not None and self.sort_order is not None:
            self.ui.file_table.sortItems(self.sort_column, self.sort_order)

    def format_size(self, size):
        """Format the file size into a human-readable string."""
        # Implementing a basic human-readable format: bytes, KB, MB, GB
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if size < 1024 or unit == 'GB':
                return f"{size:.1f} {unit}"
            size /= 1024.0

    def is_folder_empty(self, path):
        """Recursively checks if a folder (and its subfolders) is empty."""
        try:
            for root, dirs, files in os.walk(path):
                if files or dirs:
                    return False
        except PermissionError:
            pass  # Ignore folders that cannot be accessed
        return True

    def sort_table(self, column):
        """Sort the table by the selected column."""
        order = self.ui.file_table.horizontalHeader().sortIndicatorOrder()
        self.ui.file_table.sortItems(column, order)
        # Remember and persist the sort preference
        self.sort_column = column
        self.sort_order = order
        self.settings.setValue("sort_column", column)
        self.settings.setValue("sort_order", order)

    def on_table_double_click(self, row, column):
        """Handle double-click event on table."""
        item = self.ui.file_table.item(row, 0)
        if not item:
            return

        selected_name = item.text()
        selected_path = QDir(self.current_path).filePath(selected_name)

        # If it's a folder, navigate into it
        if QDir(selected_path).exists():
            self.load_directory(selected_path)
        else:
            # If it's a file, open it with the default program
            self.open_file(selected_path)

    def open_file(self, file_path):
        """Open a file with the default program associated with its type."""
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)  # Windows-specific
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux and other Unix-like systems
                subprocess.run(["xdg-open", file_path])
        except Exception as e:
            print(f"Error opening file: {e}")

    def toggle_hidden_files(self):
        """Toggle visibility of hidden files."""
        self.show_hidden = not self.show_hidden
        self.settings.setValue("show_hidden", self.show_hidden)
        self.load_directory(self.current_path)
