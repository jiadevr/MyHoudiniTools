import hou
import os
import pdb


def create_usd_comp_builder(in_asset_path: str):
    """
    创建usd ComponentBuilder节点组

    :param in_asset_path: 目标几何体路径
    :type asset_path: str
    """
    if in_asset_path == "":
        in_asset_path = hou.ui.selectFile(
            title="Select Target Geometry File",
            file_type=hou.fileType.Geometry,
            multiple_select=False,
        )

    # 转译宏
    in_asset_path = hou.text.expandString(in_asset_path)
    if os.path.exists(in_asset_path):
        try:
            # 注意这个创建在stage而不是obj/stage需要在顶部导航栏选择OtherSubnetwork定位
            parent_subnet: hou.OpNode = hou.node("/stage")
            # 假定纹理文件在模型文件同级的map文件夹中
            parent_path, geo_file_name = os.path.split(in_asset_path)
            # 提取纹理地址和模型名称
            image_path = os.path.join(parent_path, "map").replace(os.sep, "/")
            geo_name = geo_file_name.split(".")[0]
            geo_extension = geo_file_name.split(".")[-1]
            # 创建componentBuilder中的其他节点
            comp_geo_node: hou.OpNode = parent_subnet.createNode(
                "componentgeometry", f"{geo_name}_geo"
            )
            mat_lib_node: hou.OpNode = parent_subnet.createNode(
                "materiallibrary", f"{geo_name}_mtl"
            )
            mat_assign_node: hou.OpNode = parent_subnet.createNode(
                "componentmaterial", f"{geo_name}_assign"
            )
            output_node: hou.OpNode = parent_subnet.createNode(
                "componentoutput", geo_name
            )
            # 设置节点属性
            comp_geo_node.parm("geovariantname")._set(geo_name)
            mat_lib_node.parm("matpathprefix")._set("/ASSET/mtl/")
            mat_assign_node.parm("nummaterials")._set(0)

            # 连接节点关系
            mat_assign_node.setInput(0, comp_geo_node)
            mat_assign_node.setInput(1, mat_lib_node)
            output_node.setInput(0, mat_assign_node)

            parent_subnet.layoutChildren(
                [comp_geo_node, mat_lib_node, mat_assign_node, output_node]
            )
            output_node.setSelected(True)
            
            # 设置模型处理
            _prepare_geo_asset_(comp_geo_node,geo_name,geo_extension,in_asset_path,output_node)

            # 设置材质模型映射节点连接
            edit_subnet = mat_assign_node.node("edit")
            output_node: hou.OpNode = edit_subnet.node("output0")

            assign_node: hou.OpNode = edit_subnet.createNode(
                "assignmaterial", f"{geo_name}_assign"
            )
            assign_node.setParms(
                {
                    "primpattern1": "%type:Mesh",
                    "matspecmethod1": 2,
                    "matspecvexpr1": '"/ASSET/mtl/"+@primname;',
                    "bindpurpose1": "full",
                }
            )
            assign_node.setInput(0, edit_subnet.indirectInputs()[0])
            output_node.setInput(0, assign_node)

        except:
            pass
    else:
        hou.ui.displayMessage(f"{in_asset_path} Not Existed!")

