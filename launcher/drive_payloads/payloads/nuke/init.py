import os
import nuke

taos_drive = os.getenv("TAOSDRIVE", "")

print("----------------------------------")
print("TAOS Pipeline")
print("TAOSDRIVE:", taos_drive)
print("Nuke environment loaded")
print("----------------------------------")


# Add TAOS plugin directories
nuke.pluginAddPath("./gizmos")
nuke.pluginAddPath("./python")
nuke.pluginAddPath("./icons")