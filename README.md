# test-liveness-readiness-check

Reproduces the support-thread scenario and proves the fix, so we can answer:

> "a liveness probe will restart the pod any time the check fails — is that
> before or after the retries?"

**Answer: after the retries.** Okteto maps the Compose `healthcheck.retries`
field to the Kubernetes `failureThreshold`, and a liveness probe only restarts
the container after that many *consecutive* failures. With `retries: 5` the pod
survives the first 4 failed checks and restarts on the 5th. The steps below let
you watch the `RESTARTS` count to prove it.

## What's here

- `app` — serves `/status`, which returns **503 forever**, so its healthcheck
  never passes.
- `dependent` — waits on `app` being healthy
  (`depends_on: condition: service_healthy`).

Healthcheck timing (from the thread): `start_period 5s`, `interval 5s`,
`timeout 3s`, `retries 5`.

---

## Setup (once)

```bash
okteto context use <your-okteto-url>
```

---

## Part 1 — Reproduce the issue (the hang)

**1. Turn liveness OFF.** In `compose.yaml`, under `app` → `healthcheck`, set:

```yaml
x-okteto-liveness: false
```

**2. Deploy:**

```bash
okteto deploy --wait
```

**3. In another terminal, watch the pod:**

```bash
kubectl get pods -w
```

**What you'll see — the bug:** `app` stays `0/1` with `RESTARTS = 0` forever.
`okteto deploy --wait` never finishes (in CI this hangs until GitHub cancels the
job).

```
NAME                   READY   STATUS    RESTARTS   AGE
app-xxxxxxxxxx-xxxxx   0/1     Running   0          3m     <- never restarts, never ready
```

Press `Ctrl+C` to stop watching, then `okteto destroy` to clean up before Part 2.

---

## Part 2 — Prove the fix

**1. Turn liveness ON.** In `compose.yaml`, set:

```yaml
x-okteto-liveness: true
```

(Leave `x-okteto-readiness: true` — the check must be both.)

**2. Deploy:**

```bash
okteto deploy --wait
```

**3. In another terminal, watch the RESTARTS column:**

```bash
kubectl get pods -w
```

**What you'll see — the fix.** The pod starts at `RESTARTS 0`. It does **not**
restart on the first failure. After the 5s grace period it fails a check every
5s, and only after the **5th** consecutive failure (`retries: 5`) does the
`RESTARTS` count go to `1` — about 25s later. Then it repeats:

```
NAME                   READY   STATUS    RESTARTS     AGE
app-xxxxxxxxxx-xxxxx   0/1     Running   0            10s    <- 5s grace + failing checks
app-xxxxxxxxxx-xxxxx   0/1     Running   1 (2s ago)   32s    <- restart #1 AFTER 5 retries
app-xxxxxxxxxx-xxxxx   0/1     Running   2 (1s ago)   61s    <- restart #2
```

The gap between `RESTARTS 0` and `RESTARTS 1` (~25s = 5 retries × 5s interval)
is the proof: the restart happens **after** the retries, not on the first
failure.

**4. After ~3 restarts, `okteto deploy` fast-fails instead of hanging:**

```
service 'dependent' cannot be deployed because dependent service 'app' is
failing its healthcheck probes: liveness probe failed
```

Clean up:

```bash
okteto destroy
```

---

## Tip: check restart count at any time

```bash
kubectl get pods                    # RESTARTS column
kubectl describe pod <pod-name>     # look for "Restart Count" and the Liveness/Readiness lines
```

## Optional: simulate a slow-to-start service

To test the caveat that a liveness probe can kill a merely-slow pod, set
`HEALTHY_AFTER` on `app` to the number of seconds before it turns healthy:

```yaml
environment:
  HEALTHY_AFTER: "40"   # 503 for the first 40s, then 200
```

If `start_period` + `interval × retries` is shorter than that warm-up time, the
pod gets killed before it recovers — which is why those values must be tuned for
legitimately slow starts.