def _prepare_geo_asset_(in_parent_node:hou.OpNode,in_geo_name:str,in_file_extension:str,in_path:str,in_out_node:hou.OpNode):
    '''
    预处理模型，包括位置调整、name覆盖、孤点删除、创建代理几何体、设置代理几何体颜色、创建凸包
    
    :param in_parent_node: stage subnet 引用
    :param in_geo_name: 导入模型名称
    :param in_file_extension: 导入模型后缀名
    :param in_path: 导入路径
    :param in_out_node: stage subnet输出节点引用
    '''
    # 编辑目标，把节点直接拖进shell可以看到
    edit_target_node:hou.OpNode=hou.node(in_parent_node.path()+"/sopnet/geo")
    children_nodes=[]
    # 输出节点定位
    default_output=edit_target_node.node("default")
    proxy_output=edit_target_node.node("proxy")
    sim_output=edit_target_node.node("simproxy")

    # default路径节点组
    print("Beign Default Generation")
    if in_file_extension.lower() in ("fbx","obj","bgeo","bgeo.sc"):
        file_import_node:hou.OpNode=edit_target_node.createNode("file",f"import_{in_geo_name}")
        file_import_node.parm("file")._set(in_path)
    elif in_file_extension.lower() =="abc":
        file_import_node:hou.OpNode=edit_target_node.createNode("alembic",f"import_{in_geo_name}")
        file_import_node.parm("fileName")._set(in_path)
    else:
        raise ValueError("Unsupport geo format")
    
    children_nodes.append(in_file_extension)
    match_size_node:hou.OpNode=edit_target_node.createNode("matchsize")
    match_size_node.setParms({
        "justify_x":0,
        "justify_y":1,
        "goal_y":1
    })
    children_nodes.append(match_size_node)
    normalize_name_node:hou.OpNode=edit_target_node.createNode("attribwrangle","normlize_name_attr")
    normalize_name_node.setParms({
        "class":1,
        "snippet":'''string material_name[]=split(s@shop_materialpath,"/");
s@name=material_name[-1];'''
    })
    children_nodes.append(normalize_name_node)
    delete_attr_node:hou.OpNode=edit_target_node.createNode("attribdelete","remove_attri")
    delete_attr_node.setParms({
        "negate":True,
        "ptdel":"N P",
        "vtxdel":"uv",
        "primdel":"name"
    })
    children_nodes.append(delete_attr_node)
    clean_isolated_point_node:hou.OpNode=edit_target_node.createNode("add","clean_isolated_point")
    clean_isolated_point_node.parm("remove")._set(True)
    children_nodes.append(delete_attr_node)
    
    match_size_node.setInput(0,file_import_node)
    normalize_name_node.setInput(0,match_size_node)
    delete_attr_node.setInput(0,normalize_name_node)
    clean_isolated_point_node.setInput(0,delete_attr_node)
    default_output.setInput(0,clean_isolated_point_node)
    print("End Default Generation")
    

    # proxy节点组路径
    print("Beign Proxy Generation")
    #pdb.set_trace()
    poly_reduce_node:hou.OpNode=edit_target_node.createNode("polyreduce::2.0","reduce_poly")
    poly_reduce_node.parm("percentage")._set(5.0)
    children_nodes.append(poly_reduce_node)
    copy_asset_name_node:hou.OpNode=edit_target_node.createNode("attribwrangle","copy_asset_name")
    copy_asset_ptg= copy_asset_name_node.parmTemplateGroup()
    asset_name_str=hou.StringParmTemplate(name="asset_name",label="AssetName",num_components=1)
    copy_asset_ptg.insertAfter("class",asset_name_str)
    copy_asset_name_node.setParmTemplateGroup(copy_asset_ptg)
    output_asset_relative_path=copy_asset_name_node.relativePathTo(in_out_node)
    expression=f'chs("{output_asset_relative_path}/rootprim")'
    copy_asset_name_node.setParms({
        "class":1,
        "asset_name":expression,
        "snippet":'s@asset_name=chs("asset_name");'
    })
    children_nodes.append(copy_asset_name_node)
    unique_color_node:hou.OpNode=edit_target_node.createNode("color","unique_color")
    unique_color_node.setParms({
        "class":1,
        "colortype":4,
        "rampattribute":"asset_name"
    })
    children_nodes.append(unique_color_node)
    attri_transfor_node:hou.OpNode=edit_target_node.createNode("attribpromote","trans_cd_to_point")
    attri_transfor_node.setParms({
        "inname":"Cd"
        #"inclass":"primitive"
    })
    children_nodes.append(attri_transfor_node)
    clean_attri_node:hou.OpNode=edit_target_node.createNode("attribdelete","remove_attri")
    clean_attri_node.parm("primdel")._set("asset_name")
    children_nodes.append(clean_attri_node)

    poly_reduce_node.setInput(0,clean_isolated_point_node)
    copy_asset_name_node.setInput(0,poly_reduce_node)
    unique_color_node.setInput(0,copy_asset_name_node)
    attri_transfor_node.setInput(0,unique_color_node)
    clean_attri_node.setInput(0,attri_transfor_node)
    proxy_output.setInput(0,clean_attri_node)
    print("End Proxy Generation")

    edit_target_node.layoutChildren(children_nodes)


