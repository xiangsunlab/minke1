#! /usr/bin/env python3

import json
import os
import os.path
import subprocess
import sys

from itertools import chain
from typing import Dict

import drivers.cclib_driver as cclib_driver
import drivers.cubegen_driver as cubegen_driver
from report.backend.latex import (
    xyz_coordinate,
    newpage,
    section,
    subsection,
    subsubsection,
    figure,
    excited_state_energies,
    excited_state_table,
    nto_analysis_table
)

MOLECULE_NAME = sys.argv[1 ]

BASE_DIRECTORY = '/home/xis19/Projects/research/xsun/excited-states/aie/pople-vacuum'

GAUSSIAN_OUTPUTS = {
    'ground': {
        'log': '{molecule_name}/ground/molecule.log',
        'fchk': '{molecule_name}/ground/molecule.fchk'
    },
    'vertical_singlet': {
        'log': '{molecule_name}/vertical-singlets/molecule.log',
        'fchk': '{molecule_name}/vertical-singlets/molecule.fchk'
    },
    'vertical_singlet_nto': {
        'nto': True,
        'log': '{molecule_name}/vertical-singlets/nto/molecule.log',
        'fchk': '{molecule_name}/vertical-singlets/nto/nto.fchk'
    },
    'vertical_triplet': {
        'log': '{molecule_name}/vertical-triplets/molecule.log',
        'fchk': '{molecule_name}/vertical-triplets/molecule.fchk'
    },
    'vertical_triplet_nto': {
        'nto': True,
        'log': '{molecule_name}/vertical-triplets/nto/molecule.log',
        'fchk': '{molecule_name}/vertical-triplets/nto/nto.fchk'
    },
    'adiabatic_singlet': {
        'log': '{molecule_name}/adiabatic-singlets/molecule.log',
        'fchk': '{molecule_name}/adiabatic-singlets/molecule.fchk'
    },
    'adiabatic_singlet_nto': {
        'nto': True,
        'log': '{molecule_name}/adiabatic-singlets/nto/molecule.log',
        'fchk': '{molecule_name}/adiabatic-singlets/nto/nto.fchk'
    },
    'adiabatic_triplet': {
        'log': '{molecule_name}/adiabatic-triplets/molecule.log',
        'fchk': '{molecule_name}/adiabatic-triplets/molecule.fchk'
    },
    'adiabatic_triplet_nto': {
        'nto': True,
        'log': '{molecule_name}/adiabatic-triplets/nto/molecule.log',
        'fchk': '{molecule_name}/adiabatic-triplets/nto/nto.fchk'
    },
}

def get_path(k, t):
    return os.path.join(
        BASE_DIRECTORY,
        GAUSSIAN_OUTPUTS[k][t].format(molecule_name=MOLECULE_NAME)
    )

def excited_state_orbitals(excited_states_description: Dict,
                           max_excited_states: int):
    orbits = set()

    for excited_states in excited_states_description.values():
        for excited_state in excited_states[:max_excited_states]:
            for orbital in excited_state['orbitals']:
                orbits.add(orbital['from'])
                orbits.add(orbital['to'])

    return sorted(orbits)


def render_structure(log_file):
    xyz_file_name = log_file.replace('.log', '.xyz')
    png_file_name = log_file.replace('.log', '.png')

    pwd = os.getcwd()
    os.chdir(os.path.split(log_file)[0])

    if not os.path.exists(xyz_file_name):
        subprocess.call(
            'xyz.py {} > {}'.format(log_file, xyz_file_name),
            shell=True
        )
    if not os.path.exists(png_file_name):
        subprocess.call([
            'render.py',
            xyz_file_name
        ])
    os.chdir(pwd)

    return png_file_name


