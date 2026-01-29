import hou
import pdb
from pxr import Usd, Gf, UsdGeom
import husd.assetutils as assetutils
import tools.CreateUSDCompBuilder as compbuilder
import tools.CreateUSDPreviewEnv as lightbuilder


def create_lookdev_camera():
    node = hou.pwd()
    stage: hou.OpNode = node.editableStage()
    _create_lookdev_prameters_(node)

    target_prim_str: str = node.evalParm("target_str")
    camera_path: str = node.evalParm("camera_path")
    camera_yaw: float = node.evalParm("yaw")
    camera_pitch: float = node.evalParm("pitch")
    arm_length: float = node.evalParm("arm_Length")
    banimate: bool = node.evalParm("banimate")
    buse_existing_camera: bool = node.evalParm("buse_existing_camera")
    existing_camera_path: str = node.evalParm("existing_camera_path")
    frames: int = node.evalParm("frames")
    start_frame: int = node.evalParm("start_frame")

    if not target_prim_str.startswith("/"):
        target_prim_str = "/" + target_prim_str

    target_prim = stage.GetPrimAtPath(target_prim_str)
    if not target_prim:
        hou.ui.displayMessage(f"Find Invalid Prim of Given Path:{target_prim_str}")
        return
    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.EarliestTime(), ["default", "render"])
    bounds = bbox_cache.ComputeLocalBound(target_prim).GetBox()

    camera_to_use = existing_camera_path if buse_existing_camera else camera_path

    camera_ref = None

    if buse_existing_camera:
        prim_of_given_path = stage.GetPrimAtPath(camera_to_use)
        if prim_of_given_path and prim_of_given_path.IsA(UsdGeom.Camera):
            camera_ref = UsdGeom.Camera(prim_of_given_path)
        else:
            raise hou.NodeError(f"Existing camera not found at{camera_to_use}")
    else:
        camera_ref = UsdGeom.Camera.Define(stage, camera_path)
        camera_ref.GetHorizontalApertureAttr().Set(10.0)
        camera_ref.GetVerticalApertureAttr().Set(10.0)
        camera_ref.GetFocalLengthAttr().Set(35.0)
        camera_ref.GetClippingRangeAttr().Set(Gf.Vec2f(0.01, 10000.0))

    # 静态预览图
    if not banimate:
        if buse_existing_camera:
            main_xform_camera = UsdGeom.Xformable(camera_ref)
            print(main_xform_camera)
            temp_stage = Usd.Stage.CreateInMemory()
            # 因为变换不好手写，建一个系统临时对象，然后把临时对象的变换拷贝出来
            temp_camera = _create_framed_camera_(
                temp_stage, bounds, camera_yaw, camera_pitch, arm_length
            )
            temp_xform = UsdGeom.Xformable(temp_camera)
            for xform_op in temp_xform.GetOrderedXformOps():
                # 查找对象的xform忽略父级
                # print(xform_op.GetOpName())
                if xform_op.GetOpName().endswith("frameToBounds"):
                    matrix = xform_op.Get()
                    print(matrix)
                    trans_Op = main_xform_camera.AddTransformOp(
                        opSuffix="orbitTransform"
                    )
                    trans_Op.Set(matrix)
                    break
        else:
            _create_framed_camera_(stage, bounds, camera_yaw, camera_pitch, arm_length)
    # 动态预览动画
    else:
        for frame in range(frames):
            current_frame = frame + start_frame
            time_code = Usd.TimeCode(current_frame)
            current_yaw = camera_yaw + (frame * 360.0 / frames)

            temp_stage = Usd.Stage.CreateInMemory()
            temp_camera = _create_framed_camera_(
                temp_stage, bounds, current_yaw, camera_pitch, arm_length
            )
            temp_xform = UsdGeom.Xformable(temp_camera)

            for xform_op in temp_camera.GetOrderedXformOps():
                if xform_op.GetOpName().endswith("frameToBounds"):
                    matrix = xform_op.Get()
                    main_xform_camera = UsdGeom.Xformable(camera_ref)
                    if frame == 0:
                        trans_Op = main_xform_camera.AddTransformOp(
                            opSuffix="orbitTransform"
                        )
                        trans_Op.Set(matrix)
                    else:
                        # 已经有这个属性直接变换就行
                        for op in main_xform_camera.GetOrderedXformOps():
                            if op.GetOpName().endswith("orbitTransform"):
                                op.Set(matrix, time_code)
                                break
                    break


