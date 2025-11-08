#!/usr/bin/env python3
"""
Convert a 64x48 monochrome image into an SSD1306-compatible bitmap header.

The script accepts PNG as requested but also works well with Portable Bitmap
(PBM/XBM) files, which are often easier to edit for true 1-bit artwork.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - depends on host environment
    raise SystemExit(
        "Pillow is required (pip install pillow) to load images."
    ) from exc

OLED_WIDTH = 64
OLED_HEIGHT = 48
ASCII_ON = "█"
ASCII_OFF = " "


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a 64x48 monochrome image into a row-major 1bpp bitmap "
            "and emit a C++ PROGMEM array for SSD1306 displays."
        )
    )
    parser.add_argument(
        "image",
        type=Path,
        help="Path to the source image (PNG, PBM, BMP, etc.).",
    )
    parser.add_argument(
        "-n",
        "--name",
        default="gImage64x48",
        help="Base name for the generated C++ array (default: %(default)s).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=128,
        help="Grayscale threshold (0-255) for deciding which pixels are ON.",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert the bitmap so light pixels become ON instead of dark.",
    )
    parser.add_argument(
        "--lsb-first",
        action="store_true",
        help="Pack bits with the least-significant bit representing the leftmost pixel.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Destination .h file (defaults to <name>.h in the current directory).",
    )
    return parser.parse_args()


def load_image(image_path: Path) -> Image.Image:
    if not image_path.exists():
        raise FileNotFoundError(image_path)

    img = Image.open(image_path).convert("L")

    if img.size != (OLED_WIDTH, OLED_HEIGHT):
        raise ValueError(
            f"Image must be {OLED_WIDTH}x{OLED_HEIGHT} pixels, "
            f"but is {img.size[0]}x{img.size[1]}."
        )
    return img


def image_to_bitmap(
    img: Image.Image, threshold: int, invert: bool, lsb_first: bool
) -> tuple[list[int], list[str]]:
    row_bytes = OLED_WIDTH // 8
    buffer: list[int] = []
    ascii_rows: list[str] = []

    for y in range(OLED_HEIGHT):
        ascii_line_chars: list[str] = []
        for byte_index in range(row_bytes):
            current_byte = 0
            for bit in range(8):
                x = byte_index * 8 + bit
                pixel_value = img.getpixel((x, y))
                is_on = pixel_value < threshold
                if invert:
                    is_on = not is_on
                ascii_line_chars.append(ASCII_ON if is_on else ASCII_OFF)
                if is_on:
                    bit_index = bit if lsb_first else 7 - bit
                    current_byte |= 1 << bit_index
            buffer.append(current_byte)
        ascii_rows.append("".join(ascii_line_chars))

    return buffer, ascii_rows


def format_header(name: str, bitmap: list[int], source: Path) -> str:
    bytes_per_row = OLED_WIDTH // 8
    cpp_lines = [
        "#pragma once",
        "",
        "#include <Arduino.h>",
        "",
        f"// Generated from '{source.name}' via tools/image_to_ssd1306.py",
        f"// 1bpp bitmap, row-major, {OLED_WIDTH}x{OLED_HEIGHT} pixels",
        f"const uint8_t {name}[{len(bitmap)}] PROGMEM = {{",
    ]
    for row in range(OLED_HEIGHT):
        start = row * bytes_per_row
        row_bytes = bitmap[start : start + bytes_per_row]
        cpp_lines.append("    " + ", ".join(f"0x{value:02X}" for value in row_bytes) + ",")

    cpp_lines.append("};")
    cpp_lines.append("")
    return "\n".join(cpp_lines)


def main() -> int:
    args = parse_args()
    try:
        img = load_image(args.image)
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    bitmap, ascii_rows = image_to_bitmap(
        img,
        args.threshold,
        args.invert,
        args.lsb_first,
    )

    print("ASCII preview:")
    for line in ascii_rows:
        print(line)

    header_text = format_header(args.name, bitmap, args.image)
    output_path = args.output or Path(f"{args.name}.h")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(header_text, encoding="utf-8")
    print(f"\nHeader written to: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
