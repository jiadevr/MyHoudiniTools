import hou
import os
import my_houdini_utils
import json

from PySide6 import QtCore,QtUiTools,QtWidgets,QtGui

class ProjectGenerator(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        work_dir=hou.text.expandString("$MYLIB")
        ui_path= work_dir+"/ui/project_creator.ui"
        print(ui_path)
        self.ui=QtUiTools.QUiLoader().load(ui_path,parentWidget=self)
        self.setParent(hou.qt.mainWindow(),QtCore.Qt.Window)
        self.setWindowTitle("Project Creator")
        self.setMaximumSize(400,500)

        #初始化对象引用
        self.dir_selector:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_directory")
        self.project_name:QtWidgets.QLineEdit=self.ui.findChild(QtWidgets.QLineEdit,"le_proj_name")
        self.project_code:QtWidgets.QLineEdit=self.ui.findChild(QtWidgets.QLineEdit,"le_proj")
        self.project_fps:QtWidgets.QLineEdit=self.ui.findChild(QtWidgets.QLineEdit,"le_fps")
        self.folders:QtWidgets.QPlainTextEdit=self.ui.findChild(QtWidgets.QPlainTextEdit,"qpt_folders")
        self.create_project:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_create_project")
        
        # 初始化状态
        self.project_name.setEnabled(False)
        self.project_code.setEnabled(False)
        self.project_fps.setEnabled(False)
        self.folders.setEnabled(False)
        self.create_project.setEnabled(False)

        self.dir_selector.clicked.connect(self.selectDir)
        self.project_name.textChanged.connect(self.checkButtonState)
        self.project_code.textChanged.connect(self.checkButtonState)
        self.project_fps.textChanged.connect(self.checkButtonState)
        int_validator_fps=QtGui.QIntValidator()
        self.project_fps.setValidator(int_validator_fps)
        self.create_project.clicked.connect(self.createProjectFiles)

        #初始化变量
        self.project_dir:str=""


    def selectDir(self):
        '''
        Open Direction Selector Window and Validate Selected Path
        '''
        default_dir="$Home"
        selected_path=hou.ui.selectFile(start_directory=default_dir, 
                                        title="Select Target Project Dir",
                                        file_type=hou.fileType.Directory)
        self.project_dir = my_houdini_utils.isValidDir(selected_path)
        if not self.project_dir=="None":
            self.project_name.setEnabled(True)
            self.project_code.setEnabled(True)
            self.project_fps.setEnabled(True)
    
    def checkButtonState(self):
        '''
        Change CreateProject Button Clickable By Above Info
        '''
        if (self.project_name.text and self.project_code.text and self.project_fps.text and self.folders.getPaintContext):
             self.create_project.setEnabled(True)
        else:
             self.create_project.setEnabled(False)

    def createProjectFiles(self):
        '''
        Write Info to Json File And Create Project Struction
        '''
        # 整理信息
        user_project_name=self.project_name.text().strip()
        user_project_code=self.project_code.text().strip()
        user_project_fps=self.project_fps.text().strip()
        user_project_path=os.path.join(self.project_dir,user_project_name).replace(os.sep,"/")
        user_project_folders=self.folders.toPlainText().strip()
        info_dic={
            user_project_name:{
                "enabled":True,
                "projectCode":user_project_code,
                "projectPath":user_project_path,
                "fps":user_project_fps,
                "projectFolders":user_project_folders
            }
        }
        # 反序列化Json数据
        json_file_path=hou.text.expandString("$MYLIB/configs")
        json_file_path=os.path.join(json_file_path,"ProjectConfig.json")
        print(f"Config File Path:{json_file_path}")
        data=[]
        if os.path.exists(json_file_path):
            with open(json_file_path,"r") as file:
                try:
                    data=json.load(file)
                except json.JSONDecodeError:
                    data=[]
        else:
            print(f"{json_file_path} doesn't exist Create New")
            data=[]

        for single_item in data:
            item_name=list(single_item.keys())[0]
            item_info=single_item[item_name]
            item_code=item_info["projectCode"]
            if(item_name==user_project_name or item_code==user_project_code):
                hou.ui.displayMessage(f"There already a record with same name or code:\n\n"
                                      f"Duplicated Code:{item_code}-Your Code{user_project_code}\n\n"
                                      f"Duplicated Name{item_name}-Your Project Name{user_project_name}\n\n"
                                      f"Please Use Another Code or Name",
                                      severity=hou.severityType.Error)
                return
        data.append(info_dic)
        print(data)
        #文件不存在是使用w可以创建文件，但必须保证文件路径完全（父级文件夹必须存在，否则报错）
        with open(json_file_path,"w") as file:
            json.dump(data,file,sort_keys=True,indent=4)
        print(f"Finished Wrote Info To Json File{json_file_path}")
        
        #创建文件结构
        folder_array=user_project_folders.split(",")
        for sub_folder in folder_array:
            sub_folder_path=os.path.join(user_project_path,sub_folder.strip())
            #print(f"Creat Dir: {sub_folder_path}")
            os.makedirs(sub_folder_path,exist_ok=True)

        hou.ui.displayMessage(f"Create Project {user_project_name} Successfully")

window_gui=ProjectGenerator()
window_gui.show()