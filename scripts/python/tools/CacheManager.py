import hou
import os
from PySide6 import QtCore,QtUiTools,QtWidgets,QtGui

class SceneCacheManagerUI(QtWidgets.QMainWindow):
    # 节点类型和输出数据路径配置的属性名称
    CACHE_NODES={
        "filecache":"sopoutput",
        "rop_geometry":"sopoutput",
        "rop_alembic":"filename",
        "rop_fbx":"sopoutput",
        "rop_dop":"dopoutput",
        "vellumio":"sopoutput",
        "rbdio":"sopoutput",
        "kinefx::characterio":"sopoutput"
    }

    def __init__(self) -> None:
        super().__init__()
        ui_path=hou.text.expandString("$MYLIB")+"/ui/scene_cache_manager.ui"
        print(ui_path)
        self.ui=QtUiTools.QUiLoader().load(ui_path,parentWidget=self)
        self.setParent(hou.qt.mainWindow(),QtCore.Qt.Window)
        self.setWindowTitle("Scene Cache Manager")
        self.setMinimumWidth(1200)

        self._init_ui_()
        self._init_bindings_()
        self.cache_data=[]

    def _init_ui_(self):
        self.cache_tree:QtWidgets.QTreeWidget=self.ui.findChild(QtWidgets.QTreeWidget,"cache_tree")
        self.total_node:QtWidgets.QLabel=self.ui.findChild(QtWidgets.QLabel,"lb_total_nodes")
        self.total_size:QtWidgets.QLabel=self.ui.findChild(QtWidgets.QLabel,"lb_total_size")
        self.unused_versions:QtWidgets.QLabel=self.ui.findChild(QtWidgets.QLabel,"lb_unused_versions")
        self.cleanup_button:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_cleanup")
        self.explorer_button:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_reveal")
        self.scan_button:QtWidgets.QPushButton=self.ui.findChild(QtWidgets.QPushButton,"bt_scan")

    def _init_bindings_(self):
        self.cleanup_button.clicked.connect(self.CleanUp)
        self.explorer_button.clicked.connect(self.OpenExplorer)
        self.scan_button.clicked.connect(self.ScanScene)

    def CleanUp(self):
        pass

    def OpenExplorer(self):
        pass

    def ScanScene(self):
        self.cache_tree.clear()
        self.cache_data=[]
        print("Scan Button Was Clicked")

        # Scan All Node，前边列举过所有种类的节点和他们输出属性的名称
        for node_type,output_property in self.CACHE_NODES.items():
            # 下面两行要一起理解，hou.nodeType需要输入一个category，对应的就是hou.sopNodeTypeCategory()，使用数组方便扩展更多Net的数据
            for category in [hou.sopNodeTypeCategory()]:
                node_type_in_category=hou.nodeType(category,node_type)
                if not node_type_in_category:
                    continue
                cache_nodes=node_type_in_category.instances()
                for single_cache_node in cache_nodes:
                    cache_path=single_cache_node.parm(output_property).eval()
                    if not cache_path:
                        continue
                    node_data={
                        "node_name":"name",
                        "node_path":"path",
                        "node_type":"type",
                        "cache_path":"cache",
                        "current_version":"version",
                        "other_versions":"other",
                        "lastmodified":"last",
                        "total_size":"size"
                    }
                    self._add_to_tree(node_data)

                


    def _add_to_tree(self,in_node_data:dict):
        item=QtWidgets.QTreeWidgetItem(self.cache_tree)
        data_keys=list(in_node_data.keys())
        for i in range(len(data_keys)):
           # print(data_keys[i])
           item.setText(i,in_node_data[data_keys[i]])

def ShowSceneCacheWidget():
    win=SceneCacheManagerUI()
    win.show()