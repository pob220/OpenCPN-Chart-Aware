import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('verify_pe', Path(__file__).with_name('verify_pe.py'))
pe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pe)

def fixture(path, machine=0x8664, magic=0x20b, large=True):
    data = bytearray(512)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 0x3c, 0x80)
    data[0x80:0x84] = b'PE\0\0'
    struct.pack_into('<HHIIIHH', data, 0x84, machine, 1, 0, 0, 0, 240,
                     0x0022 if large else 0x0002)
    struct.pack_into('<H', data, 0x98, magic)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

class ArchitectureGate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def test_accepts_x64_large_address_aware_core(self):
        fixture(self.root / 'opencpn.exe')
        result = pe.verify(self.root)
        self.assertTrue(result['opencpn.exe']['large_address_aware'])

    def test_rejects_x86_even_when_filename_says_x64(self):
        fixture(self.root / 'plugin-x64.dll', 0x14c, 0x10b)
        with self.assertRaises(ValueError): pe.verify(self.root)

    def test_rejects_arm64_in_x64_bundle(self):
        fixture(self.root / 'plugin.dll', 0xaa64)
        with self.assertRaises(ValueError): pe.verify(self.root)

    def test_rejects_nested_x86_dependency(self):
        fixture(self.root / 'opencpn.exe')
        fixture(self.root / 'plugins/xgrib/bin/decoder.DLL', 0x14c, 0x10b)
        with self.assertRaises(ValueError): pe.verify(self.root)

    def test_requires_large_address_aware_core(self):
        fixture(self.root / 'opencpn.exe', large=False)
        with self.assertRaises(ValueError): pe.verify(self.root)

    def test_rejects_empty_tree(self):
        with self.assertRaises(ValueError): pe.verify(self.root)

    def test_rejects_disguised_non_pe(self):
        (self.root / 'plugin.dll').write_bytes(b'ELF payload pretending to be a DLL')
        with self.assertRaises(ValueError): pe.verify(self.root)

    def test_rejects_mismatched_optional_header(self):
        fixture(self.root / 'plugin.dll', magic=0x10b)
        with self.assertRaises(ValueError): pe.verify(self.root)

if __name__ == '__main__': unittest.main()
