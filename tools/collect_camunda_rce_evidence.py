#!/usr/bin/env python3
"""
Preserve the evidence of the Camunda RCE finding (SECURITY-FINDING-camunda-rce.md)
before hardening action 6 (purge) runs.

Read-only. Connects to the production BPM database the same way the finding was
collected: DATABASE_URI from ~/.config/mcp-postgres/bpm.env (never printed), sets
default_transaction_read_only = on, and writes an evidence bundle:

  evidence/camunda-rce-<UTC>/
    manifest.json          host, db, user, time, read-only flag, row counts, SHA-256 of every file
    definitions.csv        the injected process definitions (act_re_procdef + act_re_deployment)
    sessions.csv           deploy_time_ grouped by minute (the "7 sessions")
    all_keys.csv           every distinct process definition key in the engine, with the
                           injected/application classification, so reviewers can check the filter
    instances.csv          act_hi_procinst rows for the injected keys (expect 1)
    variables.csv          act_hi_varinst rows for those instances (the captured command output)
    activities.csv         act_hi_actinst rows for those instances
    details.csv            act_hi_detail rows for those instances
    runtime.csv            act_ru_execution / act_ru_job / act_ru_incident rows for the injected keys (expect 0)
    op_log.csv             act_hi_op_log rows touching the injected deployments/definitions (expect 0)
    authorizations.csv     act_ru_authorization rows whose resource_id_ is an injected key
    payloads/<n>_<deployment>_<resource>.bpmn   the BPMN XML of every injected deployment
    expressions.csv        every camunda:expression / delegateExpression found in those payloads
    SHA256SUMS
  and evidence/camunda-rce-<UTC>.zip

Run from a machine on the corporate network segment that reaches
sqlproxy.prod.bravo.bfi.co.id:15434:

  mise x uv@latest python@3.12 -- uv run --python 3.12 --with 'psycopg[binary]' \
      python tools/collect_camunda_rce_evidence.py

Then attach the .zip and manifest.json to the Confluence evidence page (child of
page 2800844950) and paste definitions.csv into its table. Do not run the purge
until that is done.
"""
import csv, hashlib, io, json, os, re, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

import psycopg

APP_KEY_PATTERN = r'^(NDF|OPERATION|Process_|Unified_|Ro_|Sharia_|UNSECURED|unsecured|preApproval|multiAsset)'
ENV_FILE = Path.home() / '.config' / 'mcp-postgres' / 'bpm.env'


def database_uri() -> str:
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith('DATABASE_URI='):
            return line.split('=', 1)[1].strip().strip('"').strip("'")
    sys.exit(f'DATABASE_URI not found in {ENV_FILE}')


