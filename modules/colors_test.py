#!/usr/bin/env python3

# Investment Portfolio Optimizer
# Copyright (C) 2024  Vladimir Looze

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pytest
from modules import colors


@pytest.mark.parametrize(
    "ticker, color",
    [
        ["AAAA", [1.00, 1.00, 1.00]],
        ["ZAAA", [0.00, 0.00, 0.00]],
        ["AZZZ", [0.00, 0.00, 0.00]],
        ["ZZZZ", [0.00, 0.00, 0.00]],
        ["AYYY", [0.04, 0.04, 0.04]],
        ["ABBB", [0.96, 0.96, 0.96]],
        ["AXYZ", [0.08, 0.04, 0.00]],
        ["ABCD", [0.96, 0.92, 0.88]],
    ]
)
def test_ticker_color(ticker, color):
    color_returned = colors.ticker_color(ticker)
    # round to 3 decimal places to avoid floating point precision issues
    color_returned = [round(c, 3) for c in color_returned]
    assert color_returned == color


@pytest.mark.parametrize(
    "ticker",
    [
        "!ABC",
        "XYZ!",
        " ABC",
        "ABC  ",
        "FO%OBAR",
    ]
)
def test_ticker_color_non_alpha(ticker):
    assert colors.ticker_color(ticker) == [1, 1, 1]
