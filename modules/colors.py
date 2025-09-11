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

import logging


def ticker_color(ticker: str):
    """
    Returns a RGB (float) color for a ticker symbol.
    Scales ticker's A-Z characters to 1-0 for RGB from first three characters.
    Uses last character as brightness, A being brightest, Z being darkest.
    """
    if len(ticker) < 4:
        logging.warning("Ticker '%s' is less than 4 characters long. will use white for coloring.", ticker)
        return [1, 1, 1]
    for c in ticker[0:4]:
        if ord(c) < ord('A') or ord(c) > ord('Z'):
            logging.warning("Ticker '%s' contains non-alphabetic characters. will use white for coloring.", ticker)
            return [1, 1, 1]
    m = 1 + (ord('A') - ord(ticker[0])) / 25
    r = 1 + (ord('A') - ord(ticker[1])) / 25
    g = 1 + (ord('A') - ord(ticker[2])) / 25
    b = 1 + (ord('A') - ord(ticker[3])) / 25
    return [r * m, g * m, b * m]
