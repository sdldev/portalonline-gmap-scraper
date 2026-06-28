#!/usr/bin/env python3
"""CLI user management for PortalOnline GMap Scraper API."""

import asyncio
import importlib.util
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

async def _get_store():
    spec = importlib.util.spec_from_file_location(
        "store", os.path.join(PROJECT_ROOT, "portalonline_gmap_scraper/api/store.py")
    )
    store = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(store)
    return store

async def cmd_list():
    store = await _get_store()
    db = await store.init_db()
    users = await store.list_users(db)
    if not users:
        print("No users found.")
    else:
        print(f"{'USERNAME':<16} {'ROLE':<8} {'ACTIVE':<8} {'API KEY'}")
        print("-" * 70)
        for u in users:
            print(f"{u['username']:<16} {u['role']:<8} {str(u['active']):<8} {u['api_key']}")
    await db.close()

async def cmd_create(username, role="user", api_key=None):
    store = await _get_store()
    db = await store.init_db()
    user = await store.create_user(db, username, role=role, api_key=api_key)
    print(f"Created: {user['username']} (role={user['role']})")
    print(f"API Key : {user['api_key']}")
    await db.close()

async def cmd_delete(username):
    store = await _get_store()
    db = await store.init_db()
    users = await store.list_users(db)
    target = next((u for u in users if u["username"] == username), None)
    if target is None:
        print(f"User '{username}' not found.")
        await db.close()
        return
    await store.delete_user(db, target["user_id"])
    print(f"Deleted: {username}")
    await db.close()

async def cmd_seed():
    store = await _get_store()
    db = await store.init_db()
    users = await store.list_users(db)
    created = []
    if not any(u["username"] == "admin" for u in users):
        a = await store.create_user(db, "admin", role="admin")
        created.append(("admin", a["api_key"]))
    if not any(u["username"] == "user" for u in users):
        u = await store.create_user(db, "user", role="user")
        created.append(("user", u["api_key"]))
    if created:
        print("Created users:")
        for name, key in created:
            print(f"  {name}: {key}")
    else:
        print("All seed users already exist.")
    await db.close()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python manage.py <cmd> [args]")
        print("  list              List all users")
        print("  seed              Create default admin + user")
        print("  create <name> <role>   Create user (role: admin|user)")
        print("  delete <name>     Delete user")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        await cmd_list()
    elif cmd == "seed":
        await cmd_seed()
    elif cmd == "create" and len(sys.argv) >= 4:
        await cmd_create(sys.argv[2], sys.argv[3])
    elif cmd == "delete" and len(sys.argv) >= 3:
        await cmd_delete(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
