# Centralized default log masking keys

*Written 27 October 2026. Status: proposal for review by SRE, Security and the library owners. Part of [Log correlation-id, request-id and masking](request-id.md). Status of every pull request is on [Logging Improvement](README.md).*

## In short

The libraries bfi-go-pkg and bfi-java-pkg mask sensitive fields in the request and response bodies they log. The list of field names they mask, `DEFAULT_LOG_SENSITIVE_KEYS`, reaches a service only as an environment variable. That variable is copied, value and all, into each service's values file. Today there are **366 copies** on `master`. Each change to the list needs pull requests in two repositories and a restart of every service that has a copy.

This page proposes **one list in one place**. Kubernetes mounts it as a file **only into pods of services that use bfi-go-pkg or bfi-java-pkg**. Every other pod is left unchanged. The libraries re-read the file about once a minute. A change to the list then reaches every running service in about two minutes, with no pull request per service and no restart.

## Problem statement

1. **The list exists in hundreds of copies.** A pod sees only its own environment. GitHub organisation variables never reach a pod. So the 83 names are written into each values file by a script.
2. **Every change is a large, risky rollout.** Changing one name means editing every copy, merging pull requests in app-deployment and bfi-app-deployment, and restarting every service whose env changed. Both libraries read the list once, at startup.
3. **Restarts cause outages.** The SIT/UAT rollout on 20 October restarted Keycloak in UAT, which runs as one replica. Keycloak was down from 08:02:48 to 08:22:48 UTC. During that time `bpm`, `cnv`, `notification` and `notification-v2` failed to start.
4. **The copies drift and break.** Other teams keep adding env vars at the end of the same blocks. The open masking pull requests conflicted with `master` three times in one week. A script edits a text file it does not fully understand, so it makes mistakes (see the findings).
5. **The organisation variable is not the source of truth in practice.** Editing it changes nothing in any service until someone runs the sync script and merges the result. Nothing warns anyone when the two differ.

## Findings

### How the list reaches a service today

| Step | What happens |
|---|---|
| Source | The GitHub organisation variable `DEFAULT_LOG_SENSITIVE_KEYS`. Only organisation owners can read it. |
| Copy | `bravo-analysis/tools/sync_default_sensitive_keys.py` writes the value into each `values-<env>.yaml` env block. |
| Deploy | Argo CD applies the values files. The deploy workflows in `bfi-base-template` change only `*.image.tag`. None of them reads the organisation variable. |
| Read | Go `internal/envdefault` and Java `MaskingValueUtil` read the env variable when the service starts. |

### What it has cost so far

