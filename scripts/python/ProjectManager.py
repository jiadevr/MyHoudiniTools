import hou
import os
import json
import shutil

from PySide6 import QtCore,QtUiTools,QtWidgets,QtGui

class ProjectManager(QtWidgets.QMainWindow):
    # CLASS Constant

    def __init__(self) -> None:
        super().__init__()
        ui_path=hou.text.expandString("$MYLIB/ui/project_manager.ui").replace(os.sep,"/")
        self.ui=QtUiTools.QUiLoader().load(ui_path,parentWidget=self)
        self.setParent(hou.qt.mainWindow(),QtCore.Qt.Window)
        self.setWindowTitle("Project Manager")
        self.setMaximumSize(600,400)

        self._InitialUI_()
        self._SetupBindings_()

        self.config_file_path=hou.text.expandString("$MYLIB/configs/ProjectConfig.json").replace(os.sep,"/")
        
        # 读取Json信息
        self.LoadProjectsFromConfig()

    def _InitialUI_(self):
        '''
        Setup UI Element Ref
        '''
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

    def _SetupBindings_(self):
        '''
        SetupUI Binding To Functions
        '''
        self.project_detail.clicked.connect(self.ShowProjectDetails)
        self.project_enable.clicked.connect(lambda:self.ToggleProjectEnable(True))
        self.project_disable.clicked.connect(lambda:self.ToggleProjectEnable(False))
        self.delete_project.clicked.connect(self.DeleteProject)

        self.lw_project.currentItemChanged.connect(self.RefreshSceneList)
        self.create_scene.clicked.connect(self.CreateScene)
        self.delete_scene.clicked.connect(self.DeleteScene)

        self.open_file.clicked.connect(self.OpenFile)
        self.save_file.clicked.connect(self.SaveFile)
    
    def _RaiseAMessage_(self,in_message,in_severity=hou.severityType.Message,bshow_dialog:bool=False):
        '''
        Handle UI Mesaage And Status Box Text
        '''
        
        self.state_line.setText(in_message)
        if bshow_dialog or (in_severity==hou.severityType.Error or in_severity==hou.severityType.Warning or in_severity==hou.severityType.Fatal):
            return hou.ui.displayMessage(in_message,severity=in_severity)
        return 0
    
    def GetSelectedProject(self):
        '''
        Get Current Selected Project Or Display An Error
        Returns:
            tuple:(project_name,project_data) pr (None,None) if no selection
        '''
        if not self.lw_project.selectedItems:
            self._RaiseAMessage_("Plesae Select A Project",hou.severityType.Error)
            return None,None
        target_name=self.lw_project.currentItem().text()
        project_data=None

        for project in self.project_data:
            if target_name in project:
                project_data=project[target_name]
                break
        print(f"Current Select Project: {target_name},Info:{project_data}")
        return target_name,project_data


    def LoadProjectsFromConfig(self):
        '''
        List Project Data In ProjectConfig.json
        '''
        self.lw_project.clear()
        try :
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path,"r") as file:
                    self.project_data=json.load(file)
                project_names=[]
                for project in self.project_data:
                    project_names.append(list(project.keys())[0])

                project_names.sort()
                
                self.lw_project.addItems(project_names)

                self._RaiseAMessage_(f"Finish Load {len(project_names)} projects")

        except FileExistsError as error:
            self._RaiseAMessage_(f"Target File {self.config_file_path} NOT Existed!")

    def ShowProjectDetails(self):
        print("Show detail was Called")
        if not self.lw_project.selectedItems:
            self._RaiseAMessage_("Please Select A Project In Project List",in_severity=hou.severityType.Error)
        
        target_project,project_data =self.GetSelectedProject()
        
        if project_data:
            self._RaiseAMessage_(f"Project Detail for {'target_project'},\n"
                                  f"Project Code {project_data['projectCode']},\n"
                                  f"Project Path {project_data['projectPath']},\n"
                                  f"Project FPS {project_data['fps']},\n",bshow_dialog=True)
        else:
            self._RaiseAMessage_(f"Find Null Project Named {target_project}",hou.severityType.Error)
    
    def ToggleProjectEnable(self,status=True):
        if not self.lw_project.selectedItems:
            self._RaiseAMessage_("Please Select A Project In Project List",in_severity=hou.severityType.Error)
        
        env_var ={"JOB":"","CODE":"","FPS":"","PROJECT":""}

        target_project,project=self.GetSelectedProject()
        if status==True and target_project!=None:
            env_var.update({"JOB":project['projectPath'],
                            "CODE":project['projectCode'],
                            "FPS":project['fps'],
                            "PROJECT":target_project})

        for key,value in env_var.items():
            hou.putenv(key,value)
        
        self._RaiseAMessage_(f"Set  Env Value To{env_var}",bshow_dialog=True)

    def DeleteProject(self):
        if not self.lw_project.selectedItems:
            self._RaiseAMessage_("Please Select A Project In Project List",in_severity=hou.severityType.Error)
        
        target_project=self.lw_project.currentItem().text()

        user_choice= hou.ui.displayMessage(f"This Action Will Detele Project And All Project Files!!!",buttons=("Yes","Cancel"),severity=hou.severityType.Warning)
        if user_choice==1:
            self._RaiseAMessage_(f"Abandon To Delete Project {target_project}")
            return
        
        # 删除Json

        for project in self.project_data:
            if target_project in project:
                project_data = project[target_project]
                self.project_data.remove(project)
                break
        else:
            self._RaiseAMessage_(f"Find Null Project Named {target_project}")
            return
        
        try:
            with open(self.config_file_path,"w") as file:
                file.seek(0)
                file.truncate()
                json.dump(self.project_data,file,sort_keys=True,indent=4)
            # 刷新窗口
            self.LoadProjectsFromConfig()
            self._RaiseAMessage_(f"Remove Project {target_project} In Config File")
            # 删除文件
            project_dir= project_data["projectPath"]
            if os.path.exists(project_dir):
                try:
                    shutil.rmtree(project_dir)
                except Exception as Error:
                    self._RaiseAMessage_(f"Failed To Remove Project {target_project} Files: Reason{Error}",hou.severityType.Error)
                                
        except Exception as Error:
            self._RaiseAMessage_(f"Failed To Remove Project {target_project} Reason{Error}")
        
    def RefreshSceneList(self):
        self.lw_seq.clear()
        if not self.lw_project.selectedItems:
            self._RaiseAMessage_("Please Select A Project In Project List",in_severity=hou.severityType.Error)
        
        target_project,project_data=self.GetSelectedProject()
        
        seq_dir=os.path.join(project_data["projectPath"],"seq").replace(os.sep,"/")
        if not os.path.exists(seq_dir):
            self._RaiseAMessage_(f"Find Null Sequene File In Project Named {target_project}")
            return
        
        self.lw_seq.addItems(os.listdir(seq_dir))

    def CreateScene(self):
        #首先需要获得选中的路径
        target_project,project_data= self.GetSelectedProject()
        if target_project==None:
            self._RaiseAMessage_("Please Select A Project First",hou.severityType.Error)
            return
        
        project_dir:str=project_data["projectPath"].replace(os.sep,"/")
        print(project_dir)
        
        if not os.path.exists(project_dir):
            self._RaiseAMessage_(f"Give Project{target_project} 's Paths {project_dir} Doesn't Existed",hou.severityType.Error)
            return
        
        lable_tint=["SceneName:","SubFolders(comma separated)"]
        user_inputs=["NewScene","abc,tex,geo,render,cache,flip,sim"]
        user_inputs_tuple= hou.ui.readMultiInput(message="Create New Scene",input_labels=lable_tint,buttons=("OK","Cancel"),initial_contents=user_inputs)
        if user_inputs_tuple[0]!=0:
            self._RaiseAMessage_("Creating New Scene was Cancelled")
            return
        new_scene_name=user_inputs_tuple[1][0]
        sub_folders=user_inputs_tuple[1][1].split(",")
        print(f"project Dir Is{project_dir}")
        target_dir=os.path.join(project_dir,f"seq/{new_scene_name}")
        print(f"New Seq Dir Is: {target_dir}")
        if os.path.exists(target_dir):
            user_override= hou.ui.displayMessage("Given Path Is Already Existed,Do You Want To Override All Files?",buttons=("OK","Cancel"))
            if user_override==1:
                self._RaiseAMessage_("Creating New Scene was Cancelled,Reason : Duplicated Path",hou.severityType.Error)
                return
        else:

            os.makedirs(target_dir)
        for sub_folder in sub_folders:
            new_dir=os.path.join(target_dir,sub_folder).replace(os.sep,"/")
            os.makedirs(new_dir)        
        self._RaiseAMessage_(f"Finish Creating Seq {new_scene_name}")
        self.RefreshSceneList()

    def DeleteScene(self):
        target_project,project_data= self.GetSelectedProject()
        if target_project==None:
            self._RaiseAMessage_("Please Select A Project First",hou.severityType.Error)
            return
        
        project_seq_dir:str=os.path.join(project_data["projectPath"],"seq/").replace(os.sep,"/")
        print(f"Target Dir:{project_seq_dir}")
        
        if not os.path.exists(project_seq_dir):
            self._RaiseAMessage_(f"Give Project{target_project} 's Paths {project_seq_dir} Doesn't Existed",hou.severityType.Error)
            return
        
        selected_scene=self.lw_seq.currentItem().text()
        print(f"Current Select Seq Name: {selected_scene}")
        selected_scene=os.path.join(project_seq_dir,selected_scene).replace(os.path.sep,"/")

        if not os.path.exists(selected_scene):
            self._RaiseAMessage_(f"Target Path {selected_scene} Doesn't Existed",hou.severityType.Error)
            return

        user_input=hou.ui.displayMessage(f"Would You Like Delete All Files In {selected_scene}",buttons=("OK","Cancel"),severity=hou.severityType.Warning)

        if user_input!=0:
            self._RaiseAMessage_(f"Cancel Delete By User Choice")
            return
        
        shutil.rmtree(selected_scene)
        self.RefreshSceneList()
        return


    def OpenFile(self):

        pass

    def SaveFile(self):

        pass

window_gui=ProjectManager()
window_gui.show()