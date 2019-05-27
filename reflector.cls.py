__author__ = "Etienne Guignard"
__copyright__ = "Copyright 2019, Etienne Guignard"
__credits__ = ["flaticon.com"]
__license__ = "GPL"
__version__ = "1.9.0"
__maintainer__ = "Etienne Guignard"
__email__ = "guignard.etienne@gmail.com"
__status__ = "Dev"

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


class Reflector():
    def __init__(self):

        # Arg length
        self.__ARGV = 3

        # Draw line between radar and reflector
        self.__DRAWLINE = False

        # Remove last kml file generated
        self.__REMOVEFILES = False

        # Google earth file extention
        self.__KML = ".kml"

        # Show paddle name
        self.__PADDLENAME = True

        # Paddle image ref list
        self.__images = ["ylw", "grn", "blu", "red"]

        # Radar position
        self.__GV1LATITUDE = 46.239517
        self.__GV1LONGITUDE = 6.098181 
        self.__GV2LATITUDE = 46.238203
        self.__GV2LONGITUDE = 6.100250

        # Radar name
        self.__GV1 = ["GV1", "GV1S", "GT1S"]
        self.__GV2 = ["GV2", "GV2S", "GT2S"]

        # Angle radar correction
        self.__ROTATION = 90
        self.__ROTATIONFULL = 360
        self.__ROTATIONHALF = 180
    
    def run(self, argv):
        # Check user input arguments
        parser = argparse.ArgumentParser(description='Generating kml file from radar reflector file')
        requiredArg = parser.add_argument_group('required arguments')
        requiredArg.add_argument('-f', '--file', action="store", type=argparse.FileType('r'), help='Reflector file (ex: DAR-CHB.TML)', required=True)
        args = parser.parse_args()

        # Get first arg from command line
        inputFilePath = args.file.name

        # Set up logging to console and file
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%d-%m-%Y %H:%M:%S', filename='reflector.log', filemode='a+')
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
        logger = logging.getLogger('reflector.main')

        # Check arg length
        if len(argv) is self.__ARGV:

            # Check input file
            if self.__check_file(inputFilePath):

                # Remove last kml file generated
                if self.__REMOVEFILES:
                    self.__remove_last_kml_file(inputFilePath)
                
                # Generate kml file
                self.__get_reflector_datas(inputFilePath)
            else:
                logger.error('Reflector file not found')
        else:
            logger.error('Too many arguments')


    # Get reflectors data from file
    def __get_reflector_datas(self, inputFilePath):

        # Define logger
        logger = logging.getLogger(f'{Path(__file__).stem}.{str(self.__get_reflector_datas.__qualname__)}')
        try:

            # Get reflector data
            tml = Tml(inputFilePath)
            radarName = tml.get_radar_name()
            radarChannel = tml.get_radar_channel()
            refDataTable = tml.get_ref_data_table()

            # Check if radar name exist
            if radarName in self.__GV1 or radarName in self.__GV2:

                # Get all reflector data table
                for rdt in refDataTable:

                    # Calc reflector and save it to kml file
                    self.__calc_reflector_data(rdt, inputFilePath, radarChannel, radarName)
            else:
                logger.error("Radar name not valid")
        except TmlError as msg:
            logger.error(f'Unexpected exception occurred: {msg}')
        except Exception as ex:
            logger.error(f'Unexpected exception occurred: {type(ex)} {ex}')


    # Calc all reflector and add pos (latitude, long) into kml file
    def __calc_reflector_data(self, refDataTable, inputFilePath, radarChannel, radarName):

        # Define logger
        logger = logging.getLogger(f'{Path(__file__).stem}.{str(self.__calc_reflector_data.__qualname__)}')
        try:
            
            # Get paddle ref image
            paddleImage, lineColor = self.__get_paddle_image()

            # Check if data table is empty
            if refDataTable.refIndex:

                # Get radar pos (long, lat) from randar name
                longitude, latitude = self.__get_radar_lat_long(radarName)

                # Build output kml file
                p = Path(inputFilePath)
                date = datetime.datetime.now().strftime('%d%m%Y%H%M%S')
                fileName = f'{radarName.lower()}-{p.stem.lower()}'
                outputFilePath = os.path.join(p.parent, f'{fileName}-{refDataTable.refTypeMinus}{date}{self.__KML}')

                # Init kml
                kml = simplekml.Kml()

                # Convert radar deg coordinat (latitude, longitude) into UTM (Universal Transverse Mercator) coordinate [m]
                utm = Proj(f'+proj=somerc +lat_0={latitude} +lon_0={longitude} +ellps=bessel  +units=m +no_defs')
                xUtm, yUtm = utm(longitude, latitude)

                # Check is not empty
                if refDataTable.refIndex and refDataTable.refRange and refDataTable.refStartAz and refDataTable.refEndAz and refDataTable.refOrAz and refDataTable.refHits:

                    # Iter all reflector
                    for (r, sa, ea, oa, h, i) in zip(refDataTable.refRange, refDataTable.refStartAz, refDataTable.refEndAz, refDataTable.refOrAz, refDataTable.refHits, refDataTable.refIndex):

                        # Convert reflector "range" from Nm to m
                        refRangeConv = self.__nm_to_m(float(r))

                        # Convert reflector start azimuth from deg to radian and add angle correction (N to E = 90°)
                        refStartAzConv = float(math.radians(self.__ROTATION - sa))

                        # Convert reflector end azimuth from deg to radian and add angle correction (N to E = 90°)
                        refEndAzConv = float(math.radians(self.__ROTATION - ea))
                    
                        # Convert reflector orientation azimuth from deg to radian and add angle correction (N to E = 90°)
                        ang = (self.__ROTATION - oa) + self.__ROTATIONHALF
                        if ang > self.__ROTATIONFULL:
                            ang = ang - self.__ROTATIONFULL
                        refOrAzConv = float(math.radians(ang))

                        # Converting start azimuth to (x,y) coordinates and add radar position
                        xStartAz = (refRangeConv * float(math.cos(refStartAzConv))) + float(xUtm)
                        yStartAz = (refRangeConv * float(math.sin(refStartAzConv))) + float(yUtm)

                        # Calc dist of the orientation vector
                        distSEAz = (refRangeConv * (math.sin(refEndAzConv - refStartAzConv))) / (math.sin(refOrAzConv - refEndAzConv))

                        # Converting orientation azimuth to (x,y) coordinates and add start position
                        xOrAz = (distSEAz * float(math.cos(refOrAzConv))) + xStartAz
                        yOrAz = (distSEAz * float(math.sin(refOrAzConv))) + yStartAz

                        # Convert UTM (Universal Transverse Mercator) coordinate (start azimuth) into (latitude, longitude)
                        refStartAzLongLat = utm(xStartAz, yStartAz, inverse=True)

                        # Convert UTM (Universal Transverse Mercator) coordinate (orientation azimuth) into (latitude, longitude)
                        refOrAzLongLat = utm(xOrAz, yOrAz, inverse=True)

                        # Ref name (first letter uppercase)
                        refType = refDataTable.refTypeAcronym[0].upper()

                        # Create new reflector point
                        startAzPoint = kml.newpoint(name=f'{refType}{i}-{h}', coords=[refStartAzLongLat], description=f'Type= {refDataTable.refType}\nRadar name= {radarName}\nRadar channel= {radarChannel}\nRange= {r} [Nm] \\ {(refRangeConv / 1000):.3f} [km]\nStart az= {sa} [Deg]\nEnd az=  {ea} [Deg]\nOrient az=  {oa} [Deg]\nHits= {h}')
                        startAzPoint.style.labelstyle.color = simplekml.Color.white
                        startAzPoint.style.labelstyle.scale = 1.2 if self.__PADDLENAME else 0
                        startAzPoint.style.iconstyle.icon.href = paddleImage

                        # Draw line from start azimuth to oriention asimuth
                        orAzLine = kml.newlinestring(name=f'l{refType}{i}', description=f'Orientation azimuth {i}', coords=[refStartAzLongLat, refOrAzLongLat])
                        orAzLine.style.linestyle.color = lineColor
                        orAzLine.style.linestyle.width = 3

                        # Draw line from radar point to reflector point
                        if self.__DRAWLINE:
                            line = kml.newlinestring(name=f'l{refType}{i}', description=f'Line from radar to refelctor {i}', coords=[(longitude, latitude), refStartAzLongLat])
                            line.style.linestyle.color = simplekml.Color.red
                            line.style.linestyle.width = 1
                kml.save(outputFilePath)
                logger.info("KML file generated: " + outputFilePath)
        except ValueError:
            logger.error("Cast value error")
        except Exception as ex:
            logger.error(f'Unexpected exception occurred: {type(ex)} {ex}') 


    # Convert Nm to m
    def __nm_to_m(self, nm):
        return nm * 1.85200 * 1000


    # Check file
    def __check_file(self, inputFilePath):

        # Define logger
        logger = logging.getLogger(f'{Path(__file__).stem}.{str(self.__check_file.__qualname__)}')
        try:

            # Check if file path is string
            if isinstance(inputFilePath, str):

                # Check if file exist
                if os.path.isfile(inputFilePath):
                    return True
            return False
        except FileNotFoundError:
            return False
        except Exception as ex:
            logger.error(f'Unexpected exception occurred: {type(ex)} {ex}')
            return False


    # Get paddle image ref
    def __get_paddle_image(self):
        
        # Define logger
        logger = logging.getLogger(f'{Path(__file__).stem}.{str(self.__get_paddle_image.__qualname__)}')

        # Color simplekml lib
        color = {"red" : simplekml.Color.red, "blu" : simplekml.Color.blue, "grn" : simplekml.Color.green , "ylw" : simplekml.Color.yellow}
        try:
            colorName = self.__images.pop()
            return f'https://maps.google.com/mapfiles/kml/paddle/{colorName}-circle.png', color.get(colorName)
        except IndexError:
            logger.error("paddle image ref error")
            return f'https://maps.google.com/mapfiles/kml/paddle/wht-blank.png', simplekml.Color.white
        except Exception as ex:
            logger.error(f'Unexpected exception occurred: {type(ex)} {ex}')
            return f'https://maps.google.com/mapfiles/kml/paddle/wht-blank.png', simplekml.Color.white


    # Remove last kml file generated
    def __remove_last_kml_file(self, inputFilePath):

        # Define logger
        logger = logging.getLogger(f'{Path(__file__).stem}.{str(self.__remove_last_kml_file.__qualname__)}')
        try:

            # Get all last kml file
            for f in glob.glob(os.path.join(os.path.dirname(inputFilePath), f'*{self.__KML}')):
                os.remove(f)
        except FileNotFoundError:
            logger.error("File to remove not found")
        except Exception as ex:
            logger.error(f'Unexpected exception occurred: {type(ex)} {ex}')


    # Get radar pos (lat, long) from randar name
    def __get_radar_lat_long(self, radarName):
        if radarName in self.__GV1:
            return self.__GV1LONGITUDE, self.__GV1LATITUDE
        else:
            return self.__GV2LONGITUDE, self.__GV2LATITUDE


# Entree main function
if __name__ == "__main__":
    reflector = Reflector()
    reflector.run(sys.argv)