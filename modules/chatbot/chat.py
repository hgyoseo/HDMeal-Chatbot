# ██╗  ██╗██████╗ ███╗   ███╗███████╗ █████╗ ██╗
# ██║  ██║██╔══██╗████╗ ████║██╔════╝██╔══██╗██║
# ███████║██║  ██║██╔████╔██║█████╗  ███████║██║
# ██╔══██║██║  ██║██║╚██╔╝██║██╔══╝  ██╔══██║██║
# ██║  ██║██████╔╝██║ ╚═╝ ██║███████╗██║  ██║███████╗
# ╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝
# Copyright 2019-2020, Hyungyo Seo
# chat.py - Skill 응답 데이터를 만드는 스크립트입니다.

import datetime
import hashlib
import os
import time
from itertools import groupby
from threading import Thread

from modules.chatbot import user
from modules.common import security, log, get_data


# Skill 응답용 JSON 생성
def skill(msg):
    return {"version": "2.0", "data": {"msg": msg}}


def skill_simpletext(msg):
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": msg}}]}}


# 요일 처리
def wday(date):
    if date.weekday() == 0:
        return "월"
    elif date.weekday() == 1:
        return "화"
    elif date.weekday() == 2:
        return "수"
    elif date.weekday() == 3:
        return "목"
    elif date.weekday() == 4:
        return "금"
    elif date.weekday() == 5:
        return "토"
    else:
        return "일"


# 알러지정보
allergy_string = [
    "",
    "난류",
    "우유",
    "메밀",
    "땅콩",
    "대두",
    "밀",
    "고등어",
    "게",
    "새우",
    "돼지고기",
    "복숭아",
    "토마토",
    "아황산류",
    "호두",
    "닭고기",
    "쇠고기",
    "오징어",
    "조개류",
]


def getuserid(uid):
    enc = hashlib.sha256()
    enc.update(uid.encode("utf-8"))
    return "KT-" + enc.hexdigest()


def router(
    platform: str, uid: str, intent: str, params: dict, req_id: str, debugging: bool
):
    try:
        if "Briefing" in intent:
            return briefing(uid, req_id, debugging)
        elif "Meal" in intent:
            return meal(uid, params, req_id, debugging)
        elif "Timetable" in intent:
            return timetable(platform, uid, params, req_id, debugging)
        elif "Schedule" in intent:
            return schdl(params, req_id, debugging)
        elif "WaterTemperature" in intent:
            return [get_data.wtemp(req_id, debugging)], None
        elif "UserSettings" in intent:
            return user_settings(uid, req_id)
        elif "ModifyUserInfo" in intent:
            return modify_user_info(params, uid, req_id, debugging)
        else:
            return ["잘못된 요청입니다.\n요청 ID: " + req_id], None
    except OSError as e:
        log.err("[#%s] router@chat.py: Uncaught Error %s" % (req_id, e))
        return ["알 수 없는 오류가 발생했습니다.\n요청 ID: " + req_id], None


