#  Copyright 2008, Patrick C. McGinty

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module for mktoc that prints a progress indication. The default usage is to
prompt the user when an operation is running that the user must wait for. The
following object classes are:

   ProgressBar
      Creates a progress bar given program input.
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import time

from mktoc.base import *

__all__ = ['ProgressBar']


class ProgressBar( object ):
   """Creates a progress bar string to be printed by the calling function.

   Public Data Members:
      max_
         The maximum input input value expected by the progress bar. This value
         should be set before trying to print the progress bar. All percentage
         calculations are based from this value. It is OK to update this value
         as many times as needed, however it might confuse the user.

   Private Data Members:
      _notice_text
         String to contain a message printed alongside the progress bar.

      _size
         The total integer count of the 'progress'. This value is modified by
         the overloaded '+=' operator. This value can never go above 'max_'.
   """
   def __init__(self, notice_txt):
      """Initialize object defaults.

      Parameters:
         notice_txt  : String assigned to _notice_txt member that is printed
                       alongside the progress bar.
      """
      self._notice_txt = notice_txt
      self._size  = 0
      self.max_   = 0           # default max value

   def __iadd__(self, other):
      """+= operator that increments the current state of the progress bar. The
      input value can be of any range, but the progress bar value will be fixed
      at 'max_'."""
      self._size += min(other, self.max_ - self._size)
      return self

   def __str__(self):
      """Returns a progress bar string."""
      if not self.max_:
         raise Exception("You must initialize ProgressBar.max_ first")
      if not hasattr(self,'_start_time'):
         self._start_time = time.time()
         time_dif = 0
      else:
         time_dif = time.time() - self._start_time    # compute time from start
      percent = float(self._size) / self.max_ * 100
      if time_dif:
         rate = self._size / time_dif      # calculate sample/sec
         # estimate time left
         remain_time = (self.max_ - self._size) / rate
         remain_str = '\tETA [%d:%02d]' % divmod(remain_time,60)
      else:
         remain_str = '\tETA [?:??]'
      return '%s %3d%% %s\r' % (self._notice_txt, percent, remain_str)

