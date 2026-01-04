import hou
import os
import re
import pprint
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
        ".targa",
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
        "norm",
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
        self.mtlTX = False

        self._setup_help_section()
        self._setup_material_section()
        self._setup_list_section()
        self._setup_create_section()
        self._setup_connections()

        self.material_lib_path = None
        self.material_lib_node: hou.OpNode = hou.node(
            "/shop"
        )  # <---------Remove After Test
        self.tex_collection:dict={}


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
        \nAmbient Occlusion:ambient_occlusion, ao, occlusion, cavity,
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
        self.tex_collection=self._collect_images_in_dir(folder_path)
        if len(self.tex_collection)==0:
            return
        #pprint.pprint(self.tex_collection)
        # 把图片信息添加到List
        self.model.clear()
        for tex_group in self.tex_collection:
            self.model.appendRow(QtGui.QStandardItem(tex_group))

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

    def _collect_images_in_dir(self, in_dir_path: str)->dict:
        # 解析文件夹中的纹理，构造一个二维字典
        if not os.path.exists(in_dir_path):
            hou.ui.displayMessage("Given Path Is Not Valid,Please Check")
            return {}
        material_collection=defaultdict(lambda:defaultdict(list))
        for elem in os.listdir(in_dir_path):
            current_testing_path = os.path.join(in_dir_path, elem)
            if not os.path.isfile(current_testing_path):
                continue
            if not elem.endswith(self.SUPPORT_IMAGE_FORMAT):
                continue
            file_name=elem.split(".")[0].lower()
            # 使用_分段
            name_keywords=file_name.split("_")
            material_name=name_keywords[0]
            # 使用关键词匹配纹理种类
            texure_type=""
            for type in self.TEX_TYPE:
                for name_keyword in name_keywords[1:]:
                    if type in name_keyword:
                        texure_type=name_keyword
                        break
            # 没有匹配的字段，纹理不加入纹理组
            if texure_type=="":
                continue
            material_collection[material_name][texure_type].append(elem)
            # 使用正则表达式获取纹理分辨率
            tex_res=self.ORDINARY_TEX_REGEX_PATTERN.search(elem)
            if not tex_res==None:
                material_collection[material_name]["res"].append(tex_res.group(1))
            # 使用正则表达式匹配UDIM
            is_UDIM= self.UDIM_TEX_REGEX_PATTERN.search(elem)
            if not is_UDIM==None:
                material_collection[material_name]["UDIM"].append(is_UDIM)
            
        if len(material_collection)==0:
            return {}
        return dict(material_collection)


def ShowTexToMatTool():
    window_gui = TxToMtlx()
    window_gui.show()
