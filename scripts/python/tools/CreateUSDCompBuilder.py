import hou
import os
import random
import colorsys
import tools.tex_to_mtlx as tex_to_mtlx

# import pprint
# import pdb


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
            image_path = os.path.join(parent_path, "maps").replace(os.sep, "/")
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
            _create_comment_node_(
                geo_name, (comp_geo_node, mat_lib_node, mat_assign_node, output_node)
            )
            output_node.setSelected(True)

            # 设置模型处理
            _prepare_geo_asset_(
                comp_geo_node, geo_name, geo_extension, in_asset_path, output_node
            )

            # 创建材质
            _create_materials_(mat_lib_node, image_path)

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

        except Exception as error:
            hou.ui.displayMessage(
                f"Fail to Create,Error {error}", severity=hou.severityType.Error
            )
    else:
        hou.ui.displayMessage(
            f"{in_asset_path} Not Existed!", severity=hou.severityType.Error
        )


def _prepare_geo_asset_(
    in_parent_node: hou.OpNode,
    in_geo_name: str,
    in_file_extension: str,
    in_path: str,
    in_out_node: hou.OpNode,
):
    """
    预处理模型，包括位置调整、name覆盖、孤点删除、创建代理几何体、设置代理几何体颜色、创建凸包

    :param in_parent_node: stage subnet 引用
    :param in_geo_name: 导入模型名称
    :param in_file_extension: 导入模型后缀名
    :param in_path: 导入路径
    :param in_out_node: stage subnet输出节点引用
    """
    # 编辑目标，把节点直接拖进shell可以看到
    edit_target_node: hou.OpNode = hou.node(in_parent_node.path() + "/sopnet/geo")
    children_nodes = []
    # 输出节点定位
    default_output = edit_target_node.node("default")
    proxy_output = edit_target_node.node("proxy")
    sim_output = edit_target_node.node("simproxy")

    # default路径节点组
    print("Beign Default Generation")
    if in_file_extension.lower() in ("fbx", "obj", "bgeo", "bgeo.sc"):
        file_import_node: hou.OpNode = edit_target_node.createNode(
            "file", f"import_{in_geo_name}"
        )
        file_import_node.parm("file")._set(in_path)
    elif in_file_extension.lower() == "abc":
        file_import_node: hou.OpNode = edit_target_node.createNode(
            "alembic", f"import_{in_geo_name}"
        )
        file_import_node.parm("fileName")._set(in_path)
    else:
        raise ValueError("Unsupport geo format")

    children_nodes.append(in_file_extension)
    match_size_node: hou.OpNode = edit_target_node.createNode("matchsize")
    match_size_node.setParms({"justify_x": 0, "justify_y": 1, "goal_y": 1})
    children_nodes.append(match_size_node)
    normalize_name_node: hou.OpNode = edit_target_node.createNode(
        "attribwrangle", "normlize_name_attr"
    )
    normalize_name_node.setParms(
        {
            "class": 1,
            "snippet": """string material_name[]=split(s@shop_materialpath,"/");
s@name=material_name[-1];""",
        }
    )
    children_nodes.append(normalize_name_node)
    delete_attr_node: hou.OpNode = edit_target_node.createNode(
        "attribdelete", "remove_attri"
    )
    delete_attr_node.setParms(
        {"negate": True, "ptdel": "N P", "vtxdel": "uv", "primdel": "name"}
    )
    children_nodes.append(delete_attr_node)
    clean_isolated_point_node: hou.OpNode = edit_target_node.createNode(
        "add", "clean_isolated_point"
    )
    clean_isolated_point_node.parm("remove")._set(True)
    children_nodes.append(delete_attr_node)

    match_size_node.setInput(0, file_import_node)
    normalize_name_node.setInput(0, match_size_node)
    delete_attr_node.setInput(0, normalize_name_node)
    clean_isolated_point_node.setInput(0, delete_attr_node)
    default_output.setInput(0, clean_isolated_point_node)
    print("End Default Generation")

    # proxy节点组路径
    print("Beign Proxy Generation")
    # pdb.set_trace()
    poly_reduce_node: hou.OpNode = edit_target_node.createNode(
        "polyreduce::2.0", "reduce_poly"
    )
    poly_reduce_node.parm("percentage")._set(5.0)
    children_nodes.append(poly_reduce_node)
    copy_asset_name_node: hou.OpNode = edit_target_node.createNode(
        "attribwrangle", "copy_asset_name"
    )
    copy_asset_ptg = copy_asset_name_node.parmTemplateGroup()
    asset_name_str = hou.StringParmTemplate(
        name="asset_name", label="AssetName", num_components=1
    )
    copy_asset_ptg.insertAfter("class", asset_name_str)
    copy_asset_name_node.setParmTemplateGroup(copy_asset_ptg)
    output_asset_relative_path = copy_asset_name_node.relativePathTo(in_out_node)
    expression = f'chs("{output_asset_relative_path}/rootprim")'
    copy_asset_name_node.setParms(
        {
            "class": 1,
            "asset_name": expression,
            "snippet": 's@asset_name=chs("asset_name");',
        }
    )
    children_nodes.append(copy_asset_name_node)
    unique_color_node: hou.OpNode = edit_target_node.createNode("color", "unique_color")
    unique_color_node.setParms(
        {"class": 1, "colortype": 4, "rampattribute": "asset_name"}
    )
    children_nodes.append(unique_color_node)
    attri_transfor_node: hou.OpNode = edit_target_node.createNode(
        "attribpromote", "trans_cd_to_point"
    )
    attri_transfor_node.setParms(
        {
            "inname": "Cd"
            # "inclass":"primitive"
        }
    )
    children_nodes.append(attri_transfor_node)
    clean_attri_node: hou.OpNode = edit_target_node.createNode(
        "attribdelete", "remove_attri"
    )
    clean_attri_node.parm("primdel")._set("asset_name")
    children_nodes.append(clean_attri_node)

    poly_reduce_node.setInput(0, clean_isolated_point_node)
    copy_asset_name_node.setInput(0, poly_reduce_node)
    unique_color_node.setInput(0, copy_asset_name_node)
    attri_transfor_node.setInput(0, unique_color_node)
    clean_attri_node.setInput(0, attri_transfor_node)
    proxy_output.setInput(0, clean_attri_node)
    print("End Proxy Generation")

    # Sim Proxy节点组路径
    print("Begin Sim Proxy Generation")
    convex_creator = _create_sim_proxy_(edit_target_node)
    convex_creator.setInput(0, poly_reduce_node)
    sim_output.setInput(0, convex_creator)
    print("End Sim Proxy Generation")
    edit_target_node.layoutChildren()


