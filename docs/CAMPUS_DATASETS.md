# Versioned campus datasets

`Building` remains the API's place entity. Its numeric `id` survives renaming and
legacy adoption. `code` is a persistent external identifier, immutable through
the ordinary update endpoints. The graph uses numeric IDs as string keys in the
existing academic graph implementation. The old unique `name` remains a routing
alias for compatibility; `display_name` is the human label and may repeat on
different floors. Search covers both fields. The frontend uses the visible label
in its directory, markers and instructions.

Places optionally identify `block_code` and `floor_code`. These are source codes,
not inferred physical assignments. The integrated C2 floor is `ucc-first-floor`;
its physical A/B partition remains derived in the source catalogue. No room has
been reassigned to a physical block. No upper-floor places or vertical edges are
added by this migration.

`elevation_m` is world Y in metres; API `(x, y)` becomes `(x, elevation_m, -y)`.
`elevation_source` records its provenance. Legacy null elevations use the explicit
`effective_elevation_m` response field, currently `floor * 3.5`. The C2 dataset
declares 3.5 m with provisional flat-model provenance. This is not a survey datum.
Future floor datasets must specify their own elevations and sources.

Routes retain `path`, endpoint names and existing step fields. Calculate,
compare and multi-stop responses also return `waypoints`: place ID/code, label,
plan coordinates, elevation and floor/block codes. Steps include endpoint IDs,
path ID and connection code. The frontend validates these against the loaded
places and directed edges before moving; it accepts legacy name responses from
already-running older servers. Model/data binding hashes remain unchanged.

The route cost is at least the 3D straight-line distance at the stored elevations.
A* still uses its admissible 2D Euclidean heuristic, which cannot overestimate that
cost. Both A* and Dijkstra remain in FastAPI.

## Migrate and seed the existing real campus

On normal startup `init_db()` adds nullable metadata columns, fills missing codes
with `legacy-place:<id>` / `legacy-path:<id>`, creates unique code indexes and the
revision ledger. It preserves numeric IDs, coordinates, paths, users and history.
The migration is repeatable. Back up the database before changing its schema.

```powershell
venv/Scripts/python.exe -m scripts.seed_ucc_floor1
venv/Scripts/python.exe -m scripts.run_campus --port 8001
```

Inspect existing processes/ports before running the server. An already-running
server retains its loaded Python/API contract until its normal restart. The
frontend continues to support it. The seed targets `uninav-campus.db`, preserves
other scoped floors, and refuses an unrelated unscoped sample campus.

`data/datasets/ucc-first-floor.json` contains exactly the original 19 places and
16 bidirectional paths from `scripts.ucc_floor1_data` at `3809907`, with the C2
elevation and persistent `ucc:floor1:pNN` / `ucc:floor1:eNN` codes. These stored
codes are identities, not an instruction to regenerate numbers on reordering.
The controlled seed adopts legacy records only when coordinates, floor,
effective elevation and path attributes match. It preserves their row IDs and
history. It does not delete obsolete or omitted records.

## Import another confirmed dataset

Use the admin endpoint `POST /campus/datasets/import` or the explicit-file CLI:

```powershell
venv/Scripts/python.exe -m scripts.import_campus_dataset confirmed-floor.json --database uninav-campus.db
```

The JSON schema is `schemas/datasets.py`. A payload declares `scope`, `revision`,
`source`, `places` and `paths`. Every place requires code, legacy alias, plan
coordinates, explicit elevation and its source. Paths refer to endpoint codes;
an endpoint may already belong to another scope. Such a connection never updates
the foreign place. Unknown endpoints, duplicate codes, name conflicts, occupied
path pairs or attempts to modify foreign records reject the entire import.

Imports run inside a savepoint and the caller commits only after full success.
No record is deleted. Existing records are updated only within the named scope.
The revision ledger stores `(scope, revision)`, canonical payload SHA-256, source
and application time. Repeating an identical revision is a no-op when its records
still match. Reusing its name with another payload, missing records or manual
drift fails; create a reviewed new revision for intentional changes. Replaying an
older revision cannot silently roll back changed records. Ordinal revision names
are not interpreted as sortable version numbers.

API and generic CLI imports do not adopt legacy aliases. Only the dedicated
first-floor seed enables that narrowly checked transition. Administrative CRUD
can still change a scoped record; a subsequent same-revision import reports that
drift instead of overwriting it silently.

## Verification

`data/datasets/ucc-second-floor.json` prepares the first three source destinations
on floor 2: mixed reality, molecular biology and the medical research centre.
It adds 45 records (including hidden waypoints and three structural references)
and 43 bidirectional paths in `ucc:floor2-connection`. Combined with the base,
the prepared dataset has 64 places and 59 paths. Original IDs and all 16 base
connections remain unchanged. Two collinear links add the east-stair junction
to the existing north corridor while retaining its legacy direct edge.

