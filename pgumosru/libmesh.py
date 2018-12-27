#!env python3

import requests
import time
import random
import json
import re
import pdb
import logging
from tqdm import tqdm

from .utils import my_get_post, print_dict

"""
Классы, обслуживающие Библиотеку МЭШ
"""

class MESHLibrary:

    """ Данные для аутентификации в библиотеке берутся из Дневника """
    def __init__(self, Dnevnik):
        #if not Dnevnik._authenticated:
        #    if not Dnevnik.Authenticate():
        #        raise "Ошибка аутентификации в Электронном дневнике"
        self.d = Dnevnik
        self._ps = requests.Session()
        self._ps.cookies["Ltpatoken2"]=self.d._auth.Ltpatoken2
        self._ps.cookies["mos_oauth20_token"]=self.d._auth.mos_oauth20_token
        self._si=""


    def Open(self):
        ps = self._ps
        params={ 
            "userId" : self.d._userId, 
            "profileId" : self.d._profileId,
            "authToken" : self.d._auth_token}
        r = my_get_post(ps.get, "https://uchebnik.mos.ru/authenticate", params=params)
        opts = {"auth_token" : self.d._auth_token }
        headers={"referer"    :
                f"https://uchebnik.mos.ru/authenticate?userId={self.d._userId}&profileId={self.d._profileId}&authToken={self.d._auth_token}", 
            "Accept"     : "application/json; charset=UTF-8",
            "profile-id" : self.d._profileId,
            "user-id" : self.d._userId,
            }        
        r = my_get_post(ps.post, "https://uchebnik.mos.ru/api/sessions", json=opts, headers=headers)
        if r.status_code == 200:
            self._si=json.loads(r.text)
            logging.info("Аутентификация прошла успешно")
            logging.info(f"Пользователь: {self._si['first_name']} {self._si['middle_name']} {self._si['last_name']}")
            logging.info(f"Роль: {self._si['profiles'][0]['type']}")
            self._ps.cookies["profile_id"]=self.d._profileId
            self._ps.cookies["user_id"]=self.d._userId
            self._ps.cookies["auth_token"]=self.d._auth_token

    
    def DownloadComposedDocument(self,id):
        ps = requests.Session()
        ps.cookies["request_method"]="GET"
        headers={"referer"    : f"https://uchebnik.mos.ru/composer2/document/{id}/view", 
            "Accept"     : "application/vnd.cms-v2+json",
            "profile-id" : self.d._profileId,
            "user-id" : self.d._userId,
            "Auth-Token" : self.d._auth_token }        

        r=ps.get("https://uchebnik.mos.ru/cms/api/composed_documents/"+id, headers=headers, stream=True)
        sz=int(r.headers.get('content-length', None))
#        js=r.content
        js=bytes()
        pbar=tqdm(r.iter_content(chunk_size=4096), unit="B", unit_scale=1, total=sz)
        for data in pbar:
            js+=data
            pbar.update(len(data))
        pbar.close()
        return js



