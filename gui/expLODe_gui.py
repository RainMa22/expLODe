from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import *
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
import os
from persistence.expLODe_config import get_config,write_config, check_version
from core.sexp import make_string, make_list, make_symbol,sexp
from globals import expLODe_root as proj_root

class StepsPreset:
    def __init__(self):
        self.import_step = None
        self.choose_file_step = None
        self.additional_steps = []
        self.export_step = None


class FileMenu(QMenu):
    open_signal = QtCore.Signal()
    save_signal = QtCore.Signal()
    def __init__(self):
        super().__init__("File")
        options = {
            "Open": lambda : self.open_signal.emit(),
            "Save": lambda: self.save_signal.emit(),
            "Specify Blender Installation": MenuBar.findAndSetBlender
        }

        for k,v in options.items():
            self.addAction(k).triggered.connect(v)
            
class MenuBar(QMenuBar):


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
        self.fileMenu = FileMenu()
        self.addMenu(self.fileMenu)
        self.open_signal = self.fileMenu.open_signal
        self.save_signal = self.fileMenu.save_signal

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
    
    def apply_preset(self, preset: StepsPreset):
        self.fileStep.apply_preset(preset)
        self.exportStep.apply_preset(preset)

    @QtCore.Slot()
    def export(self):
        if(len(self.fileStep.inFiles) == 0):
            QMessageBox.warning(None,"WARNING","No Input File Specified! \n" \
                                "Please Specify at least 1 Input File")
            return
        script = str(self)
        import time
        from bio.blenderio import open_blender_python
        from persistence.expLODe_config import get_config
        blendercmd = get_config().get("expLODe.blenderCmd")
        features_wf_path = os.path.join(proj_root, "core/features_wf.py")
        with open_blender_python(blendercmd, features_wf_path) as proc:
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

class ContentWidget(QSplitter):
    def __init__(self):
        super().__init__(Qt.Orientation.Horizontal)
        self.workflows_widget = WorkflowWidget()
        self.code_indicator = QLabel("")
        self.code_indicator.setFont("Courier")
        self.code_indicator.setProperty("type", "code")

        self.addWidget(self.workflows_widget)
        self.addWidget(self.code_indicator)
        self.workflows_widget.code_signal.connect(self.show_code)

    def get_code(self):
        return str(self.workflows_widget)
    
    def apply_preset(self, preset:StepsPreset, show_code=False):
        self.workflows_widget.apply_preset(preset)
        if(show_code):
            self.show_code()
    
    def show_code(self):
        self.code_indicator.setText(self.get_code())
        self.code_indicator.setParent(None)
        self.addWidget(self.code_indicator)

class MainWidget(QFrame):
                
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout(self))
        self.ContentWidget = ContentWidget()
        self.layout().addWidget(self.ContentWidget)
        self.get_code = self.ContentWidget.get_code

    def apply_preset(self, preset:StepsPreset, show_code=False):
        self.ContentWidget.apply_preset(preset, show_code = show_code)

    def get_workflows_widget(self):
        return self.ContentWidget.workdlow_widget


class QStepWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.id = hash(os.times().elapsed)
        # self.setObjectName("QStepWidget")
        self.setProperty("widgetclass", "QStepWidget")
        self.setAutoFillBackground(True)
    
    def apply_preset(self, d_struct:StepsPreset):
        pass

class EmptyStepWidget(QStepWidget):
    def __init__(self, compatible_classes:list, onconnect):
        super().__init__()
        self.compatible_classes = compatible_classes
        self.btn = QPushButton("+")
        self.selection_menu = QMenu()
        grid_layout = QGridLayout(self)
        grid_layout.setContentsMargins(0,0,0,0)
        self.setLayout(grid_layout)
        for name, compatible_class in compatible_classes:
            def on_trigger(cl):
                # this is done because closures are weird in Python
                return lambda: onconnect(cl)
            self.selection_menu.addAction(
                name).triggered.connect(
                    on_trigger(compatible_class))
        self.btn.setMenu(self.selection_menu)
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
    
    def apply_preset(self,d_struct: StepsPreset):
        super().apply_preset(d_struct)
        self.copy_from(d_struct.choose_file_step)
        if self.substep is not None:
            self.substep.apply_preset(d_struct)

    def copy_from(self, cfs):
        self.updateFileList(cfs.inFiles)
        
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
            self.fileLabels.setText(f'<h1><b>WARNING: 3D Model Input(s) Not Set!</b></h1>')
            self.fileLabels.setStyleSheet("color:red")
        else:
            self.fileLabels.setText(f'For Each InFile in {basenames} do:')
            self.fileLabels.setStyleSheet("color:black")
    
    @QtCore.Slot()
    def chooseFBX(self):
        file_names,_ = QFileDialog.getOpenFileNames(self, 
                                                 "fbx models",
                                                 ".",
                                                 "fbx models(*.fbx)")
        self.updateFileList(file_names)

