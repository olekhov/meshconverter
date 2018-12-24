#!env pyton3

import requests

from .utils import my_get_post, print_dict

class PGUAuthenticator:
    """ PGU Authenticator """
    def __init__(self, cfg):
        self._ps = requests.Session()
        self._cfg = cfg
        self._ps.headers['User-Agent'] = self._cfg.UA
        self.token = ""
        self.mostoken = ""
        self.Authenticated = False
                
        pass
    

    def Authenticate(self):

        try:
            ps=self._ps
            r=my_get_post(ps.get,"https://www.mos.ru")
            #print(r)
            #print("cookies:")
            #print_dict(r.cookies)
            ps.cookies.update(r.cookies)
            r=my_get_post(ps.get,"https://www.mos.ru/api/oauth20/v1/frontend/json/ru/process/enter")
            ps.cookies.update(r.cookies)
            r=my_get_post(ps.get,r.headers['Location'])
            ps.cookies.update(r.cookies)
            r=my_get_post(ps.get,r.headers['Location'])
            ps.cookies.update(r.cookies)
            r=my_get_post(ps.get,r.headers['Location'])
            login_data={ 'j_username':self._cfg.login, 'j_password' : self._cfg.password , 'accessType' : 'alias'}
            r= my_get_post(ps.post,"https://oauth20.mos.ru/sps/j_security_check", data=login_data)

            self.token = self._ps.cookies['Ltpatoken2']
            self._ps.cookies.update(r.cookies)
            r = my_get_post(self._ps.get,r.headers['Location']) # wsauth
            self._ps.cookies.update(r.cookies)
            r = my_get_post(self._ps.get,r.headers['Location']) # result?code=XXX
            self.mostoken = self._ps.cookies['mos_oauth20_token']
            #print("mostoken : " ,self.mostoken)

            self.Authenticated = self.mostoken != ""
            #print("Authenticated:", self.Authenticated)
        except:
            self.Authenticated = False

        return self.Authenticated

        
