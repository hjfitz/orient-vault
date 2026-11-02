import re,sys
ts=open(sys.argv[1]).read(); gos=" ".join(open(p).read() for p in sys.argv[2:])
pat_ts=re.compile(r'\bit(?:\.each\([^)]*\))?\(\s*(["`])((?:\\.|(?!\1).)*)\1',re.S)
pat_go=re.compile(r'"((?:\\.|[^"\\\n])*)"')
a=[m.group(2) for m in pat_ts.finditer(ts)]; b=set(m.group(1) for m in pat_go.finditer(gos))
missing=[n for n in a if n not in b]
print(f"ts={len(a)} go_names={len(b)} missing={len(missing)}")
for n in missing: print("  MISSING:",n)
