"""Render a bundled reviewed example without Git, network or source-project dependencies."""
from pathlib import Path
from evidence import load
from art import render_bundle

ROOT=Path(__file__).resolve().parents[1]
CASES=('completion-race','one-line-edit','publish-gap','moonnotes')

def run_demo(case,locale,out,images=False,font=None):
    if case not in CASES:raise ValueError('Unknown bundled case')
    if locale not in {'zh','en'}:raise ValueError('Unknown example language')
    if case=='moonnotes':
        packet=ROOT/'assets/packet.example.json';board=ROOT/f'assets/board.{locale}.example.json'
    else:
        packet=ROOT/'assets/cases'/case/'packet.json';board=packet.parent/f'board.{locale}.json'
    result=render_bundle(load(packet),load(board),out,images,font)
    return {'case':case,'locale':locale,'output':str(out),'files':result['files'],
            'scope':'Render of a bundled reviewed storyboard. Source projects, models and historical checks were not rerun.'}
