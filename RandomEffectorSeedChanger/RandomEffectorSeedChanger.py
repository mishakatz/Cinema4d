"""
Random Effector Seed Changer — Python Tag для Cinema 4D 2024/2025+

Скрипт для Python-тега: находит Random Effector в сцене
и каждые N кадров меняет ему seed.

Настройка:
    1. Создайте Python Tag на любом объекте.
    2. Вставьте этот код.
    3. Вручную добавьте User Data на теге (правый клик → User Data → Add User Data):
       - "Frame Interval" (Integer) — через сколько кадров менять seed
       - "Seed Offset" (Integer) — шаг seed
    4. Убедитесь, что Random Effector в сцене называется "Random"
       (или измените переменную EFFECTOR_NAME ниже).
"""

import c4d

# ============================================================
# НАСТРОЙКИ — меняйте здесь
# ============================================================
EFFECTOR_NAME  = "Random"   # Имя Random Effector в сцене
FRAME_INTERVAL = 10         # Через сколько кадров менять seed
SEED_OFFSET    = 1          # Шаг изменения seed
# ============================================================

# Тип Random Effector (MoGraph)
RANDOM_EFFECTOR_TYPE = 1018643


def find_effector(doc, name):
    """Рекурсивный поиск объекта по имени и типу Random Effector."""

    def recurse(obj):
        while obj:
            if obj.GetName() == name and obj.GetType() == RANDOM_EFFECTOR_TYPE:
                return obj
            found = recurse(obj.GetDown())
            if found:
                return found
            obj = obj.GetNext()
        return None

    return recurse(doc.GetFirstObject())


def main():
    doc = c4d.documents.GetActiveDocument()

    # Читаем User Data если есть, иначе используем константы сверху
    tag = op

    interval = FRAME_INTERVAL
    offset = SEED_OFFSET

    # Пробуем прочитать User Data (ID 1 = interval, ID 2 = offset)
    try:
        val = tag[c4d.ID_USERDATA, 1]
        if val is not None and val >= 1:
            interval = int(val)
    except Exception:
        pass

    try:
        val = tag[c4d.ID_USERDATA, 2]
        if val is not None and val >= 1:
            offset = int(val)
    except Exception:
        pass

    # Текущий кадр
    fps = doc.GetFps()
    frame = doc.GetTime().GetFrame(fps)

    # Проверяем кратность кадра интервалу
    if frame % interval != 0:
        return

    # Ищем Random Effector
    effector = find_effector(doc, EFFECTOR_NAME)
    if effector is None:
        print("[SeedChanger] Random Effector '{}' не найден!".format(EFFECTOR_NAME))
        return

    # Новый seed
    new_seed = (frame // interval) * offset

    # Пробуем установить seed разными способами (совместимость версий)
    seed_set = False

    # Способ 1: MGRANDOMEFFECTOR_SEED
    if hasattr(c4d, "MGRANDOMEFFECTOR_SEED"):
        effector[c4d.MGRANDOMEFFECTOR_SEED] = new_seed
        seed_set = True

    # Способ 2: ID_MG_BASEEFFECTOR_SEED
    if not seed_set and hasattr(c4d, "ID_MG_BASEEFFECTOR_SEED"):
        effector[c4d.ID_MG_BASEEFFECTOR_SEED] = new_seed
        seed_set = True

    # Способ 3: прямой числовой ID seed параметра
    if not seed_set:
        # Перебираем описание объекта и ищем параметр с "seed" в имени
        desc = effector.GetDescription(c4d.DESCFLAGS_DESC_NONE)
        for bc, paramid, groupid in desc:
            name = bc[c4d.DESC_NAME]
            if name and "seed" in name.lower():
                effector[paramid] = new_seed
                seed_set = True
                break

    if seed_set:
        effector.Message(c4d.MSG_UPDATE)
        c4d.EventAdd()
