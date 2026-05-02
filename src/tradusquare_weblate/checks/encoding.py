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
from codecs import register_error

from django.utils.translation import gettext_lazy

from weblate.checks.base import TargetCheckParametrized
from weblate.checks.parser import multi_value_flag

if TYPE_CHECKING:
    from weblate.trans.models import Unit

REGISTERED_ERROR_HANDLERS: list[str] = []

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
        return multi_value_flag(str, 2, 3)

    def check_target_params(
        self, sources: list[str], targets: list[str], unit: Unit, value
    ):
        # from: https://docs.python.org/3/library/codecs.html#standard-encodings
        enc_name = value[0]
        max_length = int(value[1])

        error_handler = 'replace'
        if len(value) == 3:
            replace_char = value[2]
            error_handler = f"ts-replace-{replace_char}"
            if error_handler not in REGISTERED_ERROR_HANDLERS:
                register_error(error_handler, lambda e : (replace_char, e.end))
                REGISTERED_ERROR_HANDLERS.append(error_handler)

        replace = self.get_replacement_function(unit)
        return any(len(replace(target).encode(enc_name, error_handler)) > max_length for target in targets)
