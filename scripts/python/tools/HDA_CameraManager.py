import hou


class MultiCameraManager:
    """
    Helps manager cameras in a houdini scene
    Allow to set cameras-set camera,set frame range
    Allow batch rename camera
    Merge all camera into one single camera
    Render submission
    """

    def __init__(self) -> None:
        self.cameras = {}
        self.obj = hou.node("/obj")
        self.node = hou.pwd()
        self.TIME_DEPENDECY_PARMS = [
            "tx",
            "ty",
            "tz",
            "rx",
            "ry",
            "rz",
            "resx",
            "resy",
            "aspect",
            "focal",
            "aperture",
            "near",
            "far",
            "focus",
            "fstop",
        ]
        print("Finish Init Camera Manager")

    def scan_scene_cameras(self):
        if not self.obj:
            hou.ui.displayMessage(
                "Error: Invalid Parent Node", severity=hou.severityType.Error
            )
            return
        try:
            self.cameras = {
                cam.name(): cam
                for cam in self.obj.recursiveGlob(
                    "*", filter=hou.nodeTypeFilter.ObjCamera
                )
            }
            if len(self.cameras) == 0:
                hou.ui.displayMessage("Find Null Camera In Scene")
                return
            self._create_camera_menu_()
        except Exception as e:
            print(f"Fail to scan camera,with Error:{e}")

    def _create_camera_menu_(self):
        if not self.obj:
            hou.ui.displayMessage(
                "Error: Invalid Parent Node", severity=hou.severityType.Error
            )
            return
        print(f"self.Node:{self.node}")
        node_ptg = self.node.parmTemplateGroup()
        camera_names = list(self.cameras.keys())

        existed_selector = node_ptg.find("cameras_selector")

        camera_menu = hou.MenuParmTemplate(
            name="cameras_selector",
            label="Select Camera",
            menu_items=camera_names,
            menu_labels=camera_names,
        )
        if not existed_selector:
            node_ptg.insertAfter("scan_scene", camera_menu)
        else:
            node_ptg.replace(existed_selector, camera_menu)
        self.node.setParmTemplateGroup(node_ptg)
        self.node.parm("set_visible")._set(1)

    def activate_selected_camera(self):
        camera_name = self.node.parm("cameras_selector").rawValue()
        selected_camera = self.cameras[camera_name]

        view_port: hou.SceneViewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
        if not view_port or not selected_camera:
            print("Fail to Get Viewport")
            return
        # 设置为对应视角
        view_port.curViewport().setCamera(selected_camera)
        # 设置对应的时间轴
        frames=self._get_framespan_by_camera_prams_(selected_camera)
        first_frame=min(frames)
        last_frame=max(frames)
        # 这个设置的是上方刻度条
        hou.playbar.setPlaybackRange(first_frame, last_frame)
        # 这个设置是下方帧范围
        set_global_frame_range=f"tset `({first_frame}-1)/$FPS` `{last_frame}/$FPS`"
        # hou.hscript(set_global_frame_range)
        hou.setFrame(first_frame)

    def _get_framespan_by_camera_prams_(self, in_selected_camera)->list:
        # 查找是否有打了关键帧的参数
        #hou.playbar.playbackRange()[0],hou.playbar.playbackRange()[1]
        if any(
            in_selected_camera.parm(time_parm).isTimeDependent()
            for time_parm in self.TIME_DEPENDECY_PARMS
        ):
            key_frames = []
            for potential_parm in self.TIME_DEPENDECY_PARMS:
                parm_keyframes = in_selected_camera.parm(potential_parm).keyframes()
                if parm_keyframes:
                    key_frames.extend(keyframe.frame() for keyframe in parm_keyframes)
            return key_frames
        else:
            return []


    def merge_cameras(self):
        merged_camera=self.obj.createNode("cam","merged_camera")
        camera_to_merge={}
        for name,camera_ref in self.cameras.items():
           # 可能有重复关键帧.先用set包一层，再转list
           frames=list(set(self._get_framespan_by_camera_prams_(camera_ref)))
           camera_to_merge[name]={
               "camera":camera_ref,
               "frames":frames,
               "start":min(frames) if len(frames)>0 else float("inf"),
               "end":max(frames) if len(frames)>0 else float("inf")
           }
        # 根据start对dict进行排序
        sorted_cameras=dict(sorted(camera_to_merge.items(),key=lambda x:x[1]["start"]))
        view_start=float("inf")
        view_end=0

        for name, data in sorted_cameras.items():
            camera_ref=data["camera"]
            original_frames_data=data["frames"]
            view_start=min(view_start,data["start"])
            if data["end"]!=float("inf"):
                view_end=max(view_end,data["end"])

            if len(original_frames_data)>0:
                # 遍历查询哪些属性有变更
                for parm_name in self.TIME_DEPENDECY_PARMS:
                    source_parm=camera_ref.parm(parm_name)
                    target_parm=merged_camera.parm(parm_name)

                    if source_parm and target_parm:
                        keyframes= source_parm.keyframes()
                        
                        if len(keyframes)>0:
                            for keyframe in keyframes:
                                new_key_frame=hou.Keyframe()
                                new_key_frame.setFrame(keyframe.frame())
                                new_key_frame.setValue(keyframe.value())
                                new_key_frame.setExpression(keyframe.expression())
                                target_parm.setKeyframe(new_key_frame)
                        else:
                            # 不存在多个关键帧但是有值
                            new_key_frame=hou.Keyframe()
                            new_key_frame.setFrame(keyframe.frame())
                            new_key_frame.setValue(keyframe.value())
                            target_parm.setKeyframe(new_key_frame)
            else:
                # 只有单个静帧的相机
                for parm_name in self.TIME_DEPENDECY_PARMS:
                    source_parm=camera_ref.parm(parm_name)
                    target_parm=merged_camera.parm(parm_name)

                    if source_parm and target_parm:
                        new_key_frame=hou.Keyframe()
                        new_key_frame.setValue(keyframe.value())
                        new_key_frame.setFrame(keyframe.frame())
                        target_parm.setKeyframe(new_key_frame)

        if view_start<view_end:
            print(f"Set Framespan {view_start}-{view_end}")
            # 这个设置的是上方刻度条
            hou.playbar.setPlaybackRange(view_start, view_end)
            # 这个设置是下方帧范围
            set_global_frame_range=f"tset `({view_start}-1)/$FPS` `{view_end}/$FPS`"
            # hou.hscript(set_global_frame_range)
            hou.setFrame(view_start)