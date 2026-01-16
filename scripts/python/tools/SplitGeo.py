import hou
#获取选中节点
def SplitGeo():
    selected_nodes=hou.selectedNodes()
    if not selected_nodes:
        hou.ui.displayMessage("Select None Node")
        raise ValueError("Select None Node")
    target_node:hou.SopNode=selected_nodes[0]
    if not target_node:
        hou.ui.displayMessage("Invalid Node")
        raise ValueError("Invalid Node")
    button_index_pressed,attribute_name=hou.ui.readInput("Provide the attribute's name to split the geometry",buttons=('OK',"Cancel"))
    #处理未输入attributename情况
    if button_index_pressed==1 or not attribute_name:
        hou.ui.displayMessage("No Attirbute Input")
        raise ValueError("No Attirbute Input")
    #判断属性有效性

    parent_node=target_node.parent()
    target_node_geo=target_node.geometry()
    split_attribute=target_node_geo.findPrimAttrib(attribute_name)
    if not split_attribute:
        hou.ui.displayMessage(f"Find Null Attribute Named -{attribute_name}- In Selected Node Geo")
        raise ValueError(f"Find Null Attribute Named -{attribute_name}- In Selected Node Geo")
        
    merge_node=parent_node.createNode("merge","Geo_split_merge")
    child_nodes=[merge_node]
    unique_value=set()
    for prim in target_node_geo.prims():
        unique_value.add(prim.attribValue(attribute_name))#注意不要直接加prim，否则只有一个元素
    for index,value in enumerate(unique_value):
        blast_node= parent_node.createNode("blast",node_name=f"{attribute_name}_{value}")
        blast_node.parm("group").set(f"@{attribute_name}={value}")
        blast_node.setInput(0,target_node)

        child_nodes.append(blast_node) 

        null_node=parent_node.createNode("null",node_name=f"{value}_output")
        null_node.setInput(0,blast_node)
        merge_node.setInput(index,null_node)
        
        child_nodes.append(null_node)

    child_nodes.append(target_node)
    parent_node.layoutChildren(items=child_nodes)

    merge_node.setDisplayFlag(True)
    merge_node.setRenderFlag(True)