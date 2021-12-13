# MIT License
#
# Copyright (c) 2021 Artem Hotenov
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
"""Test cases for the download command module."""
from typing import Callable
from typing import List

from click.testing import Result
from requests_mock.mocker import Mocker as rm_Mocker


def test_download_stub_call(
    requests_mock: rm_Mocker,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints message and exits."""
    # TODO (hotenov): Update in release version
    result = run_cli_with_args(["download"])
    assert "download_cmd()" in result.output
    assert "was executed..." in result.output
    assert result.exit_code == 0
