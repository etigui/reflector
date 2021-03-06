__author__ = "Etienne Guignard"
__copyright__ = "Copyright 2019, Etienne Guignard"
__credits__ = ["flaticon.com"]
__license__ = "GPL"
__version__ = "1.5.0"
__maintainer__ = "Etienne Guignard"
__email__ = "guignard.etienne@gmail.com"
__status__ = "Production"

# External import
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
import logging

# Internal import
from tml import Tml, TmlError

# Arg count
ARGS = 5

# Draw line between radar and reflector
DRAWLINE = False

# Remove last kml file generated
REMOVEFILES = False

# No data in tml file
NODATA = "No Reflectors to output"

# Google earth file extention
KML = ".kml"

# Show paddle name
PADDLENAME = True

# Radar position
GV1LATITUDE =  6.098181
GV1LONGITUDE = 46.239517
GV2LATITUDE =  6.10025
GV2LONGITUDE = 46.238203

# Radar name
GV1 = "GV1"
GV2 = "GV2"
RADARNAME = [GV1, GV2]

# Angle radar correction
ROTATION = 90
DELTA = 2.13


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
    
    # Set up logging to console and file
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%d-%m-%Y %H:%M:%S', filename='reflector.log', filemode='a+')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logger = logging.getLogger('reflector.main')

    # Check arg count
    if len(sys.argv) is ARGS:

        # Check radar name
        if radarName in RADARNAME:

            # Latidude and logitude radar pos
            global latitude
            global longitude
            if radarName.startswith(GV1):
                latitude = GV1LATITUDE
                longitude = GV1LONGITUDE
            else:
                latitude = GV2LATITUDE
                longitude = GV2LONGITUDE

            # Check input file
            if check_file(inputFilePath):

                # Remove last kml file generated
                if REMOVEFILES:
                    remove_last_kml_file(inputFilePath)

                # Global paddle image ref list
                global images
                images = ["ltblu", "purple", "pink", "ylw", "grn", "blu", "red"]

                # Generate kml file
                get_reflector_datas(inputFilePath)
            else:
                logger.error('Reflector file not found')
        else:
            logger.error('Radar name not valid')
    else:
        logger.error('Too many arguments')

# Get reflectors data from file
def get_reflector_datas(inputFilePath):

    # Define logger
    logger = logging.getLogger(f'{Path(__file__).stem}.{str(get_reflector_datas.__qualname__)}')
    try:

        # Get reflector data
        tml = Tml(inputFilePath)
        ##radarName = tml.get_radar_name()
        radarChannel = tml.get_radar_channel()
        refDataTable = tml.get_ref_data_table()

        # Get all reflector data table
        for rdt in refDataTable:

            # Calc reflector and save it to kml file
            calc_reflector_data(rdt, inputFilePath, radarChannel)
    except TmlError as msg:
        logger.error(f'Unexpected exception occurred: {msg}')
    except Exception as ex:
        logger.error(f'Unexpected exception occurred: {type(ex)} {ex}')


