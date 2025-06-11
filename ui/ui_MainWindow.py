# -*- coding: utf-8 -*-

import os
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import (QCoreApplication, QMetaObject, Qt, QSize)
from PySide6.QtGui import QFont, QTextOption, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget, QMainWindow, QLabel,
    QPushButton, QListWidget, QTextEdit, QListWidgetItem,
    QLineEdit, QFrame, QSizePolicy, QMenu, QInputDialog, 
)
from ui.custom_text_input import ChatTextInput

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        
        # Window Size Management
        MainWindow.resize(1200, 800)
        MainWindow.setMinimumSize(QSize(800, 600))
        
        # Central Widget
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)

        # ===== FONT SETTINGS =====
        self.base_font = QFont()
        self.base_font.setFamily("Arial")  # Default font family
        self.base_font.setPointSize(12)     # Base font size
        
        # Button-specific font
        self.button_font = QFont(self.base_font)
        self.button_font.setPointSize(13)   # Slightly larger for buttons
        
        # List-specific font
        self.list_font = QFont(self.base_font)
        self.list_font.setPointSize(11)

        # Main Layout
        self.main_horizontal_layout = QHBoxLayout(self.centralwidget)
        self.main_horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self.main_horizontal_layout.setSpacing(0)

        # Image Preview
        self.imagePreviewLabel = QLabel()
        self.imagePreviewLabel.setVisible(False)
        self.imagePreviewLabel.setFixedSize(64, 64)
        self.imagePreviewLabel.setStyleSheet("""
            border-radius: 12px;
            border: 2px solid #00cc66;
            background: #f8f8f8;
        """)

        # ===== LEFT SIDEBAR =====
        self.sidebarWidget = QWidget()
        self.sidebarWidget.setObjectName(u"sidebarWidget")
        self.sidebarWidget.setMinimumWidth(250)
        self.sidebarWidget.setMaximumWidth(350)
        self.sidebarWidget.setStyleSheet("""
            background-color: #f0f0f0;
            border-right: 1px solid #d0d0d0;
        """)

        self.sidebar_layout = QVBoxLayout(self.sidebarWidget)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_layout.setSpacing(10)

        # New Chat Button
        self.newChatButton = QPushButton("New Chat")
        self.newChatButton.setFont(self.button_font)
        self.newChatButton.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #e0e0e0;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        self.sidebar_layout.addWidget(self.newChatButton)

        # Separator
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.sidebar_layout.addWidget(self.separator)

        # Chat History List
        self.listWidget = QListWidget()
        self.listWidget.setFont(self.list_font)
        self.listWidget.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:hover {
                background-color: #e8e8e8;
            }
        """)
        self.listWidget.addItems(["Chat 1", "Chat 2", "Chat 3"])
        self.sidebar_layout.addWidget(self.listWidget)

        # Hide Sidebar Button
        self.hideSidebarButton = QPushButton("Hide Sidebar")
        self.hideSidebarButton.setFont(self.button_font)
        self.hideSidebarButton.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #e0e0e0;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        self.hideSidebarButton.clicked.connect(self.toggle_sidebar)
        self.sidebar_layout.addWidget(self.hideSidebarButton, alignment=Qt.AlignBottom)

        # ===== MINI SIDEBAR =====
        self.miniSidebar = QWidget()
        self.miniSidebar.setMinimumWidth(50)
        self.miniSidebar.setMaximumWidth(50)
        self.miniSidebar.setStyleSheet("""
            background-color: #f0f0f0;
            border-right: 1px solid #d0d0d0;
        """)
        self.miniSidebar.setVisible(False)  # Hidden by default

        self.miniSidebarLayout = QVBoxLayout(self.miniSidebar)
        self.miniSidebarLayout.setContentsMargins(5, 5, 5, 5)
        self.miniSidebarLayout.setSpacing(5)

        # Show Sidebar Icon Button (icon only)
        self.sidebarToggleButton = QPushButton(">>")
        self.sidebarToggleButton.setFont(self.button_font)
        self.sidebarToggleButton.setFixedSize(40, 40)
        self.sidebarToggleButton.setToolTip("Show Sidebar")
        self.sidebarToggleButton.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        self.miniSidebarLayout.addStretch()  # Push everything up
        self.miniSidebarLayout.addWidget(self.sidebarToggleButton, alignment=Qt.AlignBottom)

        # ===== RIGHT CONTENT AREA =====
        self.right_content = QWidget()
        self.right_layout = QVBoxLayout(self.right_content)
        self.right_layout.setContentsMargins(10, 10, 10, 10)
        self.right_layout.setSpacing(10)

        self.chat_title_bar = QHBoxLayout()
        self.chat_title = QLabel("Welcome to FamousNSFW!")
        self.chat_title.setFont(QFont("Arial", 14, QFont.Bold))
        self.chat_title_bar.addWidget(self.chat_title)
        self.right_layout.addLayout(self.chat_title_bar)

        # Main Text Display
        self.plainText = QTextEdit()
        self.plainText.setReadOnly(True)
        self.plainText.setFont(self.base_font)
        self.plainText.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 10px;
                background: white;
            }
        """)
        self.plainText.setPlainText("Welcome to the chat!")
        self.right_layout.addWidget(self.plainText)

        # === VOICE INPUT BUTTON ===
        self.micOnButton = QtWidgets.QPushButton(self.centralwidget)
        self.micOnButton.setObjectName("micOnButton")
        self.micOnButton.setFixedSize(40, 40)
        self.micOnButton.setIcon(QtGui.QIcon(os.path.join("ui", "icons", "mic.png")))
        self.micOnButton.setIconSize(QtCore.QSize(24, 24))
        self.micOnButton.setStyleSheet("""
            QPushButton {
                background-color: #00cc66;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #00cc11;
            }
        """)
        # self.micOnButton.move(680, 500)  # 🔁 adjust based on your layout
        self.micOnButton.setVisible(True)

        # Mic OFF button
        self.micOffButton = QtWidgets.QPushButton(self.centralwidget)
        self.micOffButton.setObjectName("micOffButton")
        self.micOffButton.setFixedSize(40, 40)
        self.micOffButton.setIcon(QtGui.QIcon(os.path.join("ui", "icons", "mic_off.png")))
        self.micOffButton.setIconSize(QtCore.QSize(24, 24))
        self.micOffButton.setStyleSheet("""
            QPushButton {
                background-color: #cc0011;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #cc0033;
            }
        """)
        # self.micOffButton.move(680, 500)  # 🔁 same position as micOn
        self.micOffButton.setVisible(False)

        # === FILE UPLOAD BUTTON ===
        self.uploadButton = QPushButton()
        self.uploadButton.setFixedSize(40, 40)
        self.uploadButton.setToolTip("Upload Image")
        self.uploadButton.setIcon(QIcon.fromTheme("document-open"))
        self.uploadButton.setStyleSheet("""
            QPushButton {
                background-color: #00cc66;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #00cc11;
            }
        """)

        # === TEXT INPUT ===
        self.textInput = ChatTextInput()
        self.textInput.setFont(self.base_font)
        self.textInput.setPlaceholderText("Type your message...")
        self.textInput.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }
        """)

        # === SEND BUTTON ===
        self.sendButton = QPushButton()
        self.sendButton.setFixedSize(40, 40)
        self.sendButton.setToolTip("Send Message")
        self.sendButton.setIcon(QIcon.fromTheme("mail-send"))
        self.sendButton.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.statusLabel = QLabel("")
        self.retryButton = QPushButton("🔁 Retry")
        self.cancelButton = QPushButton("❌ Cancel")

        self.retryButton.setVisible(False)
        self.cancelButton.setVisible(False)

        # === INPUT BAR LAYOUT (cleaned) ===
        self.inputLayout = QHBoxLayout()
        self.inputLayout.setSpacing(6)

        # Mic & Upload
        self.inputLayout.addWidget(self.micOnButton)
        self.inputLayout.addWidget(self.micOffButton)
        self.inputLayout.addWidget(self.uploadButton)

        # Text input (stretchable)
        self.inputLayout.addWidget(self.textInput, stretch=1)

        # Send & controls
        self.inputLayout.addWidget(self.sendButton)
        self.inputLayout.addWidget(self.statusLabel)
        self.inputLayout.addWidget(self.retryButton)
        self.inputLayout.addWidget(self.cancelButton)

        # --- FIX: Create a vertical layout for input area ---
        self.input_area_layout = QVBoxLayout()
        self.input_area_layout.setSpacing(4)
        self.input_area_layout.addWidget(self.imagePreviewLabel)  # Image preview on top
        self.input_area_layout.addLayout(self.inputLayout)

        self.right_layout.addLayout(self.input_area_layout)  

        # Add to main layout
        self.main_horizontal_layout.addWidget(self.sidebarWidget)
        self.main_horizontal_layout.addWidget(self.miniSidebar)
        self.main_horizontal_layout.addWidget(self.right_content)

        # Set input focus
        self.textInput.setFocus()

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"FamousNSFW", None))

    def toggle_sidebar(self):
        if self.sidebarWidget.isVisible():
            self.sidebarWidget.hide()
            self.miniSidebar.setVisible(True)
        else:
            self.sidebarWidget.show()
            self.miniSidebar.setVisible(False)
    