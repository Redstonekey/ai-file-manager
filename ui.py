from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QWidget, QSplitter, QFrame, QHeaderView, QMenu, QAction, QInputDialog, QMessageBox, QLineEdit,
    QProgressDialog, QFileDialog, QAbstractItemView, QDialog, QCheckBox, QDialogButtonBox, QGridLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QPoint, QSize, QSettings
import shutil
import zipfile
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtGui import QPixmap
import os
from logic import FileManagerLogic
from pathlib import Path
import subprocess
import platform
import ctypes


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
        self.sidebar.setObjectName("sidebar")  # for styling
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

        # Add breadcrumb navigation and three-points menu above the table
        self.header_frame = QFrame()
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(0, 0, 0, 0)

        # Breadcrumb navigation widget
        self.breadcrumb_widget = QWidget(self)
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_widget)
        self.breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.addWidget(self.breadcrumb_widget, alignment=Qt.AlignLeft)

        # Header frame for styling
        self.header_frame.setObjectName("headerFrame")

        # Search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_files)
        self.header_layout.addWidget(self.search_bar)

        # Add three-points menu to the header
        self.menu_button = QPushButton("⋮", self)
        self.menu_button.setObjectName("menuButton")  # for styling
        self.menu_button.setFixedSize(30, 30)
        self.menu_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                border: none;
                background-color: #ffffff;
                padding: 5px;
                border-radius: 15px;
            }            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.menu_button.clicked.connect(self.show_menu)
        self.header_layout.addWidget(self.menu_button, alignment=Qt.AlignRight)

        # File table
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(6)
        self.file_table.setHorizontalHeaderLabels(["Name", "Type", "Size", "Permissions", "Last Modified", "Empty"])
        # Allow interactive column resizing and load saved widths
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionsMovable(True)
        header.setSectionsClickable(True)
        header.setStretchLastSection(False)
        self.file_table.horizontalHeader().sectionClicked.connect(self.logic.sort_table)
        self.file_table.setShowGrid(False)  # Remove gridlines globally
        self.file_table.setSelectionBehavior(QTableWidget.SelectRows)  # Full-row selection
        self.file_table.setSelectionMode(QTableWidget.ExtendedSelection)  # Allow multi-selection via Shift/Ctrl
        self.file_table.setDragEnabled(True)
        self.file_table.setAcceptDrops(True)
        self.file_table.setDragDropMode(QAbstractItemView.DragDrop)
        self.file_table.dragEnterEvent = self._table_drag_enter
        self.file_table.dropEvent = self._table_drop
        self.file_table.dragMoveEvent = self._table_drag_move  # Accept drag move events
        self.file_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.file_table.cellDoubleClicked.connect(self.logic.on_table_double_click)

        # Add context menu to file table
        self.file_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)

        # Connect selection change to preview update
        self.file_table.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Create splitter for table and preview
        self.content_splitter = QSplitter(Qt.Horizontal)
        self.content_splitter.addWidget(self.file_table)
        self.preview_label = QLabel("Preview Area")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedWidth(300)
        self.content_splitter.addWidget(self.preview_label)

        # Main content layout
        self.content_layout = QVBoxLayout()
        self.content_layout.addWidget(self.header_frame)  # Add header (breadcrumb + menu) above table
        self.content_layout.addWidget(self.content_splitter)

        # Splitter to divide sidebar and content
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.content_frame = QFrame()
        self.content_frame.setLayout(self.content_layout)
        self.splitter.addWidget(self.content_frame)
        self.layout.addWidget(self.splitter)

        # Load the default directory (Home)
        self.logic.load_directory(self.logic.home_path)

        # Clipboard for copy/paste
        self.clipboard = []

        # Dark mode flag
        self.dark_mode = False
        # Initialize settings for preferences
        self.settings = QSettings("MyCompany", "AIFileManager")
        # Load and apply column visibility
        self.load_column_settings()
        # Load and apply column widths
        self.load_column_widths()
        # Save widths when resized
        self.file_table.horizontalHeader().sectionResized.connect(lambda idx, old, new: self.save_column_widths())
        # Load and apply preview visibility
        self.preview_visible = self.settings.value("preview_visible", True, type=bool)
        self.content_splitter.widget(1).setVisible(self.preview_visible)

    def add_sidebar_button(self, name, icon_path, path):
        button = QPushButton(name)
        button.setObjectName("sidebarButton")  # for QSS styling
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

    def show_context_menu(self, position: QPoint):
        """Show context menu for file table."""
        menu = QMenu(self)

        # Define actions
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_item)
        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self.paste_item)
        compress_action = QAction("Compress", self)
        compress_action.triggered.connect(self.compress_items)
        extract_action = QAction("Extract Here", self)
        extract_action.triggered.connect(self.extract_item)
        new_file_action = QAction("New File", self)
        new_folder_action = QAction("New Folder", self)
        new_folder_action.triggered.connect(self.create_new_folder)
        new_file_action.triggered.connect(self.create_new_file)

        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(self.rename_item)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_item)

        open_with_action = QAction("Open With...", self)
        open_with_action.triggered.connect(self.open_with_program)

        # Add actions to menu
        menu.addAction(new_folder_action)
        menu.addAction(new_file_action)
        menu.addSeparator()
        menu.addAction(copy_action)
        menu.addAction(paste_action)
        menu.addSeparator()
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(compress_action)
        menu.addAction(extract_action)
        menu.addSeparator()
        menu.addAction(open_with_action)

        # Show the menu
        menu.exec_(self.file_table.viewport().mapToGlobal(position))

    def copy_item(self):
        """Copy selected items to clipboard."""
        self.clipboard.clear()
        for item in self.file_table.selectedItems()[::6]:  # step by columns
            path = os.path.join(self.logic.current_path, item.text())
            self.clipboard.append(path)
        QMessageBox.information(self, "Copy", f"{len(self.clipboard)} item(s) copied.")

    def paste_item(self):
        """Paste items from clipboard to current directory."""
        if not self.clipboard:
            QMessageBox.warning(self, "Paste", "Clipboard is empty.")
            return
        dlg = QProgressDialog("Pasting files...", "Cancel", 0, len(self.clipboard), self)
        dlg.setWindowModality(Qt.WindowModal)
        for i, src in enumerate(self.clipboard):
            if dlg.wasCanceled(): break
            fname = os.path.basename(src)
            dest = os.path.join(self.logic.current_path, fname)
            try:
                if os.path.isdir(src): shutil.copytree(src, dest)
                else: shutil.copy2(src, dest)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to paste {fname}: {e}")
            dlg.setValue(i+1)
        dlg.close()
        self.logic.load_directory(self.logic.current_path)

    def compress_items(self):
        """Compress selected items into a zip archive."""
        # Get unique selected rows
        rows = sorted({idx.row() for idx in self.file_table.selectionModel().selectedIndexes()})
        items = [self.file_table.item(r, 0).text() for r in rows]
        if not items:
            QMessageBox.warning(self, "Compress", "No items selected.")
            return
        name, ok = QInputDialog.getText(self, "Compress", "Enter archive name:")
        if not ok or not name: return
        archive_path = os.path.join(self.logic.current_path, name + ".zip")
        dlg = QProgressDialog("Compressing...", "Cancel", 0, len(items), self)
        dlg.setWindowModality(Qt.WindowModal)
        with zipfile.ZipFile(archive_path, 'w') as zf:
            for i, fname in enumerate(items):
                if dlg.wasCanceled(): break
                path = os.path.join(self.logic.current_path, fname)
                if os.path.isdir(path):
                    for root, dirs, files in os.walk(path):
                        for f in files:
                            full = os.path.join(root, f)
                            zf.write(full, os.path.relpath(full, self.logic.current_path))
                else:
                    zf.write(path, fname)
                dlg.setValue(i+1)
        dlg.close()
        self.logic.load_directory(self.logic.current_path)

    def extract_item(self):
        """Extract selected zip archive into current directory."""
        selected = self.file_table.currentItem()
        if not selected: return
        path = os.path.join(self.logic.current_path, selected.text())
        ext = os.path.splitext(path)[1].lower()
        if ext != ".zip":
            QMessageBox.warning(self, "Extract", "Selected file is not a zip archive.")
            return
        try:
            shutil.unpack_archive(path, self.logic.current_path)
            self.logic.load_directory(self.logic.current_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to extract: {e}")

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

    def create_new_folder(self):
        """Create a new folder in the current directory."""
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            folder_path = os.path.join(self.logic.current_path, folder_name)
            try:
                os.mkdir(folder_path)
                self.logic.load_directory(self.logic.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create folder: {e}")

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
        # Use Windows Shell 'Open With' dialog if on Windows
        if platform.system() == "Windows":
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "openas", file_path, None, None, 1)
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open with Windows dialog: {e}")
        # Fallback: select program manually
        program, _ = QFileDialog.getOpenFileName(self, "Select program to open with", "", "Executables (*.exe);;All Files (*)")
        if program:
            try:
                subprocess.Popen([program, file_path])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def show_menu(self):
        """Show a three-point menu with options."""
        menu = QMenu(self)
        toggle_hidden_action = QAction("Show Hidden Files", self)
        toggle_hidden_action.setCheckable(True)
        toggle_hidden_action.setChecked(self.logic.show_hidden)
        toggle_hidden_action.triggered.connect(self.logic.toggle_hidden_files)
        # Dark mode toggle
        toggle_theme_action = QAction("Dark Mode", self)
        toggle_theme_action.setCheckable(True)
        toggle_theme_action.setChecked(self.dark_mode)
        toggle_theme_action.triggered.connect(self.toggle_dark_mode)
        # Toggle preview pane
        preview_action = QAction("Show Preview", self)
        preview_action.setCheckable(True)
        preview_action.setChecked(self.preview_visible)
        # Use toggled so checked state is passed
        preview_action.toggled.connect(self.toggle_preview)
        menu.addAction(preview_action)
        # Select visible details
        details_action = QAction("Select Details...", self)
        details_action.triggered.connect(self.show_details_dialog)
        menu.addAction(details_action)

        menu.addAction(toggle_hidden_action)
        menu.addAction(toggle_theme_action)
        menu.exec_(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))

    def toggle_dark_mode(self):
        """Toggle between light and dark themes."""
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.setStyleSheet(self.load_dark_styles())
        else:
            self.setStyleSheet(self.load_styles())

    def load_dark_styles(self):
        return '''
        QMainWindow { background-color: #2e2e2e; color: #f0f0f0; }
        QFrame { background-color: #3c3c3c; border-radius: 8px; }
        QLabel { color: #f0f0f0; }
        QPushButton { color: #f0f0f0; }
        '''

    def update_breadcrumb(self, path):
        """Update the breadcrumb buttons with the current path."""
        # Clear existing breadcrumb items
        for i in reversed(range(self.breadcrumb_layout.count())):
            widget = self.breadcrumb_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        # Build breadcrumb path parts
        parts = Path(path).parts
        cumulative = ""
        for idx, part in enumerate(parts):
            # Build cumulative path for this segment
            cumulative = os.path.join(cumulative, part) if cumulative else part
            # Add separator
            if idx > 0:
                sep = QLabel(" > ")
                self.breadcrumb_layout.addWidget(sep)
            # Add clickable part
            btn = QPushButton(part)
            btn.setFlat(True)
            btn.setStyleSheet("color: blue; background: none; border: none; padding: 0;")
            btn.clicked.connect(lambda checked, p=cumulative: self.logic.load_directory(p))
            self.breadcrumb_layout.addWidget(btn)

    def load_styles(self):
        return """
        /* Theme variables */
        QWidget {
            --primary-bg: #ffffff;
            --secondary-bg: #f8f9fa;
            --accent-color: #0078d4;
            --text-primary: #323130;
            --text-secondary: #605e5c;
            --border-color: #e1e1e1;
            --border-radius: 8px;
            --shadow: 0px 2px 8px rgba(0,0,0,0.1);
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            color: var(--text-primary);
            background: var(--primary-bg);
        }

        /* Frames and panels */
        QFrame {
            background: var(--secondary-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
        }

        /* Sidebar styling */
        QFrame#sidebar {
            background: var(--secondary-bg);
            border: none;
        }
        QPushButton#sidebarButton {
            background: var(--secondary-bg);
            color: var(--text-primary);
            border: none;
            border-radius: var(--border-radius);
            padding: 8px 12px;
            text-align: left;
        }
        QPushButton#sidebarButton:hover {
            background: var(--accent-color);
            color: #ffffff;
        }

        /* Header styling */
        QFrame#headerFrame {
            background: var(--primary-bg);
            border-bottom: 1px solid var(--border-color);
        }        QPushButton#menuButton {
            background: none;
            border: none;
            color: var(--text-secondary);
            padding: 4px;
        }
        QPushButton#menuButton:hover {
            background: var(--secondary-bg);
            color: var(--text-primary);
        }

        /* Search bar */
        QLineEdit#searchBar {
            background: var(--primary-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 4px 8px;
            min-height: 24px;
        }

        /* Table styling */
        QTableWidget {
            background: var(--primary-bg);
            alternate-background-color: var(--secondary-bg);
            gridline-color: var(--border-color);
        }
        QTableWidget::item:selected {
            background: var(--accent-color);
            color: #ffffff;
        }
        QHeaderView::section {
            background: var(--secondary-bg);
            color: var(--text-secondary);
            padding: 4px;
            border: none;
            border-bottom: 2px solid var(--accent-color);
        }

        /* Scrollbar styling */
        QScrollBar:vertical, QScrollBar:horizontal {
            background: var(--secondary-bg);
            border-radius: var(--border-radius);
            width: 8px;
            height: 8px;
        }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background: var(--border-color);
            border-radius: 4px;
        }
        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
            background: var(--accent-color);
        }

        /* Preview area */
        QLabel#previewLabel {
            background: var(--secondary-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 8px;
        }
        """

    def load_column_settings(self):
        """Load visible columns preferences."""
        visible = self.settings.value("visible_columns", None)
        if visible is None:
            indices = list(range(self.file_table.columnCount()))
        else:
            indices = [int(i) for i in visible]
        for i in range(self.file_table.columnCount()):
            self.file_table.setColumnHidden(i, i not in indices)

    def load_column_widths(self):
        """Load column widths based on saved percentages for current table width."""
        percents = self.settings.value("column_percents", None)
        header = self.file_table.horizontalHeader()
        # allow resizing handles and moving sections
        header.setSectionsMovable(True)
        header.setStretchLastSection(False)
        table_width = self.file_table.viewport().width() or self.file_table.width()
        if percents:
            # apply saved percentages
            for i, p in enumerate(percents):
                try:
                    percent = float(p)
                    self.file_table.setColumnWidth(i, int(table_width * percent))
                except (IndexError, ValueError):
                    pass
        else:
            # no saved: enable interactive resizing for all columns
            for i in range(self.file_table.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.Interactive)
                # ensure interactive resize hint
                header.setHighlightSections(True)

    def save_column_widths(self):
        """Save current column widths as percentages for relative resizing."""
        widths = [self.file_table.columnWidth(i) for i in range(self.file_table.columnCount())]
        total = sum(widths)
        if total > 0:
            percents = [w / total for w in widths]
            self.settings.setValue("column_percents", [str(p) for p in percents])

    def resizeEvent(self, event):
        """Reapply proportional column widths when window is resized."""
        super().resizeEvent(event)
        self.load_column_widths()

    def show_details_dialog(self):
        """Show dialog to select which details (columns) are visible."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Details")
        layout = QVBoxLayout(dialog)
        checkboxes = []
        for i in range(self.file_table.columnCount()):
            name = self.file_table.horizontalHeaderItem(i).text()
            cb = QCheckBox(name)
            cb.setChecked(not self.file_table.isColumnHidden(i))
            layout.addWidget(cb)
            checkboxes.append((i, cb))
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(btn_box)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        if dialog.exec_() == QDialog.Accepted:
            visible = []
            for i, cb in checkboxes:
                show = cb.isChecked()
                self.file_table.setColumnHidden(i, not show)
                if show:
                    visible.append(i)
            self.settings.setValue("visible_columns", [str(i) for i in visible])

    def _table_drag_enter(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _table_drop(self, event):
        for url in event.mimeData().urls():
            src = url.toLocalFile()
            dest = os.path.join(self.logic.current_path, os.path.basename(src))
            try:
                # Copy file or directory
                if os.path.isdir(src):
                    shutil.copytree(src, dest)
                else:
                    shutil.copy2(src, dest)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import item: {e}")
        self.logic.load_directory(self.logic.current_path)

    def _table_drag_move(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def filter_files(self, text):
        """Filter table rows based on search text."""
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item:
                match = text.lower() in item.text().lower()
                self.file_table.setRowHidden(row, not match)

    def on_selection_changed(self, selected, deselected):
        """Update preview when selection changes."""
        items = self.file_table.selectedItems()
        if not items:
            return
        file_name = items[0].text()
        file_path = os.path.join(self.logic.current_path, file_name)
        self.show_preview(file_path)

    def show_preview(self, file_path):
        """Show a simple preview for images or filename for other types."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            pixmap = QPixmap(file_path)
            self.preview_label.setPixmap(pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio))
        else:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText(os.path.basename(file_path))

    def toggle_preview(self, checked: bool):
        """Show or hide the preview pane and reload column layouts."""
        self.preview_visible = checked
        self.settings.setValue("preview_visible", self.preview_visible)
        self.content_splitter.widget(1).setVisible(self.preview_visible)        # Adjust columns to new available width
        self.load_column_widths()

