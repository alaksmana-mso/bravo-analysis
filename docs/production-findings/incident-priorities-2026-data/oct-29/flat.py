import json, sys
d = json.load(open("prd-2026.json"))
def adf(n):
    if n is None: return ""
    if isinstance(n, str): return n
    if isinstance(n, list): return " ".join(adf(x) for x in n)
    t = n.get("text","")
    return (t + " " + adf(n.get("content"))).strip() + ("\n" if n.get("type") in ("paragraph","heading","listItem","tableRow") else "")
def v(x):
    if x is None: return ""
    if isinstance(x, dict): return x.get("value") or x.get("name") or ""
    if isinstance(x, list): return ",".join(filter(None,[v(i) for i in x]))
    return str(x)
rows=[]
for i in d:
    f=i["fields"]
    rows.append(dict(key=i["key"], created=f["created"][:10], resolved=(f.get("resolutiondate") or "")[:10],
      sev=v(f.get("customfield_10655")), rcc=v(f.get("customfield_10225")), area=v(f.get("customfield_12031")),
      app=v(f.get("customfield_10979")), squad=v(f.get("customfield_11044")), type=v(f.get("issuetype")),
      status=v(f.get("status")), summary=f.get("summary") or "", desc=adf(f.get("description"))[:4000]))
json.dump(rows, open("flat.json","w"), ensure_ascii=False)
