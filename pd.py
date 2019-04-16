##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Ben Dooks <ben.dooks@codethink.co.uk>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd

class Decoder(srd.Decoder):
    api_version = 3
    id = 'TDM'
    name = 'TDM'
    longname = 'TDM Audio'
    desc = 'TDM multi-channel audio'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['tdm']
    channels = (
        { 'id': 'clock', 'name': 'bitclk', 'desc': 'Data bit clock' },
        { 'id': 'frame', 'name': 'framesync', 'desc': 'Frame sync' },
        { 'id': 'data', 'name': 'data', 'desc': 'Serial data' },
     )
    optional_channels = ()
    options = (
        {'id': 'bps', 'desc': 'Bits per sample', 'default':16 }, 
        {'id': 'edge', 'desc': 'Clock edge to sample on', 'default':'r', 'values': ('r', 'f') }
    )
    annotations = (
        ('ch0', 'Data channel 0'),
        ('ch1', 'Data channel 1'),
        ('ch2', 'Data channel 2'),
        ('ch3', 'Data channel 3'),
        ('ch4', 'Data channel 4'),
        ('ch5', 'Data channel 5'),
        ('ch6', 'Data channel 6'),
        ('ch7', 'Data channel 7'),
        ('data', 'Data'),
        ('warning', 'Warning'),
    )

    def __init__(self, **kwargs):
        # initialsation here
        self.samplerate = None
        self.channels = 2
        self.channel = 0
        self.bitdepth = 16
        self.bitcount = 0
        self.samplecount = 0
        self.lastsync = 0
        self.lastframe = 0
        self.data = 0
        self.ss_block = None

    def metdatadata(self, key, value):
        if key == srd.SRC_CONF_SAMPLERATE:
            self.samplerate = value

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.bitdepth = self.options['bps']
        self.edge = self.options['edge']

    def decode(self):
       while True:
           # wait for edge of clock (sample on rising/falling edge)
           clock, frame, data =  self.wait({0: self.edge})

           # check for new frame
           # note, frame may be a single clock, or active for the first
           # sample in the frame
           if frame != self.lastframe and frame == 1:
               self.channel = 0
               self.bitcount = 0
               self.data = 0
               if self.ss_block is None:
                   self.ss_block = 0

           self.data = (self.data << 1) | data
           self.bitcount += 1

           if self.ss_block is not None:
               if self.bitcount >= self.bitdepth:
                   self.bitcount = 0
                   self.channel += 1

                   c1 = 'Channel %d' % self.channel
                   c2 = 'C%d' % self.channel
                   c3 = '%d' % self.channel
                   if self.bitdepth <= 8:
                       v = '%02x' % self.data
                   elif self.bitdepth <= 16:
                       v = '%04x' % self.data
                   else:
                       v = '%08x' % self.data

                   self.put(self.ss_block, self.samplenum, self.out_ann,
                            [self.channel, ['%s: %s' % (c1, v),
                                 '%s: %s' % (c2, v),
                                 '%s: %s' % (c3, v) ]])
                   self.data = 0
                   self.ss_block = self.samplenum
                   self.samplecount += 1


           self.lastframe = frame
