import os
import platform
import subprocess
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import QDir, QDateTime, Qt
from PyQt5.QtGui import QColor


class FileManagerLogic:
    def __init__(self, ui):
        self.ui = ui
        self.show_hidden = False
        self.current_path = QDir.homePath()  # Initialize current_path to the home directory
        self.home_path = QDir.homePath()
        self.downloads_path = QDir.homePath() + "/Downloads"
        self.documents_path = QDir.homePath() + "/Documents"
        self.pictures_path = QDir.homePath() + "/Pictures"
        self.music_path = QDir.homePath() + "/Music"

    def load_directory(self, path):
        """Load the contents of a directory into the table."""
        # Normalize the path to avoid any duplication or invalid paths
        normalized_path = os.path.abspath(path)
        self.current_path = normalized_path  

        # Clear the file table and populate it with the directory contents
        self.ui.file_table.setRowCount(0)
        directory = QDir(normalized_path)
        directory.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
        if not self.show_hidden:
            directory.setFilter(directory.filter() & ~QDir.Hidden)

        for i, entry in enumerate(directory.entryInfoList()):
            self.ui.file_table.insertRow(i)

            # Set Name column
            name_item = QTableWidgetItem(entry.fileName())
            name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.ui.file_table.setItem(i, 0, name_item)

            # Set Type column
            type_item = QTableWidgetItem("Folder" if entry.isDir() else "File")
            type_item.setFlags(Qt.ItemIsEnabled)
            self.ui.file_table.setItem(i, 1, type_item)

            # Set Last Modified column
            last_modified = QDateTime(entry.lastModified()).toString("yyyy-MM-dd HH:mm:ss")
            last_modified_item = QTableWidgetItem(last_modified)
            last_modified_item.setFlags(Qt.ItemIsEnabled)
            self.ui.file_table.setItem(i, 2, last_modified_item)

            # Set Empty column
            if entry.isDir():
                is_empty = self.is_folder_empty(entry.filePath())
                empty_item = QTableWidgetItem("Empty" if is_empty else "")
                empty_item.setFlags(Qt.ItemIsEnabled)
                self.ui.file_table.setItem(i, 3, empty_item)

                if is_empty:
                    for col in range(4):
                        item = self.ui.file_table.item(i, col)
                        item.setBackground(QColor(255, 200, 200))
                        item.setForeground(QColor(0, 0, 0))
            else:
                empty_item = QTableWidgetItem("")
                empty_item.setFlags(Qt.ItemIsEnabled)
                self.ui.file_table.setItem(i, 3, empty_item)

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
        self.load_directory(self.current_path)
