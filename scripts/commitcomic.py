#!/usr/bin/env python3
"""CommitComic — collect Git evidence, author a storyboard and export an original comic."""
import argparse
from pathlib import Path
from evidence import attach_check,collect,draft,load,pretty,record,validate_board,write_new


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('collect');c.add_argument('--repo',type=Path,required=True);c.add_argument('--base');c.add_argument('--head',default='HEAD')
    c.add_argument('--project',default='Project update');c.add_argument('--project-url');c.add_argument('--ledger',type=Path)
    c.add_argument('--max-commits',type=int,default=60);c.add_argument('--max-files',type=int,default=30);c.add_argument('--out',type=Path,required=True)
    c=sub.add_parser('attach-check');c.add_argument('--packet',type=Path,required=True);c.add_argument('--log',type=Path,required=True);c.add_argument('--label',required=True);c.add_argument('--out',type=Path,required=True)
    c=sub.add_parser('draft');c.add_argument('--packet',type=Path,required=True);c.add_argument('--locale',choices=['zh','en'],default='en');c.add_argument('--edition',default='edition-1');c.add_argument('--out',type=Path,required=True)
    for name in ['validate','render','record']:
        c=sub.add_parser(name);c.add_argument('--packet',type=Path,required=True);c.add_argument('--board',type=Path,required=True)
        if name=='render':c.add_argument('--out',type=Path,required=True);c.add_argument('--images',action='store_true');c.add_argument('--font',type=Path)
        if name=='record':c.add_argument('--ledger',type=Path,required=True)
    a=p.parse_args()
    try:
        if a.command=='collect':value=collect(a.repo,a.base,a.head,a.project,a.project_url,a.max_commits,a.max_files,a.ledger);write_new(a.out,value);value={'evidence':len(value['evidence']),'coverage':value['coverage']}
        elif a.command=='attach-check':
            if a.log.stat().st_size>1_000_000:raise ValueError('Check log exceeds 1 MB')
            value=attach_check(load(a.packet),a.log.read_bytes(),a.label);write_new(a.out,value);value={'check':value['evidence'][-1]}
        elif a.command=='draft':value=draft(load(a.packet),a.locale,a.edition);write_new(a.out,value);value={'storyboard':'created; adapt text to the actual evidence before sharing'}
        else:
            packet=load(a.packet);board=load(a.board);validate_board(packet,board)
            if a.command=='validate':value={'valid':True,'semantic_faithfulness':'requires Agent/source review'}
            elif a.command=='record':value=record(packet,board,a.ledger)
            else:
                from art import render_bundle
                value=render_bundle(packet,board,a.out,a.images,a.font)
        print(pretty(value),end='')
    except (ValueError,KeyError,TypeError,OSError,ImportError,TimeoutError) as e:p.error(str(e))


if __name__=='__main__':main()
