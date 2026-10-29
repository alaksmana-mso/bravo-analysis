import os, json, base64, urllib.request, urllib.parse, sys
base = os.environ.get("JIRA_URL") or "https://bfifinance.atlassian.net"
user = os.environ.get("JIRA_USERNAME") or os.environ["CONFLUENCE_USERNAME"]
tok = os.environ.get("JIRA_API_TOKEN") or os.environ["CONFLUENCE_API_TOKEN"]
auth = base64.b64encode(f"{user}:{tok}".encode()).decode()
fields = "summary,created,resolutiondate,status,labels,issuetype,customfield_10655,customfield_10225,customfield_10979,customfield_10479,customfield_12031,customfield_11926,customfield_10082,customfield_11044,customfield_10457,description"
jql = 'project = PRD AND created >= "2026-01-01" ORDER BY created ASC'
out = []; token = None
while True:
    q = {"jql": jql, "fields": fields, "maxResults": 100}
    if token: q["nextPageToken"] = token
    req = urllib.request.Request(base + "/rest/api/3/search/jql?" + urllib.parse.urlencode(q), headers={"Authorization": "Basic " + auth, "Accept": "application/json"})
    d = json.load(urllib.request.urlopen(req))
    out += d["issues"]; token = d.get("nextPageToken")
    print(len(out), file=sys.stderr)
    if not token or d.get("isLast"): break
json.dump(out, open("prd-2026.json", "w"))
