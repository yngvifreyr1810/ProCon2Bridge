import asyncio
from pathlib import Path
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import unittest
import bridge

class DesktopLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_start_closes_device_and_releases_listener(self):
        fake = SimpleNamespace(run=AsyncMock(side_effect=RuntimeError('adapter not ready')),
            close=AsyncMock())
        guard = SimpleNamespace(close=lambda: None, wait_closed=AsyncMock())
        options = SimpleNamespace(calibrate=False, duration=0)
        with patch('bridge.load_config', return_value={'gyro_calibrated':True,'gyro_bias':[0,0,0]}), \
             patch('bridge.Bridge', return_value=fake), \
             patch('bridge.asyncio.start_server', AsyncMock(return_value=guard)):
            with self.assertRaisesRegex(RuntimeError, 'adapter not ready'):
                await bridge.main(options)
        fake.close.assert_awaited_once()
        guard.wait_closed.assert_awaited_once()

    async def test_startup_retry_can_be_stopped_while_adapter_unavailable(self):
        shutdown = threading.Event()
        async def fail(*args):
            shutdown.set()
            raise OSError('Bluetooth not ready')
        with patch('bridge.main', AsyncMock(side_effect=fail)) as run:
            await asyncio.wait_for(bridge.desktop_main(object(), shutdown), 1)
        run.assert_awaited_once()

class InstallationTests(unittest.TestCase):
    def test_upgrade_preserves_config_and_does_not_reenable_disabled_startup(self):
        import tempfile
        import desktop_runtime as runtime
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'download'; target=Path(directory)/'installed'
            root.mkdir(); target.mkdir()
            (root/'ProCon2Bridge.exe').write_bytes(b'same binary')
            (target/'ProCon2Bridge.exe').write_bytes(b'same binary')
            (root/'config.json').write_text('download config')
            (target/'config.json').write_text('user mappings and calibration')
            (target/'desktop.json').write_text('{"startup_registered":true}')
            with patch.object(runtime,'INSTALL',target), \
                 patch.object(runtime,'register_startup') as register, \
                 patch.object(runtime,'spawn') as launch, \
                 patch.object(runtime.sys,'argv',['ProCon2Bridge.exe']):
                self.assertTrue(runtime.prepare(root,SimpleNamespace(stop=False,settings=False)))
            self.assertEqual((target/'config.json').read_text(),'user mappings and calibration')
            register.assert_not_called()
            launch.assert_called_once_with(target/'ProCon2Bridge.exe','--background')
