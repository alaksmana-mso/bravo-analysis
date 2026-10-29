import json, re, collections
r=[x for x in json.load(open("flat.json")) if x["created"]<="2026-10-28"]
def rc_text(x):
    m=re.search(r"Root Cause(?! Category)[:\s]*(.*?)(Solutions?:|Temporary|PIC / Reporter|$)", x["desc"], re.S|re.I)
    return (m.group(1) if m else "")[:1500]
def rc_cat(x):
    if x["rcc"]: return x["rcc"]
    m=re.search(r"Root Cause Category:\s*([^\n]+)|Category:\s*([^\n]+?)\s{2,}", x["desc"])
    return (m.group(1) or m.group(2)).strip() if m else ""
STOP=set("dan di yang ke pada untuk dengan tidak bisa dari atas r3 r1 lms confins system sistem the to of and on in for error gagal issue kontrak data".split())
def sig(x):
    s=x["summary"].lower()
    s=re.sub(r"^\s*\d{8}\s*[-–]?\s*","",s); s=re.sub(r"\(r3\)|\d+","",s)
    return set(t for t in re.findall(r"[a-z]{3,}",s) if t not in STOP)
# cluster within app by Jaccard
for x in r: x["sig"]=sig(x); x["rctext"]=rc_text(x); x["cat"]=rc_cat(x)
clusters=[]; 
for x in r:
    best=None
    for c in clusters:
        if c["app"]!=x["app"]: continue
        j=len(x["sig"]&c["sig"])/max(1,len(x["sig"]|c["sig"]))
        if j>=0.5 and (best is None or j>best[0]): best=(j,c)
    if best: best[1]["m"].append(x); x["cl"]=best[1]
    else:
        c={"app":x["app"],"sig":x["sig"],"m":[x]}; clusters.append(c); x["cl"]=c
INFRA_CAT={"Infrastructure Issues","Network Issue","Database Issue","Access Management Issue","Issue by Security and Non Functionality ex Performance Degradation,etc","External Systems Issues"}
DEFECT_CAT={"Missed on Development","Missed Error Handling on Development","Missing/Incorrect Requirements Technical","Missing/Incorrect Requirements Functional","Missing/Incorrect Requirements","Known Issues/Bugs","Missing/Incorrect UI Design"}
K_INFRA=r"time ?out|timed out|\bdown\b|\bpod\b|restart|memory|\boom\b|\bcpu\b|latency|lambat|slow|connection pool|too many connections|max.?connection|disk|gw01|gateway|redis|kafka|rabbit|certificate|\bssl\b|\bdns\b|\bvpn\b|\b50[234]\b|server|tidak (dapat|bisa) diakses|cannot be accessed|unreachable|network|jaringan|koneksi|connection refused|deadlock|lock wait|high load|spike|cpu|replica|node pool|vm |firewall|sftp"
K_RELEASE=r"deploy|deployment|after upgrade|setelah upgrade|upgrade|cutover|migrasi|migration|r1 to r3|r1 ke r3|rollback|hotfix|config(uration)? (belum|missing|tidak)|setting(an)?/?config|belum (di)?setting|belum tersedia.*config|feature flag|new version|versi baru|go-?live (r3|lms)"
K_DATA=r"\bdata\b|selisih|double|duplikat|duplicate|tidak sinkron|not sync|mismatch|perbedaan status|beda status|tidak sesuai|update (data|flag|status)|support data|patch|null|kosong|missing data|tidak terbentuk|tidak muncul"
K_GLITCH=r"intermittent|sesaat|sempat|sementara waktu|sudah normal|kembali normal|sudah bisa|retry (berhasil|success)|hit ulang|re-?hit|restart|re-?run|rerun|trigger ulang|one.?off|human error|user error|salah input|kesalahan input|incorrectly|by user"
K_SYSTEMIC=r"berulang|terulang|selalu|setiap (kali|hari|bulan)|every|massal|masif|banyak kontrak|beberapa kontrak|semua (kontrak|cabang|user)|all (contracts|branches)|belum handle|tidak handle|not handled|logic|logika|bug|perhitungan|calculation|kalkulasi|eod|eom|batch|scheduler|job"
K_STRONG=r"high cpu|cpu tinggi|\bdown\b|server restart|restart server|out of memory|\boom\b|connection pool|too many connections|disk full|network|jaringan|gw01|certificate|ssl"
def cause(x):
    t=(x["summary"]+" "+x["rctext"]).lower()
    if x["cat"] in INFRA_CAT or re.search(K_STRONG,t) or (re.search(K_INFRA,t) and x["cat"] not in DEFECT_CAT and x["cat"]!="Data Issues"): return "Infra"
    if x["area"]=="Issue Migrasi" or x["cat"]=="Configuration Issue" or re.search(K_RELEASE,t): return "Release process"
    if x["cat"]=="Data Issues": return "Data problem"
    if x["cat"] in DEFECT_CAT or x["cat"] in ("Functionality Issue","Application Issue"): return "Dev process (QA)"
    if re.search(K_DATA,t): return "Data problem"
    return "Dev process (QA)"
def nature(x):
    t=(x["summary"]+" "+x["rctext"]).lower()
    n=len(x["cl"]["m"])
    if x["cat"]=="Invalid Issues": return "Glitch","invalid / not a defect"
    if n>=3: return "Systemic",f"recurs: {n} similar tickets"
    if x["cat"] in DEFECT_CAT: return "Systemic","code/requirement defect category"
    if x["area"]=="Issue Migrasi": return "Systemic","R1→R3 migration defect"
    if re.search(K_GLITCH,t): return "Glitch","transient / one-off fix"
    if re.search(K_SYSTEMIC,t): return "Systemic","logic/batch/multi-record signal"
    return "Glitch","isolated (≤2 similar tickets), no defect signal"
out=[]
for x in r:
    nat,why=nature(x); ca=cause(x)
    if x["cat"]=="Invalid Issues": ca="Not a defect"
    out.append(dict(key=x["key"],created=x["created"],sev=x["sev"],app=x["app"],cat=x["cat"],area=x["area"],summary=x["summary"].strip(),nature=nat,why=why,cause=ca,cluster=len(x["cl"]["m"]),r3=("(R3)" in x["summary"].upper()),rc=x["rctext"][:300]))
json.dump(out,open("classified.json","w"),ensure_ascii=False)
C=collections.Counter((o["nature"],o["cause"]) for o in out)
for k,v in sorted(C.items()): print(k,v)
print(collections.Counter(o["nature"] for o in out))
print(collections.Counter(o["why"].split(":")[0] for o in out))
big=sorted(clusters,key=lambda c:-len(c["m"]))[:25]
for c in big: print(len(c["m"]),c["app"],"|",c["m"][0]["summary"][:90])
