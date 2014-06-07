#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fileinput
import sys

in_chars = (128, 146, 147, 148, 149, 150, 151)
out_chars = [x.encode('utf8') for x in list(u'€’“”•–—')]

count = 0

for line in fileinput.input():
    for in_ch, out_ch in zip(in_chars, out_chars):
        line = line.replace('\xc2' + chr(in_ch), out_ch)
    if count == 0:
        line = line.replace('ISO-8859-1', 'UTF-8')
    sys.stdout.write(line)
    count += 1