def _create_sim_proxy_(in_parent_node: hou.OpNode) -> hou.OpNode:
    convex_creator_node: hou.OpNode = in_parent_node.createNode(
        "python", "convex_creator"
    )
    # 添加输入参数
    convex_creator_ptg = convex_creator_node.parmTemplateGroup()
    bnormalized_toggle = hou.ToggleParmTemplate(
        name="normalize", label="Normalize", default_value=True
    )
    convex_creator_ptg.append(bnormalized_toggle)

    bfilp_normal_toggle = hou.ToggleParmTemplate(
        name="filp_normal", label="FilpNormal", default_value=True
    )
    convex_creator_ptg.append(bfilp_normal_toggle)

    bsimplify_toggle = hou.ToggleParmTemplate(
        name="simplify_toggle", label="Simplify", default_value=True
    )
    convex_creator_ptg.append(bsimplify_toggle)

    level_detail = hou.FloatParmTemplate(
        name="level_detail",
        label="LevelOfDetail",
        num_components=1,
        # 注意需要一个tuple，后边要带逗号
        default_value=(1.0,),
        disable_when="{bsimplify_toggle==0}",
    )
    convex_creator_ptg.append(level_detail)

    convex_creator_node.setParmTemplateGroup(convex_creator_ptg)
    code = """
import modules.geometry_utils as geoutil

node=hou.pwd()
geo=node.geometry()

bnormalize=node.parm('normalize').eval()
bfilp_normal=node.parm('filp_normal').eval()
bsimplify=node.parm('simplify_toggle').eval()
lod=node.parm('level_detail').eval()

points=[point.position() for point in geo.points()]
geoutil.create_convex_cull(geo,points,bnormalize,bfilp_normal,bsimplify,lod)
"""
    convex_creator_node.parm("python")._set(code)

    return convex_creator_node


