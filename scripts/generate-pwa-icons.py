#!/usr/bin/env python3
"""Generate project-owned PWA icons without external image dependencies."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def inside_rotated_ellipse(x: float, y: float, size: int) -> bool:
    center = size / 2
    angle = -0.593411946
    dx, dy = x - center, y - center
    rx = dx * __import__("math").cos(angle) - dy * __import__("math").sin(angle)
    ry = dx * __import__("math").sin(angle) + dy * __import__("math").cos(angle)
    return (rx / (size * 0.246)) ** 2 + (ry / (size * 0.348)) ** 2 <= 1


def render(size: int) -> bytes:
    rows = bytearray()
    radius = size * 0.188
    for y in range(size):
        rows.append(0)
        for x in range(size):
            corner_x = min(x, size - 1 - x)
            corner_y = min(y, size - 1 - y)
            if corner_x < radius and corner_y < radius and (corner_x - radius) ** 2 + (corner_y - radius) ** 2 > radius**2:
                pixel = (0, 0, 0, 0)
            else:
                pixel = (8, 8, 7, 255)
                if inside_rotated_ellipse(x, y, size):
                    pixel = (92, 255, 123, 255)
                # Curved seed division, approximated as a governed graphic
                # primitive rather than copied visual reference material.
                curve_x = size * (0.32 + 0.36 * (y / size) ** 0.72)
                if abs(x - curve_x) < size * 0.027 and size * 0.2 < y < size * 0.8:
                    pixel = (8, 8, 7, 255)
                for marker_x, marker_y in ((0.283, 0.283), (0.717, 0.717)):
                    if (x - size * marker_x) ** 2 + (y - size * marker_y) ** 2 < (size * 0.037) ** 2:
                        pixel = (242, 240, 234, 255)
            rows.extend(pixel)
    signature = b"\x89PNG\r\n\x1a\n"
    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return signature + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b"")


for icon_size in (192, 512):
    (ROOT / "public" / f"icon-{icon_size}.png").write_bytes(render(icon_size))
