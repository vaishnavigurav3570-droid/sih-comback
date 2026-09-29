import os
import h5py
import numpy as np
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.inspect_hdf5 import get_h5_structure, _parse_attr

def test_parse_attr():
    assert _parse_attr(10) == 10
    assert _parse_attr(10.5) == 10.5
    assert _parse_attr("test") == "test"
    assert _parse_attr(b"test") == "test"
    assert _parse_attr([1, 2, b"test"]) == [1, 2, "test"]
    assert _parse_attr(np.array([1, 2, 3])) == [1, 2, 3]
    assert _parse_attr(None) == None
    assert _parse_attr(True) == True

def test_get_h5_structure(tmp_path):
    h5_path = tmp_path / "test.h5"
    
    with h5py.File(h5_path, 'w') as f:
        f.attrs['test_attr'] = 'value'
        f.attrs['num_attr'] = 42
        
        # Dataset
        ds = f.create_dataset('data1', data=np.arange(10, dtype=np.int32))
        ds.attrs['scale_factor'] = 0.5
        
        # Group
        grp = f.create_group('group1')
        grp.attrs['desc'] = b'A test group'
        grp.create_dataset('data2', data=np.array([[1.1, 2.2], [3.3, 4.4]]))
        
    with h5py.File(h5_path, 'r') as f:
        structure = get_h5_structure(f)
        
        assert 'data1' in structure
        assert structure['data1']['type'] == 'Dataset'
        assert structure['data1']['shape'] == [10]
        assert structure['data1']['dtype'] == 'int32'
        assert structure['data1']['attributes']['scale_factor'] == 0.5
        assert structure['data1']['min'] == 0.0
        assert structure['data1']['max'] == 9.0
        
        assert 'group1' in structure
        assert structure['group1']['type'] == 'Group'
        assert structure['group1']['attributes']['desc'] == 'A test group'
        
        assert 'data2' in structure['group1']['children']
        assert structure['group1']['children']['data2']['type'] == 'Dataset'
        assert structure['group1']['children']['data2']['shape'] == [2, 2]
        assert structure['group1']['children']['data2']['dtype'] == 'float64'
        assert structure['group1']['children']['data2']['min'] == 1.1
        assert structure['group1']['children']['data2']['max'] == 4.4
