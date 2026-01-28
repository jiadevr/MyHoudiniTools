import hou
from pxr import Usd,Gf,UsdGeom

def create_lookdev_camera():
    node=hou.pwd()
    stage:hou.OpNode=node.editableStage()
    _create_lookdev_prameters_(node)

    target_prim_str:str=node.evalParm("target_str")
    camera_path:str=node.evalParm("camera_path")
    camera_yaw:float=node.evalParm("yaw")
    camera_pith:float=node.evalParm("pitch")
    arm_length:float=node.evalParm("arm_Length")
    banimate:bool=node.evalParm("banimate")
    buse_existing_camera:bool=node.evalParm("buse_existing_camera")
    existing_camera_path:str=node.evalParm("existing_camera_path")
    frames:int=node.evalParm("frames")
    start_frame:int=node.evalParm("start_frame")

    if not target_prim_str.startswith("/"):
        target_prim_str="/"+target_prim_str

    target_prim=stage.GetPrimAtPath(target_prim_str)
    if not target_prim:
        hou.ui.displayMessage(f"Find Invalid Prim of Given Path:{target_prim_str}")
        return
    bbox_cache=UsdGeom.BBoxCache(Usd.TimeCode.EarliestTime(),["default","render"])
    bounds=bbox_cache.ComputeLocalBound(target_prim).GetBox()

    camera_to_use=existing_camera_path if buse_existing_camera else camera_path

    camera_ref=None

    if buse_existing_camera:
        prim_of_given_path=stage.GetPrimAtPath(camera_to_use)
        if prim_of_given_path and prim_of_given_path.IsA(UsdGeom.Camera):
            camera_ref=UsdGeom.Camera(prim_of_given_path)
        else:
            raise hou.NodeError(f"Existing camera not found at{camera_to_use}")
    else:
        camera_ref=UsdGeom.Camera.Define(stage,camera_path)
        camera_ref.GetHorizontalApertureAttr().Set(10.0)
        camera_ref.GetVerticalApertureAttr().Set(10.0)
        camera_ref.GetFocalLengthAttr().Set(35.0)
        camera_ref.GetClippingRangeAttr().Set(Gf.Vec2f(0.01,10000.0))

def _create_lookdev_prameters_(node:hou.OpNode):
    '''
    给节点创建lookdev参数
    
    :param node: 调节目标参数
    :type node: hou.OpNode
    '''
    node_ptg=node.parmTemplateGroup()

    # 如果存在对应参数则认为已经创建过
    find_parm=node_ptg.find("target_str")
    if find_parm:
        return
    
    camera_folder=hou.FolderParmTemplate(
        name="camera_folder",
        label="LookDev Camera Settings",
        folder_type=hou.folderType.Simple
    )

    target_str=hou.StringParmTemplate(
        name="target_str",
        label="Target Prim",
        num_components=1
    )

    camera_str=hou.StringParmTemplate(
        name="camera_path",
        label="Camera Path",
        num_components=1,
        default_value=("/ThumbnailCamera",)
    )

    rot_yaw_float=hou.FloatParmTemplate(
        name="yaw",
        label="Camera Yaw",
        num_components=1,
        default_value=(0,),
        min=-180.0,
        max=180.0
    )

    rot_pitch_float=hou.FloatParmTemplate(
        name="pitch",
        label="Camera Pitch",
        num_components=1,
        default_value=(0,),
        min=-90.0,
        max=90.0
    )

    camera_arm_length=hou.FloatParmTemplate(
        name="arm_Length",
        label="Camera Arm Length",
        num_components=1,
        default_value=(0,),
        min=0.0,
        max=20.0
    )

    camera_folder.addParmTemplate(target_str)
    camera_folder.addParmTemplate(camera_str)
    camera_folder.addParmTemplate(rot_yaw_float)
    camera_folder.addParmTemplate(rot_pitch_float)
    camera_folder.addParmTemplate(camera_arm_length)
    node_ptg.append(camera_folder)

    animated_cam_folder=hou.FolderParmTemplate(
        name="animated_folder",
        label="Lookdev Animated Camera Settings"
        folder_type=hou.folderType.Simple
    )

    camera_folder.addParmTemplate(animated_cam_folder)

    banimate_toggle=hou.ToggleParmTemplate(
        name="banimate",
        label="Animate"
    )

    buse_existing_camera=hou.ToggleParmTemplate(
        name="buse_existing_camera",
        label="Use Existing Camera",
        disable_when="{banimate==0}"
    )

    camera_path_string=hou.StringParmTemplate(
        name="existing_camera_path",
        label="Existing Camera Path",
        num_components=1,
        disable_when="{buse_existing_camera==0}"
    )

    num_frames=hou.IntParmTemplate(
        name="frames",
        label="Number of Frames",
        num_components=1,
        default_value=(60,),
        min=30,
        disable_when="{banimate==0}"
    )

    start_frame=hou.IntParmTemplate(
        name="start_frame",
        label="Start Frame",
        default_value=(0,),
        num_components=1,
        disable_when="{banimate==0}"
    )

    animated_cam_folder.addParmTemplate(banimate_toggle)
    animated_cam_folder.addParmTemplate(buse_existing_camera)
    animated_cam_folder.addParmTemplate(camera_path_string)
    animated_cam_folder.addParmTemplate(num_frames)
    animated_cam_folder.addParmTemplate(start_frame)
    node_ptg.append(animated_cam_folder)

    node.setParmTemplateGroup(node_ptg)