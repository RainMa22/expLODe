from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import *
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
import os
from expLODe_config import get_config,write_config, check_version
from sexp import make_string, make_list, make_symbol


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
    class WorkflowWidget(QScrollArea):
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
            self.add(ExportStep())
        
        def add(self, widget:QWidget):
            self.center_widget.layout().addWidget(widget)

    class content_widget(QSplitter):
        def __init__(self):
            super().__init__(Qt.Orientation.Horizontal)
            self.workflows_widget = mainWidget.WorkflowWidget()
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
        self.id = hash(os.times().elapsed)
        # self.setObjectName("QStepWidget")
        # TODO: make the code below work
        self.setStyleSheet("QStepWidget{border: 1px solid black; border-radius: 1%;}")

class EmptyStepWidget(QStepWidget):
    def __init__(self, compatible_classes:list, onconnect):
        super().__init__()
        self.compatible_classes = compatible_classes
        self.btn = QPushButton("+")
        self.selection_menu = QMenu()
        grid_layout = QGridLayout(self)
        grid_layout.setContentsMargins(0,0,0,0)
        self.setLayout(grid_layout)
        for compatible_class in compatible_classes:
            def on_trigger(cl):
                # this is done because closures are weird in Python
                return lambda: onconnect(cl)
            self.selection_menu.addAction(
                str(compatible_class)).triggered.connect(
                    on_trigger(compatible_class))
        self.btn.setMenu(self.selection_menu)
        # self.btn.clicked.connect(lambda: self.btn.showMenu)
        # self.selection_menu.show()
        grid_layout.addWidget(self.btn,0,4,Qt.AlignmentFlag.AlignRight)

class ChooseFileStep(QStepWidget):
    def __init__(self):
        super().__init__()
        glayout = QGridLayout()
        glayout.setContentsMargins(0,0,0,0)
        self.setLayout(glayout)
        self.fileLabels = QLabel()
        self.fileLabels.setWordWrap(True)
        choose_prompt = "Choose File(s)"
        choose_label:QLabel = QLabel(choose_prompt)
        choose_btn: QPushButton = QPushButton("...")
        glayout.addWidget(choose_label,0,0)
        glayout.addWidget(choose_btn,0,4)
        choose_btn.clicked.connect(self.chooseFBX)
        
        glayout.addWidget(self.fileLabels,1,0,1,5)
        self.updateFileList([])
        self.substep = None
        self.clear_substep()
        
    def set_substep(self,substep:QStepWidget):
        prev = self.substep
        self.substep = substep
        glayout: QGridLayout = self.layout()
        if(prev is not None):
            glayout.removeWidget(prev)
            prev.deleteLater()
        if(substep is not None):
            if hasattr(substep, "removal_action"):
                substep.removal_action = lambda : self.clear_substep()
            self.layout().addWidget(substep,2,1,1,4)
        return prev
    
    def clear_substep(self):
        return self.set_substep(EmptyStepWidget(GENERAL_CLASSES,lambda step: self.set_substep(step())))
    
    def __str__(self):
        base_string = f"(def inFiles {repr(self.inFiles)})"
        if self.substep is None:
            return base_string
        return f"""
        {base_string}
        (def (fn-for-inFile{self.id} inFile) {str(self.substep)})    
        (def (fn-for-inFiles{self.id} inFiles)
            (if (empty? inFiles)
                '()
                (cons (fn-for-inFile{self.id} (first inFiles)
                    (fn-for-inFiles{self.id} (rest inFiles))))))
        (fn-for-inFiles{self.id} inFiles)
        """
    
    def updateFileList(self, files):
        self.inFiles = make_list(map(lambda inFile: make_string(inFile), files))
        basenames = list(map(lambda inFile: os.path.basename(inFile), files))
        print(basenames, len(basenames))
        if(len(basenames) == 0):
            self.fileLabels.setText(f'3D Model Input(s) Not Set...')
        else:
            self.fileLabels.setText(f'For Each InFile in {basenames} do:')
    
    @QtCore.Slot()
    def chooseFBX(self):
        file_names,_ = QFileDialog.getOpenFileNames(self, 
                                                 "fbx models",
                                                 ".",
                                                 "fbx models(*.fbx)")
        self.updateFileList(file_names)

