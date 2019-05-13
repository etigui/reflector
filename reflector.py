__author__ = "Etienne Guignard"
__copyright__ = "Copyright 2007, The Cogent Project"
__credits__ = ["flaticon.com"]
__license__ = "GPL"
__version__ = "1.1.2"
__maintainer__ = "Etienne Guignard"
__email__ = "guignard.etienne@gmail.com"
__status__ = "Production"

import sys
import os
import math
import random
import simplekml
from pyproj import _datadir, datadir, Proj
from operator import itemgetter
from pathlib import Path
import datetime
import re
import glob
import itertools
import argparse

# Arg count
ARGS = 5

# Draw line between radar and reflector
DRAWLINE = False

# Remove last kml file generated
REMOVEFILES = True

# No data in tml file
NODATA = "No Reflectors to output"

# Google earth file extention
KML = ".kml"

# Show paddle name
PADDLENAME = True

# Radar position
GV1LATITUDE = 6.098199
GV1LONGITUDE = 46.2395083
GV2LATITUDE =  6.099153
GV2LONGITUDE = 46.238859

def main():

    # Check user input arguments
    parser = argparse.ArgumentParser(description='Generating kml file from radar reflector file')
    requiredArg = parser.add_argument_group('required arguments')
    requiredArg.add_argument('-r', '--radar', action="store", type=str, help='Radar name (ex: GV1)', required=True, default='GV1', dest="rad")
    requiredArg.add_argument('-f', '--file', action="store", type=argparse.FileType('r'), help='Reflector file (ex: DAR-CHB.TML)', required=True)
    args = parser.parse_args()

    # Get first and second arg from command line
    global radarName
    inputFilePath = args.file.name
    radarName = args.rad

    # Ccheck arg count
    if len(sys.argv) is ARGS:

        # Check radar name
        if radarName in ["GV1", "GV2"]:

            # Latidude and logitude radar pos
            global latitude
            global longitude
            if radarName is "GV1":
                latitude = GV1LATITUDE
                longitude = GV1LONGITUDE
            else:
                latitude = GV2LATITUDE
                longitude = GV2LONGITUDE

            # Check input file
            if check_file(inputFilePath):

                # Remove last kml file generated
                if REMOVEFILES:
                    remove_last_kml_file()

                # Global paddle image ref list
                global images
                images = ["ltblu", "purple", "pink", "ylw", "grn", "blu", "red"]

                # Generate kml file
                get_reflector_datas(inputFilePath)
            else:
                print("Reflector file not found")
        else:
            print("Radar name not valid")
    else:
        print("Too many arguments")



# Get reflectors data from file
def get_reflector_datas(inputFilePath):
    try:
        # Read reflector file
        with open(inputFilePath) as f:

            # Split elements with " " and add each value in the list
            content = [" ".join(l.split()) for l in f.readlines()]

        # Check if reflector file
        if(content.pop(0).startswith("_DAR")):

            # Remove empty list item
            content = list(filter(None, content))

            # Clean up unwanted item
            content = [l for l in content if l not in ("START END ORIENT REV", "INDEX RANGE AZIMUTH AZIMUTH AZIMUTH NUM HITS", "Nm Deg Deg Deg")]

            # Search for start
            cdrIndex = int([i for i, j in zip(itertools.count(), content) if j.startswith('CURRENT DYNAMIC REFLECTORS')].pop())
            ncdrIndex = int([i for i, j in zip(itertools.count(), content) if j.startswith('NON-CURRENT DYNAMIC REFLECTORS')].pop())

            # Build output kml file
            p = Path(inputFilePath)
            date = datetime.datetime.now().strftime('%d%m%Y%H%M%S')
            fileName = f'{radarName.lower()}-{p.stem.lower()}'

            # Calc and slice reflector table with output kml file
            shift = 1
            calc_reflect_data(check_no_data(content[shift:cdrIndex]), os.path.join(p.parent, f'{fileName}-fixed-{date}{KML}'), "fr", "Fixed")
            calc_reflect_data(check_no_data(content[cdrIndex + shift:ncdrIndex]), os.path.join(p.parent, f'{fileName}-current-dynamic-{date}{KML}'), "cdf", "Current dynamic")
            calc_reflect_data(check_no_data(content[ncdrIndex + shift:len(content)]), os.path.join(p.parent, f'{fileName}-non-current-dynamic-{date}{KML}'), "ncdf", "Non-current dynamic")
        else:
            print("Reflector file struct not valid")
    except IndexError:
        print("Reflector file not valid")
    except ValueError:
        print("Cast value error")
    except FileNotFoundError:
        print("Reflector file not found")


