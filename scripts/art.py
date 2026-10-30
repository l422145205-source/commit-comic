"""Original vector comic scenes, with optional Pillow exports. No image API or network."""
from __future__ import annotations
import html
import json
import math
from pathlib import Path
import unicodedata

from evidence import check_line, digest, md, pretty, safe_board, validate_board

PALETTES={
 'pop':{'paper':'#FFF4D4','ink':'#202339','panel':'#FFFFFF','accent':'#FFD34D','blue':'#9DDAE2','pink':'#FFA5B5','green':'#A8DCA9'},
 'night':{'paper':'#161B33','ink':'#F7F2DF','panel':'#252D4B','accent':'#FFD34D','blue':'#79C9D8','pink':'#F39EBC','green':'#94D0AE'}}


class Canvas:
    def __init__(self,width,height,theme='pop'):
        self.width=width;self.height=height;self.p=PALETTES[theme];self.commands=[]
        self.rect(0,0,width,height,self.p['paper'],None,0)
    def rect(self,x,y,w,h,fill,stroke=None,sw=3,r=0):self.commands.append(('rect',(x,y,w,h,fill,stroke,sw,r)))
    def ellipse(self,x,y,w,h,fill,stroke=None,sw=3):self.commands.append(('ellipse',(x,y,w,h,fill,stroke,sw)))
    def line(self,pts,fill=None,sw=4):self.commands.append(('line',(pts,fill or self.p['ink'],sw)))
    def poly(self,pts,fill,stroke=None,sw=3):self.commands.append(('poly',(pts,fill,stroke,sw)))
    def text(self,x,y,value,size=26,fill=None,bold=False):self.commands.append(('text',(x,y,str(value),size,fill or self.p['ink'],bold)))
    def wrap(self,x,y,value,width,size=26,max_lines=4,fill=None):
        # Conservative glyph estimates keep the editable SVG independent of font libraries.
        lines=[];line='';used=0
        for char in value:
            units=1 if unicodedata.east_asian_width(char) in {'W','F'} else .61
            if char=='\n' or used+units>width/size:
                if char!='\n' and char.isascii() and char.isalnum() and ' ' in line and line.rfind(' ')>len(line)*.4:
                    last=line.rfind(' ');lines.append(line[:last].rstrip());line=line[last+1:]+char
                    used=sum(1 if unicodedata.east_asian_width(v) in {'W','F'} else .61 for v in line)
                else:lines.append(line.rstrip());line='' if char=='\n' else char;used=0 if char=='\n' else units
            else:line+=char;used+=units
        if line:lines.append(line)
        if len(lines)>max_lines:raise ValueError('Comic text overflows its panel; shorten the storyboard copy')
        for i,line in enumerate(lines):self.text(x,y+i*(size+10),line,size,fill)
        return y+len(lines)*(size+10)
    def svg(self):
        out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" role="img" aria-label="CommitComic">']
        def esc(s):return html.escape(str(s),quote=True)
        for kind,args in self.commands:
            if kind=='rect':
                x,y,w,h,fill,stroke,sw,r=args;out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="{sw}"/>')
            elif kind=='ellipse':
                x,y,w,h,fill,stroke,sw=args;out.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{sw}"/>')
            elif kind in {'line','poly'}:
                pts,fill,sw=args if kind=='line' else (args[0],args[1],args[3])
                points=' '.join(f'{x},{y}' for x,y in pts)
                if kind=='line':out.append(f'<polyline points="{points}" fill="none" stroke="{fill}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')
                else:out.append(f'<polygon points="{points}" fill="{fill}" stroke="{args[2] or "none"}" stroke-width="{sw}"/>')
            else:
                x,y,value,size,fill,bold=args
                out.append(f'<text x="{x}" y="{y+size*.85}" font-size="{size}" fill="{fill}" font-family="Microsoft YaHei,Noto Sans CJK SC,DejaVu Sans,sans-serif" font-weight="{700 if bold else 400}">{esc(value)}</text>')
        return '\n'.join(out+['</svg>'])+'\n'
    def png(self,font_path=None):
        from PIL import Image,ImageDraw,ImageFont
        im=Image.new('RGB',(self.width,self.height));d=ImageDraw.Draw(im)
        chinese=any(any(unicodedata.east_asian_width(c) in {'W','F'} for c in a[2]) for k,a in self.commands if k=='text')
        if not font_path:
            candidates=['C:/Windows/Fonts/msyh.ttc','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/System/Library/Fonts/PingFang.ttc']
            font_path=next((p for p in candidates if Path(p).is_file()),None)
        if chinese and not font_path:raise ValueError('Chinese PNG needs a local CJK font via --font; SVG is available without it')
        cache={}
        def font(n):
            if n not in cache:
                try:cache[n]=ImageFont.truetype(str(font_path or 'DejaVuSans.ttf'),n)
                except OSError:cache[n]=ImageFont.load_default(size=n)
            return cache[n]
        for kind,args in self.commands:
            if kind=='rect':
                x,y,w,h,fill,stroke,sw,r=args;d.rounded_rectangle((x,y,x+w,y+h),radius=r,fill=fill,outline=stroke,width=sw)
            elif kind=='ellipse':
                x,y,w,h,fill,stroke,sw=args;d.ellipse((x,y,x+w,y+h),fill=fill,outline=stroke,width=sw)
            elif kind=='line':pts,fill,sw=args;d.line(pts,fill=fill,width=sw,joint='curve')
            elif kind=='poly':pts,fill,stroke,sw=args;d.polygon(pts,fill=fill);d.line(pts+[pts[0]],fill=stroke or fill,width=sw,joint='curve')
            else:
                x,y,value,size,fill,bold=args;d.text((x,y),value,font=font(size),fill=fill,anchor='lt',stroke_width=1 if bold else 0,stroke_fill=fill)
        return im