class WfFunctionStep(QStepWidget):
    def __init__(self, wf_fun_name, wf_fun_params):
        super().__init__()
        self.varname = wf_fun_name
        self.target = "inFile"
        self.wf_fun_name = wf_fun_name
        self.wf_fun_params = wf_fun_params
        self.objs = None
        self.next = None
        layout = QGridLayout(self)
        self.setLayout(layout)
        self.layout().setContentsMargins(0,0,0,0)
        label = QLabel(f"{wf_fun_name}")
        as_var_label = QLabel(" as variable: ")
        self.rmbtn = QPushButton("-")
        self.varname_field = QLineEdit()
        self.target_field = QLineEdit()
        layout.addWidget(label, 0,0)
        layout.addWidget(self.target_field,0,1)
        layout.addWidget(as_var_label, 0, 2)
        layout.addWidget(self.varname_field,0,3)
        self.varname_field.textChanged.connect(self.on_varname_change)
        self.target_field.textChanged.connect(self.on_target_name_change)
        self.varname_field.setText(wf_fun_name)
        self.target_field.setText("InFile")
        layout.addWidget(self.rmbtn, 0,4,Qt.AlignmentFlag.AlignRight)
        self.removal_action = lambda: None
        self.rmbtn.clicked.connect(lambda: self.get_removal_action()()) # abusing closures
        self.clear_next()
    
    @QtCore.Slot()
    def on_target_name_change(self):
        self.target = self.target_field.text()
    @QtCore.Slot()
    def on_varname_change(self):
        self.varname = self.varname_field.text()
    def get_removal_action(self):
        return self.removal_action
    def set_next(self, next:QStepWidget):
        prev =self.next
        if(prev is not None):
            self.layout().removeWidget(prev)
            prev.deleteLater()
        if(next is not None):
            glayout:QGridLayout = self.layout()
            glayout.addWidget(next,1,0,1,5)
            if(hasattr(next, "removal_action")):
                next.removal_action = lambda: self.clear_next()
            # next.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.next = next
        return prev
    
    def clear_next(self):
        return self.set_next(EmptyStepWidget(GENERAL_CLASSES,lambda step: self.set_next(step())))
    
    def __str__(self):
        return f"""
        (with ({self.varname} ({self.wf_fun_name} 
                                {" ".join(self.wf_fun_params)}
                                {repr(make_list(self.objs)) if self.objs is not None else "ALL"}))
            {self.varname if self.next is None else str(self.next)})
        """
    
class UvUnwrapStep(WfFunctionStep):
    def __init__(self):
        super().__init__("uv-unwrap", [])

class PlanarStep(WfFunctionStep):
    def __init__(self, deg:int|float = 10):
        super().__init__("Planar", [make_string(f"(deg->rad {deg})")])

class UnsubdivStep(WfFunctionStep):
    def __init__(self, iterations:int|float = 10):
        super().__init__("unsubdiv", [make_string(str(iterations))])

class DecimateStep(WfFunctionStep):
    def __init__(self, ratio:int|float = 1.0):
        super().__init__("Decimate", [make_string(str(ratio))])

class ExportStep(QStepWidget):
    def __init__(self):
        super().__init__()
        glayout = QGridLayout()
        self.setLayout(glayout)
        "export variables: ... as file ..."
        export_label = QLabel("Export Variable(s): ")
        self.variable_field = QLineEdit()
        as_label = QLabel("as File: ")
        self.export_to = "./out.fbx"
        self.file_choose_button = QPushButton(self.export_to)
        self.file_choose_button.clicked.connect(self.chooseFile)
        export_btn = QPushButton("Export")
        glayout.addWidget(export_label, 0,0)
        glayout.addWidget(self.variable_field,0,1)
        glayout.addWidget(as_label, 0 ,2)
        glayout.addWidget(self.file_choose_button,1,3)
        glayout.addWidget(export_btn, 1,3)
        self.export_signal = export_btn.clicked
    
    @QtCore.Slot()
    def chooseFile(self):
        file, _ = QFileDialog.getSaveFileName(None, 
                                              "Choose an File to save to",
                                              os.path.expanduser("~"),
                                              "FBX files (*.fbx)")
        self.export_to = os.path.relpath(file)
        self.file_choose_button.setText(self.export_to)

    def __str__(self):
        variables = self.variable_field.text().split(",")
        variables = make_list(map(lambda v: make_string(v.strip()),variables))
        return f"(export FBX {make_string(os.path.abspath(self.export_to))} {repr(variables)})"

GENERAL_CLASSES = [UvUnwrapStep,
                    PlanarStep,
                    UnsubdivStep,
                    DecimateStep]

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