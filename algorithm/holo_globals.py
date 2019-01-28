# -*- coding: utf-8 -*-
"""
Created on 03.08.2018
"""

import enum


class ProcessingStep(enum.Enum):
    STEP_UNDEFINED = 0
    STEP_CAM_IMAGE = 1
    STEP_FFT = 2
    STEP_VIS_PHASES_RAW = 10
    # synthetic phases not used in Holmos - if they are, these are the values used at IPM:
    #STEP_SYN_PHASES_RAW = 20
    #STEP_SYN_PHASES_FILT = 21
    #STEP_SYN_PHASES_COMBINED = 30


class RpiCamMode(enum.Enum):
    MJPEG_STREAM = 0
    BAYER_RAW = 1
