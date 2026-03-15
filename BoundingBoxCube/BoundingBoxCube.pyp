"""
BoundingBoxCube — Cinema 4D Command Plugin (2024 / 2025+)

Создаёт полигональный куб (6 квадов), точно облекающий выделенный объект,
с настраиваемыми отступами (padding) по каждой оси.

Установка:
    Скопируйте папку BoundingBoxCube/ в папку плагинов Cinema 4D:
      - Windows : %AppData%/Maxon/Maxon Cinema 4D/plugins/
      - macOS   : ~/Library/Preferences/Maxon/Maxon Cinema 4D/plugins/
    Перезапустите Cinema 4D. Плагин появится в меню Extensions (Расширения).
"""

import c4d
from c4d import gui, Vector

# Уникальный ID плагина (зарегистрирован через www.plugincafe.com/forum)
# Для личного использования можно оставить как есть; для публикации —
# получите собственный ID на plugincafe.
PLUGIN_ID = 1063489

# ---------------------------------------------------------------------------
#  ID элементов диалога
# ---------------------------------------------------------------------------
ID_GRP_MAIN      = 10000
ID_GRP_PADDING    = 10001

ID_PADDING_UNIFORM = 10010
ID_PADDING_X       = 10011
ID_PADDING_Y       = 10012
ID_PADDING_Z       = 10013
ID_LINK_PADDING    = 10014   # чекбокс «одинаковый отступ по всем осям»

ID_BTN_CREATE      = 10020


# ---------------------------------------------------------------------------
#  Geometry helpers
# ---------------------------------------------------------------------------

