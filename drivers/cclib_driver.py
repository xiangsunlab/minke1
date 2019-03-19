#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import logging
import re
import unittest.mock

from typing import Any, Callable, Dict, List, Text

import cclib
import periodictable

CCDATA = cclib.parser.data.ccData
ExtractResult = Dict[Text, Any]
ExtractorFunction = Any    # Callable[[CCDATA, ExtractResult], NoReturn]

logger = logging.getLogger(__name__)

# https://physics.nist.gov/cgi-bin/cuu/Value?threv
# EV_TO_HARTREE = 1.0 / 27.21138602
# cclib is using the value below
EV_TO_HARTREE = 1.0 / 27.21138505
HARTREE_TO_EV = 27.21138602

HARTREE_TO_RECCM = 219474.6313705
RECCM_TO_HARTREE = 1 / HARTREE_TO_RECCM

SQRT_2 = 1.414213562373095

# cclib has some weird behavior, e.g. not extracting de-excitation states in
# Gaussian parser. This dirty patch solves it.
class _PatchedStr(str):
    REGEX = re.compile('(\d+) *(<-|->) *(\d+) +(-?\d+\.\d+)')

    def find(self, seq, start=None, end=None):
        if seq == ' ->':
            rarrow = super().find(' ->', start, end)
            if rarrow != -1:
                return rarrow
            return super().find(' <-', start, end)
        return super().find(seq, start, end)

    def split(self, seq=None, max_split=-1):
        if seq == '->' and '<-' in self:
            m = self.REGEX.search(self)
            g = m.groups()
            _1, _2, _3, _4 = g
            return [_3, '{} {}'.format(_1, _4)]
        return super().split(seq, max_split)

_OriginalWrapper = cclib.parser.logfileparser.FileWrapper

class _PatchedFileWrapper(_OriginalWrapper):

    def next(self):
        return _PatchedStr(super().next())

cclib.parser.logfileparser.FileWrapper = _PatchedFileWrapper


def extractor(dependencies: List[Text] = None,
              provides: List[Text] = None):
    """ Decorator for an extractor in an Extractor class
    """
    def _func_wrapper(func: ExtractorFunction) -> ExtractorFunction:
        """ Wraps an extractor function, provide additional tags
        """
        func.is_extractor = True    # The value is not important through
        func.dependencies = dependencies or []
        func.provides = provides or  []

        @functools.wraps(func)
        def _wrapper(self, parsed: CCDATA, target: Dict) -> None:
            func(self, parsed, target)

        return _wrapper

    return _func_wrapper


def property_extractor(ccdata_property: Text, output_property: Text):
    """ Decorator for an simple extractor in the Extractor class.
    The definition fo a simple extractor is, it extracts data from the ccdata,
    and directly put it into the corresponding key in the extact result.
    """ 
    def _func_wrapper(func: ExtractorFunction) -> ExtractorFunction:
        """ Wraps an dummy function
        """
        func.is_extractor = True
        func.dependencies = []
        func.provides = [output_property]

        @functools.wraps(func)
        def _wrapper(self, parsed: CCDATA, target: Dict) -> None:
            if hasattr(parsed, ccdata_property):
                target[output_property] = getattr(parsed, ccdata_property)
            else:
                target[output_property] = None
        
        return _wrapper

    return _func_wrapper


class ExtractorBase(object):
    """ Base class for all quantum chemistry log extractor
    """

    def __init__(self):
        self._method_list: List[ExtractorFunction] = None

    def _get_all_extractor_methods(self) -> List[ExtractorFunction]:
        unprocessed_methods: List[ExtractorFunction] = []
        for method_name in dir(self):
            method = getattr(self, method_name)
            if hasattr(method, 'is_extractor'):
                unprocessed_methods.append(method)
        logger.info('Class {} has {} extractors: {}'.format(
            self.__class__.__name__, len(unprocessed_methods),
            ', '.join(method.__name__ for method in unprocessed_methods)
        ))
        return unprocessed_methods

    def _construct_method_list(self) -> None:
        """ Find all functions that are marked as extractor, solve the extractor
        dependencies using similar approach to Python MRO
        """
        self._method_list = []
        unprocessed_methods = self._get_all_extractor_methods()

        provides_set = set()
        method_added = [None]
        while method_added:
            method_added.clear()
            for method in unprocessed_methods:
                for dependency in method.dependencies:
                    if dependency not in provides_set:
                        break
                else:
                    method_added.append(method)
                    provides_set.update(method.provides)

            self._method_list.extend(method_added)
            for method in method_added:
                unprocessed_methods.remove(method)

        if unprocessed_methods:
            all_dependencies = set(
                dependency
                for method in self._get_all_extractor_methods()
                for dependency in method.dependencies
            )
            missing_dependencies = all_dependencies - provides_set
            raise RuntimeError('Unfulfilled or circular dependencies: {}'.
                               format(', '.join(missing_dependencies)))

        logger.info('Generated extractor submethods: {}'.format(
            ', '.join(method.__name__
                      for method in (self._method_list or []))
        ))

    def _all_methods(self):
        if not self._method_list:
            self._construct_method_list()
        return self._method_list

    def _is_success(self, parsed: cclib.parser.data.ccData) -> bool:
        if not hasattr(parsed, 'metadata'):
            return False
        return parsed.metadata.get('success', False)

    def extract(self, log_file_name: str) -> dict:
        """ Extract all possible features from a quantum chemistry calculation
        log file.
        """
        parsed = cclib.ccopen(log_file_name).parse()

        if not self._is_success(parsed):
            raise RuntimeError('Calculation in {} is not successful.'.format(
                log_file_name
            ))

        result = {}
        for method in self._all_methods():
            method(parsed, result)

        return result


