import hou
import numpy as np
import scipy.spatial as spatial


def create_convex_cull(
    in_geo:hou.Geometry,
    points:list[hou.Vector3],
    in_bnormlaize: bool = True,
    in_bfilp_normal: bool = True,
    in_bsimplify: bool = True,
    in_level_of_detail: float = 1.0,
):
    '''
    根据传入几何体创建凸包
    
    :param in_geo: 传入几何体
    :param points: 几何体点信息
    :param in_bnormlaize: 是否进行标准化法线方向
    :type in_bnormlaize: bool
    :param in_bfilp_normal: 是否反转法线
    :type in_bfilp_normal: bool
    :param in_bsimplify: 是否进行简化
    :type in_bsimplify: bool
    :param in_level_of_detail: 简化级别
    :type in_level_of_detail: float
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.ConvexHull.html
    '''
    try:
        print("Begin Creating Convex Hull")
        points_array=np.array([(p.x(),p.y(),p.z())for p in points])
        # 简化点
        if in_bsimplify and in_level_of_detail>0:
            grid_size=in_level_of_detail
            # 这步的意义是网格化，把空间按照grid_size切分为格子，各自内的点吸附到附近的网格点上
            grid_points=np.round(points_array/grid_size)*grid_size
            # axis=0表示按行去重，因为每个点作为一行
            unique_points=np.unique(grid_points,axis=0)
            hull_input=unique_points
        else:
            hull_input=points_array

        hull=spatial.ConvexHull(hull_input)

        # 求凸包几何中心,hull.vertices返回构成凸包的点序号
        hull_points_pos=hull_input[hull.vertices]
        centroid=np.mean(hull_points_pos,axis=0)
        centroid_pos=hou.Vector3(centroid[0],centroid[1],centroid[2])

        # 原来的形体完全抛弃，仅用hou.geometry的容器即可
        in_geo.clear()
        hull_points=[]

        for hull_vert in range(len(hull.vertices)):
            new_point= in_geo.createPoint()
            pos=hull_input[hull.vertices[hull_vert]]
            new_point.setPosition((pos[0],pos[1],pos[2]))
            hull_points.append(new_point)

        for face in hull.simplices:
            new_face=in_geo.createPolygon()
            verts_for_face=[]
            for id in face:
                #where返回满足条件的矩阵行列坐标，[0][0]相当于(array([2]),)中取出2
                vert_id=np.where(hull.vertices==id)[0][0]
                verts_for_face.append(hull_points[vert_id])

            if len(verts_for_face)>=3 and in_bnormlaize:
                v1=verts_for_face[1].position()-verts_for_face[0].position()
                v2=verts_for_face[2].position()-verts_for_face[0].position()
                normal=v1.cross(v2)
                normal=normal.normalized()

                center_to_face= verts_for_face[0].position()-centroid_pos
                dot_value=normal.dot(center_to_face)
                bis_filpped=dot_value<0
                if in_bfilp_normal and bis_filpped:
                    verts_for_face.reverse()

            for ordered_point in verts_for_face:
                new_face.addVertex(ordered_point)

        print("End Creating Convex Hull")
    except Exception as error:
        raise RuntimeError(f"Fail to create convex hull in[create_convex_cull]:Error {error}") 
