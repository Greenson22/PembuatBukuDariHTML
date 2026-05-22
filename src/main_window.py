import os
import json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QFileDialog, 
                             QLabel, QLineEdit, QMessageBox, QCheckBox, QProgressBar,
                             QComboBox, QRadioButton, QButtonGroup, QScrollArea, 
                             QSpinBox, QFrame, QApplication, QDialog, QDialogButtonBox)

from styles import get_modern_theme
from pdf_worker import PDFWorker
from html_merger import generate_combined_html


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pengaturan Dokumen")
        self.setMinimumWidth(600)
        
        self.cover_file_path = None
        self.cover_image_path = None
        self._is_updating_margins = False
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 1. Ukuran Kertas
        size_layout = QHBoxLayout()
        size_label = QLabel("Ukuran Kertas (PDF):")
        size_label.setObjectName("sectionLabel")
        self.combo_size = QComboBox()
        self.combo_size.addItems(["A4", "Letter", "Legal", "A3", "A5"])
        self.combo_size.setCurrentText("A4") 
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.combo_size)
        size_layout.addStretch()
        layout.addLayout(size_layout)

        # 2. Pengaturan Margin
        margin_title = QLabel("Pengaturan Margin (PDF):")
        margin_title.setObjectName("sectionLabel")
        layout.addWidget(margin_title)

        preset_layout = QHBoxLayout()
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
        preset_layout.addWidget(QLabel("Gaya Margin:"))
        preset_layout.addWidget(self.combo_margin_preset)
        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        self.custom_margin_widget = QWidget()
        custom_margin_layout = QHBoxLayout(self.custom_margin_widget)
        custom_margin_layout.setContentsMargins(0, 0, 0, 0)
        self.spin_margin_top = self.create_margin_spinbox("Atas:", 13, custom_margin_layout)
        self.spin_margin_bottom = self.create_margin_spinbox("Bawah:", 13, custom_margin_layout)
        self.spin_margin_left = self.create_margin_spinbox("Kiri:", 13, custom_margin_layout)
        self.spin_margin_right = self.create_margin_spinbox("Kanan:", 13, custom_margin_layout)
        custom_margin_layout.addStretch()
        layout.addWidget(self.custom_margin_widget)
        self.custom_margin_widget.setVisible(False) 

        # 3. Pengaturan Cover
        cover_label = QLabel("Pengaturan Cover (Sampul Depan):")
        cover_label.setObjectName("sectionLabel")
        layout.addWidget(cover_label)

        cover_layout = QHBoxLayout()
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

        cover_layout.addWidget(self.radio_no_cover)
        cover_layout.addWidget(self.radio_html_cover)
        cover_layout.addWidget(self.radio_image_cover)
        cover_layout.addWidget(self.radio_text_cover)
        cover_layout.addStretch()
        layout.addLayout(cover_layout)

        cover_input_layout = QHBoxLayout()
        self.btn_select_cover = QPushButton("Pilih HTML Cover")
        self.btn_select_cover.setObjectName("btnInfo")
        self.btn_select_cover.setVisible(False)
        self.lbl_cover_status = QLabel("Belum ada file dipilih")
        self.lbl_cover_status.setVisible(False)

        self.btn_select_image = QPushButton("Pilih Foto/PDF")
        self.btn_select_image.setObjectName("btnInfo")
        self.btn_select_image.setVisible(False)
        self.lbl_image_status = QLabel("Belum ada file dipilih")
        self.lbl_image_status.setVisible(False)
        
        self.input_cover_title = QLineEdit()
        self.input_cover_title.setPlaceholderText("Masukkan Judul Cover Dokumen...")
        self.input_cover_title.setVisible(False)

        cover_input_layout.addWidget(self.btn_select_cover)
        cover_input_layout.addWidget(self.lbl_cover_status)
        cover_input_layout.addWidget(self.btn_select_image)
        cover_input_layout.addWidget(self.lbl_image_status)
        cover_input_layout.addWidget(self.input_cover_title)
        layout.addLayout(cover_input_layout)

        # 4. Pengaturan Teks / Penulis (Khusus PDF)
        layout.addWidget(QLabel("Pengaturan Teks / Penulis (Khusus PDF):", objectName="sectionLabel"))
        hf_input_layout = QHBoxLayout()
        self.input_author = QLineEdit("F. R. Gerung") 
        self.combo_hf_pos = QComboBox()
        self.combo_hf_pos.addItems(["Header", "Footer"]) 
        self.combo_hf_align = QComboBox()
        self.combo_hf_align.addItems(["Kiri", "Tengah", "Kanan"]) 
        
        hf_input_layout.addWidget(QLabel("Teks:"))
        hf_input_layout.addWidget(self.input_author)
        hf_input_layout.addWidget(self.combo_hf_pos)
        hf_input_layout.addWidget(self.combo_hf_align)
        layout.addLayout(hf_input_layout)

        # 5. Pengaturan Visual Judul BAB
        layout.addWidget(QLabel("Pengaturan Visual Judul BAB (Jika Aktif):", objectName="sectionLabel"))
        bab_inputs = QHBoxLayout()
        self.combo_bab_style = QComboBox()
        self.combo_bab_style.addItems(["Minimalis Elegan", "Klasik Tengah (Default)", "Modern Kiri (Garis Bawah)", "Blok Latar Warna"])
        self.spin_bab_size = QSpinBox()
        self.spin_bab_size.setRange(16, 100)
        self.spin_bab_size.setValue(16) 
        bab_inputs.addWidget(QLabel("Tema BAB:"))
        bab_inputs.addWidget(self.combo_bab_style)
        bab_inputs.addWidget(QLabel("Ukuran Font:"))
        bab_inputs.addWidget(self.spin_bab_size)
        bab_inputs.addStretch()
        layout.addLayout(bab_inputs)

        # 6. Pengaturan Visual Judul File (Materi)
        layout.addWidget(QLabel("Pengaturan Visual Judul File (Materi):", objectName="sectionLabel"))
        materi_inputs = QHBoxLayout()
        self.combo_materi_style = QComboBox()
        self.combo_materi_style.addItems(["Miring (Italic)", "Normal", "Tebal (Bold)", "Tebal & Miring"])
        self.spin_materi_size = QSpinBox()
        self.spin_materi_size.setRange(8, 36)
        self.spin_materi_size.setValue(12)
        materi_inputs.addWidget(QLabel("Gaya Teks:"))
        materi_inputs.addWidget(self.combo_materi_style)
        materi_inputs.addWidget(QLabel("Ukuran Font:"))
        materi_inputs.addWidget(self.spin_materi_size)
        materi_inputs.addStretch()
        layout.addLayout(materi_inputs)

        layout.addStretch()

        layout.addWidget(QLabel("Pengaturan Umum Dokumen:", objectName="sectionLabel"))
        self.cb_toc = QCheckBox("Buat Daftar Isi Otomatis")
        self.cb_toc.setChecked(True)
        self.cb_page_numbers = QCheckBox("Tambahkan Nomor Halaman (Khusus Ekspor PDF)")
        self.cb_page_numbers.setChecked(True)
        
        layout.addWidget(self.cb_toc)
        layout.addWidget(self.cb_page_numbers)
        
        # Tombol Tutup
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.accept)
        layout.addWidget(btn_box)

        # Connections
        self.combo_margin_preset.currentIndexChanged.connect(self.apply_margin_preset)
        self.radio_no_cover.toggled.connect(self.toggle_cover_options)
        self.radio_html_cover.toggled.connect(self.toggle_cover_options)
        self.radio_image_cover.toggled.connect(self.toggle_cover_options)
        self.radio_text_cover.toggled.connect(self.toggle_cover_options)
        self.btn_select_cover.clicked.connect(self.select_cover_file)
        self.btn_select_image.clicked.connect(self.select_cover_image)

        self.apply_margin_preset()

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
            self.lbl_cover_status.setText(f"<b><font color='#27ae60'>✓ File: {os.path.basename(file)}</font></b>")

    def select_cover_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Pilih Foto/PDF Cover", "", "Images & PDF (*.png *.jpg *.jpeg *.bmp *.pdf)")
        if file:
            self.cover_image_path = file
            self.lbl_image_status.setText(f"<b><font color='#27ae60'>✓ File: {os.path.basename(file)}</font></b>")


class HTMLMergerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTML & PDF Merger - Penggabung File")
        self.setMinimumSize(1000, 750) 
        
        self.custom_titles = {}
        self.file_bab_mapping = {}  
        
        # Variabel untuk menyimpan folder pertama kali dipilih
        self.base_dir = "" 
        
        # Inisiasi dialog pengaturan
        self.settings = SettingsDialog(self)

        self.setStyleSheet(get_modern_theme())
        self.init_ui()

    def init_ui(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.main_container = QWidget()
        self.main_container.setObjectName("mainContainer")
        
        # Layout utama window tanpa margin agar banner bisa full width
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.scroll_area.setWidget(self.main_container)
        self.setCentralWidget(self.scroll_area)

        # ================= TOP BANNER =================
        self.top_banner = QFrame()
        self.top_banner.setObjectName("topBanner")
        banner_layout = QHBoxLayout(self.top_banner)
        banner_layout.setContentsMargins(0, 15, 0, 15)
        
        title_label = QLabel("Penggabung Dokumen HTML & PDF")
        title_label.setObjectName("appTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_layout.addWidget(title_label)
        
        self.main_layout.addWidget(self.top_banner)

        # ================= CONTENT AREA =================
        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(25, 25, 25, 25)
        self.content_layout.setSpacing(20)

        self.left_layout = QVBoxLayout()
        self.left_layout.setSpacing(15)
        self.right_layout = QVBoxLayout()
        self.right_layout.setSpacing(15)
        
        # Split rasio layout 5:5 mirip gambar
        self.content_layout.addLayout(self.left_layout, stretch=5) 
        self.content_layout.addLayout(self.right_layout, stretch=5) 
        self.main_layout.addWidget(self.content_widget)
        self.main_layout.addStretch()

        # ================= BAGIAN KIRI =================
        
        # -- Card 1: Proses Eksekusi --
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

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.hide()
        l_exec.addWidget(self.progress_bar)
        
        self.left_layout.addWidget(self.card_exec)

        # -- Card 2: Judul Kustom & JSON --
        self.card_json = QFrame()
        self.card_json.setProperty("class", "Card")
        l_json = QVBoxLayout(self.card_json)
        l_json.setContentsMargins(20, 20, 20, 20)
        l_json.setSpacing(15)
        
        hbox_json_title = QHBoxLayout()
        lbl_json = QLabel("Judul Kustom & Struktur BAB")
        lbl_json.setProperty("class", "CardTitle")
        self.cb_group_bab = QCheckBox() # Berperan sebagai switch di kanan
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
        
        l_json.addWidget(self.btn_export_json)
        l_json.addWidget(self.btn_load_json)
        
        self.left_layout.addWidget(self.card_json)
        
        # -- Card 3: Status Default --
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
        
        # -- Card 1: Manajemen File --
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
        
        hbox_file_actions = QHBoxLayout()
        self.btn_delete = QPushButton("Hapus Terpilih")
        self.btn_delete.setObjectName("btnRed")
        self.btn_clear = QPushButton("Bersihkan Semua")
        self.btn_clear.setObjectName("btnGray")
        hbox_file_actions.addWidget(self.btn_delete)
        hbox_file_actions.addWidget(self.btn_clear)
        l_file.addLayout(hbox_file_actions)
        
        self.right_layout.addWidget(self.card_file)
        
        # -- Card 2: List File --
        self.card_list = QFrame()
        self.card_list.setProperty("class", "Card")
        l_list = QVBoxLayout(self.card_list)
        l_list.setContentsMargins(20, 20, 20, 20)
        
        lbl_list = QLabel("Urutan file materi yang akan digabung")
        lbl_list.setProperty("class", "CardTitle")
        l_list.addWidget(lbl_list)
        
        self.file_list = QListWidget()
        self.file_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.file_list.setMinimumHeight(250) 
        l_list.addWidget(self.file_list)
        
        self.right_layout.addWidget(self.card_list)

        # Signal connections
        self.btn_generate_html.clicked.connect(self.merge_to_html)
        self.btn_generate_pdf.clicked.connect(self.merge_to_pdf)
        self.btn_settings.clicked.connect(self.settings.exec) 
        
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_add_files.clicked.connect(self.add_files)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_export_json.clicked.connect(self.export_json_template)
        self.btn_load_json.clicked.connect(self.load_json_titles)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder")
        if folder:
            if not self.base_dir:
                self.base_dir = folder
                
            all_files = os.listdir(folder)
            html_files = []
            for f in all_files:
                f_lower = f.lower()
                file_path = os.path.join(folder, f)
                
                if f_lower in ["meta.json", "template_judul.json"]: 
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
            self.file_list.addItems(html_files)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Pilih File HTML", "", "HTML Files (*.html)")
        if files: 
            if not self.base_dir:
                self.base_dir = os.path.dirname(files[0])
            self.file_list.addItems(files)

    def delete_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def clear_all(self):
        self.file_list.clear()
        self.custom_titles.clear()
        self.file_bab_mapping.clear()
        
        self.lbl_json_status.setText("Status: Default (Nama File)")
        self.settings.lbl_cover_status.setText("Belum ada file dipilih")
        self.settings.lbl_image_status.setText("Belum ada file dipilih")
        self.settings.cover_file_path = None
        self.settings.cover_image_path = None
        self.base_dir = ""
        self.settings.radio_no_cover.setChecked(True)

    def export_json_template(self):
        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "Peringatan", "Tambahkan file HTML terlebih dahulu!")
            return

        template_data = {"judul_utama": "Masukkan Judul Dokumen Utama Di Sini", "struktur": {}}
        if self.cb_group_bab.isChecked():
            bab_dict = {os.path.basename(self.file_list.item(i).text()): os.path.basename(self.file_list.item(i).text()).replace('.html', '').title() for i in range(count)}
            template_data["struktur"]["BAB 1: Pendahuluan"] = bab_dict
        else:
            for i in range(count):
                f_name = os.path.basename(self.file_list.item(i).text())
                template_data["struktur"][f_name] = f_name.replace('.html', '').title()

        default_path = os.path.join(self.base_dir, "template_judul.json") if self.base_dir else "template_judul.json"
        save_path, _ = QFileDialog.getSaveFileName(self, "Simpan Template JSON", default_path, "JSON Files (*.json)")
        
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Berhasil", "Template JSON berhasil disimpan!")

    def load_json_titles(self):
        start_dir = self.base_dir if self.base_dir else ""
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih File JSON", start_dir, "JSON Files (*.json)")
        if file_path: self._process_json_file(file_path, show_message=True)

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
            if show_message: QMessageBox.information(self, "Berhasil", "Data judul berhasil dimuat!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def set_ui_enabled(self, enabled):
        self.btn_generate_html.setEnabled(enabled)
        self.btn_generate_pdf.setEnabled(enabled)
        self.btn_settings.setEnabled(enabled)
        self.btn_add_folder.setEnabled(enabled)
        self.btn_add_files.setEnabled(enabled)
        self.btn_delete.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)

    def _get_export_options(self, is_pdf):
        cover_type = "none"
        if self.settings.radio_html_cover.isChecked(): cover_type = "html"
        elif self.settings.radio_image_cover.isChecked(): cover_type = "image"
        elif self.settings.radio_text_cover.isChecked(): cover_type = "text"

        return {
            "doc_title": self.settings.input_cover_title.text().strip() or "Gabungan Materi",
            "is_pdf": is_pdf,
            
            # UBAH 2 BARIS INI: Tambahkan referensi 'self.settings.' di depannya
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

    def merge_to_html(self):
        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "Peringatan", "Daftar file materi kosong!")
            return

        self.set_ui_enabled(False)
        self.progress_bar.show()
        self.progress_bar.setRange(0, count)

        items = [self.file_list.item(i).text() for i in range(count)]
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

        items = [self.file_list.item(i).text() for i in range(count)]
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