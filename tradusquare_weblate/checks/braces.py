#   Copyright 2019 Benito Palacios Sanchez (aka pleonex)
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
"""Weblate format for brace control code styles."""

import re

from django.utils.translation import ugettext_lazy as _
from weblate.checks.base import TargetCheck

BRACE_MATCH = re.compile(r"{[^}]+}")


class BraceCheck(TargetCheck):
    """
    Custom checks for control codes enclosed in braces.

    Validates that the translation has the same control codes
    as the original text. The expected format uses braces: {CONTROL_CODE}

    It also adds highlighting.
    """

    check_id = "brace-format"
    name = _("Mismatched brace control codes")
    description = _("Brace control codes in translation does not match source")
    severity = "warning"
    default_disabled = True

    def check_highlight(self, source, unit):
        """Highlight the braces and its content."""
        if self.should_skip(unit):
            return []
        ret = []
        for match in BRACE_MATCH.finditer(source):
            ret.append((match.start(), match.end(), match.group()))
        return ret

    def check_single(self, source, target, unit):
        """Validate that the same control codes are in the translated text."""
        src_match = BRACE_MATCH.findall(source)
        if not src_match:
            return False

        tgt_match = BRACE_MATCH.findall(target)
        if len(src_match) != len(tgt_match):
            return True

        return src_match != tgt_match