def note(c,x,y,s=1,tilt=0):
    p=c.p;w=105*s;h=120*s
    c.rect(x+7*s,y+9*s,w,h,p['ink'],r=5)
    c.rect(x,y,w,h,p['accent'],p['ink'],4,r=6)
    c.poly([(x+w-27*s,y),(x+w,y+27*s),(x+w-27*s,y+27*s)],p['paper'],p['ink'],3)
    c.ellipse(x+24*s,y+39*s,8*s,12*s,p['ink']);c.ellipse(x+64*s,y+39*s,8*s,12*s,p['ink'])
    c.line([(x+31*s,y+73*s),(x+52*s,y+84*s),(x+75*s,y+73*s)],p['ink'],4)


def coder(c,x,y,s=1,mood='happy'):
    p=c.p
    c.rect(x+27*s,y+102*s,82*s,42*s,p['blue'],p['ink'],4,r=10)
    c.line([(x+49*s,y+144*s),(x+43*s,y+171*s)],p['ink'],6)
    c.line([(x+87*s,y+144*s),(x+94*s,y+171*s)],p['ink'],6)
    c.line([(x+27*s,y+113*s),(x+5*s,y+(82 if mood=='cheer' else 134)*s)],p['ink'],5)
    c.line([(x+109*s,y+113*s),(x+139*s,y+(65 if mood=='cheer' else 91)*s)],p['ink'],5)
    c.rect(x,y,135*s,105*s,p['ink'],p['ink'],4,r=12)
    c.rect(x+10*s,y+10*s,115*s,81*s,p['blue'],p['ink'],2,r=7)
    c.ellipse(x+34*s,y+37*s,10*s,15*s,p['ink']);c.ellipse(x+91*s,y+37*s,10*s,15*s,p['ink'])
    if mood=='worried':
        c.line([(x+49*s,y+74*s),(x+68*s,y+65*s),(x+87*s,y+74*s)],p['ink'],4)
        c.line([(x+28*s,y+27*s),(x+49*s,y+32*s)],p['ink'],3)
        c.line([(x+87*s,y+32*s),(x+109*s,y+27*s)],p['ink'],3)
    else:c.line([(x+49*s,y+66*s),(x+68*s,y+73*s),(x+87*s,y+66*s)],p['ink'],4)


def bug(c,x,y,s=1):
    p=c.p
    for dy in (22,46,71):
        c.line([(x+15*s,y+dy*s),(x-10*s,y+(dy-13)*s)],p['ink'],4)
        c.line([(x+78*s,y+dy*s),(x+103*s,y+(dy-13)*s)],p['ink'],4)
    c.ellipse(x,y,92*s,103*s,p['pink'],p['ink'],4)
    c.line([(x+46*s,y+22*s),(x+46*s,y+95*s)],p['ink'],3)
    c.ellipse(x+14*s,y-20*s,64*s,50*s,p['ink'])
    for xx in (x+31*s,x+58*s):c.ellipse(xx,y-5*s,7*s,10*s,p['paper'])
    c.line([(x+24*s,y-17*s),(x+12*s,y-35*s)],p['ink'],4)
    c.line([(x+67*s,y-17*s),(x+82*s,y-35*s)],p['ink'],4)


