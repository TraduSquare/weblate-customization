#   Copyright 2026 Tradusquare
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
from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy

from weblate.checks.base import TargetCheckParametrized

if TYPE_CHECKING:
    from weblate.trans.models import Unit


class MaxEncodedLengthCheck(TargetCheckParametrized):
    """Check for maximum encoded length of translation."""

    check_id = "max-encoded"
    name = gettext_lazy("Maximum encoded length of translation")
    description = gettext_lazy(
        "Byte count of encoded translation should not exceed given length."
    )
    default_disabled = True

    @property
    def param_type(self):
        def parse_values(val):
            if len(val) != 2:
                msg = "Missing required parameter"
                raise ValueError(msg)
            return [val[0], int(val[1])]

        return parse_values

    def check_target_params(
        self, sources: list[str], targets: list[str], unit: Unit, value
    ):
        # from: https://docs.python.org/3/library/codecs.html#standard-encodings
        enc_name = value[0]
        max_length = int(value[1])

        replace = self.get_replacement_function(unit)
        print(f"running max-encoded on {targets} with {enc_name} for {max_length}")
        return any(len(replace(target).encode(enc_name)) > max_length for target in targets)