# Calc all reflector and add pos (latitude, long) into kml file
def calc_reflect_data(data, outputFilePath, reflectionTypeName, reflectionTypeFullName):
    try:

        # Check if data are ot empty
        if data:

                # Split elements with " "
                data = [l.strip().split(" ") for l in data]

                # Map each element and cast into adequate type
                refIndex = [int(e) for e in list(map(itemgetter(0), data))]
                refRange = [float(e) for e in list(map(itemgetter(1), data))]
                refDeg = [float(e) for e in list(map(itemgetter(2), data))]

                # Init kml
                kml = simplekml.Kml()

                # Angle correction
                rotation = 90
                delta = 2.13
                correction = rotation - delta

                # Convert radar deg coordinat (latitude, longitude) into UTM (Universal Transverse Mercator) coordinate [m]
                utm = Proj(proj='utm', zone='32U', ellps='WGS84')
                xUtm, yUtm = utm(latitude, longitude)

                # Check is list has the same length
                if refIndex and refRange and refDeg:
                    
                    # Get paddle ref image
                    paddleImage = get_paddle_image()

                    # Iter all reflector
                    for (r, d, i) in zip(refRange, refDeg, refIndex):
                        
                        # Convert reflector "range" from Nm to m
                        refRangeConv = nm_to_m(float(r))

                        # Convert reflector "deg" to radian and add angle correction
                        refDegConv = float(math.radians((correction - d)))

                        # Converting degrees to (x,y) coordinates
                        x = (refRangeConv * float(math.cos(refDegConv))) + float(xUtm)
                        y = (refRangeConv * float(math.sin(refDegConv))) + float(yUtm)

                        # Convert UTM (Universal Transverse Mercator) coordinate into (latitude, longitude)
                        refLongLat = utm(x, y, inverse=True)

                        # Create new reflector point
                        pnt = kml.newpoint(name=f'{reflectionTypeName}{i}', coords=[refLongLat], description=f'Ref type={reflectionTypeFullName}\nRadar name={radarName}\nRange={r} [Nm] \\ {(refRangeConv / 1000):.3f} [km]\nDeg={d} [Deg]')
                        pnt.style.labelstyle.color = simplekml.Color.white
                        pnt.style.labelstyle.scale = 1.2 if PADDLENAME else 0
                        pnt.style.iconstyle.icon.href = paddleImage

                        # draw line from radar point to reflector point
                        if DRAWLINE:
                            line = kml.newlinestring(name=f'l{reflectionTypeName}{i}', description=f'Line from radar to refelctor {i}', coords=[(latitude, longitude), refLongLat])
                            line.style.linestyle.color = simplekml.Color.red
                            line.style.linestyle.width = 1
                kml.save(outputFilePath)
                print("KML file generated: " + outputFilePath)
    except ValueError:
        print("Cast value error")

# Convert Nm to m
def nm_to_m(nm):
    return nm * 1.85200 * 1000


# Check if not data in the tml table file
def check_no_data(data):
    if data:
        if data[0].startswith(NODATA):
            return []
    return data


# Check file
def check_file(inputFilePath):
    try:

        # Check if file path is string
        if isinstance(inputFilePath, str):

            # Check if file exist
            if os.path.isfile(inputFilePath):
                return True
        return False
    except FileNotFoundError:
        print("File not found")


# Get paddle image ref
def get_paddle_image():
    try:
        return f'https://maps.google.com/mapfiles/kml/paddle/{images.pop()}-blank.png'
    except IndexError:
        print("paddle image error")
        return f'https://maps.google.com/mapfiles/kml/paddle/wht-blank.png'


# Remove last kml file generated
def remove_last_kml_file():
    try:

        # Get all last kml file
        for f in glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)), f'*{KML}')):
            os.remove(f)
    except FileNotFoundError:
        print("File to remove not found")



# Entree main function
if __name__ == "__main__":
    main()