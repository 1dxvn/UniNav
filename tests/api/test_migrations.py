from sqlalchemy import create_engine

import database


def test_additive_migration_keeps_legacy_ids_and_history(tmp_path, monkeypatch):
    legacy = create_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}")
    try:
        with legacy.begin() as connection:
            for sql in (
                "CREATE TABLE buildings (id INTEGER PRIMARY KEY, name VARCHAR(100) UNIQUE NOT NULL, x FLOAT NOT NULL, y FLOAT NOT NULL, faculty VARCHAR(100), building_type VARCHAR(50))",
                "CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(50) UNIQUE, password_hash VARCHAR(255), created_at DATETIME)",
                "CREATE TABLE paths (id INTEGER PRIMARY KEY, source_id INTEGER REFERENCES buildings(id), target_id INTEGER REFERENCES buildings(id), weight FLOAT, bidirectional BOOLEAN)",
                "CREATE TABLE route_visits (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), origin_id INTEGER REFERENCES buildings(id), destination_id INTEGER REFERENCES buildings(id), distance FLOAT, visited_at DATETIME)",
                "INSERT INTO buildings (id,name,x,y) VALUES (11,'Legacy Hall',1,2),(27,'Legacy Lab',4,6)",
                "INSERT INTO paths VALUES (31,11,27,NULL,1)",
                "INSERT INTO users VALUES (5,'legacy_user','hash','2026-01-01')",
                "INSERT INTO route_visits VALUES (99,5,11,27,5,'2026-01-01')",
            ):
                connection.exec_driver_sql(sql)
        monkeypatch.setattr(database, "engine", legacy)
        database.init_db()
        database.init_db()
        with legacy.connect() as connection:
            assert connection.exec_driver_sql("SELECT id,name,x,y,floor,code,elevation_m FROM buildings ORDER BY id").all() == [
                (11,"Legacy Hall",1,2,0,"legacy-place:11",None), (27,"Legacy Lab",4,6,0,"legacy-place:27",None)]
            assert connection.exec_driver_sql("SELECT id,source_id,target_id,weight,bidirectional,code,kind FROM paths").one() == (31,11,27,None,1,"legacy-path:31","corridor")
            assert connection.exec_driver_sql("SELECT id,user_id,origin_id,destination_id,distance FROM route_visits").one() == (99,5,11,27,5)
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
    finally:
        legacy.dispose()