def render_mos(formchk_file, mos):
    generated_images = []
    work_dir = os.path.split(formchk_file)[0]

    pwd = os.getcwd()
    os.chdir(work_dir)
    for mo in mos:
        cube_file = os.path.join(work_dir, '{}.cube'.format(mo))
        png_file = os.path.join(work_dir, '{}.png'.format(mo))

        if not os.path.exists(cube_file):
            cube_file = cubegen_driver.cubegen_mo(formchk_file, mo=mo)
        if not os.path.exists(png_file):
            subprocess.call([
                'render.py',
                cube_file
            ])
        generated_images.append(png_file)

    os.chdir(pwd)
    return generated_images


data_set = {}
for data_set_key in GAUSSIAN_OUTPUTS.keys():
    extractor = cclib_driver.GenericExtractor() if 'nto' not in data_set_key else cclib_driver.NTOExtractor()
    data_set[data_set_key] = extractor.extract(
        get_path(data_set_key, 'log')
    )

rendered_ground_state = render_structure(
    get_path('ground', 'log')
)

# === Vertical Excitation
vertical_excitation_mos = []
vertical_excitation_mos.extend(
    excited_state_orbitals(data_set['vertical_singlet']['excited_states'], 10)
)
vertical_excitation_mos.extend(
    excited_state_orbitals(data_set['vertical_triplet']['excited_states'], 10)
)
vertical_excitation_mos = sorted(list(set(vertical_excitation_mos)))
# NOTE the excited state is a linear combination of multiple ground state
# molecular orbitals.
rendered_ground_structure_mos = render_mos(
    get_path('ground', 'fchk'),
    vertical_excitation_mos
)

# === Vertical singlet NTO
vertical_excitation_singlet_orbits = sorted(list(chain.from_iterable(
    [d['from'], d['to']]
    for d in data_set['vertical_singlet_nto']['nto_contributions']
)))
render_vertical_excitation_singlet_mos = render_mos(
    get_path('vertical_singlet_nto', 'fchk'),
    vertical_excitation_singlet_orbits
)

# === Vertical triplet NTO
vertical_excitation_triplet_orbits = sorted(list(chain.from_iterable(
   [d['from'], d['to']]
   for d in data_set['vertical_triplet_nto']['nto_contributions']
)))
render_vertical_excitation_triplet_mos = render_mos(
   get_path('vertical_triplet_nto', 'fchk'),
   vertical_excitation_triplet_orbits
)

# === Adiabatic singlet
adiabatic_singlet_mos = excited_state_orbitals(data_set['adiabatic_singlet']['excited_states'], 10)
rendered_adiabatic_singlet_state = render_structure(
    get_path('adiabatic_singlet', 'log')
)
rendered_adiabatic_singlet_mos = render_mos(
    get_path('adiabatic_singlet', 'fchk'),
    adiabatic_singlet_mos
)

# === Adiabatic singlet NTO
adiabatic_excitation_singlet_orbits = sorted(list(chain.from_iterable(
   [d['from'], d['to']]
   for d in data_set['adiabatic_singlet_nto']['nto_contributions']
)))
render_adiabatic_excitation_singlet_mos = render_mos(
   get_path('adiabatic_singlet_nto', 'fchk'),
   adiabatic_excitation_singlet_orbits
)

# === Adiabatic triplet
adiabatic_triplet_mos = excited_state_orbitals(data_set['adiabatic_triplet']['excited_states'], 10)
rendered_adiabatic_triplet_state = render_structure(
    get_path('adiabatic_triplet', 'log')
)
rendered_adiabatic_triplet_mos = render_mos(
    get_path('adiabatic_triplet', 'fchk'),
    adiabatic_triplet_mos
)

# === Adiabatic triplet NTO
adiabatic_excitation_triplet_orbits = sorted(list(chain.from_iterable(
   [d['from'], d['to']]
   for d in data_set['adiabatic_triplet_nto']['nto_contributions']
)))
render_adiabatic_excitation_triplet_mos = render_mos(
   get_path('adiabatic_triplet_nto', 'fchk'),
   adiabatic_excitation_triplet_orbits
)


