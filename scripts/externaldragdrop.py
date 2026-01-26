import hou
import os
import my_houdini_utils as utils
import tools.CreateUSDCompBuilder as compbuilder


def dropAccept(file_list)->bool:
    '''
    拖放单个外部资产进行导入
    '''
    # hip文件拖放时合并文件
    if len(file_list)!=1:
        hou.ui.displayMessage("Only support single file drag import,please select single file and try again",severity=hou.severityType.Error)
    target_file_path=file_list[0]
    if os.path.splitext(target_file_path)[1] in ("hip","hiplc"):
        hou.hipFile.merge(target_file_path)
        return True
    
    if utils.is_in_solaris():
        compbuilder.create_usd_comp_builder(target_file_path)
    return True