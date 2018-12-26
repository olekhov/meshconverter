#!env pyton3

import requests
import logging
import pdb
import re

from .utils import my_get_post, print_dict

class PGUAuthenticator:
    """ PGU Authenticator """
    def __init__(self, cfg):
        self._ps = requests.Session()
        self._cfg = cfg
        self._ps.headers['User-Agent'] = self._cfg.UA
        self.Ltpatoken2 = ""
        self.mos_oauth20_token = ""
        self.Authenticated = False
                
        pass
    

    def Authenticate(self):
        popular="https://www.mos.ru/services/catalog/popular/"

        if True:
            ps=self._ps
            logging.debug("Открываем портал www.mos.ru")
            r_ae=ps.get("https://login.mos.ru/sps/oauth/ae?client_id=Wiu8G6vfDssAMOeyzf76&response_type=code&redirect_uri=https://my.mos.ru/my/website_redirect_uri&scope=openid+profile", allow_redirects=False)
            if r_ae.status_code != 303 or r_ae.headers['Location']!="/sps/login/methods/password":
                logging.error("Церемония поменялась")
                raise
            #ps.cookies.update(r.cookies)
            r_password=ps.get("https://login.mos.ru"+r_ae.headers['Location'], allow_redirects=False)
            logging.debug("Начало аутентификационной сессии")
            r_opts=ps.get("https://www.mos.ru/api/oauth20/v1/frontend/json/ru/options", headers={"referer":popular})
            logging.debug("Вход")
            r_enter=ps.get(f"https://www.mos.ru/api/oauth20/v1/frontend/json/ru/process/enter?redirect={popular}",
                    cookies=r_opts.cookies, allow_redirects=False)

            if r_enter.status_code !=302:
                logging.error("Церемония поменялась")
                raise
            r_authorize=ps.get(r_enter.headers['Location'], allow_redirects=False)
            logging.debug("Переход на форму авторизации")
            if r_enter.status_code !=302:
                logging.error("Церемония поменялась")
                raise

            #ps.cookies.update(r_password.cookies)
            #ps.cookies.update(r.cookies)
            r_ae2=ps.get(r_authorize.headers['Location'], allow_redirects=False)

            if r_ae2.status_code !=303 or r_ae2.headers['Location']!="/sps/login/methods/password":
                logging.error("Церемония поменялась")
                raise

            r_password2=ps.get("https://login.mos.ru"+r_ae2.headers['Location'], allow_redirects=False, cookies=r_ae2.cookies)
            if r_password2.status_code != 200 :
                logging.error("Церемония поменялась")
                raise
                    
            logging.debug("Выбираем вариант входа: через госуслуги")

            r_execute=ps.get("https://login.mos.ru/sps/login/externalIdps/execute?typ=esia&name=esia_1&isPopup=false",
                    headers={"referer": "https://login.mos.ru/sps/login/methods/password"}, 
                    cookies=r_ae2.cookies, allow_redirects=False)
            
            if r_execute.status_code !=303 :
                logging.error("Церемония поменялась")
                raise

            r_ac=ps.get(r_execute.headers["Location"], allow_redirects=False, 
                    headers={"referer":"https://login.mos.ru/"})

            m=re.search('<meta http-equiv="refresh" content="0;url=([^"]*)">',r_ac.text)
            r_SSO=ps.get(m.group(1), cookies=r_ac.cookies, allow_redirects=False)

            if r_SSO.status_code !=302 :
                logging.error("Церемония поменялась")
                raise

            #ps.cookies.update(r_SSO.cookies)
            #ps.cookies['JSESSIONID']=r_ac.cookies['JSESSIONID']
            AuthnEngine_cookies={
                    '_idp_authn_lc_key' : r_SSO.cookies['_idp_authn_lc_key'],
                    'dtCookie' : r_SSO.cookies['dtCookie'],
                    'idp_id':r_SSO.cookies['idp_id'],
                    'JSESSIONID':r_ac.cookies['JSESSIONID'],
                    'oiosaml-fragment':'',
                    'usi':r_SSO.cookies['usi']}

            r_AuthnEngine=ps.get(r_SSO.headers["Location"], allow_redirects=False,
                    cookies=AuthnEngine_cookies)


            command=re.search("LoginViewModel\('/idp','','(.*)','','null','null',false, 300, 'gosuslugi.ru'\);", 
                    r_AuthnEngine.text )
            login_data={
                    "mobileOrEmail":self._cfg.login,
                    "snils":"",
                    "password":self._cfg.password,
                    "login":self._cfg.login,
                    "command":command.group(1),
                    "idType":"email" }

