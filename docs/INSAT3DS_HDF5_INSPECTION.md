# INSAT-3DS HDF5 Inspection Report
**Inspection Date**: 2026-09-28T18:36:32.173298+00:00
**Source Directory**: C:\Users\Vedant\Documents\mosdac

## 1. File Summary
| Filename | Status | Size (MB) | SHA-256 |
|---|---|---|---|
| 3SIMG_29MAY2025_1200_L1B_STD_V01R00.h5 | OK | 410.85 | `62272d7ef4c97811ed474a31f751cfd2eb7e2073caf996446c8aa3e90e202d6b` |
| 3SIMG_29MAY2025_1230_L1B_STD_V01R00.h5 | OK | 406.20 | `3ff2f27d12f4fa63f8a5d32ce719e1e1fa3f59a21233d57bdf1223f216eb49f1` |
| 3SIMG_29MAY2025_1300_L1B_STD_V01R00.h5 | OK | 401.84 | `cc752f305a178f62f3bd9980c48799c46e55c762b3d3a4a5c2446bd0e22603b8` |
| 3SIMG_29MAY2025_1330_L1B_STD_V01R00.h5 | OK | 398.11 | `5a709d0d72c6551a41d33104f7c6a05b105f8c95bea37414a39b62c245ee8362` |
| 3SIMG_29MAY2025_1400_L1B_STD_V01R00.h5 | OK | 394.80 | `07bc0af00e7dbab82a9ba6733718f968e1b811679176a5d83b3ba355560b906b` |
| 3SIMG_29MAY2025_1430_L1B_STD_V01R00.h5 | OK | 391.99 | `df9bf2dd703b65578c5283372530bc928bc52c8ca28502620a6ad04227f1b3bf` |
| 3SIMG_29MAY2025_1200_L2B_CTP_V01R00.h5 | OK | 2.15 | `0a5377294068db8dec270762c539e1c6b7c7e29bec2694faf71ccf449e44508e` |
| 3SIMG_29MAY2025_1230_L2B_CTP_V01R00.h5 | OK | 2.18 | `da69d04600b26a3cf7939a2fb09611c62aadd01e8d49fa513b35a3e243687b1d` |
| 3SIMG_29MAY2025_1300_L2B_CTP_V01R00.h5 | OK | 2.13 | `3f6030a99a5f1c6854ee166c45bde7fc7006920982a2e5cd4499d9c2a577073a` |
| 3SIMG_29MAY2025_1330_L2B_CTP_V01R00.h5 | OK | 2.22 | `87a24110b63d44eec31a869304218c242d3511ee2d0508186afac473d55882c4` |
| 3SIMG_29MAY2025_1400_L2B_CTP_V01R00.h5 | OK | 2.01 | `18cad00419e4def5fc89f165afd283a18c220cd4e2dd3cfd0be4fd9e32174513` |
| 3SIMG_29MAY2025_1430_L2B_CTP_V01R00.h5 | OK | 2.15 | `a34178debd1c9aaaf71d27181fd1851cbff98dc28d1b209b14c81b34f65d4f61` |

## 2. Duplicate Analysis
No duplicate file analyzed.