The model source is the committed C13 `a2dbda0`; elevations follow its 3.5 / 6.44 m
model frame, with flattened A/B half-levels and derived physical identities.
Door D14 enters mixed reality, D15 molecular biology and D13 medical research.
The source's staff-room label is across glass from D13 and is not assigned to it.
The only mapped vertical connection is the measured east stair. Avoiding stairs
therefore returns no route to these destinations; no elevator/ramp is invented.

The file is prepared for controlled import and is not automatically seeded by
`scripts.run_campus`. Neither development database has received it. The real
service still has its older loaded contract. Importing new places behind that
service would mix API/data revisions and invalidate the frontend binding.
Use an isolated database for rehearsal; activate only with the compatible API
and frontend model/data manifest. Preparation is not a completed public rollout.

Source door facts, geometry and browser evidence live in the frontend's
`docs/blocks/floor2-door-accesses.json`, `floor2-route-review.md` and
`docs/verification/h2-floor2-candidate/`. The new API tests check both algorithms,
round trips, explicit heights/IDs/doors, repeated import, base-record preservation,
stairs exclusion and atomic rejection without the required first-floor endpoints.

API tests cover legacy migration twice with retained history, controlled adoption,
outer rollback, atomic import failure, foreign scope/path conflicts, omitted-record
preservation, revision drift and repeated display labels across synthetic floors.
Both algorithms, reverse routes, stairs avoidance, comparison and multi-stop use
explicit heights. The four real destinations and their returns also verify IDs,
connection codes and 3.5 m C2 waypoints. Synthetic upper-floor examples exist only
in temporary tests, never in either development database.

The reviewed C13 cuts and C5 exterior remain unchanged. Temporary-API browser
journeys already pass through the C13 east stair at model elevations 3.5 / 6.44 m.
Physical level changes elsewhere still require matching geometry and waypoints.

## Prepared first-floor stair classification

`data/datasets/ucc-first-floor-stairs.json` is a separate prepared revision of
`ucc:floor1`. It updates only kinds for e08, e09 and e10 to `stairs`. These whole
connections contain confirmed steps. It creates no records and changes no IDs,
endpoints, positions, elevations or weights. It works with either 19/16 or 64/59
data and retains the other scope. It is not automatically seeded or imported.

The source is Claude's first-floor level review, including `b9648f5`: three
numbered hall treads lie between four risers, about 0.158 m each, dropping from
N 0.00 to -0.63. The B laboratory approach climbs nine steps to N +1.19. The
south-east polygon is a roof; no step-free ramp to that laboratory is confirmed.
Stair avoidance now rejects the three affected destinations from Hall Acceso in
both directions, while ICETEX and travel within the upper hall area remain open.

This classification protects filtering. Its connection distances include clear
approaches and must not be interpreted as measured stair-flight lengths. C13
still flattens these areas. Physical splitting, affected level assignments and
clearance/support rehearsals await the separate model candidate requested in
`UniNav-Frontend/docs/blocks/first-floor-level-review.json`. Those proposed points
are explicitly approximate and the handoff file is not an importable dataset.

Do not import this revision into the live development DB yet. The current 8001
process exposes the earlier contract; a future release must also advance the
full baseline seed to a new reviewed revision carrying these classifications.
Replaying the old baseline after applying this revision deliberately reports
drift instead of silently restoring corridor types. Tests cover this behavior.

`tests.serve_campus --dataset ...` can be repeated to rehearse the upper dataset
and stair revision in order. Its `--snapshot-json` mode produces actual API
serialization without opening a port. Both modes use only their new temporary
database. Frontend profiles preserve the old base/upper bindings and add reviewed
stair-classified bindings; the legacy API UI separately rejects the same audited
crossings when Avoid stairs is selected.

## Prepared C15 physical hall and Block A levels

`ucc-first-floor-c15.json` and `ucc-second-floor-c15.json` are complete scoped
revisions of `ucc:floor1` and `ucc:floor2-connection`. Apply both within one
outer transaction after the canonical first-floor baseline. They prepare
68 places / 63 bidirectional connections and preserve the existing 64 place IDs
and 59 connection IDs when upgrading the older two-floor data.

The original e09 connection is retargeted from the new hall-after node to the
elevator hall. Four new stair connections replace its direct crossing, preserving
the e09 ID without a remaining bypass. The before-node keeps its ID and moves to
the documented point (28,47.6). The three tread centres and after-point follow
C15's four 0.1575 m risers. A's walking levels are world 2.87 / 6.18 m; the east
stair keeps its measured plan layout with its corrected 3.31 m rise. Structural
reference heights remain at the B datum and do not become walking surfaces.

Sources are the committed C15 exports and `level-zones.json` at frontend
`3177ca7`, including the corrected y=49.23 boundary. The B laboratory/Lockers
zone remains physically pending at the candidate's flat world 3.5 m; it is not
raised to +1.19 by inference. Its known stair crossing remains classified.
The outdoor courtyard node uses model-only world 3.35 m to match the `Site`
mesh top, 0.15 m below the B slab; this is not a surveyed physical level.

