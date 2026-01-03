import hou
import os
import datetime
import platform
import shutil
from PySide6 import QtCore, QtUiTools, QtWidgets, QtGui


class SceneCacheManagerUI(QtWidgets.QMainWindow):
    # 节点类型和输出数据路径配置的属性名称
    CACHE_NODES = {
        "rop_geometry": "sopoutput",
        "rop_alembic": "filename",
        "rop_fbx": "sopoutput",
        "rop_dop": "dopoutput",
    }

    KB = 1024
    MB = KB * 1024
    GB = MB * 1024

    def __init__(self) -> None:
        super().__init__()
        ui_path = hou.text.expandString("$MYLIB") + "/ui/scene_cache_manager.ui"
        print(ui_path)
        self.ui = QtUiTools.QUiLoader().load(ui_path, parentWidget=self)
        self.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
        self.setWindowTitle("Scene Cache Manager")
        self.setMinimumWidth(1200)

        self._init_ui_()
        self._init_bindings_()
        self.cache_data = []

    def _init_ui_(self):
        self.cache_tree: QtWidgets.QTreeWidget = self.ui.findChild(
            QtWidgets.QTreeWidget, "cache_tree"
        )
        self.total_node: QtWidgets.QLabel = self.ui.findChild(
            QtWidgets.QLabel, "lb_total_nodes"
        )
        self.total_size: QtWidgets.QLabel = self.ui.findChild(
            QtWidgets.QLabel, "lb_total_size"
        )
        self.unused_versions: QtWidgets.QLabel = self.ui.findChild(
            QtWidgets.QLabel, "lb_unused_versions"
        )
        self.cleanup_button: QtWidgets.QPushButton = self.ui.findChild(
            QtWidgets.QPushButton, "bt_cleanup"
        )
        self.explorer_button: QtWidgets.QPushButton = self.ui.findChild(
            QtWidgets.QPushButton, "bt_reveal"
        )
        self.scan_button: QtWidgets.QPushButton = self.ui.findChild(
            QtWidgets.QPushButton, "bt_scan"
        )

        self.cache_tree.setSortingEnabled(True)

        self.cache_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.cache_tree.customContextMenuRequested.connect(self._open_right_shortcut_)

    def _init_bindings_(self):
        self.cleanup_button.clicked.connect(lambda: self._cleanup_(True))
        self.explorer_button.clicked.connect(self._open_explore_)
        self.scan_button.clicked.connect(self.ScanScene)

        self.cache_tree.itemDoubleClicked.connect(self._focus_on_node_)

    def ScanScene(self):
        self.cache_tree.clear()
        self.cache_data = []
        print("Scan Button Was Clicked")

        # Scan All Node，前边列举过所有种类的节点和他们输出属性的名称
        for node_type, output_property in self.CACHE_NODES.items():
            # 下面两行要一起理解，hou.nodeType需要输入一个category，对应的就是hou.sopNodeTypeCategory()，使用数组方便扩展更多Net的数据
            for category in [
                hou.sopNodeTypeCategory(),
                hou.dopNodeTypeCategory(),
                hou.ropNodeTypeCategory(),
            ]:
                node_type_in_category = hou.nodeType(category, node_type)
                if not node_type_in_category:
                    continue
                cache_nodes = node_type_in_category.instances()
                for single_cache_node in cache_nodes:
                    cache_path = single_cache_node.parm(output_property).eval()
                    if not cache_path:
                        continue
                    last_modified_str = self._get_last_modify_time_(cache_path)
                    total_version_count, node_cache_size_sum = (
                        self._get_total_version_info_(cache_path)
                    )
                    other_version_count = max(0, total_version_count - 1)
                    # relative_path = self._convert_to_relative_path(cache_path)
                    node_name, node_path, node_type_real = self._get_node_base_info_(
                        single_cache_node
                    )
                    node_data = {
                        "node_name": node_name,
                        "node_path": node_path,
                        "node_type": node_type_real,
                        "cache_path": cache_path,
                        "current_version": self._get_current_version_(node_path),
                        "other_versions": str(other_version_count),
                        "lastmodified": last_modified_str,
                        "total_size": self._convert_byte_to_bigger_unit_(
                            node_cache_size_sum
                        ),
                    }
                    self._add_to_tree(node_data)
                    self.cache_data.append(node_data)
        self._update_stat_text_()

    def _add_to_tree(self, in_node_data: dict):
        item = QtWidgets.QTreeWidgetItem(self.cache_tree)
        data_keys = list(in_node_data.keys())
        for i in range(len(data_keys)):
            # print(data_keys[i])
            item.setText(i, in_node_data[data_keys[i]])

    def _get_node_base_info_(self, in_node: hou.Node):
        """
        Return the Correct Node Details-name,path,type

        :param self: Description
        :param in_node: Description
        :type in_node: hou.Node
        Return
            tuple- Name,Path,type in Str
        """
        node_name = in_node.name()
        node_path = in_node.path()
        node_type = in_node.type().name()
        check_parent = in_node.parent()
        # 临时解决方案
        if node_name == "render" and check_parent.name() == "filecache":
            node_name = in_node.parent().parent().name()
            node_path = in_node.parent().parent().path()
            node_type = in_node.parent().parent().type().name()
        elif node_name == "render":
            node_name = in_node.parent().name()
            node_path = in_node.parent().path()
            node_type = in_node.parent().type().name()
        return node_name, node_path, node_type

    def _convert_to_relative_path(self, in_absolute_path: str) -> str:
        project_path = hou.text.expandString("$HIP")
        if not os.path.exists(project_path):
            # print("Env $HIP Not Exist")
            return in_absolute_path
        relative_path = in_absolute_path
        if in_absolute_path.startswith(project_path):
            # print(f"Replace {project_path} with $HIP")
            relative_path = in_absolute_path.replace(project_path, "$HIP")
        return relative_path

    def _get_current_version_(self, in_node_path: str) -> str:
        # 这里有不明原因必须这么做，传入Node即使调用Node.path()也无法获取对应值
        target_node: hou.OpNode = hou.node(in_node_path)
        try:
            version = target_node.parm("version").eval()
            # print(type(target_node.parm("version")))
            return str(version) if version else "N/A"
        except:
            return "N/A"

    def _get_versions_path_(
        self, in_current_version_path: str, include_current_version: bool = False
    ) -> list:
        """
        获取历史版本路径数组
        Params:
            in_current_version_path: 当前版本存储路径
            include_current_version: 是否包含当前版本
        Return:
            历史版本数组
        """
        versions_path = []
        # 获得版本存储路径，本质上是利用特殊文件结构查询文件夹，文件夹以v版本号为名称
        # 先把文件名和文件夹名拆开，再使用dirname获得v版本号的上一级目录
        current_version_folder = os.path.split(in_current_version_path)[0]
        cache_parent_dir = os.path.dirname(current_version_folder)
        if not os.path.exists(cache_parent_dir):
            return versions_path
        for item in os.listdir(cache_parent_dir):
            target_path = os.path.join(cache_parent_dir, item).replace(os.sep, "/")
            if os.path.isdir(target_path) and item.startswith("v"):
                print(
                    f"Current Searching Path={target_path},Last version={current_version_folder},CompareReuslt:include: {include_current_version}, Is SamePath{target_path == current_version_folder},path Exist {os.path.exists(target_path)}"
                )
                if not os.path.exists(target_path):
                    continue
                # 是否排除当前路径
                if (
                    not include_current_version
                    and target_path == current_version_folder
                ):
                    continue
                try:
                    # 切片器，去除v
                    version_num_str = "".join(item[1:])
                    if not version_num_str.isdigit():
                        continue
                    versions_path.append(target_path)
                except:
                    continue
        return versions_path

    def _get_total_version_info_(self, in_cache_dir: str) -> tuple:
        """
        获取缓存路径中历史版本数量，返回文件数量和总大小,均为int
        """
        cache_size_sum = 0
        # 先切分文件名和所在路径，再使用dirname返回上一层
        version = self._get_versions_path_(in_cache_dir,True)
        if len(version) == 0:
            return (0, 0)
        for cache_path in version:
            cache_size_sum += self._get_folder_size_(cache_path)
        return (len(version), cache_size_sum)

    def _get_last_modify_time_(self, in_file_path: str) -> str:
        if os.path.exists(in_file_path):
            time_stamp = os.path.getmtime(in_file_path)
            timestr = datetime.datetime.fromtimestamp(time_stamp).strftime(
                "%d/%m/%Y, %H:%M"
            )
            return timestr
        else:
            return "--"

    def _focus_on_node_(self):
        """
        聚焦到首个所选对象
        """
        selected_node = self.cache_tree.selectedItems()[0]
        if not selected_node:
            hou.ui.displayMessage(
                "Please Select A Node In List", severity=hou.severityType.Warning
            )
            return
        # 获取节点路径
        selected_node_path = selected_node.text(1)
        selected_node_ref = hou.node(selected_node_path)
        if not selected_node_ref:
            hou.ui.displayMessage(
                "Invalid Node Selected,Please Scan And Reselect",
                severity=hou.severityType.Warning,
            )
            return
        selected_node_ref.setSelected(True)
        # 查找邻近的UI(但是不会给UI设置突出显示，如果有多个ui可能需要找到对应)，打开所选择节点父级
        target_pane = None
        for pane in hou.ui.paneTabs():
            if isinstance(pane, hou.NetworkEditor):
                target_pane = pane
                break
        if not target_pane:
            hou.ui.displayMessage(
                "Find Null Avaliable Network Table", severity=hou.severityType.Warning
            )
            return
        print(target_pane)
        print(selected_node_ref.parent().path())
        target_pane.cd(selected_node_ref.parent().path())
        target_pane.frameSelection()

    def _open_explore_(self):
        """
        打开节点缓存路径对应的文件夹
        """
        select_item = self.cache_tree.selectedItems()[0]
        select_path = select_item.text(3)
        select_path = os.path.split(select_path)[0]
        if not os.path.exists(select_path):
            print(f"Target Path {select_path} Does't Exist")
            return
        # 对不同平台采用不同打开策略
        try:
            if platform.system() == "Windows":
                os.startfile(select_path)
            elif platform.system() == "Linux":
                os.system(f"xfg-open '{select_path}")
            else:
                os.system(f"open '{select_path}")
        except Exception as error:
            print(f"Fail to Open Path{select_path},on your {platform.system()} OS")

    def _open_right_shortcut_(self, position):
        select_item = self.cache_tree.selectedItems()[0]
        if not select_item:
            return
        right_shortcut = QtWidgets.QMenu()
        # 设置子菜单行为
        explore_action = right_shortcut.addAction("Open In Explore")
        explore_action.triggered.connect(self._open_explore_)
        clean_action = right_shortcut.addAction("Delete Old Version")
        clean_action.triggered.connect(lambda: self._cleanup_(False))

        right_shortcut.exec_(self.cache_tree.viewport().mapToGlobal(position))

    def _cleanup_(self, clean_all=False):
        # 从缓存中删除、内容更新
        target_nodes = self.cache_tree.selectedItems()
        if not clean_all:
            target_nodes = target_nodes[:1]
        if not target_nodes:
            hou.ui.displayMessage("Please Select A Item In List")
            return
        folders_to_delete = set()
        # 获取对象缓存路径
        for node in target_nodes:
            # 获取历史版本计数，没有历史版本直接跳过
            if int(node.text(5)) < 1:
                continue
            current_cache_path = node.text(3)
            other_version_path = self._get_versions_path_(current_cache_path, False)
            if len(other_version_path) < 1:
                continue
            # 对于包含历史版本的，直接把非当前加入统计
            for early_version in other_version_path:
                folders_to_delete.add(early_version)
        if len(folders_to_delete) == 0:
            return
        message = "Following Folder Will Be Delete After Confirm:\n"
        for single_folder in folders_to_delete:
            message += f"{single_folder} \n"
        user_input = hou.ui.displayMessage(
            message, buttons=("DeleteAll", "NO"), severity=hou.severityType.Warning
        )
        # 取消删除
        if not user_input == 0:
            hou.ui.displayMessage("Cancel Delete", severity=hou.severityType.Message)
            return
        # 确认删除
        for single_folder in folders_to_delete:
            try:
                shutil.rmtree(single_folder)
            except Exception as Error:
                hou.ui.displayMessage(
                    f"Fail to Delete {single_folder},Reason {Error}",
                    severity=hou.severityType.Error,
                )

    def _update_stat_text_(self):
        self.total_node.setText("Total Cache Nodes:" + str(len(self.cache_data)))

        total_cache_size = 0
        for node_cache_info in self.cache_data:
            target_cache_path = node_cache_info["cache_path"]
            cache_size_of_current_node = self._get_total_version_info_(
                target_cache_path
            )[1]
            total_cache_size += cache_size_of_current_node
            print(
                f"Node {node_cache_info['node_name']} With Cache Size:{cache_size_of_current_node},At Path{target_cache_path}"
            )
        self.total_size.setText(
            "Total Cache Size:" + self._convert_byte_to_bigger_unit_(total_cache_size)
        )

    def _convert_byte_to_bigger_unit_(self, in_num_in_byte: int) -> str:
        if in_num_in_byte == 0:
            return "--"
        if in_num_in_byte // self.KB == 0:
            return f"{in_num_in_byte:.2f} B"
        if in_num_in_byte // self.MB == 0:
            return f"{in_num_in_byte/self.KB:.2f} KB"
        if in_num_in_byte // self.GB == 0:
            return f"{in_num_in_byte/self.MB:.2f} MB"
        return f"{in_num_in_byte/self.GB:.2f} GB"

    def _get_folder_size_(self, in_target_path: str) -> int:
        if not os.path.exists:
            return 0
        folder_size = 0
        for path, dirs, files in os.walk(in_target_path):
            for file in files:
                folder_size += os.path.getsize(os.path.join(path, file))
        return folder_size


def ShowSceneCacheWidget():
    win = SceneCacheManagerUI()
    win.show()
