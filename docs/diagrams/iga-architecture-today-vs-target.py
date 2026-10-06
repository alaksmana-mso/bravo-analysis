W, H = 2400, 1400
out = []
def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
STYLES = {"src":("#DCE8F7","#3B6FB6"),"iga":("#E9DDF7","#7A4FB5"),"kc":("#DDF2E3","#2F8F55"),"role":("#FDEBD2","#D6872B"),
 "app":("#F1F1F1","#777777"),"bad":("#FBDADA","#C0392B"),"dec":("#FFF4C2","#B7950B"),"mon":("#E3F2FD","#1E88E5"),"man":("#FFFFFF","#C0392B")}
MK = {"#555":"grey","#C0392B":"red","#2F8F55":"green","#7A4FB5":"purple","#D6872B":"orange","#1E88E5":"blue","#B7950B":"gold"}
boxes=[]; lines=[]
def box(x,y,w,h,title,lines_=(),style="app",dashed=False,strike=False,fs=15,tfs=17):
    fill,stroke = STYLES[style]; dash = ' stroke-dasharray="9,6"' if dashed else ''
    s=[f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2.5"{dash}/>']
    ty=y+26
    s.append(f'<text x="{x+w/2}" y="{ty}" text-anchor="middle" font-size="{tfs}" font-weight="700" fill="#222">{esc(title)}</text>')
    for i,l in enumerate(lines_):
        s.append(f'<text x="{x+w/2}" y="{ty+22+i*19}" text-anchor="middle" font-size="{fs}" fill="#333">{esc(l)}</text>')
    if strike:
        s.append(f'<line x1="{x+8}" y1="{y+8}" x2="{x+w-8}" y2="{y+h-8}" stroke="#C0392B" stroke-width="3"/><line x1="{x+w-8}" y1="{y+8}" x2="{x+8}" y2="{y+h-8}" stroke="#C0392B" stroke-width="3"/>')
    boxes.extend(s)
def path(pts,label="",color="#555",dashed=False,lx=None,ly=None,anchor="start",head=True):
    dash = ' stroke-dasharray="8,6"' if dashed else ''
    d="M"+" L".join(f"{x},{y}" for x,y in pts)
    mk=f' marker-end="url(#a-{MK[color]})"' if head else ''
    lines.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.2"{dash}{mk}/>')
    if label:
        lines.append(f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="14" fill="{color}">{esc(label)}</text>')
def text(x,y,s,fs=16,w="400",color="#222",anchor="start"):
    boxes.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{fs}" font-weight="{w}" fill="{color}">{esc(s)}</text>')

out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">')
out.append('<defs>'+''.join(f'<marker id="a-{n}" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for c,n in MK.items())+'</defs>')
out.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
out.append('<rect x="20" y="20" width="1170" height="1300" rx="14" fill="#FAFAFA" stroke="#BBB" stroke-width="2"/>')
out.append('<rect x="1210" y="20" width="1170" height="1300" rx="14" fill="#FAFAFA" stroke="#BBB" stroke-width="2"/>')
text(605,62,"TODAY (October 2026): four Keycloaks, nine role stores, no lifecycle owner",24,"700","#C0392B","middle")
text(1795,62,"TARGET (end of 2027): one IGA, one Keycloak, one decision service",24,"700","#2F8F55","middle")

# ============ LEFT ============
L=20
box(L+40,100,240,78,"HCIS (HR, MSSQL)",["Employee master, resign date"],"src")
box(L+330,100,250,78,"Google Workspace",["Email identity, MFA","(created/suspended by hand)"],"src")
box(L+640,100,230,78,"Active Directory",["VPN, Windows, e-self"],"src")
box(L+900,100,230,78,"Engineers by hand",["PRs, CSV uploads, curl,","Confluence tables, Jira tickets"],"man",dashed=True)
box(L+40,300,220,78,"bravo-employee-service",["copy of HCIS record"],"iga")
path([(L+90,178),(L+90,300)],"RabbitMQ, D+2, lossy","#C0392B",lx=L+100,ly=235)
path([(L+230,178),(L+230,300)],"Airflow, daily","#555",lx=L+240,ly=262)
# fan-out bus
path([(L+150,378),(L+150,470)],"fan-out MQ","#555",lx=L+160,ly=430,head=False)
lines.append(f'<line x1="{L+150}" y1="470" x2="{L+890}" y2="470" stroke="#555" stroke-width="2.2"/>')
for x in (L+150,L+400,L+640,L+890):
    path([(x,470),(x,500)],color="#555")
box(L+40,500,230,96,"bravo-user-iam-service",["creates Keycloak users,","Enabled=true, never disables,","predictable temp password"],"iga")
box(L+300,500,200,96,"CNV",["user_access, checker-maker;","discards 212k HCIS","messages a day"],"iga")
box(L+530,500,220,96,"BPM nightly job",["adds roles for past","resign dates; admin APIs","create users directly"],"iga")
box(L+780,500,220,96,"LORA BPP + LTS",["POST /mgmt/people with","shared api-secret; no delete,","no session revoke"],"iga")
# engineers trunk down the right edge
T=L+1158
path([(L+1130,139),(T,139),(T,1069),(L+1142,1069)],color="#C0392B",dashed=True)
path([(T,548),(L+1002,548)],"CSV / curl","#C0392B",dashed=True,lx=T-8,ly=540,anchor="end")
path([(T,908),(L+1142,908)],color="#C0392B",dashed=True)
# Keycloak row
box(L+40,690,340,110,"Keycloak auth.bfi.co.id 26.7",["realm google-workspace, 3 pods,","brokers Google Workspace by SAML;","1.04M calls/week; realm not in git"],"kc")
box(L+400,690,300,110,"Keycloak legacy Bravo 21.1.1",["realms bravo, bpm, spvcockpit,","lms-gateway; 1 pod; config not in git","197k calls/week (repeat-order)"],"bad",dashed=True)
box(L+720,690,220,110,"Keycloak sso.bfi.co.id 21.1.1",["realm IAM_BFI; 1 pod","nightly group-mapper cron"],"bad",dashed=True)
box(L+960,690,170,110,"Keycloak Sharia 21.1.1",["realm Bravo; 1 pod"],"bad",dashed=True)
path([(L+455,178),(L+455,205),(L+282,205),(L+282,690)],"SAML","#2F8F55",lx=L+292,ly=300)
path([(L+700,178),(L+700,232),(L+515,232),(L+515,690)],"LDAP, plain, weekly sync","#C0392B",dashed=True,lx=L+525,ly=300)
path([(L+200,596),(L+480,690)],"attributes 14k/wk","#555",lx=L+215,ly=655)
path([(L+250,596),(L+800,690)],"BAU copy 14k/wk","#555",lx=L+300,ly=624)
path([(L+660,596),(L+620,690)],"bpm realm roles","#555",lx=L+600,ly=640,anchor="end")
# role stores row
box(L+40,860,200,96,"user-iam roles",["SQL in prod; CSV in git","for Sharia and BAU;","no approval step"],"role")
box(L+275,860,170,96,"CNV user_access",["branches, roles,","approval tables"],"role")
box(L+480,860,200,96,"Per-app user tables",["OTRS, digital-web, FinOps,","Pimcore, Strapi, gateways,","Salesforce"],"role")
box(L+715,860,200,96,"LTS people (ArangoDB)",["JSON per NIK, roles,","branches; written by curl"],"role")
box(L+950,860,190,96,"Confluence + Sheets",["surveyor role table,","116 revisions"],"role")
path([(L+60,596),(L+60,640),(L+30,640),(L+30,908),(L+40,908)],color="#D6872B")
path([(L+400,596),(L+400,660),(L+390,660),(L+390,830),(L+360,830),(L+360,860)],color="#D6872B")
path([(L+890,596),(L+890,650),(L+950,650),(L+950,830),(L+815,830),(L+815,860)],color="#D6872B")
# apps row
box(L+40,1030,320,78,"Bravo apps (30+)",["token from one of 4 Keycloaks;","roles from user-iam or app table"],"app")
box(L+390,1030,230,78,"LORA back office",["token from GWS realm;","roles from LTS people"],"app")
box(L+650,1030,240,78,"BAU apps",["OTRS, OpEx, MySIS, treasury:","IAM_BFI realm"],"app")
box(L+920,1030,220,78,"Platform access",["GCP per-user Terraform, GitHub,","Datadog, Atlassian: by ticket"],"app")
path([(L+300,800),(L+300,830),(L+257,830),(L+257,1030)],color="#2F8F55")        # auth -> Bravo apps
path([(L+420,800),(L+420,815),(L+257,815)],color="#C0392B",head=False)            # legacy joins trunk
path([(L+380,745),(L+390,745),(L+390,830),(L+462,830),(L+462,1030)],color="#2F8F55")  # auth -> LORA
path([(L+830,800),(L+830,830),(L+697,830),(L+697,1030)],color="#C0392B")          # IAM_BFI -> BAU
path([(L+140,956),(L+140,1030)],color="#D6872B"); path([(L+330,956),(L+330,1030)],color="#D6872B")
path([(L+760,956),(L+760,990),(L+560,990),(L+560,1030)],color="#D6872B")
path([(L+620,956),(L+620,990),(L+730,990),(L+730,1030)],color="#D6872B")
out_banner=[f'<rect x="{L+40}" y="1150" width="1110" height="140" rx="10" fill="#FBDADA" stroke="#C0392B" stroke-width="2"/>']
boxes.extend(out_banner); text(L+60,1180,"What is missing today",18,"700","#C0392B")
for i,l in enumerate(["No owner for a person's access across HCIS, Keycloak, Google Workspace, AD and apps. Leaver: nothing disables a Keycloak user.",
 "One shared api-secret in 52 production deployments. Keycloak sends no logs or traces to Datadog. No approval outside CNV.",
 "No access review anywhere. Offboarding is manual in 4 Keycloaks, AD, Google Workspace and every app table."]):
    text(L+60,1208+i*24,l,15,"400","#4A1F1F")

# ============ RIGHT ============
R=1210
box(R+40,100,240,78,"HCIS (read-only view)",["pulled every 15 min,","resign every 5 min"],"src")
box(R+310,100,200,78,"Confins (agents)",["agent master"],"src")
box(R+540,100,260,78,"Google Workspace",["the only employee IdP,","MFA; created/suspended by IGA"],"src")
box(R+830,100,140,78,"n8n",["Chat approvals,","notifications"],"app")
box(R+990,100,160,78,"Active Directory",["VPN and Windows only"],"app")
box(R+40,290,620,170,"midPoint: identity governance (IGA)",[
 "One identity per person · organisation tree from HCIS · role catalogue with owners",
 "Birthright roles from job title and branch · requests and approvals · mover recompute",
 "Leaver: disable, suspend, revoke everywhere within 15 minutes · reconciliation",
 "Certification campaigns · separation of duties · audit of every grant"],"iga",fs=15,tfs=19)
path([(R+160,178),(R+160,290)],"HR feed","#7A4FB5",lx=R+170,ly=272); path([(R+410,178),(R+380,290)],color="#7A4FB5")
path([(R+600,290),(R+640,178)],"create, suspend","#7A4FB5",lx=R+632,ly=240)
path([(R+900,178),(R+640,290)],color="#555",dashed=True)
box(R+700,290,450,170,"Datadog",["Keycloak user and admin events","midPoint audit and provisioning failures","Monitors: user created outside the IGA,",
 "role change by a human, login by a resigned NIK","Realm-retirement gauge: calls per realm"],"mon",fs=15,tfs=19)
path([(R+660,400),(R+700,400)],color="#1E88E5")
box(R+40,540,440,120,"Keycloak 26.x, one cluster",["operator-managed, realm google-workspace,","realm config in git; brokers Google Workspace;","enable, disable, groups, logout driven by midPoint;","brute force on, events on"],"kc")
box(R+520,540,360,120,"Decision service",["OpenFGA / SpiceDB / Ory Keto (evaluate):","branch, product, task ownership;","midPoint writes org and branch tuples,","apps write ownership, apps call check"],"dec")
box(R+910,540,240,120,"Retired",["Keycloak 21.1.1 x3:","bravo, bpm, spvcockpit,","lms-gateway, IAM_BFI, Sharia"],"bad",dashed=True,strike=True)
path([(R+200,460),(R+200,540)],"enable / disable / logout","#7A4FB5",lx=R+210,ly=505)
path([(R+560,460),(R+640,540)],"org tuples","#7A4FB5",lx=R+605,ly=495)
path([(R+560,178),(R+560,215),(R+25,215),(R+25,600),(R+40,600)],"SAML / OIDC login, MFA","#2F8F55",lx=R+30,ly=232)
path([(R+440,540),(R+440,500),(R+720,500),(R+720,460)],"events","#1E88E5",lx=R+730,ly=486)
# provisioning bus
Y=740
path([(R+500,460),(R+500,700)],color="#7A4FB5",head=False)
lines.append(f'<line x1="{R+140}" y1="700" x2="{R+1020}" y2="700" stroke="#7A4FB5" stroke-width="2.2"/>')
for x in (R+140,R+360,R+565,R+770,R+1020): path([(x,700),(x,Y)],color="#7A4FB5")
text(R+800,690,"midPoint provisions, revokes and reconciles every store",14,"400","#7A4FB5","middle")
box(R+40,Y,200,96,"user-iam API",["grant / revoke with actor,","audit event; no CSV"],"role")
box(R+260,Y,200,96,"LTS people API",["create / update / deactivate,","session revoke, task reassign"],"role")
box(R+480,Y,170,96,"CNV API",["user_access,","allowed branches"],"role")
box(R+670,Y,200,96,"bravo-auth-service",["agents, suppliers:","deactivate endpoint"],"role")
box(R+890,Y,260,96,"Platform access",["Google Groups for GCP, GitHub","teams, Datadog, Atlassian, Temporal","(SCIM), DB access via PAM"],"role")
boxes.append(f'<rect x="{R+40}" y="880" width="1110" height="60" rx="10" fill="#EFEFEF" stroke="#777" stroke-width="2"/>')
text(R+595,916,"Krakend gateway · Istio mTLS in-cluster · one credential per service, rotated · Workload Identity Federation for CI",16,"700","#333","middle")
path([(R+250,660),(R+250,880)],"tokens","#2F8F55",lx=R+258,ly=860)
path([(R+660,880),(R+660,660)],"apps check branch / task rights","#B7950B",lx=R+668,ly=860)
box(R+40,990,340,96,"Bravo apps",["token from Keycloak; roles from","user-iam API; data checks via","decision service"],"app")
box(R+410,990,340,96,"LORA back office",["token from Keycloak; people from","LTS API; task filters via","decision service"],"app")
box(R+780,990,370,96,"BAU and platform tools",["OTRS, OpEx, treasury, Argo CD,","Grafana on the same realm;","GCP and GitHub via groups"],"app")
for x in (R+210,R+580,R+965): path([(x,940),(x,990)],color="#555")
boxes.append(f'<rect x="{R+40}" y="1150" width="1110" height="140" rx="10" fill="#DDF2E3" stroke="#2F8F55" stroke-width="2"/>')
text(R+60,1180,"What changes",18,"700","#2F8F55")
for i,l in enumerate(["Every grant has an actor, an approver and a record. A resignation in HCIS removes access everywhere within 15 minutes.",
 "One Keycloak, one employee realm, configuration in git, events in Datadog. Zero shared service secrets.",
 "Quarterly certification of privileged roles. Data-level authorization in one service instead of nine hand-edited stores."]):
    text(R+60,1208+i*24,l,15,"400","#1F4A2B")
# legend
for i,(name,st) in enumerate([("Source of truth","src"),("Identity / lifecycle","iga"),("Authentication (Keycloak)","kc"),("Role store","role"),("Applications","app"),("Decision service","dec"),("Monitoring","mon"),("Unsupported / to retire","bad")]):
    fill,stroke=STYLES[st]; x=40+i*290
    boxes.append(f'<rect x="{x}" y="1345" width="26" height="18" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'); text(x+34,1360,name,15)
out.extend(lines); out.extend(boxes); out.append('</svg>')
open('/Users/mac-6000202/Documents/BFI_GITHUB/bravo-analysis/docs/diagrams/iga-architecture-today-vs-target.svg','w').write('\n'.join(out))
print("ok")
