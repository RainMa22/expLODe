from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import *
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
import os
from expLODe_config import get_config,write_config, check_version

class menubar(QMenuBar):
    class fileMenu(QMenu):
        def __init__(self):
            super().__init__("File")
            options = {
                "Open": lambda : (),
                "Save": lambda: (),
                "Specify Blender Installation": menubar.findAndSetBlender
            }

            for k,v in options.items():
                self.addAction(k).triggered.connect(v)

    @QtCore.Slot()
    def findAndSetBlender():
        config = get_config()
        config["expLODe.blenderCmd"],_ = QFileDialog.getOpenFileName(None,"Locate Blender",
                                                                     os.path.expanduser("~"),"All file (*)")
        write_config(config)
        mBox = QMessageBox()
        if(check_version()):
            mBox.setText("Blender Version Satisfied")
            mBox.setIcon(QMessageBox.Icon.Information)
        else:
            mBox.setText("Invalid Blender Executable")
            mBox.setIcon(QMessageBox.Icon.Critical)
        mBox.exec()


    def __init__(self):
        super().__init__()
        self.addMenu(menubar.fileMenu())

class mainWidget(QWidget):
    class listOfWorkflow_widget(QScrollArea):
        def __init__(self):
            super().__init__()
            self.setWidgetResizable(True)
            self.center_widget = QWidget()
            layout = QVBoxLayout(self.center_widget)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.center_widget.setLayout(layout)
            self.setWidget(self.center_widget)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.add(ChooseFileStep())
        
        def add(self, widget:QWidget):
            self.center_widget.layout().addWidget(widget)

    class content_widget(QSplitter):
        def __init__(self):
            super().__init__(Qt.Orientation.Horizontal)
            self.workflows_widget = mainWidget.listOfWorkflow_widget()
            self.addWidget(self.workflows_widget)
            self.addWidget(QLabel("Hello"))
            
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout(self))
        self.content_widget = mainWidget.content_widget()
        self.layout().addWidget(self.content_widget)

    def get_workflows_widget(self):
        return self.content_widget.workdlow_widget


class QStepWidget(QWidget):
    def __init__(self):
        super().__init__()
        # self.setObjectName("QStepWidget")
        # self.setStyleSheet("QStepWidget{border: 1px solid black; border-radius: 1%;}")


class ChooseFileStep(QStepWidget):
    def __init__(self):
        super().__init__()
        self.inFiles = []
        self.setLayout(QVBoxLayout())
        self.fileLabels = QLabel()
        choose_file_widget = QWidget()
        choose_file_widget.setLayout(QHBoxLayout())
        choose_prompt = "Choose File(s)"
        choose_label:QLabel = QLabel(choose_prompt)
        choose_btn: QPushButton = QPushButton("...")
        choose_file_widget.layout().addWidget(choose_label)
        choose_file_widget.layout().addWidget(choose_btn)
        choose_btn.clicked.connect(self.chooseFBX)
        self.layout().addWidget(choose_file_widget)
        self.layout().addWidget(self.fileLabels)
        self.fileLabels.setText(",".join(self.inFiles))

    
    @QtCore.Slot()
    def chooseFBX(self):
        file_names,_ = QFileDialog.getOpenFileNames(self, 
                                                 "fbx models",
                                                 ".",
                                                 "fbx models(*.fbx)")
        print(file_names)
        self.inFiles = file_names
        self.fileLabels.setText(",".join(self.inFiles))
    




class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("expLODe")
        self.main_widget = mainWidget()
        self.setCentralWidget(self.main_widget)
        self.setMenuBar(menubar())
        self.resize(800,600)
    def get_workflows_widget(self):
        return self.main_widget.get_workflows_widget()

class expLODe_gui_app(QApplication):
    def __init__(self):
        super().__init__([])
        self.window = mainWindow()
        self.config = get_config()
        if(self.config.get("expLODe.blenderCmd", "") == "" or not check_version()):
            QMessageBox.information(None, "Notification", "Blender Not Detected! Please Select a Valid Blender >=4.2, <5 Installation.")
            menubar.findAndSetBlender()
    def exec(self):
        self.window.show()
        return super().exec()