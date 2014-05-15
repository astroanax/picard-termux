# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2014 Laurent Monin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import StringIO
import struct


class ImageInfoError(Exception):
    pass


class ImageInfoUnrecognized(Exception):
    pass


def image_info(data):
    """Parse data for jpg, gif, png metadata
    If successfully recognized, it returns a tuple with:
        - width
        - height
        - mimetype
        - extension
        - data length
    If there is not enough data (< 16 bytes), it will raise `ImageInfoError`.
    If format isn't recognized, it will raise `ImageInfoUnrecognized`
    """

    datalen = len(data)
    if datalen < 16:
        raise ImageInfoError('Not enough data')

    w = -1
    h = -1
    mime = ''
    extension = ''

    # http://en.wikipedia.org/wiki/Graphics_Interchange_Format
    if data[:6] in ('GIF87a', 'GIF89a'):
        w, h = struct.unpack('<HH', data[6:10])
        mime = 'image/gif'
        extension = '.gif'

    # http://en.wikipedia.org/wiki/Portable_Network_Graphics
    # http://www.w3.org/TR/PNG/#11IHDR
    elif data[:8] == '\x89PNG\x0D\x0A\x1A\x0A' and data[12:16] == 'IHDR':
        w, h = struct.unpack('>LL', data[16:24])
        mime = 'image/png'
        extension = '.png'

    # http://en.wikipedia.org/wiki/JPEG
    elif data[:2] == '\xFF\xD8':  # Start Of Image (SOI) marker
        jpeg = StringIO.StringIO(data)
        # skip SOI
        jpeg.read(2)
        b = jpeg.read(1)
        try:
            while (b and ord(b) != 0xDA):  # Start Of Scan (SOS)
                while (ord(b) != 0xFF): b = jpeg.read(1)
                while (ord(b) == 0xFF): b = jpeg.read(1)
                if ord(b) in (0xC0, 0xC1, 0xC2, 0xC5, 0xC6, 0xC7,
                              0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    jpeg.read(2)  # parameter length (2 bytes)
                    jpeg.read(1)  # data precision (1 byte)
                    h, w = struct.unpack('>HH', jpeg.read(4))
                    mime = 'image/jpeg'
                    extension = '.jpg'
                    break
                else:
                    # read 2 bytes as integer
                    length = int(struct.unpack('>H', jpeg.read(2))[0])
                    # skip data
                    jpeg.read(length - 2)
                b = jpeg.read(1)
        except struct.error:
            pass
        except ValueError:
            pass

    else:
        raise ImageInfoUnrecognized('Unrecognized image data')
    assert(w != -1)
    assert(h != -1)
    assert(mime != '')
    assert(extension != '')
    return (int(w), int(h), mime, extension, datalen)
