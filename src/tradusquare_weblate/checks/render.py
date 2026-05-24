# Copyright © Michal Čihař <michal@weblate.org>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from typing import TYPE_CHECKING

import re

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext, gettext_lazy

from weblate.checks.base import TargetCheckParametrized
from weblate.checks.parser import multi_value_flag
from tradusquare_weblate.checks.font_utils import check_render_size, RenderingTextbox

if TYPE_CHECKING:
    from weblate.auth.models import AuthenticatedHttpRequest
    from weblate.trans.models import Unit

IMAGE = (
    '<a href="{0}" class="thumbnail img-check"><img class="img-fluid" src="{0}" /></a>'
)


class TextboxFlagCheck(TargetCheckParametrized):
    check_id = "textbox"
    name = gettext_lazy("Rendering textbox")
    description = gettext_lazy("Define the textbox dimensions for rendering")
    default_disabled = True

    @property
    def param_type(self):
        def parse_values(val):
            if len(val) != 3:
                msg = "Missing required parameter"
                raise ValueError(msg)
            return [val[0], int(val[1]), int(val[2])]

        return parse_values

    def check_target_params(
        self, sources: list[str], targets: list[str], unit: Unit, value
    ):
        return False


class ReplacementsRegexCheck(TargetCheckParametrized):
    check_id = "replacements-regex"
    name = gettext_lazy("Extended replacements")
    description = gettext_lazy("Define text replacements with regular expressions")
    default_disabled = True

    @property
    def param_type(self):
        return multi_value_flag(lambda x: x, modulo=2)

    def check_target_params(
        self, sources: list[str], targets: list[str], unit: Unit, value
    ):
        return False


class MaxSizeCheck(TargetCheckParametrized):
    """Check for maximum size of rendered text."""

    check_id = "max-size"
    name = gettext_lazy("Maximum size of translation")
    description = gettext_lazy(
        "Translation rendered text should not exceed given size."
    )
    default_disabled = True
    last_font = None
    always_display = True

    @property
    def param_type(self):
        return multi_value_flag(int, 1, 2)

    def get_params(self, unit: Unit) -> tuple[str, int | None, int, int, list[str]]:
        all_flags = unit.all_flags
        return (
            all_flags.get_value_fallback("font-family", "sans"),
            all_flags.get_value_fallback("font-weight", None),
            all_flags.get_value_fallback("font-size", 10),
            all_flags.get_value_fallback("font-spacing", 0),
            all_flags.get_value_fallback("textbox", ["none", "0", "0"])
        )

    def load_font(self, project, language, name: str) -> str:
        try:
            group = project.fontgroup_set.get(name=name)
        except ObjectDoesNotExist:
            return "sans"
        try:
            override = group.fontoverride_set.get(language=language)
        except ObjectDoesNotExist:
            return f"{group.font.family} {group.font.style}"
        return f"{override.font.family} {override.font.style}"

    def check_target_params(
        self, sources: list[str], targets: list[str], unit: Unit, value
    ):
        if len(value) == 2:
            width, lines = value
        else:
            width = value[0]
            lines = 1
        font_group, weight, size, spacing, textbox = self.get_params(unit)
        font = self.last_font = self.load_font(
            unit.translation.component.project, unit.translation.language, font_group
        )
        replace = self.get_extended_replacement_function(unit)
        screenshot = unit.screenshots.first()
        background = screenshot.image if screenshot is not None else None

        return any(
            (
                not check_render_size(
                    text=replace(target),
                    font=font,
                    weight=weight,
                    size=size,
                    spacing=spacing,
                    width=width,
                    lines=lines,
                    cache_key=self.get_cache_key(unit, i),
                    background=background,
                    textbox=RenderingTextbox(textbox[0], int(textbox[1]), int(textbox[2]))
                )
                for i, target in enumerate(targets)
            )
        )

    @staticmethod
    def get_extended_replacement_function(unit: Unit):
        def noop(content: str) -> str:
            return content

        flags = unit.all_flags
        replacements = []
        if flags.has_value("replacements"):
            replacements += flags.get_value("replacements")
        if flags.has_value("replacements-regex"):
            replacements += flags.get_value("replacements-regex")

        if len(replacements) == 0:
            return noop

        # Parse the flag as key-values
        replacements = dict(
            replacements[pos: pos + 2] for pos in range(0, len(replacements), 2)
        )

        # For each key (regex or string) and value (replacement) change the text
        # It follows the order of appearance, so be careful not matching a
        # replacement with the follow-up expression.
        def regexp_replacement(text: str) -> str:
            for expr, replaced in replacements.items():
                if isinstance(expr, re.Pattern):
                    text = expr.sub(replaced, text)
                else:
                    text = text.replace(expr, replaced)
            return text

        return regexp_replacement

    def get_description(self, check_obj):
        url = reverse(
            "render-check",
            kwargs={"check_id": self.check_id, "unit_id": check_obj.unit_id},
        )
        images = format_html_join(
            "\n",
            IMAGE,
            (
                (f"{url}?pos={i}",)
                for i in range(len(check_obj.unit.get_target_plurals()))
            ),
        )
        if not check_obj.id:
            return format_html(
                "{}{}",
                gettext(
                    "It fits into given boundaries. The rendering is shown for your convenience."
                ),
                images,
            )
        return images

    def render(self, request: AuthenticatedHttpRequest, unit: Unit):
        try:
            pos = int(request.GET.get("pos", "0"))
        except ValueError:
            pos = 0
        key = self.get_cache_key(unit, pos)
        result = cache.get(key)
        if result is None:
            self.check_target_unit(
                unit.get_source_plurals(), unit.get_target_plurals(), unit
            )
            result = cache.get(key)
        if result is None:
            msg = "Invalid check"
            raise Http404(msg)
        response = HttpResponse(content_type="image/png")
        response.write(result)
        return response
