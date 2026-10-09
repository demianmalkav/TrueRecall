import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("recovery_doctor", ROOT / "tools" / "recovery_doctor.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class RecoveryDoctorStaticTests(unittest.TestCase):
    def test_manifest_static_contract_has_no_failures(self):
        manifest = mod.load_manifest(ROOT)
        checks = mod.validate_static(ROOT, manifest)
        failures = [c for c in checks if c.status == "FAIL"]
        self.assertEqual(failures, [])

    def test_manifest_canonical_identity(self):
        manifest = mod.load_manifest(ROOT)
        spec = manifest["canonical_rom"]
        self.assertEqual(spec["size_bytes"], 2097152)
        self.assertEqual(spec["sha1"], "d39174bed46ede85531b86df7ba49123ce2f8411")
        self.assertTrue(spec["availability_is_session_local"])

    def test_bad_rom_is_rejected(self):
        manifest = mod.load_manifest(ROOT)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.bin"
            path.write_bytes(b"not the canonical rom")
            checks = mod.validate_rom(manifest, path)
        self.assertEqual(checks[0].status, "FAIL")


if __name__ == "__main__":
    unittest.main()
