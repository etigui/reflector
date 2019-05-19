# Reflector
Generating kml file from radar reflector file

                                            START      END      ORIENT     REV
                                INDEX   RANGE   AZIMUTH   AZIMUTH   AZIMUTH     NUM   HITS
                                        Nm       Deg       Deg       Deg
                                00000      0.42     83.15     84.90    313.50  23548  02271
                                00001      0.81     86.90     89.30     45.53  24241  07618
                                00002      0.77     92.20     95.10     45.53  20066  00715
                                00003      0.77     98.60    105.10     44.96  24407  11872
                                00004      0.70    105.40    112.10     45.53  24418  03967
                                00005      0.69    111.80    117.20     45.52  22739  01780

<p align="middle" ><img src="/images/reflector.png" alt="Reflector map" width="600"></p>


## Usage
The exe file "reflector.exe" is located [here](https://github.com/etigui/reflector/raw/rname/output/reflector.exe).

    reflector.py -f <reflector_file>
    [or]
    reflector.exe -f <reflector_file>

## Make py to exe

    pip install pyinstaller
    pyinstaller -y -F -i "radar.ico" "reflector.py"
    [or]
    pip install auto-py-to-exe
    auto-py-to-exe

## Ref

- [lat/lon to utm to lat/lon is extremely flawed, how come?](https://stackoverflow.com/questions/6778288/lat-lon-to-utm-to-lat-lon-is-extremely-flawed-how-come)
- [Transverse universelle de Mercator](https://fr.wikipedia.org/wiki/Transverse_universelle_de_Mercator)
- [Is there a known system of converting degrees to (x,y) coordinates?](https://forums.tigsource.com/index.php?topic=34039.0)
- [Convert from latitude, longitude to x,y](https://stackoverflow.com/questions/16266809/convert-from-latitude-longitude-to-x-y)
- [PGC Coordinate Converter](https://www.pgc.umn.edu/apps/convert/)
- [Simplekml lib](https://simplekml.readthedocs.io/en/latest/)
- [Pyinstaller _datadir error](https://stackoverflow.com/questions/55824830/i-get-error-no-module-named-pyproj-datadir-after-i-made-py-to-exe-with-py)
- [Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
- [Easily change coordinate projection systems in Python with pyproj](http://all-geo.org/volcan01010/2012/11/change-coordinates-with-pyproj/)
- [EPSG:21780](https://spatialreference.org/ref/epsg/21780/)
- [EPSG:21780](https://epsg.io/21780)
- [Coordinate Conversions](https://docs.obspy.org/tutorial/code_snippets/coordinate_conversions.html)
- [Converting projected coordinates to lat/lon using Python](https://gis.stackexchange.com/questions/78838/converting-projected-coordinates-to-lat-lon-using-python)
- [PROJ.4 - General Parameters](http://proj.maptools.org/gen_parms.html)