def _create_materials_(in_parent_node: hou.OpNode, in_tex_folder: str) -> bool:
    # 复用tex to mtlx内容
    print("Begin Creating Material")
    if not os.path.exists(in_tex_folder):
        raise ValueError(f"Invalid Path {in_tex_folder}")
        return False
    try:
        texture_manager = tex_to_mtlx.TxToMtlx()
        if texture_manager._contain_any_image_file_(in_tex_folder):

            material_dict = texture_manager._collect_images_in_dir(in_tex_folder)
            # pprint.pprint(material_dict)
            if len(material_dict) > 0:
                if not in_tex_folder.endswith("/"):
                    in_tex_folder = in_tex_folder + "/"
                print(in_tex_folder)
                public_data = {
                    "b_use_mtlTX": False,
                    "node_path": in_parent_node.path(),
                    "node_ref": in_parent_node,
                    "tex_folder_path": in_tex_folder,
                }
                # pdb.set_trace()
                for material_name, material_data in material_dict.items():
                    print(f"{material_name} - {material_data}")
                    material_creator = tex_to_mtlx.MtlxMaterial(
                        mat_name=material_name,
                        **public_data,
                        all_texture_dict=material_dict,
                    )
                    material_creator.create_material()
                print("End Creating Material")
                return True
        else:
            raise ValueError(f"The Path {in_tex_folder} contains none valid texture")

    except Exception as error:
        raise ValueError(f"Fail to create material,Error {error}")
    return False


def _get_random_colors_in_scheme() -> tuple[hou.Color, hou.Color]:
    """
    生成同一色系的两个颜色
    :return: 返回tuple,包含两个元素,分别是主色和副色
    :rtype: tuple[Color]
    """
    base_color_r = random.random() * 0.5 + 0.5
    base_color_g = random.random() * 0.5 + 0.5
    base_color_b = random.random() * 0.5 + 0.5

    main_color = hou.Color(base_color_r, base_color_g, base_color_b)
    h, s, v = colorsys.rgb_to_hsv(base_color_r, base_color_g, base_color_b)
    secondary_r, secondary_g, secondary_b = colorsys.hsv_to_rgb(h, s * 0.5, v)
    secondary_color = hou.Color(secondary_r, secondary_g, secondary_b)

    return main_color, secondary_color


def _create_comment_node_(in_asset_name: str, in_wrapped_nodes: tuple[hou.OpNode, ...]):
    if len(in_wrapped_nodes) <= 0:
        raise RuntimeError(
            "Fail to Create Common Node, The Passedin Node Tuple Was Empty"
        )
        return
    parent_network: hou.OpNode = in_wrapped_nodes[0].parent()
    if not parent_network:
        raise RuntimeError("Fail to Create Common Node, Get Parent Network Failed")
        return

    parent_comment_box = parent_network.createNetworkBox()

    inner_comment_box = parent_network.createNetworkBox()
    parent_comment_box.addItem(inner_comment_box)
    name_sticky_node = parent_network.createStickyNote()
    parent_comment_box.addItem(name_sticky_node)

    # 添加节点组到commentBox并计算中点
    count_reciprocal = 1.0 / len(in_wrapped_nodes)
    nodes_centroid: hou.Vector2 = hou.Vector2((0.0,0.0))
    for node in in_wrapped_nodes:
        inner_comment_box.addItem(node)
        nodes_centroid = nodes_centroid + node.position() * count_reciprocal

    inner_comment_box.setPosition(nodes_centroid)
    inner_comment_box.fitAroundContents()
    parent_comment_box.setPosition(nodes_centroid)

    nodes_bounding_size = inner_comment_box.size()
    sticky_height = 0.75
    name_sticky_node.setSize((nodes_bounding_size.x(), sticky_height))
    sticky_pos: hou.Vector2 = inner_comment_box.position()
    #位置需要调整
    sticky_height_offset=nodes_bounding_size.y()+sticky_height+0.25
    sticky_offset:hou.Vector2=hou.Vector2((0.0,sticky_height_offset))
    print(sticky_offset)
    sticky_pos=sticky_pos+sticky_offset
    name_sticky_node.setPosition(sticky_pos)

    parent_comment_box.fitAroundContents()

    # 设置文字和颜色
    parent_comment_box.setComment(in_asset_name)
    name_sticky_node.setText(in_asset_name)
    name_sticky_node.setTextSize(0.35)

    parent_comment_box.setColor(hou.Color(0.189,0.189,0.189))
    node_color, text_color = _get_random_colors_in_scheme()
    inner_comment_box.setColor(node_color)
    name_sticky_node.setColor(node_color)
    name_sticky_node.setTextColor(text_color)
