# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiAuto
    role: mandatory
    command: eeschema_do
    version: 1.5.4
"""
import os
from sys import exit
from .macros import macros, pre_class  # noqa: F401
from .gs import GS
from .optionable import Optionable
from .kiplot import load_sch
from .error import KiPlotConfigurationError
from .misc import ERC_ERROR
from .log import get_logger

logger = get_logger(__name__)


@pre_class
class Run_ERC(BasePreFlight):  # noqa: F821
    """ [boolean=false] Runs the ERC (Electrical Rules Check). To ensure the schematic is electrically correct.
        The report file name is controlled by the global output pattern (%i=erc %x=txt) """
    def __init__(self, name, value):
        super().__init__(name, value)
        if not isinstance(value, bool):
            raise KiPlotConfigurationError('must be boolean')
        self._enabled = value
        self._sch_related = True
        self._expand_id = 'erc'
        self._expand_ext = 'txt'

    def get_targets(self):
        """ Returns a list of targets generated by this preflight """
        load_sch()
        out_pattern = GS.global_output if GS.global_output is not None else GS.def_global_output
        name = Optionable.expand_filename_sch(self, out_pattern)
        out_dir = self.expand_dirname(GS.out_dir)
        if GS.global_dir and GS.global_use_dir_for_preflights:
            out_dir = os.path.join(out_dir, self.expand_dirname(GS.global_dir))
        return [os.path.abspath(os.path.join(out_dir, name))]

    def run(self):
        command = self.ensure_tool('KiAuto')
        # The schematic is loaded only before executing an output related to it.
        # But here we need data from it.
        output = self.get_targets()[0]
        os.makedirs(os.path.dirname(output), exist_ok=True)
        logger.debug('ERC report: '+output)
        cmd = [command, 'run_erc', '-o', output]
        if BasePreFlight.get_option('erc_warnings'):  # noqa: F821
            cmd.append('-w')
        if GS.filter_file:
            cmd.extend(['-f', GS.filter_file])
        cmd.extend([GS.sch_file, self.expand_dirname(GS.out_dir)])
        # If we are in verbose mode enable debug in the child
        cmd = self.add_extra_options(cmd)
        logger.info('- Running the ERC')
        ret = self.exec_with_retry(cmd)
        if ret:
            if ret > 127:
                ret = -(256-ret)
            if ret < 0:
                logger.error('ERC errors: %d', -ret)
            else:
                logger.error('ERC returned %d', ret)
                if GS.sch.annotation_error:
                    logger.error('Make sure your schematic is fully annotated')
            exit(ERC_ERROR)
