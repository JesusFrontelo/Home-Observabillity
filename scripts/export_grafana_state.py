#!/usr/bin/env python3
"""Export Grafana state from grafana.db into versionable files.

Exports:
- dashboards to grafana/dashboards
- datasources provisioning to grafana/provisioning/datasources/datasources.yml
- library elements to grafana/library-elements
- playlists to grafana/playlists
- alert configuration to grafana/alerting
"""

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_CANDIDATES = [
    ROOT / "grafana" / "data" / "grafana.db",
    ROOT / "grafana.db",
]


def find_db() -> Path:
    for candidate in DB_CANDIDATES:
        if candidate.exists():
            return candidate
    raise SystemExit("No se encontro grafana.db en grafana/data ni en la raiz del proyecto")


def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "item"


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=True)
        f.write("\n")


def export_dashboards(cur: sqlite3.Cursor) -> int:
    out_dir = ROOT / "grafana" / "dashboards"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = cur.execute(
        "SELECT uid, title, data FROM dashboard WHERE is_folder = 0 ORDER BY title COLLATE NOCASE"
    ).fetchall()

    for uid, title, data in rows:
        doc = json.loads(data)
        filename = f"{uid or 'no-uid'}-{slugify(title or 'dashboard')}.json"
        write_json(out_dir / filename, doc)

    return len(rows)


def export_datasources(cur: sqlite3.Cursor) -> int:
    out_file = ROOT / "grafana" / "provisioning" / "datasources" / "datasources.yml"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    cols = [r[1] for r in cur.execute("PRAGMA table_info(data_source)").fetchall()]
    select_cols = [
        c
        for c in [
            "uid",
            "name",
            "type",
            "access",
            "url",
            "user",
            "database",
            "basic_auth",
            "basic_auth_user",
            "with_credentials",
            "is_default",
            "json_data",
        ]
        if c in cols
    ]
    rows = cur.execute("SELECT " + ", ".join(select_cols) + " FROM data_source ORDER BY id").fetchall()

    datasources = []
    for row in rows:
        d = dict(zip(select_cols, row))
        ds = {
            "name": d.get("name"),
            "type": d.get("type"),
            "access": d.get("access") or "proxy",
            "url": d.get("url") or "",
            "isDefault": bool(d.get("is_default")),
            "editable": False,
        }
        if d.get("uid"):
            ds["uid"] = d["uid"]
        if d.get("basic_auth") is not None:
            ds["basicAuth"] = bool(d.get("basic_auth"))
        if d.get("basic_auth_user"):
            ds["basicAuthUser"] = d.get("basic_auth_user")
        if d.get("database"):
            ds["database"] = d.get("database")
        if d.get("user"):
            ds["user"] = d.get("user")
        if d.get("with_credentials") is not None:
            ds["withCredentials"] = bool(d.get("with_credentials"))
        if d.get("json_data"):
            try:
                ds["jsonData"] = json.loads(d["json_data"])
            except json.JSONDecodeError:
                ds["jsonData"] = {}

        datasources.append(ds)

    with out_file.open("w", encoding="utf-8") as f:
        f.write("apiVersion: 1\n")
        f.write("datasources:\n")
        for ds in datasources:
            f.write(f"  - name: {json.dumps(ds['name'])}\n")
            if ds.get("uid"):
                f.write(f"    uid: {json.dumps(ds['uid'])}\n")
            f.write(f"    type: {json.dumps(ds['type'])}\n")
            f.write(f"    access: {json.dumps(ds['access'])}\n")
            f.write(f"    url: {json.dumps(ds['url'])}\n")
            f.write(f"    isDefault: {'true' if ds['isDefault'] else 'false'}\n")
            f.write("    editable: false\n")
            if "basicAuth" in ds:
                f.write(f"    basicAuth: {'true' if ds['basicAuth'] else 'false'}\n")
            if ds.get("basicAuthUser"):
                f.write(f"    basicAuthUser: {json.dumps(ds['basicAuthUser'])}\n")
            if ds.get("database"):
                f.write(f"    database: {json.dumps(ds['database'])}\n")
            if ds.get("user"):
                f.write(f"    user: {json.dumps(ds['user'])}\n")
            if "withCredentials" in ds:
                f.write(
                    f"    withCredentials: {'true' if ds['withCredentials'] else 'false'}\n"
                )
            if ds.get("jsonData"):
                f.write("    jsonData:\n")
                for k, v in ds["jsonData"].items():
                    if isinstance(v, bool):
                        vtxt = "true" if v else "false"
                    elif isinstance(v, (int, float)):
                        vtxt = str(v)
                    else:
                        vtxt = json.dumps(v)
                    f.write(f"      {k}: {vtxt}\n")

    return len(datasources)


