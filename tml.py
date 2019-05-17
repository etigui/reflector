__author__ = "Etienne Guignard"
__copyright__ = "Copyright 2019, Etienne Guignard"
__credits__ = ["flaticon.com"]
__license__ = "GPL"
__version__ = "1.6.0"
__maintainer__ = "Etienne Guignard"
__email__ = "guignard.etienne@gmail.com"
__status__ = "Production"

import os
import itertools
from operator import itemgetter


# Class to store data table
class DataTable():
    def __init__(self, refType, refTypeAcronym, refTypeMinus, refIndex, refRange, refStartAz, refEndAz, refOrAz, refRevNum, refHits):
        self.refType = refType
        self.refTypeAcronym = refTypeAcronym
        self.refTypeMinus = refTypeMinus
        self.refIndex = refIndex
        self.refRange = refRange
        self.refStartAz = refStartAz
        self.refEndAz = refEndAz
        self.refOrAz = refOrAz
        self.refRevNum = refRevNum
        self.refHits = refHits


# Class exception to handle class TML error
class TmlError(Exception):
    """Generic exception for Tml class"""
    def __init__(self, msg, original_exception=""):
        super(TmlError, self).__init__(f'<Tml class> {msg} {": " + original_exception if original_exception else ""}')
        self.original_exception = original_exception


# Class to process tml file
class Tml():
    def __init__(self, fileName):

        # Private class const
        self.__RADARCHANNEL = 2
        self.__RADARNAME = 4
        self.__FR = "FIXED REFLECTORS"
        self.__CDR = "CURRENT DYNAMIC REFLECTORS"
        self.__NCDR = "NON-CURRENT DYNAMIC REFLECTORS"
        self.__NODATA = "No Reflectors to output"
        self.__SHIFT = 1
        self.__SPLIT = " "
        self.__STARTFILE = "_DAR"
        
        # Private class var
        self.__fileName = fileName
        self.__data = None
        self.__channelName = None
        self.__radarName = None
        self.__dataTable = []

        # Process tml data file
        self.__process_data()

    # Get radar name
    def get_radar_name(self):
        return self.__radarName


    # Get radar channel
    def get_radar_channel(self):
        return self.__channelName


    # Get all data table
    def get_ref_data_table(self):
        return self.__dataTable


    # Process tml data file
    def __process_data(self):

        # Get tml file lines
        self.__data = self.__read_file()
        if self.__data:

            # Clean up lines 
            self.__data = self.__clean_up()

            # Check if reflector file
            if(self.__data.pop(0).startswith(self.__STARTFILE)):
                self.__process_radar_info()
                self.__process_data_table()
            else:
                raise TmlError("Tml file not valid")
        else:
            raise TmlError("Tml file not found or not valid")


    # Process radar info (name, channel)
    def __process_radar_info(self):
        try:
            radarInfos = [r.split(self.__SPLIT)[self.__RADARCHANNEL:self.__RADARNAME] for r in self.__data if r.startswith(self.__FR)].pop()
            self.__channelName = radarInfos.pop()
            self.__radarName = radarInfos.pop()
        except Exception as ex:
            raise TmlError("Process radar info function error", str(ex))

    
    # Process each data table (fr, cdr, ncdr)
    def __process_data_table(self):
        try:

            # Search for start in each table
            cdrIndex = int([i for i, j in zip(itertools.count(), self.__data) if j.startswith(self.__CDR)].pop())
            ncdrIndex = int([i for i, j in zip(itertools.count(), self.__data) if j.startswith(self.__NCDR)].pop())

            # Calc and slice reflector data table
            self.__dataTable.append(self.__process_reflector_data(self.__check_no_data(self.__data[self.__SHIFT:cdrIndex]), self.__FR))
            self.__dataTable.append(self.__process_reflector_data(self.__check_no_data(self.__data[cdrIndex + self.__SHIFT:ncdrIndex]), self.__CDR))
            self.__dataTable.append(self.__process_reflector_data(self.__check_no_data(self.__data[ncdrIndex + self.__SHIFT:len(self.__data)]), self.__NCDR))
        except Exception as ex:
            raise TmlError("Process data table function error", str(ex))


    # Process all reflector data
    def __process_reflector_data(self, tableData, refType):
        try:
            if tableData:
                
                # Split elements with " "
                data = [l.strip().split(" ") for l in tableData]

                # Map each element and cast into adequate type
                refIndex = [int(e) for e in list(map(itemgetter(0), data))]
                refRange = [float(e) for e in list(map(itemgetter(1), data))]
                refStartAz = [float(e) for e in list(map(itemgetter(2), data))]
                refEndAz = [float(e) for e in list(map(itemgetter(3), data))]
                refOrAz = [float(e) for e in list(map(itemgetter(4), data))]
                refRevNum = [int(e) for e in list(map(itemgetter(5), data))]
                refHits = [int(e) for e in list(map(itemgetter(6), data))]
                return DataTable(self.__get_reflector_type(refType), self.__get_refpector_type_acronym(refType), self.__get_reflector_type_minus(refType), refIndex, refRange, refStartAz, refEndAz, refOrAz, refRevNum, refHits)
            else:
                return DataTable("", "", "", [], [], [], [], [], [], [])
        except Exception as ex:
            raise TmlError("Process reflector data function error", str(ex))


    # Clean up file
    def __clean_up(self):
        try:

            # Remove empty list item
            self.__data = list(filter(None, self.__data))

            # Clean up unwanted item
            return [l for l in self.__data if l not in ("START END ORIENT REV", "INDEX RANGE AZIMUTH AZIMUTH AZIMUTH NUM HITS", "Nm Deg Deg Deg")]
        except Exception as ex:
            raise TmlError("Clean up function error", str(ex))


    # Read tml file
    def __read_file(self):
        try:

            # Check if tml file exist
            if self.__check_file():

                # Read reflector file
                with open(self.__fileName) as f:

                    # Split elements with " " and add each value in the list
                    return [" ".join(l.split()) for l in f.readlines()]
            else:
                return None
        except Exception as ex:
            raise TmlError("Read file function error", str(ex))


    # Check file
    def __check_file(self):
        try:

            # Check if file path is string
            if isinstance(self.__fileName, str):

                # Check if file exist
                if os.path.isfile(self.__fileName):
                    return True
            return False
        except FileNotFoundError:
            return False
        except Exception:
            return False


    # Check if not data in the tml table file
    def __check_no_data(self, data):
        try:

            # Check if data in table
            if data:
                if data[0].startswith(self.__NODATA):
                    return []
                else:
                    return data
            return []
        except Exception:
            return []


    # Get reflector type  like (Non-current dynamic reflectors)
    def __get_reflector_type(self, name):
        return name.lower().replace('reflectors','')


    # Get reflector type like (ndr)
    def __get_refpector_type_acronym(self, name):
        return ''.join([s[0].lower() for s in name.split()])


    # Get reflector type like (non-current-dynamic-reflectors)
    def __get_reflector_type_minus(self, name):
        return '-'.join(self.__get_reflector_type(name).replace('-',' ').split(" "))
