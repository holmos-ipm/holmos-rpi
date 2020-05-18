# -*- coding: utf-8 -*-
"""
Created on 18.05.2020

@author: beckmann

Start rpi_ui/unwrap_ui.py from base dir, so that paths are resolved.
"""

import sys

from rpi_ui.unwrap_ui import HolmosUnwrapUI

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Please specify a phase image file to open: 'start_unwrap_ui.py <filename>'")
        exit()
    else:
        fn = sys.argv[1]
    HolmosUnwrapUI(fn)
