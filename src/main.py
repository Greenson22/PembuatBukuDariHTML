import sys
import os
import json
from pathlib import Path
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QFileDialog, 
                             QLabel, QLineEdit, QMessageBox, QCheckBox, QProgressBar,
                             QComboBox, QRadioButton, QButtonGroup, QScrollArea, QSpinBox, QFrame)
from bs4 import BeautifulSoup

# ==========================================
# WORKER THREAD UNTUK PROSES PDF WEASYPRINT
# ==========================================
class PDFWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, html_string, output_file):
        super().__init__()
        self.html_string = html_string
        self.output_file = output_file

    def run(self):
        try:
            from weasyprint import HTML
            HTML(string=self.html_string).write_pdf(self.output_file)
            self.finished.emit(self.output_file)
        except Exception as e:
            self.error.emit(str(e))


# ==========================================
# KELAS UTAMA APLIKASI
# ==========================================
class HTMLMergerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTML & PDF Merger - Penggabung File")
        self.setMinimumSize(1000, 750) 
        
        # Variabel penyimpanan data
        self.custom_titles = {}
        self.file_bab_mapping = {}  
        self.cover_file_path = None
        self.cover_image_path = None
        self._is_updating_margins = False 

        self.apply_modern_theme()
        
        # QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        self.main_container = QWidget()
        
        # LAYOUT UTAMA
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(15)

        self.scroll_area.setWidget(self.main_container)
        self.setCentralWidget(self.scroll_area)

        # Header Title
        title_label = QLabel("Penggabung Dokumen HTML & PDF")
        title_label.setObjectName("appTitle")
        self.main_layout.addWidget(title_label)

        # ==========================================
        # SPLIT LAYOUT (KIRI & KANAN)
        # ==========================================
        self.split_layout = QHBoxLayout()
        self.split_layout.setSpacing(20)
        
        self.left_layout = QVBoxLayout()
        self.left_layout.setSpacing(10)
        
        self.right_layout = QVBoxLayout()
        self.right_layout.setSpacing(10)
        
        self.split_layout.addLayout(self.left_layout, stretch=6) 
        self.split_layout.addLayout(self.right_layout, stretch=4) 
        self.main_layout.addLayout(self.split_layout)

        # ==========================================
        # BAGIAN KANAN: Tombol & Daftar File
        # ==========================================
        right_title = QLabel("Manajemen File Materi")
        right_title.setObjectName("sectionLabel")
        self.right_layout.addWidget(right_title)

        # Tombol-tombol baris 1
        row1 = QHBoxLayout()
        self.btn_add_folder = QPushButton("Pilih Folder")
        self.btn_add_folder.setObjectName("btnActionSmall")
        self.btn_add_files = QPushButton("Pilih File HTML")
        self.btn_add_files.setObjectName("btnActionSmall")
        row1.addWidget(self.btn_add_folder)
        row1.addWidget(self.btn_add_files)

        # Tombol-tombol baris 2
        row2 = QHBoxLayout()
        self.btn_delete = QPushButton("Hapus Terpilih")
        self.btn_delete.setObjectName("btnDangerSmall")
        self.btn_clear = QPushButton("Bersihkan Semua")
        self.btn_clear.setObjectName("btnWarningSmall")
        row2.addWidget(self.btn_delete)
        row2.addWidget(self.btn_clear)

        self.right_layout.addLayout(row1)
        self.right_layout.addLayout(row2)

        list_label = QLabel("Urutan file materi yang akan digabung:")
        list_label.setObjectName("sectionLabel")
        self.right_layout.addWidget(list_label)
        
        self.file_list = QListWidget()
        self.file_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.file_list.setMinimumHeight(450) 
        self.right_layout.addWidget(self.file_list)
        
        self.right_layout.addStretch()

        # ==========================================
        # BAGIAN KIRI: Opsi & Pengaturan
        # ==========================================

        # --------------------------------------------------
        # 1. BAGIAN EKSEKUSI & OUTPUT (DIPINDAHKAN KE PALING ATAS AGAR SELALU TERLIHAT)
        # --------------------------------------------------
        action_title = QLabel("Proses Eksekusi & Nama Output:")
        action_title.setObjectName("sectionLabel")
        action_title.setStyleSheet("color: #e74c3c; font-size: 15px;") # Beri warna agak merah agar mencolok
        self.left_layout.addWidget(action_title)
        
        self.action_layout = QHBoxLayout()
        self.output_name = QLineEdit("Gabungan_Materi")
        self.output_name.setPlaceholderText("Nama file tanpa ekstensi...")
        
        self.btn_generate_html = QPushButton("Gabung HTML")
        self.btn_generate_html.setStyleSheet("background-color: #3498db; color: white; padding: 8px 12px; font-size: 13px; font-weight: bold; border-radius: 4px;")
        self.btn_generate_html.clicked.connect(self.merge_to_html)

        self.btn_generate_pdf = QPushButton("Gabung PDF")
        self.btn_generate_pdf.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 12px; font-size: 13px; font-weight: bold; border-radius: 4px;")
        self.btn_generate_pdf.clicked.connect(self.merge_to_pdf)

        self.action_layout.addWidget(self.output_name)
        self.action_layout.addWidget(self.btn_generate_html)
        self.action_layout.addWidget(self.btn_generate_pdf)
        
        self.left_layout.addLayout(self.action_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.hide()
        self.left_layout.addWidget(self.progress_bar)

        # Garis Pemisah (Divider)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #dcdde1; margin-top: 5px; margin-bottom: 10px;")
        self.left_layout.addWidget(line)
        # --------------------------------------------------

        
        # 2. Ukuran Kertas PDF
        self.size_layout = QHBoxLayout()
        size_label = QLabel("Ukuran Kertas (PDF):")
        size_label.setObjectName("sectionLabel")
        self.combo_size = QComboBox()
        self.combo_size.addItems(["A4", "Letter", "Legal", "A3", "A5"])
        self.combo_size.setCurrentText("A4") 
        
        self.size_layout.addWidget(size_label)
        self.size_layout.addWidget(self.combo_size)
        self.size_layout.addStretch()
        self.left_layout.addLayout(self.size_layout)

        # 3. Pengaturan Margin
        margin_title = QLabel("Pengaturan Margin (PDF):")
        margin_title.setObjectName("sectionLabel")
        self.left_layout.addWidget(margin_title)

        self.preset_layout = QHBoxLayout()
        self.combo_margin_preset = QComboBox()
        self.combo_margin_preset.addItems([
            "Normal (Atas/Bawah 25mm, Kiri/Kanan 25mm)",
            "Sempit / Narrow (13mm)",
            "Moderat (Atas/Bawah 25mm, Kiri/Kanan 19mm)",
            "Lebar / Wide (Atas/Bawah 25mm, Kiri/Kanan 51mm)",
            "Tanpa Margin (0mm)",
            "Kustom / Manual"
        ])
        self.combo_margin_preset.setCurrentIndex(1)
        
        lbl_preset = QLabel("Gaya Margin:")
        self.preset_layout.addWidget(lbl_preset)
        self.preset_layout.addWidget(self.combo_margin_preset)
        self.preset_layout.addStretch()
        self.left_layout.addLayout(self.preset_layout)

        # Kotak Input Manual
        self.custom_margin_widget = QWidget()
        self.custom_margin_layout = QHBoxLayout(self.custom_margin_widget)
        self.custom_margin_layout.setContentsMargins(0, 0, 0, 0)
        
        self.spin_margin_top = self.create_margin_spinbox("Atas:", 13, self.custom_margin_layout)
        self.spin_margin_bottom = self.create_margin_spinbox("Bawah:", 13, self.custom_margin_layout)
        self.spin_margin_left = self.create_margin_spinbox("Kiri:", 13, self.custom_margin_layout)
        self.spin_margin_right = self.create_margin_spinbox("Kanan:", 13, self.custom_margin_layout)
        self.custom_margin_layout.addStretch()
        
        self.left_layout.addWidget(self.custom_margin_widget)
        self.custom_margin_widget.setVisible(False) 

        self.combo_margin_preset.currentIndexChanged.connect(self.apply_margin_preset)
        self.apply_margin_preset()

        # 4. Pengaturan Cover
        cover_label = QLabel("Pengaturan Cover (Sampul Depan):")
        cover_label.setObjectName("sectionLabel")
        self.left_layout.addWidget(cover_label)

        self.cover_layout = QHBoxLayout()
        
        self.radio_no_cover = QRadioButton("Tanpa Cover")
        self.radio_no_cover.setChecked(True)
        self.radio_html_cover = QRadioButton("Gunakan File HTML")
        self.radio_image_cover = QRadioButton("Gunakan Foto/PDF")
        self.radio_text_cover = QRadioButton("Judul Sederhana")

        self.cover_group = QButtonGroup()
        self.cover_group.addButton(self.radio_no_cover)
        self.cover_group.addButton(self.radio_html_cover)
        self.cover_group.addButton(self.radio_image_cover)
        self.cover_group.addButton(self.radio_text_cover)

        self.cover_layout.addWidget(self.radio_no_cover)
        self.cover_layout.addWidget(self.radio_html_cover)
        self.cover_layout.addWidget(self.radio_image_cover)
        self.cover_layout.addWidget(self.radio_text_cover)
        self.cover_layout.addStretch()
        self.left_layout.addLayout(self.cover_layout)

        # Input dinamis untuk Cover
        self.cover_input_layout = QHBoxLayout()
        self.btn_select_cover = QPushButton("Pilih HTML Cover")
        self.btn_select_cover.setObjectName("btnInfo")
        self.btn_select_cover.setVisible(False)
        self.lbl_cover_status = QLabel("Belum ada file dipilih")
        self.lbl_cover_status.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.lbl_cover_status.setVisible(False)

        self.btn_select_image = QPushButton("Pilih Foto/PDF")
        self.btn_select_image.setObjectName("btnInfo")
        self.btn_select_image.setVisible(False)
        self.lbl_image_status = QLabel("Belum ada file dipilih")
        self.lbl_image_status.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.lbl_image_status.setVisible(False)
        
        self.input_cover_title = QLineEdit()
        self.input_cover_title.setPlaceholderText("Masukkan Judul Cover Dokumen...")
        self.input_cover_title.setVisible(False)

        self.cover_input_layout.addWidget(self.btn_select_cover)
        self.cover_input_layout.addWidget(self.lbl_cover_status)
        self.cover_input_layout.addWidget(self.btn_select_image)
        self.cover_input_layout.addWidget(self.lbl_image_status)
        self.cover_input_layout.addWidget(self.input_cover_title)
        self.left_layout.addLayout(self.cover_input_layout)

        self.radio_no_cover.toggled.connect(self.toggle_cover_options)
        self.radio_html_cover.toggled.connect(self.toggle_cover_options)
        self.radio_image_cover.toggled.connect(self.toggle_cover_options)
        self.radio_text_cover.toggled.connect(self.toggle_cover_options)
        self.btn_select_cover.clicked.connect(self.select_cover_file)
        self.btn_select_image.clicked.connect(self.select_cover_image)

        # 5. Bagian Opsi Tambahan (Checklist)
        self.options_layout = QVBoxLayout() 
        self.options_layout.setSpacing(4)
        
        self.cb_toc = QCheckBox("Buat Daftar Isi Otomatis")
        self.cb_toc.setChecked(True)
        self.cb_page_numbers = QCheckBox("Tambahkan Nomor Halaman (Khusus Ekspor PDF)")
        self.cb_page_numbers.setChecked(True)
        
        self.options_layout.addWidget(self.cb_toc)
        self.options_layout.addWidget(self.cb_page_numbers)
        self.left_layout.addLayout(self.options_layout)

        # ==================================================
        # 6. Pengaturan Header / Footer (Penulis)
        # ==================================================
        self.hf_layout = QVBoxLayout()
        hf_label = QLabel("Pengaturan Teks / Penulis (Khusus PDF):")
        hf_label.setObjectName("sectionLabel")
        self.left_layout.addWidget(hf_label)

        hf_input_layout = QHBoxLayout()
        self.input_author = QLineEdit("F.R.Gerung") # Default value
        self.input_author.setPlaceholderText("Masukkan teks/penulis...")
        
        self.combo_hf_pos = QComboBox()
        self.combo_hf_pos.addItems(["Header", "Footer"]) # Default Header
        
        self.combo_hf_align = QComboBox()
        self.combo_hf_align.addItems(["Kiri", "Tengah", "Kanan"]) # Default Kiri
        
        hf_input_layout.addWidget(QLabel("Teks:"))
        hf_input_layout.addWidget(self.input_author)
        hf_input_layout.addWidget(self.combo_hf_pos)
        hf_input_layout.addWidget(self.combo_hf_align)
        
        self.hf_layout.addLayout(hf_input_layout)
        self.left_layout.addLayout(self.hf_layout)

        # ==================================================
        # 7. Pengaturan Gaya Visual Penulisan BAB
        # ==================================================
        self.bab_style_layout = QVBoxLayout()
        bab_style_label = QLabel("Pengaturan Visual Judul BAB (Jika Aktif):")
        bab_style_label.setObjectName("sectionLabel")
        self.left_layout.addWidget(bab_style_label)

        bab_inputs = QHBoxLayout()
        
        self.combo_bab_style = QComboBox()
        self.combo_bab_style.addItems([
            "Klasik Tengah (Default)", 
            "Modern Kiri (Garis Bawah)", 
            "Blok Latar Warna", 
            "Minimalis Elegan"
        ])
        
        self.spin_bab_size = QSpinBox()
        self.spin_bab_size.setRange(16, 100)
        self.spin_bab_size.setValue(38) # Default
        self.spin_bab_size.setSuffix(" pt")
        
        bab_inputs.addWidget(QLabel("Tema BAB:"))
        bab_inputs.addWidget(self.combo_bab_style)
        bab_inputs.addWidget(QLabel("Ukuran Font:"))
        bab_inputs.addWidget(self.spin_bab_size)
        bab_inputs.addStretch()
        
        self.bab_style_layout.addLayout(bab_inputs)
        self.left_layout.addLayout(self.bab_style_layout)

        # 8. Manajemen JSON untuk Judul & BAB
        self.json_layout = QVBoxLayout()
        json_label = QLabel("Judul Kustom & Struktur BAB (Opsional):")
        json_label.setObjectName("sectionLabel")
        
        self.cb_group_bab = QCheckBox("Tambahkan grup BAB di dalam Template JSON (Hirarki Bersarang)")
        self.cb_group_bab.setChecked(False)

        json_btns_layout = QHBoxLayout()
        self.btn_export_json = QPushButton("1. Ekspor Template JSON")
        self.btn_export_json.setObjectName("btnInfo")
        self.btn_load_json = QPushButton("2. Muat Judul JSON")
        self.btn_load_json.setObjectName("btnInfo")
        
        json_btns_layout.addWidget(self.btn_export_json)
        json_btns_layout.addWidget(self.btn_load_json)
        json_btns_layout.addStretch()

        self.lbl_json_status = QLabel("Status: Default (Nama File)")
        self.lbl_json_status.setStyleSheet("color: #7f8c8d; font-style: italic; margin-top: 5px;")

        self.json_layout.addWidget(json_label)
        self.json_layout.addWidget(self.cb_group_bab)
        self.json_layout.addLayout(json_btns_layout)
        self.json_layout.addWidget(self.lbl_json_status)
        
        self.left_layout.addLayout(self.json_layout)
        
        # Mendorong seluruh isi left_layout ke atas agar rapat
        self.left_layout.addStretch() 

        # Connect signals
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_add_files.clicked.connect(self.add_files)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_export_json.clicked.connect(self.export_json_template)
        self.btn_load_json.clicked.connect(self.load_json_titles)

    def apply_modern_theme(self):
        modern_qss = """
            QMainWindow { background-color: #f4f6f9; }
            QLabel { font-family: 'Segoe UI', Arial, sans-serif; color: #2c3e50; }
            QLabel#appTitle { font-size: 22px; font-weight: bold; color: #1a252f; margin-bottom: 10px; }
            QLabel#sectionLabel { font-size: 14px; font-weight: 600; margin-top: 5px; }
            
            QPushButton {
                background-color: #34495e; color: white; border: none;
                border-radius: 6px; padding: 10px 15px;
                font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: #2c3e50; }
            QPushButton:pressed { background-color: #1a252f; }
            
            QPushButton#btnActionSmall { background-color: #34495e; padding: 6px 12px; font-size: 12px; border-radius: 4px; color: white; font-weight: 600; }
            QPushButton#btnDangerSmall { background-color: #e74c3c; padding: 6px 12px; font-size: 12px; border-radius: 4px; color: white; font-weight: 600; }
            QPushButton#btnDangerSmall:hover { background-color: #c0392b; }
            QPushButton#btnWarningSmall { background-color: #95a5a6; padding: 6px 12px; font-size: 12px; border-radius: 4px; color: white; font-weight: 600; }
            QPushButton#btnInfo { background-color: #8e44ad; padding: 8px 12px; font-size: 12px; }
            QPushButton#btnInfo:hover { background-color: #732d91; }
            
            QListWidget, QComboBox {
                background-color: white; border: 1px solid #dcdde1; border-radius: 6px;
                padding: 5px; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #2f3640;
            }
            QComboBox { padding: 5px 10px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #f1f2f6; }
            QListWidget::item:selected { background-color: #e8f4fd; color: #2980b9; border-radius: 4px; }
            QRadioButton, QCheckBox { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #2c3e50; }
            QLineEdit, QSpinBox {
                padding: 6px 10px; border: 1px solid #dcdde1; border-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px;
                background-color: white; color: #2c3e50;
            }
            QProgressBar { border: 1px solid #dcdde1; border-radius: 6px; text-align: center; background-color: white; color: #2c3e50; font-weight: bold; height: 18px; }
            QProgressBar::chunk { background-color: #3498db; border-radius: 5px; }
        """
        self.setStyleSheet(modern_qss)

    def create_margin_spinbox(self, label_text, default_value, parent_layout):
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,10,0)
        lbl = QLabel(label_text)
        spin = QSpinBox()
        spin.setRange(0, 500)
        spin.setValue(default_value)
        spin.setSuffix(" mm")
        layout.addWidget(lbl)
        layout.addWidget(spin)
        parent_layout.addLayout(layout)
        return spin

    def apply_margin_preset(self):
        if self._is_updating_margins: return
        self._is_updating_margins = True
        text = self.combo_margin_preset.currentText()
        self.custom_margin_widget.setVisible("Kustom" in text)

        if "Normal" in text: self._set_spin_margins(25, 25, 25, 25)
        elif "Sempit" in text: self._set_spin_margins(13, 13, 13, 13)
        elif "Moderat" in text: self._set_spin_margins(25, 25, 19, 19)
        elif "Lebar" in text: self._set_spin_margins(25, 25, 51, 51)
        elif "Tanpa" in text: self._set_spin_margins(0, 0, 0, 0)
        self._is_updating_margins = False

    def _set_spin_margins(self, top, bottom, left, right):
        self.spin_margin_top.setValue(top)
        self.spin_margin_bottom.setValue(bottom)
        self.spin_margin_left.setValue(left)
        self.spin_margin_right.setValue(right)

    def toggle_cover_options(self):
        self.btn_select_cover.setVisible(False)
        self.lbl_cover_status.setVisible(False)
        self.input_cover_title.setVisible(False)
        self.btn_select_image.setVisible(False)
        self.lbl_image_status.setVisible(False)

        if self.radio_html_cover.isChecked():
            self.btn_select_cover.setVisible(True)
            self.lbl_cover_status.setVisible(True)
        elif self.radio_text_cover.isChecked():
            self.input_cover_title.setVisible(True)
        elif self.radio_image_cover.isChecked():
            self.btn_select_image.setVisible(True)
            self.lbl_image_status.setVisible(True)

    def select_cover_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Pilih File HTML Cover", "", "HTML Files (*.html)")
        if file:
            self.cover_file_path = file
            self.lbl_cover_status.setText(f"File: {os.path.basename(file)}")

    def select_cover_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Pilih Foto/PDF Cover", "", "Images & PDF (*.png *.jpg *.jpeg *.bmp *.pdf)")
        if file:
            self.cover_image_path = file
            self.lbl_image_status.setText(f"File: {os.path.basename(file)}")

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder")
        if folder:
            all_files = os.listdir(folder)
            html_files = []
            
            for f in all_files:
                f_lower = f.lower()
                file_path = os.path.join(folder, f)
                
                if f_lower == "meta.json":
                    self._process_json_file(file_path, show_message=False)
                
                elif f_lower == "cover.html":
                    self.radio_html_cover.setChecked(True)
                    self.cover_file_path = file_path
                    self.lbl_cover_status.setText(f"File: {f}")
                    self.lbl_cover_status.setStyleSheet("color: #27ae60; font-weight: bold;")
                
                elif f_lower.startswith("cover.") and f_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.pdf')):
                    self.radio_image_cover.setChecked(True)
                    self.cover_image_path = file_path
                    self.lbl_image_status.setText(f"File: {f}")
                    self.lbl_image_status.setStyleSheet("color: #27ae60; font-weight: bold;")

                elif f_lower.endswith('.html') and f_lower != "cover.html":
                    html_files.append(file_path)

            html_files.sort()
            self.file_list.addItems(html_files)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Pilih File HTML", "", "HTML Files (*.html)")
        if files:
            self.file_list.addItems(files)

    def delete_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def clear_all(self):
        self.file_list.clear()
        self.custom_titles = {}
        self.file_bab_mapping = {}
        self.lbl_json_status.setText("Status: Default (Nama File)")
        self.lbl_json_status.setStyleSheet("color: #7f8c8d; font-style: italic; margin-top: 5px;")
        self.cover_file_path = None
        self.cover_image_path = None
        self.radio_no_cover.setChecked(True)
        self.lbl_cover_status.setText("Belum ada file dipilih")
        self.lbl_image_status.setText("Belum ada file dipilih")

    def export_json_template(self):
        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "Peringatan", "Tambahkan file HTML terlebih dahulu sebelum mengekspor JSON!")
            return

        template_data = {
            "judul_utama": "Masukkan Judul Dokumen Utama Di Sini",
            "struktur": {}
        }
        
        use_bab = self.cb_group_bab.isChecked()

        if use_bab:
            bab_dict = {}
            for i in range(count):
                file_name = os.path.basename(self.file_list.item(i).text())
                clean_title = file_name.replace('.html', '').replace('_', ' ').replace('-', ' ').title()
                bab_dict[file_name] = clean_title
            template_data["struktur"]["BAB 1: Pendahuluan"] = bab_dict
        else:
            for i in range(count):
                file_name = os.path.basename(self.file_list.item(i).text())
                clean_title = file_name.replace('.html', '').replace('_', ' ').replace('-', ' ').title()
                template_data["struktur"][file_name] = clean_title

        save_path, _ = QFileDialog.getSaveFileName(self, "Simpan Template JSON", "template_judul.json", "JSON Files (*.json)")
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=4, ensure_ascii=False)
                QMessageBox.information(self, "Berhasil", f"Template JSON berhasil disimpan di:\n{save_path}\n\nSilakan edit (tambah nama BAB jika perlu), lalu muat kembali.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menyimpan JSON: {str(e)}")

    def load_json_titles(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih File JSON", "", "JSON Files (*.json)")
        if file_path:
            self._process_json_file(file_path, show_message=True)

    def _process_json_file(self, file_path, show_message=False):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.custom_titles.clear()
            self.file_bab_mapping.clear()

            if "judul_utama" in data:
                judul = data.pop("judul_utama")
                self.input_cover_title.setText(judul)
                self.output_name.setText(judul) 
                
                if self.radio_no_cover.isChecked():
                    self.radio_text_cover.setChecked(True)
                
            if "struktur" in data:
                data = data["struktur"]

            is_nested = data and isinstance(next(iter(data.values())), dict)

            if is_nested:
                for bab_name, files_dict in data.items():
                    for file_name, file_title in files_dict.items():
                        self.custom_titles[file_name] = file_title
                        self.file_bab_mapping[file_name] = bab_name
            else:
                self.custom_titles = data

            filename = os.path.basename(file_path)
            mode_str = "(Mode: BAB Aktif)" if is_nested else "(Mode: Datar)"
            self.lbl_json_status.setText(f"Status: Menggunakan {filename} {mode_str}")
            self.lbl_json_status.setStyleSheet("color: #27ae60; font-weight: bold; margin-top: 5px;")
            
            if show_message:
                QMessageBox.information(self, "Berhasil", "Data judul (dan struktur BAB) berhasil dimuat!")
        except Exception as e:
            self.custom_titles = {}
            self.file_bab_mapping = {}
            self.lbl_json_status.setText("Status: Gagal memuat JSON")
            self.lbl_json_status.setStyleSheet("color: #e74c3c; margin-top: 5px;")
            if show_message:
                QMessageBox.critical(self, "Error", f"Gagal membaca JSON:\n{str(e)}")

    def set_ui_enabled(self, enabled):
        self.btn_generate_html.setEnabled(enabled)
        self.btn_generate_pdf.setEnabled(enabled)
        self.btn_add_folder.setEnabled(enabled)
        self.btn_add_files.setEnabled(enabled)
        self.btn_delete.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)

    def generate_combined_html_string(self, is_pdf=False):
        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "Peringatan", "Daftar file materi masih kosong!")
            return None

        items = [self.file_list.item(i).text() for i in range(count)]
        doc_title = self.input_cover_title.text().strip() or "Gabungan Materi"

        # --- 1. HEAD & CSS ---
        html_head = "\n<!DOCTYPE html>\n<html lang='id'>\n<head>\n"
        html_head += "    <meta charset='UTF-8'>\n"
        html_head += f"    <title>{doc_title}</title>\n"
        html_head += "    <style>\n"
        html_head += "        body { font-family: Arial, sans-serif; line-height: 1.6; }\n"
        html_head += "        .section-container { margin-bottom: 50px; padding-bottom: 20px; }\n"
        html_head += "        .page-break { page-break-before: always; }\n"
        
        if self.cb_toc.isChecked():
            html_head += """
                .toc-container { margin-bottom: 50px; }
                .toc-container h1 { text-align: center; margin-bottom: 30px; }
                .toc-list { list-style-type: none; padding: 0; }
                .toc-list li { margin-bottom: 10px; font-size: 14pt; }
                .toc-list a { text-decoration: none; color: #333; display: block; }
            """
            if is_pdf:
                html_head += ".toc-list a.toc-link::after { content: leader('.') target-counter(attr(href), page); }"

        if is_pdf:
            page_size = self.combo_size.currentText()
            m_top, m_bottom = self.spin_margin_top.value(), self.spin_margin_bottom.value()
            m_left, m_right = self.spin_margin_left.value(), self.spin_margin_right.value()

            html_head += f"""
                @page {{
                    size: {page_size};
                    margin: {m_top}mm {m_right}mm {m_bottom}mm {m_left}mm;
            """
            
            # Rendering Header/Footer & Nomor Halaman
            author_text = self.input_author.text().strip()
            if author_text:
                pos = "top" if self.combo_hf_pos.currentText() == "Header" else "bottom"
                align = "left"
                if self.combo_hf_align.currentText() == "Tengah": align = "center"
                elif self.combo_hf_align.currentText() == "Kanan": align = "right"
                
                if self.cb_page_numbers.isChecked() and pos == "bottom" and align == "right":
                    html_head += f"""
                        @bottom-right {{ content: "{author_text} | Halaman " counter(page) " dari " counter(pages); font-family: Arial, sans-serif; font-size: 10pt; color: #555; }}
                    """
                else:
                    html_head += f"""
                        @{pos}-{align} {{ content: "{author_text}"; font-family: Arial, sans-serif; font-size: 10pt; color: #555; }}
                    """
                    if self.cb_page_numbers.isChecked():
                        html_head += """
                            @bottom-right { content: "Halaman " counter(page) " dari " counter(pages); font-family: Arial, sans-serif; font-size: 10pt; color: #555; }
                        """
            else:
                if self.cb_page_numbers.isChecked():
                    html_head += """
                        @bottom-right { content: "Halaman " counter(page) " dari " counter(pages); font-family: Arial, sans-serif; font-size: 10pt; color: #555; }
                    """

            html_head += "        }\n"

            if self.cb_page_numbers.isChecked() or author_text:
                html_head += """
                @page cover {
                    @top-left { content: none; }
                    @top-center { content: none; }
                    @top-right { content: none; }
                    @bottom-left { content: none; }
                    @bottom-center { content: none; }
                    @bottom-right { content: none; }
                }
                .cover-container { page: cover; }
                """

        html_head += "    </style>\n</head>\n<body>\n"

        # --- 2. COVER ---
        cover_html = ""
        if self.radio_html_cover.isChecked() and self.cover_file_path:
            with open(self.cover_file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                body_content = soup.find('body')
                content = str(body_content.decode_contents()) if body_content else str(soup)
                cover_html += f"    <div class='cover-container'>\n{content}\n    </div>\n"
                if is_pdf: cover_html += "    <div class='page-break'></div>\n"
        elif self.radio_image_cover.isChecked() and self.cover_image_path:
            file_uri = Path(os.path.abspath(self.cover_image_path)).as_uri()
            cover_html += f"<div class='cover-container' style='width: 100%; height: 98vh; overflow: hidden;'><img src='{file_uri}' style='width: 100%; height: 100%; object-fit: cover; object-position: top; display: block;' /></div>\n"
            if is_pdf: cover_html += "    <div class='page-break'></div>\n"
        elif self.radio_text_cover.isChecked():
            judul = self.input_cover_title.text().strip() or "Judul Dokumen (Kosong)"
            cover_html += f"<div class='cover-container' style='text-align: center; margin-top: 35%; padding: 20px;'><h1 style='font-size: 42pt; color: #2c3e50;'>{judul}</h1></div>\n"
            if is_pdf: cover_html += "    <div class='page-break'></div>\n"

        # --- 3. DAFTAR ISI KEPALA ---
        toc_html = ""
        if self.cb_toc.isChecked():
            toc_html += "<div class='toc-container'>\n    <h1>Daftar Isi</h1>\n    <ul class='toc-list'>\n"

        # --- 4. RENDER ISI & STYLING BAB ---
        body_html = ""
        self.progress_bar.show()
        self.progress_bar.setRange(0, count)
        
        current_bab = None
        is_first_body_item = True 
        
        # Ambil setelan gaya penulisan BAB
        bab_style_mode = self.combo_bab_style.currentText()
        bab_font_size = self.spin_bab_size.value()

        for i, file_path in enumerate(items):
            file_name = os.path.basename(file_path)
            
            display_title = self.custom_titles.get(file_name, file_name.replace('.html', '').replace('_', ' ').replace('-', ' ').title())
            bab_title = self.file_bab_mapping.get(file_name)
            
            if bab_title and bab_title != current_bab:
                current_bab = bab_title
                bab_id = f"bab-{i}"
                
                if self.cb_toc.isChecked():
                    toc_html += f"        <li style='margin-top: 20px; font-weight: bold; font-size: 16pt;'><a href='#{bab_id}' class='toc-link'>{bab_title}</a></li>\n"
                
                if is_pdf and not is_first_body_item:
                    body_html += "    <div class='page-break'></div>\n"
                
                # Menentukan CSS HTML untuk BAB berdasarkan pilihan Tema
                if "Modern Kiri" in bab_style_mode:
                    body_html += f"""
                    <div class='bab-container' id='{bab_id}' style='margin-top: 15%; margin-bottom: 50px; text-align: left; border-bottom: 4px solid #2980b9; padding-bottom: 15px;'>
                        <h1 style='font-size: {bab_font_size}pt; color: #2c3e50; margin: 0;'>{bab_title}</h1>
                    </div>
                    """
                elif "Blok Latar Warna" in bab_style_mode:
                    body_html += f"""
                    <div class='bab-container' id='{bab_id}' style='margin-top: 25%; margin-bottom: 50px; text-align: center; background-color: #ecf0f1; padding: 40px 20px; border-radius: 8px; border-left: 10px solid #34495e;'>
                        <h1 style='font-size: {bab_font_size}pt; color: #2c3e50; margin: 0;'>{bab_title}</h1>
                    </div>
                    """
                elif "Minimalis Elegan" in bab_style_mode:
                    body_html += f"""
                    <div class='bab-container' id='{bab_id}' style='margin-top: 30%; margin-bottom: 50px; text-align: center;'>
                        <h1 style='font-size: {bab_font_size}pt; color: #333; font-weight: normal; letter-spacing: 5px; text-transform: uppercase; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; padding: 25px 0;'>{bab_title}</h1>
                    </div>
                    """
                else: # Klasik Tengah (Default)
                    body_html += f"""
                    <div class='bab-container' id='{bab_id}' style='text-align: center; margin-top: 30%; margin-bottom: 50px;'>
                        <h1 style='font-size: {bab_font_size}pt; color: #000; margin: 0;'>{bab_title}</h1>
                    </div>
                    """
                
                is_first_body_item = False
                if is_pdf:
                    body_html += "    <div class='page-break'></div>\n"
            else:
                if is_pdf and not is_first_body_item:
                    body_html += "    <div class='page-break'></div>\n"

            element_id = f"file-{i}" 
            if self.cb_toc.isChecked():
                margin_kiri = "margin-left: 20px;" if current_bab else ""
                toc_html += f"        <li style='{margin_kiri}'><a href='#{element_id}' class='toc-link'>Materi: {display_title}</a></li>\n"

            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                body_content = soup.find('body')
                content = str(body_content.decode_contents()) if body_content else str(soup)
                
                body_html += f"    <div class='section-container' id='{element_id}'>\n"
                body_html += f"        <h2>Materi: {display_title}</h2>\n"
                body_html += content
                body_html += "\n    </div>\n"
            
            is_first_body_item = False 
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()

        if self.cb_toc.isChecked():
            toc_html += "    </ul>\n</div>\n"
            if is_pdf:
                toc_html += "<div class='page-break'></div>\n"

        full_html = html_head + cover_html + toc_html + body_html + "</body>\n</html>"
        return full_html

    def merge_to_html(self):
        self.set_ui_enabled(False)
        html_content = self.generate_combined_html_string(is_pdf=False)
        if html_content:
            output_file = self.output_name.text() if self.output_name.text().endswith(".html") else self.output_name.text() + ".html"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            QMessageBox.information(self, "Berhasil", f"File HTML berhasil dibuat: {output_file}")
        self.progress_bar.hide()
        self.set_ui_enabled(True)

    def merge_to_pdf(self):
        self.set_ui_enabled(False)
        html_content = self.generate_combined_html_string(is_pdf=True)
        if not html_content:
            self.progress_bar.hide()
            self.set_ui_enabled(True)
            return

        output_file = self.output_name.text() if self.output_name.text().endswith(".pdf") else self.output_name.text() + ".pdf"
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("Sedang merender PDF, harap tunggu...")

        self.worker = PDFWorker(html_content, output_file)
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HTMLMergerApp()
    window.show()
    sys.exit(app.exec())