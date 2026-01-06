import hou
import os
import re
import pprint
import pdb
from collections import defaultdict
from PySide6 import QtCore, QtUiTools, QtWidgets, QtGui


class TxToMtlx(QtWidgets.QMainWindow):

    SUPPORT_IMAGE_FORMAT = (
        ".jpg",
        ".jpge",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".exr",
        ".targa"
    )
    ORDINARY_TEX_REGEX_PATTERN = re.compile(r"(\d+[Kk])")
    UDIM_TEX_REGEX_PATTERN = re.compile(r"(_\d{4})")
    TEX_TYPE = (
        "diffuse",
        "diff",
        "albedo",
        "alb",
        "base",
        "col",
        "color",
        "basecolor",
        "metallic",
        "metalness",
        "metal",
        "mlt",
        "met",
        "speculatiry",
        "specular",
        "spec",
        "spc",
        "roughness",
        "rough",
        "rgh",
        "gloss",
        "glossy",
        "glossiness",
        "transmission",
        "transparency",
        "trans",
        "translucency",
        "sss",
        "emission",
        "emissive",
        "emit",
        "emm",
        "opacity",
        "opac",
        "alpha",
        "ambient_occlusion",
        "ao",
        "occlusion",
        "cavity",
        "bump",
        "bmp",
        "displacement",
        "displace",
        "disp",
        "dsp",
        "heightmap",
        "height",
        "user",
        "mask",
        "normal",
        "nor",
        "nrm",
        "nrml",
        "norm"
    )

    def __init__(self):
        super().__init__()

        # SETUP CENTRAL WIDGET FOR UI
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)

        # WINDOW PROPERTIES
        self.setWindowTitle("TexToMtlX Tool")
        self.resize(340, 570)
        self.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        ## DATA
        self.mtlTX: bool = False

        self._setup_help_section()
        self._setup_material_section()
        self._setup_list_section()
        self._setup_create_section()
        self._setup_connections()

        self.material_lib_path = None
        self.material_lib_node: hou.OpNode = hou.node(
            "/obj/lopnet1/materiallibrary1"
        )  # <---------Remove After Test
        # 用户选择的纹理文件夹路径
        self.tex_folder: str = ""
        self.tex_collection: dict = {}

    def _setup_help_section(self):
        """Setup the help button section"""
        self.help_layout = QtWidgets.QVBoxLayout()

        self.bt_instructions = QtWidgets.QPushButton("Instructions")
        self.bt_instructions.setMinimumHeight(80)
        self.help_layout.addWidget(self.bt_instructions)
        self.main_layout.addLayout(self.help_layout)

    def _setup_material_section(self):
        """Setup the material library section"""

        self.material_layout = QtWidgets.QGridLayout()
        # MATERIAL LIBRARY
        self.bt_lib = QtWidgets.QPushButton("Material Lib")
        self.bt_lib.setMinimumHeight(70)
        self.material_layout.addWidget(self.bt_lib, 0, 0, 2, 1)
        # TX CHECKBOX
        self.checkbox = QtWidgets.QCheckBox("Convert to TX?")
        self.checkbox.setEnabled(False)
        self.material_layout.addWidget(self.checkbox, 0, 1)
        # OPEN FOLDER
        self.bt_open_folder = QtWidgets.QPushButton("Open Folder")
        self.bt_open_folder.setMinimumHeight(40)
        self.bt_open_folder.setEnabled(True)  # <---------False After Test
        self.material_layout.addWidget(self.bt_open_folder, 1, 1)

        self.main_layout.addLayout(self.material_layout)

    def _setup_list_section(self):
        """Setup the material list section"""
        self.list_layout = QtWidgets.QVBoxLayout()

        # HEADER LAYOUT
        self.header_layout = QtWidgets.QHBoxLayout()

        self.lb_material_list = QtWidgets.QLabel("List of Materials:")
        self.bt_sel_all = QtWidgets.QPushButton("All")
        self.bt_sel_non = QtWidgets.QPushButton("Reset")

        self.bt_sel_all.setEnabled(False)
        self.bt_sel_non.setEnabled(False)

        self.header_layout.addWidget(self.lb_material_list)
        self.header_layout.addWidget(self.bt_sel_all)
        self.header_layout.addWidget(self.bt_sel_non)

        # MATERIAL LIST
        self.material_list = QtWidgets.QListView()
        self.material_list.setMinimumHeight(200)
        self.model = QtGui.QStandardItemModel()
        self.material_list.setModel(self.model)
        self.material_list.setSelectionMode(QtWidgets.QListView.MultiSelection)

        self.list_layout.addLayout(self.header_layout)
        self.list_layout.addWidget(self.material_list)
        self.main_layout.addLayout(self.list_layout)

    def _setup_create_section(self):
        """Setup the create button and progress bar section"""
        self.create_layout = QtWidgets.QVBoxLayout()

        # Create Button
        self.bt_create = QtWidgets.QPushButton("Create Materials")
        self.bt_create.setMinimumHeight(50)
        self.bt_create.setEnabled(False)

        # Progress Bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setValue(0)

        self.create_layout.addWidget(self.bt_create)
        self.create_layout.addWidget(self.progress_bar)

        self.main_layout.addLayout(self.create_layout)

    def _setup_connections(self):
        """Setup Signal Connections"""
        self.bt_instructions.clicked.connect(self._show_help_)
        self.bt_lib.clicked.connect(self._set_material_lib_)
        self.bt_open_folder.clicked.connect(self._open_file_browser_)
        self.bt_sel_all.clicked.connect(self._select_all_in_matlist_)
        self.bt_sel_non.clicked.connect(self._deselect_all_in_matlist_)
        self.bt_create.clicked.connect(self._create_materials_)
        self.checkbox.stateChanged.connect(self._change_use_mtlTX_)

    def _show_help_(self):
        message = """
        Instructions\n\n\n 
        Supports textures with and without UDIMs.nMATERIAL_TEXTURE_UDIM Or MATERIAL_TEXTURE
        \nFor example: tires_Alb_1001.tif or tires_Alb.tif
        \nNaming Convention for the textures:
        \nColor: diffuse, diff, albedo, alb, base, col, color, basecolor,
        \nMetal:metallic, metalness, metal, mlt, met,
        \nSpecular:speculatiry, specular, spec, spc,
        \nRouhness: roughness, rough, rgh,
        \nGlossiness: gloss, glossy, glossiness,
        \nTransmission:transmission, transparency, trans,
        \nSSS: translucency, sss,
        \nEmission: emission, emissive, emit, emm,
        \nOpacity:opacity, opac, alpha,
        \nAmbient Occlusion:ambient_occlusion, ao, occlusion,
        \nBump:bump, bmp,
        \nHeight:displacement, displace, disp, dsp, heightmap, height,
        \nExtra:user, mask,
        \nNormal:normal, nor, nrm, nrml, norm
        """
        hou.ui.displayMessage(message, hou.severityType.ImportantMessage)

    def _set_material_lib_(self):
        # 选择节点
        self.material_lib_path = hou.ui._selectNode(
            title="Please Select On Material Library",
            node_type_filter=hou.nodeTypeFilter.ShopMaterial,
        )[0]
        self.material_lib_node = hou.node(self.material_lib_path)
        if not self.material_lib_node:
            hou.ui.displayMessage(
                "Invalid Node Selected!,Please Select Other",
                severity=hou.severityType.Error,
            )
            return

        # 检测指定路径是否可以创建节点
        if self.material_lib_node.isInsideLockedHDA():
            hou.ui.displayMessage(
                "The Node Is Editable,Please Select Again",
                severity=hou.severityType.Error,
            )
            return
        # 启用下一步配置
        self.bt_open_folder.setEnabled(True)

    def _open_file_browser_(self):
        """
        打开包含纹理的文件路径
        """
        self.model.clear()
        folder_path: str = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Please Select Your Texture Folder"
        )
        if not os.path.exists(folder_path):
            hou.ui.displayMessage("Given Path Is Not Valid,Please Check")
            return
        # 检查给定路径中是否包含图片文件
        if not self._contain_any_image_file_(folder_path):
            hou.ui.displayMessage(
                "Given Path Doesn't Any Valid Image File,Please Check and Select Other Folder"
            )
            return
        # 查找图片信息
        self.tex_folder = folder_path
        self.tex_collection = self._collect_images_in_dir(folder_path)
        if len(self.tex_collection) == 0:
            return
        # pprint.pprint(self.tex_collection)
        # 把图片信息添加到List
        for tex_group in self.tex_collection:
            self.model.appendRow(QtGui.QStandardItem(tex_group))
        self.bt_sel_all.setEnabled(True)
        self.bt_sel_non.setEnabled(True)
        self.bt_create.setEnabled(True)

    def _contain_any_image_file_(self, in_dir_path: str) -> bool:
        """
        检查给定路径是否包含图片文件,不递归
        """
        if not os.path.exists(in_dir_path) or not os.path.isdir(in_dir_path):
            return False
        for elem in os.listdir(in_dir_path):
            current_testing_path = os.path.join(in_dir_path, elem)
            # 不递归，排除文件夹
            if not os.path.isfile(current_testing_path):
                continue
            if elem.endswith(self.SUPPORT_IMAGE_FORMAT):
                print(
                    f"Find Image File In Given Path {in_dir_path},Image File Name {elem}"
                )
                if "_" in elem:
                    print(f"Image File Name {elem} with Underscore Seperator")
                    return True
        return False

    def _collect_images_in_dir(self, in_dir_path: str) -> dict:
        # 解析文件夹中的纹理，构造一个二维字典
        if not os.path.exists(in_dir_path):
            hou.ui.displayMessage("Given Path Is Not Valid,Please Check")
            return {}
        material_collection = defaultdict(lambda: defaultdict(list))
        for elem in os.listdir(in_dir_path):
            current_testing_path = os.path.join(in_dir_path, elem)
            if not os.path.isfile(current_testing_path):
                continue
            if not elem.endswith(self.SUPPORT_IMAGE_FORMAT):
                continue
            file_name = elem.split(".")[0].lower()
            # 使用_分段
            name_keywords = file_name.split("_")
            material_name = name_keywords[0]
            # 使用关键词匹配纹理种类
            texure_type = ""
            for type in self.TEX_TYPE:
                for name_keyword in name_keywords[1:]:
                    if type in name_keyword:
                        texure_type = name_keyword
                        break
            # 没有匹配的字段，纹理不加入纹理组
            if texure_type == "":
                continue
            material_collection[material_name][texure_type].append(elem)
            # 使用正则表达式获取纹理分辨率
            tex_res = self.ORDINARY_TEX_REGEX_PATTERN.search(elem)
            if not tex_res == None:
                material_collection[material_name]["res"] = tex_res.group(1)
            # 使用正则表达式匹配UDIM
            is_UDIM = self.UDIM_TEX_REGEX_PATTERN.search(elem)
            material_collection[material_name]["UDIM"] = (
                True if is_UDIM != None else False
            )

        if len(material_collection) == 0:
            return {}
        result: dict = {}
        for name, tex_data in material_collection.items():
            result[name] = dict(tex_data)
        return result

    def _change_use_mtlTX_(self, status):
        if status == QtCore.Qt.CheckState.Checked:
            self.mtlTX = True
        else:
            self.mtlTX = False
        print(f"Use mtlTX:{self.mtlTX}")

    def _select_all_in_matlist_(self):
        # self.material_list.selectAll()
        # 另一种选择方式
        selection_model = self.material_list.selectionModel()
        for row in range(self.model.rowCount()):
            index = self.model.index(row, 0)
            selection_model.select(
                index, QtCore.QItemSelectionModel.SelectionFlag.Select
            )

    def _deselect_all_in_matlist_(self):
        self.material_list.clearSelection()

    def _create_materials_(self):
        # 重置状态
        self.progress_bar.setValue(0)
        selected_mat_items = self.material_list.selectedIndexes()
        if len(selected_mat_items) == 0:
            hou.ui.displayMessage(
                "Please Select A Least One Material", severity=hou.severityType.Error
            )
            return
        self.progress_bar.setMaximum(len(selected_mat_items))
        current_progress = 0
        base_info = {
            "b_use_mtlTX": self.mtlTX,
            "node_path": self.material_lib_path,
            "node_ref": self.material_lib_node,
            "tex_folder_path": self.tex_folder,
        }
        for item in selected_mat_items:
            item_index = item.row()
            # 这有点问题，dict的key是保序的么
            material_name = list(self.tex_collection.keys())[item_index]
            material_creator = MtlxMaterial(
                material_name, **base_info, texture_list=self.tex_collection
            )
            material_creator.create_material()

            current_progress += 1
            self.progress_bar.setValue(current_progress)

        hou.ui.displayMessage(
            "Finish Creating Material", severity=hou.severityType.Message
        )


