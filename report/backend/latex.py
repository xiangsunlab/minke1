#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import re

from typing import Dict, List, Text

import jinja2

LATEX_JINJA2_ENV = jinja2.Environment(
	block_start_string = r'\BLOCK{',
	block_end_string = '}',
	variable_start_string = r'\VAR{',
	variable_end_string = '}',
	comment_start_string = r'\#{',
	comment_end_string = '}',
	line_statement_prefix = '%%',
	line_comment_prefix = '%#',
	trim_blocks = True,
	autoescape = False,
)


SECTION_TEMPLATE = LATEX_JINJA2_ENV.from_string(
    r'\section{\VAR{section_name}}'
)
SUBSECTION_TEMPLATE = LATEX_JINJA2_ENV.from_string(
    r'\subsection{\VAR{subsection_name}}'
)
SUBSUBSECTION_TEMPLATE = LATEX_JINJA2_ENV.from_string(
    r'\subsubsection{\VAR{subsubsection_name}}'
)

FIGURE_TEMPLATE = LATEX_JINJA2_ENV.from_string(r"""
\begin{figure}[htp]
\begin{center}
  \caption{\VAR{caption}}
  \includegraphics[width=\textwidth]{\VAR{image_path}}
\end{center}
\end{figure}
""")

COORDINATE_TABLE_HEADING = LATEX_JINJA2_ENV.from_string(r"""
\begin{center}
\begin{longtable}{rcrrr}
  \caption{\VAR{caption}}\\

  \hline\hline

  \multirow{2}{*}{Index}
  &\multirow{2}{*}{Symbol}
  &\multicolumn{3}{c}{Coordinate}\\

  &&\multicolumn{1}{c}{X}
  &\multicolumn{1}{c}{Y}
  &\multicolumn{1}{c}{Z}\\

  \hline
  \endfirsthead

  \caption[]{\VAR{caption}}\\
  \hline\hline

  \multirow{2}{*}{Index}
  &\multirow{2}{*}{Symbol}
  &\multicolumn{3}{c}{Coordinate}\\

  &&\multicolumn{1}{c}{X}
  &\multicolumn{1}{c}{Y}
  &\multicolumn{1}{c}{Z}\\
  \hline
  \endhead
""")
COORDINATE_TABLE_TAILING = LATEX_JINJA2_ENV.from_string(r"""

  \hline\hline
\end{longtable}
\end{center}
""")
COORDINATE_TABLE_ROW = LATEX_JINJA2_ENV.from_string(r"""
  \VAR{index}
  &\VAR{'%02s' % symbol}
  &\VAR{'%0.5f' % x}
  &\VAR{'%0.5f' % y}
  &\VAR{'%0.5f' % z}\\
""")

EXCITED_STATE_ENERGIES_COMPARISION = LATEX_JINJA2_ENV.from_string(r"""
\begin{center}
\begin{longtable}{l|ccc}
  \caption{\VAR{caption}}\\
  \hline\hline
  &$R^{GS}$
  &$R^{ES-S}$
  &$R^{ES-T}$\\
  \hline
  \endfirsthead

  \caption[]{\VAR{caption}}\\
  \endhead


  $E^{GS}$
  &\VAR{'%0.7f' % rgs_egs}
  &\VAR{'%0.7f' % ress_egs}
  &\VAR{'%0.7f' % rest_egs}\\

  $E^{ES-S}$
  &\VAR{'%0.7f' % rgs_eess}
  &\VAR{'%0.7f' % ress_eess}
  &-\\

  $E^{ES-T}$
  &\VAR{'%0.7f' % rgs_eest}
  &-
  &\VAR{'%0.7f' % rest_eest}\\

  \hline\hline
\end{longtable}
\end{center}
""")

