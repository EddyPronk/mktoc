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
This module is the main entry point for the mktoc application. The
simpliest way to run this module is with the following statements:

   import mktoc._mktoc as mktoc
   mktoc.main()

For detailed application usage information, run 'mktoc --help' or
'pydoc mktoc'.
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import os
import sys
import traceback
import logging
import re
from optparse import OptionParser

from mktoc.base import *
from mktoc import parser as mt_parser

__all__ = ['main']

# WAV file reading command-line switch
#  - allow 'file not found' errors when reading WAV files
_OPT_ALLOW_WAV_FNF   = '-a'
# Offset correction command-line switch
# - enable output of offset corrected WAV files
_OPT_OFFSET_CORRECT  = '-c'
# Output CUE file name
_OPT_CUE_FILE        = '-f'
# Temp WAV Files
# - write offset corrected WAV files to /tmp dir
_OPT_TEMP_WAV        = '-t'
# WAV File List
# - create a TOC file using a list of WAV files
_OPT_WAV_LIST        = '-w'


##############################################################################
class _Mktoc(object):
   """Container class for mktoc's primary execution code."""

   def __init__(self):
      """Starts the main parsing routine for mktoc."""
      self._main()

   def _main(self):
      """Starting execution point. Interprets all program arguments
      and creates a CueParser object to generate a final TOC file."""
      # parse all command line arguments, exit if there is any error
      opt,args = self._parse_args()
      # setup logging
      if opt.debug: logging.basicConfig(level=logging.DEBUG)
      # check if using WAV list or CUE file
      if opt.wav_files is None:
         # open CUE file
         if opt.cue_file:
            try:
               fh_in = open(opt.cue_file)
               # set the working dir of the input file
               cue_dir = os.path.dirname( fh_in.name ) or os.curdir
            except:
               print >> sys.stderr, sys.exc_value
               exit(-1)
         else:
            cue_dir = os.curdir
            fh_in = sys.stdin
         # create CUE file parser
         assert(cue_dir)
         p = mt_parser.CueParser( cue_dir, opt.find_wav)
         cd_data = p.parse( fh_in)
         fh_in.close()
      else:
         wav_dir = os.path.dirname( opt.wav_files[0] )
         # create WAV list parser
         p = mt_parser.WavParser( wav_dir, opt.find_wav)
         cd_data = p.parse( opt.wav_files)
      if opt.wav_offset:
         cd_data.modWavOffset( opt.wav_offset, opt.write_tmp )
      toc = cd_data.getToc()
      # open TOC file
      if opt.toc_file:
         try:
            fh_out = open(opt.toc_file,'w')
         except:
            print >> sys.stderr, sys.exc_value
            exit(-1)
      else:
         fh_out = sys.stdout
      fh_out.write( self._banner_msg() )
      fh_out.write( '\n'.join(toc) )
      fh_out.close()

   def _banner_msg(self):
      """Returns a TOC comment header that is placed at the top of the
      TOC file."""
      return "// Generated by %s %s\n" % (progName, VERSION) + \
         "// %s, %s\n" % (__copyright__, __author__) + \
         "// Report bugs to <%s>\n" % __email__

   def _parse_args(self):
      """Use OptionParser object to handle all input arguments and
      return opt structure and args list as a tuple. All argument
      error checking is performed in this function."""
      usage = '[OPTIONS] [[-f] CUE_FILE|-w WAV_FILES] [[-o] TOC_FILE]'
      parser = OptionParser( usage='%prog '+usage, version='%prog '+VERSION,
                             conflict_handler='resolve')
      parser.add_option('--help', action='callback',
            callback=self._parse_full_help,
            help='show detailed usage instructions and exit' )
      parser.add_option( _OPT_ALLOW_WAV_FNF, '--allow-missing-wav',
            dest='find_wav', action="store_false", default=True,
            help='do not abort when WAV file(s) are missing, (experts only)')
      parser.add_option( _OPT_OFFSET_CORRECT, '--offset-correction',
            dest='wav_offset', type='int',
            help='correct reader/writer offset by creating WAV file(s) '\
                 'shifted by WAV_OFFSET samples (original data is '\
                 'not modified)' )
      parser.add_option('-d', '--debug', dest='debug', action="store_true",
            default=False, help='enable debugging statements' )
      parser.add_option( _OPT_CUE_FILE, '--file', dest='cue_file',
            help='specify the input CUE file to read')
      parser.add_option('-o', '--output', dest='toc_file',
            help='specify the output TOC file to write')
      parser.add_option( _OPT_TEMP_WAV, '--use-temp', dest='write_tmp',
            action='store_true', default=False,
            help='write offset corrected WAV files to /tmp directory' )
      parser.add_option( _OPT_WAV_LIST, '--wave', dest='wav_files',
            action='callback', callback=self._parse_wav,
            help='write a TOC file using list of WAV files' )
      # execute parsing step
      opt,args = parser.parse_args()

      # test "WAV file not found" and "offset correction" argument combination
      if opt.wav_offset and not opt.find_wav:
         parser.error("Can not combine '%s' and '%s' options!" % \
                        (_OPT_ALLOW_WAV_FNF,_OPT_OFFSET_CORRECT) )
      # test "offset correction" and "temp WAV" argument combination
      if opt.write_tmp and not opt.wav_offset:
         parser.error("Can not use '%s' without '%s' option!" % \
                        (_OPT_TEMP_WAV, _OPT_OFFSET_CORRECT) )
      # test "CUE File" and "-w" argument combination
      if opt.cue_file is not None and opt.wav_files is not None:
         parser.error("Can not combine '%s' and '%s' options!" % \
                        (_OPT_CUE_FILE, _OPT_WAV_LIST) )
      # The '-w' option is used to create a TOC file using a list of WAV files.
      # The default mode is to convert a CUE file. The 'if' checks for the
      # default mode.
      if opt.wav_files is None:
         # the '-w' flag is not set. 1st argument names the input CUE file, 2nd
         # argument names the output TOC file.
         if len(args)>2 or \
               (len(args)>=1 and opt.cue_file) or \
               (len(args)>=2 and opt.toc_file):
            parser.error("Ambiguous file arguments!")
         else:
            # set file names if 'args' list is not empty
            if len(args)>=1: opt.cue_file = args[0]
            if len(args)>=2: opt.toc_file = args[1]
      else:
         # the '-w' flag was set. Only 1 argument is allowed to name the output
         # TOC file.
         if len(args)>1:
            parser.error("Ambiguous file arguments!")
         else:
            # set file names if 'args' list is not empty
            if len(args)>=1: opt.toc_file = args[0]
      return opt,args

   def _parse_full_help(self, option, opt_str, value, parser):
      """Callback to print a detailed help output page."""
      import mktoc
      parser.exit( msg=mktoc.__doc__)

   def _parse_wav(self, option, opt_str, value, parser):
      """OptionParser callback function to correctly handle '-w' WAV
      file input arguments. All trailing WAV files will be placed in
      the parser.values.wav_files list. The operation will stop at
      either the first non-WAV file argument or the end of the
      argument list."""
      slice_idx = 0
      for arg in parser.rargs:
         if re.search( r'\.wav$', arg, re.IGNORECASE):
            slice_idx += 1
         else: break

      # if one or more WAV files were found, move them to the parser wav_file
      # list
      if slice_idx:
         parser.values.wav_files = parser.rargs[0:slice_idx]
         del parser.rargs[0:slice_idx]
      else:
         parser.error( '%s option requires one or more WAV file arguments' \
                        % opt_str )


