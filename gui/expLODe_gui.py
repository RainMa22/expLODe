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

class mainWidget(QFrame):
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
            self.fileStep = ChooseFileStep()
            self.exportStep = ExportStep()
            self.exportStep.export_signal.connect(self.export)
            self.code_signal = self.exportStep.show_code_signal
            self.add(self.fileStep)
            self.add(self.exportStep)
        
        @QtCore.Slot()
        def export(self):
            script = str(self)
            import time
            from expLODe import open_blender_python
            with open_blender_python("features_wf.py") as proc:
                time.sleep(1.)
                proc_in = proc.stdin
                for line in script.splitlines():
                    proc_in.write(line.encode())  
                    proc_in.write("\n".encode())
                    print(line)
                    proc_in.flush()
                    time.sleep(0.1)
                proc_in.close()
            QMessageBox.information(None,"Export Completed","Export completed")
            
            
        
        def add(self, widget:QWidget):
            self.center_widget.layout().addWidget(widget)
        
        def __str__(self):
            return f"""
{str(self.fileStep).format(exportStep = str(self.exportStep))}
            """

    class content_widget(QSplitter):
        def __init__(self):
            super().__init__(Qt.Orientation.Horizontal)
            self.workflows_widget = mainWidget.WorkflowWidget()
            self.code_indicator = QLabel("")
            self.code_indicator.setFont("Courier")
            self.code_indicator.setStyleSheet("background: black; color: white")
            self.addWidget(self.workflows_widget)
            self.addWidget(self.code_indicator)
            self.workflows_widget.code_signal.connect(self.show_code)

        def show_code(self):
            self.code_indicator.setText((str(self.workflows_widget)))
            self.code_indicator.setParent(None)
            self.addWidget(self.code_indicator)
            
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout(self))
        self.content_widget = mainWidget.content_widget()
        self.layout().addWidget(self.content_widget)

    def get_workflows_widget(self):
        return self.content_widget.workdlow_widget


class QStepWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.id = hash(os.times().elapsed)
        # self.setObjectName("QStepWidget")
        self.setProperty("widgetclass", "QStepWidget")
        self.setAutoFillBackground(True)
        self.setStyleSheet("""
                           QStepWidget{
                            border: 1px solid black; 
                            border-radius: 20%;
                            background-color: transparent;
                           }""")
    # def paintEvent(self, event):
    #     super().paintEvent(event)
    #     painter = QtGui.QPainter(self)
    #     painter.setPen(QtGui.QPen(Qt.black, 1))
    #     painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

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
        self.setStyleSheet(
            """
            EmptyStepWidget{
                border: 0px;
                border-radius: 0px;
            }
            """
        )
        grid_layout.addWidget(self.btn,0,4,Qt.AlignmentFlag.AlignRight)

class ChooseFileStep(QStepWidget):
    def __init__(self):
        super().__init__()
        glayout = QGridLayout()
        glayout.setContentsMargins(10,10,10,10)
        # print(glayout.contentsMargins())
        self.setLayout(glayout)
        self.fileLabels = QLabel()
        self.fileLabels.setWordWrap(True)
        choose_prompt = "Choose File(s)"
        choose_label:QLabel = QLabel(choose_prompt)
        choose_btn: QPushButton = QPushButton("Choose File")
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
        return self.set_substep(ImportStep())
    
    def __str__(self):
        base_string = f"(def inFiles {repr(self.inFiles)})"
        if self.substep is None:
            return base_string
        return f"""
{base_string}
(def (fn-for-inFile inFile) {"{exportStep}" if type(self.substep) is EmptyStepWidget else str(self.substep)})    
(def (fn-for-inFiles inFiles)
    (if (empty? inFiles)
        '()
        (cons (fn-for-inFile (first inFiles))
            (fn-for-inFiles (rest inFiles)))))
(fn-for-inFiles inFiles)
        """
    
    def updateFileList(self, files):
        self.inFiles = make_list(map(lambda inFile: (make_string(inFile)), files))
        basenames = list(map(lambda inFile: os.path.basename(inFile), files))
        # print(basenames, len(basenames))
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
    def __init__(self, wf_fun_name, wf_fun_params,max_row_idx = 0, target = "og"):
        super().__init__()
        self.max_row_idx = max_row_idx
        self.varname = wf_fun_name+"ed"
        self.target = target
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
        self.varname_field.setText(self.varname)
        self.target_field.setText(self.target)
        layout.addWidget(self.rmbtn, 0,4,Qt.AlignmentFlag.AlignRight)
        self.removal_action = lambda: None
        self.rmbtn.clicked.connect(lambda: self.get_removal_action()()) # abusing closures
        self.setStyleSheet(
            """
            WfFunctionStep{
                border: 0px;
                border-radius: 0px;
            }
            """
        )
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
            glayout.addWidget(next,self.max_row_idx+1,0,1,5)
            if(hasattr(next, "target_field")):
                next.target_field.setText(self.varname)
                next.target_field.textChanged.emit(None)
            if(hasattr(next, "removal_action")):
                next.removal_action = lambda: self.clear_next()
            # next.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.next = next
        return prev
    
    def clear_next(self):
        return self.set_next(EmptyStepWidget(GENERAL_CLASSES,lambda step: self.set_next(step())))
    
    def __str__(self):
        fun_name = self.wf_fun_name.lower()
        return f"""
(with 
    ({self.varname} 
        ({fun_name} {" ".join(self.wf_fun_params)} {self.target if self.target is not None else "ALL"})) 
    {"{exportStep}" if type(self.next) is EmptyStepWidget else str(self.next)})
"""

