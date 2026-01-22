import hou
import viewerstate.utils as su


class State(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

        print(kwargs)
        self.scene_viewer:hou.SceneViewer=kwargs["scene_viewer"]
        self.node=hou.node("/obj")
        self.light=None
        self.light_distance=1.0

        self.hit_location:hou.Vector3
        self.light_dir:hou.Vector3
        self.light_position:hou.Vector3

        self.guide_line_container=hou.GeometryDrawable(scene_viewer=self.scene_viewer, geo_type=hou.drawableGeometryType.Line, name="light_guide_line")
        self.guide_line_container.show(False)

    def _create_guide_line_geo_(self):
        '''
        创建灯光用于Debug的几何体
        '''
        # 先做基础检查
        if not self.light or not self.hit_location:
            return
        # 获取点的两端 self.hit_location,
        light_location=hou.Vector3(self.light.worldTransform().extractTranslates())

        # 构造线几何体
        guide_line_geo=hou.Geometry()
        points=[]
        points.append(guide_line_geo.createPoints([self.hit_location,light_location]))
        guide_line_geo.createPolygons(points,False)

        self.guide_line_container.setGeometry(guide_line_geo)

    def onEnter(self, kwargs):
        """Called on node bound states when it starts"""
        state_parms = kwargs["state_parms"]

    def onExit(self, kwargs):
        """Called when the state terminates"""
        state_parms = kwargs["state_parms"]
        self.guide_line_container.show(False)

    def onInterrupt(self, kwargs):
        """Called when the state is interrupted e.g when the mouse
        moves outside the viewport
        """
        pass

    def onResume(self, kwargs):
        """Called when an interrupted state resumes"""
        self.guide_line_container.show(True)
        pass

    def _get_light_position_by_reflection_(self,in_current_viewport:hou.GeometryViewport,in_mouse_x:int,in_mouse_y:int)->bool:
        trace_object=in_current_viewport.queryNodeAtPixel(in_mouse_x,in_mouse_y)
        
        # 忽略空对象和灯光对象
        ignore_nodes=["hlight::2.0"]
        if not trace_object or trace_object.type() in ignore_nodes:
            return False
        obj_transform:hou.Matrix4=trace_object.worldTransform()
        # trace到的几何体,不要从这里拿transform，没有这个属性
        geo_object=trace_object.displayNode().geometry()
        

        view_dir,mouse_position= in_current_viewport.mapToWorld(in_mouse_x,in_mouse_y)
        view_dir=view_dir.normalized()
        #射线检测需要在对象空间
        view_dir_local=view_dir.multiplyAsDir(obj_transform.inverted())
        mouse_position_local=mouse_position*obj_transform.inverted()

        primitive_number,hit_position_local,hit_normal_local,uvw_coordinates=su.sopGeometryIntersection(geo_object,mouse_position_local,view_dir_local)
        # 转换回世界坐标
        self.hit_location=hit_position_local*obj_transform
        hit_normal=hit_normal_local.multiplyAsDir(obj_transform).normalized()

        # 计算反射方向https://zhuanlan.zhihu.com/p/555451478
        reflect_dir=2*view_dir.dot(hit_normal)*hit_normal-view_dir

        # 上面是以相机为射源计算方向，实际应该反过来
        self.light_dir=-reflect_dir
        self.light_position=self.hit_location+(self.light_dir*self.light_distance)

        return True

    def onMouseEvent(self, kwargs):
        """Process mouse and tablet events"""
        ui_event = kwargs["ui_event"]
        mouse_operation=ui_event.reason()
        dev:hou.UIEventDevice = ui_event.device()
        # 在窗口下方显示提示文字
        self.scene_viewer.setPromptMessage("Chick with LMB or Press and Drag LMB to Place Light")
        if mouse_operation==hou.uiEventReason.Picked or mouse_operation==hou.uiEventReason.Active:
            if self.light:
                # 获取当前视口
                current_viewport:hou.GeometryViewport= self.scene_viewer.curViewport()
                # 鼠标左键按下或者按下+拖拽
                
                bsuccess:bool=self._get_light_position_by_reflection_(current_viewport,int(dev.mouseX()),int(dev.mouseY()))

                if bsuccess:
                    light_matrix=hou.hmath.buildRotateZToAxis(self.light_dir)
                    light_matrix*=hou.hmath.buildTranslate(self.light_position)
                    self.light.setWorldTransform(light_matrix)

                    self._create_guide_line_geo_()
                    self.guide_line_container.show(True)
                    return True
        return False

    def onMouseWheelEvent(self, kwargs):
        """Process a mouse wheel event"""

        ui_event = kwargs["ui_event"]
        state_parms = kwargs["state_parms"]

        device=ui_event.device()
        scroll_value=device.mouseWheel()
        delta_value=scroll_value/10.0
        if self.light:
            
            self.light_distance=max(1.0,self.light_distance+delta_value)
            self.light_position=self.hit_location+(self.light_dir*self.light_distance)
            light_matrix=hou.hmath.buildRotateZToAxis(self.light_dir)
            light_matrix*=hou.hmath.buildTranslate(self.light_position)
            self.light.setWorldTransform(light_matrix)

            self._create_guide_line_geo_()

        # Must return True to consume the event
        return False

    def onMenuAction(self, kwargs):
        """Callback implementing the actions of a bound menu. Called
        when a menu item has been selected.
        """

        menu_item = kwargs["menu_item"]
        state_parms = kwargs["state_parms"]

    def onKeyEvent(self, kwargs):
        """Called for processing a keyboard event"""
        ui_event = kwargs["ui_event"]
        state_parms = kwargs["state_parms"]

        # Must returns True to consume the event
        return False

    def onDraw(self, kwargs):
        """Called for rendering a state e.g. required for
        hou.AdvancedDrawable objects
        """
        draw_handle = kwargs["draw_handle"]

        draw_parms={
            "color1":(0.5,0.85,0.25,0.85),
            "fade_factor":1.0,
            "style":hou.drawableGeometryLineStyle.Dot2,
            "glow_width":2,
            "line_width":5,
            "highlight_mode":hou.drawableHighlightMode.Matte,
            "use_cd":True,
            "use_uv":True
        }
    
        self.guide_line_container.draw(draw_handle,draw_parms)

    def onSelection(self, kwargs):
        """Called when a selector has selected something"""
        selection = kwargs["selection"]
        state_parms = kwargs["state_parms"]
        selector_name=kwargs["name"]
        
        if len(selection)!=1:
            print(f"Can not handle Multi or None Selection,{selection}")
            return False
        
        if selector_name=="light_selection" and selection[0]:
            self.light=selection[0]
            #hou.ui.displayMessage(f"Select Light: {self.light.name()}",severity=hou.severityType.Message)
        #if selection

        # Must return True to accept the selection
        return False

    def onGenerate(self, kwargs):
        """Called when a nodeless state starts"""
        state_parms = kwargs["state_parms"]


def createViewerStateTemplate():
    """Mandatory entry point to create and return the viewer state
    template to register."""

    state_typename = "_place_light"
    state_label = "Place Light Highlight"
    state_cat = hou.objNodeTypeCategory()

    template = hou.ViewerStateTemplate(state_typename, state_label, state_cat)
    template.bindFactory(State)
    template.bindIcon("MISC_python")    
    print("Enter Place Light")
    template.bindObjectSelector(
        prompt="Select A Light",
        quick_select=True,
        auto_start=True,
        use_existing_selection=False,
        allow_multisel=False,
        secure_selection=hou.secureSelectionOption.Ignore,
        allowed_types=("hlight::2.0",),
        name="light_selection",
    )

    return template
