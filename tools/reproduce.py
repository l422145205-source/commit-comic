#!/usr/bin/env python3
"""Create an original synthetic Git demo and execute the complete CommitComic tool workflow."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from evidence import FORMAT,attach_check,collect,digest,git,pretty,record,validate_board,write_new
from art import render_bundle

BEFORE='''def import_note(notes, event_id, content):
    notes.append({"id": event_id, "content": content})
    return True
'''
AFTER='''def import_note(notes, event_id, content):
    if not event_id:
        raise ValueError("An event ID is required")
    for note in notes:
        if note["id"] == event_id:
            if note["content"] != content:
                raise ValueError("Conflicting content for the same event")
            return False
    notes.append({"id": event_id, "content": content})
    return True
'''
TESTS='''import unittest
from notes import import_note

class NoteChecks(unittest.TestCase):
    def test_same_event_is_idempotent(self):
        notes=[]
        self.assertTrue(import_note(notes,"e1","hello"))
        self.assertFalse(import_note(notes,"e1","hello"))
        self.assertEqual(len(notes),1)
    def test_conflict_keeps_existing_content(self):
        notes=[]; import_note(notes,"e1","hello")
        with self.assertRaises(ValueError): import_note(notes,"e1","changed")
        self.assertEqual(notes[0]["content"],"hello")
    def test_same_text_new_event_is_not_a_duplicate(self):
        notes=[]
        import_note(notes,"e1","hello"); import_note(notes,"e2","hello")
        self.assertEqual(len(notes),2)
    def test_missing_id_is_rejected(self):
        with self.assertRaises(ValueError):import_note([],"","hello")

if __name__=="__main__":unittest.main()
'''


def fixture(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ);env.update(GIT_AUTHOR_NAME='CommitComic Demo',GIT_AUTHOR_EMAIL='demo@users.noreply.github.com',
                                   GIT_COMMITTER_NAME='CommitComic Demo',GIT_COMMITTER_EMAIL='demo@users.noreply.github.com',
                                   GIT_AUTHOR_DATE='2026-10-30T00:00:00+00:00',GIT_COMMITTER_DATE='2026-10-30T00:00:00+00:00')
    def change(*args):
        subprocess.run(['git','-c','core.autocrlf=false','-c','commit.gpgsign=false','-c','core.hooksPath=/dev/null','-C',str(out),*args],
                       env=env,check=True,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    change('init','--initial-branch=main')
    (out/'notes.py').write_text(BEFORE,encoding='utf-8',newline='\n')
    change('add','notes.py');change('commit','-m','feat: add note import')
    base=git(out,'rev-parse','HEAD').decode().strip()
    (out/'notes.py').write_text(AFTER,encoding='utf-8',newline='\n')
    change('add','notes.py');change('commit','-m','fix: keep repeated note events idempotent')
    (out/'test_notes.py').write_text(TESTS,encoding='utf-8',newline='\n')
    change('add','test_notes.py');change('commit','-m','test: cover replay conflict and distinct events')
    head=git(out,'rev-parse','HEAD').decode().strip()
    return base,head,change


def board(packet,locale):
    diff=next(e['id'] for e in packet['evidence'] if e.get('path')=='notes.py')
    check=next(e['id'] for e in packet['evidence'] if e['kind']=='check')
    zh=locale=='zh'
    titles=['事故现场','找到线索','动手修复','结果与边界'] if zh else ['Double trouble','Follow the clue','Patch the replay','Result and limits']
    bubbles=['我只是重试了一次！','同一件事，要有同一个ID。','内容变了？先停，别覆盖。','让测试也来作证。'] if zh else ['I only clicked retry!','Same event. Same ID.','Changed content? Stop.','Let the checks speak.']
    captions=['旧版直接追加，重复导入会多一张便签。','相同文字也可能是两次不同事件，不能只按文字去重。','相同ID同内容跳过；相同ID异内容报错，保留原文。','仅原创合成演示仓库的本地检查；不代表线上效果。'] if zh else ['The previous importer appended a second note on replay.','Two distinct events can share text; text alone is not an event ID.','Same ID and content: skip. Conflicting content: reject and preserve the note.','Local checks on this original demo fixture; no production-impact claim.']
    return {'format':FORMAT,'packet_sha256':digest(packet),'edition':'demo-zh' if zh else 'demo-en','locale':locale,'theme':'pop',
            'title':'点一次，怎么长出两张便签？' if zh else 'One retry. Two notes. What happened?',
            'subtitle':'MoonNotes / 一次有据可查的修复小剧场' if zh else 'MoonNotes / a repair story with traceable evidence',
            'notice':'原创虚构Git演示，实际运行工具产物。' if zh else 'Original synthetic Git demo; actual tool outputs.',
            'panels':[dict(beat=['problem','clue','change','result'][i],title=titles[i],bubble=bubbles[i],caption=captions[i],
                           scene=['duplicate','inspect','repair','check'][i],evidence=[check if i==3 else diff],
                           **({'mode':'check','check_id':check} if i==3 else {'mode':'summary'})) for i in range(4)]}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--locale',choices=['en','zh','both'],default='en');p.add_argument('--images',action='store_true');p.add_argument('--font',type=Path)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    repo=out/'fixture';base,head,_=fixture(repo)
    packet=collect(repo,base,head,'MoonNotes demo')
    log=subprocess.run([sys.executable,'-B','-m','unittest','-q'],cwd=repo,capture_output=True,check=True).stderr
    (out/'demo-check.log').write_bytes(log)
    packet=attach_check(packet,log,'original synthetic MoonNotes fixture')
    write_new(out/'packet.json',packet)
    locales=['en','zh'] if a.locale=='both' else [a.locale]
    for locale in locales:
        b=board(packet,locale);validate_board(packet,b);write_new(out/f'board.{locale}.json',b)
        render_bundle(packet,b,out/locale,a.images,a.font)
    b=board(packet,locales[0]);first=record(packet,b,out/'editions.json');again=record(packet,b,out/'editions.json')
    result={'basis':'Original synthetic Git fixture, real four-test execution and real render tools; no online-user or Agent performance results.',
            'commit_range':{'base':base,'head':head},'net_diff_evidence':len([e for e in packet['evidence'] if e['kind']=='net_diff']),
            'fixture_tests_reported':packet['evidence'][-1]['count'],'suite_status':packet['evidence'][-1]['status'],
            'first_record_added':first['added'],'repeated_record_added':again['added'],'locales':locales}
    write_new(out/'verification.json',result);print(pretty(result),end='')


if __name__=='__main__':main()
