import os
import json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QFileDialog, 
                             QLabel, QLineEdit, QMessageBox, QCheckBox, QProgressBar,
                             QComboBox, QRadioButton, QButtonGroup, QScrollArea, QSpinBox, QFrame, QApplication)

from styles import get_modern_theme
from pdf_worker import PDFWorker
from html_merger import generate_combined_html

class HTMLMergerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTML & PDF Merger - Penggabung File")
        self.setMinimumSize(1000, 750) 
        
        self.custom_titles = {}
        self.file_bab_mapping = {}  
        self.cover_file_path = None
        self.cover_image_path = None
        self._is_updating_margins = False 
        
        # Variabel untuk menyimpan folder pertama kali dipilih
        self.base_dir = "" 

        self.setStyleSheet(get_modern_theme())
        self.init_ui()

    def init_ui(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.main_container = QWidget()
        
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(15)

        self.scroll_area.setWidget(self.main_container)
        self.setCentralWidget(self.scroll_area)

        title_label = QLabel("Penggabung Dokumen HTML & PDF")
        title_label.setObjectName("appTitle")
        self.main_layout.addWidget(title_label)

        self.split_layout = QHBoxLayout()
        self.split_layout.setSpacing(20)
        self.left_layout = QVBoxLayout()
        self.left_layout.setSpacing(10)
        self.right_layout = QVBoxLayout()
        self.right_layout.setSpacing(10)
        self.split_layout.addLayout(self.left_layout, stretch=6) 
        self.split_layout.addLayout(self.right_layout, stretch=4) 
        self.main_layout.addLayout(self.split_layout)

        # BAGIAN KANAN
        right_title = QLabel("Manajemen File Materi")
        right_title.setObjectName("sectionLabel")
        self.right_layout.addWidget(right_title)

        row1 = QHBoxLayout()
        self.btn_add_folder = QPushButton("Pilih Folder")
        self.btn_add_folder.setObjectName("btnActionSmall")
        self.btn_add_files = QPushButton("Pilih File HTML")
        self.btn_add_files.setObjectName("btnActionSmall")
        row1.addWidget(self.btn_add_folder)
        row1.addWidget(self.btn_add_files)

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

        # BAGIAN KIRI
        action_title = QLabel("Proses Eksekusi & Nama Output:")
        action_title.setObjectName("sectionLabel")
        action_title.setStyleSheet("color: #e74c3c; font-size: 15px;")
        self.left_layout.addWidget(action_title)
        
        self.action_layout = QHBoxLayout()
        self.output_name = QLineEdit("Gabungan_Materi")
        self.output_name.setPlaceholderText("Nama file tanpa ekstensi...")
        
        self.btn_generate_html = QPushButton("Gabung HTML")
        self.btn_generate_html.setStyleSheet("background-color: #3498db; color: white; padding: 8px 12px; font-size: 13px; font-weight: bold; border-radius: 4px;")
        
        self.btn_generate_pdf = QPushButton("Gabung PDF")
        self.btn_generate_pdf.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 12px; font-size: 13px; font-weight: bold; border-radius: 4px;")

        self.action_layout.addWidget(self.output_name)
        self.action_layout.addWidget(self.btn_generate_html)
        self.action_layout.addWidget(self.btn_generate_pdf)
        self.left_layout.addLayout(self.action_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.hide()
        self.left_layout.addWidget(self.progress_bar)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #dcdde1; margin-top: 5px; margin-bottom: 10px;")
        self.left_layout.addWidget(line)
        
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
        self.preset_layout.addWidget(QLabel("Gaya Margin:"))
        self.preset_layout.addWidget(self.combo_margin_preset)
        self.preset_layout.addStretch()
        self.left_layout.addLayout(self.preset_layout)

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

        self.cover_input_layout = QHBoxLayout()
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

        self.cover_input_layout.addWidget(self.btn_select_cover)
        self.cover_input_layout.addWidget(self.lbl_cover_status)
        self.cover_input_layout.addWidget(self.btn_select_image)
        self.cover_input_layout.addWidget(self.lbl_image_status)
        self.cover_input_layout.addWidget(self.input_cover_title)
        self.left_layout.addLayout(self.cover_input_layout)

        self.options_layout = QVBoxLayout() 
        self.cb_toc = QCheckBox("Buat Daftar Isi Otomatis")
        self.cb_toc.setChecked(True)
        self.cb_page_numbers = QCheckBox("Tambahkan Nomor Halaman (Khusus Ekspor PDF)")
        self.cb_page_numbers.setChecked(True)
        self.options_layout.addWidget(self.cb_toc)
        self.options_layout.addWidget(self.cb_page_numbers)
        self.left_layout.addLayout(self.options_layout)

        self.hf_layout = QVBoxLayout()
        self.left_layout.addWidget(QLabel("Pengaturan Teks / Penulis (Khusus PDF):", objectName="sectionLabel"))
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
        self.hf_layout.addLayout(hf_input_layout)
        self.left_layout.addLayout(self.hf_layout)

        self.bab_style_layout = QVBoxLayout()
        self.left_layout.addWidget(QLabel("Pengaturan Visual Judul BAB (Jika Aktif):", objectName="sectionLabel"))
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
        self.bab_style_layout.addLayout(bab_inputs)
        self.left_layout.addLayout(self.bab_style_layout)

        self.materi_style_layout = QVBoxLayout()
        self.left_layout.addWidget(QLabel("Pengaturan Visual Judul File (Materi):", objectName="sectionLabel"))
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
        self.materi_style_layout.addLayout(materi_inputs)
        self.left_layout.addLayout(self.materi_style_layout)

        self.json_layout = QVBoxLayout()
        self.left_layout.addWidget(QLabel("Judul Kustom & Struktur BAB (Opsional):", objectName="sectionLabel"))
        self.cb_group_bab = QCheckBox("Tambahkan grup BAB di dalam Template JSON (Hirarki Bersarang)")
        json_btns_layout = QHBoxLayout()
        self.btn_export_json = QPushButton("1. Ekspor Template JSON")
        self.btn_load_json = QPushButton("2. Muat Judul JSON")
        json_btns_layout.addWidget(self.btn_export_json)
        json_btns_layout.addWidget(self.btn_load_json)
        json_btns_layout.addStretch()
        self.lbl_json_status = QLabel("Status: Default (Nama File)")
        self.json_layout.addWidget(self.cb_group_bab)
        self.json_layout.addLayout(json_btns_layout)
        self.json_layout.addWidget(self.lbl_json_status)
        self.left_layout.addLayout(self.json_layout)
        self.left_layout.addStretch() 

        # Signal connections
        self.btn_generate_html.clicked.connect(self.merge_to_html)
        self.btn_generate_pdf.clicked.connect(self.merge_to_pdf)
        self.combo_margin_preset.currentIndexChanged.connect(self.apply_margin_preset)
        self.radio_no_cover.toggled.connect(self.toggle_cover_options)
        self.radio_html_cover.toggled.connect(self.toggle_cover_options)
        self.radio_image_cover.toggled.connect(self.toggle_cover_options)
        self.radio_text_cover.toggled.connect(self.toggle_cover_options)
        self.btn_select_cover.clicked.connect(self.select_cover_file)
        self.btn_select_image.clicked.connect(self.select_cover_image)
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_add_files.clicked.connect(self.add_files)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_export_json.clicked.connect(self.export_json_template)
        self.btn_load_json.clicked.connect(self.load_json_titles)
        
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
            # Memberikan highlight tebal dan warna hijau sukses
            self.lbl_cover_status.setText(f"<b><font color='#27ae60'>✓ File: {os.path.basename(file)}</font></b>")

    def select_cover_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Pilih Foto/PDF Cover", "", "Images & PDF (*.png *.jpg *.jpeg *.bmp *.pdf)")
        if file:
            self.cover_image_path = file
            # Memberikan highlight tebal dan warna hijau sukses
            self.lbl_image_status.setText(f"<b><font color='#27ae60'>✓ File: {os.path.basename(file)}</font></b>")
    
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder")
        if folder:
            # Simpan base_dir jika baru pertama kali memilih
            if not self.base_dir:
                self.base_dir = folder
                
            all_files = os.listdir(folder)
            html_files = []
            for f in all_files:
                f_lower = f.lower()
                file_path = os.path.join(folder, f)
                
                # PERBAIKAN: Deteksi meta.json atau template_judul.json yang diekspor sebelumnya
                if f_lower in ["meta.json", "template_judul.json"]: 
                    self._process_json_file(file_path, show_message=False)
                elif f_lower == "cover.html":
                    self.radio_html_cover.setChecked(True)
                    self.cover_file_path = file_path
                    self.lbl_cover_status.setText(f"<b><font color='#27ae60'>✓ File: {f}</font></b>")
                elif f_lower.startswith("cover.") and f_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.pdf')):
                    self.radio_image_cover.setChecked(True)
                    self.cover_image_path = file_path
                    self.lbl_image_status.setText(f"<b><font color='#27ae60'>✓ File: {f}</font></b>")
                elif f_lower.endswith('.html') and f_lower != "cover.html":
                    html_files.append(file_path)

            html_files.sort()
            self.file_list.addItems(html_files)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Pilih File HTML", "", "HTML Files (*.html)")
        if files: 
            # Simpan base_dir dari folder file pertama jika baru pertama kali memilih
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
        # Mengembalikan teks status ke default
        self.lbl_json_status.setText("Status: Default (Nama File)")
        self.lbl_cover_status.setText("Belum ada file dipilih")
        self.lbl_image_status.setText("Belum ada file dipilih")
        self.cover_file_path = None
        self.cover_image_path = None
        self.base_dir = ""
        self.radio_no_cover.setChecked(True)

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

        # Gunakan base_dir jika ada, jika tidak, di direktori kerja saat ini
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
                self.input_cover_title.setText(judul)
                self.output_name.setText(judul) 
                if self.radio_no_cover.isChecked(): self.radio_text_cover.setChecked(True)
                
            data = data.get("struktur", data)
            is_nested = data and isinstance(next(iter(data.values())), dict)

            if is_nested:
                for bab_name, files_dict in data.items():
                    for file_name, file_title in files_dict.items():
                        self.custom_titles[file_name] = file_title
                        self.file_bab_mapping[file_name] = bab_name
            else:
                self.custom_titles = data

            # Memberikan highlight tebal berwarna biru/hijau penanda template aktif
            self.lbl_json_status.setText(f"<b><font color='#2980b9'>✓ Aktif: {os.path.basename(file_path)}</font></b>")
            if show_message: QMessageBox.information(self, "Berhasil", "Data judul berhasil dimuat!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def set_ui_enabled(self, enabled):
        self.btn_generate_html.setEnabled(enabled)
        self.btn_generate_pdf.setEnabled(enabled)
        self.btn_add_folder.setEnabled(enabled)
        self.btn_add_files.setEnabled(enabled)
        self.btn_delete.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)

    def _get_export_options(self, is_pdf):
        cover_type = "none"
        if self.radio_html_cover.isChecked(): cover_type = "html"
        elif self.radio_image_cover.isChecked(): cover_type = "image"
        elif self.radio_text_cover.isChecked(): cover_type = "text"

        return {
            "doc_title": self.input_cover_title.text().strip() or "Gabungan Materi",
            "is_pdf": is_pdf,
            "use_toc": self.cb_toc.isChecked(),
            "page_size": self.combo_size.currentText(),
            "margins": (self.spin_margin_top.value(), self.spin_margin_bottom.value(), self.spin_margin_left.value(), self.spin_margin_right.value()),
            "author_text": self.input_author.text().strip(),
            "hf_pos": self.combo_hf_pos.currentText(),
            "hf_align": self.combo_hf_align.currentText(),
            "use_page_numbers": self.cb_page_numbers.isChecked(),
            "cover_type": cover_type,
            "cover_file_path": self.cover_file_path,
            "cover_image_path": self.cover_image_path,
            "bab_style_mode": self.combo_bab_style.currentText(),
            "bab_font_size": self.spin_bab_size.value(),
            "materi_style_text": self.combo_materi_style.currentText(),
            "materi_font_size": self.spin_materi_size.value(),
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
            # Gabungkan dengan base_dir agar tersimpan di direktori folder terpilih
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
        # Gabungkan dengan base_dir agar tersimpan di direktori folder terpilih
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