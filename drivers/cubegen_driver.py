#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess

from typing import Text

NPROCS = 2

def cubegen_mo(formchk_file: Text,
               mo: int,
               npts: int = -2
               ) -> Text:
    cube_file = '{}.cube'.format(mo)

    command = ['cubegen']

    command.append(str(NPROCS))
    command.append('MO={}'.format(mo))
    command.append(formchk_file)
    command.append(cube_file)
    command.append(str(npts))
    command.append('h')

    subprocess.call(
        command
    )

    return cube_file