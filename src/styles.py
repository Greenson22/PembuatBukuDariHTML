def get_modern_theme():
    return """
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