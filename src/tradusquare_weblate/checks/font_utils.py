# Copyright © Michal Čihař <michal@weblate.org>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Font handling wrapper."""

from __future__ import annotations

import os
from functools import cache, lru_cache
from io import BytesIO
from math import ceil
from typing import TYPE_CHECKING, NamedTuple

import cairo
import gi
from django.core.cache import cache as django_cache
from PIL import ImageFont, Image

from weblate.screenshots.fields import ScreenshotField
from weblate.utils.data import data_path
from weblate.utils.hash import calculate_hash
from weblate.utils.icons import find_static_file
from weblate.fonts.utils import configure_fontconfig

gi.require_version("PangoCairo", "1.0")
gi.require_version("Pango", "1.0")

# pylint: disable-next=wrong-import-position,wrong-import-order
from gi.repository import Pango, PangoCairo  # noqa: E402

if TYPE_CHECKING:
    from django.core.files.base import File
    from django.db.models.fields.files import FieldFile


class Dimensions(NamedTuple):
    width: int
    height: int

class RenderingTextbox(NamedTuple):
    wrap_mode: str
    x: int
    y: int

FONT_WEIGHTS = {
    "normal": Pango.Weight.NORMAL,
    "light": Pango.Weight.LIGHT,
    "bold": Pango.Weight.BOLD,
    "": None,
}

WRAP_MODES = {
    "none": Pango.WrapMode.NONE,
    "word": Pango.WrapMode.WORD,
    "char": Pango.WrapMode.CHAR,
    "": Pango.WrapMode.WORD,
}

def get_font_weight(weight: str) -> Pango.Weight | None:
    return FONT_WEIGHTS[weight]

def get_textbox_wrap_mode(wrap_mode: str) -> Pango.WrapMode:
    return WRAP_MODES[wrap_mode]

@lru_cache(maxsize=32)
def _render_size(
    text: str,
    *,
    font: str = "Kurinto Sans",
    weight: int | Pango.Weight | None = Pango.Weight.NORMAL,
    size: int = 11,
    spacing: int = 0,
    width: int = 1000,
    lines: int = 1,
    needs_output: bool = False,
    surface_height: int | None = None,
    surface_width: int | None = None,
    background: ScreenshotField | None = None,
    wrap_mode: str = 'word',
    textbox_x: int = 0,
    textbox_y: int = 0
) -> tuple[Dimensions, int, bytes]:
    """Check whether rendered text fits."""
    configure_fontconfig()
    normalized_weight = None if weight is None else Pango.Weight(weight)

    if surface_height is None:
        surface_height = int(lines * size * 1.5)
    if surface_width is None:
        surface_width = width

    fontdesc = Pango.FontDescription.from_string(font)
    fontdesc.set_absolute_size(size * Pango.SCALE)
    if normalized_weight:
        fontdesc.set_weight(normalized_weight)

    attr_list = None
    if spacing:
        letter_spacing_attr = Pango.attr_letter_spacing_new(Pango.SCALE * spacing)
        attr_list = Pango.AttrList()
        attr_list.insert(letter_spacing_attr)

    buffer = b""

    while True:
        # Setup Pango/Cairo
        if background is not None:
            background.open(mode='rb')
            surface = cairo.ImageSurface.create_from_png(background)
        else:
            textbox_x = 0
            textbox_y = 0
            surface = cairo.ImageSurface(cairo.FORMAT_RGB24, surface_width, surface_height)
        context = cairo.Context(surface)

        layout = PangoCairo.create_layout(context)

        layout.set_font_description(fontdesc)

        # Reapply attributes to each layout bound to the current context.
        if attr_list is not None:
            layout.set_attributes(attr_list)

        # Set the actual text
        layout.set_text(text)

        # Set width and line wrapping
        layout.set_width(width * Pango.SCALE)
        layout.set_wrap(get_textbox_wrap_mode(wrap_mode))

        # Calculate dimensions
        line_count = layout.get_line_count()
        pixel_size = Dimensions(*layout.get_pixel_size())

        if not needs_output:
            break

        required_height = max(surface_height, pixel_size.height)
        required_width = max(width, surface_width, pixel_size.width)
        if required_height == surface_height and required_width == surface_width:
            break

        surface_height = required_height
        surface_width = required_width

    if needs_output:
        if background is None:
            # Render gray background
            # This matches .img-check CSS style
            context.save()
            context.set_source_rgb(0.8, 0.8, 0.8)
            context.paint()
            context.restore()

        expected_height = ceil(lines * pixel_size.height / line_count)

        # Render the text clipped to the allowed area.
        context.save()
        context.rectangle(textbox_x, textbox_y, width, expected_height)
        context.clip()
        context.set_source_rgb(0, 0, 0)
        context.move_to(textbox_x, textbox_y)
        PangoCairo.show_layout(context, layout)
        context.restore()

        # Highlight overflowing parts in red instead of hiding them.
        if pixel_size.width > width or line_count > lines:
            context.save()
            context.rectangle(textbox_x, textbox_y, surface_width, surface_height)
            context.rectangle(textbox_x, textbox_y, width, expected_height)
            context.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            context.clip()
            context.set_source_rgb(246 / 255, 102 / 255, 76 / 255)
            context.move_to(textbox_x, textbox_y)
            PangoCairo.update_layout(context, layout)
            PangoCairo.show_layout(context, layout)
            context.restore()

        # Render box around desired size
        context.new_path()
        context.set_source_rgb(0.1, 0.1, 0.1)
        context.set_line_width(1)
        context.move_to(textbox_x + 1, textbox_y + 1)
        context.line_to(textbox_x + width - 1, textbox_y + 1)
        context.line_to(textbox_x + width - 1, textbox_y + expected_height - 1)
        context.line_to(textbox_x + 1, textbox_y + expected_height - 1)
        context.line_to(textbox_x + 1, textbox_y + 1)
        context.stroke()

        # Render box about actual size if it does not fit
        if pixel_size.width > width or line_count > lines:
            context.new_path()
            context.set_source_rgb(246 / 255, 102 / 255, 76 / 255)
            context.set_line_width(1)
            context.move_to(textbox_x + 1, textbox_y + 1)
            context.line_to(textbox_x + pixel_size.width - 1, textbox_y +  1)
            context.line_to(textbox_x + pixel_size.width - 1, textbox_y + pixel_size.height - 1)
            context.line_to(textbox_x + 1, textbox_y + pixel_size.height - 1)
            context.line_to(textbox_x + 1, textbox_y + 1)
            context.stroke()

        with BytesIO() as buff:
            surface.write_to_png(buff)
            buffer = buff.getvalue()

    return pixel_size, line_count, buffer


