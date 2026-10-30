import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
from evidence import (attach_check,check_line,collect,digest,draft,git,load,pretty,record,redact,safe_path,validate_board,write_new)
from art import render_bundle
from reproduce import BEFORE,board,fixture


class ComicChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.out=Path(self.tmp.name);self.repo=self.out/'repo'
        self.base,self.head,self.change=fixture(self.repo)
        self.p=collect(self.repo,self.base,self.head,'MoonNotes')
        self.p=attach_check(self.p,b'Ran 4 tests in 0.001s\n\nOK\n','synthetic fixture')
        self.b=board(self.p,'en')

    def test_collect_real_net_diff_without_author_identity_or_local_paths(self):
        p=self.p
        self.assertEqual(p['coverage']['range_commits'],2)
        self.assertEqual({e['path'] for e in p['evidence'] if e['kind']=='net_diff'},{'notes.py','test_notes.py'})
        raw=pretty(p)
        self.assertNotIn('demo@',raw);self.assertNotIn(str(self.repo),raw)
        self.assertIn('+            return False',raw)

    def test_uncommitted_changes_are_not_mistaken_for_committed_results(self):
        (self.repo/'notes.py').write_text('private uncommitted content',encoding='utf-8')
        before=(self.repo/'notes.py').read_bytes()
        p=collect(self.repo,self.base,self.head)
        self.assertNotIn('private uncommitted content',pretty(p))
        self.assertEqual((self.repo/'notes.py').read_bytes(),before)

    def test_empty_net_diff_cannot_be_presented_as_a_shipped_change(self):
        p=collect(self.repo,self.head,self.head)
        self.assertEqual(p['evidence'],[])
        self.assertTrue(p['coverage']['net_diff_empty'])
        with self.assertRaises(ValueError):draft(p)

    def test_reverted_history_does_not_become_live_feature_evidence(self):
        self.change('revert','--no-edit',self.head)
        self.change('revert','--no-edit',self.head+'^')
        p=collect(self.repo,self.base,'HEAD')
        self.assertEqual(p['coverage']['range_commits'],4)
        self.assertTrue(p['coverage']['net_diff_empty'])
        self.assertEqual(p['evidence'],[])

    def test_sensitive_files_excluded_and_common_contact_patterns_masked(self):
        (self.repo/'.env').write_text('PASSWORD=not-real\n',encoding='utf-8')
        (self.repo/'contact.py').write_text('contact="person@example.org"\n',encoding='utf-8')
        self.change('add','.env','contact.py');self.change('commit','-m','test: collect fixture redaction')
        p=collect(self.repo,self.head,'HEAD')
        self.assertEqual(p['coverage']['excluded_paths'],1)
        self.assertNotIn('not-real',pretty(p));self.assertNotIn('person@example.org',pretty(p))
        self.assertIn('[EMAIL]',pretty(p))

    def test_literal_filename_does_not_expand_pathspec(self):
        (self.repo/'name[1].py').write_text('x=1\n',encoding='utf-8')
        (self.repo/'name1.py').write_text('y=1\n',encoding='utf-8')
        self.change('add','--','name[1].py','name1.py');self.change('commit','-m','test: literal paths')
        p=collect(self.repo,self.head,'HEAD')
        e=next(e for e in p['evidence'] if e['path']=='name[1].py')
        self.assertIn('+x=1',e['text']);self.assertNotIn('+y=1',e['text'])

    def test_rename_has_real_diff_evidence(self):
        self.change('mv','notes.py','renamed.py');self.change('commit','-m','refactor: rename module')
        p=collect(self.repo,self.head,'HEAD')
        self.assertEqual(p['evidence'][0]['path'],'renamed.py')
        self.assertTrue(p['evidence'][0]['status'].startswith('R'))

    def test_large_blob_is_not_read_into_export(self):
        (self.repo/'large.py').write_text('x'*250000,encoding='utf-8')
        self.change('add','large.py');self.change('commit','-m','test: large fixture')
        p=collect(self.repo,self.head,'HEAD')
        self.assertEqual(p['coverage']['excluded_paths'],1);self.assertEqual(p['evidence'],[])

    def test_bounds_are_reported_as_partial_coverage(self):
        p=collect(self.repo,self.base,self.head,max_files=1,max_commits=1)
        self.assertEqual(p['coverage']['included_diffs'],1)
        self.assertEqual(p['coverage']['excluded_paths'],1)
        self.assertEqual(p['coverage']['range_commits'],2)
        self.assertEqual(p['coverage']['included_commits'],1)

    def test_empty_commit_subject_does_not_break_history_pairing(self):
        self.change('commit','--allow-empty','--allow-empty-message','-m','')
        p=collect(self.repo,self.head,'HEAD')
        self.assertEqual(p['commits'][0]['subject'],'(empty subject)')
        self.assertTrue(p['coverage']['net_diff_empty'])

    def test_non_ancestor_range_is_rejected(self):
        with self.assertRaises(ValueError):collect(self.repo,self.head,self.base)

    def test_hash_binding_rejects_board_from_changed_packet(self):
        p=copy.deepcopy(self.p);p['project']='other'
        with self.assertRaises(ValueError):validate_board(p,self.b)

    def test_unknown_evidence_and_unbacked_check_rejected(self):
        b=copy.deepcopy(self.b);b['panels'][0]['evidence']=['missing']
        with self.assertRaises(ValueError):validate_board(self.p,b)
        b=copy.deepcopy(self.b);b['panels'][3]['check_id']='E1'
        with self.assertRaises(ValueError):validate_board(self.p,b)

    def test_quotes_are_literal_but_summaries_are_not_semantically_certified(self):
        b=copy.deepcopy(self.b);b['panels'][0].update(mode='quote',bubble='return False')
        validate_board(self.p,b)
        b['panels'][0]['bubble']='An invented quote'
        with self.assertRaises(ValueError):validate_board(self.p,b)
        b['panels'][0]['mode']='summary';validate_board(self.p,b)

    def test_pass_fail_unknown_and_skips_keep_their_meaning(self):
        passed=attach_check(self.p,b'Ran 5 tests in 0.2s\n\nOK (skipped=1)\n','demo')['evidence'][-1]
        self.assertEqual(passed['status'],'passed');self.assertEqual(passed['count'],5);self.assertEqual(passed['skipped'],1)
        self.assertIn('skipped',check_line(passed,'en'))
        failed=attach_check(self.p,b'Ran 5 tests in 0.2s\n\nFAILED (failures=1)\n','demo')['evidence'][-1]
        self.assertEqual(failed['status'],'failed')
        unknown=attach_check(self.p,b'No test summary, only a commit saying tests pass','demo')['evidence'][-1]
        self.assertEqual(unknown['status'],'unknown')

    def test_multiple_test_summaries_are_not_added_as_one_verified_total(self):
        e=attach_check(self.p,b'Ran 4 tests in 1s\nOK\nRan 7 tests in 2s\nOK\n','combined')['evidence'][-1]
        self.assertEqual(e['status'],'unknown');self.assertEqual(e['count'],0)

    def test_redaction_masks_common_patterns_including_escaped_paths(self):
        samples=['p@example.org','13800138000','ghp_'+'a'*30,'Bearer abcdefghijk123',r'C:\\Users\\Example\\note.txt','password="not-a-real-secret"']
        for value in samples:
            cleaned,count=redact(value);self.assertGreater(count,0);self.assertNotEqual(value,cleaned)

    def test_unsafe_paths_and_urls_are_not_exportable(self):
        for path in ['../secret.py','/home/x.py','.env.prod','secrets/key.py','file\nname.py','private.pem']:
            self.assertFalse(safe_path(path),path)
        with self.assertRaises(ValueError):collect(self.repo,self.base,self.head,url='https://user:password@github.com/x/y')

    def test_svg_is_escaped_self_contained_and_input_is_unchanged(self):
        b=copy.deepcopy(self.b);b['title']='<script>alert(1)</script>'
        original=copy.deepcopy(b);out=self.out/'svg'
        result=render_bundle(self.p,b,out)
        root=ET.fromstring((out/'comic.svg').read_text(encoding='utf-8'))
        self.assertFalse(any(el.tag.endswith('script') or 'href' in el.attrib for el in root.iter()))
        self.assertEqual(b,original)
        self.assertEqual(result,load(out/'manifest.json'))
        for name,sha in result['artifact_sha256'].items():self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(),sha)

    def test_render_refuses_overwrite_and_text_overflow_before_making_output(self):
        out=self.out/'comic';render_bundle(self.p,self.b,out)
        before=(out/'comic.svg').read_bytes()
        with self.assertRaises(FileExistsError):render_bundle(self.p,self.b,out)
        self.assertEqual((out/'comic.svg').read_bytes(),before)
        b=copy.deepcopy(self.b);b['panels'][0]['bubble']='W'*100
        with self.assertRaises(ValueError):render_bundle(self.p,b,self.out/'overflow')
        self.assertFalse((self.out/'overflow').exists())

    def test_ledger_is_idempotent_and_drives_next_range(self):
        ledger=self.out/'editions.json'
        self.assertTrue(record(self.p,self.b,ledger)['added']);before=ledger.read_bytes()
        self.assertFalse(record(self.p,self.b,ledger)['added']);self.assertEqual(ledger.read_bytes(),before)
        (self.repo/'next.py').write_text('next_change=True\n',encoding='utf-8')
        self.change('add','next.py');self.change('commit','-m','feat: next original fixture change')
        p=collect(self.repo,None,'HEAD',ledger=ledger)
        self.assertEqual(p['base'],self.head);self.assertEqual(p['coverage']['range_commits'],1)

    def test_conflicting_edition_and_busy_lock_do_not_change_ledger(self):
        ledger=self.out/'ledger.json';record(self.p,self.b,ledger);before=ledger.read_bytes()
        b=copy.deepcopy(self.b);b['title']='different text'
        with self.assertRaises(ValueError):record(self.p,b,ledger)
        self.assertEqual(ledger.read_bytes(),before)
        lock=ledger.with_name(ledger.name+'.comic.lock');lock.write_text('other writer')
        with self.assertRaises(FileExistsError):record(self.p,self.b,ledger)
        self.assertEqual(lock.read_text(),'other writer')

    def test_other_repository_cannot_use_this_ledger(self):
        ledger=self.out/'ledger.json';record(self.p,self.b,ledger)
        p=copy.deepcopy(self.p);p['repository_id']='0'*64;b=board(p,'en')
        with self.assertRaises(ValueError):record(p,b,ledger)

    def test_real_cli_collect_draft_validate_and_render(self):
        prefix=[sys.executable,'-X','utf8','-B',str(ROOT/'scripts/commitcomic.py')]
        packet=self.out/'cli-packet.json';storyboard=self.out/'cli-board.json'
        calls=[['collect','--repo',self.repo,'--base',self.base,'--head',self.head,'--out',packet],
               ['draft','--packet',packet,'--out',storyboard],
               ['validate','--packet',packet,'--board',storyboard],
               ['render','--packet',packet,'--board',storyboard,'--out',self.out/'cli-comic']]
        for args in calls:
            r=subprocess.run(prefix+list(map(str,args)),capture_output=True,encoding='utf-8')
            self.assertEqual(r.returncode,0,r.stderr)
        self.assertTrue((self.out/'cli-comic/comic.svg').is_file())


if __name__=='__main__':unittest.main()