# 식단조회
def meal(uid: str, params: dict, req_id: str, debugging: bool):
    try:
        if not params["date"]:
            return ["언제의 급식을 조회하시겠어요?"], None
        if isinstance(params["date"], datetime.datetime):
            date: datetime = params["date"]
            if date.weekday() >= 5:  # 주말
                return ["급식을 실시하지 않습니다. (주말)"], None
            meal = get_data.meal(date.year, date.month, date.day, req_id, debugging)
            if "message" not in meal:  # 파서 메시지 있는지 확인, 없으면 만들어서 응답
                # 사용자 설정 불러오기
                user_preferences = user.get_user(uid, req_id, debugging)[2]
                if user_preferences.get("AllergyInfo") == "None":
                    menus = [i[0] for i in meal["menu"]]
                elif user_preferences.get("AllergyInfo") == "FullText":
                    menus = []
                    for i in meal["menu"]:
                        if i[1]:
                            menus.append(
                                "%s(%s)"
                                % (i[0], ", ".join(allergy_string[x] for x in i[1]))
                            )
                        else:
                            menus.append(i[0])
                else:
                    menus = []
                    for i in meal["menu"]:
                        if i[1]:
                            menus.append(
                                "%s(%s)" % (i[0], ", ".join(str(x) for x in i[1]))
                            )
                        else:
                            menus.append(i[0])
                return [
                    "%s:\n%s\n\n열량: %s kcal"
                    % (meal["date"], "\n".join(menus), meal["kcal"])
                ], None
            if meal["message"] == "등록된 데이터가 없습니다.":
                cal = get_data.schdl(date.year, date.month, date.day, req_id, debugging)
                if not cal == "일정이 없습니다.":
                    return ["급식을 실시하지 않습니다. (%s)" % cal], None
            return [meal["message"]], None
        else:
            return ["정확한 날짜를 입력해주세요.\n현재 식단조회에서는 여러날짜 조회를 지원하지 않습니다."], None
    except ConnectionError:
        return ["급식 서버에 연결하지 못했습니다.\n요청 ID: " + req_id], None


# 시간표 조회
def timetable(platform: str, uid: str, params: dict, req_id: str, debugging: bool):
    suggest_to_register = False
    try:
        log.info("[#%s] tt_registered@chat.py: New Request" % req_id)
        print(params)
        if (
            "grade" in params
            and "class" in params
            and params["grade"]
            and params["class"]
        ):
            try:
                tt_grade = int(params["grade"])
                tt_class = int(params["class"])
            except ValueError:
                return ["올바른 숫자를 입력해 주세요."], None
            if platform == "KT":
                suggest_to_register = True
        else:
            user_data = user.get_user(uid, req_id, debugging)  # 사용자 정보 불러오기
            tt_grade = user_data[0]
            tt_class = user_data[1]
            if not tt_grade or not tt_class:
                if platform == "KT":
                    return [
                        {
                            "type": "card",
                            "title": "사용자 정보를 찾을 수 없습니다.",
                            "body": '"내 정보 관리"를 눌러 학년/반 정보를 등록 하시거나, '
                            '"1학년 1반 시간표 알려줘"와 같이 조회할 학년/반을 직접 언급해 주세요.',
                            "buttons": [{"type": "message", "title": "내 정보 관리"}],
                        }
                    ], None
                else:
                    return ['사용자 정보를 찾을 수 없습니다. "내 정보 관리"를 눌러 학년/반 정보를 등록해 주세요.'], None
        if not params["date"]:
            return ["언제의 시간표를 조회하시겠어요?"], None
        if isinstance(params["date"], datetime.datetime):
            date: datetime = params["date"]
            if suggest_to_register:
                return [
                    get_data.tt(tt_grade, tt_class, date, req_id, debugging),
                    {
                        "type": "card",
                        "title": "방금 입력하신 정보를 저장할까요?",
                        "body": "학년/반 정보를 등록하시면 다음부터 더 빠르고 편하게 이용하실 수 있습니다.",
                        "buttons": [
                            {
                                "type": "message",
                                "title": "네, 저장해 주세요.",
                                "postback": "사용자 정보 등록: %d학년 %d반"
                                % (tt_grade, tt_class),
                            }
                        ],
                    },
                ], None
            else:
                return [get_data.tt(tt_grade, tt_class, date, req_id, debugging)], None
        else:
            return ["정확한 날짜를 입력해주세요.\n현재 시간표조회에서는 여러날짜 조회를 지원하지 않습니다."], None
    except ConnectionError:
        return ["시간표 서버에 연결하지 못했습니다.\n요청 ID: " + req_id], None


