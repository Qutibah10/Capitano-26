def calc_group_match_points(pred_winner, real_winner):
    """
    حساب نقاط مباراة من دور المجموعات.

    pred_winner = توقع اللاعب
    real_winner = النتيجة الحقيقية

    القيم الممكنة:
    "A" = الفريق الأول فاز
    "B" = الفريق الثاني فاز
    "DRAW" = تعادل

    النظام:
    - فوز/خسارة صحيح = 3 نقاط
    - تعادل صحيح = 4 نقاط
    - توقع خاطئ = 0
    """

    pred_winner = str(pred_winner).strip().upper()
    real_winner = str(real_winner).strip().upper()

    if pred_winner != real_winner:
        return 0

    if real_winner == "DRAW":
        return 4

    return 3


def calc_group_ranking_points(predicted_order, real_order):
    """
    حساب نقاط ترتيب المجموعة.

    predicted_order = ترتيب اللاعب المتوقع
    real_order = الترتيب الحقيقي

    النظام الجديد:
    - نحاسب فقط أول 3 مراكز.
    - كل مركز صحيح من أول 3 = 1 نقطة.
    - المركز الرابع لا يعطي نقاط.
    - الحد الأقصى لكل مجموعة = 3 نقاط.
    """

    if not predicted_order or not real_order:
        return 0

    points = 0

    max_positions = min(3, len(predicted_order), len(real_order))

    for i in range(max_positions):
        predicted_team = str(predicted_order[i]).strip()
        real_team = str(real_order[i]).strip()

        if predicted_team == real_team:
            points += 1

    return points


def calc_champion_points(predicted_champion, real_champion):
    """
    حساب نقاط توقع البطل.

    النظام:
    - توقع البطل الصحيح = 10 نقاط
    - توقع خاطئ = 0
    """

    predicted_champion = str(predicted_champion).strip()
    real_champion = str(real_champion).strip()

    if predicted_champion and real_champion and predicted_champion == real_champion:
        return 10

    return 0


def calc_knockout_points(pred_winner, pred_method, real_winner, real_method):
    """
    حساب نقاط مباراة من الأدوار الإقصائية.

    القيم الممكنة للسيناريو:
    NORMAL = الوقت الأصلي
    ET = الأشواط الإضافية
    PEN = ركلات الترجيح

    النظام الجديد:

    إذا الفائز صح + السيناريو صح:
    - NORMAL = 3 نقاط
    - ET = 4 نقاط
    - PEN = 5 نقاط

    إذا الفائز صح + السيناريو غلط:
    - 2 نقاط

    إذا الفائز غلط + السيناريو صح:
    - NORMAL = 0 نقاط
    - ET = 1 نقطة
    - PEN = 2 نقاط

    إذا الفائز غلط + السيناريو غلط:
    - 0 نقاط
    """

    pred_winner = str(pred_winner).strip()
    real_winner = str(real_winner).strip()

    pred_method = str(pred_method).strip().upper()
    real_method = str(real_method).strip().upper()

    winner_correct = pred_winner == real_winner
    method_correct = pred_method == real_method

    # الفائز صح + السيناريو صح
    if winner_correct and method_correct:
        if real_method == "NORMAL":
            return 3
        if real_method == "ET":
            return 4
        if real_method == "PEN":
            return 5
        return 0

    # الفائز صح + السيناريو غلط
    if winner_correct and not method_correct:
        return 2

    # الفائز غلط + السيناريو صح
    if not winner_correct and method_correct:
        if real_method == "NORMAL":
            return 0
        if real_method == "ET":
            return 1
        if real_method == "PEN":
            return 2
        return 0

    # الفائز غلط + السيناريو غلط
    return 0


def calc_champion_points(predicted_champion, real_champion):
    """
    حساب نقاط توقع البطل.

    النظام:
    - توقع البطل الصحيح = 10 نقاط
    - توقع خاطئ = 0
    """

    predicted_champion = str(predicted_champion).strip()
    real_champion = str(real_champion).strip()

    if predicted_champion and real_champion and predicted_champion == real_champion:
        return 10

    return 0