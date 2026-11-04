import asyncio
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import unittest
import bridge
from configuration import load_config,update_config
from protocol import Sample,BUTTONS

class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        shutil.copy(Path(__file__).parent.parent/'config.example.json',self.root/'config.example.json')
        self.patch=patch('bridge.ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)
        self.instance=bridge.Bridge(load_config(self.root/'config.json'),SimpleNamespace(calibrate=False),self.root/'config.json')
        self.states=[];self.instance.server=SimpleNamespace(update_state=self.states.append)

    async def test_disconnect_releases_held_buttons_and_ignores_old_session_callback(self):
        b=self.instance;client=object();b.client=client;b.state='connected'
        b.sample=b.raw_sample=Sample(buttons=BUTTONS['A']);b.dsu.connected=True
        b.controller_disconnected(object());self.assertFalse(b.disconnected.is_set())
        b.controller_disconnected(client)
        self.assertTrue(b.disconnected.is_set());self.assertFalse(b.dsu.connected)
        self.assertEqual(self.states[-1][3:6],b'\0'*3);self.assertEqual(b.state,'reconnecting')

    async def test_input_watchdog_is_independent_of_haptic_writes(self):
        b=self.instance;b.state='connected';b.last_input=bridge.time.monotonic()-3
        task=asyncio.create_task(b.maintenance())
        try:
            await asyncio.wait_for(b.disconnected.wait(),.8)
            self.assertEqual(self.states[-1][3:6],b'\0'*3)
        finally:
            task.cancel()
            try:await task
            except asyncio.CancelledError:pass

    async def test_live_mapping_reload(self):
        b=self.instance;update_config(b.config_path,mappings={'GL':['ZL','ZR'],'GR':'B'})
        task=asyncio.create_task(b.maintenance())
        try:
            async with asyncio.timeout(1):
                while b.cfg['button_mapping']['GR']!='B':await asyncio.sleep(.02)
            self.assertEqual(b.cfg['button_mapping']['GL'],['ZL','ZR'])
        finally:
            task.cancel()
            try:await task
            except asyncio.CancelledError:pass

    async def test_stalled_ble_write_has_a_deadline(self):
        async def stuck(*args,**kwargs):await asyncio.Future()
        self.instance.client=SimpleNamespace(write_gatt_char=stuck)
        with self.assertRaises(TimeoutError):await self.instance.write_packet(b'test')
