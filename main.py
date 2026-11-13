import hashlib
import os
import shutil
import struct
import sys


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
output = os.path.join(output_dir, "entry.png")

if not os.path.isfile(source):
    fail(f"source image not found: {source}")

try:
    os.makedirs(output_dir, exist_ok=True)
    shutil.copyfile(source, output)
except OSError as error:
    fail(f"could not copy image to {output}: {error}")

try:
    source_size = os.path.getsize(source)
    output_size = os.path.getsize(output)
    source_hash = sha256_file(source)
    output_hash = sha256_file(output)
except OSError as error:
    fail(f"could not verify image copy: {error}")

if source_size != output_size or source_hash != output_hash:
    fail("copied image does not match source")

if source_size > 1048576:
    fail(f"source image is too large: {source_size} bytes (maximum 1048576)")

try:
    with open(output, "rb") as file:
        header = file.read(24)
except OSError as error:
    fail(f"could not read copied image: {error}")

png_signature = b"\x89PNG\r\n\x1a\n"
if header.startswith(png_signature):
    if len(header) < 24 or header[12:16] != b"IHDR":
        fail("copied PNG has an invalid IHDR chunk")
    width, height = struct.unpack(">II", header[16:24])
    if width > 1024 or height > 1024:
        fail(f"PNG dimensions exceed 1024x1024: {width}x{height}")
elif not header.startswith(b"\xff\xd8\xff"):
    fail("copied image is not a PNG or JPEG")

print(f"Wrote {output} ({output_size} bytes, sha256 {output_hash})")
