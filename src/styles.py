def get_modern_theme():
    return """
        /* Main Application Background */
        QMainWindow, QScrollArea, QWidget#mainContainer { 
            background-color: #f0f2f5; 
        }
        
        /* Top Banner */
        QFrame#topBanner { 
            background-color: #293b5a; 
        }
        QLabel#appTitle { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            font-size: 22px; 
            font-weight: bold; 
            color: white; 
            padding: 10px;
        }
        
        /* Card Containers */
        QFrame[class="Card"] { 
            background-color: white; 
            border: 1px solid #e0e0e0; 
            border-radius: 8px; 
        }
        
        /* Card Titles */
        QLabel[class="CardTitle"] { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            font-size: 16px; 
            font-weight: bold; 
            color: #000000; 
            margin-bottom: 5px;
        }
        QLabel[class="StatusLabel"] {
            font-family: 'Segoe UI', Arial, sans-serif; 
            font-size: 14px; 
            color: #2c3e50; 
        }
        
        /* Input Fields */
        QLineEdit {
            padding: 10px 15px; 
            border: 1px solid #bce0fd; 
            border-radius: 6px;
            font-family: 'Segoe UI', Arial, sans-serif; 
            font-size: 14px;
            background-color: white; 
            color: #2d3436;
        }
        QLineEdit:focus { border: 1px solid #1976D2; }
        
        /* Standard Buttons */
        QPushButton {
            border: none; 
            border-radius: 6px; 
            padding: 12px 15px;
            font-family: 'Segoe UI', Arial, sans-serif; 
            font-size: 14px; 
            font-weight: bold; 
            color: white;
        }
        
        QPushButton#btnBlue { background-color: #1976D2; }
        QPushButton#btnBlue:hover { background-color: #1565C0; }
        
        QPushButton#btnGreen { background-color: #4CAF50; }
        QPushButton#btnGreen:hover { background-color: #43A047; }
        
        QPushButton#btnPurple { background-color: #7E57C2; }
        QPushButton#btnPurple:hover { background-color: #673AB7; }
        
        QPushButton#btnDarkGray { background-color: #607D8B; }
        QPushButton#btnDarkGray:hover { background-color: #546E7A; }
        
        QPushButton#btnRed { background-color: #E53935; }
        QPushButton#btnRed:hover { background-color: #D32F2F; }
        
        QPushButton#btnGray { background-color: #78909C; }
        QPushButton#btnGray:hover { background-color: #607D8B; }
        
        /* Dashed Dropzone Buttons */
        QPushButton[class="DashedBox"] {
            background-color: #f8f9fa;
            border: 1px dashed #b2bec3;
            border-radius: 6px;
            color: #2d3436;
            font-weight: normal;
            font-size: 14px;
            padding: 20px;
            text-align: center;
        }
        QPushButton[class="DashedBox"]:hover { 
            background-color: #e9ecef; 
            border-color: #636e72; 
        }
        
        /* List Widget */
        QListWidget {
            background-color: white; 
            border: 1px solid #dcdde1; 
            border-radius: 6px;
            padding: 5px; 
            font-family: 'Segoe UI', Arial, sans-serif; 
            font-size: 14px; 
            color: #2d3436;
        }
        QListWidget::item { padding: 10px; border-bottom: 1px solid #f1f2f6; }
        QListWidget::item:selected { background-color: #e8f4fd; color: #1976D2; border-radius: 4px; }
        
        /* Checkbox as Toggle */
        QCheckBox { font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; color: #2d3436; }
        QCheckBox::indicator { width: 45px; height: 25px; }
        
        /* Progress Bar */
        QProgressBar { 
            border: 1px solid #dcdde1; 
            border-radius: 6px; 
            text-align: center; 
            background-color: white; 
            color: #2c3e50; 
            font-weight: bold; 
            height: 18px; 
        }
        QProgressBar::chunk { background-color: #3498db; border-radius: 5px; }
    """