| Date | Event |
|---|---|
| 13 Oct | Decision: no list built into the libraries. The baseline comes only from the env variable. |
| 20 Oct | SIT and UAT pull requests merged: [app-deployment#14328](https://github.com/bfi-finance/app-deployment/pull/14328) (234 files) and [bfi-app-deployment#4114](https://github.com/bfi-finance/bfi-app-deployment/pull/4114) (168 files). UAT Keycloak was down for 20 minutes. |
| 20 Oct | The production pull requests were split into stacks of batches, so one merge does not restart every service at once. |
| 22–24 Oct | The batches were trimmed, restored and trimmed again while the scope was settled. |
| 26 Oct | SIT/UAT clean-up [app-deployment#14524](https://github.com/bfi-finance/app-deployment/pull/14524) merged (36 files). |
| 27 Oct | Still open: production stacks [#14466–#14473](https://github.com/bfi-finance/app-deployment/pull/14466) (70 files) and [bfi-app-deployment#4151–#4154](https://github.com/bfi-finance/bfi-app-deployment/pull/4151) (32 files), and clean-up [bfi-app-deployment#4175](https://github.com/bfi-finance/bfi-app-deployment/pull/4175) (45 files). |

In total, 19 pull requests and four rounds of rework for one list. Production services still do not have the list.

### Copies on `master` (27 October)

| Repository | Files | Apps | Environments |
|---|---|---|---|
| app-deployment | 198 | 84 | sit 78, uat 75, dev 29, sit-sharia 8, uat-sharia 8 |
| bfi-app-deployment | 168 | 74 | dev 57, uat 32, test 32, sit 30, digital-dev/test/uat 12, digital-prod 4, sit-2 1 |

When the open pull requests merge, there will be about 423 copies.

**A copy reached production by mistake.** The "non-production" pull request #4114 also wrote the list into four production files: `values-digital-prod.yaml` for `bfi-digital-ui`, `bfi-digital-ui-x`, `bfi-digital-web-api` and `bfi-digital-web-dashboard-api`. The script decides "production" from the file-name prefix `values-prod`, and `values-digital-prod` does not start with it. The extra entry is harmless, but those four apps restarted outside the batch plan. This is the kind of mistake that copying by script invites.

### What the cluster offers (SIT/UAT cluster `dev-bravo-cluster`, checked 20 October)

- **Kyverno 1.14.2** is installed and healthy: admission, background, cleanup and reports controllers, with its mutating webhooks registered. It has **no policies yet**, so a new policy collides with nothing.
- **Reloader v0.0.118** runs, with `reloader.stakater.com/auto: "true"` on 101 of 154 deployments in `sit`. Reloader restarts a deployment when any ConfigMap or Secret named in its template changes. So a shared ConfigMap or Secret referenced from deployments would restart about 100 deployments at once on every change.
- **Sealed Secrets** is installed. External Secrets and the Secret Store CSI driver are not.
- No service shares a Secret through `envFrom`. Every Secret is referenced key by key in each manifest, for example `sit-internal-service-key-secret` in 66 deployments.
- App containers run next to the sidecars `istio-proxy` and `cloud-sql-proxy`.
- The production cluster is not visible to this analysis. **SRE must confirm that Kyverno runs there too.**

### What the libraries do today (checked 27 October)

- **Java** (`bfi-java-pkg` master `f313f5a`, core 0.1.4, starter 0.1.5): `MaskingValueUtil` reads the env variable once, when the class loads. Both production callers, `RequestLoggingFilter` and `BravoFeignLogger`, ask `MaskingValueUtil` for the key set on every call. So one change, in one class, is enough to make the list reloadable.
- **Go** (`bfi-go-pkg` main `165d034`, masking code unchanged since `3026177`): `internal/envdefault` reads the env. The HTTP middleware, the HTTP client transport and the gRPC interceptor each read the list once, when they are built. Each keeps a fixed lookup table in a closure. A reloadable list needs one shared source, plus a small change where those tables are built: `internal/bodylog.Config.MaskFields` and the two query-parameter scrubbers.

## Proposal

### How it works

```
git: one ConfigMap "bfi-log-masking-keys": the masked names and the allow-list "library-apps",
     reviewed by pull request
  │  Argo CD applies it to the namespace bfi-logging
  ▼
Kyverno rule 1: copy the masked names into every app namespace and keep the copies in step
  ▼
Kyverno rules 2 and 3: when a pod of a service in the allow-list "library-apps" is created,
  mount it read-only as /etc/bfi/logging/default-log-sensitive-keys and set
  DEFAULT_LOG_SENSITIVE_KEYS_FILE. Pods of all other services are not changed.
  ▼
kubelet updates the mounted file in running pods (about 1–2 minutes after a change)
  ▼
bfi-go-pkg / bfi-java-pkg re-read the file every 60 seconds and use the new list at once
```

Five design choices make it safe:

1. **Only services on the libraries get it.** The central ConfigMap holds a second list, `library-apps`: the services that use bfi-go-pkg or bfi-java-pkg. Kyverno changes a pod only if its `app.kubernetes.io/name` label is on that list. Other pods, such as Keycloak, KrakenD or a Java service on plain logback, are never touched. On top of that, only the two libraries ever read the file.
2. **Kyverno changes pods, not Deployments.** Argo CD sees no drift. Reloader sees no new reference, so it restarts nothing.
3. **New pods only.** The policy acts when a pod is created. Services get the file at their next normal deploy. There is no mass restart to roll it out.
4. **A file, not an env variable.** Kubernetes refreshes a mounted ConfigMap file inside a running pod. It never refreshes an env variable. The mount must not use `subPath`, because a `subPath` mount is never refreshed.
5. **Safe fallbacks.** If the file is missing, the libraries use the `DEFAULT_LOG_SENSITIVE_KEYS` env variable, as today. If the file cannot be read, or is empty, they keep the last good list. If Kyverno is down, pods still start (`failurePolicy: Ignore`), just without the file.

### Change 1: the libraries

Both libraries get the same behaviour:

| Situation | List used |
|---|---|
| `DEFAULT_LOG_SENSITIVE_KEYS_FILE` names a readable, non-empty file | the file's names |
| file missing | the `DEFAULT_LOG_SENSITIVE_KEYS` env variable (today's behaviour) |
| file unreadable or empty after a good read | the last good list |
| neither file nor env | no baseline (today's behaviour) |

The service's own `LOG_SENSITIVE_KEYS`, and Go's per-direction lists, still add to the baseline as today. The file replaces only the baseline.

**Go (bfi-go-pkg), draft:** a new package `internal/maskkeys` holds the baseline.

```go
// Package maskkeys holds the organisation's baseline of field names to mask.
// It reads them from the file named by DEFAULT_LOG_SENSITIVE_KEYS_FILE and re-reads
// that file every minute. Without the file it uses DEFAULT_LOG_SENSITIVE_KEYS.
package maskkeys

const (
	FileEnv  = "DEFAULT_LOG_SENSITIVE_KEYS_FILE"
	ListEnv  = "DEFAULT_LOG_SENSITIVE_KEYS"
	interval = time.Minute
)

type snapshot struct{ names map[string]struct{} } // lowercase names

var (
	current atomic.Pointer[snapshot]
	start   sync.Once
)

// Has reports whether name, in any case, is in the baseline. Safe for concurrent use.
func Has(name string) bool {
	start.Do(begin)
	_, ok := current.Load().names[strings.ToLower(name)]
	return ok
}

func begin() {
	current.Store(load(nil))
	go func() {
		for range time.Tick(interval) {
			current.Store(load(current.Load()))
		}
	}()
}

// load returns the file's list, or the env list when there is no file.
// On a read error, or an empty file after a good read, it returns last.
func load(last *snapshot) *snapshot { /* … */ }
```

The scrubbers then look a name up in two places, the component's own fixed table and the baseline, instead of one merged table:

```go
// in internal/bodylog.Config.MaskFields and the two query-parameter scrubbers
match := func(key string) bool { return own[key] || maskkeys.Has(key) }
```

`internal/envdefault` stops adding `DEFAULT_LOG_SENSITIVE_KEYS` to the per-component lists, because `maskkeys` now owns the baseline. Tests replace `t.Setenv` with a temporary file and a package-level reload hook.

**Java (bfi-java-pkg, logging-core), draft:** a new class holds the baseline. Core has no Spring, so it uses plain JDK classes.

```java
/** The organisation's baseline of field names to mask, from a file that is re-read every minute. */
final class MaskingKeys {
  static final String FILE_ENV = "DEFAULT_LOG_SENSITIVE_KEYS_FILE";

  private record Snapshot(Set<String> baseline, Set<String> withServiceKeys) {}

  private static volatile Snapshot current = load(null);

  static {
    ScheduledExecutorService timer = Executors.newSingleThreadScheduledExecutor(r -> {
      Thread t = new Thread(r, "bfi-masking-keys");
      t.setDaemon(true); // never keeps the JVM alive
      return t;
    });
    timer.scheduleWithFixedDelay(() -> current = load(current), 60, 60, TimeUnit.SECONDS);
  }

  static Set<String> baseline() { return current.baseline(); }
  static Set<String> withServiceKeys() { return current.withServiceKeys(); }

  /** File list, else env list. Keeps last on a read error or an empty file. */
  static Snapshot load(Snapshot last) { /* … */ }

  static void reloadNow() { current = load(current); } // for tests
}
```

`MaskingValueUtil.sensitiveKeys()` returns `MaskingKeys.withServiceKeys()`, and `defaultSensitiveKeys()` returns `MaskingKeys.baseline()`. Both callers already ask on every call, so nothing else changes.

These drafts show the design. They have not been compiled.

### Change 2: the central list

One ConfigMap holds both lists. It lives once in git, in SRE's platform repository. Argo CD applies it to a namespace of its own:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: bfi-log-masking-keys
  namespace: bfi-logging
data:
  # The field names to mask (the 83 names in use today).
  default-log-sensitive-keys: >-
    nik,ktp,ktp_number,ktp_data,identity_number,id_number,idnumber,legal_id_number,
    spouse_identity_number,npwp,npwp_number,tax_number,passport_number,password,…
  # The services that may receive them: pod label app.kubernetes.io/name, * allowed.
  library-apps: >-
    ms-agency,ms-agent,…,*-disbursement-ssf-v*,…
```

- A change to either list is one pull request to this file. CODEOWNERS can require Security's review.
- The libraries accept names separated by commas or new lines, so the file can stay readable.
- Only `default-log-sensitive-keys` is copied into the app namespaces, because a pod can mount only a ConfigMap from its own namespace. Kyverno reads `library-apps` from the source, so the allow-list exists once.

**What goes on `library-apps`.** The same services as the production batch pull requests: every service whose repository depends on any module of bfi-go-pkg or bfi-java-pkg (rule decided 24 October). Each entry is the pod's `app.kubernetes.io/name` label. For the shared chart that is `microservices-http.image.name` in the app's `values.yaml`, for example `ms-branch`. That was checked on a live SIT pod. LORA Temporal workers name their pods `<namespace>-<service>-v<version>`, so they get one wildcard pattern each.

| Source | Entries |
|---|---|
| app-deployment (55) | `ms-agency`, `ms-agent`, `ms-agent-marketing`, `ms-aqm-service`, `ms-asset-pricing`, `ms-assistance`, `ms-audit-trail`, `ms-auth-service`, `ms-backoffice`, `ms-bfi-connect`, `ms-bpm`, `ms-branch`, `call-gateway-service`, `ms-cnv`, `collection-consumer-registry`, `conversation-gateway-service`, `ms-customer`, `ms-customer-app-loan`, `ms-customer-bff`, `ms-data-admin`, `bravo-database-catalog`, `doc-renderer`, `ms-document`, `ms-document-hub`, `ms-edoc`, `ms-gen-ai`, `ms-gold-service`, `ms-insurance`, `ms-integrity`, `ms-inventory-management`, `ms-kyc-proxy`, `ms-kyc-sign`, `ms-lms-ops`, `ms-lora-cdc-bridges`, `ms-lora-customer-app`, `diff-inspector`, `ms-lora-gateway`, `ms-lora-schema`, `ms-lora-task`, `ms-notification`, `ms-bravo-notification`, `ms-onboarding`, `ms-partnership`, `ms-partnership-provisioning`, `ms-payment`, `ms-pbf`, `portfolio-management-service`, `ms-repeat-order`, `ms-robot-controller`, `ms-rule-engine`, `ms-samsat-resolver`, `ms-scheduling`, `ms-supplier`, `ms-unsecured-v2`, `ms-user-iam` |
| LORA workers (9 patterns) | `*-disbursement-ssf-v*`, `*-disbursement-ssf-task-v*`, `*-task-disbursement-ssf-v*`, `*-mou-ssf-v*`, `*-task-mou-ssf-v*`, `*-ndf-4w-v*`, `*-task-ndf-4w-v*`, `*-dp-ndf-v*`, `*-task-dp-ndf-v*` |
| bfi-app-deployment (32) | `ms-bfi-agency-api`, `ms-bfi-audit-api`, `ms-bfi-incentive-api`, `ms-bfi-insurance-api`, `ms-bfi-omni-middleware-api`, `ms-bfi-operation-api`, `ms-otrs-report`, `ms-bfi-panel-dashboard-api`, `ms-bfi-payment-api`, `ms-bfi-task-allocation`, `ms-bfi-treasury-backoffice-api`, `ms-bfi-treasury-bank-facility-api`, `ms-bfi-treasury-batching-api`, `ms-bfi-treasury-disbursement-api`, `ms-bfi-treasury-gateway-api`, `ms-bfi-treasury-notification-api`, `ms-bfi-treasury-time-deposit-api`, `ms-bfi-user-management-api`, `ms-ams`, `ms-findigital-ars`, `ms-findigital-costcontrol`, `ms-findigital-fpa`, `ms-findigital-onegate`, `ms-findigital-scorebranch`, `ms-findigital-shareholders`, `ms-pcms-accounting-be`, `ms-sa-tools`, `ms-sampling-ams`, `ms-findigital-whistleblower`, `ms-pos-tools`, `ms-rabbit`, `ms-user-iam` |

`user-iam` in both repositories uses the label `ms-user-iam`, so the list has 95 entries. The labels come from the values files. **SRE checks them against live pods** with `kubectl get pods -A -L app.kubernetes.io/name` before the policy goes live.

When a service starts using one of the libraries, its label is added to `library-apps` by a pull request to the same file. Nothing changes in the service's own manifest.

### Change 3: the Kyverno policy

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: bfi-log-masking-keys
  annotations:
    policies.kyverno.io/title: Give the log masking list to services on bfi-go-pkg or bfi-java-pkg
    policies.kyverno.io/description: >-
      Copies the masked field names into each app namespace, and mounts them as a read-only file
      into pods of services listed in library-apps. Every other pod is left unchanged.
spec:
  background: false
  webhookConfiguration:
    failurePolicy: Ignore   # if Kyverno is down, pods still start (without the file)
    timeoutSeconds: 5
  rules:
    - name: copy-list-into-app-namespaces
      match:
        any:
          - resources:
              kinds: [Namespace]
              names: [sit, uat, prod, sit-sharia, uat-sharia, prod-sharia]   # SRE completes this list
      generate:
        generateExisting: true
        synchronize: true          # a change to the source is copied everywhere
        apiVersion: v1
        kind: ConfigMap
        name: bfi-log-masking-keys
        namespace: "{{ request.object.metadata.name }}"
        clone:
          namespace: bfi-logging
          name: bfi-log-masking-keys
    - name: add-volume
      match:
        any:
          - resources:
              kinds: [Pod]
              namespaces: [sit, uat, prod, sit-sharia, uat-sharia, prod-sharia]   # same list as above
              operations: [CREATE]
      context:
        - name: maskingConfig
          configMap:
            name: bfi-log-masking-keys
            namespace: bfi-logging          # the one source; the allow-list is never copied
        - name: libraryApps
          variable:
            jmesPath: split(maskingConfig.data."library-apps", ',')
            default: []
      preconditions:
        all:
          - key: "{{ request.object.metadata.labels.\"app.kubernetes.io/name\" || '' }}"
            operator: AnyIn                 # entries may use * wildcards (LORA worker versions)
            value: "{{ libraryApps }}"
      mutate:
        patchStrategicMerge:
          spec:
            volumes:
              - name: bfi-log-masking-keys
                configMap:
                  name: bfi-log-masking-keys
                  optional: true   # a pod still starts if the ConfigMap is missing
    - name: mount-into-app-containers
      match:
        any:
          - resources:
              kinds: [Pod]
              namespaces: [sit, uat, prod, sit-sharia, uat-sharia, prod-sharia]   # same list as above
              operations: [CREATE]
      context:
        - name: maskingConfig
          configMap:
            name: bfi-log-masking-keys
            namespace: bfi-logging
        - name: libraryApps
          variable:
            jmesPath: split(maskingConfig.data."library-apps", ',')
            default: []
      preconditions:
        all:
          - key: "{{ request.object.metadata.labels.\"app.kubernetes.io/name\" || '' }}"
            operator: AnyIn
            value: "{{ libraryApps }}"
      mutate:
        foreach:
          - list: request.object.spec.containers
            preconditions:
              all:
                - key: "{{ element.name }}"
                  operator: AnyNotIn
                  value: [istio-proxy, cloud-sql-proxy]
            patchStrategicMerge:
              spec:
                containers:
                  - name: "{{ element.name }}"
                    volumeMounts:
                      - name: bfi-log-masking-keys
                        mountPath: /etc/bfi/logging   # whole directory, no subPath, so it stays fresh
                        readOnly: true
                    env:
                      - name: DEFAULT_LOG_SENSITIVE_KEYS_FILE
                        value: /etc/bfi/logging/default-log-sensitive-keys
```

**Tested offline on 27 October** with the Kyverno CLI 1.14.2, the same version as the cluster, with the full allow-list of 95 entries:

| Pod (label `app.kubernetes.io/name`) | Uses the libraries? | Result |
|---|---|---|
| `ms-branch` | yes, Java starter | file mounted into the app container. `istio-proxy` and `cloud-sql-proxy` untouched. Existing env kept. |
| `prod-disbursement-ssf-v0-0-1` | yes, LORA Go worker | file mounted (matched by `*-disbursement-ssf-v*`) |
| `ms-bfi-payment-api` | yes, bfi Java | file mounted |
| `ms-master` | no, plain logback | **not changed** |
| `keycloak` | no, third-party | **not changed** |
| `ms-branch` in `kube-system` | (not an app namespace) | **not changed** |

- The mount is read-only and has no `subPath`, so the file stays fresh.
- The CLI test supplies the ConfigMap's contents itself. The live lookup of `library-apps`, and the namespace-copy rule, need a cluster. SRE should test both with `kubectl apply --dry-run=server` and on one SIT pod.

### Rollout

1. **Libraries.** Release bfi-go-pkg and bfi-java-pkg (core 0.1.6, starter 0.1.7) with file support and the env fallback. Without the file, nothing changes.
2. **SIT/UAT cluster.** SRE checks the allow-list against live pod labels, then adds the source ConfigMap and the policy, and runs the checks listed below.
3. **Production cluster.** SRE confirms Kyverno runs there, then repeats step 2.
4. **Services.** Each service gets the file at its next normal deploy. It uses the file once it runs the new library version, which is the same bump it needs for masking anyway.
5. **Retire the copies.** Keep the env copies as a fallback while the file route proves itself. Then remove them, in batches, at a quiet time. Retire the organisation variable, or keep it only if a workflow keeps it equal to the git file.

Checks for step 2, and again for step 3:

- A newly created pod of a listed service has the mount. A pod of an unlisted service does not.
- A change to the list reaches a running pod within about two minutes, with no restart.
- The pod's logs mask a field that was added only in the file.

**The open production stacks** (#14466–#14473, #4151–#4154) are still useful in the meantime. Until the file route is live in production, a service on the new libraries masks nothing there without them. Merge them as the fallback layer, or hold them if the file route can go live first.

## Options compared

| Option | One place to edit? | Change reaches running pods without a restart? | Per-service manifest changes? | Main problem |
|---|---|---|---|---|
| **ConfigMap file + Kyverno + library reload (proposed)** | yes, one file in git, for the names and the services | yes, about 2 minutes | none. Only services on the allow-list are touched. | needs Kyverno in every cluster, a library change, and an allow-list kept current |
| Env copied into every values file (today) | no, about 400 copies | no, restart needed | every service, every change | rollouts, restarts, drift, script mistakes |
| Env from a shared ConfigMap (`configMapKeyRef`) | yes | no, read at startup only | one-time change in every manifest | Reloader restarts about 100 deployments at once on each change |
| Env from a shared Secret (`secretKeyRef`) | yes | no, read at startup only | one-time change in every manifest | same Reloader problem. The list is not secret, and as a Sealed Secret reviewers cannot read its diff. |
| Secret mounted as a file | yes | yes | none, with Kyverno | works like the ConfigMap, but the list is not secret: tighter RBAC and an unreadable diff for no gain |
| Libraries fetch the list over HTTP | yes | yes | none | puts a network call in the logging path, and a new service to run |
| List built into the libraries | yes, in the library | no, needs a release and a bump in every service | every service, every change | slowest path for each change |
| GitHub organisation variable alone | yes | not at all | — | pods cannot see it |

### About a Kubernetes Secret

A Secret works mechanically, but it is not better than a ConfigMap here:

- **As an env variable** (`secretKeyRef`), a Secret is read only at startup, like any env variable. Every manifest needs a one-time change to reference it. After that, each change to the Secret would make Reloader restart every deployment that references it, about 100 in `sit` alone.
- **As a mounted file**, a Secret refreshes in running pods exactly like a ConfigMap. But the list holds field names, not secret values. A Secret brings stricter access rules. With Sealed Secrets, the file in git is encrypted, so reviewers cannot see which names were added or removed.

A ConfigMap gives the same behaviour, with a readable diff for Security to review.

## Risks

| Risk | Mitigation |
|---|---|
| Kyverno is down when a pod starts | `failurePolicy: Ignore`: the pod starts without the file and uses the env fallback. Run more than one Kyverno admission replica in production. |
| Kyverno adds a webhook call to every pod creation in the app namespaces | The rules are limited to the app namespaces, with a 5-second timeout. A pod not on the allow-list is skipped after one label check. |
| Production has no Kyverno | SRE confirms before step 3. Until then, the env copies stay. |
| A library service is missing from `library-apps`, or its label differs | It gets no file and keeps using the env variable, or nothing. Check the list against live pod labels before go-live. Add a service to the list when it adopts a library. |
| A bad edit empties the list | The libraries never switch to an empty list after a good read. Review by pull request, with CODEOWNERS. |
| Up to about 2 minutes before a change is in use | Fine for this list. |
| A service on an old library version ignores the file | It keeps using the env variable. Bumping the library is needed for masking anyway. |

## Decisions needed

1. **Owner of the lists:** Security, SRE or Platform. This decides who must approve changes to the masked names and to `library-apps`.
2. **Source of truth:** the git file (recommended), or the organisation variable with a sync workflow.
3. **Library work:** who builds and releases the two library changes.
4. **The open production stacks:** merge them now as the fallback layer, or hold them until the file route is live.

## Related finding

The gRPC request logger in bfi-go-pkg writes the body of an **error** response (`res_body`, `grpc/grpcinterceptor/requestloggerinterceptor/server.go`, unary error path) without passing it through the masking function. This matters only if error details can hold sensitive fields. Fix it in the same Go change.
