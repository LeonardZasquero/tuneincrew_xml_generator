import sys
import os
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QFileDialog, QScrollArea, 
                             QMessageBox, QGroupBox, QSpacerItem, QSizePolicy, QCheckBox,
                             QDockWidget)
from PyQt5.QtCore import Qt, QProcess, QSettings, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wave import WAVE

class DragDropLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.mp3', '.wav', '.flac', '.dds')):
                self.setText(file_path)
                # Notify parent to extract metadata if needed
                if hasattr(self.parent(), 'handle_dropped_audio'):
                    self.parent().handle_dropped_audio(file_path, self)

class SongWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.parent_app = parent
        self.initUI()
        
    def initUI(self):
        self.song_layout = QVBoxLayout(self)
        
        # File selection
        file_layout = QHBoxLayout()
        self.song_file_edit = DragDropLineEdit(self)
        self.song_file_edit.textChanged.connect(self.on_file_changed)
        song_browse_btn = QPushButton("Browse")
        song_browse_btn.clicked.connect(self.browse_audio_file)
        
        file_layout.addWidget(QLabel("Music File:"))
        file_layout.addWidget(self.song_file_edit)
        file_layout.addWidget(song_browse_btn)
        self.song_layout.addLayout(file_layout)
        
        # Song details
        details_layout = QHBoxLayout()
        
        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("Song Name:"))
        self.song_name_edit = QLineEdit()
        self.song_name_edit.textChanged.connect(self.on_data_changed)
        name_layout.addWidget(self.song_name_edit)
        
        artist_layout = QVBoxLayout()
        artist_layout.addWidget(QLabel("Artist:"))
        self.song_artist_edit = QLineEdit()
        self.song_artist_edit.textChanged.connect(self.on_data_changed)
        artist_layout.addWidget(self.song_artist_edit)
        
        year_layout = QVBoxLayout()
        year_layout.addWidget(QLabel("Year:"))
        self.song_year_edit = QLineEdit()
        self.song_year_edit.textChanged.connect(self.on_data_changed)
        year_layout.addWidget(self.song_year_edit)
        
        length_layout = QVBoxLayout()
        length_layout.addWidget(QLabel("Length (min:sec):"))
        self.song_length_edit = QLineEdit()
        self.song_length_edit.textChanged.connect(self.on_data_changed)
        length_layout.addWidget(self.song_length_edit)
        
        force_layout = QVBoxLayout()
        force_layout.addWidget(QLabel("Force:"))
        self.song_force_edit = QLineEdit("0")
        self.song_force_edit.textChanged.connect(self.on_data_changed)
        force_layout.addWidget(self.song_force_edit)
        
        details_layout.addLayout(name_layout)
        details_layout.addLayout(artist_layout)
        details_layout.addLayout(year_layout)
        details_layout.addLayout(length_layout)
        details_layout.addLayout(force_layout)
        
        self.song_layout.addLayout(details_layout)
        
        # Remove button
        self.remove_btn = QPushButton("Remove Song")
        self.song_layout.addWidget(self.remove_btn)
        
    def on_file_changed(self, text):
        """Handle when the file path changes"""
        if text and os.path.exists(text) and text.lower().endswith(('.mp3', '.wav', '.flac')):
            self.extract_audio_metadata(text)
        
    def on_data_changed(self):
        """Handle when any song data changes"""
        if self.parent_app:
            self.parent_app.update_song_data(self)
        
    def browse_audio_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", 
            "Audio Files (*.mp3 *.wav *.flac)"
        )
        if file_path:
            self.song_file_edit.setText(file_path)
            
    def extract_audio_metadata(self, file_path):
        try:
            # Get file extension to determine the type
            ext = os.path.splitext(file_path)[1].lower()
            
            # Load the file based on its type
            if ext == '.mp3':
                audio = MP3(file_path)
            elif ext == '.flac':
                audio = FLAC(file_path)
            elif ext == '.wav':
                audio = WAVE(file_path)
            else:
                return  # Unsupported format
            
            # Extract metadata with fallback for different tag formats
            title = None
            artist = None
            date = None
            
            # Try different tag formats for title
            for tag in ['TIT2', 'TITLE', 'Title', 'title']:
                if tag in audio.tags:
                    title = str(audio.tags[tag][0])
                    break
            
            # Try different tag formats for artist
            for tag in ['TPE1', 'ARTIST', 'Artist', 'artist']:
                if tag in audio.tags:
                    artist = str(audio.tags[tag][0])
                    break
            
            # Try different tag formats for date/year
            for tag in ['TDRC', 'DATE', 'Date', 'date', 'YEAR', 'Year', 'year']:
                if tag in audio.tags:
                    date = str(audio.tags[tag][0])
                    break
            
            # Update the UI fields if they're empty
            if not self.song_name_edit.text() and title:
                self.song_name_edit.setText(title)
                
            if not self.song_artist_edit.text() and artist:
                self.song_artist_edit.setText(artist)
                
            if not self.song_year_edit.text() and date:
                self.song_year_edit.setText(date)
                
            if not self.song_length_edit.text():
                length = audio.info.length
                minutes = int(length // 60)
                seconds = int(length % 60)
                self.song_length_edit.setText(f"{minutes}:{seconds:02d}")
                
        except Exception as e:
            # If metadata extraction fails, just continue silently
            print(f"Metadata extraction error: {e}")
            
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        # Handle file drops
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith(('.mp3', '.wav', '.flac')):
                    self.song_file_edit.setText(file_path)

class XMLGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("TuneInCrew", "XMLGenerator")
        self.initUI()
        self.current_file = None
        self.tuneincrew_path = None
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        
    def initUI(self):
        self.setWindowTitle('TuneInCrew Radio XML Generator')
        self.setGeometry(100, 100, 1000, 800)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_layout.addWidget(scroll_area)
        
        # Scroll content widget
        self.scroll_content = QWidget()
        scroll_area.setWidget(self.scroll_content)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        
        # TuneInCrew path section
        tuneincrew_group = QGroupBox("TuneInCrew Settings")
        tuneincrew_layout = QVBoxLayout(tuneincrew_group)
        
        tuneincrew_path_layout = QHBoxLayout()
        tuneincrew_label = QLabel("TuneInCrew Path:")
        self.tuneincrew_path_edit = QLineEdit()
        self.tuneincrew_path_edit.textChanged.connect(self.on_tuneincrew_path_changed)
        tuneincrew_browse_btn = QPushButton("Browse")
        tuneincrew_browse_btn.clicked.connect(self.browse_tuneincrew)
        
        # Load saved TuneInCrew path
        saved_path = self.settings.value("tuneincrew_path", "")
        if saved_path and os.path.exists(saved_path):
            self.tuneincrew_path_edit.setText(saved_path)
            self.tuneincrew_path = saved_path
        
        tuneincrew_path_layout.addWidget(tuneincrew_label)
        tuneincrew_path_layout.addWidget(self.tuneincrew_path_edit)
        tuneincrew_path_layout.addWidget(tuneincrew_browse_btn)
        tuneincrew_layout.addLayout(tuneincrew_path_layout)
        
        self.scroll_layout.addWidget(tuneincrew_group)
        
        # FMOD path section
        fmod_group = QGroupBox("FMOD Settings")
        fmod_layout = QVBoxLayout(fmod_group)
        
        fmod_path_layout = QHBoxLayout()
        fmod_label = QLabel("FMOD Designer Path:")
        self.fmod_path_edit = QLineEdit("C:\\Program Files (x86)\\FMOD SoundSystem\\FMOD Designer\\fmod_designercl.exe")
        fmod_browse_btn = QPushButton("Browse")
        fmod_browse_btn.clicked.connect(self.browse_fmod)
        
        fmod_path_layout.addWidget(fmod_label)
        fmod_path_layout.addWidget(self.fmod_path_edit)
        fmod_path_layout.addWidget(fmod_browse_btn)
        fmod_layout.addLayout(fmod_path_layout)
        
        self.scroll_layout.addWidget(fmod_group)
        
        # Radio settings section
        radio_group = QGroupBox("Radio Settings")
        radio_layout = QVBoxLayout(radio_group)
        
        # Radio ID
        id_layout = QHBoxLayout()
        id_label = QLabel("Radio ID (max 4 chars):")
        self.id_edit = QLineEdit("EXMP")
        self.id_edit.textChanged.connect(self.limit_id_length)
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_edit)
        radio_layout.addLayout(id_layout)
        
        # Radio name
        name_layout = QHBoxLayout()
        name_label = QLabel("Radio Name:")
        self.name_edit = QLineEdit("default")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        radio_layout.addLayout(name_layout)
        
        # Radio logo
        logo_layout = QHBoxLayout()
        logo_label = QLabel("Radio Logo (.dds):")
        self.logo_edit = DragDropLineEdit(self)
        self.logo_edit.setPlaceholderText("Drag & drop .dds file or click Browse")
        logo_browse_btn = QPushButton("Browse")
        logo_browse_btn.clicked.connect(self.browse_logo)
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(self.logo_edit)
        logo_layout.addWidget(logo_browse_btn)
        radio_layout.addLayout(logo_layout)
        
        self.scroll_layout.addWidget(radio_group)
        
        # Jingles section
        jingles_group = QGroupBox("Jingles")
        jingles_layout = QVBoxLayout(jingles_group)
        
        self.jingles_widget = QWidget()
        self.jingles_layout = QVBoxLayout(self.jingles_widget)
        jingles_layout.addWidget(self.jingles_widget)
        
        # Add jingle button
        add_jingle_btn = QPushButton("Add Jingle")
        add_jingle_btn.clicked.connect(self.add_jingle)
        jingles_layout.addWidget(add_jingle_btn)
        
        self.scroll_layout.addWidget(jingles_group)
        
        # Songs section
        songs_group = QGroupBox("Songs")
        songs_layout = QVBoxLayout(songs_group)
        
        self.songs_widget = QWidget()
        self.songs_layout = QVBoxLayout(self.songs_widget)
        songs_layout.addWidget(self.songs_widget)
        
        # Add song button
        add_song_btn = QPushButton("Add Song")
        add_song_btn.clicked.connect(self.add_song)
        songs_layout.addWidget(add_song_btn)
        
        self.scroll_layout.addWidget(songs_group)
        
        # Add spacer to push content to top
        self.scroll_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Create dock widget for persistent search at the bottom
        self.create_search_dock()
        
        # Buttons at the bottom
        button_layout = QHBoxLayout()
        
        run_btn = QPushButton("Run TuneInCrew")
        run_btn.clicked.connect(self.run_tuneincrew)
        button_layout.addWidget(run_btn)
        
        load_btn = QPushButton("Load XML")
        load_btn.clicked.connect(self.load_xml)
        button_layout.addWidget(load_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_xml)
        button_layout.addWidget(save_btn)
        
        save_as_btn = QPushButton("Save As")
        save_as_btn.clicked.connect(self.save_as_xml)
        button_layout.addWidget(save_as_btn)
        
        main_layout.addLayout(button_layout)
        
        # Add one empty jingle and song by default
        self.add_jingle()
        self.add_song()
        
    def create_search_dock(self):
        """Create a dock widget for persistent search at the bottom"""
        search_dock = QDockWidget("Search Songs", self)
        search_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        search_dock.setTitleBarWidget(QWidget())  # Hide title bar
        
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter song name or artist...")
        self.search_edit.textChanged.connect(self.search_songs)
        
        search_case_check = QCheckBox("Case sensitive")
        self.case_sensitive = False
        search_case_check.stateChanged.connect(lambda state: setattr(self, 'case_sensitive', state == Qt.Checked))
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_search)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(search_case_check)
        search_layout.addWidget(clear_btn)
        
        search_dock.setWidget(search_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, search_dock)
        
    def clear_search(self):
        """Clear the search box and show all songs"""
        self.search_edit.clear()
        self.search_songs()
        
    def limit_id_length(self):
        text = self.id_edit.text()
        if len(text) > 4:
            self.id_edit.setText(text[:4])
            
    def on_tuneincrew_path_changed(self, text):
        """Handle when TuneInCrew path is changed"""
        if text and os.path.exists(text):
            self.tuneincrew_path = text
            self.settings.setValue("tuneincrew_path", text)
            
    def browse_tuneincrew(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select TuneInCrew.exe", "", "Executable Files (*.exe)"
        )
        if file_path:
            self.tuneincrew_path_edit.setText(file_path)
            self.tuneincrew_path = file_path
            self.settings.setValue("tuneincrew_path", file_path)
            
    def browse_fmod(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select FMOD Designer CLI", 
            "C:\\Program Files (x86)", "Executable Files (*.exe)"
        )
        if file_path:
            self.fmod_path_edit.setText(file_path)
            
    def browse_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Radio Logo", "", "DDS Files (*.dds)"
        )
        if file_path:
            self.logo_edit.setText(file_path)
            
    def add_jingle(self):
        jingle_widget = QWidget()
        jingle_widget.setAcceptDrops(True)
        jingle_layout = QHBoxLayout(jingle_widget)
        
        jingle_file_edit = DragDropLineEdit(self)
        jingle_browse_btn = QPushButton("Browse")
        jingle_browse_btn.clicked.connect(lambda: self.browse_audio_file(jingle_file_edit))
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_jingle(jingle_widget))
        
        jingle_layout.addWidget(QLabel("Jingle File:"))
        jingle_layout.addWidget(jingle_file_edit)
        jingle_layout.addWidget(jingle_browse_btn)
        jingle_layout.addWidget(remove_btn)
        
        self.jingles_layout.addWidget(jingle_widget)
        
    def remove_jingle(self, jingle_widget):
        self.jingles_layout.removeWidget(jingle_widget)
        jingle_widget.deleteLater()
        
    def add_song(self):
        song_widget = SongWidget(self)
        song_widget.remove_btn.clicked.connect(lambda: self.remove_song(song_widget))
        self.songs_layout.addWidget(song_widget)
        self.update_song_data(song_widget)
        
    def update_song_data(self, song_widget):
        """Update the searchable data for a song widget"""
        song_name = song_widget.song_name_edit.text()
        artist = song_widget.song_artist_edit.text()
        song_data = f"{song_name} {artist}".lower()
        song_widget.setProperty("song_data", song_data)
        
    def remove_song(self, song_widget):
        self.songs_layout.removeWidget(song_widget)
        song_widget.deleteLater()
        
    def search_songs(self):
        """Search through songs and highlight matches"""
        search_text = self.search_edit.text()
        if not self.case_sensitive:
            search_text = search_text.lower()
        
        for i in range(self.songs_layout.count()):
            song_widget = self.songs_layout.itemAt(i).widget()
            if song_widget:
                song_data = song_widget.property("song_data") or ""
                if not self.case_sensitive:
                    song_data = song_data.lower()
                
                # Show/hide based on search match
                match_found = search_text in song_data if search_text else True
                song_widget.setVisible(match_found)
        
    def browse_audio_file(self, file_edit):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", 
            "Audio Files (*.mp3 *.wav *.flac)"
        )
        if file_path:
            file_edit.setText(file_path)
            
    def handle_dropped_audio(self, file_path, line_edit):
        """Handle audio files dropped on line edits"""
        line_edit.setText(file_path)
        
    def run_tuneincrew(self):
        # Check if we have a valid TuneInCrew path
        if not self.tuneincrew_path or not os.path.exists(self.tuneincrew_path):
            QMessageBox.warning(self, "Warning", "Please select a valid TuneInCrew.exe first")
            self.browse_tuneincrew()
            return
            
        # First save the XML to a temporary file if not saved yet
        if not self.current_file:
            temp_file = os.path.join(os.getcwd(), "temp_radio.xml")
            self.generate_xml(temp_file)
            xml_path = temp_file
        else:
            xml_path = self.current_file
            
        # Run TuneInCrew with the XML file
        try:
            # Change to the directory where TuneInCrew is located
            tuneincrew_dir = os.path.dirname(self.tuneincrew_path)
            self.process.setWorkingDirectory(tuneincrew_dir)
            
            # Run the process with the XML file as argument
            self.process.start(self.tuneincrew_path, [xml_path])
            
            QMessageBox.information(self, "Info", f"Running TuneInCrew with: {xml_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run TuneInCrew: {str(e)}")
            
    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        print("TuneInCrew output:", stdout)
        
    def handle_stderr(self):
        data = self.process.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        print("TuneInCrew error:", stderr)
        
    def process_finished(self, exit_code, exit_status):
        print(f"TuneInCrew finished with exit code: {exit_code}")
            
    def load_xml(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load XML File", "", "XML Files (*.xml)"
        )
        if file_path:
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                # Clear existing jingles and songs
                self.clear_layout(self.jingles_layout)
                self.clear_layout(self.songs_layout)
                
                # Load FMOD path
                fmod_elem = root.find('fmod')
                if fmod_elem is not None:
                    self.fmod_path_edit.setText(fmod_elem.text)
                
                # Load radio settings
                radio_elem = root.find('radio')
                if radio_elem is not None:
                    id_elem = radio_elem.find('id')
                    if id_elem is not None:
                        self.id_edit.setText(id_elem.text)
                    
                    name_elem = radio_elem.find('name')
                    if name_elem is not None:
                        self.name_edit.setText(name_elem.text)
                    
                    logo_elem = radio_elem.find('logo')
                    if logo_elem is not None:
                        self.logo_edit.setText(logo_elem.text)
                
                # Load jingles
                jingles_elem = radio_elem.find('jingles')
                if jingles_elem is not None:
                    for jingle_elem in jingles_elem.findall('file'):
                        self.add_jingle()
                        last_jingle = self.jingles_layout.itemAt(self.jingles_layout.count() - 1).widget()
                        file_edit = last_jingle.findChild(QLineEdit)
                        file_edit.setText(jingle_elem.text)
                
                # Load songs
                songs_elem = radio_elem.find('songs')
                if songs_elem is not None:
                    for song_elem in songs_elem.findall('song'):
                        self.add_song()
                        last_song = self.songs_layout.itemAt(self.songs_layout.count() - 1).widget()
                        
                        file_elem = song_elem.find('file')
                        if file_elem is not None:
                            last_song.song_file_edit.setText(file_elem.text)
                        
                        name_elem = song_elem.find('name')
                        if name_elem is not None:
                            last_song.song_name_edit.setText(name_elem.text)
                        
                        artist_elem = song_elem.find('artist')
                        if artist_elem is not None:
                            last_song.song_artist_edit.setText(artist_elem.text)
                        
                        year_elem = song_elem.find('year')
                        if year_elem is not None:
                            last_song.song_year_edit.setText(year_elem.text)
                        
                        length_elem = song_elem.find('length')
                        if length_elem is not None:
                            last_song.song_length_edit.setText(length_elem.text)
                        
                        force_elem = song_elem.find('force')
                        if force_elem is not None:
                            last_song.song_force_edit.setText(force_elem.text)
                
                self.current_file = file_path
                self.setWindowTitle(f'TuneInCrew Radio XML Generator - {file_path}')
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load XML: {str(e)}")
                
    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def save_xml(self):
        if self.current_file:
            self.generate_xml(self.current_file)
        else:
            self.save_as_xml()
            
    def save_as_xml(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save XML File", "", "XML Files (*.xml)"
        )
        if file_path:
            self.generate_xml(file_path)
            self.current_file = file_path
            self.setWindowTitle(f'TuneInCrew Radio XML Generator - {file_path}')
            
    def generate_xml(self, file_path):
        try:
            # Create root element
            root = ET.Element("project")
            
            # Add FMOD path
            fmod_elem = ET.SubElement(root, "fmod")
            fmod_elem.text = self.escape_xml_text(self.fmod_path_edit.text())
            
            # Add radio element
            radio_elem = ET.SubElement(root, "radio")
            
            # Add radio ID
            id_elem = ET.SubElement(radio_elem, "id")
            id_elem.text = self.escape_xml_text(self.id_edit.text())
            
            # Add radio name
            name_elem = ET.SubElement(radio_elem, "name")
            name_elem.text = self.escape_xml_text(self.name_edit.text())
            
            # Add radio logo
            logo_elem = ET.SubElement(radio_elem, "logo")
            logo_elem.text = self.escape_xml_text(self.logo_edit.text())
            
            # Add jingles if any
            jingles_added = False
            for i in range(self.jingles_layout.count()):
                jingle_widget = self.jingles_layout.itemAt(i).widget()
                file_edit = jingle_widget.findChild(QLineEdit)
                if file_edit and file_edit.text():
                    if not jingles_added:
                        jingles_elem = ET.SubElement(radio_elem, "jingles")
                        jingles_added = True
                    file_elem = ET.SubElement(jingles_elem, "file")
                    file_elem.text = self.escape_xml_text(file_edit.text())
            
            # Add songs
            songs_elem = ET.SubElement(radio_elem, "songs")
            for i in range(self.songs_layout.count()):
                song_widget = self.songs_layout.itemAt(i).widget()
                if song_widget.isVisible():  # Only include visible songs (not filtered out by search)
                    if song_widget.song_file_edit.text():  # Check if file path is set
                        song_elem = ET.SubElement(songs_elem, "song")
                        
                        file_elem = ET.SubElement(song_elem, "file")
                        file_elem.text = self.escape_xml_text(song_widget.song_file_edit.text())
                        
                        name_elem = ET.SubElement(song_elem, "name")
                        name_elem.text = self.escape_xml_text(song_widget.song_name_edit.text())
                        
                        artist_elem = ET.SubElement(song_elem, "artist")
                        artist_elem.text = self.escape_xml_text(song_widget.song_artist_edit.text())
                        
                        year_elem = ET.SubElement(song_elem, "year")
                        year_elem.text = self.escape_xml_text(song_widget.song_year_edit.text())
                        
                        length_elem = ET.SubElement(song_elem, "length")
                        length_elem.text = self.escape_xml_text(song_widget.song_length_edit.text())
                        
                        force_elem = ET.SubElement(song_elem, "force")
                        force_elem.text = self.escape_xml_text(song_widget.song_force_edit.text())
            
            # Create XML tree and write to file with formatting
            tree = ET.ElementTree(root)
            
            # Add XML declaration with pretty formatting
            with open(file_path, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                self.pretty_write(f, root, 0)
            
            QMessageBox.information(self, "Success", "XML file saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save XML: {str(e)}")
    
    def escape_xml_text(self, text):
        """Escape special XML characters"""
        if not text:
            return text
            
        # Replace special characters with their XML entities
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")
        
        return text
    
    def pretty_write(self, file, elem, level=0):
        """Recursively write XML with proper indentation"""
        indent = "  " * level
        if len(elem) == 0:  # No children
            if elem.text and elem.text.strip():
                file.write(f"{indent}<{elem.tag}>{elem.text}</{elem.tag}>\n".encode('utf-8'))
            else:
                file.write(f"{indent}<{elem.tag}></{elem.tag}>\n".encode('utf-8'))
        else:
            file.write(f"{indent}<{elem.tag}>\n".encode('utf-8'))
            if elem.text and elem.text.strip():
                file.write(f"{indent}  {elem.text}\n".encode('utf-8'))
            
            for child in elem:
                self.pretty_write(file, child, level + 1)
                
            file.write(f"{indent}</{elem.tag}>\n".encode('utf-8'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = XMLGenerator()
    window.show()
    sys.exit(app.exec_())