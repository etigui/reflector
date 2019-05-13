# Reflector
Generating kml file from radar reflector file

<p align="middle" ><img src="/images/reflector.png" alt="Reflector map" width="600"></p>


## Usage
The exe file "reflector.exe" is located [here](/output/reflector.exe).

    reflector.py -r <radar_name> -f <reflector_file>
    [or]
    reflector.exe -r <radar_name> -f <reflector_file>

## Make py to exe

    pip install pyinstaller
    pyinstaller -y -F -i "radar.ico" "reflector.py"
    [or]
    pip install auto-py-to-exe
    auto-py-to-exe

## Ref

[lat/lon to utm to lat/lon is extremely flawed, how come?](https://stackoverflow.com/questions/6778288/lat-lon-to-utm-to-lat-lon-is-extremely-flawed-how-come)
[Transverse universelle de Mercator](https://fr.wikipedia.org/wiki/Transverse_universelle_de_Mercator)
[Is there a known system of converting degrees to (x,y) coordinates?](https://forums.tigsource.com/index.php?topic=34039.0)
[Convert from latitude, longitude to x,y](https://stackoverflow.com/questions/16266809/convert-from-latitude-longitude-to-x-y)
[PGC Coordinate Converter](https://www.pgc.umn.edu/apps/convert/)
[simplekml lib](https://simplekml.readthedocs.io/en/latest/)
[Pyinstaller _datadir error](https://stackoverflow.com/questions/55824830/i-get-error-no-module-named-pyproj-datadir-after-i-made-py-to-exe-with-py)