#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Assemble TIWARI-8 source into 4096 16-bit program words."""
import argparse
from pathlib import Path
OPS={name:i<<12 for i,name in enumerate('SYS LDI LDB LDA STA ADD SUB AND OR XOR JMP JZ JC IN OUT JNZ'.split())}
SPECIAL={'NOP':0,'HLT':1,'SHL':2,'SHR':3,'MOVAB':4,'MOVBA':5,'NOT':6}
ARG=set('LDI LDB LDA STA JMP JZ JC IN OUT JNZ'.split())
BRANCH=set('JMP JZ JC JNZ'.split())

def assemble(source):
    symbols={}; rows=[]; addr=0
    def number(token):
        return symbols[token] if token in symbols else int(token,0)
    for lineno,line in enumerate(source.splitlines(),1):
        line=line.split(';',1)[0].strip()
        if not line: continue
        if line.upper().startswith('.EQU '):
            fields=line.split()
            if len(fields)!=3 or not fields[1].isidentifier() or fields[1] in symbols:
                raise ValueError(f'line {lineno}: invalid constant')
            symbols[fields[1]]=number(fields[2]); continue
        if ':' in line:
            label,line=(x.strip() for x in line.split(':',1))
            if not label.isidentifier() or label in symbols: raise ValueError(f'line {lineno}: invalid/duplicate label')
            symbols[label]=addr
        if not line: continue
        fields=line.split(); name=fields[0].upper()
        if name not in (OPS.keys()|SPECIAL.keys())-{'SYS'} or len(fields)!=(2 if name in ARG else 1):
            raise ValueError(f'line {lineno}: invalid instruction or operand count')
        if addr>=4096: raise ValueError('program exceeds 4096 words')
        rows.append((lineno,name,fields[1:])); addr+=1
    output=[]
    for lineno,name,args in rows:
        if name in SPECIAL: output.append(SPECIAL[name]); continue
        try: value=number(args[0]) if args else 0
        except ValueError as exc: raise ValueError(f'line {lineno}: unknown label or number') from exc
        if not 0<=value<(4096 if name in BRANCH else 256): raise ValueError(f'line {lineno}: operand out of range')
        output.append(OPS[name]|value)
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
    try: words=assemble(args.source.read_text())
    except ValueError as exc: p.error(str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(''.join(f'{word:04x}\n' for word in words+[1]*(4096-len(words))))
    print(f'Assembled {len(words)} words ({2*len(words)} bytes) -> {args.output}')