EXCITED_STATE_TABLE_HEADING = LATEX_JINJA2_ENV.from_string(r"""
\begin{center}
\begin{longtable}{crrrcr}
  \caption{\VAR{caption}}\\
  \hline\hline
  Excited&
  \multicolumn{3}{c}{Excitation Energy}&
  \multicolumn{1}{c}{Symmmetric}&
  \multicolumn{1}{c}{Oscillaton}\\

  State&
  \multicolumn{1}{c}{eV}&
  \multicolumn{1}{c}{nm}&
  \multicolumn{1}{c}{Hartree}&
  \multicolumn{1}{c}{Group}&
  \multicolumn{1}{c}{Strength}\\
  \hline
  \endfirsthead
  
  \caption[]{\VAR{caption}}\\
  \hline\hline
  Excited&
  \multicolumn{3}{c}{Excitation Energy}&
  \multicolumn{1}{c}{Symmmetric}&
  \multicolumn{1}{c}{Oscillaton}\\

  State&
  \multicolumn{1}{c}{eV}&
  \multicolumn{1}{c}{nm}&
  \multicolumn{1}{c}{Hartree}&
  \multicolumn{1}{c}{Group}&
  \multicolumn{1}{c}{Strength}\\
  \hline
  \endhead
""")
EXCITED_STATE_TABLE_TAILING = LATEX_JINJA2_ENV.from_string(r"""
    \hline\hline
\end{longtable}
\end{center}
""")

EXCITED_STATE_ROW = LATEX_JINJA2_ENV.from_string(r"""
\rule{0pt}{4ex}
\VAR{index}
&\VAR{'%0.4f' % eV}
&\VAR{'%0.2f' % nm}
&\VAR{'%0.5f' % hartree}
&\VAR{symmetric_group}
&\VAR{'%0.4f' % oscillator_strength}\\
\rule{0pt}{1ex}
""")

EXCITED_STATE_COEFFICIENT_ROW = LATEX_JINJA2_ENV.from_string(r"""
&&\multicolumn{4}{r}{
  \begin{tabular}{rclm{2cm}}
     \VAR{('%3d' % from_) | replace(' ', '\\ ')}
    &\VAR{direction}
    &\VAR{('%3d' % to) | replace(' ', '\\ ')}
    &\VAR{('% 0.5f' % coefficient) | replace(' ', '\\ ')}\\
  \end{tabular}
}\\
""")

NTO_ANALYSIS_TABLE_HEADING = LATEX_JINJA2_ENV.from_string(r"""
\begin{center}
\begin{longtable}{ccr}
  \caption{\VAR{caption}}\\
  \hline\hline
  From&To&\multicolumn{1}{c}{Contribution}\\
  \hline
  \endfirsthead

  \caption{\VAR{caption}}\\
  \hline\hline
  From&To&\multicolumn{1}{c}{Contribution}\\
  \hline
  \endfirsthead
  \endhead
""")
NTO_ANALYSIS_TABLE_TAILING = LATEX_JINJA2_ENV.from_string(r"""
    \hline\hline
\end{longtable}
\end{center}
""")
NTO_ANALYSIS_TABLE_ROW = LATEX_JINJA2_ENV.from_string(r"""
  \VAR{('%3d' % from_) | replace(' ', '\\ ')} &
  \VAR{('%3d' % to) | replace(' ', '\\ ')} &
  \VAR{('% 0.5f' % contribution) | replace(' ', '\\ ')} \\ 
""")

HARTREE_TO_EV = 27.21138602
NM_TO_HARTREE = 45.56335

def newpage() -> Text:
    return r'\newpage'

def section(name: Text) -> Text:
    return SECTION_TEMPLATE.render(section_name=name)

def subsection(name: Text) -> Text:
    return SUBSECTION_TEMPLATE.render(subsection_name=name)

def subsubsection(name: Text) -> Text:
    return SUBSUBSECTION_TEMPLATE.render(subsubsection_name=name)

def figure(caption: Text, image_path: Text) -> Text:
    return FIGURE_TEMPLATE.render(
        caption=caption,
        image_path=image_path
    )

def xyz_coordinate(caption: Text, data_set: Dict, data_set_key: Text) -> Text:
    table_data = []
    table_data.append(COORDINATE_TABLE_HEADING.render(
        caption=caption
    ))
    for index in range(data_set[data_set_key]['num_atoms']):
        atom_symbol = data_set[data_set_key]['atoms']['symbols'][index]
        atom_coord = data_set[data_set_key]['atoms']['coordinates'][index]
        table_data.append(COORDINATE_TABLE_ROW.render(
            index=index + 1,
            symbol=atom_symbol,
            x=atom_coord[0],
            y=atom_coord[1],
            z=atom_coord[2]
        ))
    table_data.append(COORDINATE_TABLE_TAILING.render())
    return '\n'.join(table_data)