These revisions require the separate frontend `ucc-two-floors-c15` model/data
profile. They are not imported by the normal launcher, and neither live database
has received them. Repeating the imports is idempotent; the old baseline then
reports drift instead of restoring old endpoints and heights. API tests rehearse
upgrading both scopes, identity preservation, bypass removal, rollback, both
algorithms, seven round-trip destinations and stair exclusion. Browser and
geometry evidence is in frontend `docs/verification/c15/`.

The versioned launcher offers the historical reviewed combinations, including C15
through an explicit `--profile ucc-two-floors-c15`. The default stays at the old
baseline, and the existing 8001 database/service remains unchanged. Profile
restarts compose patches before import and apply both C15 scopes atomically;
they do not replay the superseded flat seed. See [startup profiles](CAMPUS_STARTUP.md)
for isolated commands, revision hashes, port reservation and downgrade behavior.

## Prepared C16 third-floor scope

`ucc-third-floor.json` adds 42 places and 39 bidirectional connections under
`ucc:floor3-connection` / `c16-third-floor-v1`. The versioned
`ucc-three-floors-c16` startup profile composes the two unchanged C15 scopes and
this addition: 110 places / 102 connections. It preserves their IDs, paths and
history, supports repeated startup, rolls back the complete upgrade on failure,
and rejects later profiles omitting the installed third-floor scope.

Only Informática 1 / 308 A, Informática 2 / 309 A, and Informática 3 / 310 A
are destinations. Doorway D15, D14 and D13 centres and inside/outside stands come
from frontend `model/tools/data/floor3/doorways.json @389cfd9`; the paired literal
laboratory/classroom labels come from `wing.json` at the same revision. Their
drawn partitions and approaches are checked against committed C16 `002aaec`.
Targets lie inside the doors, not at the label centroids. Faculty is unknown.

The existing floor-2 north corridor connects to the next east stair through
(36.35,54.7), then (36.35,55.9). C16's documented 21-riser layout rises from
world 6.18 to 9.87. Stair waypoints keep floor 2 through the high landing and
change to floor 3 at the final upper endpoint. Three isolated structural anchors
remain at B datum 9.38. Avoiding stairs rejects inter-floor travel while allowing
travel between these same-floor entrances.

The matching frontend profile has its own third-floor API reference and data
fingerprints; old profiles remain available. No live import or service restart
is part of this prepared delivery. Floors 0/4/5, other rooms and unresolved level
zones remain pending. This data now binds to the C16 set with the reviewed C17
floor-2 ramp; coordinates, IDs, graph topology and dataset payloads are unchanged.
No public ramp connection is added. The read-only catalogue records the user's
Block A/B identity confirmation from frontend `level-zones.md @b36d328`, retaining
all existing floor datums and derived/provisional level evidence. See frontend `docs/blocks/floor3-navigation.md`
and `docs/verification/floor3/` for the source and rehearsal evidence.

## Prepared C18 piso cero scope

`ucc-floor-zero.json` adds 40 places and 37 bidirectional connections under
`ucc:floor0-connection` / `c18-floor-zero-v1`. The `ucc-four-floors-c18` startup
profile composes the two C15 scopes, the C16 third-floor scope and this addition:
150 places / 139 connections. IDs, paths and history are preserved, a repeated
startup creates nothing, a failure rolls back the whole upgrade, and later
profiles omitting the installed scope are rejected.

- **Levels:** Block A and the east clinic are at N -4.13, world -0.63. They come
  from the frontend piso cero sources (`docs/blocks/level-zones.md @de3815e /
  e3c18dc`) and candidate `model/candidates/c18/` @711fb9d. The C18 floor-1
  companion opens the ground slab under the stair well; all its other meshes are
  identical to C16.
- **East tower:** it reuses the reviewed floor 1-2 east stair plan points
  (21 risers) with heights rescaled to the 3.50 m rise. It joins the existing
  floor-1 north junction at world 2.87.
- **Destinations:**
  - Clinical Simulation Laboratory, inside stand of doorway D32 (1.57 m, clear),
    with the literal label `LABORATORIO DE SIMULACIÓN CLÍNICA`.
  - Waiting room, labelled `SALA DE ESPERA`, reached through the drawn facade
    sliding door.
  - A floor-0 elevator lobby waypoint is reachable but is not a destination.
- **Reference anchors:** three isolated structural anchors stay at the B datum,
  world 0.56.
- **Not modelled:** the B stair flights, the west stair, the south-west ramp,
  the east-yard steps, the southern rooms and the elevators as operating stops.
  None of them has a connection.

The geometry audit (`tools/prepare-floor0.ts` in the frontend) walks all 139
connections in both directions. It uses the runtime support and collision
functions against floors 0–5. As a negative control, the flat C14 preview rejects
all 35 floor-0 connections. See frontend `docs/verification/floor0/`.