# === LATEX OUTPUT

latex_output_list = []

latex_output_list.append(r"""\documentclass[a4paper, 8pt]{article}

\usepackage{float}
\usepackage{graphicx}
\usepackage[a4paper, margin=0.7in]{geometry}
\usepackage{hyperref}
\usepackage{longtable}
\usepackage{multirow}
\usepackage{tabularx}
\usepackage{times}
\usepackage[flushleft]{threeparttable}

\pagestyle{headings}

\setlength\extrarowheight{1pt}

\begin{document}

\tableofcontents
\newpage

\listoftables
\newpage

\listoffigures
\newpage
""")

latex_output_list.append(section('Overview'))
latex_output_list.append(excited_state_energies(
    data_set=data_set,
    caption='S0 and 1st excitation state energies (in Hartrees)',
    n_root=0,
    ground_state_key='ground',
    vertical_excitation_singlet_key='vertical_singlet',
    vertical_excitation_triplet_key='vertical_triplet',
    relaxed_excitation_singlet_key='adiabatic_singlet',
    relaxed_excitation_triplet_key='adiabatic_triplet'
))
latex_output_list.append(newpage())

latex_output_list.append(section('Ground state'))
latex_output_list.append(figure(
    'S0 state structure',
    rendered_ground_state
))
latex_output_list.append(newpage())

latex_output_list.append(xyz_coordinate(
    'S0 state structure (in \\AA)',
    data_set,
    'ground'
))
latex_output_list.append(newpage())

latex_output_list.append(subsection('Vertical excitation: singlets'))
latex_output_list.append(excited_state_table(
    data_set=data_set,
    caption='Vertical excitation: Singlets',
    data_set_key='vertical_singlet',
    max_states=10
))
latex_output_list.append(newpage())

latex_output_list.append(subsection('Vertical excitation: triplets'))
latex_output_list.append(excited_state_table(
    data_set=data_set,
    caption='Vertical excitation: Triplets',
    data_set_key='vertical_triplet',
    max_states=10
))
latex_output_list.append(newpage())

latex_output_list.append(subsection('Orbits (S0 structure)'))
for index in range(len(vertical_excitation_mos)):
    mo_index = vertical_excitation_mos[index]
    caption = 'S0 molecular orbital {}'.format(mo_index)
    if mo_index <= data_set['ground']['homo_index']:
        caption += ' (occupied)'
    else:
        caption += ' (unoccupied)'
    latex_output_list.append(figure(
        caption,
        rendered_ground_structure_mos[index]
    ))
    latex_output_list.append(newpage())

# S0 -- NTO Vertical Singlets
latex_output_list.append(subsection('Natural Transition Orbital (NTO) Analysis'))
latex_output_list.append(subsubsection('Vertical Singlets'))
latex_output_list.append(nto_analysis_table(
    data_set, 'NTO -- Vertical Singlets', 'vertical_singlet_nto'))
latex_output_list.append(newpage())

for index in range(len(vertical_excitation_singlet_orbits)):
    mo_index = vertical_excitation_singlet_orbits[index]
    caption = 'Vertical Singlet NTO Orbital {}'.format(mo_index)
    latex_output_list.append(figure(
        caption,
        render_vertical_excitation_singlet_mos[index]
    ))
    latex_output_list.append(newpage())

latex_output_list.append(subsubsection('Vertical Triplets'))
latex_output_list.append(nto_analysis_table(
    data_set, 'NTO -- Vertical Triplets', 'vertical_triplet_nto'))
latex_output_list.append(newpage())


for index in range(len(vertical_excitation_triplet_orbits)):
    mo_index = vertical_excitation_triplet_orbits[index]
    caption = 'Vertical Triplet NTO Orbital {}'.format(mo_index)
    latex_output_list.append(figure(
        caption,
        render_vertical_excitation_triplet_mos[index]
    ))
    latex_output_list.append(newpage())