def _get_geometry_points(op, points_world):
    """Рекурсивно собирает мировые координаты точек объекта и его кэшей."""
    cache = op.GetDeformCache() or op.GetCache()
    if cache:
        _get_geometry_points(cache, points_world)

    if op.IsInstanceOf(c4d.Opolygon) or op.IsInstanceOf(c4d.Ospline):
        mg = op.GetMg()
        for p in op.GetAllPoints():
            points_world.append(mg * p)

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
    PolygonObject — куб из 8 вершин и 6 четырёхугольных полигонов.

        3 ---- 2          top:    (3,2,1,0)
       /|     /|          bottom: (4,5,6,7)
      0 ---- 1 |          front:  (0,1,5,4)
      | 7 ---| 6          back:   (2,3,7,6)
      |/     |/           left:   (3,0,4,7)
      4 ---- 5            right:  (1,2,6,5)
    """
    obj = c4d.PolygonObject(8, 6)

    obj.SetPoint(0, Vector(bb_min.x, bb_max.y, bb_min.z))
    obj.SetPoint(1, Vector(bb_max.x, bb_max.y, bb_min.z))
    obj.SetPoint(2, Vector(bb_max.x, bb_max.y, bb_max.z))
    obj.SetPoint(3, Vector(bb_min.x, bb_max.y, bb_max.z))
    obj.SetPoint(4, Vector(bb_min.x, bb_min.y, bb_min.z))
    obj.SetPoint(5, Vector(bb_max.x, bb_min.y, bb_min.z))
    obj.SetPoint(6, Vector(bb_max.x, bb_min.y, bb_max.z))
    obj.SetPoint(7, Vector(bb_min.x, bb_min.y, bb_max.z))

    obj.SetPolygon(0, c4d.CPolygon(3, 2, 1, 0))   # top
    obj.SetPolygon(1, c4d.CPolygon(4, 5, 6, 7))   # bottom
    obj.SetPolygon(2, c4d.CPolygon(0, 1, 5, 4))   # front
    obj.SetPolygon(3, c4d.CPolygon(2, 3, 7, 6))   # back
    obj.SetPolygon(4, c4d.CPolygon(3, 0, 4, 7))   # left
    obj.SetPolygon(5, c4d.CPolygon(1, 2, 6, 5))   # right

    obj.Message(c4d.MSG_UPDATE)
    return obj


def _get_world_points(sel):
    """Возвращает список мировых точек для объекта (с фолбэком на GetRad)."""
    points = []
    _get_geometry_points(sel, points)

    if not points:
        mg = sel.GetMg()
        center = sel.GetMp()
        rad = sel.GetRad()
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    points.append(mg * (center + Vector(sx * rad.x, sy * rad.y, sz * rad.z)))
    return points


# ---------------------------------------------------------------------------
#  Диалог настроек
# ---------------------------------------------------------------------------

class BoundingBoxDialog(gui.GeDialog):

    def CreateLayout(self):
        self.SetTitle("Bounding Box Cube")

        # --- Padding group ---------------------------------------------------
        self.GroupBegin(ID_GRP_PADDING, c4d.BFH_SCALEFIT, cols=2, rows=0,
                        title="Отступы (Padding)")
        self.GroupBorderSpace(10, 10, 10, 10)
        self.GroupBorder(c4d.BORDER_GROUP_IN)

        # Чекбокс «Одинаковый отступ»
        self.AddCheckbox(ID_LINK_PADDING, c4d.BFH_LEFT, 0, 0,
                         "Одинаковый отступ по всем осям")
        self.AddStaticText(0, c4d.BFH_LEFT, name="")  # пустая ячейка

        # Uniform
        self.AddStaticText(0, c4d.BFH_LEFT, name="Отступ:")
        self.AddEditNumberArrows(ID_PADDING_UNIFORM, c4d.BFH_SCALEFIT)

        # Per-axis
        self.AddStaticText(0, c4d.BFH_LEFT, name="Padding X:")
        self.AddEditNumberArrows(ID_PADDING_X, c4d.BFH_SCALEFIT)

        self.AddStaticText(0, c4d.BFH_LEFT, name="Padding Y:")
        self.AddEditNumberArrows(ID_PADDING_Y, c4d.BFH_SCALEFIT)

        self.AddStaticText(0, c4d.BFH_LEFT, name="Padding Z:")
        self.AddEditNumberArrows(ID_PADDING_Z, c4d.BFH_SCALEFIT)

        self.GroupEnd()

        # --- Create button ----------------------------------------------------
        self.AddButton(ID_BTN_CREATE, c4d.BFH_CENTER, 200, 30,
                       "Создать контейнер")

        return True

    def InitValues(self):
        self.SetBool(ID_LINK_PADDING, True)
        self.SetFloat(ID_PADDING_UNIFORM, 0.0, min=0.0, max=100000.0, step=1.0)
        self.SetFloat(ID_PADDING_X, 0.0, min=0.0, max=100000.0, step=1.0)
        self.SetFloat(ID_PADDING_Y, 0.0, min=0.0, max=100000.0, step=1.0)
        self.SetFloat(ID_PADDING_Z, 0.0, min=0.0, max=100000.0, step=1.0)
        self._update_padding_visibility()
        return True

    # -- UI helpers -----------------------------------------------------------

    def _update_padding_visibility(self):
        linked = self.GetBool(ID_LINK_PADDING)
        self.Enable(ID_PADDING_UNIFORM, linked)
        self.Enable(ID_PADDING_X, not linked)
        self.Enable(ID_PADDING_Y, not linked)
        self.Enable(ID_PADDING_Z, not linked)

    # -- Events ---------------------------------------------------------------

    def Command(self, msg_id, msg):
        if msg_id == ID_LINK_PADDING:
            self._update_padding_visibility()
            return True

        if msg_id == ID_BTN_CREATE:
            self._create_bounding_box()
            return True

        return True

    # -- Core logic -----------------------------------------------------------

    def _create_bounding_box(self):
        doc = c4d.documents.GetActiveDocument()
        sel = doc.GetActiveObject()

        if sel is None:
            gui.MessageDialog("Выделите объект в сцене.")
            return

        points = _get_world_points(sel)
        if not points:
            gui.MessageDialog("Не удалось определить размеры объекта.")
            return

        bb_min, bb_max = _compute_aabb(points)

        # Применяем padding
        linked = self.GetBool(ID_LINK_PADDING)
        if linked:
            pad = self.GetFloat(ID_PADDING_UNIFORM)
            pad_vec = Vector(pad, pad, pad)
        else:
            pad_vec = Vector(
                self.GetFloat(ID_PADDING_X),
                self.GetFloat(ID_PADDING_Y),
                self.GetFloat(ID_PADDING_Z),
            )

        bb_min -= pad_vec
        bb_max += pad_vec

        cube = _build_cube_polygon_object(bb_min, bb_max)
        cube.SetName("BoundingBox_" + sel.GetName())

        doc.StartUndo()
        doc.InsertObject(cube)
        doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, cube)
        doc.EndUndo()
        c4d.EventAdd()


# ---------------------------------------------------------------------------
#  Команда плагина
# ---------------------------------------------------------------------------

class BoundingBoxCubeCommand(c4d.plugins.CommandData):

    _dialog = None

    def Execute(self, doc):
        if self._dialog is None:
            self._dialog = BoundingBoxDialog()
        return self._dialog.Open(
            dlgtype=c4d.DLG_TYPE_ASYNC,
            pluginid=PLUGIN_ID,
            defaultw=340,
            defaulth=220,
        )

    def RestoreLayout(self, sec_ref):
        if self._dialog is None:
            self._dialog = BoundingBoxDialog()
        return self._dialog.Restore(pluginid=PLUGIN_ID, secret=sec_ref)


# ---------------------------------------------------------------------------
#  Регистрация
# ---------------------------------------------------------------------------

def main():
    c4d.plugins.RegisterCommandPlugin(
        id=PLUGIN_ID,
        str="Bounding Box Cube",
        info=0,
        icon=None,
        help="Создаёт полигональный куб-контейнер вокруг выделенного объекта",
        dat=BoundingBoxCubeCommand(),
    )


if __name__ == "__main__":
    main()
