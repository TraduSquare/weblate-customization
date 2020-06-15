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

from weblate.checks.base import TargetCheck
import re

XML_MATCH = re.compile(r'<[^>]+>')

class AofmKeywordCheck(TargetCheck):
    check_id = 'game-aofm'
    name = 'AoFM keywords'
    description = 'AoFM keywords are missing'
    default_disabled = True

    def check_highlight(self, source, unit):
        if self.should_skip(unit):
            return []
        return [(match.start(), match.end(), match.group()) for match in XML_MATCH.finditer(source)]

    # Real check code
    def check_single(self, source, target, unit):
        if self.should_skip(unit):
            return False

        return '<end>' not in target
