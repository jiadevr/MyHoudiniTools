import hou
import sys
import os
import numpy as np

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import my_houdini_utils as utils


def create_preview_lights(in_target_node):
    """
    在当前节点创建三盏灯
    Return:
        None or graftbranches Node (last node)
    """
    if not utils.is_in_solaris():
        hou.ui.displayMessage(
            "Current Operation Is Not In LOPNetwork,Quit",
            severity=hou.severityType.Error,
        )
        return None

    target_node: hou.LopNode = in_target_node if in_target_node else hou.selectedNodes()[0]

    if not target_node:
        hou.ui.displayMessage(
            "Please Select node of 'compontent output'", severity=hou.severityType.Error
        )
        return None
    bound_info: dict = utils.get_prim_bounds(target_node)

    if bound_info["bbox"] == None:
        hou.ui.displayMessage(
            f"Find Null Geo in {target_node.path()}", severity=hou.severityType.Error
        )
        return None

    center = bound_info["center"]
    bound_info["center"]
    size = bound_info["size"]
    max_dimension = max(size)

    key_light_pos = hou.Vector3(
        center[0] - max_dimension * 1,
        center[1] + max_dimension * 1,
        center[2] + max_dimension * 0.5,
    )
    fill_light_pos = hou.Vector3(
        center[0] + max_dimension * 1,
        center[1] + max_dimension * 1,
        center[2] + max_dimension * 0.5,
    )
    back_light_pos = hou.Vector3(
        center[0] - max_dimension * 1,
        center[1] + max_dimension * 1,
        center[2] - max_dimension * 0.5,
    )

    stage= hou.node("/stage")
    nodes_to_layout=[]

    key_light=stage.createNode("light::2.0","key_light")
    key_light.parmTuple("t")._set(key_light_pos)
    key_light.parm("xn__inputsintensity_i0a")._set(4)
    nodes_to_layout.append(key_light)

    fill_light=stage.createNode("light::2.0","fill_light")
    fill_light.parmTuple("t")._set(fill_light_pos)
    fill_light.parm("xn__inputsintensity_i0a")._set(2)
    fill_light.parmTuple("xn__inputscolor_zta")._set((0.8,0.8,1))
    nodes_to_layout.append(fill_light)

    back_light=stage.createNode("light::2.0","back_light")
    back_light.parmTuple("t")._set(back_light_pos)
    back_light.parm("xn__inputsintensity_i0a")._set(2)
    back_light.parmTuple("xn__inputscolor_zta")._set((1,0.7,0.7))
    nodes_to_layout.append(back_light)

    # 设置旋转
    for light in (key_light,fill_light,back_light):
        light.parm("lighttype")._set(4)
        light_position=hou.Vector3(light.parmTuple("t").eval())
        light_dir=center-light_position
        x_angle_pitch=np.arctan2(light_dir[1],np.sqrt(light_dir[0]**2+light_dir[2]**2))
        y_angle_yaw=np.arctan2(-light_dir[0],-light_dir[2])

        light.parmTuple("r")._set((np.degrees(x_angle_pitch),np.degrees(y_angle_yaw),0))

    # 辅助节点
    xform_node=stage.createNode("xform","lights_transform")
    nodes_to_layout.append(xform_node)
    
    light_mixer:hou.OpNode=stage.createNode("lightmixer","light_mixer")
    mixer_ptg=light_mixer.parmTemplateGroup()
    settings_folder=hou.FolderParmTemplate(name="settings_folder",label="Settings",folder_type=hou.folderType.Simple)
    settings_str=hou.StringParmTemplate(name="setting_layout",label="Layout",num_components=1)
    settings_folder.addParmTemplate(settings_str)
    mixer_ptg.append(settings_folder)
    light_mixer.setParmTemplateGroup(mixer_ptg)
    light_parm=('['+
          '{"type": "LightItem", "path": "/lights/key_light", "prim_path": "/lights/key_light", "rgb": [55, 55, 55], "controls": ["buttons"], "contents": []},'+
          '{"type": "LightItem", "path": "/lights/fill_light", "prim_path": "/lights/fill_light", "rgb": [55, 55, 55], "controls": ["buttons"], "contents": []},'+
          '{"type": "LightItem", "path": "/lights/back_light", "prim_path": "/lights/back_light", "rgb": [55, 55, 55], "controls": ["buttons"], "contents": []}'+
          ']')
    light_mixer.parm("setting_layout")._set(light_parm)
    nodes_to_layout.append(light_mixer)

    graft_branch=stage.createNode("graftbranches","point_merge")
    graft_branch.parm("srcprimpath1")._set("/")
    nodes_to_layout.append(graft_branch)

    # 设置连接关系
    fill_light.setInput(0,key_light)
    back_light.setInput(0,fill_light)
    xform_node.setInput(0,back_light)
    light_mixer.setInput(0,xform_node)
    graft_branch.setInput(0,target_node)
    graft_branch.setInput(1,light_mixer)

    # 设置排布
    graft_node_pos:hou.Vector2=graft_branch.moveToGoodPosition()
    graft_node_pos=hou.Vector2(graft_node_pos.x()-2.0,graft_node_pos.y()+2.0)
    graft_branch.setPosition(graft_node_pos)
    stage.layoutChildren(items=nodes_to_layout)

    return graft_branch

