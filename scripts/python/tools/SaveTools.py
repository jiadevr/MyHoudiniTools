import hou
import os

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
        self.scene_dir=in_scene_dir
        self.project_name=in_project_name
        self.seq_name=in_seq_name


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
        self.save_button.clicked.connect(self.SaveProj)


    def SaveProj(self):
        print(self.project_dir)
        print(self.project_name)
        print(self.seq_name)


#win=SaveToolWindow()
#win.show()