def _create_lookdev_prameters_(node: hou.OpNode):
    """
    给节点创建lookdev参数

    :param node: 调节目标参数
    :type node: hou.OpNode
    """
    node_ptg = node.parmTemplateGroup()

    # 如果存在对应参数则认为已经创建过
    find_parm = node_ptg.find("target_str")
    if find_parm:
        return

    camera_folder = hou.FolderParmTemplate(
        name="camera_folder",
        label="LookDev Camera Settings",
        folder_type=hou.folderType.Simple,
    )

    buse_existing_camera = hou.ToggleParmTemplate(
        name="buse_existing_camera", 
        label="Use Existing Camera",
        default_value=False
    )

    camera_path_string = hou.StringParmTemplate(
        name="existing_camera_path",
        label="Existing Camera Path",
        num_components=1,
        disable_when="{buse_existing_camera==0}",
    )

    target_str = hou.StringParmTemplate(
        name="target_str", label="Target Prim", num_components=1
    )

    camera_str = hou.StringParmTemplate(
        name="camera_path",
        label="Camera Path",
        num_components=1,
        default_value=("/ThumbnailCamera",),
    )

    rot_yaw_float = hou.FloatParmTemplate(
        name="yaw",
        label="Camera Yaw",
        num_components=1,
        default_value=(0,),
        min=-180.0,
        max=180.0,
    )

    rot_pitch_float = hou.FloatParmTemplate(
        name="pitch",
        label="Camera Pitch",
        num_components=1,
        default_value=(0,),
        min=-90.0,
        max=90.0,
    )

    camera_arm_length = hou.FloatParmTemplate(
        name="arm_Length",
        label="Camera Arm Length",
        num_components=1,
        default_value=(0,),
        min=0.0,
        max=20.0,
    )

    camera_folder.addParmTemplate(target_str)
    camera_folder.addParmTemplate(camera_str)
    camera_folder.addParmTemplate(buse_existing_camera)
    camera_folder.addParmTemplate(camera_path_string)
    camera_folder.addParmTemplate(rot_yaw_float)
    camera_folder.addParmTemplate(rot_pitch_float)
    camera_folder.addParmTemplate(camera_arm_length)
    node_ptg.append(camera_folder)

    animated_cam_folder = hou.FolderParmTemplate(
        name="animated_folder",
        label="Lookdev Animated Camera Settings",
        folder_type=hou.folderType.Simple,
    )

    camera_folder.addParmTemplate(animated_cam_folder)

    banimate_toggle = hou.ToggleParmTemplate(name="banimate", label="Animate")

    num_frames = hou.IntParmTemplate(
        name="frames",
        label="Number of Frames",
        num_components=1,
        default_value=(60,),
        min=30,
        max=1000,
        disable_when="{banimate==0}",
    )

    start_frame = hou.IntParmTemplate(
        name="start_frame",
        label="Start Frame",
        default_value=(0,),
        num_components=1,
        disable_when="{banimate==0}",
    )

    animated_cam_folder.addParmTemplate(banimate_toggle)
    animated_cam_folder.addParmTemplate(num_frames)
    animated_cam_folder.addParmTemplate(start_frame)
    node_ptg.append(animated_cam_folder)

    node.setParmTemplateGroup(node_ptg)


def _create_framed_camera_(in_stage, in_bounds, in_yaw, in_pitch, in_distance):
    """
    Docstring for _create_framed_camera

    :param stage: targetStage
    :param bounds: Prim Bound
    :param yaw: Camera Rotation Yaw
    :param pitch: Camera Rotation Pitch
    :param distance: Camera Distance
    """

    temp_camera = assetutils.createFramedCameraToBounds(
        stage=in_stage,
        bounds=in_bounds,
        cameraprimpath="/TempCamera",
        rotatex=25 + in_pitch,
        rotatey=-35 + in_yaw,
        fitbounds=1.3,
        offsetdistance=in_distance,
    )
    return temp_camera


def import_mesh_and_create_lookdev():
    """
    整体导入
    """
    # 导入模型
    component_node = compbuilder.create_usd_comp_builder("")
    print(component_node)
    if not component_node:
        raise ValueError("Fail to Create Component Builder,Quit")
        return
    component_node.setSelected(True)
    stage: hou.LopNetwork = hou.node("/stage")
    python_node= stage.createNode("pythonscript", "lookdev_config")
    code = """
import importlib
from tools import CreateUSDLookDev as lookdev

importlib.reload(lookdev)
lookdev.create_lookdev_camera()
"""
    python_node.parm("python")._set(code)
    python_node.setInput(0,component_node)     
    graftbranches_node = lightbuilder.create_preview_lights(python_node)
    if not graftbranches_node:
        raise ValueError("Fail to Create Light Env,Quit")
        return
    graftbranches_node.setInput(0,python_node)
