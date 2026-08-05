"""Build helper: convert the TAOS logo PNG to a multi-size .ico for the exe."""
from PIL import Image

SRC = "icons/taos_launcher_logo.png"
DST = "icons/taos.ico"

img = Image.open(SRC).convert("RGBA")
img.save(DST, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("wrote %s" % DST)
