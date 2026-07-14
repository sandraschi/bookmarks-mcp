"""Generate a simple 512x512 PNG app icon."""

import struct
import zlib
from pathlib import Path

w, h = 512, 512
rows = []
for y in range(h):
    row = b"\x00" + bytes([30, 80, 200, 180 + (y * 75 // h)]) * w
    rows.append(row)
raw = b"".join(rows)


def chunk(tag: bytes, data: bytes) -> bytes:
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


png = b"".join(
    [
        b"\x89PNG\r\n\x1a\n",
        chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)),
        chunk(b"IDAT", zlib.compress(raw, 9)),
        chunk(b"IEND", b""),
    ]
)

out = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(png)
print(f"Wrote {out} ({len(png)} bytes)")
