import hou

class MultiCameraManager:
    '''
    Helps manager cameras in a houdini scene
    Allow to set cameras-set camera,set frame range
    Allow batch rename camera
    Merge all camera into one single camera
    Render submission
    '''
    def __init__(self) -> None:
        self.cameras={}
        self.obj=hou.node("/obj")
        print("Finish Init Camera Manager")

    def scan_scene_cameras(self):
        if not self.obj:
            hou.ui.displayMessage("Error: Invalid Parent Node",severity=hou.severityType.Error)
            return
        try:
            self.cameras={
                cam.name():cam for cam in self.obj.recursiveGlob("*",filter=hou.nodeTypeFilter.ObjCamera)
            }
            if len(self.cameras)==0:
                hou.ui.displayMessage("Find Null Camera In Scene")
                return
            self.create_camera_menu()
        except Exception as e:
            print(f"Fail to scan camera,with Error:{e}")

    def create_camera_menu(self):
        if not self.obj:
            hou.ui.displayMessage("Error: Invalid Parent Node",severity=hou.severityType.Error)
            return
        hda_node=hou.pwd()
        node_ptg=hda_node.parmTemplateGroup()
        camera_names=list(self.cameras.keys())

        existed_selector=node_ptg.find("cameras_selector")
        
        camera_menu=hou.MenuParmTemplate(
            name="cameras_selector",
            label="Select Camera",
            menu_items=camera_names,
            menu_labels=camera_names
        )
        if not existed_selector:
            node_ptg.insertAfter("scan_scene",camera_menu)
        else:
            node_ptg.replace(existed_selector,camera_menu)
        hda_node.setParmTemplateGroup(node_ptg)
        hda_node.parm("set_visible")._set(1)