class GenericExtractor(ExtractorBase):
    """ Extractor that works on most of the quantum chemistry properties
    """
    @property_extractor('charge', 'charge')
    def _extractor_charge(self, parsed: CCDATA, target: Dict) -> None:
        pass
    
    @property_extractor('mult', 'multiplicity')
    def _extractor_multiplicity(self, parsed: CCDATA, target: Dict) -> None:
        pass

    @property_extractor('natom', 'num_atoms')
    def _extractor_num_atoms(self, parsed: CCDATA, target: Dict) -> None:
        pass

    @property_extractor('nbasis', 'num_basis_sets')
    def _extractor_num_basis_sets(self, parsed: CCDATA, target: Dict) -> None:
        pass

    @extractor(provides=['restricted'])
    def _extractor_restricted(self, parsed: CCDATA, target: Dict) -> None:
        if not hasattr(parsed, 'moenergies'):
            target['restricted'] = None
        else:
            num_sets_of_mos = len(parsed.moenergies)
            if num_sets_of_mos == 1:
                target['restricted'] = True
            else:
                target['restricted'] = False

    @extractor(dependencies=['restricted'], provides=['mos'])
    def _extractor_mos(self, parsed: CCDATA, target: Dict) -> None:
        """ Extracts MOs
        """
        target['mos'] = {}
        mos = target['mos']
        mos['num_mos'] = (getattr(parsed, 'nmo') 
                          if hasattr(parsed, 'nmo') else None)

        mo_operations = [
            # MO energies are in eV, we translate it to Hartree
            ('energies', 'moenergies', lambda v: v * EV_TO_HARTREE),
            ('symmetric_group', 'mosyms', lambda v: v)
        ]
        
        for base_key, prop, transform in mo_operations:
            task = []
            if hasattr(parsed, prop):
                if target['restricted']:
                    task = [(base_key, getattr(parsed, prop)[0])]
                else:
                    task = [('alpha_{}'.format(base_key),
                             getattr(parsed, prop)[0]),
                            ('beta_{}'.format(base_key),
                             getattr(parsed, prop)[1])]

            for key, data in task:
                mos[key] = [
                    transform(item)    
                    for item in data
                ]

    @extractor(provides=['num_electrons'])
    def _extractor_num_electrons(self, parsed: CCDATA, target: Dict) -> None:
        target['num_electrons'] = None
        if hasattr(parsed, 'nelectrons'):
            target['num_electrons'] = parsed.nelectrons
    
    @extractor(provides=['atom_symbols', 'atom_numbers'])
    def _extract_atom_data(self, parsed: CCDATA, target: Dict) -> None:
        target['atoms'] = {}
        atoms =target['atoms']
        atoms['numbers'] = None
        atoms['symbols'] = None
        if not hasattr(parsed, 'atomnos'):
            return

        atoms['numbers'] = parsed.atomnos.tolist()
        atoms['symbols'] = [
            periodictable.elements[i].symbol
            for i in atoms['numbers']
        ]

    @extractor(dependencies=['atom_symbols'],
               provides=['optimization', 'atom_coordinates'])
    def _extractor_optimizations(self, parsed: CCDATA, target: Dict) -> None:
        if not hasattr(parsed, 'optstatus'):
            target['optimization_steps'] = 0
            target['atoms']['coordinates'] = [
                atom_coord.tolist()
                for atom_coord in parsed.atomcoords[-1]
            ]
        else:
            target['optimization_steps'] = len(parsed.optstatus)
            # We pick up the last converged structure
            target['atoms']['coordinates'] = [
                atom_coord.tolist()
                for atom_coord in parsed.converged_geometries[-1]
            ]

    @extractor(provides=['scf_energy'])
    def _extractor_scf_energy(self, parsed: CCDATA, target: Dict) -> None:
        """ Extracts SCF energy
        """
        target['scf_energy'] = None
        if hasattr(parsed, 'scfenergies'):
            # We always assume the last energy is the final energy
            target['scf_energy'] = parsed.scfenergies[-1] * EV_TO_HARTREE

    def _extractor_mp_energy(self, parsed: CCDATA, target: Dict) -> None:
        """ Extracts MPx energies
        """
        target['mp2'] = target['mp3'] = target['mp4'] = target['mp5'] = None
        if not hasattr(parsed, 'mpenergies'):
            # We always assume the last set of energies are the final energies
            return
        # FIXME complete the MP2 part

    def _extractor_cc_energy(self, parsed: CCDATA, target: Dict) -> None:
        """ Extracts Couple-cluster energies
        """
        # FIXME complete CC part

    @extractor(dependencies=['scf_energy', 'restricted', 'optimization'])
    def _extractor_excited_states(self, parsed: CCDATA, target: Dict) -> None:
        """ Extract excited states
        """
        # We have singlet/triplets while there could be doublet or other
        # possibilities
        target['excited_states'] = {
            'singlet': [],
            'triplet': [],
            'unknown': []
        }
    
        excited_states = target['excited_states']

        if not hasattr(parsed, 'etenergies'):
            # No excited state calculation
            return

        # In an optimization calculation, all excited state energies are stored
        # in the same list. We need to exract the excited state energy for the
        # final state -- which is expected to be the last part
        num_optimization_steps = target['optimization_steps']
        if num_optimization_steps:
            num_excited_states = int(len(parsed.etenergies) /
                                    num_optimization_steps)

            excited_state_start_index = ((num_optimization_steps - 1) * 
                                         num_excited_states)
        else:
            num_excited_states = len(parsed.etenergies)
            excited_state_start_index = 0

        excited_state_end_index = (excited_state_start_index +
                                   num_excited_states)

        for index in range(excited_state_start_index, excited_state_end_index):
            sym = parsed.etsyms[index]
            multiplicity, sym_group = sym.split('-')
            multiplicity = multiplicity.lower()

            oscillator_strength = parsed.etoscs[index]
            excitation_energy = parsed.etenergies[index] * RECCM_TO_HARTREE

            orbitals_raw = parsed.etsecs[index]
            orbitals = []
            if target['restricted']:
                for item in orbitals_raw:
                    orbitals.append({
                        'from': item[0][0] + 1,
                        'to': item[1][0] + 1,
                        # cclib authors normalize the values by default, we
                        # need to normalize it back...
                        'coefficient': item[2] / SQRT_2
                    })
            else:
                for item in orbitals_raw:
                    orbitals.append({
                        'from': '{}{}'.format(item[0][0] + 1,
                                              ['A', 'B'][item[0][1]]),
                        'to': '{}{}'.format(item[1][0] + 1,
                                            ['A', 'B'][item[1][1]]),
                        'coefficient': item[2]
                    })

            state_list = (excited_states[multiplicity]
                          if multiplicity in excited_states
                          else excited_states['unknown'])
            state_list.append({
                'multiplicity': multiplicity,
                'symmetric_group': sym_group,
                'oscillator_strength': oscillator_strength,
                'excitation_energy': excitation_energy,
                'orbitals': orbitals,
            })

    @extractor(dependencies=['multiplicity', 'num_electrons'],
               provides=['homo_index', 'lumo_index', 'unpaired_electrons'])
    def extract_homo_index(self, parsed: CCDATA, target: Dict) -> None:
        target['unpaired_electrons'] = (target['multiplicity'] - 1) / 2
        target['homo_index'] = (
            (target['num_electrons'] - target['unpaired_electrons']) / 2 +
            target['unpaired_electrons']
        )
        target['lumo_index'] = target['homo_index'] + 1


class NTOExtractor(ExtractorBase):

    # We collect NTO orbtitals that contributes more than 1% of the excited state
    NTO_CRITERIA = 0.01

    @extractor(provides=['nto_contributions'])
    def _extract_nto_coefficients(self, parsed: CCDATA, target: Dict) -> None:
        target['nto_contributions'] = None

        if not hasattr(parsed, 'moenergies'):
            return

        homo = parsed.homos[0]

        # Yes, cclib is converting the unit of energies, making things harder
        result = []
        orbit_number = homo
        exci_orbit = homo + 1
        contribution = parsed.moenergies[0][orbit_number] * EV_TO_HARTREE
        while contribution > self.NTO_CRITERIA:
            result.append({
                # Orbit number starts with 0
                'from': orbit_number + 1,
                'to': exci_orbit + 1,
                'contribution': contribution 
            })
            orbit_number -= 1
            exci_orbit += 1
            contribution = parsed.moenergies[0][orbit_number] * EV_TO_HARTREE

        target['nto_contributions'] = result


if __name__ == '__main__':
    import sys
    import pprint
    logging.basicConfig(level=logging.DEBUG)
    pprint.pprint(NTOExtractor().extract(sys.argv[1]))
