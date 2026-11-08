# Reviewed campus startup profiles

The launcher can seed and serve six reviewed model/data combinations. The
default remains the historical 19/16 baseline. C15 is an explicit prepared profile,
not a completed physical survey or a public rollout. The existing 8001 process
and its database have not been upgraded by this delivery.

| `--profile` | Reviewed places / connections | Frontend selection |
| --- | --- | --- |
| `base` (default) | 19 / 16 | C14 base, historical flat data |
| `ucc-two-floors` | 64 / 59 | C14 two-floor profile |
| `ucc-first-floor-stair-review` | 19 / 16 | C14 with mapped first-floor stairs |
| `ucc-two-floors-stair-review` | 64 / 59 | C14 two-floor and mapped first-floor stairs |
| `ucc-two-floors-c15` | 68 / 63 | C15 data, C16 set with C17 floor-2 ramp |
| `ucc-three-floors-c16` | 110 / 102 | Three-floor data, C16 set with C17 floor-2 ramp |
| `ucc-four-floors-c18` | 150 / 139 | Floors 0–3: C18 piso cero and floor 1, C17 floor 2, C16 floor 3 |
| `ucc-six-floors-c18` | 235 / 218 | Floors 0–5: adds Block A floors 4 and 5 (C16) with six classroom entrances |

These counts describe the reviewed campus data. Unrelated scoped blocks are
preserved, so a database containing those records has larger totals. New connected
blocks also need a compatible reviewed frontend binding before navigation.

## Existing command

```powershell
venv/Scripts/python.exe -m scripts.run_campus --port 8001
```

With no profile argument, this keeps the historical baseline. An occupied port
is rejected **before the database is opened or seeded**. The launcher reserves
its actual socket and passes it to Uvicorn, avoiding a free-port check/start race.
It never stops another service. `/app/`, `/docs`, `/openapi.json` and all API
routes remain available.

## Isolated C15 rehearsal

Choose a new temporary file instead of the live database:

```powershell
$campusReviewDirectory = Join-Path $env:TEMP ('uninav-rehearsal-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $campusReviewDirectory
$campusReviewDatabase = Join-Path $campusReviewDirectory 'campus.db'
venv/Scripts/python.exe -m scripts.run_campus --profile ucc-two-floors-c15 --database $campusReviewDatabase --port 0
```

Port `0` lets the OS reserve an unused loopback port. `UNINAV_CAMPUS_READY=`
prints the reserved URL, database, selected profile, counts and scoped revisions
after the seed. Uvicorn then starts the API; wait for `/health` to return 200
before using it. The browser fixture does this automatically and closes only
its own process tree. The normal launcher seeds the existing demo users and
preserves existing credentials and roles; it does not create an isolated test
destination.

For seed-only preparation of that explicit review file:

```powershell
venv/Scripts/python.exe -m scripts.seed_campus --profile ucc-two-floors-c15 --database $campusReviewDatabase
```

`--database` explicitly selects a file. Otherwise `UNINAV_DATABASE_URL` is
honored, falling back to `uninav-campus.db`. The selected URL is configured
before importing the SQLAlchemy engine or FastAPI. The original sample
`uninav.db`, including an alias to that same file, is protected. Seed-only or
alternate-port attempts against the canonical `uninav-campus.db` are also
refused while the known legacy 8001 service listens. These checks protect the
current development setup; they are not a general distributed database lease.

## Versioning and restart behavior

`data/campus-profiles.json` pins each input's scope, revision and canonical
payload hash. Whitespace and CRLF do not alter that digest. A changed input is
rejected before creating tables; accepting a new export requires a reviewed
dataset/profile revision and matching frontend resources.

The first-floor stair patch is composed with its baseline **in memory** into a
complete `startup-first-floor-stairs-v1` scope. The two classified profiles share
that exact revision and payload. Restarts import only their complete effective
scopes; they do not replay the flat baseline into already upgraded data.

A new database or recognized unscoped legacy floor is bootstrapped once, retaining
legacy IDs. Target scopes are then imported in one outer transaction, along with
demo-user creation. Failure or caller rollback leaves no partial hall or upper
floor. Repeated startup is idempotent and preserves users, history and other
scoped blocks. Known revision downgrades and profiles omitting an installed UCC
scope are rejected; records are not removed to force a profile match. Use a
separate file or a reviewed migration for such transitions.

