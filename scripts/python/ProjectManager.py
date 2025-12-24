import hou
import os
import json
import shutil

from PySide6 import QtCore,QtUiTools,QtWidgets,QtGui

class ProjectManager(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        project_description_path=hou.text.expandString("$MYLIB")+"configs/ProjectConfig.json"
        ui_path=hou.text.expandString("$MYLIB")+"/ui/project_manager.ui"
        print(ui_path)
        self.ui=QtUiTools.QUiLoader().load(ui_path,parentWidget=self)
        self.setParent(hou.qt.mainWindow(),QtCore.Qt.Window)
        self.setWindowTitle("Project Manager")
        self.setMaximumSize(600,400)

        # 获取各对象引用
        self.lw_project:QtWidgets.QListWidget=self.ui.findChild(QtWidgets.QListWidget,"lw_projects")

        self.project_detail:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_proj_details")
        self.project_enable:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_proj_enable")
        self.project_disable:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_proj_disable")
        self.delete_project:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_proj_delete")

        self.lw_seq:QtWidgets.QListWidget=self.ui.findChild(QtWidgets.QListWidget,"lw_seq")
        self.create_scene:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_create_scene")
        self.delete_scene:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_delete_scene")

        self.lw_files:QtWidgets.QListWidget=self.ui.findChild(QtWidgets.QListWidget,"lw_files")
        self.open_file:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_open")
        self.save_file:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_save")

        self.state_line:QtWidgets.QLineEdit=self.ui.findChild(QtWidgets.QLineEdit,"lineEdit")
        
        
        # 读取Json信息
        self.LoadProjectsFromConfig()

        # 绑定按键行为
        self.project_detail.clicked.connect(self.ShowProjectDetails)
        self.project_enable.clicked.connect(lambda:self.ToggleProjectEnable(True))
        self.project_disable.clicked.connect(lambda:self.ToggleProjectEnable(False))
        self.delete_project.clicked.connect(self.DeleteProject)

        self.lw_project.itemSelectionChanged.connect(self.RefreshSceneList)
        #self.create_scene.clicked.connect()
        
    def LoadProjectsFromConfig(self):
        '''
        List Project Data In ProjectConfig.json
        '''
        self.lw_project.clear()
        config_path=hou.text.expandString("$MYLIB/configs/ProjectConfig.json")
        try :
            if os.path.exists(config_path):
                with open(config_path,"r") as file:
                    self.project_data=json.load(file)
                project_names=[]
                for project in self.project_data:
                    project_names.append(list(project.keys())[0])

                project_names.sort()
                

                self.lw_project.addItems(project_names)

                self.state_line.setText(f"Finish Load {len(project_names)} projects")

        except FileExistsError as error:
            self.state_line.setText(f"Target File {config_path} NOT Existed!")

    def ShowProjectDetails(self):
        print("Show detail was Called")
        if not self.lw_project.selectedItems:
            hou.ui.displayMessage("Please Select A Project In Project List",severity=hou.severityType.Error)
        
        target_project=self.lw_project.currentItem().text()

        for project in self.project_data:
            if target_project in project:
                project_data = project[target_project]
                break
        
        if project_data:
            hou.ui.displayMessage(f"Project Detail for {'target_project'},\n"
                                  f"Project Code {project_data['projectCode']},\n"
                                  f"Project Path {project_data['projectPath']},\n"
                                  f"Project FPS {project_data['fps']},\n",
                                  title=f"Detail for {target_project}")
        else:
            hou.ui.displayMessage(f"Find Null Project Named {target_project}")
    
    def ToggleProjectEnable(self,status=True):
        if not self.lw_project.selectedItems:
            hou.ui.displayMessage("Please Select A Project In Project List",severity=hou.severityType.Error)
        
        env_var ={"JOB":"","CODE":"","FPS":"","PROJECT":""}

        target_project=self.lw_project.currentItem().text()
        if status==True:
            for project in self.project_data:
                if target_project in project:
                    env_var.update({"JOB":project[target_project]['projectPath'],
                                    "CODE":project[target_project]['projectCode'],
                                    "FPS":project[target_project]['fps'],
                                    "PROJECT":target_project})
                    break
            else:
                hou.ui.displayMessage(f"Find Null Item Named {target_project}")
                return

        for key,value in env_var.items():
            hou.putenv(key,value)
        
        self.state_line.setText(f"Set Env Value To{env_var}")
        hou.ui.displayMessage(f"Set  Env Value To{env_var}")

    def DeleteProject(self):
        if not self.lw_project.selectedItems:
            hou.ui.displayMessage("Please Select A Project In Project List",severity=hou.severityType.Error)
        
        target_project=self.lw_project.currentItem().text()

        user_choice= hou.ui.displayMessage(f"This Action Will Detele Project And All Project Files!!!",buttons=("Yes","Cancel"),severity=hou.severityType.Warning)
        if user_choice==1:
            self.state_line.setText(f"Abandon To Delete Project {target_project}")
            return
        
        # 删除Json
        for project in self.project_data:
            if target_project in project:
                project_data = project[target_project]
                self.project_data.remove(project)
                break
        else:
            hou.ui.displayMessage(f"Find Null Project Named {target_project}")
            return
        
        try:
            config_path=hou.text.expandString("$MYLIB/configs/ProjectConfig.json")
            with open(config_path,"w") as file:
                file.seek(0)
                file.truncate()
                json.dump(self.project_data,file,sort_keys=True,indent=4)
            # 刷新窗口
            self.LoadProjectsFromConfig()
            self.state_line.setText(f"Remove Project {target_project} In Config File")
            # 删除文件
            project_dir= project_data["projectPath"]
            if os.path.exists(project_dir):
                try:
                    shutil.rmtree(project_dir)
                except Exception as Error:
                    self.state_line.setText(f"Failed To Remove Project {target_project} Files: Reason{Error}")
                    hou.ui.displayMessage(f"Failed To Remove Project {target_project} Files: Reason{Error}")
                                
        except Exception as Error:
            self.state_line.setText(f"Failed To Remove Project {target_project} Reason{Error}")
        
    def RefreshSceneList(self):
        self.lw_seq.clear()
        if not self.lw_project.selectedItems:
            hou.ui.displayMessage("Please Select A Project In Project List",severity=hou.severityType.Error)
        
        target_project=self.lw_project.currentItem().text()

        for project in self.project_data:
            if target_project in project:
                project_data= project[target_project]
                break
        else:
            hou.ui.displayMessage(f"Find Null Project Named {target_project}")
            return
        
        seq_dir=os.path.join(project_data["projectPath"],"seq").replace(os.sep,"/")
        if not os.path.exists(seq_dir):
            hou.ui.displayMessage(f"Find Null Sequene File In Project Named {target_project}")
            return
        
        self.lw_seq.addItems(os.listdir(seq_dir))

window_gui=ProjectManager()
window_gui.show()