# 학사일정 조회
def schdl(params: dict, req_id: str, debugging: bool):
    global msg
    try:
        log.info("[#%s] cal@chat.py: New Request" % req_id)
        if "date" in params:
            if not params["date"]:
                return ["언제의 학사일정을 조회하시겠어요?"], None
            # 특정일자 조회
            if isinstance(params["date"], datetime.datetime):
                try:
                    date: datetime = params["date"]
                except Exception:
                    log.err("[#%s] cal@chat.py: Error while Parsing Date" % req_id)
                    return ["오류가 발생했습니다.\n요청 ID: " + req_id], None

                prsnt_schdl = get_data.schdl(
                    date.year, date.month, date.day, req_id, debugging
                )

                prsnt_schdl = prsnt_schdl
                if prsnt_schdl:
                    msg = "%s-%s-%s(%s):\n%s" % (
                        str(date.year).zfill(4),
                        str(date.month).zfill(2),
                        str(date.day).zfill(2),
                        wday(date),
                        prsnt_schdl,
                    )  # YYYY-MM-DD(Weekday)
                else:
                    msg = "일정이 없습니다."
            # 특정일자 조회 끝
            # 기간 조회
            elif isinstance(params["date"], list):  # 기간
                body = str()
                try:
                    start: datetime = params["date"][0]  # 시작일 파싱
                except Exception:
                    log.err("[#%s] cal@chat.py: Error while Parsing StartDate" % req_id)
                    return ["오류가 발생했습니다.\n요청 ID: " + req_id], None
                try:
                    end: datetime = params["date"][1]  # 종료일 파싱
                except Exception:
                    log.err("[#%s] cal@chat.py: Error while Parsing EndDate" % req_id)
                    return ["오류가 발생했습니다.\n요청 ID: " + req_id], None

                if (end - start).days > 90:  # 90일 이상을 조회요청한 경우,
                    head = (
                        "서버 성능상의 이유로 최대 90일까지만 조회가 가능합니다."
                        "\n조회기간이 %s부터 %s까지로 제한되었습니다.\n\n"
                        % (start.date(), (start + datetime.timedelta(days=90)).date())
                    )
                    end = start + datetime.timedelta(days=90)  # 종료일 앞당김
                else:
                    head = "%s부터 %s까지 조회합니다.\n\n" % (start.date(), end.date())

                schdls = get_data.schdl_mass(start, end, req_id, debugging)
                # 년, 월, 일, 일정 정보를 담은 튜플이 리스트로 묶여서 반환됨

                # body 쓰기, 연속되는 일정은 묶어 처리함
                for content, group in groupby(schdls, lambda k: k[3]):
                    lst = [*group]
                    if lst[0] != lst[-1]:
                        start_date = datetime.date(*lst[0][:3])
                        end_date = datetime.date(*lst[-1][:3])
                        body = "%s%s(%s)~%s(%s):\n%s\n" % (
                            body,
                            start_date,
                            wday(start_date),
                            end_date,
                            wday(end_date),
                            content,
                        )
                    else:
                        date = datetime.date(*lst[0][:3])
                        body = "%s%s(%s):\n%s\n" % (body, date, wday(date), content)

                if not body:
                    body = "일정이 없습니다.\n"
                msg = (head + body)[:-1]  # 맨 끝의 줄바꿈을 제거함
                # 기간 조회 끝

        else:  # 아무런 파라미터도 넘겨받지 못한 경우
            log.info("[#%s] cal@chat.py: No Parameter" % req_id)
            return ["언제의 학사일정을 조회하시겠어요?"], None

        return [msg], None
    except ConnectionError:
        return ["학사일정 서버에 연결하지 못했습니다.\n요청 ID: " + req_id], None