class ImportStep(WfFunctionStep):
    def __init__(self):
        super().__init__("import", ["FBX"])
        self.varname_field.setText("og")
        self.target_field.setText("inFile")
        self.target_field.textChanged.emit(None)
        self.varname_field.textChanged.emit(None)

class UvUnwrapStep(WfFunctionStep):
    def __init__(self):
        super().__init__("uv-unwrap", [])


class PlanarStep(WfFunctionStep):
    @QtCore.Slot()
    def on_deg_change(self):
        if(self.deg_field.value()==0):
            self.deg_field.setValue(1)
        self.deg_indicator.setText(f"degree: {self.deg_field.value()/100.0:.02f}")
        self.deg = self.deg_field.value()/100.0
        self.wf_fun_params = [str(f"(deg->rad {self.deg})")]

    def __init__(self, deg:int|float = 10):
        super().__init__("Planar", [str(f"(deg->rad {deg})")],1)
        glayout: QGridLayout = self.layout()
        self.deg_indicator = QLabel()
        self.deg_field = QSlider(Qt.Orientation.Horizontal)
        self.deg_field.setRange(1,36000)
        self.deg_field.valueChanged.connect(self.on_deg_change)
        self.deg_field.setValue(deg*100.0)
        self.on_deg_change()
        glayout.addWidget(self.deg_indicator,1,0)
        glayout.addWidget(self.deg_field,1,1,1,3)
        self.clear_next()
        

class UnsubdivStep(WfFunctionStep):
    def __init__(self, iterations:int = 10):
        super().__init__("Unsubdiv", [make_string(str(iterations))],1)
        glayout: QGridLayout = self.layout()
        self.iteration_indicator = QLabel()
        self.iteration_field = QSlider(Qt.Orientation.Horizontal)
        self.iteration_field.setValue(iterations)
        self.iteration_field.setRange(1,100)
        self.iteration_field.valueChanged.connect(self.iteration_changed)
        self.iteration_changed()
        glayout.addWidget(self.iteration_indicator, 1,0)
        glayout.addWidget(self.iteration_field, 1,1,1,3)
    
    @QtCore.Slot()
    def iteration_changed(self):
        self.iteration_indicator.setText(f"iterations: {self.iteration_field.value()}")
        self.iterations = self.iteration_field.value()
        self.wf_fun_params = [make_string(str(self.iterations))]


class DecimateStep(WfFunctionStep):
    def __init__(self, ratio:int|float = 1.0):
        super().__init__("Decimate", [make_string(str(ratio))],1)
        glayout: QGridLayout = self.layout()
        self.ratio_indicator = QLabel()
        self.ratio_field = QSlider(Qt.Orientation.Horizontal)
        self.ratio_field.setRange(1,100)
        self.ratio_field.setValue(ratio*100.0)
        self.ratio_field.valueChanged.connect(self.iteration_changed)
        self.iteration_changed()
        glayout.addWidget(self.ratio_indicator, 1,0)
        glayout.addWidget(self.ratio_field, 1,1,1,3)
    
    @QtCore.Slot()
    def iteration_changed(self):
        self.ratio_indicator.setText(f"ratio: {self.ratio_field.value()/100.0}")
        self.ratio = self.ratio_field.value()/100.0
        self.wf_fun_params = [make_string(str(self.ratio))]

class ExportStep(QStepWidget):
    def __init__(self, targets=["og"].copy(),suffix="out"):
        super().__init__()
        glayout = QGridLayout()
        self.setLayout(glayout)
        "export variables: ... as file ..."
        export_label = QLabel("Export Variable(s): ")
        self.targets_field = QLineEdit(text=", ".join(targets))
        as_label = QLabel("at Folder: ")
        self.export_to = "./"
        self.file_choose_button = QPushButton(os.path.relpath(self.export_to))
        self.file_choose_button.clicked.connect(self.chooseFolder)
        self.suffix_label = QLabel("With suffix: ")
        self.suffix_field = QLineEdit(text = suffix)
        self.extension_label = QLabel(".fbx")
        show_code_btn = QPushButton("Show Emitted Code")
        export_btn = QPushButton("Export")
        glayout.addWidget(export_label, 0,0)
        glayout.addWidget(self.targets_field,0,1,1,2)
        glayout.addWidget(as_label, 0 ,3)
        glayout.addWidget(self.file_choose_button,0,3)
        glayout.addWidget(self.suffix_label,1,0)
        glayout.addWidget(self.suffix_field,1,1, 1, 2)
        glayout.addWidget(self.extension_label, 1, 3)
        glayout.addWidget(show_code_btn, 2,2)
        glayout.addWidget(export_btn, 2,3)
        self.export_signal = export_btn.clicked
        self.show_code_signal = show_code_btn.clicked
    
    @QtCore.Slot()
    def chooseFolder(self):
        folder = QFileDialog.getExistingDirectory(None, 
                                              "Choose an File to save to",
                                              self.export_to)
        
        self.export_to = os.path.abspath(folder)
        self.file_choose_button.setText(os.path.relpath(self.export_to))

    def __str__(self):
        targets = self.targets_field.text().split(",")
        if(len(targets) == 1):
            targets = targets[0]        
        else:
            targets = "(+ " + " ".join(map(lambda v: v.strip(),targets)) + ")"

        outFile = f"""
(+ {repr(make_string(self.export_to))} 
    (filepath-filenameNoExt inFile) 
    {repr(make_string(self.suffix_field.text()+".fbx"))})"""
        return f"(export FBX {make_string(outFile)} {str(targets)})"

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
        self.resize(1920,1080)
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