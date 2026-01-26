import hou
import importlib
import os
import sys

def reloadPackageAndModules():
    #重新加载包，对应User/Documents下的个人配置文件
    package_dir=hou.text.expandString("$HOUDINI_USER_PREF_DIR/packages/")+"my_houdini_tools.json"
    hou.ui.reloadPackage(package_dir)
    print(f"Reload Package {package_dir}")

    #重新加载模块，对应json文件指向的个人库，其中$MYLIB是json中定义的个人库路径
    modules_dir=hou.text.expandString("$MYLIB/scripts/python")
    #print(sys.modules)
    #函数返回多个元组、每个文件夹对应一个元组，算组三个元素分别表示当前路径、当前路径下文件夹名称、当前路径下文件名称
    for dirpath, dirnames, filenames in os.walk(modules_dir):
        #print(f"DirPath={dirpath},DirName={dirnames},FileNames={filenames}")
        #对每一个.py模块调用加载或重加载Importlib需要使用.分割的路径
        for file in filenames:
            if file.endswith(".py") and file!="__init__.py":
                module_path=os.path.join(dirpath,file).replace(os.sep,"/")
                module_name=os.path.relpath(module_path,modules_dir).replace(os.sep,".").replace(".py","")
                print(module_name)
                try:
                # 已经加载过就重加载MY
                    if module_name in sys.modules:
                        importlib.reload(sys.modules[module_name])
                        print(f"Reload module:{module_name}")
                    else:
                        importlib.import_module(module_name)
                        print(f"Load module:{module_name}")
                except Exception as error:
                    print(f"Load module {module_name} Failed:{error}")
    # 重新加载菜单
    hou.hscript("menurefresh")
    # 重新加载shelves
    shelves=hou.shelves.shelves()
    path_shelves=hou.text.expandString("$MYLIB/toolbar")
    for dirpath, dirnames, filenames in os.walk(path_shelves):
        for filename in filenames:
            if filename.endswith(".shelf"):
                shelf_path=os.path.join(dirpath,filename).replace(os.sep,"/")
                hou.shelves.loadFile(shelf_path)

def isValidDir(path:str)->str:
    """
    Check Given Path Validation,
    Return Path if Valid
    Return "None" if Not Valid
    """
    import hou
    import os

    full_path=hou.text.expandString(path)
    path_dir=os.path.dirname(full_path).strip()
   
    if os.path.exists(path_dir) and os.access(path_dir,os.R_OK):
        print(f"{path_dir} is valid path")
        return path_dir
    else:
        hou.ui.displayMessage(f"Invalid Path {path_dir}")
        return "None"
    

def is_in_solaris()->bool:
    network_editor=hou.ui.curDesktop().paneTabOfType(hou.paneTabType.NetworkEditor)
    if network_editor:
        if network_editor.pwd().childTypeCategory().name()=="Lop":
            return True
    return False
