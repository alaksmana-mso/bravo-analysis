import json,collections,re,sys
sys.path.insert(0,".")
from themes import theme
o=json.load(open("classified.json"))
for x in o: x["theme"]=theme(x["summary"])
at=collections.Counter((x["app"],x["theme"]) for x in o)
DEFECT=("code/requirement defect category",)
K_SYS=r"berulang|terulang|selalu|setiap (kali|hari|bulan)|massal|masif|banyak kontrak|beberapa kontrak|semua (kontrak|cabang|user)|belum handle|tidak handle|not handled|logic|logika|perhitungan|calculation|kalkulasi"
K_GL=r"intermittent|sesaat|sempat|sudah normal|kembali normal|retry (berhasil|success)|restart|human error|user error|salah input|kesalahan input|incorrectly"
for x in o:
    t=(x["summary"]+" "+x["rc"]).lower(); n=at[(x["app"],x["theme"])]
    if x["cause"]=="Not a defect": x["nature"],x["why"]="Glitch","Invalid / not a defect"
    elif x["cluster"]>=3: x["nature"],x["why"]="Systemic","Same symptom repeated (≥3 near-identical tickets)"
    elif x["theme"]!="Other" and n>=5: x["nature"],x["why"]="Systemic",f"Recurring failure mode in the same app (≥5 tickets)"
    elif x["why"] in DEFECT: x["nature"],x["why"]="Systemic","Defect category (missed in dev / requirements / known bug)"
    elif x["area"]=="Issue Migrasi": x["nature"],x["why"]="Systemic","R1→R3 migration defect"
    elif re.search(K_GL,t): x["nature"],x["why"]="Glitch","Transient or one-off (retry, restart, user input)"
    elif re.search(K_SYS,t): x["nature"],x["why"]="Systemic","Logic or multi-record signal in root cause"
    else: x["nature"],x["why"]="Glitch","Isolated: no repeat, no defect signal"
json.dump(o,open("final.json","w"),ensure_ascii=False)
N=len(o)
C=collections.Counter((x["nature"],x["cause"]) for x in o)
for k,v in sorted(C.items()): print(k,v,f"{v/N:.1%}")
print(collections.Counter(x["nature"] for x in o)); print(collections.Counter(x["why"] for x in o))
S=collections.Counter((x["nature"],x["sev"]) for x in o); print(sorted(S.items()))
