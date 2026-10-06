#!/usr/bin/env python3
"""
Generate the KrakenD endpoint set for the BPM service (bravo-bpm-service) from its
OpenAPI document, so the Bravo consoles can call BPM through the public gateway
instead of the public Ingress (SRE-1803, "all backend services private").

Why generated: the consoles call about 800 distinct BPM endpoints; KrakenD CE has
no wildcard routing, so every path/method pair needs an explicit endpoint. Writing
1,100 template files by hand is not reviewable; one generated file plus this
script is.

Usage:
  python3 gen/openapi-to-krakend/bpm.py <openapi.json> [config/template] > config/template/bpm._generated.endpoints.tmpl

Input:  the service's springdoc document, GET <bpm-base-url>/api-docs
        (public on every environment; servers[0].url ends in /bpm).
Output: a Go-template fragment: comma-separated endpoint objects, included once
        from krakend.tmpl / krakend.prod.tmpl inside "endpoints": [ ... ].

Rules:
  - endpoint = "/bpm" + openapi path; backend url_pattern is identical; host =
    env BPM_SERVICE_URL (cluster-local service URL, set in app-deployment).
  - "no-op" encoding in and out: bodies, multipart uploads and file downloads
    pass through untouched. Query strings: all forwarded ("*").
  - Path parameters are renamed positionally ({path_1}, {path_2}, ...), the
    convention of the hand-written bpm.*.tmpl files, because the router (gin)
    rejects two routes that use different parameter names at the same position
    (e.g. /v1/x/{id}/a and /v1/x/{applicationId}/b). The backend pattern is
    renamed identically, so behaviour is unchanged.
  - Sorted by path then method for a stable diff.
"""
import json, pathlib, re, sys
from collections import OrderedDict

METHODS = ("get", "post", "put", "patch", "delete")
PREFIX = "/bpm"
PARAM = re.compile(r"\{([^}/]+)\}")


def clean_path(path):
    """springdoc sometimes glues query parameters into the path
    (/v1/admin/user={surveyorId}&role={userRole}); keep the path part only."""
    return re.split(r"[=&?]", path, 1)[0].rstrip("/") or "/"


def load_operations(spec):
    ops = set()
    for path, item in spec["paths"].items():
        for m in METHODS:
            if m in item:
                ops.add((clean_path(path), m.upper()))
    return sorted(ops)


def canonicalise_params(paths):
    """Return {original_path: renamed_path} with positional parameter names
    ({path_1}, {path_2}, ...), the convention of the hand-written bpm.*.tmpl
    files. The router (gin) rejects two routes that use different parameter
    names at the same position, so one convention for every bpm route is the
    only safe choice. The backend url_pattern is renamed identically."""
    out = {}
    for p in sorted(paths):
        n = 0
        segs = []
        for s in p.split("/"):
            if PARAM.fullmatch(s):
                n += 1
                segs.append("{path_%d}" % n)
            else:
                segs.append(s)
        out[p] = "/".join(segs)
    return out


def endpoint_json(path, method):
    return OrderedDict([
        ("endpoint", PREFIX + path),
        ("method", method),
        ("output_encoding", "no-op"),
        ("input_headers", "__BPM_INPUT_HEADERS__"),
        ("input_query_strings", ["*"]),
        ("backend", [OrderedDict([
            ("method", method),
            ("url_pattern", PREFIX + path),
            ("encoding", "no-op"),
            ("host", ["__BPM_HOST__"]),
            ("extra_config", {"plugin/http-client": "__BPM_CLIENT_EXECUTOR__"}),
        ])]),
    ])


def handwritten_routes(template_dir):
    """(method, normalised endpoint) of the hand-written bpm.*.tmpl files, which
    carry their own rate-limit / auth settings and must not be generated twice."""
    routes = set()
    for f in sorted(pathlib.Path(template_dir).glob("bpm.*.tmpl")):
        if "_generated" in f.name:
            continue
        text = f.read_text()
        ep = re.search(r'"endpoint":\s*"([^"]+)"', text)
        me = re.search(r'"method":\s*"([A-Z]+)"', text)
        if ep and me:
            routes.add((me.group(1), PARAM.sub("{p}", ep.group(1))))
    return routes


def main():
    spec = json.load(open(sys.argv[1]))
    template_dir = sys.argv[2] if len(sys.argv) > 2 else "config/template"
    skip = handwritten_routes(template_dir)
    ops = load_operations(spec)
    renamed = canonicalise_params({p for p, _ in ops})
    seen = set()
    objs = []
    skipped = 0
    for path, method in ops:
        key = (renamed[path], method)
        if key in seen:
            continue  # two OpenAPI paths that collapse to one route after renaming
        seen.add(key)
        if (method, PARAM.sub("{p}", PREFIX + renamed[path])) in skip:
            skipped += 1
            continue  # a hand-written template already serves this route
        objs.append(endpoint_json(renamed[path], method))
    body = ",\n".join(json.dumps(o, indent=2) for o in objs)
    body = (body
            .replace('"__BPM_INPUT_HEADERS__"', '{{ template "bpm_input_headers.tmpl" . }}')
            .replace('"__BPM_HOST__"', '"{{ env \"BPM_SERVICE_URL\" }}"')
            .replace('"__BPM_CLIENT_EXECUTOR__"', '{{ template "bpm_client_executor.tmpl" . }}'))
    renames = sum(1 for p in renamed if renamed[p] != p)
    sys.stdout.write(
        "{{/* GENERATED FILE - do not edit by hand.\n"
        f"     Source: bravo-bpm-service OpenAPI (openapi {spec.get('openapi')}), {len(spec['paths'])} paths, "
        f"{len(ops)} operations -> {len(objs)} endpoints ({renames} paths had a parameter renamed for router consistency; "
        f"{skipped} routes left to the hand-written bpm.*.tmpl files).\n"
        "     Regenerate: python3 gen/openapi-to-krakend/bpm.py <api-docs.json> > config/template/bpm._generated.endpoints.tmpl */}}\n")
    sys.stdout.write(body)
    sys.stdout.write("\n")
    print(f"endpoints={len(objs)} renamed_paths={renames} skipped_handwritten={skipped}", file=sys.stderr)


if __name__ == "__main__":
    main()
