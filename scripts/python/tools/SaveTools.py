import hou
import os
import glob

from PySide6 import QtCore,QtUiTools,QtWidgets,QtGui

class SaveToolWindow(QtWidgets.QWidget):
    def __init__(self,in_scene_dir=None,in_project_name=None,in_seq_name=None) -> None:
        super().__init__()
        # 基础窗口设置
        self.setWindowTitle("Save Tool")
        self.resize(400,200)
        self.setParent(hou.qt.mainWindow(),QtCore.Qt.Window)
        self._init_ui_()
        self._init_bindings_()
        self.scene_dir=str(in_scene_dir)
        self.project_name=in_project_name
        self.seq_name=in_seq_name

        self._init_tints_()

        self.current_version=-1
        self.save_path:str=""

    def _init_ui_(self):
        # 定义提示文字
        self.project_label=QtWidgets.QLabel("Project Info Here")
        self.project_label.setMinimumHeight(20)
        self.stage_lable=QtWidgets.QLabel("Stage")
        self.stage_lable.setMinimumHeight(20)
        self.department_lable=QtWidgets.QLabel("Department")
        self.department_lable.setMinimumHeight(20)
        self.file_name_lable=QtWidgets.QLabel("File Name:")
        self.file_name_lable.setMinimumHeight(20)
        self.status_lable=QtWidgets.QLabel("Show Stage Here")
        self.status_lable.setMinimumHeight(20)
        # 定义下拉框
        self.stage_combo=QtWidgets.QComboBox()
        self.stage_combo.setMinimumHeight(25)
        self.stage_combo.addItems(["MAIN","DEV","WIP"])

        self.department_combo=QtWidgets.QComboBox()
        self.department_combo.setMinimumHeight(25)
        self.department_combo.addItems(["GEN","ANIM","CFX","ENV","FX","LRC","RIG","LAYOUT"])
        # 定义输入框
        self.file_name_input=QtWidgets.QLineEdit()
        self.file_name_input.setMinimumHeight(25)
        # 定于Button
        self.save_button=QtWidgets.QPushButton()
        self.save_button.setText("Save")
        self.save_button.setMinimumSize(400,50)
        

        # 定义LayOut
        self.main_layout=QtWidgets.QVBoxLayout()

        self.main_layout.addWidget(self.project_label)
        self.tint_stage_row=QtWidgets.QHBoxLayout()
        self.tint_stage_row.addWidget(self.stage_lable)
        self.tint_stage_row.addWidget(self.department_lable)
        self.main_layout.addLayout(self.tint_stage_row)

        self.combo_row=QtWidgets.QHBoxLayout()
        self.combo_row.addWidget(self.stage_combo)
        self.combo_row.addWidget(self.department_combo)
        self.main_layout.addLayout(self.combo_row)

        self.main_layout.addWidget(self.file_name_lable)
        self.main_layout.addWidget(self.file_name_input)
        self.main_layout.addWidget(self.save_button)
        self.main_layout.addWidget(self.status_lable)

        self.setLayout(self.main_layout)

    def _init_bindings_(self):
        self.stage_combo.currentTextChanged.connect(self.RefreshSavePath)
        self.department_combo.currentIndexChanged.connect(self.RefreshSavePath)
        self.file_name_input.textChanged.connect(self.RefreshSavePath)
        self.save_button.clicked.connect(self.SaveProj)

    def _init_tints_(self):
        self.project_label.setText(f"Target Project:{self.project_name},Target Seq:{self.seq_name}")
        self.status_lable.setText(f"Current Path:{self.scene_dir}")

    def RefreshSavePath(self):

        user_input_file_name=self.file_name_input.text().replace(" ","_").strip() or "Unnamed"
        user_name=hou.getenv("USER")
        target_file_name=f"{self.stage_combo.currentText()}_{self.department_combo.currentText()}_{user_input_file_name}_{user_name}"
        extension=self.GetFileExtension()
        ver_num=self.GetCurrentVersion(target_file_name,extension)
        self.save_path=target_file_name+f"_v{ver_num:03d}.{extension}"
        self.save_path=os.path.join(self.scene_dir,self.save_path).replace(os.sep,"/")
        self.status_lable.setText(f"Target Saving Path:{self.save_path}")
        
    def GetCurrentVersion(self,in_name_prefix,in_extension="hip")->int:
        if not self.scene_dir==None and os.path.exists(self.scene_dir):
            #查找文件夹下对应的文件
            pattern=os.path.join(self.scene_dir,in_name_prefix).replace(os.sep,"/")
            pattern=f"{pattern}_v[0-9][0-9][0-9].{in_extension}"
            existing_files=glob.glob(pattern)

            if not existing_files:
                return 1
            else: 
                version=0
                for file in existing_files:
                    try:
                        version_str=file.split("_v")[-1].split(".")[0]
                        version_num=int(version_str)
                        version=max(version_num,version)
                    except(ValueError,IndexError):
                        continue
                return version+1
        else:
            hou.ui.displayMessage("Empty Path ,Get Scene Dir Failed,Please Check If The Path Exist")
        return 1

    def GetFileExtension(self)->str:
        license_extension_map={
            "Commercial":"hip",
            "Indie":"hiplc",
            "Apprentice":"hipnc",
            "ApprenticeHD":"hipnc",
            "Education":"hipnc"
        }
        user_license=hou.licenseCategory().name()
        return license_extension_map[user_license]

    def SaveProj(self):
        try:
            hou.hipFile.save(self.save_path)
            self.status_lable.setText("Finish Save hip File")
        except Exception as Error:
            hou.ui.displayMessage(f"Fail to Save hip File,Reason:{Error}")


#win=SaveToolWindow()
#win.show()