#            ps.cookies.update(r_SSO.cookies)
            pwd_cookies={
                    '_idp_authn_id': 'email:'+self._cfg.login,
                    '_idp_authn_lc_key':r_SSO.cookies['_idp_authn_lc_key'],
                    'dtCookie':r_SSO.cookies['dtCookie'],
                    'dtPC':'46056292_870h1',
                    'idp_id':r_AuthnEngine.cookies['idp_id'],
                    'SCS':r_AuthnEngine.cookies['SCS'],
                    'JSESSIONID':r_ac.cookies['JSESSIONID'],
                    'login_value':self._cfg.login,
                    'oiosaml-fragment':'',
                    'timezone':'3',
                    'userSelectedLanguage':'ru',
                    'usi':r_AuthnEngine.cookies['usi'] }
            ps.cookies.clear()

            r_pwddo=ps.post("https://esia.gosuslugi.ru/idp/login/pwd/do", 
                    data=login_data, 
                    headers={"referer":"https://esia.gosuslugi.ru/idp/rlogin?cc=bp"},
                    cookies=pwd_cookies,
                    allow_redirects=False)
            if r_pwddo.status_code !=302 :
                logging.error("Церемония поменялась")
                raise

            SSO2_cookies={
                    '_idp_authn_id': 'email:'+self._cfg.login,
                    '_idp_authn_lc_key':r_SSO.cookies['_idp_authn_lc_key'],
                    '_idp_session':r_pwddo.cookies['_idp_session'],
                    'dtCookie':r_SSO.cookies['dtCookie'],
                    'dtPC':'46056292_870h1',
                    'idp_id':r_AuthnEngine.cookies['idp_id'],
                    'SCS':r_AuthnEngine.cookies['SCS'],
                    'JSESSIONID':r_ac.cookies['JSESSIONID'],
                    'login_value':self._cfg.login,
                    'oiosaml-fragment':'',
                    'timezone':'3',
                    'userSelectedLanguage':'ru',
                    'usi':r_AuthnEngine.cookies['usi'] }


            r_SSO2=ps.get(r_pwddo.headers['Location'],
                    allow_redirects=False,
                    headers={"referer":"https://esia.gosuslugi.ru/idp/rlogin?cc=bp"},
                    cookies=SSO2_cookies)

            samlr=re.search('<input type="hidden" name="SAMLResponse" value="(.*)"/>',r_SSO2.text)

            SAMLResponse=samlr.group(1)
            RelayState=re.search('RelayState=([-_a-z0-9]*)',m.group(1)).group(1)

            post_data={
                    'RelayState':RelayState,
                    'SAMLResponse':SAMLResponse}
            consumer_cookies={
                    '_idp_authn_id': 'email:'+self._cfg.login,
                    'bs':r_pwddo.cookies['bs'],
                    'idp_id':r_AuthnEngine.cookies['idp_id'],
                    'SCS':r_AuthnEngine.cookies['SCS'],
                    'JSESSIONID':r_ac.cookies['JSESSIONID'],
                    'login_value':self._cfg.login,
                    'oauth_id':r_ac.cookies['oauth_id'],
                    'oiosaml-fragment':'',
                    'timezone':'3',
                    'userSelectedLanguage':'ru',
                    'usi':r_AuthnEngine.cookies['usi'] }

            r_SAMLAC=ps.post("https://esia.gosuslugi.ru/aas/oauth2/saml/SAMLAssertionConsumer",
                    data=post_data,
                    allow_redirects=False,
                    headers={'referer':'https://esia.gosuslugi.ru/idp/profile/SAML2/Redirect/SSO'},
                    cookies=consumer_cookies)

            if r_SAMLAC.status_code !=302 :
                logging.error("Церемония поменялась")
                raise

            ps.cookies.clear()
            r_acfinish=ps.get(r_SAMLAC.headers['location'],
                    allow_redirects=False,
                    headers={'referer':'https://esia.gosuslugi.ru/idp/profile/SAML2/Redirect/SSO'},
                    cookies=consumer_cookies)

            if r_acfinish.status_code !=302 :
                logging.error("Церемония поменялась")
                raise

            callback_cookies={
                    'fm': r_ae.cookies['fm'],
                    'history': r_execute.cookies['history'],
                    'lstate' : r_execute.cookies['lstate'],
                    'oauth_az':r_ae.cookies['oauth_az'],
                    'origin': r_ae.cookies['origin']}

            r_callback=ps.get(r_acfinish.headers['location'],allow_redirects=False,
                    cookies=callback_cookies,
                    headers={'referer':'https://esia.gosuslugi.ru/'})
            
            self.mos_oauth20_token = r_opts.cookies['OAUTH20-PHPSESSID']
            self.Ltpatoken2 = r_callback.cookies['Ltpatoken2']
            self.Authenticated = self.Ltpatoken2 != ""
#        except:
#            self.Authenticated = False

        return self.Authenticated

        
