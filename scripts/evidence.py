"""Local, read-only Git evidence and bounded storyboard contracts. Standard library only."""
from __future__ import annotations
import copy
import hashlib
import html
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unicodedata
from urllib.parse import urlparse

FORMAT='commit-comic/1'
SCENES={'duplicate','inspect','repair','check','race','snapshot','audio','reuse','artifact','gate','recover',
        'handoff','schedule','fingerprint','audio-check','crash'}
MAX_FILE=240_000
MAX_PACKET=3_000_000
SHA=re.compile(r'[0-9a-f]{40}|[0-9a-f]{64}')


def text(value,limit=500):
    if not isinstance(value,str) or not value.strip() or len(value)>limit:
        raise ValueError(f'Expected non-empty text up to {limit} characters')
    if any(ord(c)<32 and c not in '\n\t' for c in value):raise ValueError('Control characters are not supported')
    return value


def ident(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',value):raise ValueError('Invalid stable ID')
    return value


def number(value,low=0,high=200):
    if isinstance(value,bool) or not isinstance(value,int) or not low<=value<=high:raise ValueError('Invalid integer bound')
    return value


def sha(value):
    if not isinstance(value,str) or not SHA.fullmatch(value):raise ValueError('Invalid Git object ID')
    return value


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def pretty(value):return json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n'


def load(path):
    b=Path(path).read_bytes()
    if len(b)>MAX_PACKET:raise ValueError('Input exceeds 3 MB')
    def reject(v):raise ValueError('Non-finite numbers are not allowed')
    value=json.loads(b.decode('utf-8-sig'),parse_constant=reject)
    if not isinstance(value,dict):raise ValueError('Input must be a JSON object')
    return value


def write_new(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:f.write(pretty(value))


def redact(value):
    """Best-effort common pattern masking, not certification for public disclosure."""
    rules=[(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b','[EMAIL]'),
           (r'(?<![\w])1[3-9]\d{9}(?![\w])','[PHONE]'),
           (r'(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,}|sk-[A-Za-z0-9_-]{16,})','[TOKEN]'),
           (r'(?i)(\b(?:api[_-]?key|password|secret|access[_-]?token)\s*[=:]\s*)[\"\'][^\"\'\r\n]{4,}[\"\']',r'\1"[SECRET]"'),
           (r'(?i)\bBearer\s+[A-Za-z0-9._~+/-]{8,}','Bearer [TOKEN]'),
           (r'(?i)[A-Z]:[\\/]+(?:Users|Documents and Settings)[\\/]+[^\s\"\'<>]+','[LOCAL_PATH]'),
           (r'/(?:Users|home)/[^\s\"\'<>]+','[LOCAL_PATH]'),
           (r'https?://[^\s/]+:[^\s/@]+@[^\s]+','[CREDENTIAL_URL]')]
    total=0
    for pattern,replacement in rules:
        value,n=re.subn(pattern,replacement,value);total+=n
    return value,total


def safe_path(path):
    path=path.replace('\\','/')
    if any(ord(c)<32 for c in path):return False
    parts=path.split('/')
    if path.startswith('/') or any(p in {'..',''} for p in parts) or re.match(r'^[A-Za-z]:',path):return False
    lower=path.lower()
    denied={'secrets','credentials','secrets.json','credentials.json','id_rsa','id_ed25519','.ssh','.aws','.git','node_modules','vendor'}
    if any(p.lower() in denied for p in parts):return False
    if any(p.lower()=='.env' or p.lower().startswith('.env.') for p in parts):return False
    if lower.endswith(('.pem','.key','.p12','.pfx','.pdf','.docx','.csv','.xlsx','.ipynb','.log')):return False
    return True


def project_url(value):
    if not value:return None
    p=urlparse(value)
    if p.scheme!='https' or p.netloc!='github.com' or p.query or p.fragment or not re.fullmatch(r'/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?',p.path):
        raise ValueError('Optional project URL must be a plain https://github.com/owner/repo URL')
    return value.rstrip('/')


def git(repo,*args,limit=2_000_000):
    env=dict(os.environ);env.update(GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1')
    cmd=['git','--no-pager','--literal-pathspecs','-c','core.quotePath=false','-c','diff.external=', '-C',str(repo),*args]
    try:r=subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=30)
    except subprocess.TimeoutExpired:raise ValueError('Git read timed out; narrow the range') from None
    if r.returncode:raise ValueError('Git read failed: '+redact(r.stderr.decode('utf-8',errors='replace'))[0][:250])
    if len(r.stdout)>limit:raise ValueError('Git metadata output exceeds collection limit; narrow the range')
    return r.stdout


def resolve(repo,ref):
    text(ref,200)
    return sha(git(repo,'rev-parse','--verify','--end-of-options',ref+'^{commit}').decode().strip())


def changes(raw):
    fields=raw.decode('utf-8',errors='replace').split('\0');result=[];i=0
    while i<len(fields) and fields[i]:
        status=fields[i];i+=1
        if i>=len(fields):raise ValueError('Incomplete Git path output')
        path=fields[i];i+=1
        old=None
        if status.startswith(('R','C')):
            old=path
            if i>=len(fields):raise ValueError('Incomplete rename output')
            path=fields[i];i+=1
        result.append((status,path,old))
    return result


def blob_info(repo,ref,path):
    raw=git(repo,'ls-tree','-l',ref,'--',path).decode('utf-8',errors='replace')
    if not raw:return None
    header=raw.split('\t',1)[0].split()
    if len(header)!=4 or header[0]!='100644' and header[0]!='100755' or header[1]!='blob':return {'skip':True}
    return {'oid':header[2],'size':int(header[3])}


def collect(repo,base,head,project='Project update',url=None,max_commits=60,max_files=30,ledger=None):
    number(max_commits,1,200);number(max_files,1,60);text(project,80)
    url=project_url(url);head=resolve(repo,head)
    roots=git(repo,'rev-list','--max-parents=0',head).decode().splitlines()
    repository_id=digest(sorted(roots))
    if ledger:
        old=load(ledger)
        if old.get('format')!=FORMAT or old['repository_id']!=repository_id:raise ValueError('Ledger belongs to another repository')
        if base is None:base=old['last_head']
    if not base:raise ValueError('Supply --base for the first edition; later editions may use --ledger')
    base=resolve(repo,base)
    git(repo,'merge-base','--is-ancestor',base,head)
    count=int(git(repo,'rev-list','--count',base+'..'+head).decode().strip())
    log=git(repo,'log','--no-show-signature','--reverse','--topo-order','--format=%H%x00%s%x00',base+'..'+head).decode('utf-8',errors='replace')
    fields=[x.strip('\r\n') for x in log.split('\0')]
    if fields and not fields[-1]:fields.pop()
    if len(fields)%2:raise ValueError('Incomplete Git log output')
    commits=[];redactions=0
    for i in range(0,min(len(fields),max_commits*2),2):
        subject,n=redact(fields[i+1] or '(empty subject)');redactions+=n
        commits.append({'sha':sha(fields[i]),'subject':subject[:250]})
    changed=changes(git(repo,'diff','--no-ext-diff','--no-textconv','--name-status','-z','-M',base,head,'--'))
    evidence=[];excluded=0;truncated=0
    for status,path,old_path in changed:
        if len(evidence)>=max_files or not safe_path(path) or old_path and not safe_path(old_path):excluded+=1;continue
        infos=[blob_info(repo,r,p) for r,p in [(base,old_path or path),(head,path)]]
        if any(info and (info.get('skip') or info['size']>MAX_FILE) for info in infos):excluded+=1;continue
        args=[p for p in [old_path,path] if p]
        patch=git(repo,'diff','--no-ext-diff','--no-textconv','--unified=3',base,head,'--',*dict.fromkeys(args),limit=MAX_FILE*3)
        if b'\0' in patch or patch.startswith(b'Binary files ') or b'\nBinary files ' in patch:excluded+=1;continue
        decoded=patch.decode('utf-8',errors='replace')
        decoded,n=redact(decoded);redactions+=n
        lines=decoded.splitlines();cut=len(lines)>90 or len(decoded)>10000
        excerpt='\n'.join(lines[:90])[:10000]
        clean_path,n=redact(path);redactions+=n
        if clean_path!=path:excluded+=1;continue
        if cut:truncated+=1
        evidence.append({'id':f'E{len(evidence)+1}','kind':'net_diff','path':clean_path,'status':status,
                         'base':base,'head':head,'text':excerpt,'truncated':cut,
                         'source':'Git base..head net diff; commit subjects are intent, not deployment proof'})
    result={'format':FORMAT,'project':redact(project)[0],'project_url':url,'repository_id':repository_id,
            'base':base,'head':head,'commits':commits,'evidence':evidence,
            'coverage':{'range_commits':count,'included_commits':len(commits),'changed_paths':len(changed),
                        'included_diffs':len(evidence),'excluded_paths':excluded,'truncated_diffs':truncated,
                        'common_pattern_redactions':redactions,'net_diff_empty':not changed},
            'basis':'Read-only local Git collection. No authors, emails, remotes or working-tree changes collected. Masking is best effort, not public-disclosure certification.'}
    validate_packet(result)
    return result


def validate_packet(p):
    if p.get('format')!=FORMAT:raise ValueError('Unsupported packet format')
    text(p['project'],80);sha(p['base']);sha(p['head']);project_url(p.get('project_url'))
    if not re.fullmatch(r'[0-9a-f]{64}',p['repository_id']):raise ValueError('Invalid repository binding')
    seen=set()
    for e in p['evidence']:
        ident(e['id'])
        if e['id'] in seen:raise ValueError('Duplicate evidence ID')
        seen.add(e['id']);text(e['text'],15000)
        if e['kind'] not in {'net_diff','check','record'}:raise ValueError('Unknown evidence kind')
        if e.get('source_url'):
            u=urlparse(e['source_url'])
            if u.scheme!='https' or u.netloc!='github.com' or u.query or u.fragment:
                raise ValueError('Source URL must be a plain GitHub source link')
            root=p.get('project_url')
            if not root or not e['source_url'].startswith(root+'/'):
                raise ValueError('Source URL must belong to the selected project')
            if not re.fullmatch(r'/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(?:blob|commit)/[0-9a-f]{40}(?:/[A-Za-z0-9_./-]+)?',u.path):
                raise ValueError('Source URL must pin a commit or file to a full SHA')
        if e['kind']=='net_diff':
            if e['base']!=p['base'] or e['head']!=p['head'] or not safe_path(e['path']):raise ValueError('Diff outside packet range')
        elif e['kind']=='record':
            if e['ref']!=p['head'] or not safe_path(e['path']) or not e.get('source_url'):
                raise ValueError('Frozen record needs a safe path and pinned source at packet head')
            if not re.fullmatch(r'[0-9a-f]{64}',e['file_sha256']):raise ValueError('Invalid source-file hash')
        else:
            text(e['label'],80)
            if e['status'] not in {'passed','failed','unknown'}:raise ValueError('Unknown check status')
            number(e['count'],0,1000000)
    return p


def attach_check(p,raw,label):
    validate_packet(p);text(label,80)
    if len(raw)>1_000_000:raise ValueError('Check log exceeds 1 MB')
    value=raw.decode('utf-8-sig',errors='replace')
    # Read summaries only; never execute user-supplied commands or logs.
    units=re.findall(r'^Ran (\d+) tests? in .+$',value,re.M)
    unit=units[0] if len(units)==1 else None
    ok=bool(re.search(r'^OK(?: \([^\n]*\))?\s*$',value,re.M))
    failure=bool(re.search(r'^(?:FAILED|ERROR:|FAIL:)',value,re.M))
    count=int(unit) if unit else 0
    skipped_match=re.search(r'\bskipped=(\d+)',value)
    skipped=int(skipped_match.group(1)) if skipped_match else 0
    if skipped>count:skipped=0;unit=None
    status='failed' if failure else 'passed' if unit and ok else 'unknown'
    summary=f'{count} tests run; suite {status}; {skipped} skipped; supplied log, scope: {label}'
    result=copy.deepcopy(p);ids={e['id'] for e in result['evidence']};n=1
    while f'C{n}' in ids:n+=1
    result['evidence'].append({'id':f'C{n}','kind':'check','label':redact(label)[0],
                              'status':status,'count':count,'skipped':skipped,'text':redact(summary)[0],
                              'log_sha256':hashlib.sha256(raw).hexdigest(),
                              'source':'Supplied unittest summary; no claim that this tool executed the test or verified the environment'})
    validate_packet(result);return result


def validate_board(p,b):
    validate_packet(p)
    if b.get('format')!=FORMAT or b['packet_sha256']!=digest(p):raise ValueError('Storyboard does not match this exact evidence packet')
    ident(b['edition']);text(b['title'],70);text(b['subtitle'],150)
    if b['locale'] not in {'zh','en'}:raise ValueError('locale must be zh or en')
    if b.get('theme','pop') not in {'pop','night'}:raise ValueError('Unknown theme')
    if not isinstance(b['panels'],list) or len(b['panels'])!=4:raise ValueError('This format uses four panels')
    known={e['id']:e for e in p['evidence']}
    for index,panel in enumerate(b['panels']):
        if panel['beat']!=['problem','clue','change','result'][index]:raise ValueError('Use problem, clue, change, result in order')
        text(panel['title'],40);text(panel['bubble'],100);text(panel['caption'],180)
        if panel.get('scene') not in SCENES:raise ValueError('Unknown original scene')
        refs=panel['evidence']
        if not isinstance(refs,list) or not refs or any(e not in known for e in refs):raise ValueError('Each panel needs existing evidence references')
        if panel.get('mode','summary') not in {'summary','quote','check'}:raise ValueError('Unknown claim mode')
        if panel.get('mode')=='quote' and not any(panel['bubble'] in known[e]['text'] for e in refs):raise ValueError('Quoted speech must appear literally in cited evidence')
        if panel.get('mode')=='check':
            check=known.get(panel.get('check_id'))
            if not check or check['id'] not in refs or check['kind']!='check':raise ValueError('Check panel needs a cited check record')
    return b


def draft(p,locale='en',edition='edition-1'):
    validate_packet(p);ident(edition)
    if not p['evidence']:raise ValueError('No net diff or supplied check evidence: no shipped-change comic can be drafted')
    first=p['evidence'][0]['id'];check=next((e for e in p['evidence'] if e['kind']=='check'),None)
    zh=locale=='zh'
    titles=['发生了什么','找到线索','改了哪里','结果与边界'] if zh else ['What happened?','Follow the evidence','What changed?','Result and limits']
    bubbles=['先看真实差异。','提交标题只是线索。','把变化讲给人听。','有记录，才写结果。'] if zh else ['Start with the real diff.','A title is only a lead.','Explain the change.','Only report supported results.']
    captions=['从指定Git范围提取净差异，先挑一个有意义的变化。','读上下文，确认问题和本次改动之间的关系。','Agent在证据支持的范围内改写这份分镜。','没有检查记录时，不写“测试通过”或效果提升。'] if zh else ['Choose one meaningful change in this Git range.','Read the surrounding diff before claiming a cause.','The Agent adapts this storyboard to the actual evidence.','Without a check record, do not claim tests passed or metrics improved.']
    panels=[]
    for i in range(4):
        panel={'beat':['problem','clue','change','result'][i],'title':titles[i],'bubble':bubbles[i],
               'caption':captions[i],'scene':['duplicate','inspect','repair','check'][i],'evidence':[check['id'] if i==3 and check else first],'mode':'summary'}
        if i==3 and check:panel.update(mode='check',check_id=check['id'])
        panels.append(panel)
    return {'format':FORMAT,'packet_sha256':digest(p),'edition':edition,'locale':locale,'theme':'pop',
            'title':p['project'],'subtitle':'有依据的开发小剧场' if zh else 'A development story with traceable sources',
            'panels':panels,'notice':'这是一份待Agent按实际差异改写的分镜起点。' if zh else 'Starting storyboard: adapt the words to the actual diff before sharing.'}


def check_line(e,locale):
    extra=f' / 跳过{e.get("skipped",0)}项' if e.get('skipped') else ''
    if locale=='zh':return f'运行{e["count"]}项 / 检查'+{'passed':'通过','failed':'失败','unknown':'状态未知'}[e['status']]+extra
    return f'{e["count"]} run / suite {e["status"]}'+(f' / {e["skipped"]} skipped' if e.get('skipped') else '')


def safe_board(p,b):
    validate_board(p,b);result=copy.deepcopy(b);count=0
    for container,keys in [(result,['title','subtitle','notice'])]+[(row,['title','bubble','caption']) for row in result['panels']]:
        for key in keys:
            if container.get(key):container[key],n=redact(container[key]);count+=n
    return result,count


def record(p,b,path):
    validate_board(p,b);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    lock=path.with_name(path.name+'.comic.lock');tmp=None
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        os.close(fd)
        data=load(path) if path.exists() else {'format':FORMAT,'repository_id':p['repository_id'],'last_head':p['base'],'editions':[]}
        if data['format']!=FORMAT or data['repository_id']!=p['repository_id']:raise ValueError('Ledger belongs to another repository')
        row={'edition':b['edition'],'packet_sha256':digest(p),'board_sha256':digest(b),'base':p['base'],'head':p['head']}
        previous=next((x for x in data['editions'] if x['edition']==b['edition']),None)
        if previous:
            if previous!=row:raise ValueError('Edition ID already refers to different content')
            return {'added':False,'editions':len(data['editions'])}
        if data['editions'] and p['base']!=data['last_head']:raise ValueError('Edition does not continue the last recorded range')
        data['editions'].append(row);data['last_head']=p['head']
        with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,prefix='.comic-',suffix='.tmp',delete=False) as f:
            tmp=Path(f.name);f.write(pretty(data));f.flush();os.fsync(f.fileno())
        os.replace(tmp,path);tmp=None
        return {'added':True,'editions':len(data['editions'])}
    finally:
        if tmp:tmp.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)


def md(value):return html.escape(str(value)).replace('|','\\|').replace('\n',' ')
