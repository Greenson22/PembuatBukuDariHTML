import os
import json
import zipfile
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QFileDialog, 
                             QLabel, QLineEdit, QMessageBox, QCheckBox, QProgressBar,
                             QScrollArea, QFrame, QApplication, QSizePolicy, QTextEdit, 
                             QRadioButton, QDialog)
                             
from styles import get_modern_theme
from pdf_worker import PDFWorker
from html_merger import generate_combined_html
from settings_dialog import SettingsDialog

class HTMLMergerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTML & PDF Merger - Penggabung File")
        self.setMinimumSize(1000, 750) 
        
        self.custom_titles = {}
        self.file_bab_mapping = {}  
        self.base_dir = "" 
        
        self.settings = SettingsDialog(self)
        self.setStyleSheet(get_modern_theme())
        self.init_ui()

    def init_ui(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.main_container = QWidget()
        self.main_container.setObjectName("mainContainer")
        
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.scroll_area.setWidget(self.main_container)
        self.setCentralWidget(self.scroll_area)

        # ================= CONTENT AREA =================
        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(25, 25, 25, 25)
        self.content_layout.setSpacing(20)

        self.left_layout = QVBoxLayout()
        self.left_layout.setSpacing(15)
        self.right_layout = QVBoxLayout()
        self.right_layout.setSpacing(15)
        
        self.content_layout.addLayout(self.left_layout, stretch=5) 
        self.content_layout.addLayout(self.right_layout, stretch=5) 
        
        self.main_layout.addWidget(self.content_widget)

        # ================= BAGIAN KIRI =================
        self.card_exec = QFrame()
        self.card_exec.setProperty("class", "Card")
        l_exec = QVBoxLayout(self.card_exec)
        l_exec.setContentsMargins(20, 20, 20, 20)
        l_exec.setSpacing(15)
        
        lbl_exec = QLabel("Proses Eksekusi & Nama Output")
        lbl_exec.setProperty("class", "CardTitle")
        l_exec.addWidget(lbl_exec)
        
        self.output_name = QLineEdit("Nama Input Output")
        self.output_name.setPlaceholderText("Masukkan nama output...")
        l_exec.addWidget(self.output_name)
        
        hbox_btns = QHBoxLayout()
        self.btn_generate_html = QPushButton("Gabung HTML")
        self.btn_generate_html.setObjectName("btnBlue")
        self.btn_generate_pdf = QPushButton("Gabung PDF")
        self.btn_generate_pdf.setObjectName("btnGreen")
        hbox_btns.addWidget(self.btn_generate_html)
        hbox_btns.addWidget(self.btn_generate_pdf)
        l_exec.addLayout(hbox_btns)
        
        self.btn_settings = QPushButton("⚙ Pengaturan Dokumen")
        self.btn_settings.setObjectName("btnPurple")
        l_exec.addWidget(self.btn_settings)

        self.btn_create_zip = QPushButton("📦 Buat Arsip ZIP (Kecuali PDF)")
        self.btn_create_zip.setObjectName("btnDarkGray")
        l_exec.addWidget(self.btn_create_zip)

        self.btn_import_zip = QPushButton("🗂️ Import ZIP & Auto PDF")
        self.btn_import_zip.setObjectName("btnBlue")
        l_exec.addWidget(self.btn_import_zip)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.hide()
        l_exec.addWidget(self.progress_bar)
        
        self.left_layout.addWidget(self.card_exec)

        self.card_json = QFrame()
        self.card_json.setProperty("class", "Card")
        l_json = QVBoxLayout(self.card_json)
        l_json.setContentsMargins(20, 20, 20, 20)
        l_json.setSpacing(15)
        
        hbox_json_title = QHBoxLayout()
        lbl_json = QLabel("Judul Kustom & Struktur BAB")
        lbl_json.setProperty("class", "CardTitle")
        self.cb_group_bab = QCheckBox()
        self.cb_group_bab.setChecked(True)
        hbox_json_title.addWidget(lbl_json)
        hbox_json_title.addStretch()
        hbox_json_title.addWidget(self.cb_group_bab)
        l_json.addLayout(hbox_json_title)
        
        desc_json = QLabel("Judul kustom & struktur HTML & BAB")
        desc_json.setStyleSheet("color: #555;")
        l_json.addWidget(desc_json)
        
        self.btn_export_json = QPushButton("1. Ekspor Template JSON")
        self.btn_export_json.setObjectName("btnDarkGray")
        self.btn_load_json = QPushButton("2. Muat Judul JSON")
        self.btn_load_json.setObjectName("btnDarkGray")
        self.btn_ai_json = QPushButton("3. Buat JSON via AI Chat (Copy/Paste)")
        self.btn_ai_json.setObjectName("btnBlue")
        
        l_json.addWidget(self.btn_export_json)
        l_json.addWidget(self.btn_load_json)
        l_json.addWidget(self.btn_ai_json)
        
        self.left_layout.addWidget(self.card_json)
        
        self.card_status = QFrame()
        self.card_status.setProperty("class", "Card")
        l_status = QVBoxLayout(self.card_status)
        l_status.setContentsMargins(20, 15, 20, 15)
        self.lbl_json_status = QLabel("Status: Default (Nama File)")
        self.lbl_json_status.setProperty("class", "StatusLabel")
        l_status.addWidget(self.lbl_json_status)
        self.left_layout.addWidget(self.card_status)
        self.left_layout.addStretch()

        # ================= BAGIAN KANAN =================
        self.card_file = QFrame()
        self.card_file.setProperty("class", "Card")
        l_file = QVBoxLayout(self.card_file)
        l_file.setContentsMargins(20, 20, 20, 20)
        l_file.setSpacing(15)
        
        lbl_file = QLabel("Manajemen File Materi")
        lbl_file.setProperty("class", "CardTitle")
        l_file.addWidget(lbl_file)
        
        self.btn_add_folder = QPushButton("Pilih Folder\nDrag dan drop atau Pilih Folder")
        self.btn_add_folder.setProperty("class", "DashedBox")
        
        self.btn_add_files = QPushButton("Pilih File HTML\nDrag dan drop atau Pilih File HTML")
        self.btn_add_files.setProperty("class", "DashedBox")
        
        l_file.addWidget(self.btn_add_folder)
        l_file.addWidget(self.btn_add_files)

        hbox_list_html = QHBoxLayout()
        self.btn_create_list = QPushButton("📝 Buat list.txt")
        self.btn_create_list.setObjectName("btnDarkGray")
        self.btn_auto_html = QPushButton("📄 Generate HTML Kosong")
        self.btn_auto_html.setObjectName("btnBlue")
        
        hbox_list_html.addWidget(self.btn_create_list)
        hbox_list_html.addWidget(self.btn_auto_html)
        l_file.addLayout(hbox_list_html)
        
        hbox_file_actions = QHBoxLayout()
        self.btn_delete = QPushButton("Hapus Terpilih")
        self.btn_delete.setObjectName("btnRed")
        self.btn_clear = QPushButton("Bersihkan Semua")
        self.btn_clear.setObjectName("btnGray")
        hbox_file_actions.addWidget(self.btn_delete)
        hbox_file_actions.addWidget(self.btn_clear)
        l_file.addLayout(hbox_file_actions)

        self.btn_delete_others = QPushButton("🗑️ Hapus Semua Kecuali PDF & ZIP")
        self.btn_delete_others.setObjectName("btnRed")
        l_file.addWidget(self.btn_delete_others)
        
        self.right_layout.addWidget(self.card_file)
        
        self.card_list = QFrame()
        self.card_list.setProperty("class", "Card")
        l_list = QVBoxLayout(self.card_list)
        l_list.setContentsMargins(20, 20, 20, 20)
        
        lbl_list = QLabel("Urutan file materi yang akan digabung")
        lbl_list.setProperty("class", "CardTitle")
        l_list.addWidget(lbl_list)
        
        self.lbl_base_path = QLabel("Path Utama: Belum ada folder dipilih")
        self.lbl_base_path.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-bottom: 5px;")
        l_list.addWidget(self.lbl_base_path)
        
        self.file_list = QListWidget()
        self.file_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.file_list.setMinimumHeight(350)
        self.file_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        l_list.addWidget(self.file_list)
        
        self.right_layout.addWidget(self.card_list)

        # Hubungkan semua sinyal (Connectors)
        self.btn_generate_html.clicked.connect(self.merge_to_html)
        self.btn_generate_pdf.clicked.connect(self.merge_to_pdf)
        self.btn_settings.clicked.connect(self.settings.exec) 
        self.btn_create_zip.clicked.connect(self.create_zip_archive) 
        self.btn_import_zip.clicked.connect(self.import_zip_and_execute)
        
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_add_files.clicked.connect(self.add_files)
        self.btn_create_list.clicked.connect(self.create_list_txt) 
        self.btn_auto_html.clicked.connect(self.generate_html_files) 
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_delete_others.clicked.connect(self.delete_other_files) 
        
        self.btn_export_json.clicked.connect(self.export_json_template)
        self.btn_load_json.clicked.connect(self.load_json_titles)
        self.btn_ai_json.clicked.connect(self.show_ai_prompt_dialog)

        self.load_app_state_from_config()
        self.cb_group_bab.toggled.connect(self.save_app_state_to_config)

    def import_zip_and_execute(self):
        zip_path, _ = QFileDialog.getOpenFileName(self, "Pilih File ZIP Materi", "", "ZIP Files (*.zip)")
        if not zip_path:
            return

        extract_dir = os.path.join(os.path.dirname(zip_path), os.path.basename(zip_path).replace('.zip', '_extracted'))
        
        self.set_ui_enabled(False)
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("Mengekstrak ZIP...")
        QApplication.processEvents()

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except Exception as e:
            self.progress_bar.hide()
            self.set_ui_enabled(True)
            QMessageBox.critical(self, "Error", f"Gagal mengekstrak ZIP:\n{e}")
            return
            
        self.progress_bar.hide()
        self.set_ui_enabled(True)

        self.clear_all()
        self.base_dir = extract_dir
        self.lbl_base_path.setText(f"Path Utama: {self.base_dir}")
        
        files_in_dir = os.listdir(extract_dir)
        files_lower = [f.lower() for f in files_in_dir]
        
        # 1. Pengecekan Cover
        cover_found = False
        for f in files_in_dir:
            f_lower = f.lower()
            file_path = os.path.join(extract_dir, f)
            if f_lower == 'cover.html':
                self.settings.radio_html_cover.setChecked(True)
                self.settings.cover_file_path = file_path
                self.settings.lbl_cover_status.setText(f"<b><font color='#27ae60'>✓ File: {f}</font></b>")
                cover_found = True
                break
            elif f_lower.startswith('cover.') and f_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.pdf')):
                self.settings.radio_image_cover.setChecked(True)
                self.settings.cover_image_path = file_path
                self.settings.lbl_image_status.setText(f"<b><font color='#27ae60'>✓ File: {f}</font></b>")
                cover_found = True
                break

        if not cover_found:
            self.settings.radio_no_cover.setChecked(True)

        # 2. Pengecekan JSON
        json_found = False
        json_file = None
        for f in files_in_dir:
            if f.lower() in ["meta.json", "template_judul.json", "template_ai.json"]:
                json_file = os.path.join(extract_dir, f)
                json_found = True
                break
                
        if json_file:
            self._process_json_file(json_file, show_message=False)

        # 3. Pengecekan List & HTML
        list_found = 'list.txt' in files_lower
        
        html_files = []
        for f in files_in_dir:
            f_lower = f.lower()
            if f_lower.endswith('.html') and not f_lower.startswith('cover'):
                html_files.append(f)
                
        html_files.sort()
        
        missing = []
        if not cover_found: missing.append("- Cover (cover.html atau cover bergambar)")
        if not json_found: missing.append("- File Struktur JSON")
        if not list_found: missing.append("- File list.txt")
        if not html_files: missing.append("- File HTML Materi (Kosong)")
        
        self.file_list.addItems(html_files)
        self.output_name.setText(os.path.basename(zip_path).replace('.zip', ''))
        
        if missing:
            msg = "Pengecekan Komponen: Terdapat komponen yang kurang dari file ZIP:\n\n" + "\n".join(missing)
            msg += "\n\nApakah Anda tetap ingin memprosesnya menjadi PDF?"
            reply = QMessageBox.question(self, "Peringatan Kelengkapan", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes and html_files:
                self.merge_to_pdf()
        else:
            QMessageBox.information(self, "Komponen Lengkap", "Pengecekan Berhasil!\n\nSemua komponen (Cover, JSON, List, dan HTML) lengkap. Proses pembuatan PDF akan langsung dijalankan secara otomatis.")
            self.merge_to_pdf()

    def delete_other_files(self):
        if not self.base_dir:
            QMessageBox.warning(self, "Peringatan", "Pilih folder utama (Folder Induk) terlebih dahulu!")
            return

        reply = QMessageBox.question(
            self,
            "Konfirmasi Penghapusan",
            "Apakah Anda yakin ingin menghapus SEMUA file di dalam folder utama KECUALI file .pdf dan .zip?\n\nTindakan ini bersifat permanen dan tidak dapat dibatalkan!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = 0
            try:
                for filename in os.listdir(self.base_dir):
                    file_path = os.path.join(self.base_dir, filename)
                    if os.path.isfile(file_path):
                        ext = filename.lower()
                        if not (ext.endswith('.pdf') or ext.endswith('.zip')):
                            os.remove(file_path)
                            deleted_count += 1
                
                temp_dir = self.base_dir
                self.file_list.clear() 
                self.lbl_base_path.setText(f"Path Utama: {temp_dir}")
                
                QMessageBox.information(self, "Selesai", f"Berhasil menghapus {deleted_count} file (selain .pdf dan .zip).")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Terjadi kesalahan saat menghapus:\n{e}")

    def load_app_state_from_config(self):
        try:
            if os.path.exists(self.settings.config_file):
                with open(self.settings.config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    if "cb_group_bab" in cfg:
                        self.cb_group_bab.setChecked(cfg["cb_group_bab"])
                    if "custom_titles" in cfg:
                        self.custom_titles = cfg["custom_titles"]
                    if "file_bab_mapping" in cfg:
                        self.file_bab_mapping = cfg["file_bab_mapping"]
                    
                    if self.custom_titles or self.file_bab_mapping:
                        self.lbl_json_status.setText("<b><font color='#2980b9'>✓ Aktif: Dimuat dari Config</font></b>")
        except Exception as e:
            print(f"Gagal memuat state app dari config: {e}")

    def save_app_state_to_config(self, *args):
        try:
            cfg = {}
            if os.path.exists(self.settings.config_file):
                with open(self.settings.config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
            
            cfg["cb_group_bab"] = self.cb_group_bab.isChecked()
            cfg["custom_titles"] = self.custom_titles
            cfg["file_bab_mapping"] = self.file_bab_mapping
            
            with open(self.settings.config_file, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=4)
        except Exception as e:
            print(f"Gagal menyimpan state app ke config: {e}")

    def create_list_txt(self):
        if not self.base_dir:
            folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Utama Terlebih Dahulu")
            if folder:
                self.base_dir = folder
                self.lbl_base_path.setText(f"Path Utama: {self.base_dir}")
            else:
                return

        dialog = QDialog(self)
        dialog.setWindowTitle("Input Daftar Materi (list.txt)")
        dialog.setMinimumSize(500, 400)
        layout = QVBoxLayout(dialog)

        lbl = QLabel("Masukkan daftar materi (satu baris untuk satu file materi):")
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Contoh:\nPengenalan Sistem\nArsitektur Dasar\nKesimpulan")
        
        list_path = os.path.join(self.base_dir, "list.txt")
        if os.path.exists(list_path):
            try:
                with open(list_path, 'r', encoding='utf-8') as f:
                    text_edit.setPlainText(f.read())
            except Exception as e:
                print(f"Gagal membaca list.txt yang sudah ada: {e}")

        btn_save = QPushButton("Simpan list.txt")
        btn_save.setObjectName("btnBlue")

        layout.addWidget(lbl)
        layout.addWidget(text_edit)
        layout.addWidget(btn_save)

        def on_save():
            content = text_edit.toPlainText().strip()
            if not content:
                QMessageBox.warning(dialog, "Peringatan", "List tidak boleh kosong!")
                return
            try:
                with open(list_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                QMessageBox.information(dialog, "Berhasil", "list.txt berhasil disimpan di folder utama!")
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Gagal menyimpan list.txt: {e}")

        btn_save.clicked.connect(on_save)
        dialog.exec()

    def generate_html_files(self):
        if not self.base_dir:
            QMessageBox.warning(self, "Peringatan", "Silakan pilih folder utama atau buat list.txt terlebih dahulu!")
            return
            
        list_path = os.path.join(self.base_dir, "list.txt")
        if not os.path.exists(list_path):
            QMessageBox.warning(self, "Peringatan", "File list.txt tidak ditemukan di folder utama.\nSilakan gunakan tombol 'Buat list.txt' terlebih dahulu.")
            return

        try:
            with open(list_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal membaca list.txt: {e}")
            return

        if not lines:
            QMessageBox.warning(self, "Peringatan", "File list.txt kosong!")
            return

        total_files = len(lines)
        tanya = QMessageBox.question(
            self, 
            "Konfirmasi Pembuatan", 
            f"Apakah Anda yakin ingin membuat {total_files} file HTML kosong secara otomatis di folder materi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if tanya == QMessageBox.StandardButton.No:
            return

        folder_name = os.path.basename(os.path.normpath(self.base_dir))
        self.file_list.clear()

        generated_files = []
        
        for i, title in enumerate(lines):
            if i == total_files - 1:
                filename = f"{folder_name}.k.html"
            else:
                filename = f"{folder_name}.{i}.html"
                
            filepath = os.path.join(self.base_dir, filename)
            
            html_content = f""
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                generated_files.append(filename)
            except Exception as e:
                print(f"Gagal menulis file {filename}: {e}")

        self.file_list.addItems(generated_files)
        QMessageBox.information(self, "Berhasil", f"{len(generated_files)} file HTML telah berhasil dibuat berdasarkan isi list.txt!")

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder")
        if folder:
            if not self.base_dir:
                self.base_dir = folder
            
            self.lbl_base_path.setText(f"Path Utama: {self.base_dir}")
                
            all_files = os.listdir(folder)
            html_files = []
            for f in all_files:
                f_lower = f.lower()
                file_path = os.path.join(folder, f)
                
                if f_lower in ["meta.json", "template_judul.json", "template_ai.json"]: 
                    self._process_json_file(file_path, show_message=False)
                elif f_lower == "cover.html":
                    self.settings.radio_html_cover.setChecked(True)
                    self.settings.cover_file_path = file_path
                    self.settings.lbl_cover_status.setText(f"<b><font color='#27ae60'>✓ File: {f}</font></b>")
                elif f_lower.startswith("cover.") and f_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.pdf')):
                    self.settings.radio_image_cover.setChecked(True)
                    self.settings.cover_image_path = file_path
                    self.settings.lbl_image_status.setText(f"<b><font color='#27ae60'>✓ File: {f}</font></b>")
                elif f_lower.endswith('.html') and f_lower != "cover.html":
                    html_files.append(file_path)

            html_files.sort()
            file_names_only = [os.path.basename(f) for f in html_files]
            self.file_list.addItems(file_names_only)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Pilih File HTML", "", "HTML Files (*.html)")
        if files: 
            if not self.base_dir:
                self.base_dir = os.path.dirname(files[0])
            file_names_only = [os.path.basename(f) for f in files]
            self.file_list.addItems(file_names_only)

    def delete_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def clear_all(self):
        self.file_list.clear()
        self.custom_titles.clear()
        self.file_bab_mapping.clear()
        self.save_app_state_to_config()
        
        self.lbl_json_status.setText("Status: Default (Nama File)")
        self.settings.lbl_cover_status.setText("Belum ada file dipilih")
        self.settings.lbl_image_status.setText("Belum ada file dipilih")
        self.settings.cover_file_path = None
        self.settings.cover_image_path = None
        self.base_dir = ""
        self.settings.radio_no_cover.setChecked(True)

        self.lbl_base_path.setText("Path Utama: Belum ada folder dipilih")

    def export_json_template(self):
        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "Peringatan", "Tambahkan file HTML terlebih dahulu!")
            return

        judul_utama = "Masukkan Judul Dokumen Utama Di Sini"
        if self.base_dir:
            judul_utama = os.path.basename(os.path.normpath(self.base_dir))

        template_data = {"judul_utama": judul_utama, "struktur": {}}
        if self.cb_group_bab.isChecked():
            bab_dict = {os.path.basename(self.file_list.item(i).text()): os.path.basename(self.file_list.item(i).text()).replace('.html', '').title() for i in range(count)}
            template_data["struktur"]["BAB 1: Pendahuluan"] = bab_dict
        else:
            for i in range(count):
                f_name = os.path.basename(self.file_list.item(i).text())
                template_data["struktur"][f_name] = f_name.replace('.html', '').title()

        default_path = os.path.join(self.base_dir, "template_judul.json") if self.base_dir else "template_judul.json"
        
        if self.settings.cb_auto_export.isChecked() and self.base_dir:
            save_path = default_path
        else:
            save_path, _ = QFileDialog.getSaveFileName(self, "Simpan Template JSON", default_path, "JSON Files (*.json)")
        
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Berhasil", f"Template JSON berhasil disimpan di:\n{save_path}")

    def load_json_titles(self):
        start_dir = self.base_dir if self.base_dir else ""
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih File JSON", start_dir, "JSON Files (*.json)")
        if file_path: self._process_json_file(file_path, show_message=True)

    def show_ai_prompt_dialog(self):
        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "Peringatan", "Tambahkan file HTML materi terlebih dahulu ke daftar sebelum membuat struktur JSON!")
            return

        file_names = [os.path.basename(self.file_list.item(i).text()) for i in range(count)]

        dialog_input = QDialog(self)
        dialog_input.setWindowTitle("Langkah 1: Input Poin Materi")
        dialog_input.setMinimumSize(550, 450)
        layout_in = QVBoxLayout(dialog_input)

        list_txt_path = os.path.join(self.base_dir, "list.txt") if self.base_dir else ""
        has_list_txt = os.path.exists(list_txt_path) if list_txt_path else False

        radio_manual = None
        radio_list = None
        
        if has_list_txt:
            radio_layout = QHBoxLayout()
            radio_layout.addWidget(QLabel("<b>Sumber Poin Materi:</b>"))
            radio_manual = QRadioButton("Input Manual")
            radio_list = QRadioButton("Gunakan file list.txt")
            radio_list.setChecked(True)
            
            radio_layout.addWidget(radio_list)
            radio_layout.addWidget(radio_manual)
            radio_layout.addStretch()
            layout_in.addLayout(radio_layout)

        if self.cb_group_bab.isChecked():
            lbl_text = "Masukkan daftar poin-poin/BAB materi (pisahkan dengan baris baru):"
            placeholder_text = "Contoh:\nPengenalan Sistem\nArsitektur Dasar\nKesimpulan"
        else:
            lbl_text = "Masukkan daftar judul kustom untuk setiap materi (pisahkan dengan baris baru):"
            placeholder_text = f"Masukkan judul kustom untuk {count} file secara berurutan..."

        lbl_in = QLabel(lbl_text)
        text_in = QTextEdit()
        text_in.setPlaceholderText(placeholder_text)
        
        if has_list_txt:
            def toggle_input_mode():
                if radio_list.isChecked():
                    try:
                        with open(list_txt_path, 'r', encoding='utf-8') as f:
                            text_in.setPlainText(f.read().strip())
                    except Exception as e:
                        text_in.setPlainText(f"Gagal membaca list.txt: {e}")
                else:
                    text_in.clear()
            
            radio_list.toggled.connect(toggle_input_mode)
            radio_manual.toggled.connect(toggle_input_mode)
            toggle_input_mode()

        btn_copy = QPushButton("Buat Prompt & Salin ke Clipboard")
        btn_copy.setObjectName("btnBlue")

        layout_in.addWidget(lbl_in)
        layout_in.addWidget(text_in)
        layout_in.addWidget(btn_copy)

        def on_copy():
            user_list = text_in.toPlainText().strip()
            if not user_list:
                QMessageBox.warning(dialog_input, "Peringatan", "Daftar input materi tidak boleh kosong!")
                return

            judul_utama_ai = "Judul Dokumen Anda"
            if self.base_dir:
                judul_utama_ai = os.path.basename(os.path.normpath(self.base_dir))

            if self.cb_group_bab.isChecked():
                instruksi_struktur = (
                    "Tolong buatkan struktur JSON untuk mengelompokkan file-file HTML tersebut ke dalam BAB "
                    "berdasarkan poin-poin materi di atas. Gunakan format template JSON berikut:\n\n"
                    "{\n"
                    f'  "judul_utama": "{judul_utama_ai}",\n'
                    '  "struktur": {\n'
                    '    "BAB 1: [Nama Poin Materi]": {\n'
                    '      "nama_file1.html": "Judul Sub-materi 1",\n'
                    '      "nama_file2.html": "Judul Sub-materi 2"\n'
                    "    }\n"
                    "  }\n"
                    "}\n\n"
                    "Catatan penting untuk penamaan sub-materi:\n"
                    "- File dengan akhiran '.0.html' adalah Pengantar dari materi tersebut.\n"
                    "- File dengan akhiran '.k.html' adalah Kesimpulan dari materi tersebut."
                )
            else:
                instruksi_struktur = (
                    "Tolong buatkan struktur JSON datar (tanpa pengelompokan BAB) yang mencocokkan setiap file HTML "
                    "secara berurutan dengan judul kustom yang lebih rapi berdasarkan daftar poin di atas. "
                    "Gunakan format template JSON berikut:\n\n"
                    "{\n"
                    f'  "judul_utama": "{judul_utama_ai}",\n'
                    '  "struktur": {\n'
                    '    "nama_file1.html": "Judul Kustom Materi 1",\n'
                    '    "nama_file2.html": "Judul Kustom Materi 2"\n'
                    "  }\n"
                    "}\n\n"
                    "Catatan penting untuk penamaan judul kustom:\n"
                    "- File dengan akhiran '.0.html' adalah 'Pengantar''.\n"
                    "- File dengan akhiran '.k.html' adalah 'Kesimpulan'."
                )

            prompt = (
                "Saya sedang menyusun dokumen. Berikut adalah daftar file HTML yang saya miliki:\n"
                f"{', '.join(file_names)}\n\n"
                "Berikut adalah daftar poin-poin/judul materi yang saya inginkan:\n"
                f"{user_list}\n\n"
                f"{instruksi_struktur}\n\n"
                "Pastikan SEMUA file HTML yang saya berikan dimasukkan ke dalam susunan JSON tersebut. "
                "Berikan output HANYA berupa JSON yang valid, tanpa tambahan teks penjelasan, dan tanpa blok kode (```)."
            )

            QApplication.clipboard().setText(prompt)
            QMessageBox.information(
                dialog_input, 
                "Berhasil", 
                "Prompt berhasil disalin ke Clipboard!\n\n1. Buka AI Chat (ChatGPT/Claude/Gemini).\n2. Paste prompt tersebut.\n3. Copy hasil JSON yang diberikan AI.\n\nTutup dialog ini untuk lanjut ke langkah paste."
            )
            dialog_input.accept()
            self.show_ai_paste_dialog()

        btn_copy.clicked.connect(on_copy)
        dialog_input.exec()

    def show_ai_paste_dialog(self):
        dialog_out = QDialog(self)
        dialog_out.setWindowTitle("Langkah 2: Paste Hasil AI")
        dialog_out.setMinimumSize(500, 400)
        layout_out = QVBoxLayout(dialog_out)

        lbl_out = QLabel("Paste teks JSON dari hasil AI Chat ke sini:")
        text_out = QTextEdit()
        text_out.setPlaceholderText("Paste output format JSON di sini...\nPastikan berawal dari '{' dan diakhiri '}'")
        
        btn_save = QPushButton("Simpan & Muat File JSON")
        btn_save.setObjectName("btnGreen")

        layout_out.addWidget(lbl_out)
        layout_out.addWidget(text_out)
        layout_out.addWidget(btn_save)

        def on_save():
            ai_result = text_out.toPlainText().strip()
            
            if ai_result.startswith("```json"):
                ai_result = ai_result[7:]
            elif ai_result.startswith("```"):
                ai_result = ai_result[3:]
            if ai_result.endswith("```"):
                ai_result = ai_result[:-3]
            
            ai_result = ai_result.strip()

            if not ai_result:
                QMessageBox.warning(dialog_out, "Peringatan", "Input teks hasil tidak boleh kosong!")
                return

            try:
                parsed_json = json.loads(ai_result)

                default_path = os.path.join(self.base_dir, "template_ai.json") if self.base_dir else "template_ai.json"
                save_path, _ = QFileDialog.getSaveFileName(self, "Simpan Template JSON Baru", default_path, "JSON Files (*.json)")

                if save_path:
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed_json, f, indent=4, ensure_ascii=False)

                    self._process_json_file(save_path, show_message=True)
                    dialog_out.accept()

            except json.JSONDecodeError as e:
                QMessageBox.critical(dialog_out, "Error Validasi JSON", f"Teks tidak valid sebagai JSON!\n\nPesan Error: {e}\n\nPastikan Anda hanya menyalin kode JSON secara utuh.")

        btn_save.clicked.connect(on_save)
        dialog_out.exec()

    def _process_json_file(self, file_path, show_message=False):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.custom_titles.clear()
            self.file_bab_mapping.clear()

            if "judul_utama" in data:
                judul = data.pop("judul_utama")
                self.settings.input_cover_title.setText(judul)
                self.output_name.setText(judul) 
                if self.settings.radio_no_cover.isChecked(): self.settings.radio_text_cover.setChecked(True)
                
            data = data.get("struktur", data)
            is_nested = data and isinstance(next(iter(data.values())), dict)

            if is_nested:
                for bab_name, files_dict in data.items():
                    for file_name, file_title in files_dict.items():
                        self.custom_titles[file_name] = file_title
                        self.file_bab_mapping[file_name] = bab_name
            else:
                self.custom_titles = data

            self.lbl_json_status.setText(f"<b><font color='#2980b9'>✓ Aktif: {os.path.basename(file_path)}</font></b>")
            
            self.save_app_state_to_config()
            
            if show_message: QMessageBox.information(self, "Berhasil", "Data judul berhasil dimuat!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def set_ui_enabled(self, enabled):
        self.btn_generate_html.setEnabled(enabled)
        self.btn_generate_pdf.setEnabled(enabled)
        self.btn_create_zip.setEnabled(enabled) 
        self.btn_import_zip.setEnabled(enabled)
        self.btn_settings.setEnabled(enabled)
        self.btn_add_folder.setEnabled(enabled)
        self.btn_add_files.setEnabled(enabled)
        self.btn_create_list.setEnabled(enabled)
        self.btn_auto_html.setEnabled(enabled)
        self.btn_delete.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)
        self.btn_delete_others.setEnabled(enabled) 
        self.btn_ai_json.setEnabled(enabled) 

    def _get_export_options(self, is_pdf):
        cover_type = "none"
        cover_bg_css = "#ffffff" 
        
        if self.settings.radio_html_cover.isChecked(): 
            cover_type = "html"
        elif self.settings.radio_image_cover.isChecked(): 
            cover_type = "image"
            if self.settings.cover_image_path:
                try:
                    from PIL import Image
                    with Image.open(self.settings.cover_image_path) as img:
                        img = img.convert("RGB")
                        w, h = img.size
                        
                        c_0 = img.getpixel((0, 0))                       
                        c_25 = img.getpixel((0, int(h * 0.25)))          
                        c_50 = img.getpixel((0, int(h * 0.50)))          
                        c_75 = img.getpixel((0, int(h * 0.75)))          
                        c_100 = img.getpixel((0, h - 1))                 
                        
                        def to_hex(rgb):
                            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                            
                        cover_bg_css = f"linear-gradient(to bottom, {to_hex(c_0)} 0%, {to_hex(c_25)} 25%, {to_hex(c_50)} 50%, {to_hex(c_75)} 75%, {to_hex(c_100)} 100%)"
                        
                except Exception as e:
                    print(f"Gagal mengekstrak warna gradasi dari gambar cover: {e}")
                    
        elif self.settings.radio_text_cover.isChecked(): 
            cover_type = "text"

        return {
            "doc_title": self.settings.input_cover_title.text().strip() or "Gabungan Materi",
            "is_pdf": is_pdf,
            "use_toc": self.settings.cb_toc.isChecked(),
            "use_page_numbers": self.settings.cb_page_numbers.isChecked(),
            "page_size": self.settings.combo_size.currentText(),
            "margins": (self.settings.spin_margin_top.value(), self.settings.spin_margin_bottom.value(), self.settings.spin_margin_left.value(), self.settings.spin_margin_right.value()),
            "author_text": self.settings.input_author.text().strip(),
            "hf_pos": self.settings.combo_hf_pos.currentText(),
            "hf_align": self.settings.combo_hf_align.currentText(),
            "cover_type": cover_type,
            "cover_file_path": self.settings.cover_file_path,
            "cover_image_path": self.settings.cover_image_path,
            "cover_bg_css": cover_bg_css,  
            "bab_style_mode": self.settings.combo_bab_style.currentText(),
            "bab_font_size": self.settings.spin_bab_size.value(),
            "materi_style_text": self.settings.combo_materi_style.currentText(),
            "materi_font_size": self.settings.spin_materi_size.value(),
            "custom_titles": self.custom_titles,
            "file_bab_mapping": self.file_bab_mapping
        }

    def _update_progress(self, val):
        self.progress_bar.setValue(val)
        QApplication.processEvents()

    def create_zip_archive(self):
        if not self.base_dir:
            QMessageBox.warning(self, "Peringatan", "Pilih folder materi terlebih dahulu!")
            return

        out_name = self.output_name.text().strip()
        if not out_name:
            out_name = "Arsip_Materi"
        if not out_name.endswith(".zip"):
            out_name += ".zip"

        default_path = os.path.join(self.base_dir, out_name)
        
        if self.settings.cb_auto_export.isChecked():
            save_path = default_path
        else:
            save_path, _ = QFileDialog.getSaveFileName(self, "Simpan Arsip ZIP", default_path, "ZIP Files (*.zip)")

        if not save_path:
            return

        self.set_ui_enabled(False)
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("Sedang membuat file ZIP...")
        QApplication.processEvents()

        try:
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.base_dir):
                    for file in files:
                        if file.lower().endswith('.pdf') or file == os.path.basename(save_path):
                            continue
                        
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.base_dir)
                        zipf.write(file_path, arcname)

            self.progress_bar.hide()
            QMessageBox.information(self, "Berhasil", f"File ZIP berhasil dibuat:\n{save_path}")
        except Exception as e:
            self.progress_bar.hide()
            QMessageBox.critical(self, "Error", f"Gagal membuat file ZIP:\n{str(e)}")
        finally:
            self.set_ui_enabled(True)

    def merge_to_html(self):
        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "Peringatan", "Daftar file materi kosong!")
            return

        self.set_ui_enabled(False)
        self.progress_bar.show()
        self.progress_bar.setRange(0, count)
        self.progress_bar.setFormat("%p%")

        items = [os.path.join(self.base_dir, self.file_list.item(i).text()) for i in range(count)]
        options = self._get_export_options(is_pdf=False)
        
        html_content = generate_combined_html(items, options, self._update_progress)
        
        if html_content:
            out_name = self.output_name.text() if self.output_name.text().endswith(".html") else self.output_name.text() + ".html"
            out_file = os.path.join(self.base_dir, out_name) if self.base_dir else out_name
            
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            QMessageBox.information(self, "Berhasil", f"File HTML berhasil dibuat: {out_file}")
            
        self.progress_bar.hide()
        self.set_ui_enabled(True)

    def merge_to_pdf(self):
        count = self.file_list.count()
        if count == 0: return

        self.set_ui_enabled(False)
        self.progress_bar.show()
        self.progress_bar.setRange(0, count)
        self.progress_bar.setFormat("%p%")

        items = [os.path.join(self.base_dir, self.file_list.item(i).text()) for i in range(count)]
        options = self._get_export_options(is_pdf=True)
        html_content = generate_combined_html(items, options, self._update_progress)

        if not html_content:
            self.set_ui_enabled(True)
            return

        out_name = self.output_name.text() if self.output_name.text().endswith(".pdf") else self.output_name.text() + ".pdf"
        out_file = os.path.join(self.base_dir, out_name) if self.base_dir else out_name
        
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("Sedang merender PDF...")

        self.worker = PDFWorker(html_content, out_file)
        self.worker.finished.connect(self.on_pdf_success)
        self.worker.error.connect(self.on_pdf_error)
        self.worker.start()

    def on_pdf_success(self, output_file):
        self.progress_bar.hide()
        self.set_ui_enabled(True)
        QMessageBox.information(self, "Berhasil", f"File PDF berhasil dibuat: {output_file}")

    def on_pdf_error(self, error_msg):
        self.progress_bar.hide()
        self.set_ui_enabled(True)
        QMessageBox.critical(self, "Error", f"Gagal membuat PDF:\n{error_msg}")
