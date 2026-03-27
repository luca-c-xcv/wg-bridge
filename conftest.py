# conftest.py
#
# Copyright (C) 2026  MoonyFringers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Pytest configuration for WG-Bridge.

This module configures pytest to properly resolve imports from the src/
directory, allowing tests to be run from the repository root without needing
to adjust PYTHONPATH.
"""

import sys
from pathlib import Path

# Add src/ to sys.path so that 'from core.xxx import ...' resolves correctly
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