def export_library_elements(cur: sqlite3.Cursor) -> int:
    out_dir = ROOT / "grafana" / "library-elements"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = cur.execute(
        "SELECT uid, name, kind, type, description, model, version, folder_uid FROM library_element ORDER BY name"
    ).fetchall()

    for uid, name, kind, typ, desc, model, version, folder_uid in rows:
        write_json(
            out_dir / f"{uid}-{slugify(name)}.json",
            {
                "uid": uid,
                "name": name,
                "kind": kind,
                "type": typ,
                "description": desc,
                "version": version,
                "folderUid": folder_uid,
                "model": json.loads(model) if model else {},
            },
        )

    return len(rows)


def export_playlists(cur: sqlite3.Cursor) -> int:
    out_dir = ROOT / "grafana" / "playlists"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = cur.execute("SELECT id, uid, name, interval, org_id FROM playlist ORDER BY id").fetchall()

    playlist_item_cols = [r[1] for r in cur.execute("PRAGMA table_info(playlist_item)").fetchall()]
    order_col = "order_num" if "order_num" in playlist_item_cols else ("order" if "order" in playlist_item_cols else None)

    select_exprs = ["type", "value"]
    if order_col == "order_num":
        select_exprs.append("order_num AS ord")
    elif order_col == "order":
        select_exprs.append('"order" AS ord')
    if "title" in playlist_item_cols:
        select_exprs.append("title")

    q = f"SELECT {', '.join(select_exprs)} FROM playlist_item WHERE playlist_id = ?"
    if order_col == "order_num":
        q += " ORDER BY order_num"
    elif order_col == "order":
        q += ' ORDER BY "order"'

    for pid, uid, name, interval, org_id in rows:
        items = []
        for row in cur.execute(q, (pid,)).fetchall():
            if "title" in playlist_item_cols:
                t, v, o, title = row if order_col else (row[0], row[1], None, row[2])
            else:
                t, v, o = row if order_col else (row[0], row[1], None)
                title = None
            items.append({"type": t, "value": v, "order": o, "title": title})

        write_json(
            out_dir / f"{uid}-{slugify(name)}.json",
            {
                "id": pid,
                "uid": uid,
                "name": name,
                "interval": interval,
                "orgId": org_id,
                "items": items,
            },
        )

    return len(rows)


def export_alert_config(cur: sqlite3.Cursor) -> int:
    out_dir = ROOT / "grafana" / "alerting"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = cur.execute(
        "SELECT id, org_id, configuration_version, alertmanager_configuration FROM alert_configuration ORDER BY id"
    ).fetchall()

    for rid, org_id, version, cfg in rows:
        write_json(
            out_dir / f"alert_configuration-org{org_id}-id{rid}.json",
            {
                "id": rid,
                "orgId": org_id,
                "configurationVersion": version,
                "alertmanagerConfiguration": json.loads(cfg) if cfg else {},
            },
        )

    return len(rows)


def main() -> None:
    db_path = find_db()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    dashboards = export_dashboards(cur)
    datasources = export_datasources(cur)
    library_elements = export_library_elements(cur)
    playlists = export_playlists(cur)
    alerts = export_alert_config(cur)

    conn.close()

    print(f"db source: {db_path}")
    print(f"dashboards exported: {dashboards}")
    print(f"datasources exported: {datasources}")
    print(f"library elements exported: {library_elements}")
    print(f"playlists exported: {playlists}")
    print(f"alert configurations exported: {alerts}")


if __name__ == "__main__":
    main()