class FunctionStep(QStepWidget):
    def __init__(self, wf_fun_name, wf_fun_params,formal_name:str|None = None,max_row_idx = 0, target = "og"):
        super().__init__()
        self.max_row_idx = max_row_idx
        self.varname = wf_fun_name+"ed"
        self.target = target
        self.formal_name = wf_fun_name if (formal_name is None) else formal_name
        self.wf_fun_name = wf_fun_name
        self.wf_fun_params = wf_fun_params
        self.objs = None
        self.next = None
        layout = QGridLayout(self)
        self.setLayout(layout)
        self.layout().setContentsMargins(0,0,0,0)
        label = QLabel(f"{self.formal_name}")
        as_var_label = QLabel(" as variable: ")
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
        self.clear_next()
    
    def set_varname(self,varname):
        self.varname_field.setText(varname)
        self.varname_field.textChanged.emit(None)
    
    def set_target(self, target):
        self.target_field.setText(target)
        self.target_field.textChanged.emit(None)

    @QtCore.Slot()
    def on_target_name_change(self):
        self.target = self.target_field.text()
    
    @QtCore.Slot()
    def on_varname_change(self):
        self.varname = self.varname_field.text()
    
    def apply_preset(self, d_struct):
        super().apply_preset(d_struct)

    def copy_from(self, other):
        self.set_varname(other.varname)
        self.set_target(other.target)

    def set_next(self, next:QStepWidget,set_self_varname = True):
        prev =self.next
        if(prev is not None):
            self.layout().removeWidget(prev)
            prev.deleteLater()
        if(next is not None):
            glayout:QGridLayout = self.layout()
            glayout.addWidget(next,self.max_row_idx+1,0,1,5)
            if(hasattr(next, "target_field")):
                if(set_self_varname):
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
    
class RemovableFunctionStep(FunctionStep):
    def __init__(self, wf_fun_name, wf_fun_params,formal_name:str|None = None,max_row_idx = 0, target = "og"):
        super().__init__(wf_fun_name, wf_fun_params,formal_name,max_row_idx, target)
        layout: QGridLayout = self.layout()
        self.removal_action = lambda: None
        self.rmbtn = QPushButton("-")
        self.rmbtn.clicked.connect(lambda: self.get_removal_action()()) # abusing closures
        layout.addWidget(self.rmbtn, 0,4,Qt.AlignmentFlag.AlignRight)
        self.clear_next()
    
    def get_removal_action(self):
        return self.removal_action
    
    def apply_preset(self, d_struct):
        super().apply_preset(d_struct)
        self.copy_from(d_struct.additional_steps.pop(0))
        if(len(d_struct.additional_steps) != 0):
            self.set_next(d_struct.additional_steps[0],set_self_varname=False)
            self.next.apply_preset(d_struct)

class ImportStep(FunctionStep):
    FORMAL_NAME = "Import"
    def __init__(self):
        super().__init__("import", ["FBX"], formal_name=ImportStep.FORMAL_NAME)
        self.varname_field.setText("og")
        self.target_field.setText("inFile")
        self.target_field.textChanged.emit(None)
        self.varname_field.textChanged.emit(None)
    
    def apply_preset(self, d_struct:StepsPreset):
        self.copy_from(d_struct.import_step)
        self.set_next(d_struct.additional_steps[0],set_self_varname=False)
        self.next.apply_preset(d_struct)
    
    def copy_from(self, other):
        return super().copy_from(other)

class UnityfyStep(RemovableFunctionStep):
    FORMAL_NAME = "Blender -> Unity"
    def __init__(self):
        super().__init__("unityfy", [], formal_name=self.FORMAL_NAME)

class UnUnityfyStep(RemovableFunctionStep):
    FORMAL_NAME = "Unity -> Blender"
    def __init__(self):
        super().__init__("un-unityfy", [], formal_name=self.FORMAL_NAME)