# 급식봇 브리핑
def briefing(uid: str, req_id: str, debugging: bool):
    log.info("[#%s] briefing@chat.py: New Request" % req_id)
    global briefing_header, hd_err, briefing_schdl, briefing_weather, briefing_meal, briefing_meal_ga, briefing_tt
    briefing_header = "알 수 없는 오류로 헤더를 불러올 수 없었습니다.\n나중에 다시 시도해 보세요."
    briefing_schdl = "알 수 없는 오류로 학사일정을 불러올 수 없었습니다.\n나중에 다시 시도해 보세요."
    briefing_weather = "알 수 없는 오류로 날씨를 불러올 수 없었습니다.\n나중에 다시 시도해 보세요."
    briefing_meal = "알 수 없는 오류로 식단을 불러올 수 없었습니다.\n나중에 다시 시도해 보세요."
    briefing_meal_ga = "알 수 없는 오류로 식단을 불러올 수 없었습니다.\n나중에 다시 시도해 보세요."
    briefing_tt = "알 수 없는 오류로 시간표를 불러올 수 없었습니다.\n나중에 다시 시도해 보세요."

    if datetime.datetime.now().time() >= datetime.time(17):  # 오후 5시 이후이면
        # 내일을 기준일로 설정
        date = datetime.datetime.now() + datetime.timedelta(days=1)
        date_ko = "내일"
    else:  # 9시 이전이면
        # 오늘을 기준일로 설정
        date = datetime.datetime.now()
        date_ko = "오늘"

    log.info("[#%s] briefing@chat.py: Date: %s" % (req_id, date))

    def logging_time(original_fn):
        def wrapper_fn(*args, **kwargs):
            result = original_fn(*args, **kwargs)
            if debugging:
                start_time = time.time()
                print("{} 실행.".format(original_fn.__name__))
                end_time = time.time()
                print(
                    "{} 종료. 실행시간: {} 초".format(
                        original_fn.__name__, end_time - start_time
                    )
                )
            return result

        return wrapper_fn

    # 첫 번째 말풍선
    # 헤더
    @logging_time
    def f_header():
        global briefing_header, hd_err
        if date.weekday() >= 5:  # 주말이면
            log.info("[#%s] briefing@chat.py: Weekend" % req_id)
            hd_err = "%s은 주말 입니다." % date_ko
        else:
            briefing_header = "%s은 %s(%s) 입니다." % (
                date_ko,
                date.date().isoformat(),
                wday(date),
            )
            hd_err = None

    # 학사일정
    @logging_time
    def f_cal():
        global briefing_schdl
        try:
            briefing_schdl = get_data.schdl(
                date.year, date.month, date.day, req_id, debugging
            )
            if not briefing_schdl:
                log.info("[#%s] briefing@chat.py: No Schedule" % req_id)
                briefing_schdl = "%s은 학사일정이 없습니다." % date_ko
            else:
                briefing_schdl = "%s 학사일정:\n%s" % (date_ko, briefing_schdl)
        except ConnectionError:
            briefing_schdl = "학사일정 서버에 연결하지 못했습니다.\n나중에 다시 시도해 보세요."

    # 두 번째 말풍선
    # 날씨
    @logging_time
    def f_weather():
        global briefing_weather
        try:
            briefing_weather = get_data.weather(date_ko, req_id, debugging)
        except ConnectionError:
            briefing_weather = "날씨 서버에 연결하지 못했습니다.\n나중에 다시 시도해 보세요."

    # 세 번째 말풍선
    # 급식
    @logging_time
    def f_meal():
        global briefing_meal, briefing_meal_ga
        try:
            meal = get_data.meal(date.year, date.month, date.day, req_id, debugging)
            if not "message" in meal:  # 파서 메시지 있는지 확인, 없으면 만들어서 응답
                briefing_meal_ga = "%s 급식은 %s 입니다." % (
                    date_ko,
                    ", ".join(i[0] for i in meal["menu"]).replace("⭐", ""),
                )
                briefing_meal = "%s 급식:\n%s" % (
                    date_ko,
                    "\n".join(i[0] for i in meal["menu"]),
                )
            elif meal["message"] == "등록된 데이터가 없습니다.":
                log.info("[#%s] briefing@chat.py: No Meal" % req_id)
                briefing_meal_ga = date_ko + "은 급식을 실시하지 않습니다."
                briefing_meal = date_ko + "은 급식을 실시하지 않습니다."
        except ConnectionError:
            briefing_meal_ga = "급식 서버에 연결하지 못했습니다.\n나중에 다시 시도해 보세요."
            briefing_meal = "급식 서버에 연결하지 못했습니다.\n나중에 다시 시도해 보세요."

    # 시간표
    @logging_time
    def f_tt():
        global briefing_tt
        try:
            user_data = user.get_user(uid, req_id, debugging)  # 사용자 정보 불러오기
            tt_grade = user_data[0]
            tt_class = user_data[1]

            if tt_grade is not None or tt_class is not None:  # 사용자 정보 있을 때
                tt = get_data.tt(tt_grade, tt_class, date, req_id, debugging)
                if tt == "등록된 데이터가 없습니다.":
                    briefing_tt = "등록된 시간표가 없습니다."
                else:
                    briefing_tt = "%s 시간표:\n%s" % (
                        date_ko,
                        tt.split("):\n")[1],
                    )  # 헤더부분 제거
            else:
                log.info("[#%s] briefing@chat.py: Non-Registered User" % req_id)
                briefing_tt = "등록된 사용자만 시간표를 볼 수 있습니다."
        except ConnectionError:
            briefing_tt = "시간표 서버에 연결하지 못했습니다.\n나중에 다시 시도해 보세요."
        except Exception as e:
            log.err(
                "[#%s] briefing@chat.py: Failed to Fetch Timetable because %s"
                % (req_id, e)
            )

    # 쓰레드 정의
    th_header = Thread(target=f_header)
    th_cal = Thread(target=f_cal)
    th_weather = Thread(target=f_weather)
    th_meal = Thread(target=f_meal)
    th_tt = Thread(target=f_tt)
    # 쓰레드 실행
    th_header.start()
    th_cal.start()
    th_weather.start()
    th_meal.start()
    th_tt.start()
    # 전 쓰레드 종료 시까지 기다리기
    th_header.join()
    if hd_err:
        return [hd_err], None, "안녕하세요, 흥덕고 급식입니다.\n" + hd_err
    th_cal.join()
    th_weather.join()
    th_meal.join()
    th_tt.join()

    # 구글어시스턴트 응답
    ga_respns = "안녕하세요, 흥덕고 급식입니다.\n" + briefing_meal_ga

    # 응답 만들기
    return (
        [
            "%s\n\n%s" % (briefing_header, briefing_schdl),
            briefing_weather,
            "%s\n\n%s" % (briefing_meal, briefing_tt),
        ],
        None,
        ga_respns,
    )


def user_settings(uid: str, req_id: str):
    url = os.environ.get("HDMeal_BaseURL")
    return [
        {
            "type": "card",
            "title": "내 정보 관리",
            "body": "아래 버튼을 클릭해 관리 페이지로 접속해 주세요.\n" "링크는 10분 뒤 만료됩니다.",
            "buttons": [
                {
                    "type": "web",
                    "title": "내 정보 관리",
                    "url": url
                    + "?token="
                    + security.generate_token(
                        "UserSettings",
                        uid,
                        [
                            "GetUserInfo",
                            "ManageUserInfo",
                            "GetUsageData",
                            "DeleteUsageData",
                        ],
                        req_id,
                    ),
                }
            ],
        }
    ], None


def modify_user_info(params: dict, uid: str, req_id: str, debugging: bool):
    try:
        user.manage_user(
            uid, int(params["grade"]), int(params["class"]), {}, req_id, debugging
        )
    except KeyError:
        return ["변경할 학년/반 정보를 입력해 주세요."], None
    except ValueError:
        return ["올바른 숫자를 입력해 주세요."], None
    return ["저장되었습니다."], None


# 디버그
if __name__ == "__main__":
    log.init()
