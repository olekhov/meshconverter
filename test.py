#!env python3

import pdb
from colorama import init, Fore, Back, Style
import json
import logging


from gosuslugi_config import PGUAuthConfig
from pgumosru import pguauth, libmesh, dnevnik

from meshconverter import ConvertComposedMaterial

class Dmock():
    def __init__(self, auth):
        self._authToken = ""
        self._profileId = ""
        self._userId = ""
        self._auth = auth
        pass

def main():

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("chardet").setLevel(logging.WARNING)

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
    #book_id="10621820" # геометрия волчкевич
    book_id="8675576" # Решение олимпиадных задач по математике
    #book_id="7566847" # История Москвы Москва Будущего
    #book_id="11468362" # математика в кадетских классах
    book=lib.DownloadComposedDocument(book_id) 
    content=json.loads(book)["json_content"]
    with open(book_id+".json", "wb") as f:
        f.write(book)
    with open(book_id+"_content.json", "w", encoding="utf-8") as f:
        f.write(content)
    ConvertComposedMaterial(book, book_id)
    exit()

def main2():
    book_id='7566847'
    with open(book_id+'.json', encoding="utf-8") as f:
        book = f.read()
        ConvertComposedMaterial(book, book_id)



if __name__ == "__main__":
    main2()

