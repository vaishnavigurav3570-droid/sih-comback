import netCDF4 as nc

def check_nc(filepath):
    try:
        ds = nc.Dataset(filepath)
        print("Variables:")
        for v in ds.variables:
            var = ds.variables[v]
            print(f"  {v}: {var.dimensions}, shape={var.shape}, type={var.dtype}")
            if hasattr(var, 'units'):
                print(f"    units: {var.units}")
            if hasattr(var, 'long_name'):
                print(f"    long_name: {var.long_name}")
    except Exception as e:
        print(f"Failed to read netCDF: {e}")

if __name__ == "__main__":
    check_nc("polar_MUM190720194254.nc")
