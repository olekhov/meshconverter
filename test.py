#!env python3

import pdb
from colorama import init, Fore, Back, Style
import json
import logging


from gosuslugi_config import PGUAuthConfig
from pgumosru import pguauth, libmesh, dnevnik

class Dmock():
    def __init__(self, auth):
        self._authToken = ""
        self._profileId = ""
        self._userId = ""
        self._auth = auth
        pass

def main():

    logging.basicConfig(level=logging.INFO)
    init()
    print(f"Вход на {Style.BRIGHT}{Fore.WHITE}ГОС{Fore.BLUE}УСЛ{Fore.RED}УГИ{Style.RESET_ALL}: ", end="")
    cfg = PGUAuthConfig()
    auth = pguauth.PGUAuthenticator(cfg)
    if auth.Authenticate() :
        print(f"{Style.BRIGHT}{Fore.GREEN}OK{Style.RESET_ALL}")
    else:
        print(f"{Style.BRIGHT}{Back.RED}Ошибка!{Style.RESET_ALL}")
        exit()

    d=dnevnik.Dnevnik(auth)
    d.Authenticate()

    lib=libmesh.MESHLibrary(d)
    lib.Open()
    book_id="10621820" # геометрия волчкевич
    #book_id="8675576" # Решение олимпиадных задач по математике
    book=lib.DownloadComposedDocument(book_id) 
    with open(book_id+".json", "wb") as f:
        f.write(book)
    exit()





if __name__ == "__main__":
    main()