# === S1
latex_output_list.append(section('S1 state'))
latex_output_list.append(figure(
    'Relaxed S1 structure',
    rendered_adiabatic_singlet_state
))
latex_output_list.append(newpage())

latex_output_list.append(xyz_coordinate(
    'Relaxed S1 structure (in \\AA)',
    data_set,
    'adiabatic_singlet'
))
latex_output_list.append(newpage())

latex_output_list.append(excited_state_table(
    data_set=data_set,
    caption='Adiabatic excitation: Singlets',
    data_set_key='adiabatic_singlet',
    max_states=10
))
latex_output_list.append(newpage())

latex_output_list.append(subsection('Orbits (S1 structure)'))
for index in range(len(adiabatic_singlet_mos)):
    mo_index = adiabatic_singlet_mos[index]
    caption = 'S1 molecular orbital {}'.format(mo_index)
    if mo_index <= data_set['adiabatic_singlet']['homo_index']:
        caption += ' (occupied)'
    else:
        caption += ' (unoccupied)'
    latex_output_list.append(figure(
        caption,
        rendered_adiabatic_singlet_mos[index]
    ))
    latex_output_list.append(newpage())

latex_output_list.append(subsection('Natural Transition Orbital (NTO) Analysis'))
latex_output_list.append(nto_analysis_table(
    data_set, 'NTO -- Adiabatic Singlets', 'adiabatic_singlet_nto'))
latex_output_list.append(newpage())

for index in range(len(adiabatic_excitation_singlet_orbits)):
    mo_index = adiabatic_excitation_singlet_orbits[index]
    caption = 'Adiabatic Singlet NTO Orbital {}'.format(mo_index)
    latex_output_list.append(figure(
        caption,
        render_adiabatic_excitation_singlet_mos[index]
    ))
    latex_output_list.append(newpage())


# === T1
latex_output_list.append(section('T1 state'))
latex_output_list.append(figure(
    'Relaxed T1 structure',
    rendered_adiabatic_triplet_state
))
latex_output_list.append(newpage())

latex_output_list.append(xyz_coordinate(
    'Relaxed T1 structure (in \\AA)',
    data_set,
    'adiabatic_triplet'
))
latex_output_list.append(newpage())

latex_output_list.append(excited_state_table(
    data_set=data_set,
    caption='Adiabatic excitation: Triplets',
    data_set_key='adiabatic_triplet',
    max_states=10
))
latex_output_list.append(newpage())

latex_output_list.append(subsection('Orbits (T1 structure)'))
for index in range(len(adiabatic_triplet_mos)):
    mo_index = adiabatic_triplet_mos[index]
    caption = 'T1 molecular orbital {}'.format(mo_index)
    if mo_index <= data_set['adiabatic_triplet']['homo_index']:
        caption += ' (occupied)'
    else:
        caption += ' (unoccupied)'
    latex_output_list.append(figure(
        caption,
        rendered_adiabatic_triplet_mos[index]
    ))
    latex_output_list.append(newpage())

latex_output_list.append(subsection('Natural Transition Orbital (NTO) Analysis'))
latex_output_list.append(nto_analysis_table(
    data_set, 'NTO -- Adiabatic Triplets', 'adiabatic_triplet_nto'))
latex_output_list.append(newpage())

for index in range(len(adiabatic_excitation_triplet_orbits)):
    mo_index = adiabatic_excitation_triplet_orbits[index]
    caption = 'Adiabatic Triplet NTO Orbital {}'.format(mo_index)
    latex_output_list.append(figure(
        caption,
        render_adiabatic_excitation_triplet_mos[index]
    ))
    latex_output_list.append(newpage())



latex_output_list.append(r"\end{document}")


with open('output_aie_pople/{}.tex'.format(MOLECULE_NAME), 'w') as stream:
    stream.write('\n'.join(latex_output_list))
