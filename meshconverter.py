#!env python3

import json
import pdb
from pprint import pprint
from urllib.parse import unquote
from tqdm import tqdm
import os
import requests
import hashlib
from anytree import Node, RenderTree, PreOrderIter
import queue

class MeshArticle():
    """ Класс, представляющий одну статью в материале """
    def __init__(self):
        self.name=""
        self.parent=""
        self.html=""
        pass

class MeshConverter():
    """ Класс, преобразующий материал в html """

    def __init__(self,dlfolder):
        self.dlfolder=dlfolder
        self.site="https://uchebnik.mos.ru"
        pass


    def RenderImage(self,j):
        #pdb.set_trace()
        url=self.site+j['atomic']['file']
        ts=url.rfind('?')
        if ts>0 : url=url[:ts]
        extp=url.rfind(".")
        ext=url[extp+1:]
        bn=hashlib.md5(url.encode('utf-8')).hexdigest()
        filename=f"download/{bn}.{ext}"
        self.DownloadFile(url, self.dlfolder+"/"+filename,
            os.path.basename(unquote(url)))
        w=str(j['block']['width'])
        h=str(j['block']['height'])

        if w.isnumeric(): w=w+'px'
        if h.isnumeric(): h=h+'px'
        if h=='auto': h='inherit'

        html=f'<img src="{filename}" style="position:relative;width:auto; height:{h}; max-width:100%; max-height:100%;"/>'
        return html

    def ProcessPars(self,text):
        r=text.replace("<p>","<span>").replace("</p>","</span>")
        return r

    def RenderText(self,j):
        if 'displayContent' in j['atomic']:
            b=j['block']            
            w=str(b['width'])+'px'
            h=str(b['height'])+'px'
            if not b['maxWidth'] : 
                w='auto' 
            style=f'text-align:{b["align"]}; color:{b["textColor"]}; font-size:{b["textSize"]}px; background:{b["background"]}'
            par=self.ProcessPars(j['atomic']['displayContent'])
            html=f'<span style="">\n'+par+'\n</span>'
            s=""
            if b["bold"] : s+=" bold-style"
            if b["italic"] : s+=" text_italic"
            html=f'<div class="content-editor {s}" style="{style}">'+html+'</div>'
        else:
            html=''
        return html

    ObjectRenderers={
            "text" : RenderText,
            "image" : RenderImage,
#        "video" : RenderVideo,
#        "link" : RenderLink
            }



    """ Отрисовать один объект в ячейке """
    def RenderObject(self,j):
        html='<div class="block">'

        if j["atomic"]["content_type"] in self.ObjectRenderers :
            html+=self.ObjectRenderers[j["atomic"]["content_type"]](self,j)
        else:
            html+=f'Не знаю, как отобразить {j["atomic"]["content_type"]}'
        html+='</div>'
        return html

    """ Отрисовать одну ячейку """
    def RenderCell(self,j):
        w=str(j['content']['width'])
        h=str(j['content']['height'])
        if w.isnumeric() : w=w+'px'
        if h.isnumeric() : h=h+'px'
        fontsize=j['content']['textSize']
        ta=j['content']['align']
        if j['content']['italic'] : 
            fontstyle="font-style:italic;"
        else:
            fontstyle=""


        html=f'<div class="cell" style="text-align:{ta}; width:{w}; font-size:{fontsize}px; {fontstyle}">'
        for oidx,o in enumerate(j["content"]["objects"]):
            html+=self.RenderObject(o)+"\n"
        html+='</div>'
        return html

    """ Отрисовать один ряд """
    def RenderRaw(self,j):
        nc=len(j["cells"])
        html=f'<div class="row-wrapper"><div class="row row{nc}">\n'
        for cidx, c in enumerate(j["cells"]):
            html+=self.RenderCell(c)+"\n"
        html+='</div></div>'
        return html

    """ Отрисовать статью """
    def RenderArticle(self,j):
        html='<div class="container container_main"><div class="center">'
        for ridx,row in enumerate(j["layout"]["rows"]):
            html+='<div class="center-container">'+self.RenderRaw(row)+"</div>\n"
        html+='</div></div>'
        return html

    def CalculateArticleWidth(self,j):
        w=0
        for ridx,row in enumerate(j["layout"]["rows"]):
            for cell in enumerate(row["cells"]):
                cw=int(cell["width"],0)
                if w<cw : w=cw
        return w

    """ Download composed_material """
    def ConvertComposedMaterial(self,data):
        material=json.loads(data)
        content_name = material['name'] if 'name' in material else 'UNKNOWN'
        content_desc = material['description'] if 'description' in material  else 'UNKNOWN'
        content_author = material['author_name'] if 'author_name' in material else 'UNKNOWN'

        print(f"Название: {content_name}")
        print(f"Описание: {content_desc}")

        js=json.loads(material['json_content'])

        print(f"Разделов: {len(js['articles'])}")
        page=1

        if not os.path.isdir(self.dlfolder):
            os.makedirs(self.dlfolder)

        if not os.path.isdir(self.dlfolder+"/download"):
            os.makedirs(self.dlfolder+"/download")

        dlid=1000

        doc=open(self.dlfolder+"/index.html", "w", encoding="utf-8")
        doc.write("""
    <!DOCTYPE html>
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            <title>Играемся</title>
            <link rel="stylesheet" href="../assets/mykatex.css" >
            <link rel="stylesheet" href="../assets/main.css" >
     <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.10.0/dist/katex.min.css" integrity="sha384-9eLZqc9ds8eNjO3TmqPeYcDj8n+Qfa4nuSiGYa6DjLNcv9BtN69ZIulL9+8CqC9Y" crossorigin="anonymous">

        <!-- The loading of KaTeX is deferred to speed up page rendering -->
        <script defer src="https://cdn.jsdelivr.net/npm/katex@0.10.0/dist/katex.min.js" integrity="sha384-K3vbOmF2BtaVai+Qk37uypf7VrgBubhQreNQe9aGsz9lB63dIFiQVlJbr92dw2Lx" crossorigin="anonymous"></script>

        <!-- To automatically render math in text elements, include the auto-render extension: -->
        <script defer src="https://cdn.jsdelivr.net/npm/katex@0.10.0/dist/contrib/auto-render.min.js" integrity="sha384-kmZOZB5ObwgQnS/DuDg6TScgOiWWBiVt0plIRkZCmE6rDZGrEOQeHM5PcHi+nyqe" crossorigin="anonymous"
            onload="renderMathInElement(document.body);"></script>
        <script src="../assets/render.js"> </script>
        </head>
        <body>
        """)

        TheDocument={}

        for aidx, a in enumerate(js['articles'], start=1):
            #doc.write(f"<h1>{aidx:02}. {a['name']}</h1>")
            art = MeshArticle()
            art.name=a['name']
            art.parent=a['parentId']
            art.id=a['id']
            TheDocument[art.id]=art
            art.html=self.RenderArticle(a)

        if False:
