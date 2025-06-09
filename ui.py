from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QWidget, QSplitter, QFrame, QHeaderView, QMenu, QAction, QInputDialog, QMessageBox, QLineEdit,
    QProgressDialog, QFileDialog, QAbstractItemView, QDialog, QCheckBox, QDialogButtonBox, QGridLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QPoint, QSize, QSettings, QMimeData
from PyQt5.QtGui import QIcon, QCursor, QPixmap
import os
import time
import shutil
import zipfile
import subprocess
import platform
import ctypes
import winreg
import shlex
import string
from ctypes import wintypes, windll, create_unicode_buffer, byref
from logic import FileManagerLogic
from pathlib import Path


class HomeView(QWidget):
    def __init__(self, logic):
        super().__init__()
        self.logic = logic
        self.setObjectName("homeView")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the home view UI with icon grid."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setObjectName("homeScrollArea")
        
        # Main content widget
        content = QWidget()
        content.setObjectName("homeContent")
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(40)
          # Quick Access section - include drives
        quick_access_items = [
            ("Downloads", "downloads", self.logic.downloads_path),
            ("Documents", "documents", self.logic.documents_path), 
            ("Pictures", "pictures", self.logic.pictures_path),
            ("Music", "music", self.logic.music_path)
        ]
        
        # Add available drives to Quick Access
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                quick_access_items.append((f"Drive {letter}:", "home", drive))
        
        self.create_section("Quick Access", quick_access_items, content_layout)
          # Recent Files section
        recent_files = self.get_recent_files()
        if recent_files:
            self.create_recent_files_table("Recently Used", recent_files, content_layout)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def create_section(self, title, items, parent_layout):
        """Create a section with title and icon grid."""
        # Section title
        title_label = QLabel(title)
        title_label.setObjectName("homeSectionTitle")
        parent_layout.addWidget(title_label)
          # Grid for icons
        grid = QGridLayout()
        grid.setSpacing(25)
        
        cols = 4  # 4 items per row for single row Quick Access
        for i, (name, icon, path) in enumerate(items):
            row = i // cols
            col = i % cols
            
            # Create icon button
            btn = QPushButton()
            btn.setObjectName("homeIconButton")
            btn.setFixedSize(160, 130)  # Much bigger boxes
            
            # Set icon
            btn.setIcon(QIcon(f"icons/{icon}.svg"))
            btn.setIconSize(QSize(64, 64))  # Bigger icons
            
            # Set text below icon
            btn.setText(name)
              # Connect click
            btn.clicked.connect(lambda checked, p=path: self.logic.load_directory(p))
            
            grid.addWidget(btn, row, col)
        
        parent_layout.addLayout(grid)
    
    def get_recent_files(self):
        """Get recently modified files from common locations."""
        recent = []
        locations = [self.logic.downloads_path, self.logic.documents_path, 
                    self.logic.pictures_path, self.logic.music_path]
        
        for location in locations:
            if os.path.exists(location):
                try:
                    files = []
                    for file in os.listdir(location):
                        file_path = os.path.join(location, file)
                        if os.path.isfile(file_path):  # Only files, not directories
                            mtime = os.path.getmtime(file_path)
                            files.append((file, file_path, mtime))
                    
                    # Sort by modification time and take 2 most recent
                    files.sort(key=lambda x: x[2], reverse=True)
                    for file, path, _ in files[:2]:
                        if len(recent) < 8:  # Limit to 8 items for table view
                            recent.append((file, "file", path))  # Use full path
                except:
                    pass
        
        return recent

    def create_recent_files_table(self, title, items, parent_layout):
        """Create a table section for recent files."""
        # Section title
        title_label = QLabel(title)
        title_label.setObjectName("homeSectionTitle")
        parent_layout.addWidget(title_label)
        
        # Create table
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        table = QTableWidget()
        table.setObjectName("recentFilesTable")
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Name", "Location", "Modified"])
        table.setRowCount(len(items))
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.setFixedHeight(min(700, len(items) * 35 + 50))  # Taller table, minimum 300px
        
        # Configure column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Name column stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Location fits content
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Modified fits content
        
        # Populate table
        for i, (name, _, full_path) in enumerate(items):
            # Name
            name_item = QTableWidgetItem(name)
            name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            table.setItem(i, 0, name_item)
            
            # Location (parent directory)
            location = os.path.dirname(full_path)
            location_item = QTableWidgetItem(location)
            location_item.setFlags(Qt.ItemIsEnabled)
            table.setItem(i, 1, location_item)
            
            # Modified time
            try:
                import time
                mtime = os.path.getmtime(full_path)
                modified = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
            except:
                modified = "Unknown"
            modified_item = QTableWidgetItem(modified)
            modified_item.setFlags(Qt.ItemIsEnabled)
            table.setItem(i, 2, modified_item)
            
            # Store full path for click handling
            name_item.setData(Qt.UserRole, full_path)
        
        # Connect double click to navigate to parent and highlight file
        table.cellDoubleClicked.connect(self.on_recent_file_clicked)
        
        parent_layout.addWidget(table)
    
    def on_recent_file_clicked(self, row, column):
        """Handle clicking on a recent file - navigate to parent folder and highlight file."""
        table = self.sender()
        name_item = table.item(row, 0)
        if name_item:
            file_path = name_item.data(Qt.UserRole)
            if file_path and os.path.exists(file_path):
                # Get parent directory
                parent_dir = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)
                
                # Navigate to parent directory
                self.logic.load_directory(parent_dir)
                
                # After directory loads, highlight the specific file
                # We need to do this after the table is populated
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(100, lambda: self.highlight_file(file_name))
    
    def highlight_file(self, file_name):
        """Highlight and scroll to a specific file in the main file table."""
        # Find the file in the table
        for row in range(self.logic.ui.file_table.rowCount()):
            item = self.logic.ui.file_table.item(row, 0)
            if item and item.text() == file_name:
                # Select and scroll to the item
                self.logic.ui.file_table.selectRow(row)
                self.logic.ui.file_table.scrollToItem(item)
                break

class FileManagerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"AI File Manager")
        self.setWindowIcon(QIcon("icons/icon.png"))
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet(self.load_styles())

        # Initialize logic
        self.logic = FileManagerLogic(self)

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Top toolbar with search and menu
        self.create_toolbar()

        # Content area with sidebar and file view
        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # Sidebar
        self.create_sidebar()

        # Main file area
        self.create_main_area()
        
        # Create home view
        self.home_view = HomeView(self.logic)

        # Add content to main layout
        self.main_layout.addWidget(self.content_widget)

        # Initialize settings and preferences
        self.setup_preferences()

        # Load the default directory (Home)
        self.logic.load_directory(self.logic.home_path)

    def create_toolbar(self):
        """Create the top toolbar with navigation and search."""
        self.toolbar = QFrame()
        self.toolbar.setObjectName("toolbar")
        self.toolbar.setFixedHeight(60)
        
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(20, 10, 20, 10)
        toolbar_layout.setSpacing(15)

        # Navigation buttons
        nav_container = QWidget()
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(5)

        # Refresh and Home buttons using local vars
        refresh_btn = QPushButton()
        refresh_btn.setObjectName("navButton")
        refresh_btn.setIcon(QIcon("icons/reload.svg"))
        refresh_btn.setIconSize(QSize(24, 24))
        refresh_btn.clicked.connect(lambda: self.logic.load_directory(self.logic.current_path))
        nav_layout.addWidget(refresh_btn)

        home_btn = QPushButton()
        home_btn.setObjectName("navButton")
        home_btn.setIcon(QIcon("icons/home.svg"))
        home_btn.setIconSize(QSize(24, 24))
        home_btn.clicked.connect(lambda: self.logic.load_directory(self.logic.home_path))
        nav_layout.addWidget(home_btn)

        # Breadcrumb navigation
        self.breadcrumb_widget = QWidget()
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_widget)
        self.breadcrumb_layout.setContentsMargins(15, 0, 15, 0)
        self.breadcrumb_layout.setSpacing(5)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("Search files and folders...")
        self.search_bar.setFixedWidth(300)
        self.search_bar.textChanged.connect(self.filter_files)

        # Menu button
        self.menu_button = QPushButton()
        self.menu_button.setObjectName("menuButton")
        self.menu_button.setIcon(QIcon("icons/three-point.svg"))
        self.menu_button.setIconSize(QSize(20, 20))
        self.menu_button.clicked.connect(self.show_menu)

        # Add AI Organize icon button
        self.ai_btn = QPushButton()
        self.ai_btn.setObjectName("aiButton")
        self.ai_btn.setIcon(QIcon("icons/ai.svg"))
        self.ai_btn.setIconSize(QSize(24, 24))
        self.ai_btn.setToolTip("Click or drop a file here for AI organize")
        self.ai_btn.clicked.connect(self.ai_organize_selected)
        self.ai_btn.setAcceptDrops(True)
        self.ai_btn.dragEnterEvent = self.ai_btn_drag_enter
        self.ai_btn.dropEvent = self.ai_btn_drop
        toolbar_layout.addWidget(self.ai_btn)

        # Add to toolbar
        toolbar_layout.addWidget(nav_container)
        toolbar_layout.addWidget(self.breadcrumb_widget, 1)
        toolbar_layout.addWidget(self.search_bar)
        toolbar_layout.addWidget(self.menu_button)

        self.main_layout.addWidget(self.toolbar)

    def create_sidebar(self):
        """Create the modern sidebar."""
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 20)
        sidebar_layout.setSpacing(8)

        # Quick access label
        quick_label = QLabel("Quick access")
        quick_label.setObjectName("sidebarLabel")
        sidebar_layout.addWidget(quick_label)

        # Add sidebar buttons
        self.add_sidebar_button("Home", "home", self.logic.home_path, sidebar_layout)
        self.add_sidebar_button("Downloads", "downloads", self.logic.downloads_path, sidebar_layout)
        self.add_sidebar_button("Documents", "documents", self.logic.documents_path, sidebar_layout)
        self.add_sidebar_button("Pictures", "pictures", self.logic.pictures_path, sidebar_layout)
        self.add_sidebar_button("Music", "music", self.logic.music_path, sidebar_layout)

        sidebar_layout.addStretch()
        self.content_layout.addWidget(self.sidebar)

    def create_main_area(self):
        """Create the main file viewing area."""
        self.main_area = QWidget()
        main_area_layout = QVBoxLayout(self.main_area)
        main_area_layout.setContentsMargins(0, 0, 0, 0)
        main_area_layout.setSpacing(0)

        # File table
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(6)
        self.file_table.setHorizontalHeaderLabels(["Name", "Type", "Size", "Permissions", "Last Modified", "Empty"])
        self.file_table.setObjectName("fileTable")
        
        # Table configuration
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionsMovable(True)
        header.setSectionsClickable(True)
        header.setStretchLastSection(False)
        self.file_table.horizontalHeader().sectionClicked.connect(self.logic.sort_table)
        self.file_table.setShowGrid(False)
        self.file_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.file_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.file_table.setDragEnabled(True)
        self.file_table.setAcceptDrops(True)
        self.file_table.setDragDropMode(QAbstractItemView.DragDrop)
        self.file_table.dragEnterEvent = self._table_drag_enter
        self.file_table.dropEvent = self._table_drop
        self.file_table.dragMoveEvent = self._table_drag_move
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.cellDoubleClicked.connect(self.logic.on_table_double_click)

        # Add context menu to file table
        self.file_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)

        # Connect selection change to preview update
        self.file_table.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Create splitter for table and preview
        self.content_splitter = QSplitter(Qt.Horizontal)
        self.content_splitter.addWidget(self.file_table)
        
        # Preview panel
        self.preview_label = QLabel("Select a file to preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setObjectName("previewPanel")
        self.preview_label.setFixedWidth(300)
        self.content_splitter.addWidget(self.preview_label)

        main_area_layout.addWidget(self.content_splitter)
        self.content_layout.addWidget(self.main_area)
        
    def show_home_view(self):
        """Show the home view and hide the file table."""
        # Remove main area if it's currently shown
        if self.main_area.parent():
            self.content_layout.removeWidget(self.main_area)
            self.main_area.hide()
        
        # Add and show home view
        self.content_layout.addWidget(self.home_view)
        self.home_view.show()
    
    def show_file_view(self):
        """Show the file table and hide the home view."""
        # Remove home view if it's currently shown
        if self.home_view.parent():
            self.content_layout.removeWidget(self.home_view)
            self.home_view.hide()
        
        # Add and show main area
        self.content_layout.addWidget(self.main_area)
        self.main_area.show()

    def setup_preferences(self):
        """Initialize settings and preferences."""
        self.clipboard = []
        self.dark_mode = False
        self.settings = QSettings("MyCompany", "AIFileManager")
        self.load_column_settings()
        self.load_column_widths()
        self.file_table.horizontalHeader().sectionResized.connect(lambda idx, old, new: self.save_column_widths())
        self.preview_visible = self.settings.value("preview_visible", True, type=bool)
        self.content_splitter.widget(1).setVisible(self.preview_visible)

    def add_sidebar_button(self, name, icon_filename, path, layout):
        """Add a button to the sidebar."""
        button = QPushButton(name)
        button.setIcon(QIcon(f"icons/{icon_filename}.svg"))
        button.setIconSize(QSize(24, 24))
        button.setObjectName("sidebarButton")
        button.clicked.connect(lambda: self.logic.load_directory(path))
        layout.addWidget(button)

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
        menu.addAction(compress_action)
        menu.addAction(extract_action)
        menu.addSeparator()
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(open_with_action)

        # Show the context menu
        menu.exec_(self.file_table.mapToGlobal(position))

    def copy_item(self):
        """Copy selected items to clipboard."""
        selected_items = self.file_table.selectionModel().selectedRows()
        self.clipboard = []
        for index in selected_items:
            item_name = self.file_table.item(index.row(), 0).text()
            item_path = os.path.join(self.logic.current_path, item_name)
            self.clipboard.append(item_path)

    def paste_item(self):
        """Paste items from clipboard."""
        if not self.clipboard:
            return
        
        for source_path in self.clipboard:
            source_name = os.path.basename(source_path)
            dest_path = os.path.join(self.logic.current_path, source_name)
            
            try:
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, dest_path)
                else:
                    shutil.copy2(source_path, dest_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to paste {source_name}: {str(e)}")
        
        self.logic.load_directory(self.logic.current_path)

    def compress_items(self):
        """Compress selected items into a zip file."""
        selected_items = self.file_table.selectionModel().selectedRows()
        if not selected_items:
            return
            
        zip_name, ok = QInputDialog.getText(self, "Compress", "Enter zip file name:")
        if not ok or not zip_name:
            return
            
        if not zip_name.endswith('.zip'):
            zip_name += '.zip'
            
        zip_path = os.path.join(self.logic.current_path, zip_name)
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for index in selected_items:
                    item_name = self.file_table.item(index.row(), 0).text()
                    item_path = os.path.join(self.logic.current_path, item_name)
                    
                    if os.path.isdir(item_path):
                        for root, dirs, files in os.walk(item_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, self.logic.current_path)
                                zipf.write(file_path, arcname)
                    else:
                        zipf.write(item_path, item_name)
            
            self.logic.load_directory(self.logic.current_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create zip file: {str(e)}")

    def extract_item(self):
        """Extract selected zip file."""
        selected_items = self.file_table.selectionModel().selectedRows()
        if len(selected_items) != 1:
            return
            
        item_name = self.file_table.item(selected_items[0].row(), 0).text()
        item_path = os.path.join(self.logic.current_path, item_name)
        
        if not item_name.lower().endswith('.zip'):
            QMessageBox.warning(self, "Error", "Selected file is not a zip file.")
            return
            
        try:
            with zipfile.ZipFile(item_path, 'r') as zipf:
                zipf.extractall(self.logic.current_path)
            self.logic.load_directory(self.logic.current_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to extract zip file: {str(e)}")

    def create_new_file(self):
        """Create a new file."""
        file_name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and file_name:
            file_path = os.path.join(self.logic.current_path, file_name)
            try:
                with open(file_path, 'w') as f:
                    f.write("")
                self.logic.load_directory(self.logic.current_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create file: {str(e)}")

    def create_new_folder(self):
        """Create a new folder."""
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            folder_path = os.path.join(self.logic.current_path, folder_name)
            try:
                os.makedirs(folder_path)
                self.logic.load_directory(self.logic.current_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create folder: {str(e)}")

    def rename_item(self):
        """Rename selected item."""
        selected_items = self.file_table.selectionModel().selectedRows()
        if len(selected_items) != 1:
            return
            
        old_name = self.file_table.item(selected_items[0].row(), 0).text()
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            old_path = os.path.join(self.logic.current_path, old_name)
            new_path = os.path.join(self.logic.current_path, new_name)
            try:
                os.rename(old_path, new_path)
                self.logic.load_directory(self.logic.current_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to rename: {str(e)}")

    def delete_item(self):
        """Delete selected items."""
        selected_items = self.file_table.selectionModel().selectedRows()
        if not selected_items:
            return
            
        reply = QMessageBox.question(self, "Delete", "Are you sure you want to delete the selected items?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            for index in selected_items:
                item_name = self.file_table.item(index.row(), 0).text()
                item_path = os.path.join(self.logic.current_path, item_name)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to delete {item_name}: {str(e)}")
            
            self.logic.load_directory(self.logic.current_path)

    def open_with_program(self):
        """Show 'Open With' dialog for the selected file across platforms."""
        selected_items = self.file_table.selectionModel().selectedRows()
        if not selected_items:
            return

        item_name = self.file_table.item(selected_items[0].row(), 0).text()
        file_path = os.path.join(self.logic.current_path, item_name)

        try:
            system = platform.system()
            if system == 'Windows':
                os.system(f'rundll32.exe shell32.dll,OpenAs_RunDLL {file_path}')
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', '-R', file_path])
            elif system == 'Linux':
                # Try common Linux desktop environments
                desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
                if 'kde' in desktop:
                    subprocess.run(['kde-open5', '--chooser', file_path])
                elif 'gnome' in desktop:
                    subprocess.run(['gio', 'open', '--ask', file_path])
                else:
                    # Fallback to xdg-open for other Linux environments
                    subprocess.run(['xdg-open', file_path])
            else:
                QMessageBox.warning(self, "Error", f"Unsupported operating system: {system}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open 'Open With' dialog: {str(e)}")
    def show_menu(self):
        """Show the main menu."""
        menu = QMenu(self)
        
        # Toggle hidden files
        toggle_hidden_action = QAction("Show Hidden Files", self)
        toggle_hidden_action.setCheckable(True)
        toggle_hidden_action.setChecked(self.logic.show_hidden)
        toggle_hidden_action.triggered.connect(self.logic.toggle_hidden_files)
        
        # Toggle dark mode
        toggle_theme_action = QAction("Dark Mode", self)
        toggle_theme_action.setCheckable(True)
        toggle_theme_action.setChecked(self.dark_mode)
        toggle_theme_action.triggered.connect(self.toggle_dark_mode)
        
        # Toggle preview
        preview_action = QAction("Show Preview", self)
        preview_action.setCheckable(True)
        preview_action.setChecked(self.preview_visible)
        preview_action.toggled.connect(self.toggle_preview)
        
        # Select visible details
        details_action = QAction("Select Details...", self)
        details_action.triggered.connect(self.show_details_dialog)
        
        menu.addAction(toggle_hidden_action)
        menu.addAction(toggle_theme_action)
        menu.addSeparator()
        menu.addAction(preview_action)
        menu.addAction(details_action)
        
        menu.exec_(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))

    def toggle_dark_mode(self):
        """Toggle between light and dark themes."""
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.setStyleSheet(self.load_dark_styles())
        else:
            self.setStyleSheet(self.load_styles())

    def load_dark_styles(self):
        """Load dark theme styles."""
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
        """Load modern Chromebook-inspired styles."""
        return """
        /* Modern Chromebook-inspired design */
        QMainWindow {
            background-color: #ffffff;
            color: #202124;
            font-family: 'Google Sans', 'Roboto', 'Segoe UI', sans-serif;
            font-size: 14px;
        }
        
        /* Toolbar styling */
        QFrame#toolbar {
            background-color: #ffffff;
            border: none;
            border-bottom: 1px solid #dadce0;
        }
        
        /* Navigation buttons */
        QPushButton#navButton {
            background-color: transparent;
            border: 1px solid #dadce0;
            border-radius: 20px;
            color: #5f6368;
            font-size: 16px;
            min-width: 36px;
            min-height: 36px;
            max-width: 36px;
            max-height: 36px;
        }
        QPushButton#navButton:hover {
            background-color: #f8f9fa;
            border-color: #c4c7c5;
        }
        QPushButton#navButton:pressed {
            background-color: #f1f3f4;
        }
        
        /* Search bar */
        QLineEdit#searchBar {
            background-color: #f8f9fa;
            border: 1px solid #dadce0;
            border-radius: 24px;
            padding: 8px 16px;
            color: #202124;
            font-size: 14px;
        }
        QLineEdit#searchBar:focus {
            background-color: #ffffff;
            border-color: #1a73e8;
            outline: none;
        }
        
        /* Menu button */
        QPushButton#menuButton {
            background-color: transparent;
            border: none;
            border-radius: 20px;
            color: #5f6368;
            font-size: 18px;
            min-width: 40px;
            min-height: 40px;
            max-width: 40px;
            max-height: 40px;
        }
        QPushButton#menuButton:hover {
            background-color: #f8f9fa;
        }
          /* Home View Styling */
        QWidget#homeView {
            background-color: #ffffff;
        }
        
        QWidget#homeContent {
            background-color: #ffffff;
        }
        
        QScrollArea#homeScrollArea {
            background-color: #ffffff;
            border: none;
        }
        
        QLabel#homeSectionTitle {
            color: #202124;
            font-size: 24px;
            font-weight: 400;
            margin-bottom: 16px;
            padding-left: 8px;
        }
        
        QPushButton#homeIconButton {
            background-color: #ffffff;
            border: 1px solid #dadce0;
            border-radius: 12px;
            color: #202124;
            font-size: 14px;
            font-weight: 400;
            text-align: center;
            padding: 12px 8px;
        }
        QPushButton#homeIconButton:hover {
            background-color: #f8f9fa;
            border-color: #c4c7c5;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }        QPushButton#homeIconButton:pressed {
            background-color: #f1f3f4;
        }
        
        /* Recent Files Table */
        QTableWidget#recentFilesTable {
            background-color: #ffffff;
            border: 1px solid #dadce0;
            border-radius: 8px;
            gridline-color: #f0f0f0;
            selection-background-color: #e8f0fe;
            alternate-background-color: #fafbfc;
            margin-bottom: 16px;
        }
        
        QTableWidget#recentFilesTable::item {
            border-bottom: 1px solid #f0f0f0;
            padding: 8px;
            color: #202124;
        }
        
        QTableWidget#recentFilesTable::item:selected {
            background-color: #e8f0fe;
            color: #1a73e8;
        }
        
        QTableWidget#recentFilesTable::item:hover {
            background-color: #f8f9fa;
        }
        
        /* Sidebar styling */
        QFrame#sidebar {
            background-color: #f8f9fa;
            border: none;
            border-right: 1px solid #dadce0;
        }
        
        QLabel#sidebarLabel {
            color: #5f6368;
            font-size: 12px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 8px;
            padding-left: 4px;
        }
        
        QPushButton#sidebarButton {
            background-color: transparent;
            border: none;
            border-radius: 20px;
            color: #202124;
            font-size: 14px;
            padding: 8px 16px;
            text-align: left;
            margin: 2px 0px;
            min-height: 32px;
        }
        QPushButton#sidebarButton:hover {
            background-color: #e8f0fe;
            color: #1a73e8;
        }
        QPushButton#sidebarButton:pressed {
            background-color: #d2e3fc;
        }
        
        /* File table styling */
        QTableWidget#fileTable {
            background-color: #ffffff;
            border: none;
            gridline-color: transparent;
            selection-background-color: #e8f0fe;
            alternate-background-color: #fafbfc;
        }
        
        QTableWidget#fileTable::item {
            border-bottom: 1px solid #f0f0f0;
            padding: 8px;
            color: #202124;
        }
        
        QTableWidget#fileTable::item:selected {
            background-color: #e8f0fe;
            color: #1a73e8;
        }
        
        QTableWidget#fileTable::item:hover {
            background-color: #f8f9fa;
        }
        
        /* Table header */
        QHeaderView::section {
            background-color: #ffffff;
            color: #5f6368;
            border: none;
            border-bottom: 2px solid #dadce0;
            padding: 12px 8px;
            font-weight: 500;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        QHeaderView::section:hover {
            background-color: #f8f9fa;
        }
        
        /* Preview panel */
        QLabel#previewPanel {
            background-color: #fafbfc;
            border: none;
            border-left: 1px solid #dadce0;
            color: #5f6368;
            padding: 20px;
            font-size: 14px;
        }
        
        /* Scrollbars */
        QScrollBar:vertical {
            background-color: transparent;
            width: 12px;
            border-radius: 6px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #dadce0;
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #bdc1c6;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
            subcontrol-position: none;
        }
        
        QScrollBar:horizontal {
            background-color: transparent;
            height: 12px;
            border-radius: 6px;
            margin: 0px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #dadce0;
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #bdc1c6;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
            subcontrol-position: none;
        }
        
        /* Breadcrumb styling */
        QPushButton {
            background-color: transparent;
            border: none;
            color: #1a73e8;
            font-size: 14px;
            padding: 4px 8px;
            text-decoration: none;
        }
        QPushButton:hover {
            background-color: #e8f0fe;
            border-radius: 4px;
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
        header.setSectionsMovable(True)
        header.setStretchLastSection(False)
        table_width = self.file_table.viewport().width() or self.file_table.width()
        if percents:
            for i, p in enumerate(percents):
                if i < self.file_table.columnCount():
                    self.file_table.setColumnWidth(i, int(table_width * float(p)))

    def save_column_widths(self):
        """Save column widths as percentages."""
        table_width = self.file_table.viewport().width()
        if table_width > 0:
            percents = []
            for i in range(self.file_table.columnCount()):
                width = self.file_table.columnWidth(i)
                percent = width / table_width
                percents.append(str(percent))
            self.settings.setValue("column_percents", percents)

    def resizeEvent(self, event):
        """Handle window resize events."""
        super().resizeEvent(event)
        self.load_column_widths()

    def show_details_dialog(self):
        """Show dialog to select which columns are visible."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Details")
        dialog.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        checkboxes = []
        headers = ["Name", "Type", "Size", "Permissions", "Last Modified", "Empty"]
        
        for i, header in enumerate(headers):
            checkbox = QCheckBox(header)
            checkbox.setChecked(not self.file_table.isColumnHidden(i))
            checkboxes.append(checkbox)
            layout.addWidget(checkbox)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            visible_indices = []
            for i, checkbox in enumerate(checkboxes):
                if checkbox.isChecked():
                    visible_indices.append(i)
                self.file_table.setColumnHidden(i, not checkbox.isChecked())
            
            self.settings.setValue("visible_columns", [str(i) for i in visible_indices])

    def _table_drag_enter(self, event):
        """Handle drag enter events for the table."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def _table_drop(self, event):
        """Handle drop events for the table."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                source_path = url.toLocalFile()
                if source_path:
                    dest_name = os.path.basename(source_path)
                    dest_path = os.path.join(self.logic.current_path, dest_name)
                    
                    try:
                        if os.path.isdir(source_path):
                            shutil.copytree(source_path, dest_path)
                        else:
                            shutil.copy2(source_path, dest_path)
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to copy {dest_name}: {str(e)}")
            
            self.logic.load_directory(self.logic.current_path)
            event.accept()
        else:
            event.ignore()

    def _table_drag_move(self, event):
        """Handle drag move events for the table."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def ai_btn_drag_enter(self, event):
        """Allow dragging of files onto AI button."""
        mime = event.mimeData()
        if mime.hasUrls() and len(mime.urls()) == 1 and mime.urls()[0].isLocalFile():
            event.acceptProposedAction()
        else:
            event.ignore()

    def ai_btn_drop(self, event):
        """Handle file drop onto AI button and organize via AI."""
        mime = event.mimeData()
        if mime.hasUrls():
            urls = mime.urls()
            file_path = urls[0].toLocalFile()
            if os.path.isfile(file_path):
                # Trigger AI organization for dropped file
                suggested = self.logic.ai_organize_file(file_path)
                if not suggested:
                    QMessageBox.information(self, "AI Organize", "No suggestion could be made or AI feature is disabled.")
                else:
                    reply = QMessageBox.question(self, "AI Organize", f"AI suggests moving the file to:\n{suggested}\nProceed?", QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        try:
                            os.makedirs(os.path.dirname(suggested), exist_ok=True)
                            shutil.move(file_path, suggested)
                            QMessageBox.information(self, "AI Organize", "File moved successfully.")
                            self.logic.load_directory(self.logic.current_path)
                        except Exception as e:
                            QMessageBox.critical(self, "AI Organize", f"Error moving file: {e}")
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def filter_files(self, text):
        """Filter files based on search text."""
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item:
                visible = text.lower() in item.text().lower()
                self.file_table.setRowHidden(row, not visible)

    def on_selection_changed(self, selected, deselected):
        """Handle selection changes in the file table."""
        selected_rows = self.file_table.selectionModel().selectedRows()
        if selected_rows:
            item = self.file_table.item(selected_rows[0].row(), 0)
            if item:
                file_path = os.path.join(self.logic.current_path, item.text())
                self.show_preview(file_path)
        else:
            self.preview_label.setText("Select a file to preview")

    def show_preview(self, file_path):
        """Show preview of the selected file."""
        try:
            if os.path.isfile(file_path):
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                file_ext = os.path.splitext(file_name)[1].lower()
                
                preview_text = f"File: {file_name}\nSize: {self.logic.format_size(file_size)}\nType: {file_ext}"
                
                # Add more specific preview for text files
                if file_ext in ['.txt', '.py', '.js', '.html', '.css', '.md']:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(500)  # First 500 characters
                            preview_text += f"\n\nPreview:\n{content}"
                            if len(content) == 500:
                                preview_text += "..."
                    except:
                        pass
                
                self.preview_label.setText(preview_text)
            else:
                self.preview_label.setText("Folder selected")
        except Exception as e:
            self.preview_label.setText(f"Preview error: {str(e)}")

    def toggle_preview(self, checked: bool):
        """Toggle preview panel visibility."""
        self.preview_visible = checked
        self.content_splitter.widget(1).setVisible(checked)
        self.settings.setValue("preview_visible", checked)

    def ai_organize_selected(self):
        """Trigger AI-based file organization for the selected file."""
        # Get selected file
        selected_items = self.file_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "AI Organize", "Please select a file to organize.")
            return
        # Use first selected row
        row = selected_items[0].row()
        name_item = self.file_table.item(row, 0)
        if not name_item:
            return
        file_name = name_item.text()
        full_path = os.path.join(self.logic.current_path, file_name)
        if not os.path.isfile(full_path):
            QMessageBox.warning(self, "AI Organize", "Selected item is not a file.")
            return
        # Call AI logic
        suggested = self.logic.ai_organize_file(full_path)
        if not suggested:
            QMessageBox.information(self, "AI Organize", "No suggestion could be made or AI feature is disabled.")
            return
        # Ask to move file
        reply = QMessageBox.question(self, "AI Organize", f"AI suggests moving the file to:\n{suggested}\nProceed?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                os.makedirs(os.path.dirname(suggested), exist_ok=True)
                shutil.move(full_path, suggested)
                QMessageBox.information(self, "AI Organize", "File moved successfully.")
                # Reload directory
                self.logic.load_directory(self.logic.current_path)
            except Exception as e:
                QMessageBox.critical(self, "AI Organize", f"Error moving file: {e}")
