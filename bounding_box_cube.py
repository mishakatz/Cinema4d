"""
Bounding Box Cube — Cinema 4D Python Script (2025+)

Создаёт полигональный куб (6 квадов), который точно облекает
выделенный объект, включая все дочерние объекты и кэши генераторов
(Cloner, Array, Boole и т.д.).

Использование: выделите объект в сцене и запустите скрипт.
"""

import c4d
from c4d import Vector


# ---------------------------------------------------------------------------
#  Вспомогательные функции
# ---------------------------------------------------------------------------

def _get_geometry_points(op, points_world):
    """Рекурсивно собирает мировые координаты точек объекта и его кэшей."""

    # Попробовать деформ-кэш, потом обычный кэш (для генераторов / клонеров)
    cache = op.GetDeformCache() or op.GetCache()
    if cache:
        _get_geometry_points(cache, points_world)

    # Если сам объект — полигональный/сплайновый, собираем его точки
    if op.IsInstanceOf(c4d.Opolygon) or op.IsInstanceOf(c4d.Ospline):
        mg = op.GetMg()
        all_pts = op.GetAllPoints()
        for p in all_pts:
            points_world.append(mg * p)

    # Обходим дочерние объекты
    child = op.GetDown()
    while child:
        _get_geometry_points(child, points_world)
        child = child.GetNext()


def _compute_aabb(points):
    """Возвращает (min_vec, max_vec) — углы axis-aligned bounding box."""
    bb_min = Vector(points[0])
    bb_max = Vector(points[0])
    for p in points:
        if p.x < bb_min.x: bb_min.x = p.x
        if p.y < bb_min.y: bb_min.y = p.y
        if p.z < bb_min.z: bb_min.z = p.z
        if p.x > bb_max.x: bb_max.x = p.x
        if p.y > bb_max.y: bb_max.y = p.y
        if p.z > bb_max.z: bb_max.z = p.z
    return bb_min, bb_max


def _build_cube_polygon_object(bb_min, bb_max):
    """
    Создаёт c4d.PolygonObject — куб из 8 вершин и 6 четырёхугольных полигонов,
    точно соответствующий переданному bounding box.

    Раскладка вершин (Y — вверх, Z — вглубь):

        3 ---- 2          top:    (3,2,1,0)
       /|     /|          bottom: (4,5,6,7)
      0 ---- 1 |          front:  (0,1,5,4)  (ближняя к камере, -Z)
      | 7 ---| 6          back:   (2,3,7,6)  (дальняя, +Z)
      |/     |/           left:   (3,0,4,7)
      4 ---- 5            right:  (1,2,6,5)
    """
    obj = c4d.PolygonObject(8, 6)

    # 8 вершин
    obj.SetPoint(0, Vector(bb_min.x, bb_max.y, bb_min.z))
    obj.SetPoint(1, Vector(bb_max.x, bb_max.y, bb_min.z))
    obj.SetPoint(2, Vector(bb_max.x, bb_max.y, bb_max.z))
    obj.SetPoint(3, Vector(bb_min.x, bb_max.y, bb_max.z))
    obj.SetPoint(4, Vector(bb_min.x, bb_min.y, bb_min.z))
    obj.SetPoint(5, Vector(bb_max.x, bb_min.y, bb_min.z))
    obj.SetPoint(6, Vector(bb_max.x, bb_min.y, bb_max.z))
    obj.SetPoint(7, Vector(bb_min.x, bb_min.y, bb_max.z))

    # 6 полигонов (CPolygon: a, b, c, d — порядок обхода нормали наружу)
    obj.SetPolygon(0, c4d.CPolygon(3, 2, 1, 0))  # top
    obj.SetPolygon(1, c4d.CPolygon(4, 5, 6, 7))  # bottom
    obj.SetPolygon(2, c4d.CPolygon(0, 1, 5, 4))  # front (-Z)
    obj.SetPolygon(3, c4d.CPolygon(2, 3, 7, 6))  # back  (+Z)
    obj.SetPolygon(4, c4d.CPolygon(3, 0, 4, 7))  # left
    obj.SetPolygon(5, c4d.CPolygon(1, 2, 6, 5))  # right

    obj.Message(c4d.MSG_UPDATE)
    return obj


# ---------------------------------------------------------------------------
#  Главная функция
# ---------------------------------------------------------------------------

def main():
    doc = c4d.documents.GetActiveDocument()
    sel = doc.GetActiveObject()

    if sel is None:
        c4d.gui.MessageDialog("Пожалуйста, выделите объект в сцене.")
        return

    # Собираем все мировые точки выделенного объекта (с дочерними и кэшами)
    points = []
    _get_geometry_points(sel, points)

    if not points:
        # Если точек не нашлось (пустой нулл, камера и т.п.) — фолбэк на GetRad/GetMp
        mg = sel.GetMg()
        center = sel.GetMp()
        rad = sel.GetRad()
        # Строим 8 углов из центра и радиуса в мировых координатах
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    points.append(mg * (center + Vector(sx * rad.x, sy * rad.y, sz * rad.z)))

    if not points:
        c4d.gui.MessageDialog("Не удалось определить размеры объекта.")
        return

    bb_min, bb_max = _compute_aabb(points)

    # Создаём полигональный куб-контейнер
    cube = _build_cube_polygon_object(bb_min, bb_max)
    cube.SetName("BoundingBox_" + sel.GetName())

    doc.StartUndo()
    doc.InsertObject(cube)
    doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, cube)
    doc.EndUndo()

    c4d.EventAdd()


if __name__ == "__main__":
    main()
