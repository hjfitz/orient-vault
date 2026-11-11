import re,sys,subprocess
pat=re.compile(r'<<<<<<< [^\n]*\n(.*?)=======\n(.*?)>>>>>>> [^\n]*\n', re.S)
def union(a,b):
    out=list(a)
    for x in b:
        if x not in out: out.append(x)
    return out
def merge_line(o,t):
    # o = ours (HEAD), t = theirs (main); both single lines
    if re.match(r"^\s*\['", t) or re.match(r'^\s*- \{ app:', t) or 'app.use(' in t or re.search(r'port \d+$', t) or re.match(r'^(const|import) ', t):
        return t+'\n'+o
    m1=re.match(r'^(.*\[)(.*)(\].*)$',t); m2=re.match(r'^(.*\[)(.*)(\].*)$',o)
    if m1 and m2:
        ti=[x.strip() for x in m1.group(2).split(',')]; oi=[x.strip() for x in m2.group(2).split(',')]
        tail=[x for x in ti if x=='mock-edge']; ti=[x for x in ti if x!='mock-edge']; oi=[x for x in oi if x!='mock-edge']
        return m1.group(1)+', '.join(union(ti,oi)+tail)+m1.group(3)
    m1=re.match(r'^(.*\{ )(.*)( \}.*)$',t); m2=re.match(r'^(.*\{ )(.*)( \}.*)$',o)
    if m1 and m2:
        return m1.group(1)+', '.join(union([x.strip() for x in m1.group(2).split(',')],[x.strip() for x in m2.group(2).split(',')]))+m1.group(3)
    if 'pnpm smoke' in t:
        tt=re.findall(r'[A-Z0-9_]+_URL=https://…',t); ot=re.findall(r'[A-Z0-9_]+_URL=https://…',o)
        new=' '.join(union(tt,ot)); return re.sub(r'(?:[A-Z0-9_]+_URL=https://… )+', new+' ', t, count=1)
    m1=re.search(r'\((`[^)]*`)\)',t); m2=re.search(r'\((`[^)]*`)\)',o)
    if m1 and m2:
        items=union([x.strip() for x in m1.group(1).split(',')],[x.strip() for x in m2.group(1).split(',')])
        return t[:m1.start(1)]+', '.join(items)+t[m1.end(1):]
    m1=re.search(r'upstream: (/[^(]*) \(port',t); m2=re.search(r'upstream: (/[^(]*) \(port',o)
    if m1 and m2:
        items=union([x.strip() for x in m1.group(1).split(',')],[x.strip() for x in m2.group(1).split(',')])
        return t[:m1.start(1)]+', '.join(items)+t[m1.end(1):]
    m1=re.search(r"carrier proxies: (.*?)\. ",t); m2=re.search(r"carrier proxies: (.*?)\. ",o)
    if m1 and m2:
        sp=lambda s:[x.strip() for x in re.split(r', | and ',s)]
        items=union(sp(m1.group(1)),sp(m2.group(1)))
        return t[:m1.start(1)]+', '.join(items[:-1])+' and '+items[-1]+t[m1.end(1):]
    return t+'\n'+o
def resolve(o,t):
    ol=o.splitlines(True); tl=t.splitlines(True)
    if len(ol)==1 and len(tl)==1:
        return merge_line(ol[0].rstrip('\n'),tl[0].rstrip('\n'))+'\n'
    # README table: merge mock-upstreams rows
    up_t=[l for l in tl if 'apps/mock-upstreams' in l]; up_o=[l for l in ol if 'apps/mock-upstreams' in l]
    if up_t and up_o:
        rows=[l for l in tl if l not in up_t]+[l for l in ol if l not in up_o]
        mt=re.search(r'\| ([^|]*) APIs \|',up_t[0]); mo=re.search(r'\| ([^|]*) APIs \|',up_o[0])
        sp=lambda s:[x.strip() for x in re.split(r', (?![^()]*\))| and ',s)]
        items=union(sp(mt.group(1)),sp(mo.group(1)))
        return ''.join(rows)+up_t[0][:mt.start(1)]+', '.join(items[:-1])+' and '+items[-1]+up_t[0][mt.end(1):]
    return t+o
for p in sys.argv[1:]:
    s=open(p).read()
    s=pat.sub(lambda m: resolve(m.group(1),m.group(2)), s)
    assert '<<<<<<<' not in s, p
    open(p,'w').write(s)
    print('resolved',p)
# smoke.mts: git keeps the shared closing "}" outside the conflict, so a section concatenated before another loses it
for p in sys.argv[1:]:
    if p.endswith('smoke.mts'):
        s=open(p).read()
        s2=re.sub(r'(\n  [^\n]*\)\n)(// [A-Z][^\n]*:)', r'\1}\n\n\2', s)
        if s2!=s: open(p,'w').write(s2); print('restored a section brace in',p)
