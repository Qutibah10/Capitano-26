def calc_group_match_points(pred_winner, real_winner):
    """
    حساب نقاط مباراة من دور المجموعات.

    القيم:
    A = فوز الفريق الأول
    B = فوز الفريق الثاني
    DRAW = تعادل

    النظام:
    - فوز/خسارة صحيح = 3 نقاط
    - تعادل صحيح = 4 نقاط
    - خطأ = 0
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

    النظام الجديد:
    - نحسب أول 3 مراكز فقط.
    - كل مركز صحيح = 1 نقطة.
    - الحد الأقصى = 3 نقاط.
    - المركز الرابع لا يعطي نقاط.
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

    القيم:
    NORMAL = الوقت الأصلي
    ET = الأشواط الإضافية
    PEN = ركلات الترجيح

    النظام:

    الفائز صح + السيناريو صح:
    - NORMAL = 3 نقاط
    - ET = 4 نقاط
    - PEN = 5 نقاط

    الفائز صح + السيناريو غلط:
    - 2 نقاط

    الفائز غلط + السيناريو صح:
    - NORMAL = 0 نقاط
    - ET = 1 نقطة
    - PEN = 2 نقاط

    الفائز غلط + السيناريو غلط:
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
    if winner_correct:
        return 2

    # الفائز غلط + السيناريو صح
    if method_correct:
        if real_method == "ET":
            return 1
        if real_method == "PEN":
            return 2
        if real_method == "NORMAL":
            return 0
        return 0

    # الفائز غلط + السيناريو غلط
    return 0