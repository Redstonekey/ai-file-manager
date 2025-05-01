from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QWidget, QSplitter, QFrame, QHeaderView, QMenu, QAction, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QIcon, QCursor
from logic import FileManagerLogic
import os


class FileManagerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI File Manager")
        self.setGeometry(100, 100, 1024, 600)
        self.setStyleSheet(self.load_styles())

        # Initialize logic
        self.logic = FileManagerLogic(self)

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #e0e0e0; border-radius: 8px;")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_layout.setAlignment(Qt.AlignTop)  # Align buttons to the top

        # Add buttons to sidebar
        self.add_sidebar_button("Home", "icons/home.png", self.logic.home_path)
        self.add_sidebar_button("Downloads", "icons/downloads.png", self.logic.downloads_path)
        self.add_sidebar_button("Documents", "icons/documents.png", self.logic.documents_path)
        self.add_sidebar_button("Pictures", "icons/pictures.png", self.logic.pictures_path)
        self.add_sidebar_button("Music", "icons/music.png", self.logic.music_path)

        # Breadcrumb navigation
        self.breadcrumb_label = QWidget()
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_label)
        self.breadcrumb_layout.setContentsMargins(10, 10, 10, 10)
        self.breadcrumb_layout.setAlignment(Qt.AlignLeft)  # Align breadcrumb to the left
        self.breadcrumb_label.setStyleSheet("border-radius: 5px;")

        # Set breadcrumb example and make it interactive
        self.update_breadcrumb("Home/Documents/Projects")

        # Add breadcrumb and three-points menu above the table
        self.header_frame = QFrame()
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(0, 0, 0, 0)

        # Add breadcrumb to the header
        self.header_layout.addWidget(self.breadcrumb_label, alignment=Qt.AlignLeft)

        # Add three-points menu to the header
        self.menu_button = QPushButton("⋮", self)
        self.menu_button.setFixedSize(30, 30)
        self.menu_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                border: none;
                background-color: #ffffff;
                padding: 5px;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.menu_button.clicked.connect(self.show_menu)
        self.header_layout.addWidget(self.menu_button, alignment=Qt.AlignRight)

        # File table
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["Name", "Type", "Last Modified", "Empty"])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.file_table.horizontalHeader().sectionClicked.connect(self.logic.sort_table)
        self.file_table.setShowGrid(False)  # Remove gridlines globally
        self.file_table.setSelectionBehavior(QTableWidget.SelectRows)  # Full-row selection
        self.file_table.setSelectionMode(QTableWidget.SingleSelection)  # Single selection
        self.file_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.file_table.cellDoubleClicked.connect(self.logic.on_table_double_click)

        # Add context menu to file table
        self.file_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)

        # Main content layout
        self.content_layout = QVBoxLayout()
        self.content_layout.addWidget(self.header_frame)  # Add header (breadcrumb + menu) above table
        self.content_layout.addWidget(self.file_table)

                # Header (Breadcrumb Navigation)
        self.breadcrumb_label = QWidget()
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_label)
        self.breadcrumb_layout.setContentsMargins(10, 10, 10, 10)
        self.breadcrumb_layout.setAlignment(Qt.AlignLeft)
        self.breadcrumb_label.setStyleSheet("border-radius: 5px;")


        # Splitter to divide sidebar and content
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.content_frame = QFrame()
        self.content_frame.setLayout(self.content_layout)
        self.splitter.addWidget(self.content_frame)
        self.layout.addWidget(self.splitter)

        # Load the default directory (Home)
        self.logic.load_directory(self.logic.home_path)

    def add_sidebar_button(self, name, icon_path, path):
        button = QPushButton(name)
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(16, 16))
        button.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                border: none;
                padding: 10px;
                margin: 5px 0;
                text-align: left;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #dcdcdc;
            }
        """)
        button.clicked.connect(lambda: self.logic.load_directory(path))
        self.sidebar_layout.addWidget(button)

    def update_breadcrumb(self, path):
        """Update the breadcrumb navigation with clickable parts."""
        # Clear the current layout
        for i in reversed(range(self.breadcrumb_layout.count())):
            widget = self.breadcrumb_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Split the path and create parts
        parts = path.split('/')
        current_path = ""
        
        for idx, part in enumerate(parts):
            if not part:  # Skip empty parts
                continue
                
            # Build the absolute path progressively
            if idx == 0 and os.path.isabs(path):
                current_path = "/"
            current_path = os.path.join(current_path, part)

            # Create clickable label
            label = QLabel(part)
            label.setStyleSheet("""
                QLabel {
                    color: #007BFF;
                    font-size: 14px;
                    padding: 3px;
                }
                QLabel:hover {
                    background-color: #f0f0f0;
                    border-radius: 5px;
                }
            """)
            label.setCursor(QCursor(Qt.PointingHandCursor))
            
            # Use a local variable to store the path
            path_for_click = os.path.abspath(current_path)
            label.mousePressEvent = lambda _, p=path_for_click: self.logic.load_directory(p)
            self.breadcrumb_layout.addWidget(label)

            # Add separator if not the last part
            if idx < len(parts) - 1:
                separator = QLabel(">")
                separator.setStyleSheet("color: #333333; font-size: 14px; padding: 3px;")
                self.breadcrumb_layout.addWidget(separator)

    def show_context_menu(self, position: QPoint):
        """Show context menu for file table."""
        menu = QMenu(self)

        # Define actions
        new_file_action = QAction("New File", self)
        new_file_action.triggered.connect(self.create_new_file)

        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(self.rename_item)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_item)

        open_with_action = QAction("Open With...", self)
        open_with_action.triggered.connect(self.open_with_program)

        # Add actions to menu
        menu.addAction(new_file_action)
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(open_with_action)

        # Show the menu
        menu.exec_(self.file_table.viewport().mapToGlobal(position))

    def create_new_file(self):
        """Create a new file in the current directory."""
        file_name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and file_name:
            file_path = os.path.join(self.logic.current_path, file_name)
            try:
                open(file_path, 'w').close()  # Create empty file
                self.logic.load_directory(self.logic.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create file: {e}")

    def rename_item(self):
        """Rename the selected file or folder."""
        selected_row = self.file_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Warning", "No item selected.")
            return

        current_name = self.file_table.item(selected_row, 0).text()
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=current_name)
        if ok and new_name:
            old_path = os.path.join(self.logic.current_path, current_name)
            new_path = os.path.join(self.logic.current_path, new_name)
            try:
                os.rename(old_path, new_path)
                self.logic.load_directory(self.logic.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename item: {e}")

    def delete_item(self):
        """Delete the selected file or folder."""
        selected_row = self.file_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Warning", "No item selected.")
            return

        item_name = self.file_table.item(selected_row, 0).text()
        item_path = os.path.join(self.logic.current_path, item_name)
        confirm = QMessageBox.question(self, "Delete", f"Are you sure you want to delete '{item_name}'?",
                                        QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                if os.path.isdir(item_path):
                    os.rmdir(item_path)  # Remove directory
                else:
                    os.remove(item_path)  # Remove file
                self.logic.load_directory(self.logic.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete item: {e}")

    def open_with_program(self):
        """Open the selected file with a specific program."""
        selected_row = self.file_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Warning", "No file selected.")
            return

        file_name = self.file_table.item(selected_row, 0).text()
        file_path = os.path.join(self.logic.current_path, file_name)
        program, ok = QInputDialog.getText(self, "Open With", "Enter program name:")
        if ok and program:
            try:
                os.system(f"{program} \"{file_path}\"")  # Open with specified program
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def show_menu(self):
        """Show a three-point menu with options."""
        menu = QMenu(self)
        toggle_hidden_action = QAction("Show Hidden Files", self)
        toggle_hidden_action.setCheckable(True)
        toggle_hidden_action.setChecked(self.logic.show_hidden)
        toggle_hidden_action.triggered.connect(self.logic.toggle_hidden_files)

        menu.addAction(toggle_hidden_action)
        menu.exec_(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))

    def load_styles(self):
        return """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QFrame {
            background-color: #ffffff;
            border-radius: 8px;
        }
        QLabel {
            font-size: 14px;
            color: #333333;
        }
        QPushButton {
            font-size: 14px;
        }
        """

    def update_breadcrumb(self, path):
        """Update the breadcrumb navigation with clickable parts."""
        # Clear the current layout
        for i in reversed(range(self.breadcrumb_layout.count())):
            widget = self.breadcrumb_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Split the path and create parts
        parts = path.split(os.sep)
        current_path = ""

        for idx, part in enumerate(parts):
            if not part:  # Skip empty parts
                continue

            # Build the absolute path progressively
            if idx == 0 and os.path.isabs(path):
                current_path = os.sep
            else:
                current_path = os.path.join(current_path, part)

            # Create clickable label
            label = QLabel(part if part else os.sep)
            label.setStyleSheet("""
                QLabel {
                    color: #007BFF;
                    font-size: 14px;
                    padding: 3px;
                }
                QLabel:hover {
                    background-color: #f0f0f0;
                    border-radius: 5px;
                }
            """)
            label.setCursor(QCursor(Qt.PointingHandCursor))

            # Capture the current path correctly
            path_for_click = os.path.abspath(current_path)
            label.mousePressEvent = lambda _, p=path_for_click: self.logic.load_directory(p)
            self.breadcrumb_layout.addWidget(label)

            # Add separator if not the last part
            if idx < len(parts) - 1:
                separator = QLabel(">")
                separator.setStyleSheet("color: #333333; font-size: 14px; padding: 3px;")
                self.breadcrumb_layout.addWidget(separator)
