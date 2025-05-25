# -*- coding: utf-8 -*-

from PySide6.QtCore import (QCoreApplication, QMetaObject, Qt, QSize)
from PySide6.QtGui import QFont, QTextOption
from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget, QMainWindow, QLabel,
    QPushButton, QListWidget, QPlainTextEdit, QListWidgetItem,
    QLineEdit, QFrame, QSizePolicy, QMenu, QInputDialog
)

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

        # ===== RIGHT CONTENT AREA =====
        self.right_content = QWidget()
        self.right_layout = QVBoxLayout(self.right_content)
        self.right_layout.setContentsMargins(10, 10, 10, 10)
        self.right_layout.setSpacing(10)

        self.chat_title_bar = QHBoxLayout()
        self.chat_title = QLabel("No Chat Selected")
        self.chat_title.setFont(QFont("Arial", 14, QFont.Bold))
        self.chat_title_bar.addWidget(self.chat_title)
        self.right_layout.addLayout(self.chat_title_bar)

        # Main Text Display
        self.plainText = QPlainTextEdit()
        self.plainText.setFont(self.base_font)
        self.plainText.setReadOnly(True)
        self.plainText.setStyleSheet("""
            QPlainTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 10px;
                background: white;
            }
        """)
        self.plainText.setPlainText("Welcome to the chat!")
        self.right_layout.addWidget(self.plainText)

        # Input Area
        self.inputLayout = QHBoxLayout()
        
        # Show Sidebar Button (hidden initially)
        self.showSidebarButton = QPushButton("Show")
        self.showSidebarButton.setFont(self.button_font)
        self.showSidebarButton.setFixedSize(100, 40)
        self.showSidebarButton.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        self.showSidebarButton.setVisible(False)
        self.showSidebarButton.clicked.connect(self.toggle_sidebar)
        
        # Text Input
        self.textInput = QLineEdit()
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
        
        # Send Button
        self.sendButton = QPushButton("Send")
        self.sendButton.setFont(self.button_font)
        self.sendButton.setFixedSize(100, 40)
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
        
        self.inputLayout.addWidget(self.showSidebarButton)
        self.inputLayout.addWidget(self.textInput)
        self.inputLayout.addWidget(self.sendButton)
        self.right_layout.addLayout(self.inputLayout)

        # Add to main layout
        self.main_horizontal_layout.addWidget(self.sidebarWidget)
        self.main_horizontal_layout.addWidget(self.right_content)

        # Enable word wrap for plain text
        self.plainText.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.plainText.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)

        # Set input focus
        self.textInput.setFocus()

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Chat Application", None))

    def toggle_sidebar(self):
        if self.sidebarWidget.isVisible():
            self.sidebarWidget.hide()
            self.hideSidebarButton.setVisible(False)
            self.showSidebarButton.setVisible(True)
        else:
            self.sidebarWidget.show()
            self.hideSidebarButton.setVisible(True)
            self.showSidebarButton.setVisible(False)
    