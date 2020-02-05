# ██╗  ██╗██████╗ ███╗   ███╗███████╗ █████╗ ██╗
# ██║  ██║██╔══██╗████╗ ████║██╔════╝██╔══██╗██║
# ███████║██║  ██║██╔████╔██║█████╗  ███████║██║
# ██╔══██║██║  ██║██║╚██╔╝██║██╔══╝  ██╔══██║██║
# ██║  ██║██████╔╝██║ ╚═╝ ██║███████╗██║  ██║███████╗
# ╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝
# Copyright 2019, Hyungyo Seo
# modules/conf.py - 설정을 관리하는 스크립트입니다.

import yaml

configs = None
pubkey = None
privkey = None


def load():
    global configs, pubkey, privkey
    with open('data/conf.yaml', 'r', encoding="utf-8") as config_file:
        configs = yaml.load(config_file, Loader=yaml.SafeLoader)
    with open("data/keys/public.pem", 'r', encoding="utf-8") as pubkey_file:
        pubkey = pubkey_file.read()
    with open("data/keys/private.pem", 'r', encoding="utf-8") as privkey_file:
        privkey = privkey_file.read()