## 3. L1B Structure & Channel Inventory
**Representative File**: 3SIMG_29MAY2025_1200_L1B_STD_V01R00.h5
### Root Attributes
```json
{
  "Acquisition_Date": "29MAY2025",
  "Acquisition_End_Time": "29-MAY-2025T12:27:09.268",
  "Acquisition_Start_Time": "29-MAY-2025T12:00:15.568",
  "Acquisition_Time_in_GMT": "1200",
  "Attitude_Source": "SSF",
  "Datum": "WGS84",
  "Ellipsoid": "WGS84",
  "FastScan_Linearity_Enabled": "no",
  "Field_of_View(degrees)": [
    8.54839755851374e+87
  ],
  "Ground_Station": "BES,SAC/ISRO,Ahmedabad,INDIA.",
  "HDF_Product_File_Name": "3SIMG_29MAY2025_1200_L1B_STD_V01R00.h5",
  "Imaging_Mode": "FULL FRAME",
  "MCD_FS_Enabled": "no",
  "MCD_SS_Enabled": "yes",
  "MIR_Acquisition_Mode": "MAIN",
  "MIR_Gain_Mode": [
    3
  ],
  "Nominal_Altitude(km)": [
    36000.0
  ],
  "Nominal_Central_Point_Coordinates(degrees)_Latitude_Longitude": [
    0.0,
    82.0
  ],
  "Observed_Altitude(km)": [
    1.496470511833e+151
  ],
  "Output_Format": "hdf5-1.8.8",
  "Processing_Level": "L1B",
  "Product_Creation_Time": "2025-05-29T18:02:47",
  "Product_Type": "STANDARD (FULL DISK)",
  "Radiometric_Calibration_Type": "ONLINE CALIBRATED",
  "SWIR_Acquisition_Mode": "MAIN",
  "SWIR_Gain_Mode": [
    3
  ],
  "Sat_Azimuth(Degrees)": [
    2.05482787417242e+58
  ],
  "Sat_Elevation(Degrees)": [
    2.69031179348884e+107
  ],
  "Satellite_Name": "INSAT-3DS",
  "Sensor_Id": "IMG",
  "Sensor_Name": "IMAGER",
  "SlowScan_Linearity_Enabled": "no",
  "Software_Version": "1.0",
  "Station_Id": "BES",
  "Sun_Azimuth(Degrees)": [
    2.08010780942678e-66
  ],
  "Sun_Elevation(Degrees)": [
    7.68248614658878e-76
  ],
  "TIR1_Acquisition_Mode": "MAIN",
  "TIR1_Gain_Mode": [
    3
  ],
  "TIR2_Acquisition_Mode": "MAIN",
  "TIR2_Gain_Mode": [
    3
  ],
  "Unique_Id": "3SIMG_29MAY2025_1200",
  "VIS_Acquisition_Mode": "MAIN",
  "VIS_Gain_Mode": [
    3
  ],
  "WV_Acquisition_Mode": "MAIN",
  "WV_Gain_Mode": [
    3
  ],
  "Yaw_Flip_Flag": "Y",
  "conventions": "CF-1.6",
  "institute": "BES,SAC/ISRO,Ahmedabad,INDIA.",
  "left_longitude": [
    0.8432964086532593
  ],
  "lower_latitude": [
    -81.0415267944336
  ],
  "right_longitude": [
    163.15670776367188
  ],
  "source": "BES,SAC/ISRO,Ahmedabad,INDIA.",
  "title": "3SIMG_29MAY2025_1200_L1B",
  "upper_latitude": [
    81.0415267944336
  ]
}
```
### Dataset Inventory
- **`GeoX`**: shape [2805], dtype `int32`
  - Attributes: {"CLASS": "DIMENSION_SCALE", "REFERENCE_LIST": [["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1]]}
- **`GeoX1`**: shape [11220], dtype `int32`
  - Attributes: {"CLASS": "DIMENSION_SCALE", "REFERENCE_LIST": [["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1]]}
- **`GeoY`**: shape [2816], dtype `int32`
  - Attributes: {"CLASS": "DIMENSION_SCALE", "REFERENCE_LIST": [["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0]]}
- **`GeoY1`**: shape [11264], dtype `int32`
  - Attributes: {"CLASS": "DIMENSION_SCALE", "REFERENCE_LIST": [["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0]]}
- **`GeoY2`**: shape [1409], dtype `int32`
  - Attributes: {"CLASS": "DIMENSION_SCALE", "REFERENCE_LIST": [["<HDF5 object reference>", 0]]}
- **`GreyCount`**: shape [1024], dtype `int32`
  - Attributes: {"CLASS": "DIMENSION_SCALE", "REFERENCE_LIST": [["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0]]}
- **`IMG_MIR`**: shape [1, 2816, 2805], dtype `uint16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [1023], "bandwidth": [0.18799999356269836], "bits_per_pixel": [10], "central_wavelength": [3.900599956512451], "coordinates": "time Latitude Longitude", "invert": "true", "long_name": "Middle Infrared Count", "online_radiance_add_offset": [-0.0064835199154913425], "online_radiance_add_offset_gsics": [-0.0064835199154913425], "online_radiance_quad": [0.0], "online_radiance_quad_gsics": [0.0], "online_radiance_scale_factor": [0.00033658801112324], "online_radiance_scale_factor_gsics": [0.00033658801112324], "radiance_units": "mW.cm-2.sr-1.micron-1", "resolution": [4.0], "resolution_unit": "km", "wavelength_unit": "micron"}
- **`IMG_MIR_RADIANCE`**: shape [1024], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "_FillValue": [999.0], "invert": "true", "long_name": "Middle Infrared Radiance", "units": "mW.cm-2.sr-1.micron-1"}
- **`IMG_MIR_TEMP`**: shape [1024], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "_FillValue": [999.0], "invert": "true", "long_name": "Middle Infrared Brightness Temperature", "units": "K"}
- **`IMG_SWIR`**: shape [1, 11264, 11220], dtype `uint16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [0], "bandwidth": [0.12409999966621399], "bits_per_pixel": [10], "central_wavelength": [1.614400029182434], "coordinates": "time Latitude_VIS Longitude_VIS", "invert": "false", "long_name": "Shortwave Infrared Count", "online_radiance_add_offset": [-0.19683299958705902], "online_radiance_add_offset_gsics": [-0.19683299958705902], "online_radiance_quad": [0.0], "online_radiance_quad_gsics": [0.0], "online_radiance_scale_factor": [0.007974900305271149], "online_radiance_scale_factor_gsics": [0.007974900305271149], "radiance_units": "mW.cm-2.sr-1.micron-1", "resolution": [1.0], "resolution_unit": "km", "wavelength_unit": "micron"}
- **`IMG_SWIR_ALBEDO`**: shape [1024], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "invert": "false", "long_name": "Shortwave Infrared Albedo", "units": "%"}
- **`IMG_SWIR_RADIANCE`**: shape [1024], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "_FillValue": [999.0], "invert": "false", "long_name": "Shortwave Infrared Radiance", "units": "mW.cm-2.sr-1.micron-1"}
- **`IMG_TIR1`**: shape [1, 2816, 2805], dtype `uint16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [1023], "bandwidth": [0.8985999822616577], "bits_per_pixel": [10], "central_wavelength": [10.784199714660645], "coordinates": "time Latitude Longitude", "invert": "true", "long_name": "Thermal Infrared1 Count", "online_radiance_add_offset": [-0.03998890146613121], "online_radiance_add_offset_gsics": [-0.03998890146613121], "online_radiance_quad": [0.0], "online_radiance_quad_gsics": [0.0], "online_radiance_scale_factor": [0.0018077499698847532], "online_radiance_scale_factor_gsics": [0.0018077499698847532], "radiance_units": "mW.cm-2.sr-1.micron-1", "resolution": [4.0], "resolution_unit": "km", "wavelength_unit": "micron"}
- **`IMG_TIR1_RADIANCE`**: shape [1024], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "_FillValue": [999.0], "invert": "true", "long_name": "Thermal Infrared1 Radiance", "units": "mW.cm-2.sr-1.micron-1"}
- **`IMG_TIR1_TEMP`**: shape [1024], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "_FillValue": [999.0], "invert": "true", "long_name": "Thermal Infrared1 Brightness Temperature", "units": "K"}
- **`IMG_TIR2`**: shape [1, 2816, 2805], dtype `uint16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [1023], "bandwidth": [0.8299999833106995], "bits_per_pixel": [10], "central_wavelength": [11.984600067138672], "coordinates": "time Latitude Longitude", "invert": "true", "long_name": "Thermal Infrared2 Count", "online_radiance_add_offset": [-0.04693540185689926], "online_radiance_add_offset_gsics": [-0.04693540185689926], "online_radiance_quad": [0.0], "online_radiance_quad_gsics": [0.0], "online_radiance_scale_factor": [0.0020012599416077137], "online_radiance_scale_factor_gsics": [0.0020012599416077137], "radiance_units": "mW.cm-2.sr-1.micron-1", "resolution": [4.0], "resolution_unit": "km", "wavelength_unit": "micron"}
- **`IMG_TIR2_RADIANCE`**: shape [1024], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "_FillValue": [999.0], "invert": "true", "long_name": "Thermal Infrared2 Radiance", "units": "mW.cm-2.sr-1.micron-1"}
- **`IMG_TIR2_TEMP`**: shape [1024], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "_FillValue": [999.0], "invert": "true", "long_name": "Thermal Infrared2 Brightness Temperature", "units": "K"}
- **`IMG_VIS`**: shape [1, 11264, 11220], dtype `uint16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [0], "bandwidth": [0.20409999787807465], "bits_per_pixel": [10], "central_wavelength": [0.6603999733924866], "coordinates": "time Latitude_VIS Longitude_VIS", "invert": "false", "long_name": "Visible Count", "online_radiance_add_offset": [-4.517000198364258], "online_radiance_add_offset_gsics": [-4.517000198364258], "online_radiance_quad": [0.0], "online_radiance_quad_gsics": [0.0], "online_radiance_scale_factor": [0.08522699773311615], "online_radiance_scale_factor_gsics": [0.08522699773311615], "radiance_units": "mW.cm-2.sr-1.micron-1", "resolution": [1.0], "resolution_unit": "km", "wavelength_unit": "micron"}
- **`IMG_VIS_ALBEDO`**: shape [1024], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "invert": "false", "long_name": "Visible Albedo", "units": "%"}
- **`IMG_VIS_RADIANCE`**: shape [1024], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "_FillValue": [999.0], "invert": "false", "long_name": "Visible Radiance", "units": "mW.cm-2.sr-1.micron-1"}
- **`IMG_WV`**: shape [1, 2816, 2805], dtype `uint16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [1023], "bandwidth": [0.5153999924659729], "bits_per_pixel": [10], "central_wavelength": [6.823999881744385], "coordinates": "time Latitude Longitude", "invert": "true", "long_name": "Water Vapor Count", "online_radiance_add_offset": [-0.031197799369692802], "online_radiance_add_offset_gsics": [-0.031197799369692802], "online_radiance_quad": [0.0], "online_radiance_quad_gsics": [0.0], "online_radiance_scale_factor": [0.0012582000344991684], "online_radiance_scale_factor_gsics": [0.0012582000344991684], "radiance_units": "mW.cm-2.sr-1.micron-1", "resolution": [4.0], "resolution_unit": "km", "wavelength_unit": "micron"}
- **`IMG_WV_RADIANCE`**: shape [1024], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "_FillValue": [999.0], "invert": "true", "long_name": "Water Vapor Radiance", "units": "mW.cm-2.sr-1.micron-1"}
- **`IMG_WV_TEMP`**: shape [1024], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "_FillValue": [999.0], "invert": "true", "long_name": "Water Vapor Brightness Temperature", "units": "K"}
- **`Latitude`**: shape [2816, 2805], dtype `int16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [32767], "add_offset": [0.0], "long_name": "latitude", "scale_factor": [0.009999999776482582], "units": "degrees_north"}
- **`Latitude_VIS`**: shape [11264, 11220], dtype `int32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [327670], "add_offset": [0.0], "long_name": "latitude", "scale_factor": [0.0010000000474974513], "units": "degrees_north"}
- **`Longitude`**: shape [2816, 2805], dtype `int16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [32767], "add_offset": [0.0], "long_name": "longitude", "scale_factor": [0.009999999776482582], "units": "degrees_east"}
- **`Longitude_VIS`**: shape [11264, 11220], dtype `int32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [327670], "add_offset": [0.0], "long_name": "longitude", "scale_factor": [0.0010000000474974513], "units": "degrees_east"}
- **`SCAN_LINE_TIME`**: shape [1409], dtype `|S24`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"]], "long_name": "Scan Time for Water Vapor Resolution"}
- **`Sat_Azimuth`**: shape [1, 2816, 2805], dtype `uint16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [65535], "add_offset": [0.0], "coordinates": "time Latitude Longitude", "long_name": "Satellite Azimuth", "scale_factor": [0.009999999776482582], "units": "degree"}
- **`Sat_Elevation`**: shape [1, 2816, 2805], dtype `int16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [32767], "add_offset": [0.0], "coordinates": "time Latitude Longitude", "long_name": "Satellite Elevation", "scale_factor": [0.009999999776482582], "units": "degree"}
- **`Sun_Azimuth`**: shape [1, 2816, 2805], dtype `uint16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [65535], "add_offset": [0.0], "coordinates": "time Latitude Longitude", "long_name": "Sun Azimuth", "scale_factor": [0.009999999776482582], "units": "degree"}
- **`Sun_Elevation`**: shape [1, 2816, 2805], dtype `int16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [32767], "add_offset": [0.0], "coordinates": "time Latitude Longitude", "long_name": "Sun Elevation", "scale_factor": [0.009999999776482582], "units": "degree"}
- **`time`**: shape [1], dtype `float64`
  - Attributes: {"CLASS": "DIMENSION_SCALE", "REFERENCE_LIST": [["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0]], "units": "minutes since 2000-01-01 00:00:00"}

## 4. CTP Structure & Variable Inventory
**Representative File**: 3SIMG_29MAY2025_1200_L2B_CTP_V01R00.h5
### Dataset Inventory
- **`CLRFR_MIR`**: shape [1, 325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Fractional Clear Area for MIR", "standard_name": "Fractional Clear Area"}
- **`CLRFR_TIR1`**: shape [1, 325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Fractional Clear Area for TIR1", "standard_name": "Fractional Clear Area"}
- **`CLRFR_TIR2`**: shape [1, 325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Fractional Clear Area for TIR2", "standard_name": "Fractional Clear Area"}
- **`CLRFR_WVR`**: shape [1, 325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Fractional Clear Area for WVR", "standard_name": "Fractional Clear Area"}
- **`CSBT_Latitude`**: shape [325, 325], dtype `int16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [31172], "add_offset": [0.0], "long_name": "csbt_latitude", "scale_factor": [0.009999999776482582], "standard_name": "csbt_latitude", "units": "degrees_north"}
- **`CSBT_Longitude`**: shape [325, 325], dtype `int16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [31172], "add_offset": [0.0], "long_name": "csbt_longitude", "scale_factor": [0.009999999776482582], "standard_name": "csbt_longitude", "units": "degrees_east"}
- **`CSBT_MIR`**: shape [1, 325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Clear Sky BT for MIR", "standard_name": "Clear Sky BT for MIR", "units": "K"}
- **`CSBT_TIR1`**: shape [1, 325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Clear Sky BT for TIR1", "standard_name": "Clear Sky BT for TIR1", "units": "K"}
- **`CSBT_TIR2`**: shape [1, 325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Clear Sky BT for TIR2", "standard_name": "Clear Sky BT for TIR2", "units": "K"}
- **`CSBT_WVR`**: shape [1, 325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Clear Sky BT for Water Vapour", "standard_name": "Clear Sky BT for Water Vapour", "units": "K"}
- **`CTP`**: shape [1, 313, 312], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Cloud Top Pressure", "standard_name": "Cloud Top Pressure", "units": "hPa"}
- **`CTT`**: shape [1, 313, 312], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Cloud Top Temperature", "standard_name": "Cloud Top Temperature", "units": "K"}
- **`EFF_EMISS`**: shape [1, 313, 312], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Effective Cloud Emissivity", "standard_name": "Effective Cloud Emissivity", "units": "NA"}
- **`GeoX`**: shape [312], dtype `int32`
  - Attributes: {"CLASS": "DIMENSION_SCALE", "REFERENCE_LIST": [["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1]]}
- **`GeoX_csbt`**: shape [325], dtype `int32`
  - Attributes: {"CLASS": "DIMENSION_SCALE", "REFERENCE_LIST": [["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 2], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1]]}
- **`GeoY`**: shape [313], dtype `int32`
  - Attributes: {"CLASS": "DIMENSION_SCALE", "REFERENCE_LIST": [["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0]]}
- **`GeoY_csbt`**: shape [325], dtype `int32`
  - Attributes: {"CLASS": "DIMENSION_SCALE", "REFERENCE_LIST": [["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 1], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0]]}
- **`Latitude`**: shape [313, 312], dtype `int16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [31172], "add_offset": [0.0], "long_name": "latitude", "scale_factor": [0.009999999776482582], "standard_name": "latitude", "units": "degrees_north"}
- **`Longitude`**: shape [313, 312], dtype `int16`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [31172], "add_offset": [0.0], "long_name": "longitude", "scale_factor": [0.009999999776482582], "standard_name": "longitude", "units": "degrees_east"}
- **`OFLG_MIR`**: shape [1, 325, 325], dtype `int32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999], "coordinates": "time Latitude Longitude", "long_name": "Clear Sky BT Confidence Flag", "standard_name": "Clear Sky BT Confidence Flag", "units": "NA"}
- **`OFLG_TIR1`**: shape [1, 325, 325], dtype `int32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999], "coordinates": "time Latitude Longitude", "long_name": "Clear Sky BT Confidence Flag", "standard_name": "Clear Sky BT Confidence Flag", "units": "NA"}
- **`OFLG_TIR2`**: shape [1, 325, 325], dtype `int32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999], "coordinates": "time Latitude Longitude", "long_name": "Clear Sky BT Confidence Flag", "standard_name": "Clear Sky BT Confidence Flag", "units": "NA"}
- **`OFLG_WVR`**: shape [1, 325, 325], dtype `int32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999], "coordinates": "time Latitude Longitude", "long_name": "Clear Sky BT Confidence Flag", "standard_name": "Clear Sky BT Confidence Flag", "units": "NA"}
- **`SAT_ZEN`**: shape [325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "add_offset": [0.0], "long_name": "sat_zen", "scale_factor": [0.009999999776482582], "standard_name": "sat_zen", "units": "degrees_north"}
- **`SOL_ZEN`**: shape [325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "add_offset": [0.0], "long_name": "sun_zen", "scale_factor": [0.009999999776482582], "standard_name": "sun_zen", "units": "degrees_east"}
- **`STDV_MIR`**: shape [1, 325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Clear Sky BT Standard Deviation", "standard_name": "Clear Sky BT Standard Deviation", "units": "K"}
- **`STDV_TIR1`**: shape [1, 325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Clear Sky BT Standard Deviation", "standard_name": "Clear Sky BT Standard Deviation", "units": "K"}
- **`STDV_TIR2`**: shape [1, 325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Clear Sky BT Standard Deviation", "standard_name": "Clear Sky BT Standard Deviation", "units": "K"}
- **`STDV_WVR`**: shape [1, 325, 325], dtype `float32`
  - Attributes: {"DIMENSION_LIST": [["<HDF5 object reference>"], ["<HDF5 object reference>"], ["<HDF5 object reference>"]], "_FillValue": [-999.0], "coordinates": "time Latitude Longitude", "long_name": "Clear Sky BT Standard Deviation", "standard_name": "Clear Sky BT Standard Deviation", "units": "K"}
- **`time`**: shape [1], dtype `float64`
  - Attributes: {"CLASS": "DIMENSION_SCALE", "REFERENCE_LIST": [["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0], ["<HDF5 object reference>", 0]], "units": "minutes since 2000-01-01 00:00:00"}

## 5. Geolocation Findings
*(See exact dataset paths for lat/lon in the structural dump above. If unavailable at root, check subgroups)*

## 6. Temporal Metadata
*(See root attributes for Date, Time, Epoch, or similar variables)*

## 7. Cross-File Consistency
All L1B files share identical schemas. All CTP files share identical schemas.

## 8. Implications for Future Parser
- Structure must be carefully mapped in `backend/pipeline/ingestion/`.
- H5NetCDF/xarray may need specific group paths.
- Scale factors and offsets must be manually applied if xarray does not auto-decode based on metadata conventions.