The legacy `scripts.seed_ucc_floor1` API remains available to older callers. Its
old baseline still detects drift instead of reverting newer C15 data. The sample
`scripts.seed.py` was not modified by this work.

## Remaining activation work

The 8001 service still exposes the older loaded contract and 19/16 data. Do not
import behind it. A future coordinated switch needs a verified backup and a
service running the matching API, seed profile and frontend. Existing user
processes remain running during the isolated rehearsal.

C15 data retains pending physical B laboratory, sloped-hall, western and upper
A/B junction levels. Its 68/63 profile keeps floor 3 as a preview. The separate
110/102 profile adds a reviewed 2-to-3 east stair and three source-confirmed
Computer Lab entrances on floor 3; floors 0/4/5 remain previews. Its C16 physical
stair rises from world 6.18 to 9.87, with floor metadata retained until arrival.
The 42-place/39-connection scope is applied after the two unchanged C15 scopes.
Reverting that database to a two-floor profile is rejected instead of deleting
the new scope. Use `--profile ucc-three-floors-c16` with an explicit temporary
file and port 0 to rehearse it. The default, real database and user processes
remain unchanged. Evidence is in frontend `docs/verification/floor3/`.

The 150/139 `ucc-four-floors-c18` profile adds the piso cero scope (40 places /
37 connections) after the three unchanged scopes. The C18 east tower rises 3.50 m
from Block A on floor 0 (world -0.63) to the floor-1 north junction (world 2.87).
Its waypoints keep floor-0 metadata until the upper endpoint. Two source-backed
destinations are added: the Clinical Simulation Laboratory through doorway D32
and the waiting room through the drawn facade sliding door. Avoiding stairs
rejects travel between floor 0 and the other floors; the elevators are not
modelled as operating stops. Reverting to the three-floor profile is rejected
instead of deleting the scope. Rehearse it with `--profile ucc-four-floors-c18`,
an explicit temporary file and port 0. Evidence is in frontend
`docs/verification/floor0/`.

The 235/218 `ucc-six-floors-c18` profile adds `ucc:floor45-connection`
(85 places / 79 connections) after the four scopes above.
- **Towers:** the C16 east tower runs 3 → 4 (world 9.87 → 13.37) and 4 → 5
  (13.37 → 16.87), each with 25 waypoints.
- **Floor 4:** a drawn partition closes the corridor west of the 3–4 arrival,
  so the 4–5 foot is reached north of it, along y 55.95.
- **Destinations:** six classrooms, 420 A, 421 A and 422 A (D27, D26, D28) and
  512 A, 513 A and 515 A (D18, D19, D11).
- **Restrictions:** avoiding stairs rejects travel between floors. Reverting to
  `ucc-four-floors-c18` is rejected.

C17's floor-2 junction ramp is integrated in the two compatible profiles above;
the data-profile identifiers and 68/63 and 110/102 bindings stay unchanged. No
public graph connection across that ramp is added. Its geometry is rehearsed
using disconnected temporary ramp points and the real FastAPI. The drawn strip
is step-free; accessibility is not certified. Block A/B identities now record
the user's confirmation, without promoting derived floor levels to confirmed
survey measurements. See frontend `docs/verification/c17/`.
Other destinations, level zones and public activation remain pending; this
delivery does not complete H2 or the three project plans.

## Activating the complete campus on the real database

`scripts/activate_campus.ps1` switches the real `uninav-campus.db` to a reviewed
profile, by default `ucc-six-floors-c18` (235 places / 218 connections), and
restarts the campus service on port 8001. Run it yourself from the backend
folder:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\activate_campus.ps1
```

The script:
1. stops only the `scripts.run_campus` process listening on the port, and
   refuses if another program serves it;
2. copies the database to `backups\` before any change;
3. starts the launcher with `--profile` in the background, logging to `logs\`,
   and waits for `/health`.

The sample service on port 8000 and `uninav.db` are not touched.

**Rehearsal.** On a copy of the real database, the upgrade went from 19/16 to
235/218 and kept all 3 users and 270 route visits.

**Rollback.** Older profiles refuse to remove installed scopes, so roll back by
restoring the backup:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\activate_campus.ps1 -Restore backups\<backup-file>.db
```

