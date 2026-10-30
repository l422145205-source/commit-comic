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
sys.path.insert(0,str(ROOT/'scripts'))
from demo import CASES,run_demo
from evidence import digest,load,validate_board,validate_packet

class BundledCases(unittest.TestCase):
    def test_every_bundled_language_renders_from_a_different_working_directory(self):
        with tempfile.TemporaryDirectory() as td:
            for case in CASES:
                for lang in ['en','zh']:
                    out=Path(td)/case/lang;run_demo(case,lang,out)
                    svg=ET.parse(out/'comic.svg')
                    self.assertFalse(any(node.text in {'.',',','。','，'} for node in svg.iter('{http://www.w3.org/2000/svg}text')),
                                     'A sentence-ending mark should not occupy its own line')
                    manifest=load(out/'manifest.json')
                    for name,sha in manifest['artifact_sha256'].items():
                        self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(),sha)
            r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/commitcomic.py'),'demo','--case','one-line-edit','--out','fresh'],
                             cwd=td,capture_output=True,check=True)
            self.assertIn('historical checks were not rerun',r.stdout.decode())
            self.assertTrue((Path(td)/'fresh/comic.svg').is_file())

    def test_record_cannot_borrow_another_repository_or_ref(self):
        original=load(ROOT/'assets/cases/one-line-edit/packet.json')
        for field,value in [('ref','0'*40),('source_url','https://github.com/other/repo/blob/'+'0'*40+'/report.json'),
                            ('source_url','https://github.com/l422145205-source/voxstage/blob/main/report.json'),
                            ('source_url','https://github.com/l422145205-source/voxstage/blob/'+'0'*40+'/reports/production_pilot.json'),
                            ('path','reports/another.json'),
                            ('file_sha256','invalid')]:
            packet=copy.deepcopy(original);packet['evidence'][-1][field]=value
            with self.assertRaises(ValueError):validate_packet(packet)

    def test_real_cases_have_no_invented_unittest_summary_and_remain_bound(self):
        for case in CASES[:-1]:
            packet=load(ROOT/'assets/cases'/case/'packet.json')
            self.assertNotIn('check',{e['kind'] for e in packet['evidence']})
            for lang in ['en','zh']:
                board=load(ROOT/'assets/cases'/case/f'board.{lang}.json')
                validate_board(packet,board)
                board['packet_sha256']='0'*64
                with self.assertRaises(ValueError):validate_board(packet,board)
        record=load(ROOT/'assets/cases/one-line-edit/packet.json')['evidence'][-1]
        selected=json.loads(record['text'])
        self.assertEqual(selected['changed_cue_ids'],['s01'])
        self.assertEqual(selected['stats']['tts_calls'],1)
        self.assertEqual(selected['stats']['tts_cache_hits'],3)

    def test_demo_rejects_unknown_cases_and_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'render';run_demo('completion-race','en',out)
            before=(out/'comic.svg').read_bytes()
            with self.assertRaises(FileExistsError):run_demo('completion-race','en',out)
            self.assertEqual((out/'comic.svg').read_bytes(),before)
            with self.assertRaises(ValueError):run_demo('../other','en',Path(td)/'outside')

if __name__=='__main__':unittest.main()
