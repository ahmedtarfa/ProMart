from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from inventory_loader import refresh_inventory_data
import glob
import os
import shutil
import stat
import time
import asyncio

app = FastAPI()

# === Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Deletion Utilities ===
def force_remove_readonly(func, path, _):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        print(f"[FORCE DELETE FAIL] {path}: {e}")

def safe_rmtree(path, retries=3, delay=1):
    for i in range(retries):
        try:
            shutil.rmtree(path, onerror=force_remove_readonly)
            print(f"[SAFE DELETE] Deleted {path}")
            return
        except Exception as e:
            print(f"[RETRY {i+1}] Failed to delete {path}: {e}")
            time.sleep(delay)
    print(f"[FAILED DELETE] Could not delete {path} after {retries} retries.")

def delete_old_chroma_dirs(keep_latest=1):
    all_chroma_dirs = glob.glob("./chroma_store_*")
    if len(all_chroma_dirs) <= keep_latest:
        return

    sorted_dirs = sorted(all_chroma_dirs, key=os.path.getmtime)
    dirs_to_delete = sorted_dirs[:-keep_latest]

    for path in dirs_to_delete:
        print(f"[CHROMA CLEANUP] Deleting {path}")
        safe_rmtree(path)

# === Background Loop ===
@app.on_event("startup")
async def start_background_tasks():
    async def auto_refresh():
        while True:
            try:
                print("[TASK] Refreshing inventory...")
                refresh_inventory_data()
                print("[TASK] Refresh done.")
            except Exception as e:
                print(f"[ERROR] Refresh failed: {e}")
            await asyncio.sleep(10)

    async def auto_cleanup():
        while True:
            try:
                print("[TASK] Deleting old Chroma directories...")
                delete_old_chroma_dirs()
                print("[TASK] Cleanup done.")
            except Exception as e:
                print(f"[ERROR] Cleanup failed: {e}")
            await asyncio.sleep(30)

    asyncio.create_task(auto_refresh())
    asyncio.create_task(auto_cleanup())

# === Optional Test Endpoint ===
@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Inventory service running with auto tasks."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=2010)
