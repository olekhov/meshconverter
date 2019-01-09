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
            art.parent=a['parentId'] if not a['parentId'] is None else 'None'
            art.id=a['id']
            TheDocument[art.id]=art
            art.html=self.RenderArticle(a)
            art.json=a

        def BuildSubtreeHtml(doc,parent, depth):
            subs=[a for key,a in doc.items() if a.parent == parent]
            subs.sort(key=lambda a: a.json['sortId'] if 'sortId' in a.json else 0)
            html=''
            toc='<ol>\n'
            for a in subs:
                toc+=f'<li><p><a href="#{a.id}">{a.name}</a></p>\n'
                hdr=f'<p id="{a.id}">{a.name} <a href="#toc">Наверх</a></p>\n'
                html+='<div class="container"><div class="center">'
                hdr=f'<div class="content-editor b" style="text-align:center""><span>'+hdr+'</span></div>'
                hdr=f'<div class="cell" style="text-align:center; width:100%; font-size:24px; font-style:bold">{hdr}</div>'
                hdr=f'<div class="row-wrapper"><div class="row row1">{hdr}</div></div>\n'

                html+='<div class="center-container">'+hdr+"</div>\n"
                html+='</div></div>'
                html+=a.html+'\n'
                h,t=BuildSubtreeHtml(doc, a.id, depth+1)
                toc+=t+'</li>\n'
                html+=h
            toc+='</ol>\n'
            return html,toc


        # формируем структуру документа
        nodes=dict(TheDocument)    
        level='None'

#        pdb.set_trace()
        s,toc=BuildSubtreeHtml(nodes,'None', 1)

        doc.write('<div class="main">')
        doc.write('<p id="toc">Содержание:</p>')
        doc.write(toc)
        doc.write('<p>Документ</p>')
        doc.write(s)
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