def write_csv(path: Path, cur, sql: str, params=None) -> int:
    cur.execute(sql, params or ())
    cols = [d.name for d in cur.description]
    rows = cur.fetchall()
    with path.open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow(['' if v is None else (v.hex() if isinstance(v, (bytes, memoryview)) else v) for v in r])
    return len(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = Path('evidence') / f'camunda-rce-{stamp}'
    (out / 'payloads').mkdir(parents=True)
    counts = {}

    with psycopg.connect(database_uri(), autocommit=True) as conn:
        db_host, db_port, db_name = conn.info.host, conn.info.port, conn.info.dbname
        with conn.cursor() as cur:
            cur.execute('SET default_transaction_read_only = on')
            cur.execute('SHOW default_transaction_read_only')
            readonly = cur.fetchone()[0]
            cur.execute('SELECT now(), current_user, version()')
            db_now, db_user, db_version = cur.fetchone()

            counts['definitions'] = write_csv(out / 'definitions.csv', cur, f"""
                SELECT pd.id_ AS procdef_id, pd.key_, pd.version_, pd.name_ AS procdef_name,
                       pd.resource_name_, pd.deployment_id_, pd.suspension_state_, pd.history_ttl_,
                       pd.tenant_id_, pd.version_tag_, pd.startable_,
                       d.name_ AS deployment_name, d.deploy_time_, d.source_ AS deployment_source
                FROM act_re_procdef pd JOIN act_re_deployment d ON d.id_ = pd.deployment_id_
                WHERE pd.key_ !~ %s ORDER BY d.deploy_time_, pd.key_""", (APP_KEY_PATTERN,))

            counts['sessions'] = write_csv(out / 'sessions.csv', cur, f"""
                SELECT date_trunc('minute', d.deploy_time_) AS session_minute, count(*) AS definitions,
                       min(d.name_) AS first_name, max(d.name_) AS last_name
                FROM act_re_procdef pd JOIN act_re_deployment d ON d.id_ = pd.deployment_id_
                WHERE pd.key_ !~ %s GROUP BY 1 ORDER BY 1""", (APP_KEY_PATTERN,))

            counts['all_keys'] = write_csv(out / 'all_keys.csv', cur, f"""
                SELECT key_, count(*) AS versions, min(version_) AS min_version, max(version_) AS max_version,
                       CASE WHEN key_ ~ %s THEN 'application' ELSE 'INJECTED' END AS classification
                FROM act_re_procdef GROUP BY key_ ORDER BY classification, key_""", (APP_KEY_PATTERN,))

            cur.execute(f"SELECT DISTINCT key_ FROM act_re_procdef WHERE key_ !~ %s", (APP_KEY_PATTERN,))
            keys = [r[0] for r in cur.fetchall()]
            cur.execute(f"SELECT DISTINCT deployment_id_ FROM act_re_procdef WHERE key_ !~ %s", (APP_KEY_PATTERN,))
            dep_ids = [r[0] for r in cur.fetchall()]
            cur.execute(f"SELECT id_ FROM act_re_procdef WHERE key_ !~ %s", (APP_KEY_PATTERN,))
            pd_ids = [r[0] for r in cur.fetchall()]

            counts['instances'] = write_csv(out / 'instances.csv', cur, """
                SELECT * FROM act_hi_procinst WHERE proc_def_key_ = ANY(%s) ORDER BY start_time_""", (keys,))
            cur.execute("SELECT id_ FROM act_hi_procinst WHERE proc_def_key_ = ANY(%s)", (keys,))
            inst_ids = [r[0] for r in cur.fetchall()] or ['-']
            counts['variables'] = write_csv(out / 'variables.csv', cur, """
                SELECT id_, proc_inst_id_, proc_def_key_, name_, var_type_, text_, text2_, long_, double_,
                       create_time_, state_ FROM act_hi_varinst WHERE proc_inst_id_ = ANY(%s)""", (inst_ids,))
            counts['activities'] = write_csv(out / 'activities.csv', cur, """
                SELECT * FROM act_hi_actinst WHERE proc_inst_id_ = ANY(%s) ORDER BY start_time_""", (inst_ids,))
            counts['details'] = write_csv(out / 'details.csv', cur, """
                SELECT id_, type_, proc_inst_id_, act_inst_id_, name_, var_type_, text_, text2_, time_
                FROM act_hi_detail WHERE proc_inst_id_ = ANY(%s) ORDER BY time_""", (inst_ids,))
            counts['runtime'] = write_csv(out / 'runtime.csv', cur, """
                SELECT 'execution' AS tbl, e.id_, e.proc_def_id_, NULL::text AS extra FROM act_ru_execution e
                  JOIN act_re_procdef p ON p.id_ = e.proc_def_id_ WHERE p.key_ = ANY(%s)
                UNION ALL
                SELECT 'job', j.id_, j.process_def_id_, j.type_ FROM act_ru_job j WHERE j.process_def_key_ = ANY(%s)
                UNION ALL
                SELECT 'incident', i.id_, i.proc_def_id_, i.incident_type_ FROM act_ru_incident i
                  JOIN act_re_procdef p ON p.id_ = i.proc_def_id_ WHERE p.key_ = ANY(%s)""", (keys, keys, keys))
            counts['op_log'] = write_csv(out / 'op_log.csv', cur, """
                SELECT * FROM act_hi_op_log
                WHERE deployment_id_ = ANY(%s) OR proc_def_id_ = ANY(%s) OR proc_def_key_ = ANY(%s)
                   OR proc_inst_id_ = ANY(%s) ORDER BY timestamp_""", (dep_ids, pd_ids, keys, inst_ids))
            counts['authorizations'] = write_csv(out / 'authorizations.csv', cur, """
                SELECT * FROM act_ru_authorization WHERE resource_id_ = ANY(%s) OR resource_id_ = ANY(%s)""",
                (keys, dep_ids))

            # payloads
            cur.execute("""
                SELECT d.id_, d.name_, d.deploy_time_, b.id_, b.name_, b.bytes_
                FROM act_re_deployment d JOIN act_ge_bytearray b ON b.deployment_id_ = d.id_
                WHERE d.id_ = ANY(%s) ORDER BY d.deploy_time_, b.name_""", (dep_ids,))
            expr_rows = []
            n = 0
            for dep_id, dep_name, deploy_time, ba_id, res_name, data in cur.fetchall():
                n += 1
                safe = re.sub(r'[^A-Za-z0-9._-]+', '_', f'{dep_name}_{res_name or ba_id}')
                p = out / 'payloads' / f'{n:03d}_{safe}'
                if not p.suffix:
                    p = p.with_suffix('.bpmn')
                raw = bytes(data)
                p.write_bytes(raw)
                text = raw.decode('utf-8', errors='replace')
                for m in re.finditer(r'(camunda:(?:expression|delegateExpression|class|resultVariable))\s*=\s*"([^"]*)"', text):
                    expr_rows.append([dep_id, dep_name, str(deploy_time), res_name, m.group(1), m.group(2)])
            counts['payloads'] = n
            with (out / 'expressions.csv').open('w', newline='') as f:
                w = csv.writer(f)
                w.writerow(['deployment_id', 'deployment_name', 'deploy_time', 'resource', 'attribute', 'value'])
                w.writerows(expr_rows)
            counts['expressions'] = len(expr_rows)

    files = sorted(p for p in out.rglob('*') if p.is_file())
    sums = {str(p.relative_to(out)): sha256(p) for p in files}
    (out / 'SHA256SUMS').write_text(''.join(f'{h}  {name}\n' for name, h in sums.items()))
    manifest = {
        'collected_at_utc': stamp, 'db_host': db_host, 'db_port': db_port, 'db_name': db_name,
        'db_user': db_user, 'db_server_time': str(db_now), 'db_version': db_version,
        'default_transaction_read_only': readonly, 'injected_key_filter': f'key_ !~ {APP_KEY_PATTERN}',
        'injected_keys': sorted(keys), 'row_counts': counts, 'sha256': sums,
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, default=str))
    zpath = out.with_suffix('.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(out.parent))
    print(json.dumps({k: v for k, v in manifest.items() if k != 'sha256'}, indent=2, default=str))
    print(f'bundle: {zpath}  ({zpath.stat().st_size} bytes)')


if __name__ == '__main__':
    main()