class UvUnwrapStep(RemovableFunctionStep):
    FORMAL_NAME = "UV Unwrap"
    def __init__(self):
        super().__init__("uv-unwrap", [], formal_name=UvUnwrapStep.FORMAL_NAME)

class PlanarStep(RemovableFunctionStep):
    FORMAL_NAME = "Planar Decimate"
    @QtCore.Slot()
    def on_deg_change(self):
        if(self.deg_field.value()==0):
            self.deg_field.setValue(1)
        self.deg_indicator.setText(f"degree: {self.deg_field.value()/100.0:.02f}")
        self.deg = self.deg_field.value()/100.0
        self.wf_fun_params = [str(f"(deg->rad {self.deg})")]

    def __init__(self, deg:int|float = 10):
        super().__init__("Planar", [str(f"(deg->rad {deg})")],max_row_idx=1,formal_name=PlanarStep.FORMAL_NAME)
        glayout: QGridLayout = self.layout()
        self.deg_indicator = QLabel()
        self.deg_field = QSlider(Qt.Orientation.Horizontal)
        self.deg_field.setRange(1,36000)
        self.deg_field.valueChanged.connect(self.on_deg_change)
        self.set_deg(deg)
        glayout.addWidget(self.deg_indicator,1,0)
        glayout.addWidget(self.deg_field,1,1,1,3)
        self.clear_next()
    
    def set_deg(self, deg:int|float):
        self.deg_field.setValue(deg*100)
        self.deg_field.valueChanged.emit(None)
    
    def copy_from(self, other):
        super().copy_from(other)
        self.set_deg(other.deg)
        
class UnsubdivStep(RemovableFunctionStep):
    FORMAL_NAME = "Unsubdivide"
    def __init__(self, iterations:int = 10):
        super().__init__("unsubdiv", [make_string(str(iterations))],max_row_idx=1, formal_name=UnsubdivStep.FORMAL_NAME)
        glayout: QGridLayout = self.layout()
        self.iteration_indicator = QLabel()
        self.iteration_field = QSlider(Qt.Orientation.Horizontal)
        self.iteration_field.setRange(1,100)
        self.iteration_field.valueChanged.connect(self.iteration_changed)
        self.set_iterations(iterations)
        glayout.addWidget(self.iteration_indicator, 1,0)
        glayout.addWidget(self.iteration_field, 1,1,1,3)
    
    @QtCore.Slot()
    def iteration_changed(self):
        self.iteration_indicator.setText(f"iterations: {self.iteration_field.value()}")
        self.iterations = self.iteration_field.value()
        self.wf_fun_params = [make_string(str(self.iterations))]
    
    def set_iterations(self, iterations:int):
        self.iteration_field.setValue(iterations)
        self.iteration_field.valueChanged.emit(None)
    
    def copy_from(self, other):
        super().copy_from(other)
        self.set_iterations(other.iterations)

class CollapseStep(RemovableFunctionStep):
    FORMAL_NAME="Collapse Decimate"
    def __init__(self, ratio:int|float = 1.0):
        super().__init__("collapse", [make_string(str(ratio))],max_row_idx=1,formal_name=CollapseStep.FORMAL_NAME)
        glayout: QGridLayout = self.layout()
        self.ratio_indicator = QLabel()
        self.ratio_field = QSlider(Qt.Orientation.Horizontal)
        self.ratio_field.setRange(1,100)
        self.ratio_field.valueChanged.connect(self.ratio_changed)
        glayout.addWidget(self.ratio_indicator, 1,0)
        glayout.addWidget(self.ratio_field, 1,1,1,3)
        self.set_ratio(ratio)
    
    @QtCore.Slot()
    def ratio_changed(self):
        self.ratio_indicator.setText(f"ratio: {self.ratio_field.value()/100.0}")
        self.ratio = self.ratio_field.value()/100.0
        self.wf_fun_params = [make_string(str(self.ratio))]
    
    def set_ratio(self, ratio:int|float):
        self.ratio_field.setValue(ratio*100.0)
        self.ratio_field.valueChanged.emit(None)
    
    def copy_from(self, other):
        super().copy_from(other)
        self.set_ratio(other.ratio)

