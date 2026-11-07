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

The reviewed C2/C5 models and their sources remain unchanged. Real vertical
navigation still requires Claude's matching slab openings, stairs, landings and
confirmed endpoint coordinates, followed by collision and browser rehearsals.

Claude's updated `docs/blocks/vertical-connections.md` also identifies a physical
first-floor B stair on the laboratory approach: N 0.00 to +1.19 m. C2 represents
this region with a flat slab and the reviewed dataset still has a flat corridor.
Its physical ramp direction is unconfirmed. Preserving C2's verified coordinates
does not certify an accessible real-world route; this discrepancy must be resolved
with matching geometry and revised waypoints before the new stair is integrated.
