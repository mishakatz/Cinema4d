"""
Random Effector Seed Changer — Python Tag для Cinema 4D 2024/2025+

Скрипт для Python-тега, который находит в сцене Random Effector
и каждые N кадров меняет ему seed на новое значение.

Настройка:
    1. Создайте Python Tag на любом объекте в сцене.
    2. Вставьте этот код в Python Tag.
    3. В User Data тега появятся параметры:
       - Frame Interval: через сколько кадров менять seed (по умолчанию 10)
       - Effector Name: имя Random Effector в сцене (по умолчанию "Random")
       - Seed Offset: шаг изменения seed (по умолчанию 1)

Как это работает:
    Скрипт проверяет текущий кадр. Каждый раз, когда номер кадра
    кратен заданному интервалу, Random Effector получает новый seed.
"""

import c4d

# ID параметров User Data
UD_FRAME_INTERVAL = 1   # Интервал в кадрах
UD_EFFECTOR_NAME  = 2   # Имя эффектора в сцене
UD_SEED_OFFSET    = 3   # Шаг seed

# ID параметра seed в Random Effector
RANDOM_EFFECTOR_SEED = c4d.MGRANDOMEFFECTOR_SEED


def add_userdata(tag):
    """Создаёт User Data параметры на теге, если их ещё нет."""

    ud = tag.GetUserDataContainer()
    existing_ids = {desc[0][1].id for desc in ud}

    # Frame Interval
    if UD_FRAME_INTERVAL not in existing_ids:
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_LONG)
        bc[c4d.DESC_NAME] = "Frame Interval"
        bc[c4d.DESC_SHORT_NAME] = "Interval"
        bc[c4d.DESC_DEFAULT] = 10
        bc[c4d.DESC_MIN] = 1
        bc[c4d.DESC_MAX] = 10000
        tag.AddUserData(bc)
        tag[c4d.ID_USERDATA, UD_FRAME_INTERVAL] = 10

    # Effector Name
    if UD_EFFECTOR_NAME not in existing_ids:
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING)
        bc[c4d.DESC_NAME] = "Effector Name"
        bc[c4d.DESC_SHORT_NAME] = "Name"
        bc[c4d.DESC_DEFAULT] = "Random"
        tag.AddUserData(bc)
        tag[c4d.ID_USERDATA, UD_EFFECTOR_NAME] = "Random"

    # Seed Offset
    if UD_SEED_OFFSET not in existing_ids:
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_LONG)
        bc[c4d.DESC_NAME] = "Seed Offset"
        bc[c4d.DESC_SHORT_NAME] = "Offset"
        bc[c4d.DESC_DEFAULT] = 1
        bc[c4d.DESC_MIN] = 1
        bc[c4d.DESC_MAX] = 100000
        tag.AddUserData(bc)
        tag[c4d.ID_USERDATA, UD_SEED_OFFSET] = 1


def find_object_by_name(doc, name):
    """Ищет объект по имени во всей иерархии сцены."""

    def search(op, name):
        while op:
            if op.GetName() == name:
                return op
            found = search(op.GetDown(), name)
            if found:
                return found
            op = op.GetNext()
        return None

    return search(doc.GetFirstObject(), name)


def find_random_effector(doc, name):
    """
    Ищет Random Effector по имени.
    Сначала ищет среди объектов сцены (MoGraph эффекторы — это объекты).
    """
    obj = find_object_by_name(doc, name)
    if obj and obj.CheckType(c4d.Omgrandomeffector):
        return obj
    return None


def main():
    doc = c4d.documents.GetActiveDocument()
    tag = op  # op — это текущий Python Tag

    # Создаём User Data при первом запуске
    add_userdata(tag)

    # Читаем параметры
    interval = tag[c4d.ID_USERDATA, UD_FRAME_INTERVAL]
    effector_name = tag[c4d.ID_USERDATA, UD_EFFECTOR_NAME]
    seed_offset = tag[c4d.ID_USERDATA, UD_SEED_OFFSET]

    if not interval or interval < 1:
        interval = 10
    if not effector_name:
        effector_name = "Random"
    if not seed_offset or seed_offset < 1:
        seed_offset = 1

    # Текущий кадр
    frame = doc.GetTime().GetFrame(doc.GetFps())

    # Проверяем, кратен ли текущий кадр интервалу
    if frame % interval != 0:
        return

    # Находим Random Effector
    effector = find_random_effector(doc, effector_name)
    if effector is None:
        return

    # Вычисляем новый seed на основе текущего кадра
    new_seed = (frame // interval) * seed_offset

    # Устанавливаем новый seed
    effector[RANDOM_EFFECTOR_SEED] = new_seed
    effector.Message(c4d.MSG_UPDATE)
    c4d.EventAdd()