class ExportStep(QStepWidget):
    FORMAL_NAME = "Export"
    def __init__(self, targets=["og"].copy(),suffix="out", export_to = "./"):
        super().__init__()
        glayout = QGridLayout()
        self.setLayout(glayout)
        "export variables: ... as file ..."
        export_label = QLabel("Export Variable(s): ")
        self.targets_field = QLineEdit(text=", ".join(targets))
        as_label = QLabel("at Folder: ")
        self.export_to = export_to
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
    
    def set_targets(self, targets):
        self.targets_field.setText(",".join(targets))
        self.targets_field.textChanged.emit(None)
    
    def get_targets(self):
        targets = self.targets_field.text().split(",")
        return list(map(lambda v: v.strip(),targets))
    
    def set_suffix(self, suffix):
        self.suffix_field.setText(suffix)
        self.suffix_field.textChanged.emit(None)
    
    def get_suffix(self):
        return self.suffix_field.text()
    
    def set_export_to(self, export_to):
        self.export_to = os.path.abspath(export_to)
        self.file_choose_button.setText(os.path.relpath(self.export_to) + os.path.sep)
    
    def get_export_to(self):
        return self.export_to

    def apply_preset(self, d_struct):
        super().apply_preset(d_struct)
        self.copy_form(d_struct.export_step)
    
    def copy_form(self, other):
        self.set_targets(other.get_targets())
        # print(other.get_suffix())
        self.set_suffix(other.get_suffix())
        self.set_export_to(other.get_export_to())
    
    @QtCore.Slot()
    def chooseFolder(self):
        folder = QFileDialog.getExistingDirectory(None, 
                                              "Choose an File to save to",
                                              self.export_to)
        
        self.set_export_to(folder)
    
    def __str__(self):
        targets = self.get_targets()
        if(len(targets) == 1):
            targets = targets[0]        
        else:
            targets = "(+ " + " ".join(targets) + ")"

        outFile = f"""
(+ {repr(make_string(self.export_to))} 
    (filepath-filenameNoExt inFile) 
    {repr(make_string(self.suffix_field.text()+".fbx"))})"""
        return f"(export FBX {make_string(outFile)} {str(targets)})"