class MtlxMaterial:
    def __init__(
        self,
        mat_name,
        b_use_mtlTX,
        node_path,
        node_ref: hou.OpNode,
        tex_folder_path,
        texture_list,
    ) -> None:
        self.mat_name = mat_name
        self.b_mtlTX = b_use_mtlTX
        self.node_path = node_path
        self.node_ref: hou.OpNode = node_ref
        self.tex_folder_path = tex_folder_path
        self.texture_list = texture_list
        self._init_constants()

    def _init_constants(self):
        self.TEXTURE_TYPE_SORTED = {
            "texturesColor": [
                "diffuse",
                "diff",
                "albedo",
                "alb",
                "base",
                "col",
                "color",
                "basecolor"
            ],
            "texturesMetal": ["metallic", "metalness", "metal", "mlt", "met"],
            "texturesSpecular": ["speculatiry", "specular", "spec", "spc"],
            "texturesRough": ["roughness", "rough", "rgh"],
            "texturesGloss": ["gloss", "glossy", "glossiness"],
            "texturesTrans": ["transmission", "transparency", "trans"],
            "texturesEmm": ["emission", "emissive", "emit", "emm"],
            "texturesAplha": ["opacity", "opac", "alpha"],
            "texturesAO": ["ambient_occlusion", "ao", "occlusion"],
            "texturesBump": ["bump", "bmp", "height"],
            "texturesDisp": ["displacement", "displace", "disp", "dsp", "heightmap"],
            "texturesExtra": ["user", "mask"],
            "texturesNormal": ["normal", "nor", "nrm", "nrml", "norm"],
            "texturesSSS": ["translucency", "sss"]
        }

    def create_material(self):
        if not (self.node_ref and self.mat_name and self.texture_list):
            return

        try:

            # TX转换等
            target_material_info = self._prepare_material_info_()
            # 构建基础subnet并改造成mtlmaterial对应的输入输出
            subnet_context = self._create_material_subnet_(target_material_info)
            # 构建mtlmaterial中的基础节点，返回接收纹理的节点
            mtlx_surface_node, mtlx_displace_node = self._create_base_nodes_in_subnet_(
                subnet_context
            )
            # UV缩放，内部UDIM短路
            place2d_nodes = self._create_place2d_(subnet_context, target_material_info)
            print(target_material_info)
            # 处理纹理
            self._process_textures_(
                subnet_context,
                target_material_info,
                mtlx_surface_node,
                mtlx_displace_node,
                place2d_nodes
            )
            # 节点布局
            self._layout_nodes_(subnet_context)
        except Exception as error:
            print(f"Error:{error}")

    def _prepare_material_info_(self):
        """
        根据传入的是否需要转成TX格式执行格式转换
        Return:
        异位修改过的self.texture_list[self.mat_name]
        返回值示例
        {
        'ao': ['old_linoleum_flooring_01_ao_2k.jpg'], 
        'res': '2k', 
        'UDIM': False, 
        'diff': ['old_linoleum_flooring_01_diff_2k.jpg'], 
        'disp': ['old_linoleum_flooring_01_disp_2k.png'], 
        'nor': ['old_linoleum_flooring_01_nor_gl_2k.jpg'], 
        'rough': ['old_linoleum_flooring_01_rough_2k.jpg']
        }
        """
        target_material_info: dict = self.texture_list[self.mat_name]
        if self.b_mtlTX:
            texture_summary = []
            for key, value in target_material_info.items():
                if key not in ("UDIM", "Size"):
                    if isinstance(value, list):
                        texture_summary.extend(value)
        # 执行TX转换操作
        return target_material_info

    def _create_material_subnet_(self, in_material_info: dict):
        """
        创建MaterialSubnet并及进行初始化
        :param in_material_info: 记录材质参数的字典
        :type in_material_info: dict
        """
        material_node_name = (
            self.mat_name + f"_{in_material_info['size']}K"
            if "size" in in_material_info
            else self.mat_name
        )
        # 检查是否已经存在同名节点
        duplicated_node = self.node_ref.node(material_node_name)

        if duplicated_node:
            duplicated_node.destroy()
        # 创建新的节点
        print("Type of Parent Node")
        print(type(self.node_ref))
        print(self.node_ref.path())
        material_node = self.node_ref.createNode("subnet", material_node_name)
        # 这两个函数返回值一样都是Node
        # subnet_as_opnode = material_node
        subnet_as_opnode = self.node_ref.node(material_node.name())
        print("Type of CreatedNode")
        print(type(subnet_as_opnode))
        # 删除不需要使用的输入输出
        old_interface = subnet_as_opnode.allItems()
        for index, _ in enumerate(old_interface):
            old_interface[index].destroy()
        # 设置需要的输入输出
        self._setup_material_parameters_(material_node)
        material_node.setMaterialFlag(True)
        # 创建Subnet内基础组成部分
        return subnet_as_opnode

    def _setup_material_parameters_(self, in_mtlx_node):
        # 对已创建的节点调用AsCode并调整
        hou_parm_template_group = hou.ParmTemplateGroup()
        # Code for parameter template
        hou_parm_template = hou.FolderParmTemplate(
            "folder1",
            "MaterialX Builder",
            folder_type=hou.folderType.Collapsible,
            default_value=0,
            ends_tab_group=False,
        )
        hou_parm_template.setTags(
            {"group_type": "collapsible", "sidefx::shader_isparm": "0"}
        )
        # Code for parameter template
        hou_parm_template2 = hou.IntParmTemplate(
            "inherit_ctrl",
            "Inherit from Class",
            1,
            default_value=([2]),
            min=0,
            max=10,
            min_is_strict=False,
            max_is_strict=False,
            look=hou.parmLook.Regular,
            naming_scheme=hou.parmNamingScheme.Base1,
            menu_items=(["0", "1", "2"]),
            menu_labels=(["Never", "Always", "Material Flag"]),
            icon_names=([]),
            item_generator_script="",
            item_generator_script_language=hou.scriptLanguage.Python,
            menu_type=hou.menuType.Normal,
            menu_use_token=False,
        )
        hou_parm_template.addParmTemplate(hou_parm_template2)
        # Code for parameter template
        hou_parm_template2 = hou.StringParmTemplate(
            "shader_referencetype",
            "Class Arc",
            1,
            default_value=(
                [
                    "n = hou.pwd()\nn_hasFlag = n.isMaterialFlagSet()\ni = n.evalParm('inherit_ctrl')\nr = 'none'\nif i == 1 or (n_hasFlag and i == 2):\n    r = 'inherit'\nreturn r"
                ]
            ),
            default_expression=(
                [
                    "n = hou.pwd()\nn_hasFlag = n.isMaterialFlagSet()\ni = n.evalParm('inherit_ctrl')\nr = 'none'\nif i == 1 or (n_hasFlag and i == 2):\n    r = 'inherit'\nreturn r"
                ]
            ),
            default_expression_language=([hou.scriptLanguage.Python]),
            naming_scheme=hou.parmNamingScheme.Base1,
            string_type=hou.stringParmType.Regular,
            menu_items=(["none", "reference", "inherit", "specialize", "represent"]),
            menu_labels=(["None", "Reference", "Inherit", "Specialize", "Represent"]),
            icon_names=([]),
            item_generator_script="",
            item_generator_script_language=hou.scriptLanguage.Python,
            menu_type=hou.menuType.Normal,
        )
        hou_parm_template2.setTags(
            {"sidefx::shader_isparm": "0", "spare_category": "Shader"}
        )
        hou_parm_template.addParmTemplate(hou_parm_template2)
        # Code for parameter template
        hou_parm_template2 = hou.StringParmTemplate(
            "shader_baseprimpath",
            "Class Prim Path",
            1,
            default_value=(["/__class_mtl__/`$OS`"]),
            naming_scheme=hou.parmNamingScheme.Base1,
            string_type=hou.stringParmType.Regular,
            menu_items=([]),
            menu_labels=([]),
            icon_names=([]),
            item_generator_script="",
            item_generator_script_language=hou.scriptLanguage.Python,
            menu_type=hou.menuType.Normal,
        )
        hou_parm_template2.setTags(
            {
                "script_action": "import lopshaderutils\nlopshaderutils.selectPrimFromInputOrFile(kwargs)",
                "script_action_help": "Select a primitive in the Scene Viewer or Scene Graph Tree pane.\nCtrl-click to select using the primitive picker dialog.",
                "script_action_icon": "BUTTONS_reselect",
                "sidefx::shader_isparm": "0",
                "sidefx::usdpathtype": "prim",
                "spare_category": "Shader",
            }
        )
        hou_parm_template.addParmTemplate(hou_parm_template2)
        # Code for parameter template
        hou_parm_template2 = hou.SeparatorParmTemplate("separator1")
        hou_parm_template.addParmTemplate(hou_parm_template2)
        # Code for parameter template
        hou_parm_template2 = hou.StringParmTemplate(
            "tabmenumask",
            "Tab Menu Mask",
            1,
            default_value=(
                [
                    "MaterialX parameter constant collect null genericshader subnet subnetconnector suboutput subinput"
                ]
            ),
            naming_scheme=hou.parmNamingScheme.Base1,
            string_type=hou.stringParmType.Regular,
            menu_items=([]),
            menu_labels=([]),
            icon_names=([]),
            item_generator_script="",
            item_generator_script_language=hou.scriptLanguage.Python,
            menu_type=hou.menuType.Normal,
        )
        hou_parm_template2.setTags({"spare_category": "Tab Menu"})
        hou_parm_template.addParmTemplate(hou_parm_template2)
        # Code for parameter template
        hou_parm_template2 = hou.StringParmTemplate(
            "shader_rendercontextname",
            "Render Context Name",
            1,
            default_value=(["mtlx"]),
            naming_scheme=hou.parmNamingScheme.Base1,
            string_type=hou.stringParmType.Regular,
            menu_items=([]),
            menu_labels=([]),
            icon_names=([]),
            item_generator_script="",
            item_generator_script_language=hou.scriptLanguage.Python,
            menu_type=hou.menuType.Normal,
        )
        hou_parm_template2.setTags(
            {"sidefx::shader_isparm": "0", "spare_category": "Shader"}
        )
        hou_parm_template.addParmTemplate(hou_parm_template2)
        # Code for parameter template
        hou_parm_template2 = hou.ToggleParmTemplate(
            "shader_forcechildren", "Force Translation of Children", default_value=True
        )
        hou_parm_template2.setTags(
            {"sidefx::shader_isparm": "0", "spare_category": "Shader"}
        )
        hou_parm_template.addParmTemplate(hou_parm_template2)
        hou_parm_template_group.append(hou_parm_template)
        in_mtlx_node.setParmTemplateGroup(hou_parm_template_group)

    def _create_base_nodes_in_subnet_(self, in_material_net_node: hou.Node) -> tuple:
        """
        Docstring for _create_base_nodes_in_subnet_

        :param in_mtlx_node: 节点所在的父节点
        :type in_mtlx_node: hou.Node
        :return: 返回standard_surface和displacement节点（非输出节点）
        :rtype: tuple[Any, ...]
        """
        surface_output = self._create_output_node_(in_material_net_node, "surface")
        displace_output = self._create_output_node_(
            in_material_net_node, "displacement"
        )

        mtlx_standard_surf = in_material_net_node.createNode(
            "mtlxstandard_surface", self.mat_name + "_mtlxSurface"
        )
        mtlx_displacement = in_material_net_node.createNode(
            "mtlxdisplacement", self.mat_name + "_mtlxDisplacement"
        )

        # 设置连接
        surface_output.setInput(0, mtlx_standard_surf)
        displace_output.setInput(0, mtlx_displacement)

        return mtlx_standard_surf, mtlx_displacement

    def _create_output_node_(self, in_material_net_node: hou.Node, in_output_name: str):
        output_node = in_material_net_node.createNode(
            "subnetconnector", f"{in_output_name}_output"
        )

        if not output_node:
            hou.ui.displayMessage(
                "CreateNode Return not Match,Pleace Check",
                severity=hou.severityType.Error,
            )
            return

        output_node.parm("connectorkind")._set("output")
        output_node.parm("parmname")._set(in_output_name.lower())
        output_node.parm("parmlabel")._set(in_output_name.capitalize())
        output_node.parm("parmtype")._set(in_output_name.lower())

        color = (
            hou.Color(0.89, 0.69, 0.6)
            if in_output_name.lower() == "surface"
            else hou.Color(0.6, 0.69, 0.89)
        )
        output_node.setColor(color)

        return output_node

    def _create_place2d_(self, in_material_net_node: hou.Node, in_material_info: dict):
        # UDIM纹理不创建UV缩放
        pprint.pprint(in_material_info)
        if not in_material_info.get("UDIM",False):
            print("Create Place2D Nodes")
            nodes = {
                "coord": in_material_net_node.createNode(
                    "mtlxtexcoord", f"{self.mat_name}_texcoord"
                ),
                "scale": in_material_net_node.createNode(
                    "mtlxconstant", f"{self.mat_name}_scale"
                ),
                "rotate": in_material_net_node.createNode(
                    "mtlxconstant", f"{self.mat_name}_rotation"
                ),
                "offset": in_material_net_node.createNode(
                    "mtlxconstant", f"{self.mat_name}_offset"
                ),
                "place2d": in_material_net_node.createNode(
                    "mtlxplace2d", f"{self.mat_name}_place2d"
                ),
            }
            nodes["scale"].parm("value")._set(1)
            # 连接节点
            nodes["place2d"].setInput(0, nodes["coord"])
            nodes["place2d"].setInput(2, nodes["scale"])
            nodes["place2d"].setInput(3, nodes["rotate"])
            nodes["place2d"].setInput(4, nodes["offset"])
            return nodes["place2d"]
        return None

    def _layout_nodes_(self, in_material_net_node: hou.Node):
        in_material_net_node.layoutChildren()
        self.node_ref.layoutChildren()

    def _process_textures_(
        self,
        in_material_net_node: hou.Node,
        in_material_info: dict,
        in_surface_node: hou.Node,
        in_displace_node: hou.Node,
        in_place2d_nodes,
    ):
        """
        根据整理获得的信息创建材质

        :param in_material_net_node: 纹理采样所在的父节点
        :param in_material_info: 纹理信息dict
        :param in_surface_node: 先前创建的surface纹理attribute节点
        :param in_displace_node: 先前创建的displacement纹理attribute节点
        :param in_place2d_nodes: 先前创建的UVTranslation节点
        """
        print("Get In Process texture")
        attribute_names = in_surface_node.inputNames()
        for texture_type, texture_info in self._surface_texture_sort_iterator_(
            in_material_info
        ):
            print(f"Current Iterator {texture_type}")
            texture_sampler_node=self._create_texture_sample_node_(
                in_material_net_node, texture_info, in_material_info
            )
            if in_place2d_nodes and not in_material_info.get("UDIM",False):
                #coord_index=in_place2d_nodes.inputIndex("texcoordx texcoordy")
                #print(f"Coord_index Is {coord_index}")
                texture_sampler_node.setInput(3,in_place2d_nodes)
            #in_surface_node.inputIndex()


    def _surface_texture_sort_iterator_(self, in_material_info: dict):
        """
        传进来的粗分类数据进行重新分类
        :param in_material_info: 当前处理的材质信息
        :type in_material_info: dict
        """
        # 只处理表面纹理，置换、法线等忽略
        skip_keys = ["UDIM","Size","bump","bmp","height","displacement","displace","disp","dsp","heightmap","normal","nor","nrm","nrml","norm"]
        for texture_key in in_material_info.keys():
            if texture_key in skip_keys:
                continue
            for texture_type, type_indicators in self.TEXTURE_TYPE_SORTED.items():
                if any(
                    indicator in texture_key.lower() for indicator in type_indicators
                ):
                    texture_info = {
                        "name": texture_key,
                        "file": in_material_info[texture_key][0],
                        "type": texture_type,
                    }
                    yield texture_type, texture_info

    def _create_texture_sample_node_(
        self, in_parent_node: hou.Node, in_texture_info: dict, in_material_info: dict
    )->hou.VopNode:
        """
        创建纹理采样节点并赋值,UDIM和常规纹理使用不同采样类型

        :param in_parent_node: 纹理采样节点的父节点
        :type in_parent_node: hou.Node
        :param in_texture_info: 已进行重分类的纹理信息
        :type in_texture_info: dict
        :param in_material_info: 原始材质信息
        :type in_material_info: dict
        """
        print("Call Create Texture Sample")
        if not in_parent_node:
            print("Create Texture Sample Node Failed,Invalid Input")
            return
        sample_node_class = (
            "mtlximage" if not in_material_info.get("UDIM", False) else "mtlxtiledimage"
        )
        texture_sample_node:hou.VopNode = in_parent_node.createNode(
            sample_node_class, in_texture_info["type"][8:] + "_sampler"
        )
        print("Finish Create Node")
        # 设置路径
        texture_path=self._get_texture_path_(in_texture_info["name"],in_material_info)
        texture_sample_node.parm("file")._set(texture_path)
        print("Finish Setting Path")
        # 设置采样节点类型
        self._configure_texture_sample_node_(in_texture_info["type"],texture_sample_node)
        print("Finish configure Node")
        return texture_sample_node

    def _get_texture_path_(self,in_texture_name:str,in_material_info:dict)->str:
        '''
        返回纹理路径,主要用于tx文件的处理
        :param in_texture_name: 原dict中纹理key
        :type in_texture_name: str
        :param in_material_info: 原dict
        :type in_material_info: dict
        {
        'ao': ['old_linoleum_flooring_01_ao_2k.jpg'], 
        'res': '2k', 
        'UDIM': False, 
        'diff': ['old_linoleum_flooring_01_diff_2k.jpg'], 
        'disp': ['old_linoleum_flooring_01_disp_2k.png'], 
        'nor': ['old_linoleum_flooring_01_nor_gl_2k.jpg'], 
        'rough': ['old_linoleum_flooring_01_rough_2k.jpg']
        }
        
        '''
        file_name=in_material_info[in_texture_name][0]
        # inmaterialinfo中只有文件信息，没有路径信息
        if self.b_mtlTX:
            file_name_without_extension=file_name.split(".")[0]
            file_name=file_name_without_extension+".tx"
        if in_material_info.get("UDIM",True):
            file_name=re.sub(r"\d{4}","<UDIM>",file_name)
        file_path=os.path.join(self.tex_folder_path,file_name).replace(os.sep,"/")
        print(f"Finish Setting Path,Targte Path:{file_path}")
        return file_path
        
    def _configure_texture_sample_node_(self,_in_texture_type_:str,in_sample_node:hou.OpNode):
        if not in_sample_node:
            print("Config Node Failed,The Node Doesn't Exist")
            return
        sample_model="float"
        color_space="raw"
        # 对于BaseColor和次表面散射使用Color3 SRGB
        if _in_texture_type_ in("texturesColor","texturesSSS"):
            sample_model="color3"
            color_space="srgb_texture"
        in_sample_node.parm("signature")._set(sample_model)
        in_sample_node.parm("filecolorspace")._set(color_space)

def ShowTexToMatTool():
    window_gui = TxToMtlx()
    window_gui.show()


# def _iterate_textures(self, material_lib_info):
#     skip_keys =['UDIM''Size','normal','nor''nrm','nrml','norm','bump','bmp','height','displace']
#     for texture in material_lib_info:
#         if texture in skip_keys:
#             continue
#         for texture_type, variants in self.TEXTURE_TYPE_SORTED.items():
#             if any(variant in texture.lower() for variant in variants):
#                 texture_info = {'name':texture,
#                                 'file': material_lib_info[texture][0],
#                                 'type':texture_type}
#                 yield texture_type, texture_info
