#!env python3

import calendar
import requests
import time
import random
import json
import re
import pdb
import logging

from pprint import pprint

from dateutil.parser import *
import datetime

from .utils import my_get_post, print_dict



"""
Class to access to E-Diary
"""

class Dnevnik:
    """ Class to access electronic diary """
    def __init__(self, pgu_auth):
        """ pgu_auth: authenticator class for PGU """
        self._auth=pgu_auth
        self._data_url="https://my.mos.ru/data/"
        self._authenticated=False
        

    def Authenticate(self):
        """ authentication to PGU """
        if not self._auth.Authenticated:
            self._auth.Authenticate()

        self._ps=self._auth._ps
        ps=self._ps

        logging.debug("Вход в ЭЖД")

        cookies={
                "Ltpatoken2" : self._auth.Ltpatoken2,
                "mos_id" : "CllGxlwj8H6opE1tpFhhAgA=",
                "mos_oauth20_token" : self._auth.mos_oauth20_token,
                "OAUTH20-PHPSESSID" : self._auth.mos_oauth20_token}

        r_journal=ps.get("https://www.mos.ru/pgu/ru/application/dogm/journal/",
                allow_redirects=False, cookies=cookies,
                headers={"referer": "https://www.mos.ru/"})

        if r_journal.status_code != 302 :
            logging.error("Церемония поменялась")
            return False

        r_token=ps.get(r_journal.headers['Location'], allow_redirects=False,
                cookies=cookies,
                headers={"referer": "https://www.mos.ru/"})
        if r_token.status_code !=200 :
            logging.error("Вход в дневник неудачен")
            return False

        journal_token=re.search("token=([0-9a-z]*)",r_journal.headers['Location']).group(1)
        r_sessions=ps.post("https://dnevnik.mos.ru/lms/api/sessions",
                cookies=cookies, json={"auth_token":journal_token},
                allow_redirects=False,
                headers={"referer":r_journal.headers['Location']})
        if r_sessions.status_code != 200:
            logging.error("Вход в дневник неудачен")
            return False

        self._auth_token = journal_token

        self._profile=json.loads(r_sessions.text)
        self._profileId=str(self._profile["profiles"][0]["id"])
        self._userId=str(self._profile["profiles"][0]["user_id"])
        self.Authenticated = self._auth_token != ""
        return self.Authenticated

    def SelectAcademicYear(self, year_id):
        ps=self._ps
        year_id=str(year_id)

        ps.headers["Auth-Token"]=self._auth_token
        ps.cookies["authtype"]="1"
        ps.cookies["aid"]=year_id
        ps.cookies["auth_token"]=self._auth_token
        ps.cookies["is_auth"]="true"
        ps.cookies["profile_id"]=self._pid
        r=my_get_post(ps.get, "https://dnevnik.mos.ru/desktop",
                headers={"referer":self.dnevnik_top_referer})
        
        opts = { "auth_token": self._auth_token }
        r=my_get_post(ps.post,f"https://dnevnik.mos.ru/lms/api/sessions?pid={self._profile['profiles'][0]['id']}",
                json=opts, headers={"referer":"https://dnevnik.mos.ru/desktop"})

        pass

    def ListStudents(self):
        ps=self._ps
        headers={"referer"    : "https://dnevnik.mos.ru/desktop", 
            "Accept"     : "application/json",
            "Profile-Id" : self._pid}        
        
        r=my_get_post(ps.get,f"https://dnevnik.mos.ru/acl/api/users?ids={self._ids}&pid={self._pid}", headers=headers)
        
        j=json.loads(r.text)
        result=[]
        r=my_get_post(ps.get,"https://dnevnik.mos.ru/core/api/student_profiles?pid={self._pid}",
            headers=headers)
        j=json.loads(r.text)
        return j

    def OpenDiary(self, student_id):
        ps=self._ps

        self._sh={"referer" : f"https://dnevnik.mos.ru/manage/student_journal/{student_id}",
                "Accept" : "application/vnd.api.v3+json",
                "Auth-Token" : self._auth_token,
                "Profile-Id" : self._pid}

        r=my_get_post(ps.get,f"https://dnevnik.mos.ru/manage/student_journal/{student_id}")
        r=my_get_post(ps.post,f"https://dnevnik.mos.ru/lms/api/sessions?pid={self._pid}",
            headers=self._sh)
        self._sh["Accept"]="application/json"
        self.LoadGroups(student_id)
        self.LoadSchedule(student_id)
        return

    def LoadGroups(self, student_id):
        ps=self._ps
        params={
                "academic_year_id":"6",
                "pid":self._pid,
                "with_archived_groups":"true",
                "with_groups":"true" }
        r=my_get_post(ps.get,f"https://dnevnik.mos.ru/core/api/student_profiles/{student_id}",
                headers=self._sh, params=params)
        self.groups=json.loads(r.text)['groups']
        pass

    def LoadSchedule(self, student_id):
        ps=self._ps
        gs=[]
        for g in self.groups:
            gs.append(str(g['id']))
        params={ "group_ids" : ','.join(gs),"pid":self._pid}
        r=my_get_post(ps.get,f"https://dnevnik.mos.ru/jersey/api/groups",
                headers=self._sh, params=params)
        self.schedule=json.loads(r.text)

        self.sched_dict={}
        for s in self.schedule:
            self.sched_dict[s['id']]=s
        pass

    def GetHomework(self, year_id, student_id, begin_date, end_date):
        ps=self._ps

        params={
                "academic_year_id":year_id,
                "begin_date":begin_date,
                "end_date": end_date,
                "pid":self._pid,
                "student_profile_id":student_id}

        r=my_get_post(ps.get,f"https://dnevnik.mos.ru/core/api/student_homeworks", headers=self._sh, params=params)

        j=json.loads(r.text)

        for h in j:
            cr=parse(h['homework_entry']['created_at'])
            dt_assigned=parse(h['homework_entry']['homework']['date_assigned_on'])
            if cr>dt_assigned+datetime.timedelta(days=2):
                h['fair']=False
            else:
                h['fair']=True
        return j


        pass

    def GetMarks(self,student_id, created_from, created_to):
        ps=self._ps

        params={
                "created_at_from":created_from,
                "created_at_to"  :created_to,
                "page":"1", "per_page":"50",
                "pid" : self._pid,
                "student_profile_id": student_id}
        r=my_get_post(ps.get,"https://dnevnik.mos.ru/core/api/marks",
                params=params, headers=self._sh)
        j=json.loads(r.text)

        return j



class DiaryProfile:
    """ """
    def __init__(self, login, comment, password, system):
        self.login=login
        self.comment=comment
        self.password=password
        self.system=system

    def __repr__(self):
        return "r[%s] : login=%s password=%s\n" %(self.comment, self.login, self.password)
        
    def __str__(self):
        return "s[%s] : login=%s password=%s\n" %(self.comment, self.login, self.password)



