from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[2]


def cli(module:str,*args:str)->subprocess.CompletedProcess:
    return subprocess.run([sys.executable,"-m",module,*args],cwd=ROOT,env={**os.environ,"PYTHONIOENCODING":"utf-8"},capture_output=True,text=True,encoding="utf-8",timeout=30)


@pytest.mark.parametrize("profile,counts",[("base",(19,16)),("ucc-two-floors",(64,59)),("ucc-first-floor-stair-review",(19,16)),("ucc-two-floors-stair-review",(64,59)),("ucc-two-floors-c15",(68,63))])
def test_seed_command_repeats_against_an_explicit_database(tmp_path:Path,profile:str,counts:tuple[int,int])->None:
    path=tmp_path/"review.db"
    first=cli("scripts.seed_campus","--database",str(path),"--profile",profile)
    assert first.returncode==0,first.stderr
    report=json.loads(first.stdout.split("UNINAV_CAMPUS_SEEDED=",1)[1])
    assert (report["places"],report["paths"])==counts
    with sqlite3.connect(path) as db:
        before=db.execute("select id,code,x,y,elevation_m from buildings order by id").fetchall()
        db.execute("update users set password_hash='existing credential preserved' where username='student'");db.commit()
    repeated=cli("scripts.seed_campus","--database",str(path),"--profile",profile)
    assert repeated.returncode==0,repeated.stderr
    report=json.loads(repeated.stdout.split("UNINAV_CAMPUS_SEEDED=",1)[1]);assert report["created_places"]==report["created_paths"]==0
    with sqlite3.connect(path) as db:
        assert db.execute("select id,code,x,y,elevation_m from buildings order by id").fetchall()==before
        assert db.execute("select password_hash from users where username='student'").fetchone()[0]=='existing credential preserved'


def test_occupied_port_is_rejected_before_an_existing_db_is_changed(tmp_path:Path)->None:
    path=tmp_path/"baseline.db";seed=cli("scripts.seed_campus","--database",str(path));assert seed.returncode==0,seed.stderr
    before=path.read_bytes()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1",0));listener.listen()
        result=cli("scripts.run_campus","--database",str(path),"--profile","ucc-two-floors-c15","--port",str(listener.getsockname()[1]))
        assert result.returncode==2 and "Cannot reserve port" in result.stderr
        assert path.read_bytes()==before


def test_invalid_profile_never_creates_a_database(tmp_path:Path)->None:
    path=tmp_path/"not-created.db"
    result=cli("scripts.run_campus","--database",str(path),"--profile","unreviewed","--port","0")
    assert result.returncode==2 and "invalid choice" in result.stderr and not path.exists()
