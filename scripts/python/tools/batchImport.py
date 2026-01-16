import hou
def batchImport():
    default_dir=hou.text.expandString('$HIP')
    selected_files= hou.ui.selectFile(start_directory=default_dir,
        title='Select Files To Import',
        file_type=hou.fileType.Geometry,multiple_select=True)

    if selected_files:
        root_node=hou.node('/obj')
        sop_node=root_node.createNode('geo',node_name='geo_temp')
        merge_node=sop_node.createNode('merge')
        merge_index=0
        selected_files=selected_files.split(';')
        for item in selected_files:
            item=item.strip()
            path_elem=item.split('/')
            file_name_parser=path_elem[-1].split('.')
            file_name=file_name_parser[0]
            file_extension=file_name_parser[-1]
            if file_extension=='abc':
                abc_node=sop_node.createNode('alembic',node_name=file_name+'_abc')
                abc_node.parm('fileName').set(item)

                unpack_node=sop_node.createNode('pack',node_name=file_name+'_pack')
                unpack_node.setInput(0,abc_node)

                trans_node=sop_node.createNode('xform',node_name=file_name+'_trans')
                trans_node.parm('scale').set(0.01)
                trans_node.setInput(0,unpack_node)

                material_node=sop_node.createNode('material',node_name=file_name+'_mat')
                material_node.setInput(0,trans_node)
            else:
                file_node=sop_node.createNode('file',node_name=file_name+'_abc')
                file_node.parm('file').set(item)

                trans_node=sop_node.createNode('xform',node_name=file_name+'_trans')
                trans_node.parm('scale').set(0.01)
                trans_node.setInput(0,file_node)

                material_node=sop_node.createNode('material',node_name=file_name+'_mat')
                material_node.setInput(0,trans_node)

            merge_node.setInput(merge_index,material_node)
            merge_index+=1
        sop_node.layoutChildren()
    else:
        hou.ui.displayMessage('Please Select Geometry File',buttons=('Ok',))