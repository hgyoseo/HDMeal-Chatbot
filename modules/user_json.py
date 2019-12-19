# ██╗  ██╗██████╗ ███╗   ███╗███████╗ █████╗ ██╗
# ██║  ██║██╔══██╗████╗ ████║██╔════╝██╔══██╗██║
# ███████║██║  ██║██╔████╔██║█████╗  ███████║██║
# ██╔══██║██║  ██║██║╚██╔╝██║██╔══╝  ██╔══██║██║
# ██║  ██║██████╔╝██║ ╚═╝ ██║███████╗██║  ██║███████╗
# ╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝
# Copyright 2019, Hyungyo Seo
# modules/user_json.py - 사용자 관리 및 인증을 담당하는 스크립트입니다.

import hashlib
import json
from modules import log

path = "data/user/user.json"
admin_path = "data/user/admin.json"


# 사용자 정보 읽기
def get_user(uid, req_id, debugging):
    log.info("[#%s] get_user@modules/user_json.py: Started Fetching User Info" % req_id)
    try:
        with open(path, encoding="utf-8") as data_file:
            return_data = list()
            enc = hashlib.sha256()
            enc.update(uid.encode("utf-8"))
            enc_uid = enc.hexdigest()
            data = json.load(data_file)
        if debugging:
            print(data)
        if not enc_uid in data:  # 사용자 정보 없을 때
            return_data.append(None)
            return_data.append(None)
            log.info("[#%s] get_user@modules/user_json.py: No User Info" % req_id)
            return return_data
        if debugging:
            print(data[enc_uid])
        if data[enc_uid][0] != "" or data[enc_uid][1] != "":  # 사용자 정보 있을 때
            return_data.append(data[enc_uid][0])
            return_data.append(data[enc_uid][1])
            log.info("[#%s] get_user@modules/user_json.py: Succeeded" % req_id)
        else:  # 사용자 정보 없을 때
            return_data.append(None)
            return_data.append(None)
            log.info("[#%s] get_user@modules/user_json.py: No User Info" % req_id)
        return return_data
    except Exception:
        return Exception


# 사용자 생성 및 수정
def manage_user(uid, user_grade, user_class, req_id, debugging):
    log.info("[#%s] manage_user@modules/user_json.py: Started Managing User Info" % req_id)
    try:
        with open(path, encoding="utf-8") as data_file:
            enc = hashlib.sha256()
            enc.update(uid.encode("utf-8"))
            enc_uid = enc.hexdigest()
            data = json.load(data_file)
        if debugging:
            print(data)
        if enc_uid in data:  # 사용자 정보 있을 때
            if data[enc_uid][0] == user_grade and data[enc_uid][1] == user_class:  # 사용자 정보 똑같을 때
                log.info("[#%s] manage_user@modules/user_json.py: Same" % req_id)
                return "Same"
            else:  # 사용자 정보 있고 같지도 않을 때 - 업데이트 (삭제 후 재생성)
                del data[enc_uid]
                if debugging:
                    print("DEL USER")
                log.info("[#%s] manage_user@modules/user_json.py: Updated" % req_id)
                return_msg = "Updated"
        else:  # 사용자 정보 없을 때 - 생성
            log.info("[#%s] manage_user@modules/user_json.py: Registered" % req_id)
            return_msg = "Registered"
        user_data = list()
        user_data.append(user_grade)
        user_data.append(user_class)
        data[enc_uid] = user_data
        with open(path, "w", encoding="utf-8") as write_file:
            json.dump(data, write_file, ensure_ascii=False, indent="\t")
            log.info("[#%s] manage_user@modules/user_json.py: Succeeded" % req_id)
            return return_msg
    except Exception:
        log.err("[#%s] manage_user@modules/user_json.py: Failed" % req_id)
        return Exception


# 사용자 삭제
def delete_user(uid, req_id, debugging):
    log.info("[#%s] delete_user@modules/user_json.py: Started Deleting User Info" % req_id)
    try:
        with open(path, encoding="utf-8") as data_file:
            enc = hashlib.sha256()
            enc.update(uid.encode("utf-8"))
            enc_uid = enc.hexdigest()
            data = json.load(data_file)
        if enc_uid in data:  # 사용자 정보 있을 때
            if debugging:
                print("DEL USER")
            del data[enc_uid]
        else:  # 사용자 정보 없을 때
            log.info("[#%s] delete_user@modules/user_json.py: No User Info" % req_id)
            return "NotExist"
        with open(path, "w", encoding="utf-8") as write_file:
            json.dump(data, write_file, ensure_ascii=False, indent="\t")
            log.info("[#%s] delete_user@modules/user_json.py: Succeeded" % req_id)
            return "Deleted"
    except Exception:
        log.err("[#%s] delete_user@modules/user_json.py: Failed" % req_id)
        return Exception


# 관리자 인증
def auth_admin(uid, req_id, debugging):
    with open(admin_path, encoding="utf-8") as data_file:
        enc = hashlib.sha256()
        enc.update(uid.encode("utf-8"))
        enc_uid = enc.hexdigest()
        data = json.load(data_file)
    if debugging:
        print(enc_uid)
        print(data)
    if enc_uid in data:
        log.info("[#%s] auth_admin@modules/user_json.py: Match" % req_id)
        return True
    else:
        log.info("[#%s] auth_admin@modules/user_json.py: Not Match" % req_id)
        return False


# 디버그
if __name__ == "__main__":
    # 0 - GetUser, 1 - ManageUser, 2 - DeleteUser
    flag = 1
    user_id = "uid"
    user_grade = "3"
    user_class = "11"

    path = "../data/user/user.json"
    admin_path = "../data/user/admin.json"
    if flag == 0:
        print(get_user(user_id, "****DEBUG****", True))
    elif flag == 1:
        print(manage_user(user_id, user_grade, user_class, "****DEBUG****", True))
    elif flag == 2:
        print(delete_user(user_id, "****DEBUG****", True))