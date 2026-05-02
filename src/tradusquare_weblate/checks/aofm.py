#   Copyright 2017 Benito Palacios Sanchez (aka pleonex)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Weblate checks for 'Attack of the Friday Monsters' game."""

import re

from django.utils.translation import gettext as _
from weblate.checks.base import TargetCheck

XML_MATCH = re.compile(r"<[^>]+>")


class AofmKeywordCheck(TargetCheck):
    """
    Custom checks for the Attack of the Friday Monster translation.

    Adds a new check for the control codes enclosed by '<' and '>'. They are
    not XML as there isn't a closing equivalent. The check only ensures that
    the texts contain "<end>".

    It also adds highlighting.
    """

    check_id = "game-aofm"
    name = _("AoFM keywords")
    description = _("AoFM keywords are missing")
    default_disabled = True

    def check_highlight(self, source, unit):
        """Highlight the control codes enclosed by the angles."""
        if self.should_skip(unit):
            return []
        return [
            (match.start(), match.end(), match.group())
            for match in XML_MATCH.finditer(source)
        ]

    # Real check code
    def check_single(self, source, target, unit):
        """Validate that the text contains the end control code."""
        if self.should_skip(unit):
            return False

        return "<end>" not in target