##############################################################################
def _error_msg(e):
   """Print a default error message to the user."""
   print >> sys.stderr, """
   ERROR! -- An unrecoverable error has occurred. If you believe the CUE
   file is correct, please send the input file to <%s>,
   along with the error message below.

   ---> %s
   """ % (__email__,e)

def _error_msg_file(e):
   """Print a missing WAV file error message to the user."""
   print >> sys.stderr, """
   ERROR! -- Could not locate WAV file:
   --->  '%s'

   Cdrdao can not correctly write pregaps in TOC files without explicit file
   lengths. If you know what you are doing, you can disable this check with
   the '%s' option.
   """ % (e,_OPT_ALLOW_WAV_FNF)

def main():
   """Primary entry point for the mktoc command line application.
   Creates a _Mktoc object and catches any exceptions."""
   global progName
   progName = os.path.basename(sys.argv[0])
   try:
      _Mktoc()
   except EmptyCueData: pass     # ignore NULL data input (Ctrl-C)
   except FileNotFoundError, e:
      _error_msg_file(e)
   except MkTocError, e:
      _error_msg(e)
   except Exception:
      traceback.print_exc()
   except: pass      # ignore base exceptions (exit,key-int)
   else: return 0    # no exception, exit success
   return 1          # exit with failure

if __name__ == '__main__':
   main()