def scene(c,kind,x,y,w,h):
    p=c.p;s=min(w/600,h/190)
    for i in range(9):
        c.ellipse(x+w-100+i%3*22,y+18+i//3*23,4,4,p['pink'])
    coder(c,x+28,y+22,s*.9,'worried' if kind=='duplicate' else 'cheer' if kind=='check' else 'happy')
    if kind=='duplicate':
        note(c,x+w*.39,y+30,s*.90);note(c,x+w*.68,y+30,s*.90)
        for xx in (x+w*.57,x+w*.61):c.line([(xx,y+45),(xx,y+120)],p['pink'],5)
    elif kind=='inspect':
        note(c,x+w*.55,y+33,s*.88)
        c.ellipse(x+w*.47,y+15,155*s,155*s,None,p['ink'],9)
        c.line([(x+w*.47+130*s,y+140*s),(x+w*.47+181*s,y+190*s)],p['ink'],13)
    elif kind=='repair':
        bug(c,x+w*.44,y+80,s*.75)
        c.rect(x+w*.70,y+40,110*s,110*s,p['green'],p['ink'],4,r=12)
        c.line([(x+w*.70+21*s,y+90*s),(x+w*.70+42*s,y+111*s),(x+w*.70+88*s,y+67*s)],p['ink'],9)
    else:
        c.rect(x+w*.40,y+30,240*s,135*s,p['green'],p['ink'],4,r=12)
        for i in range(3):
            yy=y+(54+i*33)*s
            c.line([(x+w*.40+16*s,yy),(x+w*.40+26*s,yy+8*s),(x+w*.40+44*s,yy-13*s)],p['ink'],5)
            c.line([(x+w*.40+69*s,yy),(x+w*.40+204*s,yy)],p['ink'],4)


def panel(c,row,x,y,w,h,index,packet,locale):
    p=c.p
    c.rect(x+7,y+8,w,h,p['ink'],r=15)
    c.rect(x,y,w,h,p['panel'],p['ink'],4,r=15)
    c.rect(x+18,y+16,49,39,p['accent'],p['ink'],2,r=7);c.text(x+29,y+23,str(index+1),25,bold=True)
    c.wrap(x+83,y+23,row['title'],w-110,27,1)
    # A speech bubble is separate from the caption and the visual scene.
    c.rect(x+23,y+76,w-46,99,p['paper'],p['ink'],3,r=18)
    c.poly([(x+94,y+173),(x+120,y+173),(x+98,y+195)],p['paper'],p['ink'],3)
    c.wrap(x+44,y+94,row['bubble'],w-90,25,2)
    scene(c,row['scene'],x+10,y+194,w-20,193)
    yy=y+393
    if row.get('mode')=='check':
        check=next(e for e in packet['evidence'] if e['id']==row['check_id'])
        c.wrap(x+25,yy,check_line(check,locale),w-50,24,1,fill=p['ink']);yy+=38
    c.wrap(x+25,yy,row['caption'],w-50,22,2 if row.get('mode')=='check' and h<590 else 3)
    c.text(x+25,y+h-34,'SOURCE: '+', '.join(row['evidence']),16)


def comic(packet,board,layout='grid',focus=None):
    zh=board['locale']=='zh';theme=board.get('theme','pop')
    if layout=='strip':width=1000;height=2920;positions=[(50,270+i*630,900,590) for i in range(4)]
    else:width=1540;height=1500;positions=[(50+(i%2)*745,270+(i//2)*585,695,545) for i in range(4)]
    c=Canvas(width,height,theme);p=c.p
    c.text(50,35,'CommitComic',45,bold=True)
    c.rect(width-294,40,239,42,p['blue'],p['ink'],3,r=10)
    c.text(width-278,49,'GIT → COMIC',24,bold=True)
    c.wrap(50,111,board['title'],width-100,42,2)
    c.wrap(53,210,board['subtitle'],width-100,24,1)
    for i,pos in enumerate(positions):
        row=board['panels'][i]
        if focus is not None and i>focus:
            row=dict(row,bubble='下一格…' if zh else 'Next panel...',caption='继续看这次更新如何展开。' if zh else 'Continue the story of this change.',mode='summary')
        panel(c,row,*pos,i,packet,board['locale'])
    footer='分镜演绎 · 以证据说明为准 · 非线上效果或用户成绩' if zh else 'Illustrated interpretation · see evidence notes · no production-impact claim'
    c.text(52,height-59,footer,20)
    return c


def card(packet,board):
    c=Canvas(1200,1200,board.get('theme','pop'));p=c.p
    c.text(60,45,'CommitComic',48,bold=True)
    c.rect(60,125,1080,62,p['ink'],r=13);c.text(88,141,'FROM REAL CHANGES TO A SHAREABLE STORY',28,p['paper'],True)
    c.wrap(64,232,board['title'],1070,58,3)
    coder(c,150,506,1.6);note(c,620,490,1.5);bug(c,874,606,.95)
    c.wrap(66,864,board['subtitle'],1060,31,2)
    c.text(67,1014,packet['base'][:8]+' → '+packet['head'][:8],28)
    c.text(67,1083,'原创漫画演绎 / 证据说明随图交付' if board['locale']=='zh' else 'Original comic interpretation / evidence notes included',23)
    return c


def render_bundle(p,b,out,images=False,font=None):
    validate_board(p,b);board,redactions=safe_board(p,b)
    # Validate the redacted copy too, so a quote cannot silently change its source binding.
    validate_board(p,board)
    out=Path(out)
    if out.exists():raise FileExistsError('Use a new output folder; earlier editions are preserved')
    canvases={'comic':comic(p,board),'strip':comic(p,board,'strip'),'card':card(p,board)}
    prepared={}
    if images:
        for name,c in canvases.items():prepared[name]=c.png(font)
    out.mkdir(parents=True)
    files=[]
    for name,c in canvases.items():
        (out/(name+'.svg')).write_text(c.svg(),encoding='utf-8');files.append(name+'.svg')
        if images:prepared[name].save(out/(name+'.png'),optimize=True);files.append(name+'.png')
    if images:
        frames=[comic(p,board,focus=i).png(font).resize((770,750)) for i in range(4)]
        frames[0].save(out/'preview.gif',save_all=True,append_images=frames[1:],duration=[1100,1300,1400,2600],loop=0,optimize=False)
        files.append('preview.gif')
    lines=['# '+md(board['title']),'',md(board['subtitle']),'']
    evidence=['# Evidence notes / 来源说明','',f'Git range: `{p["base"]}..{p["head"]}`',
              '', 'Panel references prove a source link, not semantic faithfulness, deployment or user impact.','']
    for i,row in enumerate(board['panels'],1):
        lines += [f'## {i}. '+md(row['title']),'',md(row['bubble']),'',md(row['caption']),'']
        if row.get('mode')=='check':lines += [check_line(next(e for e in p['evidence'] if e['id']==row['check_id']),board['locale']),'']
        evidence += [f'## Panel {i} / {md(row["mode"] if "mode" in row else "summary")}','', 'Sources: '+', '.join(row['evidence']),'']
        for ref in row['evidence']:
            e=next(e for e in p['evidence'] if e['id']==ref)
            # Four-space indentation keeps arbitrary source text out of Markdown HTML/fences.
            evidence += ['### '+ref,'',md(e.get('path',e.get('label',''))),'']+['    '+line for line in e['text'].splitlines()]+['']
    lines += ['---','','Illustrated interpretation of code evidence; review the scope and evidence notes before posting.']
    (out/'post.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (out/'evidence.md').write_text('\n'.join(evidence)+'\n',encoding='utf-8')
    (out/'alt-text.txt').write_text('\n'.join(f'{i+1}. {r["title"]} — {r["bubble"]} {r["caption"]}' for i,r in enumerate(board['panels']))+'\n',encoding='utf-8')
    files+=['post.md','evidence.md','alt-text.txt']
    hashes={name:__import__('hashlib').sha256((out/name).read_bytes()).hexdigest() for name in files}
    manifest={'format':'commit-comic/1','edition':board['edition'],'packet_sha256':digest(p),'board_sha256':digest(b),
              'render_redactions':redactions,'files':files+['manifest.json'],'artifact_sha256':hashes,'coverage':p['coverage'],
              'boundary':'Source references and common-pattern redaction do not certify semantic truth or public safety. No network publication performed.'}
    (out/'manifest.json').write_text(pretty(manifest),encoding='utf-8')
    return manifest
