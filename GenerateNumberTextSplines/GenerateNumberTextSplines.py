"""
GenerateNumberTextSplines — Cinema 4D Script (Script Manager)

Генерирует строку цифр в виде Text Spline объектов.
Настройки задаются в переменных ниже.

Использование:
    1. Откройте Script Manager (Extensions > Script Manager)
    2. Вставьте этот скрипт
    3. Измените настройки ниже при необходимости
    4. Нажмите Execute
"""

import c4d
from c4d import Vector

# ---- НАСТРОЙКИ ----
NUM_FROM = 1        # Начальное число
NUM_TO   = 4        # Конечное число
HEIGHT   = 200.0    # Высота текста
SPACING  = 250.0    # Расстояние между числами по оси X
# -------------------

def main():
    num_from = NUM_FROM
    num_to = NUM_TO

    if num_from > num_to:
        num_from, num_to = num_to, num_from

    doc = c4d.documents.GetActiveDocument()

    parent = c4d.BaseObject(c4d.Onull)
    parent.SetName("Numbers_{0}-{1}".format(num_from, num_to))

    doc.StartUndo()
    doc.InsertObject(parent)
    doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, parent)

    count = num_to - num_from + 1
    offset = (count - 1) * SPACING * 0.5

    # Вставляем в обратном порядке, чтобы в Object Manager порядок был 1,2,3,4
    for i, num in enumerate(reversed(range(num_from, num_to + 1))):
        idx = count - 1 - i  # позиция по X: 0,1,2,...
        text_spline = c4d.BaseObject(c4d.Osplinetext)
        text_spline.SetName(str(num))
        text_spline[c4d.PRIM_TEXT_TEXT] = str(num)
        text_spline[c4d.PRIM_TEXT_HEIGHT] = HEIGHT
        text_spline[c4d.PRIM_TEXT_ALIGN] = 1  # Center
        text_spline.SetAbsPos(Vector(idx * SPACING - offset, 0, 0))
        doc.InsertObject(text_spline, parent=parent)
        doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, text_spline)

    doc.EndUndo()
    c4d.EventAdd()

if __name__ == "__main__":
    main()
