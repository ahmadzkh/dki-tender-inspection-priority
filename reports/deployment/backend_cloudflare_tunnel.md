# Backend Cloudflare Tunnel Verification

Status: blocked for durable production-style deployment.

## Local Docker Source Service

Backend Docker runtime was verified through `docker compose`:

- container image: `dki-tender-inspection-api:local`
- health status: `healthy`
- local health response: `ok`, artifact ready `true`
- local metadata: model version `414f1691d2bccdd9`, total records `1276`

## Public Tunnel Attempt

`cloudflared tunnel list` could not access a named tunnel because no origin certificate is configured on this machine:

```text
Error locating origin cert: client didn't specify origincert path
```

A temporary Cloudflare Quick Tunnel was started only to verify public-path behavior. Quick Tunnel output explicitly states that account-less tunnels have no uptime guarantee and are for experiments, not production.

Public smoke through the temporary tunnel passed while the local tunnel process was running:

| Check | Result |
|---|---|
| `/api/v1/health` | `ok`, artifact ready `true` |
| `/api/v1/meta` | model version `414f1691d2bccdd9`, total records `1276` |
| `/api/v1/summary` | total packages `1276` |
| `/api/v1/rankings?top_n=1&size=1` | one item, top package `57740127` |
| `/api/v1/export.csv?year=2026` | CSV disclaimer present |
| CORS from `http://localhost:3000` | allowed |

## Blocker

`TASK-BE-011` remains incomplete because durable Cloudflare Tunnel deployment requires a logged-in Cloudflare account or pre-created named tunnel credentials/config on the target VPS/server. No secret tunnel credentials should be generated into Git.

## Required Next Step

On the approved VPS/server:

1. authenticate Cloudflare Tunnel outside Git;
2. create or select a named tunnel;
3. route it to `http://127.0.0.1:8000`;
4. set production `CORS_ORIGINS` to the final Vercel origin;
5. rerun public smoke for health, meta, summary, ranking, detail, export, and CORS;
6. only then mark `TASK-BE-011` and `TASK-FE-012` complete.
