"""Render the bundled real-project stories; do not rerun their historical experiments."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from demo import run_demo

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--locale',choices=['en','zh','both'],default='en');p.add_argument('--images',action='store_true')
    p.add_argument('--font',type=Path);a=p.parse_args()
    if a.out.exists():p.error('Use a new output directory')
    for case in ['completion-race','one-line-edit','publish-gap']:
        for lang in ['en','zh'] if a.locale=='both' else [a.locale]:
            run_demo(case,lang,a.out/case/lang,a.images,a.font)
    print('Rendered reviewed stories. Historical source projects/models were not rerun.')

if __name__=='__main__':main()