def render_size(
    text: str,
    *,
    font: str = "Kurinto Sans",
    weight: int | Pango.Weight | None = Pango.Weight.NORMAL,
    size: int = 11,
    spacing: int = 0,
    width: int = 1000,
    lines: int = 1,
    cache_key: str | None = None,
    surface_height: int | None = None,
    surface_width: int | None = None,
    use_cache: bool = True,
    background: ScreenshotField | None = None,
    textbox: RenderingTextbox = RenderingTextbox('', 0, 0)
) -> tuple[Dimensions, int]:
    render_cache_key = f"render:{calculate_hash(text)}:{calculate_hash(font)}:{int(weight) if weight is not None else ''}:{size}:{spacing}:{width}:{lines}:{cache_key}:{surface_height}:{surface_width}"
    if use_cache:
        cached: tuple[Dimensions, int] | None = django_cache.get(render_cache_key)
        if cached and (cache_key is None or django_cache.get(cache_key)):
            return cached
    pixel_size, line_count, buffer = _render_size(
        text,
        font=font,
        weight=weight,
        size=size,
        spacing=spacing,
        width=width,
        lines=lines,
        needs_output=cache_key is not None,
        surface_height=surface_height,
        surface_width=surface_width,
        background=background,
        wrap_mode=textbox.wrap_mode,
        textbox_x=textbox.x,
        textbox_y=textbox.y
    )
    if cache_key:
        # Longer expiry for rendered results so that it can be recalculated
        django_cache.set(cache_key, buffer, timeout=4200)
    result = pixel_size, line_count
    django_cache.set(render_cache_key, result, timeout=3600)
    return result


def check_render_size(
    *,
    font: str,
    weight: int | Pango.Weight | None,
    size: int,
    spacing: int,
    text: str,
    width: int,
    lines: int,
    cache_key: str | None = None,
    background: ScreenshotField | None = None,
    textbox: RenderingTextbox
) -> bool:
    """Check whether rendered text fits."""
    rendered_size, actual_lines = render_size(
        font=font,
        weight=weight,
        size=size,
        spacing=spacing,
        text=text,
        width=width,
        lines=lines,
        cache_key=cache_key,
        background=background,
        textbox=textbox
    )
    return rendered_size.width <= width and actual_lines <= lines