def excited_state_energies(data_set: Dict,
                           caption: Text,
                           n_root: int,
                           ground_state_key: Text,
                           vertical_excitation_singlet_key: Text,
                           vertical_excitation_triplet_key: Text,
                           relaxed_excitation_singlet_key: Text,
                           relaxed_excitation_triplet_key: Text,
                           label: Text = None) -> Text:
    rgs_egs = data_set[ground_state_key]['scf_energy']
    ress_egs = data_set[relaxed_excitation_singlet_key]['scf_energy']
    rest_egs = data_set[relaxed_excitation_triplet_key]['scf_energy']

    rgs_eess = (
        rgs_egs + data_set[vertical_excitation_singlet_key]
                          ['excited_states']
                          ['singlet']
                          [n_root]
                          ['excitation_energy'])
    ress_eess = (
        ress_egs + data_set[relaxed_excitation_singlet_key]
                           ['excited_states']
                           ['singlet']
                           [n_root]
                           ['excitation_energy']
    )

    rgs_eest = (
        rgs_egs + data_set[vertical_excitation_triplet_key]
                          ['excited_states']
                          ['triplet']
                          [n_root]
                          ['excitation_energy'])
    rest_eest = (
        rest_egs + data_set[relaxed_excitation_triplet_key]
                           ['excited_states']
                           ['triplet']
                           [n_root]
                           ['excitation_energy']
    )

    return EXCITED_STATE_ENERGIES_COMPARISION.render(
        caption=caption,
        rgs_egs=rgs_egs, ress_egs=ress_egs, rest_egs=rest_egs,
        rgs_eess=rgs_eess, ress_eess=ress_eess,
        rgs_eest=rgs_eest, rest_eest=rest_eest
    )

def excited_state_table(data_set: Dict,
                        caption: Text,
                        data_set_key: Text,
                        max_states: int = None) -> Text:
    heading = EXCITED_STATE_TABLE_HEADING.render(caption=caption)

    multiplicity_sections = []
    for multiplicity in ['singlet', 'triplet', 'unknown']:
        rows = []
        data = data_set[data_set_key]['excited_states'][multiplicity]

        # Enumerate each excited state
        for index, state in enumerate(data):
            if max_states and index >= max_states:
                break

            exci_energy = state['excitation_energy']
            if multiplicity != 'unknown':
                symmetric = state['symmetric_group']
            else:
                # We report the multiplicity together
                symmetric = '{}-{}'.format(state['symmetric_group'],
                                           multiplicity)
            symmetric = state['symmetric_group']
            rows.append(EXCITED_STATE_ROW.render(
                index=index + 1,
                eV=exci_energy * HARTREE_TO_EV,
                nm=NM_TO_HARTREE / exci_energy,
                hartree=exci_energy,
                symmetric_group=symmetric,
                oscillator_strength=state['oscillator_strength']
            ))

            # Add coefficients for contributions from orbitals
            for orbital in state['orbitals']:
                f = orbital['from']
                t = orbital['to']
                op = r'$\rightarrow$' if f < t else r'$\leftarrow$'
                rows.append(EXCITED_STATE_COEFFICIENT_ROW.render(
                    from_=f, direction=op, to=t,
                    coefficient=orbital['coefficient']
                ))

        if not rows:
            continue

        multiplicity_sections.append('\n'.join(rows))
    content = '\\hline'.join(multiplicity_sections)

    tailing = EXCITED_STATE_TABLE_TAILING.render()

    if content:
        return heading + content + tailing
    return ""


def nto_analysis_table(data_set: Dict,
                       caption: Text,
                       data_set_key: Text):
    heading = NTO_ANALYSIS_TABLE_HEADING.render(caption=caption)

    rows = []
    for nto_contribution in data_set[data_set_key]['nto_contributions']:
        rows.append(NTO_ANALYSIS_TABLE_ROW.render(
            from_=nto_contribution['from'],
            to=nto_contribution['to'],
            contribution=nto_contribution['contribution']))
    content = '\n'.join(rows)
    
    tailing = NTO_ANALYSIS_TABLE_TAILING.render()

    if content:
        return heading + content + tailing
    return ""