GENERAL_CLASSES = [(UvUnwrapStep.FORMAL_NAME, UvUnwrapStep),
                    (PlanarStep.FORMAL_NAME, PlanarStep),
                    (UnsubdivStep.FORMAL_NAME, UnsubdivStep),
                    (CollapseStep.FORMAL_NAME, CollapseStep),
                    (UnityfyStep.FORMAL_NAME, UnityfyStep),
                    (UnUnityfyStep.FORMAL_NAME, UnUnityfyStep)]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("expLODe")
        self.main_widget = MainWidget()
        self.menuBar = MenuBar()
        self.setCentralWidget(self.main_widget)
        self.setMenuBar(self.menuBar)
        self.menuBar.open_signal.connect(self.open_gui_workflow)
        self.menuBar.save_signal.connect(self.save_gui_workflow)
        self.resize(1920,1080)

    def import_gui_workflow(self,path,show_code=True):
        preset = StepsPreset()
        content = []
        with open(path) as file:
            content = file.readlines()
        while len(content) != 0:
            inp = content.pop(0)
            if(inp.strip() == ""): 
                continue
            s_content = sexp(inp)
            while s_content.num_unclosed != 0:
                inp = " ".join([inp, content.pop(0)])
                s_content = sexp(inp)
            while(len(s_content) != 0):
                if(type(s_content) is sexp):
                    s_content = s_content.content()
                match s_content:
                    case ("def"|"define", "inFiles", inFiles):
                        s_content = make_list(())
                        # print(f"inFiles: {inFiles}")
                        cfs = ChooseFileStep()
                        cfs.updateFileList(inFiles)
                        preset.choose_file_step = cfs
                    case ("def"|"define", ("fn-for-inFile", "inFile"),step):
                        s_content=step
                    case ("def"|"define", ("fn-for-inFiles", "inFiles"), step):
                        s_content = make_list(())
                    case ("with", (varname, ("import", "FBX", "inFile")), step):
                        s_content = step
                        i_s = ImportStep()
                        i_s.set_varname(str(varname))
                        preset.import_step = i_s
                    case ("with", (varname, ("unityfy", target)), step):
                        s_content = step
                        unityfy_s = UnityfyStep()
                        unityfy_s.set_varname(str(varname))
                        preset.additional_steps.append(unityfy_s)
                    case ("with", (varname, ("un-unityfy", target)), step):
                        s_content = step
                        ununityfy_s = UnUnityfyStep()
                        ununityfy_s.set_varname(str(varname))
                        preset.additional_steps.append(ununityfy_s)
                    case ("with", (varname, ("uv-unwrap", target)),step):
                        s_content = step
                        uvstep =UvUnwrapStep()
                        uvstep.set_varname(str(varname))
                        uvstep.set_target(str(target))
                        preset.additional_steps.append(uvstep)
                    case ("with", (varname, ("planar", ("deg->rad", deg), target)), step):
                        s_content = step
                        planarstep = PlanarStep(deg)
                        planarstep.set_varname(str(varname))
                        planarstep.set_target(str(target))
                        preset.additional_steps.append(planarstep)
                    case ("with", (varname, ("unsubdiv", iterations, target)), step):
                        s_content = step
                        unsubdiv = UnsubdivStep(iterations)
                        unsubdiv.set_varname(str(varname))
                        unsubdiv.set_target(str(target))
                        preset.additional_steps.append(unsubdiv)
                    case ("with", (varname, ("collapse", ratio, target)), step):
                        s_content = step
                        collapse = CollapseStep(ratio)
                        collapse.set_varname(str(varname))
                        collapse.set_target(str(target))
                        preset.additional_steps.append(collapse)
                    case ("export", "FBX", ("+"|"add", 
                        export_to, 
                        ("filepath-filenameNoExt", "inFile"),
                        suffixWithExtension),
                        ("+"|"add", *targets)):
                        s_content = make_list(())
                        suffix = suffixWithExtension[:-4]
                        # print(targets)
                        exportStep = ExportStep([str(target) for target in targets],suffix,export_to)
                        preset.export_step = exportStep
                    case ("export", "FBX", ("+"|"add", 
                        export_to, 
                        ("filepath-filenameNoExt", "inFile"),
                        suffixWithExtension),
                        target):
                        s_content = make_list(())
                        suffix = suffixWithExtension[:-4]
                        # print(suffix)
                        exportStep = ExportStep(targets=[str(target)],suffix=suffix,export_to=export_to)
                        preset.export_step = exportStep
                    case ("fn-for-inFiles", "inFiles"):
                        # skip
                        s_content = make_list(())
                    # case ((step,)):
                    #     s_content = step
                    case step:
                        print("unknown sexp: ",step)
                        s_content = make_list(())
        self.main_widget.apply_preset(preset, show_code=show_code) 

    @QtCore.Slot()
    def open_gui_workflow(self):
        path, _ =QFileDialog.getOpenFileName(None, "Choose a gui-compatible workflow script",
                                    ".","GUI-compatible workflow (*.gui.wf)")
        self.import_gui_workflow(path)
        

    def save_gui_workflow(self):
        path, _ = QFileDialog.getSaveFileName(None,"Save a GUI-compatible workflow script",
                                           os.path.expanduser("~"),"GUI-compatible workflow (*.gui.wf)")
        if(not path.lower().endswith(".gui.wf")):
            path += ".gui.wf"
        with open(path, "w") as file:
            file.write(self.main_widget.get_code())
        
    def get_workflows_widget(self):
        return self.main_widget.get_workflows_widget()

class expLODe_gui_app(QApplication):
    def __init__(self):
        super().__init__([])
        self.window = MainWindow()
        self.window.import_gui_workflow(os.path.join(proj_root, "default.gui.wf"), show_code=False)
        self.config = get_config()
        if(self.config.get("expLODe.blenderCmd", "") == "" or not check_version()):
            QMessageBox.information(None, "Notification", "Blender Not Detected! Please Select a Valid Blender >=4.2, <5 Installation.")
            MenuBar.findAndSetBlender()

        self.setStyleSheet(
            """
            *[type=code]{
                background: black; 
                color: white;
            }

            QStepWidget{
                border: 1px solid black; 
                border-radius: 20%;
                background-color: transparent;
            }

            FunctionStep{
                border: 0px;
                border-radius: 0px;
            }

            EmptyStepWidget{
                border: 0px;
                border-radius: 0px;
            }

            ImportStep{
                border: 1px solid black;
                padding: 10px;
            }
            """)

    def exec(self):
        self.window.show()
        return super().exec()