#        pm.write(f"[ /Title <{TOHEX(str(aidx)+'. '+a['name'])}> /Page {page} /OUT pdfmark\n")
            for ridx, row in enumerate(a['layout']['rows'],start=1):
                for cidx, cell in enumerate(row['cells'],start=1):
#                if cidx>2: pdb.set_trace()

                    for oidx, obj in enumerate(cell['content']['objects'],start=1):
                        atomic_type=obj['atomic']['content_type']

                        if atomic_type == 'file':
                            url=site+obj['atomic']['file']
                            bn=os.path.basename(unquote(url))
                            filename=f"download/{aidx:02}-{ridx:02}-{cidx:02}-{oidx:02}-{bn}"
                            DownloadFile(url, folder+"/"+filename, "file")
                            #gs.write(f"\n({filename}) viewJPEG showpage \\")
                            page=page+1
                        elif atomic_type == 'text':
                            if 'displayContent' in obj['atomic']:
                                art.html+=obj['atomic']['displayContent']
                        elif atomic_type == 'image':
#                        pdb.set_trace()
                            url=site+obj['atomic']['file']
                            ts=url.rfind('?')
                            if ts>0 : url=url[1:ts]
                            #print(f"ts: {ts}")
                            extp=url.rfind(".")
                            ext=url[extp:]
                            bn=hashlib.md5(url.encode('utf-8')).hexdigest()
                            filename=f"download/{bn}.{ext}"
                            DownloadFile(url, folder+"/"+filename,
                                    os.path.basename(unquote(url)))
                            dlid+=1
                            w=obj['block']['width']
                            h=obj['block']['height']
                            art.html+=f"<img src='{filename}' width='{w}' height='{h}'/>"
                        else:
                            print(f"UNKNOWN CONTENT TYPE: {atomic_type}")


                
#        print(f": {len(a['layout']['rows'][0]['cells'])}")
#        pprint(objs, depth=2)

        # формируем структуру документа
        nodes=dict(TheDocument)    

        print("формируем структуру документа")
        while nodes:
            r=False
            cn=dict(nodes)
            for key,val in cn.items():
                if val.parent in TheDocument:
                    nodes.pop(key)
                    r=True
          #          print(f"Удалили {key}")
            if not r : 
         #       print("За этот заход так ничего и не удалили")
                break
            else:
        #        print("Удалили, ещё зайдём")
                pass

        topart=list(nodes.values())[0]

        pdb.set_trace()
        print(f"Остался только один: {topart.name}")

        nodes=dict(TheDocument)
        nodes.pop(topart.id)
        top = Node(topart.id, article=topart, nestlevel=0)

        # Очередь на поиск
        artq=queue.Queue()
        artq.put(top)

        while not artq.empty():
            print(f"Длина очереди: {artq.qsize()}")
            a=artq.get(False)
            for key,value in TheDocument.items():
                if value.parent==a.article.id:
                    n = Node(value.id, article=value, parent=a,
                            nestlevel=a.nestlevel+1)
                    print(f"Добавили {value.name} в {a.article.name}")
                    artq.put(n)

        for pre,fill,node in RenderTree(top):
            print(f"{pre} {node.article.name}")

        doc.write('<div class="main">')
        for a in PreOrderIter(top):
            #doc.write(f"<h{a.nestlevel}>{a.article.name}</h{a.nestlevel}>")
            doc.write(a.article.html)    


        doc.write("</div>")
        doc.write("</body></html>")
        doc.close()
        pass

    def TOHEX(s):
        return 'feff'+s.encode('utf-16be').hex()

    def DownloadFile(self,url, filename, desc):
        if os.path.isfile(filename):
            print(f"{desc} уже загружен")
            return
        r=requests.get(url,stream=True)
        sz=int(r.headers.get('content-length', None))
        pbar=tqdm(r.iter_content(4096), desc=desc, unit="B", unit_scale=1,total=sz)
        with open(filename,"wb") as f:
            for data in pbar:
                f.write(data)
                pbar.update(len(data))
        pbar.close()


