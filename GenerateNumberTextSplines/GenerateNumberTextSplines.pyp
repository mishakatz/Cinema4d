"""
GenerateNumberTextSplines — Cinema 4D Command Plugin

Генерирует строку цифр в виде Text Spline объектов.
Задаёте начальное и конечное число — скрипт создаёт Text Spline
для каждого числа в диапазоне и располагает их в ряд по оси X.

Установка:
    Скопируйте папку GenerateNumberTextSplines/ в папку плагинов Cinema 4D:
      - Windows : %AppData%/Maxon/Maxon Cinema 4D/plugins/
      - macOS   : ~/Library/Preferences/Maxon/Maxon Cinema 4D/plugins/
    Перезапустите Cinema 4D. Плагин появится в меню Extensions (Расширения).
"""

import c4d
from c4d import gui, Vector

PLUGIN_ID = 1063490

# ---------------------------------------------------------------------------
#  ID элементов диалога
# ---------------------------------------------------------------------------
ID_GRP_MAIN       = 20000
ID_GRP_RANGE      = 20001
ID_GRP_SETTINGS   = 20002

ID_NUM_FROM        = 20010
ID_NUM_TO          = 20011
ID_HEIGHT          = 20012
ID_SPACING         = 20013

ID_BTN_CREATE      = 20020


# ---------------------------------------------------------------------------
#  Диалог настроек
# ---------------------------------------------------------------------------

class NumberSplineDialog(gui.GeDialog):

    def CreateLayout(self):
        self.SetTitle("Generate Number Text Splines")

        # --- Диапазон чисел --------------------------------------------------
        self.GroupBegin(ID_GRP_RANGE, c4d.BFH_SCALEFIT, cols=2, rows=0,
                        title="Диапазон")
        self.GroupBorderSpace(10, 10, 10, 10)
        self.GroupBorder(c4d.BORDER_GROUP_IN)

        self.AddStaticText(0, c4d.BFH_LEFT, name="Начальное число:")
        self.AddEditNumberArrows(ID_NUM_FROM, c4d.BFH_SCALEFIT)

        self.AddStaticText(0, c4d.BFH_LEFT, name="Конечное число:")
        self.AddEditNumberArrows(ID_NUM_TO, c4d.BFH_SCALEFIT)

        self.GroupEnd()

        # --- Настройки -------------------------------------------------------
        self.GroupBegin(ID_GRP_SETTINGS, c4d.BFH_SCALEFIT, cols=2, rows=0,
                        title="Настройки")
        self.GroupBorderSpace(10, 10, 10, 10)
        self.GroupBorder(c4d.BORDER_GROUP_IN)

        self.AddStaticText(0, c4d.BFH_LEFT, name="Высота текста:")
        self.AddEditNumberArrows(ID_HEIGHT, c4d.BFH_SCALEFIT)

        self.AddStaticText(0, c4d.BFH_LEFT, name="Расстояние между:")
        self.AddEditNumberArrows(ID_SPACING, c4d.BFH_SCALEFIT)

        self.GroupEnd()

        # --- Кнопка ----------------------------------------------------------
        self.AddButton(ID_BTN_CREATE, c4d.BFH_CENTER, 200, 30,
                       "Создать")

        return True

    def InitValues(self):
        self.SetInt32(ID_NUM_FROM, 1, min=-99999, max=99999, step=1)
        self.SetInt32(ID_NUM_TO, 10, min=-99999, max=99999, step=1)
        self.SetFloat(ID_HEIGHT, 200.0, min=1.0, max=100000.0, step=1.0)
        self.SetFloat(ID_SPACING, 250.0, min=0.0, max=100000.0, step=1.0)
        return True

    # -- Events ---------------------------------------------------------------

    def Command(self, msg_id, msg):
        if msg_id == ID_BTN_CREATE:
            self._create_number_splines()
            return True
        return True

    # -- Core logic -----------------------------------------------------------

    def _create_number_splines(self):
        doc = c4d.documents.GetActiveDocument()

        num_from = self.GetInt32(ID_NUM_FROM)
        num_to = self.GetInt32(ID_NUM_TO)
        height = self.GetFloat(ID_HEIGHT)
        spacing = self.GetFloat(ID_SPACING)

        if num_from > num_to:
            num_from, num_to = num_to, num_from

        count = num_to - num_from + 1

        # Создаём родительский Null
        parent = c4d.BaseObject(c4d.Onull)
        parent.SetName("Numbers_{0}-{1}".format(num_from, num_to))

        doc.StartUndo()
        doc.InsertObject(parent)
        doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, parent)

        for i, num in enumerate(range(num_from, num_to + 1)):
            # Создаём Text Spline
            text_spline = c4d.BaseObject(c4d.Osplinetext)
            text_spline.SetName(str(num))

            # Устанавливаем текст и высоту
            text_spline[c4d.PRIM_TEXT_TEXT] = str(num)
            text_spline[c4d.PRIM_TEXT_HEIGHT] = height
            text_spline[c4d.PRIM_TEXT_ALIGN] = 1  # Center

            # Позиция по оси X
            pos = Vector(i * spacing, 0, 0)
            text_spline.SetAbsPos(pos)

            # Вставляем как дочерний объект Null
            doc.InsertObject(text_spline, parent=parent)
            doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, text_spline)

        doc.EndUndo()
        c4d.EventAdd()

        gui.MessageDialog("Создано {0} объектов Text Spline ({1}...{2})".format(
            count, num_from, num_to))


# ---------------------------------------------------------------------------
#  Команда плагина
# ---------------------------------------------------------------------------

class GenerateNumberTextSplinesCommand(c4d.plugins.CommandData):

    _dialog = None

    def Execute(self, doc):
        if self._dialog is None:
            self._dialog = NumberSplineDialog()
        return self._dialog.Open(
            dlgtype=c4d.DLG_TYPE_ASYNC,
            pluginid=PLUGIN_ID,
            defaultw=360,
            defaulth=260,
        )

    def RestoreLayout(self, sec_ref):
        if self._dialog is None:
            self._dialog = NumberSplineDialog()
        return self._dialog.Restore(pluginid=PLUGIN_ID, secret=sec_ref)


# ---------------------------------------------------------------------------
#  Регистрация
# ---------------------------------------------------------------------------

def main():
    c4d.plugins.RegisterCommandPlugin(
        id=PLUGIN_ID,
        str="Generate Number Text Splines",
        info=0,
        icon=None,
        help="Генерирует строку цифр в виде Text Spline объектов",
        dat=GenerateNumberTextSplinesCommand(),
    )


if __name__ == "__main__":
    main()
