"""Start Dezafira server as a detached process for testing."""
import os, sys, time, subprocess, signal

# Path to the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

# Kill any existing Python processes on port 8000
try:
    subprocess.run(
        ["taskkill", "/F", "/IM", "python.exe"],
        capture_output=True, timeout=5
    )
except:
    pass
time.sleep(2)

# Start the server
log_file = open(os.path.join(BASE_DIR, "server_test.log"), "w")
proc = subprocess.Popen(
    [sys.executable, "-c", """
import uvicorn
import os
os.chdir(r'""" + BASE_DIR + """')
uvicorn.run('server:app', host='0.0.0.0', port=8000, reload=False, log_level='info')
"""],
    stdout=log_file,
    stderr=subprocess.STDOUT,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0,
)

print(f"Server PID: {proc.pid}")
time.sleep(5)

# Test health
import urllib.request
try:
    resp = urllib.request.urlopen("http://localhost:8000/health", timeout=5)
    print(f"Health: {resp.read().decode()}")
except Exception as e:
    print(f"Health error: {e}")
    # Show log tail
    log_file.close()
    with open(os.path.join(BASE_DIR, "server_test.log")) as f:
        lines = f.readlines()
        print("Last 10 log lines:")
        for line in lines[-10:]:
            print(f"  {line.rstrip()}")

# Save PID for later reference
with open(os.path.join(BASE_DIR, "server_pid.txt"), "w") as f:
    f.write(str(proc.pid))
print(f"PID saved to server_pid.txt: {proc.pid}")
print("Done!")
