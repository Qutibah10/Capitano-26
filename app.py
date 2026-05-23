import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import traceback
import os
import base64
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import re
from streamlit_autorefresh import st_autorefresh
import extra_streamlit_components as stx


from engine import (
    calc_group_match_points,
    calc_group_ranking_points,
    calc_knockout_points,
    calc_champion_points
)

from api_sync import (
    get_normalized_worldcup_matches,
    normalize_group_standings
)

load_dotenv()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

COOKIE_NAME = "capitano26_login"
SESSION_SECRET = os.getenv("SESSION_SECRET", "capitano26-local-secret")

# =========================================================
# 1. Page Configuration
# =========================================================
st.set_page_config(
    page_title="Capitano 26",
    page_icon="🏆",
    layout="wide"
)

# =========================================================
# 2. Session State
# =========================================================
if "lang" not in st.session_state:
    st.session_state.lang = "EN"

if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False


if "username" not in st.session_state:
    st.session_state.username = ""
if "password_reset_success" not in st.session_state:
    st.session_state.password_reset_success = False
    
cookie_manager = stx.CookieManager()    



# =========================================================
# 3. Translation
# =========================================================
t = {
    "EN": {
        "dir": "ltr",
        "username_hint": "Username can be Arabic or English, 3-20 characters.",
        "create_err_username_len": "Username must be between 3 and 20 characters.",
        "create_err_username_chars": "Username can only contain Arabic/English letters, numbers, spaces, and underscore.",
        "auth_login": "Login",
        "auth_create": "Create Account",
        "create_header": "Create New Player Account",
        "confirm_pass_label": "Confirm Password",
        "create_btn": "Create Account",
        "create_success": "Account created successfully. You can now login.",
        "create_err_empty": "Username and password cannot be empty.",
        "create_err_short": "Password must be at least 4 characters.",
        "create_err_match": "Passwords do not match.",
        "create_err_exists": "This username already exists.",
        "title": "CAPITANO 26",
        "subtitle": "PREDICT. COMPETE. CHALLENGE.",
        "tab_score": "📊 Scoreboard",
        "tab_pred": "⚽ Live Predictions",
        "tab_reveal": "👀 Prediction Reveal",
        "tab_champion": "🏆 Champion Pick",
        "tab_group_rank": "📋 Group Ranking",
        "tab_chat": "💬 Banter Room",
        "tab_settings": "⚙️ Settings",
        "tab_admin": "🔐 Admin Dashboard",
        "leaderboard": "Global Leaderboard",
        "rank": "Rank",
        "user": "Contender",
        "pts": "Points",
        "no_data": "No active records found in the database.",
        "pred_title": "Match Prediction Radar",
        "chat_title": "Locker Room Banter",
        "chat_place": "Broadcast a competitive message to the grid...",
        "admin_sect": "Administrative Terminal",
        "admin_pass": "Access Token",
        "login_header": "🔒 Secure Gate Access",
        "user_label": "Username",
        "pass_label": "Password",
        "login_btn": "Sign In",
        "logout_btn": "Sign Out",
        "login_err": "Invalid Username or Password. Please try again.",
        "welcome": "Welcome back, Captain",
        "save": "Save Prediction",
        "locked": "Prediction locked",
        "scheduled": "Scheduled",
        "live": "Live",
        "finished": "Finished",
        "winner": "Winner",
        "method": "Winning Method",
        "normal": "Normal Time",
        "et": "Extra Time",
        "pen": "Penalties",
        "draw": "Draw",
        "recalc": "Recalculate Scores",
        "recalc_done": "Scores recalculated successfully.",
        "api_sync": "🔄 Sync Matches From API",
        "api_done": "Matches synced and scores recalculated.",
        "champion_title": "Tournament Champion Prediction",
        "champion_select": "Choose your World Cup champion",
        "champion_saved": "Champion prediction saved.",
        "champion_locked": "Champion prediction is locked because the tournament has started.",
        "current_champion": "Your current champion pick",
        "group_rank_title": "Group Ranking Predictions",
        "group_select": "Select group",
        "group_rank_saved": "Group ranking prediction saved.",
        "group_rank_locked": "Group ranking prediction is locked.",
        "position": "Position",
        "1st": "🥇 1st Place",
        "2nd": "🥈 2nd Place",
        "3rd": "🥉 3rd Place",
        "th": "th",
        
        "how_title": "📘 How to Play",
        "rules_title": "🏆 Scoring System",

        "how_intro": "Each player makes predictions in four sections:",
        "how_a": "Group-stage match predictions",
        "how_b": "Group ranking predictions",
        "how_c": "Tournament champion pick",
        "how_d": "Knockout-stage match predictions",
        "how_lock_1": "Match predictions lock automatically at kickoff based on Jordan time.",
        "how_lock_2": "Champion pick locks when the first match of the tournament starts.",
        "how_lock_3": "Each group ranking locks when the first match in that group starts.",
        "how_reveal": "After a match starts, all players' predictions become visible in Prediction Reveal.",
        "how_update": "Results and points are updated after syncing official results.",

        "rules_group_title": "Group Stage Matches",
        "rules_group_1": "In group-stage matches, players predict only the match result:",
        "rules_group_2": "Team A wins / Draw / Team B wins",
        "rules_group_3": "Correct win/loss prediction = 3 points",
        "rules_group_4": "Correct draw prediction = 4 points",
        "rules_group_5": "Wrong prediction = 0 points",

        "rules_rank_title": "Group Ranking",
        "rules_rank_1": "Each player ranks the teams in every group from 1st to 4th.",
        "rules_rank_2": "Ranking points are added only after the entire group stage is finished.",
        "rules_rank_3": "Only the top 3 positions are counted. 4th place gives no points.",
        "rules_rank_4": "Each correct position in the top 3 = 1 point",
        "rules_rank_5": "Maximum group ranking points per group = 3 points",
        "rules_rank_6": "0 correct positions = 0 points",
        
        "rules_champ_title": "Champion Pick",
        "rules_champ_1": "Correct champion pick = 10 points",
        "rules_champ_2": "Wrong champion pick = 0 points",
        
        "rules_ko_title": "Knockout Stage",
        "rules_ko_1": "For each knockout match, players choose the winner and the winning method:",
        "rules_ko_2": "Normal Time / Extra Time / Penalties",
        "rules_ko_3": "Correct winner + wrong method = 2 points",
        "rules_ko_4": "Correct winner + correct method:",
        "rules_ko_5": "Normal Time = 3 points",
        "rules_ko_6": "Extra Time = 4 points",
        "rules_ko_7": "Penalties = 5 points",
        "rules_ko_8": "Wrong winner but correct method:",
        "rules_ko_9": "Extra Time = 1 point",
        "rules_ko_10": "Penalties = 2 points",
        "rules_ko_11": "Normal Time = 0 points",
        "rules_ko_12": "Wrong winner and wrong method = 0 points"
    },
    "AR": {
        "dir": "rtl",
        "username_hint": "يمكن أن يكون الاسم عربيًا أو إنجليزيًا، من 3 إلى 20 حرفًا.",
        "create_err_username_len": "اسم المستخدم يجب أن يكون بين 3 و20 حرفًا.",
        "create_err_username_chars": "اسم المستخدم يمكن أن يحتوي فقط على حروف عربية أو إنجليزية، أرقام، مسافات، أو underscore.",
        "auth_login": "تسجيل الدخول",
        "auth_create": "إنشاء حساب",
        "create_header": "إنشاء حساب لاعب جديد",
        "confirm_pass_label": "تأكيد كلمة المرور",
        "create_btn": "إنشاء الحساب",
        "create_success": "تم إنشاء الحساب بنجاح. يمكنك الآن تسجيل الدخول.",
        "create_err_empty": "اسم المستخدم وكلمة المرور لا يمكن أن تكون فارغة.",
        "create_err_short": "كلمة المرور يجب أن تكون 4 أحرف على الأقل.",
        "create_err_match": "كلمتا المرور غير متطابقتين.",
        "create_err_exists": "اسم المستخدم موجود مسبقًا.",
        "title": "كابيتانو 26",
        "subtitle": "توقّع. نافس. وتحدّى",
        "tab_score": "📊 لوحة الصدارة",
        "tab_pred": "⚽ التوقعات الحية",
        "tab_reveal": "👀 كشف التوقعات",
        "tab_champion": "🏆 توقع البطل",
        "tab_group_rank": "📋 ترتيب المجموعات",
        "tab_chat": "💬 صالة التحدي",
        "tab_settings": "⚙️ الإعدادات",
        "tab_admin": "🔐 لوحة الأدمن",
        "leaderboard": "جدول الترتيب العالمي",
        "rank": "الترتيب",
        "user": "المتحدّي",
        "pts": "النقاط",
        "no_data": "لم يتم العثور على أي بيانات مسجلة في قاعدة البيانات.",
        "pred_title": "رادار التوقعات المباشرة",
        "chat_title": "غرفة طوش وتحديات الشباب",
        "chat_place": "أرسل تحدي قوي واصدم فيه الجميع...",
        "admin_sect": "بوابة التحكم والمشرف العام",
        "admin_pass": "رمز الدخول السري",
        "login_header": "🔒 بوابة تسجيل الدخول الآمنة",
        "user_label": "اسم المستخدم",
        "pass_label": "كلمة المرور",
        "login_btn": "تسجيل الدخول",
        "logout_btn": "تسجيل الخروج",
        "login_err": "اسم المستخدم أو كلمة المرور غير صحيحة. حاول مجدداً.",
        "welcome": "أهلاً بك مجدداً، الكابتن",
        "save": "حفظ التوقع",
        "locked": "تم إغلاق التوقع",
        "scheduled": "قادمة",
        "live": "مباشرة",
        "finished": "منتهية",
        "winner": "الفائز",
        "method": "طريقة الفوز",
        "normal": "الوقت الأصلي",
        "et": "الأشواط الإضافية",
        "pen": "ركلات الترجيح",
        "draw": "تعادل",
        "recalc": "إعادة حساب النقاط",
        "recalc_done": "تمت إعادة حساب النقاط بنجاح.",
        "api_sync": "🔄 مزامنة المباريات من API",
        "api_done": "تمت مزامنة المباريات وإعادة حساب النقاط.",
        "champion_title": "توقع بطل البطولة",
        "champion_select": "اختر بطل كأس العالم",
        "champion_saved": "تم حفظ توقع البطل.",
        "champion_locked": "تم إغلاق توقع البطل لأن البطولة بدأت.",
        "current_champion": "توقعك الحالي للبطل",
        "group_rank_title": "توقع ترتيب المجموعات",
        "group_select": "اختر المجموعة",
        "group_rank_saved": "تم حفظ توقع ترتيب المجموعة.",
        "group_rank_locked": "تم إغلاق توقع ترتيب المجموعة.",
        "position": "المركز",
        "1st": "🥇 المركز الأول",
        "2nd": "🥈 المركز الثاني",
        "3rd": "🥉 المركز الثالث",
        "th": "المركز",
        
        "how_title": "📘 طريقة اللعب",
        "rules_title": "🏆 نظام النقاط",

        "how_intro": "كل لاعب يقوم بالتوقع في أربعة أقسام:",
        "how_a": "توقع مباريات دور المجموعات",
        "how_b": "توقع ترتيب المجموعات",
        "how_c": "توقع بطل البطولة",
        "how_d": "توقع مباريات الأدوار الإقصائية",
        "how_lock_1": "تغلق توقعات المباريات تلقائيًا عند بداية المباراة حسب توقيت الأردن.",
        "how_lock_2": "يغلق توقع البطل عند بداية أول مباراة في البطولة.",
        "how_lock_3": "يغلق توقع ترتيب كل مجموعة عند بداية أول مباراة في نفس المجموعة.",
        "how_reveal": "بعد بداية المباراة، تظهر توقعات جميع اللاعبين في صفحة كشف التوقعات.",
        "how_update": "يتم تحديث النتائج والنقاط بعد مزامنة النتائج الرسمية.",

        "rules_group_title": "مباريات دور المجموعات",
        "rules_group_1": "في مباريات دور المجموعات، اللاعب يتوقع نتيجة المباراة فقط:",
        "rules_group_2": "فوز الفريق الأول / تعادل / فوز الفريق الثاني",
        "rules_group_3": "توقع فوز/خسارة صحيح = 3 نقاط",
        "rules_group_4": "توقع تعادل صحيح = 4 نقاط",
        "rules_group_5": "توقع خاطئ = 0 نقاط",

        "rules_rank_title": "ترتيب المجموعات",
        "rules_rank_1": "كل لاعب يرتب منتخبات كل مجموعة من المركز الأول إلى الرابع.",
        "rules_rank_2": "نقاط الترتيب تُضاف فقط بعد نهاية دور المجموعات بالكامل.",
        "rules_rank_3": "يتم احتساب أول 3 مراكز فقط، والمركز الرابع لا يعطي نقاط.",
        "rules_rank_4": "كل مركز صحيح من أول 3 مراكز = 1 نقطة",
        "rules_rank_5": "الحد الأقصى لنقاط ترتيب كل مجموعة = 3 نقاط",
        "rules_rank_6": "0 مراكز صحيحة = 0 نقاط",
        
        "rules_champ_title": "توقع البطل",
        "rules_champ_1": "توقع البطل الصحيح = 10 نقاط",
        "rules_champ_2": "توقع خاطئ = 0 نقاط",
        
        "rules_ko_title": "الأدوار الإقصائية",
        "rules_ko_1": "في كل مباراة إقصائية، يختار اللاعب الفائز وطريقة الفوز:",
        "rules_ko_2": "الوقت الأصلي / الأشواط الإضافية / ركلات الترجيح",
        "rules_ko_3": "الفائز صحيح + السيناريو خاطئ = 2 نقاط",
        "rules_ko_4": "الفائز صحيح + السيناريو صحيح:",
        "rules_ko_5": "الوقت الأصلي = 3 نقاط",
        "rules_ko_6": "الأشواط الإضافية = 4 نقاط",
        "rules_ko_7": "ركلات الترجيح = 5 نقاط",
        "rules_ko_8": "الفائز خاطئ لكن السيناريو صحيح:",
        "rules_ko_9": "الأشواط الإضافية = 1 نقطة",
        "rules_ko_10": "ركلات الترجيح = 2 نقاط",
        "rules_ko_11": "الوقت الأصلي = 0 نقاط",
        "rules_ko_12": "الفائز خاطئ والسيناريو خاطئ = 0 نقاط"
    }
}

current_lang = st.session_state.lang
lang_data = t[current_lang]

# =========================================================
# 4. Styling
# =========================================================



st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@500;700;900&family=Space+Grotesk:wght@500;700&display=swap');

:root {{
    --bg-main: #060913;
    --cyan: #00F0FF;
    --green: #00FF75;
    --red: #FF0055;
    --text-main: #F8FAFC;
    --text-muted: #94A3B8;
    --glass: rgba(255, 255, 255, 0.055);
    --glass-border: rgba(255, 255, 255, 0.12);
}}