# Calc all reflector and add pos (latitude, long) into kml file
def calc_reflector_data(refDataTable, inputFilePath, radarChannel):

    # Define logger
    logger = logging.getLogger(f'{Path(__file__).stem}.{str(calc_reflector_data.__qualname__)}')
    try:
        
        # Get paddle ref image
        paddleImage = get_paddle_image()

        # Check if data table is empty
        if refDataTable.refIndex:

            # Build output kml file
            p = Path(inputFilePath)
            date = datetime.datetime.now().strftime('%d%m%Y%H%M%S')
            fileName = f'{radarName.lower()}-{p.stem.lower()}'
            outputFilePath = os.path.join(p.parent, f'{fileName}-{refDataTable.refTypeMinus}{date}{KML}')

            # Init kml
            kml = simplekml.Kml()

            # Angle radar correction
            correction = ROTATION - DELTA

            # Convert radar deg coordinat (latitude, longitude) into UTM (Universal Transverse Mercator) coordinate [m]
            utm = Proj(proj='utm', zone='32U', ellps='WGS84')
            xUtm, yUtm = utm(latitude, longitude)

            # Check is not empty
            if refDataTable.refIndex and refDataTable.refRange and refDataTable.refStartAz and refDataTable.refEndAz and refDataTable.refOrAz and refDataTable.refHits:

                # Iter all reflector
                for (r, sa, ea, oa, h, i) in zip(refDataTable.refRange, refDataTable.refStartAz, refDataTable.refEndAz, refDataTable.refOrAz, refDataTable.refHits, refDataTable.refIndex):

                    # Convert reflector "range" from Nm to m
                    refRangeConv = nm_to_m(float(r))

                    # Convert reflector "deg" to radian and add angle correction
                    refDegConv = float(math.radians((correction - sa)))

                    # Converting degrees to (x,y) coordinates
                    x = (refRangeConv * float(math.cos(refDegConv))) + float(xUtm)
                    y = (refRangeConv * float(math.sin(refDegConv))) + float(yUtm)

                    # Convert UTM (Universal Transverse Mercator) coordinate into (latitude, longitude)
                    refLongLat = utm(x, y, inverse=True)

                    # Create new reflector point
                    pnt = kml.newpoint(name=f'{refDataTable.refTypeAcronym}{i}', coords=[refLongLat], description=f'Type= {refDataTable.refType}\nRadar name= {radarName}\nRadar channel= {radarChannel}\nRange= {r} [Nm] \\ {(refRangeConv / 1000):.3f} [km]\nStart az= {sa} [Deg]\nEnd az=  {ea} [Deg]\nOrient az=  {oa} [Deg]\nHits= {h}')
                    pnt.style.labelstyle.color = simplekml.Color.white
                    pnt.style.labelstyle.scale = 1.2 if PADDLENAME else 0
                    pnt.style.iconstyle.icon.href = paddleImage

                    # draw line from radar point to reflector point
                    if DRAWLINE:
                        line = kml.newlinestring(name=f'l{refDataTable.refTypeAcronym}{i}', description=f'Line from radar to refelctor {i}', coords=[(latitude, longitude), refLongLat])
                        line.style.linestyle.color = simplekml.Color.red
                        line.style.linestyle.width = 1
            kml.save(outputFilePath)
            logger.info("KML file generated: " + outputFilePath)
    except ValueError:
        logger.error("Cast value error")
    except Exception as ex:
        logger.error(f'Unexpected exception occurred: {type(ex)} {ex}') 


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

    # Define logger
    logger = logging.getLogger(f'{Path(__file__).stem}.{str(check_file.__qualname__)}')
    try:

        # Check if file path is string
        if isinstance(inputFilePath, str):

            # Check if file exist
            if os.path.isfile(inputFilePath):
                return True
        return False
    except FileNotFoundError:
        logger.error("file not found")
    except Exception as ex:
        logger.error(f'Unexpected exception occurred: {type(ex)} {ex}') 


# Get paddle image ref
def get_paddle_image():
    
    # Define logger
    logger = logging.getLogger(f'{Path(__file__).stem}.{str(get_paddle_image.__qualname__)}')
    try:
        return f'https://maps.google.com/mapfiles/kml/paddle/{images.pop()}-blank.png'
    except IndexError:
        logger.error("paddle image ref error")
        return f'https://maps.google.com/mapfiles/kml/paddle/wht-blank.png'
    except Exception as ex:
        logger.error(f'Unexpected exception occurred: {type(ex)} {ex}')
        return f'https://maps.google.com/mapfiles/kml/paddle/wht-blank.png'


# Remove last kml file generated
def remove_last_kml_file(inputFilePath):

    # Define logger
    logger = logging.getLogger(f'{Path(__file__).stem}.{str(remove_last_kml_file.__qualname__)}')
    try:

        # Get all last kml file
        for f in glob.glob(os.path.join(os.path.dirname(inputFilePath), f'*{KML}')):
            os.remove(f)
    except FileNotFoundError:
        logger.error("File to remove not found")
    except Exception as ex:
        logger.error(f'Unexpected exception occurred: {type(ex)} {ex}')


# Entree main function
if __name__ == "__main__":
    main()