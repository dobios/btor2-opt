##########################################################################
# BTOR2 parser, code optimizer, and circuit miter
# Copyright (C) 2024  Amelia Dobis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
##########################################################################

# List/register all passes here

from ..passes.genericpass import Pass
from ..passes.transforms.renameInputs import RenameInputs
from ..passes.transforms.initAllStates import InitAllStates
from ..passes.validation.checkLidOrdering import CheckLidOrdering

# Retrieves a pass from the list given an id
def find_pass(p: list[Pass], id: str) -> Pass:
    return next((e for e in p if e.id == id), None)

# List containing all passes
all_passes = [RenameInputs(), InitAllStates(), CheckLidOrdering()]