html, body, [data-testid="stAppViewContainer"], .main {{
    font-family: 'Space Grotesk', 'Cairo', sans-serif !important;
    background:
        radial-gradient(circle at 20% 10%, rgba(0, 240, 255, 0.13), transparent 28%),
        radial-gradient(circle at 80% 18%, rgba(0, 255, 117, 0.12), transparent 25%),
        radial-gradient(circle at 50% 90%, rgba(255, 0, 85, 0.10), transparent 30%),
        linear-gradient(180deg, #060913 0%, #03050C 100%) !important;
    color: var(--text-main) !important;
    direction: {lang_data['dir']} !important;
}}

.clean-logo {{
    display: block;
    margin: 0 auto;
    width: 150px;
    height: 150px;
    object-fit: cover;
    object-position: top center;
    border-radius: 28px;
    padding: 7px;
    background: linear-gradient(135deg, rgba(0,240,255,0.10), rgba(0,255,117,0.06));
    border: 1px solid rgba(255,255,255,0.14);
    filter:
        drop-shadow(0 0 16px rgba(0, 240, 255, 0.28))
        drop-shadow(0 0 20px rgba(0, 255, 117, 0.14));
}}

@media (max-width: 768px) {{
    .clean-logo {{
        width: 92px;
        height: 92px;
        border-radius: 24px;
        padding: 6px;
    }}

    .capitano-title {{
        font-size: 32px;
        letter-spacing: 2px;
    }}

    .capitano-subtitle {{
        font-size: 12px;
        letter-spacing: 2px;
    }}
}}    
    
.capitano-header {{
    text-align: center;
    margin-bottom: 24px;
    padding-top: 6px;
}}

.capitano-title {{
    font-size: 36px;
    font-weight: 900;
    letter-spacing: 3px;
    margin: 14px 0 0 0;
    color: #ffffff;
    text-shadow:
        0 0 18px rgba(0, 240, 255, 0.35),
        0 0 28px rgba(0, 255, 117, 0.18);
}}

.capitano-subtitle {{
    color: var(--cyan);
    font-size: 14px;
    font-weight: 900;
    letter-spacing: 4px;
    margin: 6px 0 0 0;
    text-transform: uppercase;
    text-shadow: 0 0 14px rgba(0, 240, 255, 0.45);
}}

.stTabs [data-baseweb="tab"] {{
    font-size: 15px !important;
    font-weight: 800 !important;
    color: #94a3b8 !important;
}}

.stTabs [aria-selected="true"] {{
    color: var(--cyan) !important;
    border-bottom: 3px solid var(--cyan) !important;
}}

div[data-testid="stDataFrame"] {{
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
    background: rgba(255,255,255,0.04) !important;
}}

button[kind="primary"], .stButton > button {{
    border-radius: 14px !important;
    font-weight: 900 !important;
    border: 1px solid rgba(0, 240, 255, 0.25) !important;
    box-shadow: 0 0 18px rgba(0, 240, 255, 0.10);
}}

.match-card {{
    background: linear-gradient(135deg, rgba(255,255,255,0.075), rgba(255,255,255,0.028));
    border: 1px solid rgba(255,255,255,0.13);
    padding: 18px;
    border-radius: 20px;
    margin-bottom: 14px;
    box-shadow:
        0 12px 35px rgba(0,0,0,0.30),
        inset 0 0 20px rgba(255,255,255,0.025);
    backdrop-filter: blur(14px);
}}

.match-title {{
    font-size: 23px;
    font-weight: 900;
    color: #ffffff;
    margin-bottom: 8px;
}}

.match-meta {{
    color: var(--text-muted);
    font-size: 13px;
    margin-top: 4px;
}}

.capitano-footer {{
    margin-top: 45px;
    padding: 22px 16px;
    text-align: center;
    border-top: 1px solid rgba(255,255,255,0.10);
    color: #94A3B8;
    font-size: 13px;
}}

.capitano-footer-title {{
    color: #ffffff;
    font-weight: 900;
    letter-spacing: 2px;
    margin-bottom: 5px;
    text-shadow: 0 0 12px rgba(0,240,255,0.25);
}}

.capitano-footer-slogan {{
    color: #00F0FF;
    font-weight: 800;
    margin-bottom: 7px;
}}

.capitano-footer-note {{
    opacity: 0.8;
}}

.prediction-box {{
    margin-top: 12px;
    padding: 10px 12px;
    border-radius: 14px;
    background: rgba(0,240,255,0.07);
    border: 1px solid rgba(0,240,255,0.18);
    color: #e2e8f0;
    font-size: 14px;
}}

.status-pill {{
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(0, 255, 117, 0.10);
    border: 1px solid rgba(0, 255, 117, 0.25);
    color: #b9ffd7;
    font-weight: 800;
    font-size: 12px;
}}
.auth-card {{
    background: linear-gradient(135deg, rgba(255,255,255,0.075), rgba(255,255,255,0.025));
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 24px;
    padding: 24px;
    box-shadow:
        0 14px 45px rgba(0,0,0,0.35),
        inset 0 0 25px rgba(255,255,255,0.025);
    backdrop-filter: blur(16px);
    margin-bottom: 18px;
}}

.auth-title {{
    text-align: center;
    font-size: 24px;
    font-weight: 900;
    color: #ffffff;
    margin-bottom: 6px;
    text-shadow: 0 0 16px rgba(0,240,255,0.30);
}}

.auth-slogan {{
    text-align: center;
    color: #00F0FF;
    font-size: 14px;
    font-weight: 900;
    letter-spacing: 1.5px;
    margin-bottom: 12px;
}}

.auth-desc {{
    text-align: center;
    color: #94A3B8;
    font-size: 14px;
    line-height: 1.8;
    margin-bottom: 6px;
}}

.recovery-warning {{
    background: rgba(255, 0, 85, 0.08);
    border: 1px solid rgba(255, 0, 85, 0.22);
    color: #ffd6df;
    padding: 10px 12px;
    border-radius: 14px;
    font-size: 13px;
    line-height: 1.7;
    margin: 8px 0 14px 0;
}}

div[data-testid="InputInstructions"] {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
</style>
""", unsafe_allow_html=True)


# =========================================================
# 5. Database Helpers
# =========================================================
@st.cache_resource
def connect_db():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    spreadsheet_name = "WorldCup_DB"

    try:
        # نحاول نقرأ أسرار Streamlit فقط إذا كانت موجودة
        secrets = st.secrets

        if "SPREADSHEET_NAME" in secrets:
            spreadsheet_name = secrets["SPREADSHEET_NAME"]

        if "gcp_service_account" in secrets:
            creds_dict = dict(secrets["gcp_service_account"])

            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                creds_dict,
                scope
            )
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                "creds.json",
                scope
            )

    except Exception:
        # التشغيل المحلي العادي باستخدام creds.json
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "creds.json",
            scope
        )

    client = gspread.authorize(creds)

    return client.open(spreadsheet_name)


@st.cache_data(ttl=180)
def load_sheet(sheet_name):
    db = connect_db()
    sheet = db.worksheet(sheet_name)

    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    df.columns = [str(col).strip() for col in df.columns]

    required_columns = {
        "Users": ["Username", "Password", "Points", "Avatar", "RecoveryCode"],
        "Predictions": ["Username", "MatchID", "Stage", "PredWinner", "PredMethod", "Points", "Locked", "LastUpdated"],
        "MatchCache": ["MatchID", "Stage", "Group", "TeamA", "TeamB", "Kickoff", "Status", "RealWinner", "RealMethod", "LastSynced"],
        "SystemSettings": ["Key", "Value"],
        "ChampionPredictions": ["Username", "Champion", "Points", "Locked", "LastUpdated"],
        "GroupRankingPredictions": ["Username", "Group", "Pos1", "Pos2", "Pos3", "Pos4", "Points", "Locked", "LastUpdated"],
        "GroupStandings": ["Group", "Position", "Team"]
    }

    if sheet_name in required_columns:
        for col in required_columns[sheet_name]:
            if col not in df.columns:
                df[col] = ""
        df = df[required_columns[sheet_name]]

    return df


def get_worksheet(sheet_name):
    db = connect_db()
    return db.worksheet(sheet_name)


def clear_all_cache():
    st.cache_data.clear()
    
def hash_password(password):
    """
    يحول كلمة السر إلى Hash.
    هذا أفضل من تخزين كلمة السر كنص واضح داخل Google Sheets.
    """
    return hashlib.sha256(str(password).encode("utf-8")).hexdigest()


def verify_password(input_password, stored_password):
    """
    يقارن كلمة السر المدخلة مع المخزنة.
    يدعم النظام القديم:
    - لو كلمة السر القديمة مخزنة نص عادي
    ويدعم النظام الجديد:
    - لو كلمة السر مخزنة Hash
    """
    input_password = str(input_password)
    stored_password = str(stored_password)

    if stored_password == input_password:
        return True

    if stored_password == hash_password(input_password):
        return True

    return False


def clean_username(username):
    username = str(username).strip()
    username = re.sub(r"\s+", " ", username)
    return username

COOKIE_NAME = "capitano26_login"


def get_session_secret():
    try:
        if "SESSION_SECRET" in st.secrets:
            return str(st.secrets["SESSION_SECRET"])
    except Exception:
        pass

    return os.getenv("SESSION_SECRET", "capitano26-local-secret")


def make_login_cookie(username, stored_password_hash):
    safe_username = clean_username(username).lower()
    stored_password_hash = str(stored_password_hash)

    raw = f"{safe_username}|{stored_password_hash}|{get_session_secret()}"

    signature = hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()

    return f"{safe_username}:{signature}"


def validate_login_cookie(df_users, token):
    try:
        if not token:
            return None

        token = str(token)

        if ":" not in token:
            return None

        safe_username, signature = token.split(":", 1)

        user_rows = df_users[
            df_users["Username"].astype(str).apply(
                lambda x: clean_username(x).lower()
            ) == safe_username
        ]

        if user_rows.empty:
            return None

        real_username = str(user_rows.iloc[0]["Username"])
        stored_password_hash = str(user_rows.iloc[0]["Password"])

        expected_token = make_login_cookie(
            real_username,
            stored_password_hash
        )

        if token == expected_token:
            return real_username

        return None

    except Exception:
        return None


def is_valid_username(username):
    username = clean_username(username)

    if len(username) < 3 or len(username) > 20:
        return False, "length"

    # يسمح بالعربي، الإنجليزي، الأرقام، المسافة، والـ underscore
    pattern = r"^[\u0600-\u06FFa-zA-Z0-9_ ]+$"

    if not re.match(pattern, username):
        return False, "chars"

    return True, ""


def is_admin_user(username):
    username_clean = clean_username(username).lower()

    admin_users = [
        
        "Qutibah"
    ]

    admin_users = [clean_username(u).lower() for u in admin_users]

    return username_clean in admin_users


def username_exists(df_users, username):
    username = clean_username(username).lower()

    if df_users.empty:
        return False

    return not df_users[
        df_users["Username"].astype(str).apply(lambda x: clean_username(x).lower())
        == username
    ].empty


def create_new_user(username, password, recovery_code, language="AR"):
    username = clean_username(username)
    password = str(password)
    recovery_code = str(recovery_code).strip()

    ws = get_worksheet("Users")

    headers = ws.row_values(1)
    headers_clean = [str(h).strip() for h in headers]

    # تأكد من وجود الأعمدة المطلوبة
    needed_headers = ["Username", "Password", "Points", "Avatar", "RecoveryCode", "Language"]

    for h in needed_headers:
        if h not in headers_clean:
            new_col = len(headers_clean) + 1
            ws.update_cell(1, new_col, h)
            headers_clean.append(h)

    values = {
        "Username": username,
        "Password": hash_password(password),
        "Points": 0,
        "Avatar": "capitano",
        "Language": language if language in ["EN", "AR"] else "AR",
        "RecoveryCode": hash_password(recovery_code)
    }

    new_row = []

    for h in headers_clean:
        new_row.append(values.get(h, ""))

    ws.append_row(new_row)

    clear_all_cache()   
    

def change_user_password(username, current_password, new_password):
    username = clean_username(username)
    current_password = str(current_password)
    new_password = str(new_password)

    df_users = load_sheet("Users")

    if df_users.empty:
        return False, "user_not_found"

    user_rows = df_users[
        df_users["Username"].astype(str).apply(lambda x: clean_username(x).lower())
        == username.lower()
    ]

    if user_rows.empty:
        return False, "user_not_found"

    user_index = user_rows.index[0]
    stored_password = str(user_rows.iloc[0]["Password"])

    if stored_password != hash_password(current_password):
        return False, "wrong_password"

    if len(new_password) < 4:
        return False, "short_password"

    ws = get_worksheet("Users")

    # +2 لأن الصف الأول Headers، والـ DataFrame يبدأ من 0
    sheet_row = int(user_index) + 2

    password_col = list(df_users.columns).index("Password") + 1

    ws.update_cell(sheet_row, password_col, hash_password(new_password))

    clear_all_cache()

    return True, "success"    


def reset_password_with_recovery_code(username, recovery_code, new_password):
    username = clean_username(username)
    recovery_code = str(recovery_code).strip()
    new_password = str(new_password)

    if len(new_password) < 4:
        return False, "short_password"

    ws = get_worksheet("Users")

    # قراءة الهيدرز مباشرة من الشيت
    headers = ws.row_values(1)
    headers_clean = [str(h).strip().lower() for h in headers]

    if "username" not in headers_clean:
        return False, "missing_username_column"

    if "password" not in headers_clean:
        return False, "missing_password_column"

    if "recoverycode" not in headers_clean:
        return False, "missing_recovery_column"

    username_col = headers_clean.index("username") + 1
    password_col = headers_clean.index("password") + 1
    recovery_col = headers_clean.index("recoverycode") + 1

    usernames = ws.col_values(username_col)
    recovery_codes = ws.col_values(recovery_col)

    target_row = None
    stored_recovery_code = ""

    for row_number, sheet_username in enumerate(usernames[1:], start=2):
        if clean_username(sheet_username).lower() == username.lower():
            target_row = row_number

            if row_number <= len(recovery_codes):
                stored_recovery_code = str(recovery_codes[row_number - 1]).strip()

            break

    if target_row is None:
        return False, "user_not_found"

    if not stored_recovery_code:
        return False, "no_recovery_code"

    if not verify_password(recovery_code, stored_recovery_code):
        return False, "wrong_recovery_code"

    # تحديث كلمة السر في عمود Password الصحيح
    ws.update_cell(target_row, password_col, hash_password(new_password))

    clear_all_cache()

    return True, "success"

def delete_user_account(username, password):
    username = clean_username(username)
    password = str(password)

    if not username or not password:
        return False, "missing_fields"

    # تحقق من كلمة السر
    df_users = load_sheet("Users")

    if df_users.empty or "Username" not in df_users.columns or "Password" not in df_users.columns:
        return False, "users_sheet_error"

    user_rows = df_users[
        df_users["Username"].astype(str).apply(lambda x: clean_username(x).lower())
        == username.lower()
    ]

    if user_rows.empty:
        return False, "user_not_found"

    stored_password = str(user_rows.iloc[0]["Password"])

    if not verify_password(password, stored_password):
        return False, "wrong_password"

    # حذف صف المستخدم من Users
    users_ws = get_worksheet("Users")
    headers = users_ws.row_values(1)
    headers_clean = [str(h).strip() for h in headers]

    username_col = headers_clean.index("Username") + 1
    usernames = users_ws.col_values(username_col)

    target_row = None
    for row_number, sheet_username in enumerate(usernames[1:], start=2):
        if clean_username(sheet_username).lower() == username.lower():
            target_row = row_number
            break

    if target_row:
        users_ws.delete_rows(target_row)

    # حذف بياناته من الشيتات الأخرى
    sheets_to_clean = [
        "Predictions",
        "GroupRankingPredictions",
        "ChampionPredictions",
        "BanterMessages"
    ]

    for sheet_name in sheets_to_clean:
        try:
            ws = get_worksheet(sheet_name)
            headers = ws.row_values(1)
            headers_clean = [str(h).strip() for h in headers]

            if "Username" not in headers_clean:
                continue

            username_col = headers_clean.index("Username") + 1
            values = ws.col_values(username_col)

            rows_to_delete = []

            for row_number, sheet_username in enumerate(values[1:], start=2):
                if clean_username(sheet_username).lower() == username.lower():
                    rows_to_delete.append(row_number)

            for row_number in reversed(rows_to_delete):
                ws.delete_rows(row_number)

        except Exception:
            pass

    clear_all_cache()

    return True, "success"

# =========================================================
# 6. Utility Functions
# =========================================================
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

def render_footer():
    if current_lang == "EN":
        title = "CAPITANO 26"
        slogan = "Predict. Compete. Challenge."
        developer = "Developed by Qutbah Amayreh"
        note = "© 2026 Capitano 26. Built for friends, rivalry, and football nights."
    else:
        title = "كابيتانو 26"
        slogan = "توقّع. نافس. وتحدّى"
        developer = "تطوير قتيبة عمايرة"
        note = "© 2026 كابيتانو 26. لعبة توقعات ودّية لعشاق كرة القدم."

    st.markdown(
        f"""
        <div class="capitano-footer">
            <div class="capitano-footer-title">{title}</div>
            <div class="capitano-footer-slogan">{slogan}</div>
            <div class="capitano-footer-note">{developer}</div>
            <div class="capitano-footer-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )



def get_team_flag_path(team_name):
    team_name = str(team_name).strip()

    flag_files = {
        "Mexico": "mexico.png",
        "South Africa": "south_africa.png",
        "South Korea": "south_korea.png",
        "Czechia": "czechia.png",
        "Canada": "canada.png",
        "Bosnia-Herzegovina": "bosnia_herzegovina.png",
        "United States": "united_states.png",
        "Paraguay": "paraguay.png",
        "Qatar": "qatar.png",
        "Switzerland": "switzerland.png",
        "Brazil": "brazil.png",
        "Morocco": "morocco.png",
        "Haiti": "haiti.png",
        "Scotland": "scotland.png",
        "Australia": "australia.png",
        "Turkey": "turkey.png",
        "Germany": "germany.png",
        "Curaçao": "curacao.png",
        "Netherlands": "netherlands.png",
        "Japan": "japan.png",
        "Ivory Coast": "ivory_coast.png",
        "Ecuador": "ecuador.png",
        "Sweden": "sweden.png",
        "Tunisia": "tunisia.png",
        "Spain": "spain.png",
        "Cape Verde Islands": "cape_verde.png",
        "Belgium": "belgium.png",
        "Egypt": "egypt.png",
        "Saudi Arabia": "saudi_arabia.png",
        "Uruguay": "uruguay.png",
        "Iran": "iran.png",
        "New Zealand": "new_zealand.png",
        "France": "france.png",
        "Senegal": "senegal.png",
        "Iraq": "iraq.png",
        "Norway": "norway.png",
        "Argentina": "argentina.png",
        "Algeria": "algeria.png",
        "Austria": "austria.png",
        "Jordan": "jordan.png",
        "Portugal": "portugal.png",
        "Congo DR": "congo_dr.png",
        "England": "england.png",
        "Croatia": "croatia.png",
        "Ghana": "ghana.png",
        "Panama": "panama.png",
        "Uzbekistan": "uzbekistan.png",
        "Colombia": "colombia.png",
    }

    filename = flag_files.get(team_name)

    if not filename:
        return None

    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "assets", "flags", filename)

    if os.path.exists(path):
        return path

    return None


TEAM_AR = {
    "Mexico": "المكسيك",
    "South Africa": "جنوب أفريقيا",
    "South Korea": "كوريا الجنوبية",
    "Czechia": "التشيك",
    "Canada": "كندا",
    "Bosnia-Herzegovina": "البوسنة والهرسك",
    "United States": "الولايات المتحدة",
    "Paraguay": "باراغواي",
    "Qatar": "قطر",
    "Switzerland": "سويسرا",
    "Brazil": "البرازيل",
    "Morocco": "المغرب",
    "Haiti": "هايتي",
    "Scotland": "اسكتلندا",
    "Australia": "أستراليا",
    "Turkey": "تركيا",
    "Germany": "ألمانيا",
    "Curaçao": "كوراساو",
    "Netherlands": "هولندا",
    "Japan": "اليابان",
    "Ivory Coast": "ساحل العاج",
    "Ecuador": "الإكوادور",
    "Sweden": "السويد",
    "Tunisia": "تونس",
    "Spain": "إسبانيا",
    "Cape Verde Islands": "الرأس الأخضر",
    "Belgium": "بلجيكا",
    "Egypt": "مصر",
    "Saudi Arabia": "السعودية",
    "Uruguay": "أوروغواي",
    "Iran": "إيران",
    "New Zealand": "نيوزيلندا",
    "France": "فرنسا",
    "Senegal": "السنغال",
    "Iraq": "العراق",
    "Norway": "النرويج",
    "Argentina": "الأرجنتين",
    "Algeria": "الجزائر",
    "Austria": "النمسا",
    "Jordan": "الأردن",
    "Portugal": "البرتغال",
    "Congo DR": "الكونغو الديمقراطية",
    "England": "إنجلترا",
    "Croatia": "كرواتيا",
    "Ghana": "غانا",
    "Panama": "بنما",
    "Uzbekistan": "أوزبكستان",
    "Colombia": "كولومبيا",
}


def team_name_display(team_name):
    team_name = str(team_name).strip()
    if current_lang == "AR":
        return TEAM_AR.get(team_name, team_name)
    return team_name



def status_display(status):
    status = str(status).strip().upper()

    status_map = {
        "SCHEDULED": {
            "EN": "Scheduled",
            "AR": "قادمة"
        },
        "LIVE": {
            "EN": "Live",
            "AR": "مباشرة"
        },
        "IN_PLAY": {
            "EN": "Live",
            "AR": "مباشرة"
        },
        "FINISHED": {
            "EN": "Finished",
            "AR": "منتهية"
        },
        "COMPLETED": {
            "EN": "Finished",
            "AR": "منتهية"
        },
        "POSTPONED": {
            "EN": "Postponed",
            "AR": "مؤجلة"
        }
    }

    return status_map.get(status, {}).get(current_lang, status)


def stage_display(stage):
    return tr_stage(stage)
    stage = str(stage).strip().upper()

    stage_map = {
        "GROUP": {
            "EN": "Group Stage",
            "AR": "دور المجموعات"
        },
        "ROUND_OF_32": {
            "EN": "Round of 32",
            "AR": "دور الـ32"
        },
        "ROUND_OF_16": {
            "EN": "Round of 16",
            "AR": "دور الـ16"
        },
        "QUARTER_FINAL": {
            "EN": "Quarter-final",
            "AR": "ربع النهائي"
        },
        "SEMI_FINAL": {
            "EN": "Semi-final",
            "AR": "نصف النهائي"
        },
        "THIRD_PLACE": {
            "EN": "Third-place match",
            "AR": "مباراة المركز الثالث"
        },
        "FINAL": {
            "EN": "Final",
            "AR": "النهائي"
        }
    }

    return stage_map.get(stage, {}).get(current_lang, stage)


def group_display(group_value):
    group_value = str(group_value).strip()

    if not group_value:
        return ""

    if current_lang == "AR":
        return f"المجموعة {group_value}"

    return f"Group {group_value}"


def kickoff_display(kickoff):
    kickoff = str(kickoff).strip()

    if current_lang == "AR":
        return f"وقت المباراة: {kickoff} - بتوقيت الأردن"

    return f"Kickoff: {kickoff} - Jordan Time"


AVATARS = {
    "capitano": {
        "file": "capitano.png",
        "label_en": "Capitano",
        "label_ar": "الكابيتانو"
    },
    "wall": {
        "file": "wall.png",
        "label_en": "The Wall",
        "label_ar": "الجدار"
    },
    "tactician": {
        "file": "tactician.png",
        "label_en": "Tactician",
        "label_ar": "التكتيكي"
    },
    "sniper": {
        "file": "sniper.png",
        "label_en": "Sniper",
        "label_ar": "القناص"
    },
    "eagle": {
        "file": "eagle.png",
        "label_en": "Eagle",
        "label_ar": "الصقر"
    },
    "crown_hunter": {
        "file": "crown_hunter.png",
        "label_en": "Crown Hunter",
        "label_ar": "صياد التاج"
    },
    "clutch": {
        "file": "clutch.png",
        "label_en": "Clutch",
        "label_ar": "الحاسم"
    },
}

def get_avatar_path(avatar_key):
    avatar_key = str(avatar_key).strip()

    if avatar_key not in AVATARS:
        avatar_key = "capitano"

    filename = AVATARS[avatar_key]["file"]
    path = os.path.join("assets", "avatars", filename)

    if os.path.exists(path):
        return path

    return None

def avatar_html(avatar_path, size=82):
    if not avatar_path or not os.path.exists(avatar_path):
        return ""

    with open(avatar_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode()

    return f"""
    <div style="
        width:{size}px;
        height:{size}px;
        border-radius:50%;
        padding:5px;
        background:radial-gradient(circle, rgba(0,240,255,0.20), rgba(255,255,255,0.04));
        border:1px solid rgba(0,240,255,0.32);
        box-shadow:0 0 24px rgba(0,240,255,0.20);
        display:flex;
        align-items:center;
        justify-content:center;
        overflow:hidden;
        margin:auto;
    ">
        <img src="data:image/png;base64,{img_base64}"
             style="
                width:100%;
                height:100%;
                object-fit:cover;
                border-radius:50%;
                image-rendering:auto;
             ">
    </div>
    """

def get_avatar_for_username(username):
    username = clean_username(username).lower()

    avatar_map = get_users_avatar_map()

    avatar_key = avatar_map.get(username, "capitano")

    return get_avatar_path(avatar_key)

def get_user_avatar(username):
    username = clean_username(username)

    ws = get_worksheet("Users")

    headers = ws.row_values(1)
    headers_clean = [str(h).strip().lower() for h in headers]

    if "username" not in headers_clean:
        return "capitano"

    if "avatar" not in headers_clean:
        return "capitano"

    username_col = headers_clean.index("username") + 1
    avatar_col = headers_clean.index("avatar") + 1

    usernames = ws.col_values(username_col)
    avatars = ws.col_values(avatar_col)

    for row_number, sheet_username in enumerate(usernames[1:], start=2):
        if clean_username(sheet_username).lower() == username.lower():
            if row_number <= len(avatars):
                avatar_key = str(avatars[row_number - 1]).strip()

                if avatar_key in AVATARS:
                    return avatar_key

            return "capitano"

    return "capitano"

@st.cache_data(ttl=60)
def get_users_avatar_map():
    df_users = load_sheet("Users")

    avatar_map = {}

    if df_users.empty:
        return avatar_map

    df_users.columns = [str(col).strip() for col in df_users.columns]

    if "Username" not in df_users.columns:
        return avatar_map

    if "Avatar" not in df_users.columns:
        return avatar_map

    for _, row in df_users.iterrows():
        username = clean_username(row.get("Username", ""))
        avatar_key = str(row.get("Avatar", "")).strip()

        if avatar_key not in AVATARS:
            avatar_key = "capitano"

        if username:
            avatar_map[username.lower()] = avatar_key

    return avatar_map


def save_user_avatar(username, avatar_key):
    username = clean_username(username)
    avatar_key = str(avatar_key).strip()

    if avatar_key not in AVATARS:
        return False, "invalid_avatar"

    ws = get_worksheet("Users")

    headers = ws.row_values(1)
    headers_clean = [str(h).strip().lower() for h in headers]

    if "username" not in headers_clean:
        return False, "missing_username_column"

    username_col = headers_clean.index("username") + 1

    if "avatar" in headers_clean:
        avatar_col = headers_clean.index("avatar") + 1
    else:
        avatar_col = len(headers) + 1
        ws.update_cell(1, avatar_col, "Avatar")

    usernames = ws.col_values(username_col)

    target_row = None

    for row_number, sheet_username in enumerate(usernames[1:], start=2):
        if clean_username(sheet_username).lower() == username.lower():
            target_row = row_number
            break

    if target_row is None:
        return False, "user_not_found"

    ws.update_cell(target_row, avatar_col, avatar_key)

    clear_all_cache()
    get_users_avatar_map.clear()

    return True, "success"


def save_user_language(username, language):
    username = clean_username(username)
    language = str(language).strip().upper()

    if language not in ["EN", "AR"]:
        language = "AR"

    ws = get_worksheet("Users")

    headers = ws.row_values(1)
    headers_clean = [str(h).strip() for h in headers]

    if "Username" not in headers_clean:
        return False

    if "Language" not in headers_clean:
        new_col = len(headers_clean) + 1
        ws.update_cell(1, new_col, "Language")
        headers_clean.append("Language")

    username_col = headers_clean.index("Username") + 1
    language_col = headers_clean.index("Language") + 1

    usernames = ws.col_values(username_col)

    for row_number, sheet_username in enumerate(usernames[1:], start=2):
        if clean_username(sheet_username).lower() == username.lower():
            ws.update_cell(row_number, language_col, language)
            clear_all_cache()
            return True

    return False

def get_user_language(username):
    username = clean_username(username)

    df_users = load_sheet("Users")

    default_lang = st.session_state.get("lang", "AR")

    if df_users.empty:
        return default_lang

    df_users.columns = [str(c).strip() for c in df_users.columns]

    if "Username" not in df_users.columns:
        return default_lang

    if "Language" not in df_users.columns:
        return default_lang

    user_rows = df_users[
        df_users["Username"].astype(str).apply(lambda x: clean_username(x).lower())
        == username.lower()
    ]

    if user_rows.empty:
        return default_lang

    lang = str(user_rows.iloc[0].get("Language", default_lang)).strip().upper()

    if lang not in ["EN", "AR"]:
        return default_lang

    return lang

def get_team_display_with_flag(team_name):
    team_name = str(team_name).strip()
    flag_path = get_team_flag_path(team_name)

    if flag_path:
        flag_base64 = get_base64_image(flag_path)

        if flag_base64:
            return f"""
            <span style="display:inline-flex; align-items:center; gap:8px;">
                <span style="
                    width:30px;
                    height:22px;
                    display:inline-flex;
                    align-items:center;
                    justify-content:center;
                    background:rgba(255,255,255,0.08);
                    border:1px solid rgba(255,255,255,0.12);
                    border-radius:5px;
                    overflow:hidden;
                ">
                    <img src="data:image/png;base64,{flag_base64}"
                         style="width:26px; height:18px; object-fit:contain;">
                </span>
                <span>{tr_team(team_name)}</span>
            </span>
            """

    return f"<span>{tr_team(team_name)}</span>"


def format_reveal_prediction(row, selected_match):
    stage = str(selected_match.get("Stage", "")).upper()

    username = str(row.get("Username", "Unknown"))

    pred_winner = str(
        row.get("PredWinner",
        row.get("Prediction",
        row.get("Winner", "")))
    ).strip()

    pred_method = str(
        row.get("PredMethod",
        row.get("Method", ""))
    ).strip().upper()

    points = row.get("PointsEarned", row.get("Points", ""))

    if stage == "GROUP":
        if pred_winner == "DRAW":
            pred_text = "Draw" if current_lang == "EN" else "تعادل"
        elif pred_winner:
            pred_text = f"{pred_winner} wins" if current_lang == "EN" else f"فوز {pred_winner}"
        else:
            pred_text = "No prediction" if current_lang == "EN" else "لا يوجد توقع"
    else:
        method_labels = {
            "NORMAL": "Normal Time" if current_lang == "EN" else "الوقت الأصلي",
            "ET": "Extra Time" if current_lang == "EN" else "الأشواط الإضافية",
            "PEN": "Penalties" if current_lang == "EN" else "ركلات الترجيح",
        }

        method_text = method_labels.get(pred_method, pred_method)

        if pred_winner:
            pred_text = (
                f"{pred_winner} wins by {method_text}"
                if current_lang == "EN"
                else f"فوز {pred_winner} عبر {method_text}"
            )
        else:
            pred_text = "No prediction" if current_lang == "EN" else "لا يوجد توقع"

    if points == "" or pd.isna(points):
        points_text = "Pending" if current_lang == "EN" else "بانتظار النتيجة"
    else:
        points_text = str(points)

    return username, pred_text, points_text


def now_jordan():
    return datetime.now(ZoneInfo("Asia/Amman"))


def is_match_locked(kickoff_text, status):
    status = str(status).upper().strip()

    if status in ["LIVE", "FINISHED"]:
        return True

    try:
        kickoff = datetime.strptime(str(kickoff_text), "%Y-%m-%d %H:%M")
        kickoff = kickoff.replace(tzinfo=ZoneInfo("Asia/Amman"))
        return now_jordan() >= kickoff
    except Exception:
        return False


def is_match_ready(match):
    team_a = str(match["TeamA"]).strip().upper()
    team_b = str(match["TeamB"]).strip().upper()

    invalid_names = ["", "TBD", "NONE", "NAN", "NULL"]

    if team_a in invalid_names:
        return False

    if team_b in invalid_names:
        return False

    return True


TEAM_AR = {
    "Mexico": "المكسيك",
    "South Africa": "جنوب أفريقيا",
    "South Korea": "كوريا الجنوبية",
    "Czechia": "التشيك",
    "Canada": "كندا",
    "Bosnia-Herzegovina": "البوسنة والهرسك",
    "United States": "الولايات المتحدة",
    "Paraguay": "باراغواي",
    "Qatar": "قطر",
    "Switzerland": "سويسرا",
    "Brazil": "البرازيل",
    "Morocco": "المغرب",
    "Haiti": "هايتي",
    "Scotland": "اسكتلندا",
    "Australia": "أستراليا",
    "Turkey": "تركيا",
    "Germany": "ألمانيا",
    "Curaçao": "كوراساو",
    "Netherlands": "هولندا",
    "Japan": "اليابان",
    "Ivory Coast": "ساحل العاج",
    "Ecuador": "الإكوادور",
    "Sweden": "السويد",
    "Tunisia": "تونس",
    "Spain": "إسبانيا",
    "Cape Verde Islands": "الرأس الأخضر",
    "Belgium": "بلجيكا",
    "Egypt": "مصر",
    "Saudi Arabia": "السعودية",
    "Uruguay": "أوروغواي",
    "Iran": "إيران",
    "New Zealand": "نيوزيلندا",
    "France": "فرنسا",
    "Senegal": "السنغال",
    "Iraq": "العراق",
    "Norway": "النرويج",
    "Argentina": "الأرجنتين",
    "Algeria": "الجزائر",
    "Austria": "النمسا",
    "Jordan": "الأردن",
    "Portugal": "البرتغال",
    "Congo DR": "الكونغو الديمقراطية",
    "England": "إنجلترا",
    "Croatia": "كرواتيا",
    "Ghana": "غانا",
    "Panama": "بنما",
    "Uzbekistan": "أوزبكستان",
    "Colombia": "كولومبيا",
}


def tr_team(team_name):
    team_name = str(team_name).strip()

    if current_lang == "AR":
        return TEAM_AR.get(team_name, team_name)

    return team_name


def tr_stage(stage):
    original_stage = str(stage).strip()
    stage_key = original_stage.upper().strip()

    stage_names = {
        "GROUP": {
            "EN": "Group Stage",
            "AR": "دور المجموعات"
        },

        "R32": {
            "EN": "Round of 32",
            "AR": "دور الـ32"
        },
        "ROUND_OF_32": {
            "EN": "Round of 32",
            "AR": "دور الـ32"
        },
        "LAST_32": {
            "EN": "Round of 32",
            "AR": "دور الـ32"
        },

        "R16": {
            "EN": "Round of 16",
            "AR": "دور الـ16"
        },
        "ROUND_OF_16": {
            "EN": "Round of 16",
            "AR": "دور الـ16"
        },
        "LAST_16": {
            "EN": "Round of 16",
            "AR": "دور الـ16"
        },

        "QF": {
            "EN": "Quarter-final",
            "AR": "ربع النهائي"
        },
        "QUARTER_FINAL": {
            "EN": "Quarter-final",
            "AR": "ربع النهائي"
        },
        "QUARTER_FINALS": {
            "EN": "Quarter-final",
            "AR": "ربع النهائي"
        },

        "SF": {
            "EN": "Semi-final",
            "AR": "نصف النهائي"
        },
        "SEMI_FINAL": {
            "EN": "Semi-final",
            "AR": "نصف النهائي"
        },
        "SEMI_FINALS": {
            "EN": "Semi-final",
            "AR": "نصف النهائي"
        },

        "THIRD": {
            "EN": "Third-place match",
            "AR": "مباراة المركز الثالث"
        },
        "THIRD_PLACE": {
            "EN": "Third-place match",
            "AR": "مباراة المركز الثالث"
        },

        "FINAL": {
            "EN": "Final",
            "AR": "النهائي"
        },
    }

    return stage_names.get(stage_key, {}).get(current_lang, original_stage)


def tr_group(group_name):
    group_name = str(group_name).strip()

    if group_name.upper() in ["", "NONE", "NAN", "NULL"]:
        return "-"

    if current_lang == "EN":
        return f"Group {group_name}"

    return f"المجموعة {group_name}"


def tr_vs():
    return "vs" if current_lang == "EN" else "ضد"


def tr_kickoff_label():
    return "Kickoff" if current_lang == "EN" else "وقت المباراة"


def tr_jordan_time():
    return "Jordan Time" if current_lang == "EN" else "توقيت الأردن"


def format_status(status):
    status = str(status).upper().strip()

    if status == "LIVE":
        return lang_data["live"]
    if status == "FINISHED":
        return lang_data["finished"]
    return lang_data["scheduled"]


def build_match_number_map(df_matches):
    """
    Creates a clean display number for each match: 1, 2, 3 ...
    The real MatchID remains unchanged in Sheets and predictions.
    """
    if df_matches is None or df_matches.empty:
        return {}

    df = df_matches.copy()

    if "MatchID" not in df.columns:
        return {}

    df["_match_id_text"] = df["MatchID"].astype(str)

    if "Kickoff" in df.columns:
        df["_kickoff_sort"] = pd.to_datetime(
            df["Kickoff"],
            format="%Y-%m-%d %H:%M",
            errors="coerce"
        )
    else:
        df["_kickoff_sort"] = pd.NaT

    df = df.sort_values(
        by=["_kickoff_sort", "_match_id_text"],
        na_position="last"
    ).reset_index(drop=True)

    return {
        str(row["MatchID"]): index + 1
        for index, row in df.iterrows()
    }


def format_match_number(match_number_map, match_id):
    number = match_number_map.get(str(match_id), str(match_id))

    if current_lang == "AR":
        return f"المباراة {number}"

    return f"Match {number}"


def format_prediction_display(match, pred_row):
    stage = str(match["Stage"]).upper().strip()
    team_a = str(match["TeamA"])
    team_b = str(match["TeamB"])

    pred_winner = str(pred_row["PredWinner"])
    pred_method = str(pred_row["PredMethod"])

    if stage == "GROUP":
        if pred_winner == "A":
            return (
                f"{tr_team(team_a)} wins"
                if current_lang == "EN"
                else f"فوز {tr_team(team_a)}"
            )

        if pred_winner == "B":
            return (
                f"{tr_team(team_b)} wins"
                if current_lang == "EN"
                else f"فوز {tr_team(team_b)}"
            )

        if pred_winner == "DRAW":
            return lang_data["draw"]

        return pred_winner

    method_text = {
        "NORMAL": lang_data["normal"],
        "ET": lang_data["et"],
        "PEN": lang_data["pen"]
    }.get(pred_method, pred_method)

    return (
        f"{tr_team(pred_winner)} - {method_text}"
        if current_lang == "EN"
        else f"{tr_team(pred_winner)} - {method_text}"
    )

def get_user_prediction_text(match, existing_prediction):
    if existing_prediction.empty:
        return "No prediction yet" if current_lang == "EN" else "لا يوجد توقع محفوظ بعد"

    pred_row = existing_prediction.iloc[0]
    return format_prediction_display(match, pred_row)


def save_banter_message(username, message):
    username = clean_username(username)
    message = str(message).strip()

    if not message:
        return False

    ws = get_worksheet("BanterRoom")

    timestamp = datetime.now(ZoneInfo("Asia/Amman")).strftime("%Y-%m-%d %H:%M")

    ws.append_row([
        timestamp,
        username,
        message
    ])

    clear_all_cache()
    return True


@st.cache_data(ttl=3)
def load_banter_messages():
    df = load_sheet("BanterRoom")

    needed_cols = ["Timestamp", "Username", "Message"]

    for col in needed_cols:
        if col not in df.columns:
            df[col] = ""

    return df[needed_cols]

# =========================================================
# 7. Predictions Helpers
# =========================================================
def get_existing_prediction(df_preds, username, match_id):
    if df_preds.empty:
        return pd.DataFrame()

    if "Username" not in df_preds.columns or "MatchID" not in df_preds.columns:
        return pd.DataFrame()

    return df_preds[
        (df_preds["Username"].astype(str) == str(username)) &
        (df_preds["MatchID"].astype(str) == str(match_id))
    ]


def save_prediction(username, match, pred_winner, pred_method):
    ws = get_worksheet("Predictions")
    df_preds = load_sheet("Predictions")

    match_id = str(match["MatchID"])
    stage = str(match["Stage"])

    locked = is_match_locked(match["Kickoff"], match["Status"])

    if locked:
        st.error(lang_data["locked"])
        return

    existing = get_existing_prediction(df_preds, username, match_id)

    new_row = [
        username,
        match_id,
        stage,
        pred_winner,
        pred_method,
        0,
        False,
        now_jordan().strftime("%Y-%m-%d %H:%M:%S")
    ]

    if existing.empty:
        ws.append_row(new_row)
    else:
        row_index = existing.index[0] + 2
        ws.update(f"A{row_index}:H{row_index}", [new_row])

    clear_all_cache()
    st.success("✅ Saved successfully")
    st.rerun()

# =========================================================
# 8. System Settings + Sync
# =========================================================
def get_system_setting(key, default_value=""):
    df_settings = load_sheet("SystemSettings")

    if df_settings.empty:
        return default_value

    row = df_settings[df_settings["Key"].astype(str) == str(key)]

    if row.empty:
        return default_value

    return str(row.iloc[0]["Value"])


def update_system_setting(key, value):
    ws = get_worksheet("SystemSettings")
    df_settings = load_sheet("SystemSettings")

    existing = df_settings[df_settings["Key"].astype(str) == str(key)]

    if existing.empty:
        ws.append_row([key, value])
    else:
        row_index = existing.index[0] + 2
        ws.update(f"A{row_index}:B{row_index}", [[key, value]])

    clear_all_cache()


def sync_matchcache_from_api():
    matches = get_normalized_worldcup_matches()

    if not matches:
        st.warning("No matches received from API.")
        return

    ws = get_worksheet("MatchCache")

    rows = [[
        "MatchID",
        "Stage",
        "Group",
        "TeamA",
        "TeamB",
        "Kickoff",
        "Status",
        "RealWinner",
        "RealMethod",
        "LastSynced"
    ]]

    sync_time = now_jordan().strftime("%Y-%m-%d %H:%M:%S")

    for m in matches:
        rows.append([
            m["MatchID"],
            m["Stage"],
            m["Group"],
            m["TeamA"],
            m["TeamB"],
            m["Kickoff"],
            m["Status"],
            m["RealWinner"],
            m["RealMethod"],
            sync_time
        ])

    ws.clear()
    ws.update("A1:J" + str(len(rows)), rows)
    clear_all_cache()


def sync_group_standings_from_api():
    standings = normalize_group_standings()

    ws = get_worksheet("GroupStandings")

    rows = [[
        "Group",
        "Position",
        "Team"
    ]]

    for row in standings:
        rows.append([
            row["Group"],
            row["Position"],
            row["Team"]
        ])

    ws.clear()
    ws.update("A1:C" + str(len(rows)), rows)

    clear_all_cache()


def auto_sync_if_needed():
    last_sync_text = get_system_setting(
        "LastAutoSync",
        "2000-01-01 00:00:00"
    )

    try:
        last_sync = datetime.strptime(last_sync_text, "%Y-%m-%d %H:%M:%S")
        last_sync = last_sync.replace(tzinfo=ZoneInfo("Asia/Amman"))
    except Exception:
        last_sync = datetime(2000, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("Asia/Amman"))

    now = now_jordan()
    minutes_passed = (now - last_sync).total_seconds() / 60

    if minutes_passed >= 15:
        sync_matchcache_from_api()
        sync_group_standings_from_api()

        # بعد تحديث النتائج والترتيب، أعد حساب النقاط تلقائيًا
        recalculate_all_scores()

        # تنظيف الكاش حتى تظهر النقاط الجديدة مباشرة
        clear_all_cache()

        update_system_setting(
            "LastAutoSync",
            now.strftime("%Y-%m-%d %H:%M:%S")
        )
        
# =========================================================
# 9. Champion Helpers
# =========================================================
def get_available_teams_from_matches(df_matches):
    teams = []

    if df_matches.empty:
        return teams

    for _, match in df_matches.iterrows():
        team_a = str(match["TeamA"]).strip()
        team_b = str(match["TeamB"]).strip()

        if team_a and team_a.upper() != "TBD":
            teams.append(team_a)

        if team_b and team_b.upper() != "TBD":
            teams.append(team_b)

    return sorted(list(set(teams)))


def is_champion_prediction_locked(df_matches):
    if df_matches.empty:
        return False

    statuses = df_matches["Status"].astype(str).str.upper().tolist()

    if "LIVE" in statuses or "FINISHED" in statuses:
        return True

    kickoff_times = []

    for _, match in df_matches.iterrows():
        try:
            kickoff = datetime.strptime(str(match["Kickoff"]), "%Y-%m-%d %H:%M")
            kickoff = kickoff.replace(tzinfo=ZoneInfo("Asia/Amman"))
            kickoff_times.append(kickoff)
        except Exception:
            pass

    if not kickoff_times:
        return False

    return now_jordan() >= min(kickoff_times)


def get_existing_champion_prediction(df_champions, username):
    if df_champions.empty:
        return pd.DataFrame()

    if "Username" not in df_champions.columns:
        return pd.DataFrame()

    return df_champions[
        df_champions["Username"].astype(str) == str(username)
    ]


def save_champion_prediction(username, champion, locked):
    if locked:
        st.error(lang_data["champion_locked"])
        return

    ws = get_worksheet("ChampionPredictions")
    df_champions = load_sheet("ChampionPredictions")

    existing = get_existing_champion_prediction(df_champions, username)

    new_row = [
        username,
        champion,
        0,
        False,
        now_jordan().strftime("%Y-%m-%d %H:%M:%S")
    ]

    if existing.empty:
        ws.append_row(new_row)
    else:
        row_index = existing.index[0] + 2
        ws.update(f"A{row_index}:E{row_index}", [new_row])

    clear_all_cache()
    st.success(lang_data["champion_saved"])
    st.rerun()


def get_real_champion(df_matches):
    if df_matches.empty:
        return ""

    final_matches = df_matches[
        df_matches["Stage"].astype(str).str.upper() == "FINAL"
    ]

    if final_matches.empty:
        return ""

    final_match = final_matches.iloc[0]

    if str(final_match["Status"]).upper().strip() != "FINISHED":
        return ""

    return str(final_match["RealWinner"]).strip()

# =========================================================
# 10. Group Ranking Helpers
# =========================================================
def get_groups_from_matches(df_matches):
    if df_matches.empty:
        return []

    group_matches = df_matches[
        df_matches["Stage"].astype(str).str.upper() == "GROUP"
    ]

    groups = group_matches["Group"].dropna().astype(str).str.strip()
    groups = [g for g in groups if g != ""]
    return sorted(list(set(groups)))


def get_teams_in_group(df_matches, group_name):
    group_matches = df_matches[
        (df_matches["Stage"].astype(str).str.upper() == "GROUP") &
        (df_matches["Group"].astype(str).str.upper() == str(group_name).upper())
    ]

    teams = []

    for _, match in group_matches.iterrows():
        team_a = str(match["TeamA"]).strip()
        team_b = str(match["TeamB"]).strip()
        
        if team_a and team_a.upper() != "TBD":
            teams.append(team_a)

        if team_b and team_b.upper() != "TBD":
            teams.append(team_b)

    return sorted(list(set(teams)))


def get_remaining_teams(all_teams, selected_teams):
    selected_clean = [
        str(team).strip()
        for team in selected_teams
        if str(team).strip()
    ]

    return [
        team for team in all_teams
        if str(team).strip() not in selected_clean
    ]


def is_group_ranking_locked(df_matches, group_name):
    group_matches = df_matches[
        (df_matches["Stage"].astype(str).str.upper() == "GROUP") &
        (df_matches["Group"].astype(str).str.upper() == str(group_name).upper())
    ]

    if group_matches.empty:
        return False

    statuses = group_matches["Status"].astype(str).str.upper().tolist()

    if "LIVE" in statuses or "FINISHED" in statuses:
        return True

    kickoff_times = []

    for _, match in group_matches.iterrows():
        try:
            kickoff = datetime.strptime(str(match["Kickoff"]), "%Y-%m-%d %H:%M")
            kickoff = kickoff.replace(tzinfo=ZoneInfo("Asia/Amman"))
            kickoff_times.append(kickoff)
        except Exception:
            pass

    if not kickoff_times:
        return False

    return now_jordan() >= min(kickoff_times)


def get_existing_group_ranking_prediction(df_group_ranks, username, group_name):
    if df_group_ranks.empty:
        return pd.DataFrame()

    if "Username" not in df_group_ranks.columns or "Group" not in df_group_ranks.columns:
        return pd.DataFrame()

    return df_group_ranks[
        (df_group_ranks["Username"].astype(str) == str(username)) &
        (df_group_ranks["Group"].astype(str).str.upper() == str(group_name).upper())
    ]


def save_group_ranking_prediction(username, group_name, ranking, locked):
    if locked:
        st.error(lang_data["group_rank_locked"])
        return

    if len(ranking) != 4:
        st.error("Please select 4 teams.")
        return

    if len(set(ranking)) != 4:
        st.error("You cannot select the same team more than once.")
        return

    ws = get_worksheet("GroupRankingPredictions")
    df_group_ranks = load_sheet("GroupRankingPredictions")

    existing = get_existing_group_ranking_prediction(
        df_group_ranks,
        username,
        group_name
    )

    new_row = [
        username,
        group_name,
        ranking[0],
        ranking[1],
        ranking[2],
        ranking[3],
        0,
        False,
        now_jordan().strftime("%Y-%m-%d %H:%M:%S")
    ]

    if existing.empty:
        ws.append_row(new_row)
    else:
        row_index = existing.index[0] + 2
        ws.update(f"A{row_index}:I{row_index}", [new_row])

    clear_all_cache()
    st.success(lang_data["group_rank_saved"])
    st.rerun()


def is_group_stage_finished(df_matches):
    """
    يتحقق هل كل مباريات دور المجموعات انتهت رسميًا.
    لا يتم احتساب نقاط ترتيب المجموعات إلا بعد نهاية دور المجموعات بالكامل.
    """
    if df_matches.empty:
        return False

    group_matches = df_matches[
        df_matches["Stage"].astype(str).str.upper() == "GROUP"
    ]

    if group_matches.empty:
        return False

    statuses = group_matches["Status"].astype(str).str.upper().tolist()

    return all(status == "FINISHED" for status in statuses)


def get_real_group_order(df_group_standings, group_name):
    if df_group_standings.empty:
        return []

    group_rows = df_group_standings[
        df_group_standings["Group"].astype(str).str.upper() == str(group_name).upper()
    ].copy()

    if group_rows.empty:
        return []

    group_rows["Position"] = pd.to_numeric(
        group_rows["Position"],
        errors="coerce"
    )

    group_rows = group_rows.dropna(subset=["Position"])
    group_rows = group_rows.sort_values(by="Position")

    return group_rows["Team"].astype(str).tolist()


def calc_group_ranking_points_from_orders(predicted_order, real_order):
    """
    Group ranking points:
    - Only first 3 positions count.
    - Each correct position from top 3 = 1 point.
    - Max points per group = 3.
    - 4th place does not count.
    """

    if not predicted_order or not real_order:
        return 0

    points = 0

    max_positions = min(3, len(predicted_order), len(real_order))

    for i in range(max_positions):
        if str(predicted_order[i]).strip() == str(real_order[i]).strip():
            points += 1

    return points

# =========================================================
# 11. Score Calculation
# =========================================================
def recalculate_all_scores():
    df_users = load_sheet("Users")
    df_matches = load_sheet("MatchCache")
    df_preds = load_sheet("Predictions")
    df_champions = load_sheet("ChampionPredictions")
    df_group_ranks = load_sheet("GroupRankingPredictions")
    df_group_standings = load_sheet("GroupStandings")

    ws_preds = get_worksheet("Predictions")
    ws_users = get_worksheet("Users")
    ws_champions = get_worksheet("ChampionPredictions")
    ws_group_ranks = get_worksheet("GroupRankingPredictions")

    if df_users.empty or df_matches.empty:
        return

    # نجمع نقاط كل لاعب من الصفر
    user_points = {
        str(row["Username"]): 0
        for _, row in df_users.iterrows()
    }

    # =====================================================
    # 1. Match Predictions Points
    # =====================================================
    pred_updates = []

    if not df_preds.empty:
        for _, pred in df_preds.iterrows():
            username = str(pred["Username"])
            match_id = str(pred["MatchID"])

            points = 0
            locked_value = False

            match_row = df_matches[
                df_matches["MatchID"].astype(str) == match_id
            ]

            if not match_row.empty:
                match = match_row.iloc[0]
                status = str(match["Status"]).upper().strip()

                if status == "FINISHED":
                    stage = str(match["Stage"]).upper().strip()
                    pred_winner = str(pred["PredWinner"])
                    pred_method = str(pred["PredMethod"])

                    real_winner = str(match["RealWinner"])
                    real_method = str(match["RealMethod"])

                    if stage == "GROUP":
                        points = calc_group_match_points(
                            pred_winner,
                            real_winner
                        )
                    else:
                        points = calc_knockout_points(
                            pred_winner,
                            pred_method,
                            real_winner,
                            real_method
                        )

                    locked_value = True
                    user_points[username] = user_points.get(username, 0) + points

            pred_updates.append([points, locked_value])

        if pred_updates:
            ws_preds.update(
                f"F2:G{len(pred_updates) + 1}",
                pred_updates
            )

    # =====================================================
    # 2. Champion Prediction Points
    # =====================================================
    champion_updates = []
    real_champion = get_real_champion(df_matches)

    if not df_champions.empty:
        for _, champ_pred in df_champions.iterrows():
            username = str(champ_pred["Username"])
            predicted_champion = str(champ_pred["Champion"]).strip()

            champion_points = 0
            locked_value = False

            if real_champion:
                champion_points = 10 if predicted_champion == real_champion else 0
                locked_value = True
                user_points[username] = user_points.get(username, 0) + champion_points

            champion_updates.append([champion_points, locked_value])

        if champion_updates:
            ws_champions.update(
                f"C2:D{len(champion_updates) + 1}",
                champion_updates
            )

    # =====================================================
    # 3. Group Ranking Points
    # =====================================================
    group_rank_updates = []
    group_stage_done = is_group_stage_finished(df_matches)

    if not df_group_ranks.empty:
        for _, rank_pred in df_group_ranks.iterrows():
            username = str(rank_pred["Username"])
            group_name = str(rank_pred["Group"])

            group_points = 0
            locked_value = False

            if group_stage_done:
                predicted_order = [
                    str(rank_pred["Pos1"]),
                    str(rank_pred["Pos2"]),
                    str(rank_pred["Pos3"]),
                    str(rank_pred["Pos4"])
                ]

                real_order = get_real_group_order(
                    df_group_standings,
                    group_name
                )

                group_points = calc_group_ranking_points_from_orders(
                    predicted_order,
                    real_order
                )

                locked_value = True
                user_points[username] = user_points.get(username, 0) + group_points

            group_rank_updates.append([group_points, locked_value])

        if group_rank_updates:
            ws_group_ranks.update(
                f"G2:H{len(group_rank_updates) + 1}",
                group_rank_updates
            )

    # =====================================================
    # 4. Update Users Scoreboard
    # =====================================================
    users_points_updates = []

    for _, user in df_users.iterrows():
        username = str(user["Username"])
        total = user_points.get(username, 0)
        users_points_updates.append([total])

    if users_points_updates:
        ws_users.update(
            f"C2:C{len(users_points_updates) + 1}",
            users_points_updates
        )

    clear_all_cache()



# =========================================================
# 13. Language Top Bar
# =========================================================


# =========================================================
# 14. Header
# =========================================================
img_base64 = get_base64_image("logo.png")

if img_base64:
    st.markdown(
        f"""
        <div class="capitano-header">
            <img src="data:image/png;base64,{img_base64}" class="clean-logo">
            <h1 class="capitano-title">{lang_data["title"]}</h1>
            <p class="capitano-subtitle">{lang_data["subtitle"]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"""
        <div class="capitano-header">
            <h1 class="capitano-title">{lang_data["title"]}</h1>
            <p class="capitano-subtitle">{lang_data["subtitle"]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.write("---")

# =========================================================
# 15. Main App
# =========================================================
try:
    df_users = load_sheet("Users")
    
    if not st.session_state.is_logged_in:
        saved_token = cookie_manager.get(COOKIE_NAME)

    # أحيانًا CookieManager يحتاج rerun صغير بعد refresh عشان يقرأ الكوكي
        if not saved_token and not st.session_state.get("cookie_checked_once", False):
            st.session_state.cookie_checked_once = True
            st.rerun()

        saved_username = validate_login_cookie(
            df_users,
            saved_token
        )

        if saved_username:
            st.session_state.is_logged_in = True
            st.session_state.username = saved_username

            saved_lang = get_user_language(saved_username)
            if saved_lang in ["EN", "AR"]:
                st.session_state.lang = saved_lang

            st.rerun()

    if not st.session_state.is_logged_in:
        st.markdown(
            f"<h3 style='text-align:center; color:#94a3b8; font-size:20px; margin-bottom:20px;'>{lang_data['login_header']}</h3>",
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            
            login_lang = st.selectbox(
                "🌐 Language / اللغة",
                ["EN", "AR"],
                index=0 if st.session_state.lang == "EN" else 1,
                key="login_language_select"
            )

            if login_lang != st.session_state.lang:
                st.session_state.lang = login_lang
                st.rerun()
            
            st.markdown(
                f"""
                <div class="auth-card">
                    <div class="auth-title">
                        {"Welcome to Capitano 26" if current_lang == "EN" else "أهلاً بك في كابيتانو 26"}
                    </div>
                    <div class="auth-slogan">
                        {"PREDICT. COMPETE. CHALLENGE." if current_lang == "EN" else "توقّع. نافس. وتحدّى"}
                    </div>
                    <div class="auth-desc">
                        {
                            "Create your account, predict the World Cup, challenge your friends, and climb the leaderboard."
                            if current_lang == "EN"
                            else "أنشئ حسابك، توقّع مباريات كأس العالم، تحدّى أصدقائك، وارتقِ لوحة الصدارة."
                        }
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            auth_mode = st.radio(
                "Auth Mode",
                [lang_data["auth_login"], lang_data["auth_create"]],
                horizontal=True,
                label_visibility="collapsed"
            )

            if auth_mode == lang_data["auth_login"]:
                if st.session_state.password_reset_success:
                    st.success(
                        "Password reset successfully. Please log in with your new password."
                        if current_lang == "EN"
                        else "تمت إعادة تعيين كلمة السر بنجاح. سجّل الدخول بكلمة السر الجديدة."
                    )
                    st.session_state.password_reset_success = False
                input_user = st.text_input(
                    lang_data["user_label"],
                    placeholder="username"
                )

                input_pass = st.text_input(
                    lang_data["pass_label"],
                    type="password",
                    placeholder="••••••••"
                )

                btn_login = st.button(
                    lang_data["login_btn"],
                    use_container_width=True
                )

                if btn_login:
                    user_rows = df_users[
                        df_users["Username"].astype(str).apply(lambda x: clean_username(x).lower())
                        == clean_username(input_user).lower()
                    ]

                    user_match = pd.DataFrame()

                    if not user_rows.empty:
                        stored_password = str(user_rows.iloc[0]["Password"])

                        if verify_password(input_pass, stored_password):
                            user_match = user_rows

                    if not user_match.empty:
                        real_username = str(user_rows.iloc[0]["Username"])
                        stored_password = str(user_rows.iloc[0]["Password"])
                        
                        st.session_state.is_logged_in = True
                        st.session_state.username = real_username
                        
                        login_cookie = make_login_cookie(
                            real_username,
                            stored_password
                        )

                        cookie_manager.set(
                            COOKIE_NAME,
                            login_cookie,
                            expires_at=datetime.now() + timedelta(days=30),
                            key="set_login_cookie"
                        )
                        
                        if "cookie_checked_once" in st.session_state:
                            del st.session_state.cookie_checked_once
                        
                        saved_lang = get_user_language(real_username)
                        if saved_lang in ["EN", "AR"]:
                            st.session_state.lang = saved_lang

                        st.rerun()
                    else:
                        st.error(lang_data["login_err"])
                        
                    st.write("---")

                with st.expander(
                        "Forgot password?"
                        if current_lang == "EN"
                        else "نسيت كلمة السر؟",
                        expanded=False
                ):
                        reset_user = st.text_input(
                            "Username" if current_lang == "EN" else "اسم المستخدم",
                            key="reset_username_input"
                        )

                        recovery_code = st.text_input(
                            "Recovery code" if current_lang == "EN" else "رمز الاسترجاع",
                            type="password",
                            key="reset_recovery_code_input"
                        )

                        new_reset_pass = st.text_input(
                            "New password" if current_lang == "EN" else "كلمة السر الجديدة",
                            type="password",
                            key="reset_new_password_input"
                        )

                        confirm_reset_pass = st.text_input(
                            "Confirm new password" if current_lang == "EN" else "تأكيد كلمة السر الجديدة",
                            type="password",
                            key="reset_confirm_password_input"
                        )

                        if st.button(
                                "Reset Password" if current_lang == "EN" else "إعادة تعيين كلمة السر",
                                use_container_width=True,
                                key="reset_password_btn"
                        ):
                            if not reset_user or not recovery_code or not new_reset_pass or not confirm_reset_pass:
                                st.warning(
                                    "Please fill all fields."
                                    if current_lang == "EN"
                                    else "يرجى تعبئة جميع الخانات."
                                )

                            elif new_reset_pass != confirm_reset_pass:
                                st.error(
                                    "Passwords do not match."
                                    if current_lang == "EN"
                                    else "كلمتا السر غير متطابقتين."
                                )

                            else:
                                ok, msg = reset_password_with_recovery_code(
                                    reset_user,
                                    recovery_code,
                                    new_reset_pass
                                )

                                if ok:
                                    clear_all_cache()
                                    
                                    st.session_state.password_reset_success = True
                                    
                                    st.rerun()

                                elif msg == "wrong_recovery_code":
                                    st.error(
                                        "Recovery code is incorrect."
                                        if current_lang == "EN"
                                        else "رمز الاسترجاع غير صحيح."
                                    )

                                elif msg == "user_not_found":
                                    st.error(
                                        "User not found."
                                        if current_lang == "EN"
                                        else "لم يتم العثور على المستخدم."
                                    )

                                elif msg == "short_password":
                                    st.error(
                                        "New password must be at least 4 characters."
                                        if current_lang == "EN"
                                        else "كلمة السر الجديدة يجب أن تكون 4 أحرف على الأقل."
                                    )

                                elif msg == "no_recovery_code":
                                    st.error(
                                        "This account does not have a recovery code. Contact the game admin."
                                        if current_lang == "EN"
                                        else "هذا الحساب لا يحتوي على رمز استرجاع. تواصل مع أدمن اللعبة."
                                    )

                                else:
                                    st.error(
                                        f"Could not reset password. Reason: {msg}"
                                        if current_lang == "EN"
                                        else f"تعذر إعادة تعيين كلمة السر. السبب: {msg}"
                                    )        

            else:
                st.markdown(
                    f"<h4 style='text-align:center; color:#00FF87;'>{lang_data['create_header']}</h4>",
                    unsafe_allow_html=True
                )

                new_user = st.text_input(
                    lang_data["user_label"],
                    placeholder="Choose username"
                )
                
                st.caption(lang_data["username_hint"])

                new_pass = st.text_input(
                    lang_data["pass_label"],
                    type="password",
                    placeholder="••••••••",
                    key="new_account_password"
                )

                confirm_pass = st.text_input(
                    lang_data["confirm_pass_label"],
                    type="password",
                    placeholder="••••••••",
                    key="new_account_confirm_password"
                )
                
                
                recovery_code_create = st.text_input(
                    "Recovery Code"
                    if current_lang == "EN"
                    else "رمز الاسترجاع",
                    type="password",
                    placeholder="e.g: 1234",
                    key="new_account_recovery_code",
                    help=(
                        "Keep this code safe. You will use it if you forget your password."
                        if current_lang == "EN"
                        else "احفظ هذا الرمز جيدًا. ستستخدمه إذا نسيت كلمة السر."
                    )
                )

                btn_create = st.button(
                    lang_data["create_btn"],
                    use_container_width=True
                )

                if btn_create:
                    new_user_clean = clean_username(new_user)
                    valid_username, username_error = is_valid_username(new_user_clean)

                    if not new_user_clean or not new_pass or not confirm_pass or not recovery_code_create:
                        st.error(
                            "Please fill all fields."
                            if current_lang == "EN"
                            else "يرجى تعبئة جميع الخانات."
                        )
                        
                    elif not valid_username:
                        if username_error == "length":
                            st.error(lang_data["create_err_username_len"])
                        else:
                            st.error(lang_data["create_err_username_chars"])
                            
                    elif len(str(new_pass)) < 4:
                        st.error(lang_data["create_err_short"])
                        
                    elif len(str(recovery_code_create).strip()) < 4:
                        st.error(
                            "Recovery code must be at least 4 characters."
                            if current_lang == "EN"
                            else "رمز الاسترجاع يجب أن يكون 4 أحرف أو أرقام على الأقل."
                        )    

                    elif str(new_pass) != str(confirm_pass):
                        st.error(lang_data["create_err_match"])
                        
                    elif username_exists(df_users, new_user_clean):
                        st.error(lang_data["create_err_exists"])

                    else:
                        create_new_user(
                            new_user_clean,
                            new_pass,
                            recovery_code_create,
                            st.session_state.lang
                        )
                        st.success(lang_data["create_success"])

    else:
        if "auto_sync_checked" not in st.session_state:
            auto_sync_if_needed()
            st.session_state.auto_sync_checked = True

        align = "right" if current_lang == "AR" else "left"

        st.markdown(
            f"""
            <div style='text-align:{align}; color:#00FF87; font-weight:bold; margin-bottom:15px;'>
                👋 {lang_data['welcome']},
                <span style='color:#fff;'>{st.session_state.username}</span>!
            </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.expander(lang_data["how_title"]):
            st.markdown(
                f"""
        {lang_data["how_intro"]}

        1. {lang_data["how_a"]}
        2. {lang_data["how_b"]}
        3. {lang_data["how_c"]}
        4. {lang_data["how_d"]}
        
        ---

        - {lang_data["how_lock_1"]}
        - {lang_data["how_lock_2"]}
        - {lang_data["how_lock_3"]}
        - {lang_data["how_reveal"]}
        - {lang_data["how_update"]}
            """
        )


        with st.expander(lang_data["rules_title"]):
            st.markdown(
                f"""
        ### {lang_data["rules_group_title"]}

        {lang_data["rules_group_1"]}

        - {lang_data["rules_group_2"]}
        - {lang_data["rules_group_3"]}
        - {lang_data["rules_group_4"]}
        - {lang_data["rules_group_5"]}
        
        ---
        
        ### {lang_data["rules_rank_title"]}
        
        - {lang_data["rules_rank_1"]}
        - {lang_data["rules_rank_2"]}
        - {lang_data["rules_rank_3"]}
        - {lang_data["rules_rank_4"]}
        - {lang_data["rules_rank_5"]}
        - {lang_data["rules_rank_6"]}
        
        ---

        ### {lang_data["rules_champ_title"]}

        - {lang_data["rules_champ_1"]}
        - {lang_data["rules_champ_2"]}
        
        ---

        ### {lang_data["rules_ko_title"]}
    
        {lang_data["rules_ko_1"]}

        - {lang_data["rules_ko_2"]}
        - {lang_data["rules_ko_3"]}
        - {lang_data["rules_ko_4"]}
        - {lang_data["rules_ko_5"]}
        - {lang_data["rules_ko_6"]}
        - {lang_data["rules_ko_7"]}
        - {lang_data["rules_ko_8"]}
        - {lang_data["rules_ko_9"]}
        - {lang_data["rules_ko_10"]}
        - {lang_data["rules_ko_11"]}
        - {lang_data["rules_ko_12"]}
                """
            )
        
        page_options = [
            lang_data["tab_score"],
            lang_data["tab_pred"],
            lang_data["tab_reveal"],
            lang_data["tab_champion"],
            lang_data["tab_group_rank"],
            lang_data["tab_chat"],
            lang_data["tab_settings"]
        ]

        if is_admin_user(st.session_state.username):
            page_options.append(lang_data["tab_admin"])

        page = st.radio(
            "Navigation",
            page_options,
            horizontal=True,
            label_visibility="collapsed"
            )

        st.write("---")

        # =================================================
        # Tab 1: Scoreboard
        # =================================================
        if page == lang_data["tab_score"]:
            st.markdown(f"## 🏆 {lang_data['leaderboard']}")

            if df_users.empty:
                st.warning(lang_data["no_data"])

            else:
                df_score = df_users.copy()
                
                df_score["Username"] = df_score["Username"].astype(str)
                df_score["Points"] = pd.to_numeric(df_score["Points"], errors="coerce").fillna(0).astype(int)
                
                df_score = df_score.sort_values(
                    by=["Points", "Username"],
                    ascending=[False, True]
                ).reset_index(drop=True)

                leader_points = int(df_score.iloc[0]["Points"]) if not df_score.empty else 0

                # ===============================
                # Top 3 Cards
                # ===============================
                top3 = df_score.head(3)

                if not top3.empty:
                    st.markdown(
                        "### 🔥 Top Contenders"
                        if current_lang == "EN"
                        else "### 🔥 أقوى المنافسين"
                    )
                    
                    top_cols = st.columns(3)
                    
                    medals = ["🥇", "🥈", "🥉"]
                    rank_labels_en = ["1st Place", "2nd Place", "3rd Place"]
                    rank_labels_ar = ["المركز الأول", "المركز الثاني", "المركز الثالث"]
                    
                    for i, (_, row) in enumerate(top3.iterrows()):
                        username = str(row["Username"])
                        points = int(row["Points"])
                        avatar_path = get_avatar_for_username(username)
                        gap = leader_points - points
                        
                        with top_cols[i]:
                            with st.container(border=True):
                                st.markdown(
                                    f"<h1 style='text-align:center; margin-bottom:0;'>{medals[i]}</h1>",
                                    unsafe_allow_html=True
                                )
                                
                                if avatar_path:
                                    st.markdown(
                                        avatar_html(avatar_path, size=92),
                                        unsafe_allow_html=True
                                    )

                                rank_label = rank_labels_en[i] if current_lang == "EN" else rank_labels_ar[i]
                                
                                st.markdown(
                                    f"<h4 style='text-align:center; color:#00FF87; margin-top:0;'>{rank_label}</h4>",
                                    unsafe_allow_html=True
                                )

                                st.markdown(
                                    f"<h3 style='text-align:center; margin-bottom:4px;'>{username}</h3>",
                                    unsafe_allow_html=True
                                )
                                
                                st.metric(
                                    "Points" if current_lang == "EN" else "النقاط",
                                    points
                                )
                                
                                if i == 0:
                                    st.success(
                                        "Current leader"
                                        if current_lang == "EN"
                                        else "المتصدر الحالي"
                                    )
                                else:
                                    st.caption(
                                        f"{gap} pts behind leader"
                                        if current_lang == "EN"
                                        else f"يبعد عن المتصدر بـ {gap} نقطة"
                                    )

                st.write("---")

                # ===============================
                # Full Ranking Table
                # ===============================
                st.markdown(
                    "### 📊 Full Ranking"
                    if current_lang == "EN"
                    else "### 📊 الترتيب الكامل"
                )
                
                ranking_rows = []
                
                for idx, row in df_score.iterrows():
                    rank_num = idx + 1
                    username = str(row["Username"])
                    points = int(row["Points"])
                    gap = leader_points - points
                    
                    if rank_num == 1:
                        rank_display = "🥇 1"
                    elif rank_num == 2:
                        rank_display = "🥈 2"
                    elif rank_num == 3:
                        rank_display = "🥉 3"
                    else:
                        rank_display = f"🏅 {rank_num}"

                    
                    ranking_rows.append({
                        lang_data["rank"]: rank_display,
                        lang_data["user"]: username,
                        lang_data["pts"]: points,
                        "Gap" if current_lang == "EN" else "الفارق": gap
                    })

                st.dataframe(
                    pd.DataFrame(ranking_rows),
                    use_container_width=True,
                    hide_index=True
                )
        
        # =================================================
        # Tab 2: Live Predictions
        # =================================================
        elif page == lang_data["tab_pred"]:
            st.markdown(
                f"<h3 style='font-size:20px; font-weight:800;'>{lang_data['pred_title']}</h3>",
                unsafe_allow_html=True
            )

            df_matches = load_sheet("MatchCache")
            df_preds = load_sheet("Predictions")
            match_number_map = build_match_number_map(df_matches)

            if df_matches.empty:
                st.warning("No matches found in MatchCache.")
            else:
                stages = list(df_matches["Stage"].dropna().unique())

                selected_stage = st.selectbox(
                    "Stage" if current_lang == "EN" else "المرحلة",
                    stages,
                    format_func=tr_stage
                )

                stage_matches = df_matches[
                    df_matches["Stage"].astype(str) == str(selected_stage)
                ]

                if str(selected_stage).upper() == "GROUP":
                    available_groups = sorted(
                        stage_matches["Group"].dropna().astype(str).unique().tolist()
                    )

                    selected_group_filter = st.selectbox(
                        "Group" if current_lang == "EN" else "المجموعة",
                        available_groups,
                        key="live_predictions_group_filter",
                        format_func=tr_group
                    )

                    stage_matches = stage_matches[
                        stage_matches["Group"].astype(str) == str(selected_group_filter)
                    ]

                for _, match in stage_matches.iterrows():
                    match_id = str(match["MatchID"])
                    match_label = format_match_number(match_number_map, match_id)
                    stage = str(match["Stage"]).upper().strip()
                    team_a = str(match["TeamA"])
                    team_b = str(match["TeamB"])

                    kickoff = str(match["Kickoff"])
                    status = str(match["Status"]).upper().strip()

                    ready = is_match_ready(match)
                    locked = is_match_locked(kickoff, status) or not ready

                    existing = get_existing_prediction(
                        df_preds,
                        st.session_state.username,
                        match_id
                    )

                    old_winner = None
                    old_method = None

                    if not existing.empty:
                        old_winner = str(existing.iloc[0]["PredWinner"])
                        old_method = str(existing.iloc[0]["PredMethod"])

                    current_prediction_text = get_user_prediction_text(match, existing)

                    stage_label = tr_stage(match["Stage"])
                    group_label = tr_group(match["Group"])

                    status_text = format_status(status) if not locked else lang_data["locked"]
                    pill_class = "locked-pill" if locked else "status-pill"

                    team_a_flag_path = get_team_flag_path(team_a)
                    team_b_flag_path = get_team_flag_path(team_b)

                    with st.container(border=True):
                        title_cols = st.columns([4.5, 1, 4.5])

                        with title_cols[0]:
                            left_cols = st.columns([0.9, 4])
                            with left_cols[0]:
                                if team_a_flag_path:
                                    st.image(team_a_flag_path, width=48)
                            with left_cols[1]:
                                st.markdown(
                                    f"<h3 style='margin-top:6px; margin-bottom:0;'>{tr_team(team_a)}</h3>",
                                    unsafe_allow_html=True
                                )

                        with title_cols[1]:
                            st.markdown(
                                f"<h3 style='text-align:center; color:#00FF87; margin-top:6px; margin-bottom:0;'>{tr_vs()}</h3>",
                                unsafe_allow_html=True
                            )

                        with title_cols[2]:
                            right_cols = st.columns([0.9, 4])
                            with right_cols[0]:
                                if team_b_flag_path:
                                    st.image(team_b_flag_path, width=56)
                            with right_cols[1]:
                                st.markdown(
                                    f"<h3 style='margin-top:6px; margin-bottom:0;'>{tr_team(team_b)}</h3>",
                                    unsafe_allow_html=True
                                )

                        st.caption(f"⚽ {match_label}")
                        st.caption(f"🏷️ {"Stage" if current_lang == "EN" else "المرحلة"}: {stage_label} | {"Group" if current_lang == "EN" else "المجموعة"}: {group_label}")
                        st.caption(f"🕒 {tr_kickoff_label()}: {kickoff} - {tr_jordan_time()}")

                        if locked:
                            st.error(status_text)
                        else:
                            st.success(status_text)

                        st.info(
                            f"**{'Your prediction' if current_lang == 'EN' else 'توقعك الحالي'}:** {current_prediction_text}"
                        )
                    
                    
                    if not ready:
                        st.info(
                            "This knockout match is waiting for confirmed teams."
                            if current_lang == "EN"
                            else "هذه المباراة الإقصائية بانتظار تأكيد طرفي المباراة."
                        )
                        st.write("---")
                        continue
                    

                    if stage == "GROUP":
                        winner_values = ["A", "DRAW", "B"]

                        def format_group_choice(choice):
                            if choice == "A":
                                return (
                                    f"{tr_team(team_a)} wins"
                                    if current_lang == "EN"
                                    else f"فوز {tr_team(team_a)}"
                                )
                            
                            if choice == "B":
                                return (
                                    f"{tr_team(team_b)} wins"
                                    if current_lang == "EN"
                                    else f"فوز {tr_team(team_b)}"
                                )

                            return lang_data["draw"]

                        default_index = 0
                        if old_winner in winner_values:
                            default_index = winner_values.index(old_winner)
                            
                        pred_winner = st.radio(
                            f"{lang_data['winner']} - {match_label}",
                            winner_values,
                            index=default_index,
                            horizontal=True,
                            disabled=locked,
                            key=f"group_{match_id}",
                            format_func=format_group_choice
                        )

                        pred_method = "GROUP"

                    else:
                        winner_options = [team_a, team_b]

                        default_winner_index = 0
                        if old_winner in winner_options:
                            default_winner_index = winner_options.index(old_winner)

                        pred_winner = st.radio(
                            f"{lang_data['winner']} - {match_label}",
                            winner_options,
                            index=default_winner_index,
                            horizontal=True,
                            disabled=locked,
                            key=f"ko_winner_{match_id}",
                            format_func=tr_team
                        )

                        method_options = {
                            lang_data["normal"]: "NORMAL",
                            lang_data["et"]: "ET",
                            lang_data["pen"]: "PEN"
                        }

                        method_labels = list(method_options.keys())
                        method_values = list(method_options.values())

                        default_method_index = 0
                        if old_method in method_values:
                            default_method_index = method_values.index(old_method)

                        selected_method_label = st.selectbox(
                            f"{lang_data['method']} - {match_label}",
                            method_labels,
                            index=default_method_index,
                            disabled=locked,
                            key=f"ko_method_{match_id}"
                        )

                        pred_method = method_options[selected_method_label]

                    if not locked:
                        if st.button(
                            f"✅ {lang_data['save']}",
                            key=f"save_{match_id}",
                            use_container_width=True
                        ):
                            save_prediction(
                                st.session_state.username,
                                match,
                                pred_winner,
                                pred_method
                            )
                    else:
                        st.info("🔒 This match is locked. Predictions can no longer be changed."
                                if current_lang == "EN"
                                else "🔒 تم إغلاق هذه المباراة. لا يمكن تعديل التوقع الآن."
                        )

                    st.write("---")

        # =================================================
        # Tab 3: Prediction Reveal
        # =================================================
        elif page == lang_data["tab_reveal"]:
            st.markdown(
                f"<h3 style='font-size:20px; font-weight:800;'>👀 {lang_data['tab_reveal']}</h3>",
                unsafe_allow_html=True
            )

            df_matches = load_sheet("MatchCache")
            df_preds = load_sheet("Predictions")
            match_number_map = build_match_number_map(df_matches)

            if df_matches.empty:
                st.warning("No matches found.")
            else:
                match_ids = df_matches["MatchID"].astype(str).tolist()

                def format_reveal_match(match_id):
                    row = df_matches[
                        df_matches["MatchID"].astype(str) == str(match_id)
                    ].iloc[0]
                    
                    match_label = format_match_number(match_number_map, row["MatchID"])

                    return (
                        f"{match_label} | {tr_team(row['TeamA'])} {tr_vs()} {tr_team(row['TeamB'])} | {format_status(row['Status'])}"
                    )

                selected_match_id = st.selectbox(
                    "Select match" if current_lang == "EN" else "اختر المباراة",
                    match_ids,
                    format_func=format_reveal_match
                )

                selected_match = df_matches[
                    df_matches["MatchID"].astype(str) == selected_match_id
                ].iloc[0]
                selected_match_label = format_match_number(match_number_map, selected_match_id)

                locked = is_match_locked(
                    selected_match["Kickoff"],
                    selected_match["Status"]
                )

                selected_team_a = str(selected_match["TeamA"])
                selected_team_b = str(selected_match["TeamB"])
                selected_team_a_display = get_team_display_with_flag(selected_team_a)
                selected_team_b_display = get_team_display_with_flag(selected_team_b)

                team_a = str(selected_match["TeamA"])
                team_b = str(selected_match["TeamB"])
                kickoff = str(selected_match["Kickoff"])
                status = str(selected_match["Status"])

                team_a_flag_path = get_team_flag_path(team_a)
                team_b_flag_path = get_team_flag_path(team_b)

                with st.container(border=True):
                    title_cols = st.columns([4.5, 1, 4.5])

                    with title_cols[0]:
                        left_cols = st.columns([1, 4])
                        with left_cols[0]:
                            if team_a_flag_path:
                                st.image(team_a_flag_path, width=52)
                        with left_cols[1]:
                            st.markdown(
                                f"<h3 style='margin-top:6px; margin-bottom:0;'>{tr_team(team_a)}</h3>",
                                unsafe_allow_html=True
                            )

                    with title_cols[1]:
                        st.markdown(
                            f"<h3 style='text-align:center; color:#00FF87; margin-top:6px; margin-bottom:0;'>{tr_vs()}</h3>",
                            unsafe_allow_html=True
                        )

                    with title_cols[2]:
                        right_cols = st.columns([1, 4])
                        with right_cols[0]:
                            if team_b_flag_path:
                                st.image(team_b_flag_path, width=52)
                        with right_cols[1]:
                            st.markdown(
                                f"<h3 style='margin-top:6px; margin-bottom:0;'>{tr_team(team_b)}</h3>",
                                unsafe_allow_html=True
                            )

                    st.caption(f"⚽ {selected_match_label}")
                    st.caption(f"🕒 {tr_kickoff_label()}: {kickoff} - {tr_jordan_time()}")
                    st.caption(
                        f"{'Status' if current_lang == 'EN' else 'الحالة'}: {format_status(status)}"
                    )

                if not locked:
                    st.warning(
                        "Predictions will be revealed when the match starts."
                        if current_lang == "EN"
                        else "سيتم كشف التوقعات عند بداية المباراة."
                    )
                else:
                    match_preds = df_preds[
                        df_preds["MatchID"].astype(str) == str(selected_match_id)
                    ]

                    if match_preds.empty:
                        st.info(
                            "No predictions submitted for this match."
                            if current_lang == "EN"
                            else "لا توجد توقعات مسجلة لهذه المباراة."
                        )
                    else:
                        st.markdown(
                            "### 👥 Players Predictions"
                            if current_lang == "EN"
                            else "### 👥 توقعات اللاعبين"
                        )

                        for _, pred in match_preds.iterrows():
                            username = str(pred.get("Username", "Unknown"))

                            pred_text = format_prediction_display(selected_match, pred)

                            points = pred.get("Points", "")
                            
                            if points == "" or pd.isna(points):
                                points_text = "Pending" if current_lang == "EN" else "بانتظار النتيجة"
                            else:
                                points_text = str(points)
                                
                            avatar_path = get_avatar_for_username(username)
                             
                            with st.container(border=True):
                                c_avatar, c_info, c_points = st.columns([1, 4, 1.2])

                            with c_avatar:
                                if avatar_path:
                                    st.markdown(
                                        avatar_html(avatar_path, size=74),
                                        unsafe_allow_html=True
                                    )

                            with c_info:
                                st.markdown(f"### {username}")
                                st.markdown(
                                    f"🎯 **{'Prediction' if current_lang == 'EN' else 'التوقع'}:** {pred_text}"
                                )

                            with c_points:
                                st.metric(
                                    "Points" if current_lang == "EN" else "النقاط",
                                    points_text
                                )

        # =================================================
        # Tab 4: Champion Pick
        # =================================================
        elif page == lang_data["tab_champion"]:
            st.markdown(
                "## 🏆 Champion Pick"
                if current_lang == "EN"
                else "## 🏆 توقع بطل البطولة"
            )   

            df_matches = load_sheet("MatchCache")
            df_champions = load_sheet("ChampionPredictions")

            tournament_started = False

            if not df_matches.empty:
                first_kickoff = df_matches["Kickoff"].dropna().astype(str).sort_values().iloc[0]
                tournament_started = is_match_locked(first_kickoff, "SCHEDULED")

            current_pick = ""

            if not df_champions.empty:
                user_champ = df_champions[
                    df_champions["Username"].astype(str) == str(st.session_state.username)
                ]

                if not user_champ.empty:
                    current_pick = str(user_champ.iloc[0]["Champion"])

            teams = sorted(
                list(
                    set(
                        df_matches["TeamA"].dropna().astype(str).tolist()
                        + df_matches["TeamB"].dropna().astype(str).tolist()
                    )
                )
            )

            teams = [
                team for team in teams
                if team and team.upper() not in ["TBD", "NONE", "NAN"]
            ]

            with st.container(border=True):
                st.markdown(
                    "### 🌍 Choose your World Cup Champion"
                    if current_lang == "EN"
                    else "### 🌍 اختر بطل كأس العالم"
                )

                st.caption(
                    "This pick locks when the first match of the tournament starts."
                    if current_lang == "EN"
                    else "يغلق هذا التوقع عند بداية أول مباراة في البطولة."
                )

                if tournament_started:
                    st.error(
                        "🔒 Champion pick is locked."
                        if current_lang == "EN"
                        else "🔒 تم إغلاق توقع البطل."
                    )
                else:
                    st.success(
                        "✅ Champion pick is still open."
                        if current_lang == "EN"
                        else "✅ توقع البطل ما زال مفتوحًا."
                    )

                if current_pick:
                    st.info(
                        f"🏆 Your current pick: **{tr_team(current_pick)}**"
                        if current_lang == "EN"
                        else f"🏆 اختيارك الحالي: **{tr_team(current_pick)}**"
                    )
                else:
                    st.warning(
                        "You have not picked a champion yet."
                        if current_lang == "EN"
                        else "لم تختر بطل البطولة بعد."
                    )

                if teams:
                    default_index = 0

                    if current_pick in teams:
                        default_index = teams.index(current_pick)

                    selected_champion = st.selectbox(
                        "Champion" if current_lang == "EN" else "البطل",
                        teams,
                        index=default_index,
                        format_func=tr_team
                    )

                    if not tournament_started:
                        if st.button(
                                "✅ Save Champion Pick"
                                if current_lang == "EN"
                                else "✅ حفظ توقع البطل",
                                use_container_width=True
                            ):
                                save_champion_prediction(
                                    st.session_state.username,
                                    selected_champion,
                                    tournament_started

                                )

                                st.success(
                                    "Champion pick saved successfully."
                                    if current_lang == "EN"
                                    else "تم حفظ توقع البطل بنجاح."
                                )

                                clear_all_cache()
                                st.rerun()
                    else:
                        st.info(
                            "You can no longer change your champion pick."
                            if current_lang == "EN"
                            else "لا يمكنك تعديل توقع البطل الآن."
                        )

                else:
                    st.warning(
                        "No teams found in MatchCache."
                        if current_lang == "EN"
                        else "لم يتم العثور على منتخبات في جدول المباريات."
                    )

        # =================================================
        # Tab 5: Group Ranking Predictions
        # =================================================
        elif page == lang_data["tab_group_rank"]:
            st.markdown(
                f"<h3 style='font-size:20px; font-weight:800;'>📋 {lang_data['group_rank_title']}</h3>",
                unsafe_allow_html=True
            )

            df_matches = load_sheet("MatchCache")
            df_group_ranks = load_sheet("GroupRankingPredictions")

            groups = get_groups_from_matches(df_matches)

            if not groups:
                st.warning("No groups available yet.")
            else:
                selected_group = st.selectbox(
                    lang_data["group_select"],
                    groups,
                    key="group_ranking_group_select"
                )

                teams = get_teams_in_group(df_matches, selected_group)
                locked = is_group_ranking_locked(df_matches, selected_group)
                
                with st.container(border=True):
                    st.markdown(
                        f"### 🧩 Group {selected_group}"
                        if current_lang == "EN"
                        else f"### 🧩 المجموعة {selected_group}"
                    )

                    st.caption(
                        "Group ranking locks when the first match in this group starts."
                        if current_lang == "EN"
                        else "يغلق توقع ترتيب المجموعة عند بداية أول مباراة في هذه المجموعة."
                    )
                    
                    if locked:
                        st.error(
                            "🔒 This group ranking is locked."
                            if current_lang == "EN"
                            else "🔒 تم إغلاق توقع ترتيب هذه المجموعة."
                        )
                    else:
                        st.success(
                            "✅ This group ranking is still open."
                            if current_lang == "EN"
                            else "✅ توقع ترتيب هذه المجموعة ما زال مفتوحًا."
                        )

                existing = get_existing_group_ranking_prediction(
                    df_group_ranks,
                    st.session_state.username,
                    selected_group
                )

                old_ranking = []

                if not existing.empty:
                    old_ranking = [
                        str(existing.iloc[0]["Pos1"]),
                        str(existing.iloc[0]["Pos2"]),
                        str(existing.iloc[0]["Pos3"]),
                        str(existing.iloc[0]["Pos4"])
                    ]

                #if locked:
                #   st.error(lang_data["group_rank_locked"])

                if len(teams) < 4:
                    st.warning("This group does not have 4 teams available yet.")
                else:
                    st.caption(
                        "Choose your rankings."
                        if current_lang == "EN"
                        else "اختر ترتيبك."
                    )

         # ترتيب قديم محفوظ إن وجد
                    default_pos1 = old_ranking[0] if len(old_ranking) == 4 and old_ranking[0] in teams else teams[0]

                    pos1_options = teams.copy()
                    pos1_index = pos1_options.index(default_pos1) if default_pos1 in pos1_options else 0
                    
                    pos1 = st.selectbox(
                        f"{lang_data['position']} 1",
                        pos1_options,
                        index=pos1_index,
                        disabled=locked,
                        key=f"group_{selected_group}_pos_1",
                        format_func=lambda team: tr_team(team)
                    )

                    pos2_options = [team for team in teams if team != pos1]
                    
                    default_pos2 = (
                        old_ranking[1]
                        if len(old_ranking) == 4 and old_ranking[1] in pos2_options
                        else pos2_options[0]
                    )

                    pos2_index = pos2_options.index(default_pos2) if default_pos2 in pos2_options else 0
                    
                    pos2 = st.selectbox(
                        f"{lang_data['position']} 2",
                        pos2_options,
                        index=pos2_index,
                        disabled=locked,
                        key=f"group_{selected_group}_pos_2",
                        format_func=lambda team: tr_team(team)
                    )

                    pos3_options = [team for team in teams if team not in [pos1, pos2]]
                    
                    default_pos3 = (
                        old_ranking[2]
                        if len(old_ranking) == 4 and old_ranking[2] in pos3_options
                        else pos3_options[0]
                    )
                    
                    pos3_index = pos3_options.index(default_pos3) if default_pos3 in pos3_options else 0
                    
                    pos3 = st.selectbox(
                        f"{lang_data['position']} 3",
                        pos3_options,
                        index=pos3_index,
                        disabled=locked,
                        key=f"group_{selected_group}_pos_3",
                        format_func=lambda team: tr_team(team)
                    )
                    
                    pos4_options = [team for team in teams if team not in [pos1, pos2, pos3]]
                    
                    default_pos4 = (
                        old_ranking[3]
                        if len(old_ranking) == 4 and old_ranking[3] in pos4_options
                        else pos4_options[0]
                    )
                    
                    pos4_index = pos4_options.index(default_pos4) if default_pos4 in pos4_options else 0
                    
                    pos4 = st.selectbox(
                        f"{lang_data['position']} 4",
                        pos4_options,
                        index=pos4_index,
                        disabled=locked,
                        key=f"group_{selected_group}_pos_4",
                        format_func=lambda team: tr_team(team)
                    )

                    ranking = [pos1, pos2, pos3, pos4]

                    st.write("---")

                    with st.container(border=True):
                        st.markdown(
                            "### 📋 Your Current Ranking"
                            if current_lang == "EN"
                            else "### 📋 ترتيبك الحالي"
                        )

                        ranking_preview = [
                            ("🥇", pos1),
                            ("🥈", pos2),
                            ("🥉", pos3),
                            ("🏅", pos4),
                        ]

                        for medal, team in ranking_preview:
                            flag_path = get_team_flag_path(team)
                            
                            row_cols = st.columns([0.8, 1, 5])
                            
                            with row_cols[0]:
                                st.markdown(
                                    f"<h3 style='margin-top:6px;'>{medal}</h3>",
                                    unsafe_allow_html=True
                                )

                            with row_cols[1]:
                                if flag_path:
                                    st.image(flag_path, width=46)
                                    
                            with row_cols[2]:
                                st.markdown(
                                    f"<h3 style='margin-top:6px; margin-bottom:0;'>{tr_team(team)}</h3>",
                                    unsafe_allow_html=True
                                )
        
                        st.caption(
                            "Ranking points are added only after the entire group stage is finished."
                            if current_lang == "EN"
                            else "نقاط ترتيب المجموعات تُضاف فقط بعد نهاية دور المجموعات بالكامل."
                        )
                    
    # حماية إضافية من تكرار نفس المنتخب
                    has_duplicates = len(set(ranking)) != 4

                    if has_duplicates:
                        st.warning(
                            "You selected the same team more than once."
                            if current_lang == "EN"
                            else "اخترت نفس المنتخب أكثر من مرة."
                        )

                    save_disabled = locked or has_duplicates

                    if st.button(
                            f"✅ {lang_data['save']}",
                            key=f"save_group_ranking_{selected_group}",
                            use_container_width=True,
                            disabled=save_disabled
                    ):
                            save_group_ranking_prediction(
                                st.session_state.username,
                                selected_group,
                                ranking,
                                locked
                            )

                            st.success(
                                "Group ranking saved successfully."
                                if current_lang == "EN"
                                else "تم حفظ ترتيب المجموعة بنجاح."
                            )

                            clear_all_cache()
                            st.rerun()

        # =================================================
        # Tab 6: Banter Room
        # =================================================
        elif page == lang_data["tab_chat"]:
            st.markdown(
                "## 💬 Banter Room"
                if current_lang == "EN"
                else "## 💬 غرفة التحدي"
            )

            # تحديث تلقائي خفيف. 10 ثواني أفضل من 5 حتى لا يزيد الضغط على Google Sheets.
            st_autorefresh(
                interval=10000,
                key="banter_room_auto_refresh"
            )

            st.caption(
                "Friendly football talk only. Keep it fun and respectful."
                if current_lang == "EN"
                else "مزح وتحديات كروية فقط. خليه ممتع ومحترم."
            )

            # ===============================
            # Send Message Box
            # ===============================
            with st.container(border=True):
                st.markdown(
                    "### ✍️ Send a message"
                    if current_lang == "EN"
                    else "### ✍️ اكتب رسالة"
                )

                # استخدمنا form + text_input بدل text_area
                # حتى يكون مريح أكثر على الهاتف ولا يظهر تنبيه Ctrl/Enter.
                with st.form(
                    key="banter_send_form",
                    clear_on_submit=True,
                    border=False
                ):
                    msg = st.text_input(
                        "Message" if current_lang == "EN" else "الرسالة",
                        placeholder=(
                            "Write your challenge here."
                            if current_lang == "EN"
                            else "اكتب تحديك هون."
                        ),
                        max_chars=180,
                        key="banter_message_input"
                    )

                    submitted = st.form_submit_button(
                        "🚀 Send" if current_lang == "EN" else "🚀 إرسال",
                        use_container_width=True
                    )

                if submitted:
                    clean_msg = str(msg).strip()

                    if not clean_msg:
                        st.warning(
                            "Message cannot be empty."
                            if current_lang == "EN"
                            else "لا يمكن إرسال رسالة فارغة."
                        )
                    else:
                        ok = save_banter_message(
                            st.session_state.username,
                            clean_msg
                        )

                        if ok:
                            st.success(
                                "Message sent."
                                if current_lang == "EN"
                                else "تم إرسال الرسالة."
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Could not send message."
                                if current_lang == "EN"
                                else "تعذر إرسال الرسالة."
                            )

            st.write("---")

            # ===============================
            # Messages Feed
            # ===============================
            df_chat = load_banter_messages()

            if df_chat.empty:
                st.info(
                    "No messages yet."
                    if current_lang == "EN"
                    else "لا توجد رسائل بعد."
                )
            else:
                df_chat = df_chat.tail(30).iloc[::-1]

                st.markdown(
                    "### 🔥 Latest Messages"
                    if current_lang == "EN"
                    else "### 🔥 آخر الرسائل"
                )

                for _, row in df_chat.iterrows():
                    username = str(row.get("Username", "Unknown")).strip()
                    message = str(row.get("Message", "")).strip()
                    timestamp = str(row.get("Timestamp", "")).strip()

                    avatar_path = get_avatar_for_username(username)

                    with st.container(border=True):
                        msg_cols = st.columns([1, 6])

                        with msg_cols[0]:
                            if avatar_path:
                                st.markdown(
                                    avatar_html(avatar_path, 64),
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown("👤")

                        with msg_cols[1]:
                            st.markdown(f"### {username}")
                            st.write(message)
                            st.caption(f"🕒 {timestamp}")

        # =================================================
        # Tab 7: Settings
        # =================================================
        elif page == lang_data["tab_settings"]:
            st.markdown(f"## ⚙️ {lang_data['tab_settings']}")

            # ===============================
            # Player Area
            # ===============================
            with st.container(border=True):
                st.markdown(
                    "### 👤 Player Area"
                    if current_lang == "EN"
                    else "### 👤 منطقة اللاعب"
                )

                st.caption(
                    "Manage your session and account access."
                    if current_lang == "EN"
                    else "إدارة الجلسة والخروج من الحساب."
                )

                st.info(
                    f"{'Logged in as' if current_lang == 'EN' else 'مسجل الدخول باسم'}: **{st.session_state.username}**"
                )
                
               
                #====================================    
                #============اللغة===================                
                #====================================
                
                
                st.write("---")

                st.markdown(
                    "### 🌐 Language"
                    if current_lang == "EN"
                    else "### 🌐 اللغة"
                )

                lang_choice = st.selectbox(
                    "Choose language" if current_lang == "EN" else "اختر اللغة",
                    ["EN", "AR"],
                    index=0 if current_lang == "EN" else 1,
                    key="settings_language_select"
                )

                if lang_choice != current_lang:
                    st.session_state.lang = lang_choice
                    
                    if st.session_state.get("is_logged_in", False):
                        save_user_language(st.session_state.username, lang_choice)
                        
                    st.rerun()
                    
                
                    #avatars
                st.write("---")

                st.markdown(
                    "### 🧑‍🚀 Avatar"
                    if current_lang == "EN"
                    else "### 🧑‍🚀 الأفاتار"
                )

                current_avatar = get_user_avatar(st.session_state.username)
                current_avatar_path = get_avatar_path(current_avatar)

                with st.container(border=True):
                    st.caption(
                        "Choose how you appear in the leaderboard, chat, and prediction reveal."
                        if current_lang == "EN"
                        else "اختر الشكل الذي سيظهر بجانب اسمك في الترتيب والشات وكشف التوقعات."
                    )

                    if current_avatar_path:
                        st.markdown(
                            avatar_html(current_avatar_path, size=95),
                            unsafe_allow_html=True
                        )

                    avatar_keys = list(AVATARS.keys())

                    avatar_labels = [
                        AVATARS[key]["label_en"] if current_lang == "EN" else AVATARS[key]["label_ar"]
                        for key in avatar_keys
                    ]

                    current_index = avatar_keys.index(current_avatar) if current_avatar in avatar_keys else 0

                    selected_label = st.selectbox(
                        "Choose Avatar" if current_lang == "EN" else "اختر الأفاتار",
                        avatar_labels,
                        index=current_index,
                        key="avatar_selectbox"
                    )

                    selected_avatar_key = avatar_keys[avatar_labels.index(selected_label)]

                    selected_avatar_path = get_avatar_path(selected_avatar_key)

                    if selected_avatar_path:
                        st.markdown(
                            avatar_html(selected_avatar_path, size=135),
                            unsafe_allow_html=True
                        )

                    if st.button(
                            "✅ Save Avatar" if current_lang == "EN" else "✅ حفظ الأفاتار",
                            use_container_width=True,
                            key="save_avatar_btn"
                    ):
                        ok, msg = save_user_avatar(
                            st.session_state.username,
                            selected_avatar_key
                        )   

                        if ok:
                            st.success(
                                "Avatar saved successfully."
                                if current_lang == "EN"
                                else "تم حفظ الأفاتار بنجاح."
                            )
                            clear_all_cache()
                            st.rerun()
                        else:
                            st.error(
                                f"Could not save avatar. Reason: {msg}"
                                if current_lang == "EN"
                                else f"تعذر حفظ الأفاتار. السبب: {msg}"
                            )
                
                
                    
                #====================================    
                #==========تغيير كلمة السر==========                
                #====================================
                
                st.write("---")

                with st.expander(
                        "🔐 Change Password"
                        if current_lang == "EN"
                        else "🔐 تغيير كلمة السر",
                        expanded=False
                ):
                        current_pass = st.text_input(
                            "Current password" if current_lang == "EN" else "كلمة السر الحالية",
                            type="password",
                            key="current_password_input"
                        )

                        new_pass = st.text_input(
                            "New password" if current_lang == "EN" else "كلمة السر الجديدة",
                            type="password",
                            key="new_password_input"
                        )

                        confirm_new_pass = st.text_input(
                            "Confirm new password" if current_lang == "EN" else "تأكيد كلمة السر الجديدة",
                            type="password",
                            key="confirm_new_password_input"
                        )

                        if st.button(
                                "✅ Update Password" if current_lang == "EN" else "✅ تحديث كلمة السر",
                                use_container_width=True,
                                key="update_password_btn"
                        ):
                                if not current_pass or not new_pass or not confirm_new_pass:
                                    st.warning(
                                        "Please fill all password fields."
                                        if current_lang == "EN"
                                        else "يرجى تعبئة جميع خانات كلمة السر."
                                    )

                                elif new_pass != confirm_new_pass:
                                    st.error(
                                        "New password and confirmation do not match."
                                        if current_lang == "EN"
                                        else "كلمة السر الجديدة وتأكيدها غير متطابقين."
                                    )

                                else:
                                    ok, msg = change_user_password(
                                        st.session_state.username,
                                        current_pass,
                                        new_pass
                                    )

                                    if ok:
                                        st.success(
                                            "Password updated successfully."
                                            if current_lang == "EN"
                                            else "تم تحديث كلمة السر بنجاح."
                                        )

                                    elif msg == "wrong_password":
                                        st.error(
                                            "Current password is incorrect."
                                            if current_lang == "EN"
                                            else "كلمة السر الحالية غير صحيحة."
                                        )

                                    elif msg == "short_password":
                                        st.error(
                                            "New password must be at least 4 characters."
                                            if current_lang == "EN"
                                            else "كلمة السر الجديدة يجب أن تكون 4 أحرف على الأقل."
                                        )

                                    else:
                                        st.error(
                                            "Could not update password."
                                            if current_lang == "EN"
                                            else "تعذر تحديث كلمة السر."
                                        )
                 
                st.write("---")
                
                with st.expander(
                        "Delete account"
                        if current_lang == "EN"
                        else "حذف الحساب",
                        expanded=False
                ):
                        st.warning(
                            "This action is permanent. Your account and predictions will be deleted."
                            if current_lang == "EN"
                            else "هذا الإجراء نهائي. سيتم حذف حسابك وتوقعاتك بالكامل."
                        )

                        delete_password = st.text_input(
                            "Current password"
                            if current_lang == "EN"
                            else "كلمة السر الحالية",
                            type="password",
                            key="delete_account_password"
                        )
                        
                        delete_confirm = st.text_input(
                            "Type DELETE to confirm"
                            if current_lang == "EN"
                            else "اكتب حذف للتأكيد",
                            key="delete_account_confirm"
                        )

                        confirm_word = "DELETE" if current_lang == "EN" else "حذف"
                        
                        if st.button(
                                "Delete my account"
                                if current_lang == "EN"
                                else "حذف حسابي",
                                type="primary",
                                use_container_width=True,
                                key="delete_account_btn"
                        ):
                                if not delete_password or not delete_confirm:
                                    st.error(
                                        "Please fill all fields."
                                        if current_lang == "EN"
                                        else "يرجى تعبئة جميع الخانات."
                                    )

                                elif delete_confirm.strip() != confirm_word:
                                    st.error(
                                        f"Please type {confirm_word} exactly."
                                        if current_lang == "EN"
                                        else "يرجى كتابة كلمة حذف بالضبط."
                                    )

                                else:
                                    ok, msg = delete_user_account(
                                        st.session_state.username,
                                        delete_password
                                    )

                                if ok:
                                    st.session_state.is_logged_in = False
                                    st.session_state.username = ""
                                    
                                    cookie_manager.delete(
                                        COOKIE_NAME,
                                        key="delete_login_cookie_after_account_delete"
                                    )
                                    if "cookie_checked_once" in st.session_state:
                                        del st.session_state.cookie_checked_once
                                            
                                    if "auto_sync_checked" in st.session_state:
                                        del st.session_state.auto_sync_checked

                                    clear_all_cache()
                                    
                                    st.success(
                                        "Your account has been deleted."
                                        if current_lang == "EN"
                                        else "تم حذف حسابك بنجاح."
                                    )

                                    st.rerun()

                                elif msg == "wrong_password":
                                    st.error(
                                        "Wrong password."
                                        if current_lang == "EN"
                                        else "كلمة السر غير صحيحة."
                                    )

                                else:
                                    st.error(
                                        f"Could not delete account. Reason: {msg}"
                                        if current_lang == "EN"
                                        else f"تعذر حذف الحساب. السبب: {msg}"
                                    )
                    
                    
                    
                #====================================    
                #==========تسجيل الخروج===================                
                #====================================

                if st.button(
                        lang_data["logout_btn"],
                        type="primary",
                        use_container_width=True
                ):
                    st.session_state.is_logged_in = False
                    st.session_state.username = ""
                    
                    cookie_manager.delete(
                        COOKIE_NAME,
                        key="delete_login_cookie"
                    )
                    
                    if "auto_sync_checked" in st.session_state:
                        del st.session_state.auto_sync_checked
                        
                    st.rerun()

        # =================================================
        # Tab 8: Admin Dashboard
        # =================================================
        elif page == lang_data["tab_admin"]:
            if not is_admin_user(st.session_state.username):
                st.error(
                    "Access denied."
                    if current_lang == "EN"
                    else "غير مصرح لك بالدخول."
                )

            else:
                st.markdown(
                    "## 🔐 Admin Dashboard"
                    if current_lang == "EN"
                    else "## 🔐 لوحة تحكم الأدمن"
                )

                st.caption(
                    "Tournament control tools. Use carefully."
                    if current_lang == "EN"
                    else "أدوات التحكم بالبطولة. استخدمها بحذر."
                )

                with st.container(border=True):
                    st.markdown(
                        "### 🔄 Data Sync"
                        if current_lang == "EN"
                        else "### 🔄 مزامنة البيانات"
                    )

                    if st.button(
                        f"🔄 {lang_data['api_sync']}",
                        use_container_width=True
                    ):
                        sync_matchcache_from_api()
                        sync_group_standings_from_api()
                        recalculate_all_scores()
                        clear_all_cache()

                        st.success(lang_data["api_done"])
                        st.rerun()

                with st.container(border=True):
                    st.markdown(
                        "### 🧮 Scoring"
                        if current_lang == "EN"
                        else "### 🧮 احتساب النقاط"
                    )

                    if st.button(
                        f"🧮 {lang_data['recalc']}",
                        use_container_width=True
                    ):
                        recalculate_all_scores()
                        clear_all_cache()

                        st.success(lang_data["recalc_done"])
                        st.rerun()

                with st.container(border=True):
                    st.markdown(
                        "### 🧹 Maintenance"
                        if current_lang == "EN"
                        else "### 🧹 الصيانة"
                    )

                    if st.button(
                        "🧹 Clear Cache"
                        if current_lang == "EN"
                        else "🧹 تنظيف الكاش",
                        use_container_width=True
                    ):
                        clear_all_cache()

                        st.success(
                            "Cache cleared successfully."
                            if current_lang == "EN"
                            else "تم تنظيف الكاش بنجاح."
                        )

                        st.rerun()

        render_footer()

except Exception:
    st.error("System pipeline sync breakdown. Diagnostic trace attached below.")
    st.code(traceback.format_exc())
