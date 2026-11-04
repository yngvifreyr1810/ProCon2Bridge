import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from configuration import load_config,update_config
from protocol import BUTTONS,remap_buttons,switch_report,Sample,mapping_targets
from settings_ui import parse_action,format_action

class MappingTests(unittest.TestCase):
    def test_two_backs_chord_overlap_and_release(self):
        m={'GL':['ZL','ZR'],'GR':'B'}
        def output(raw):return int.from_bytes(switch_report(Sample(buttons=remap_buttons(raw,m)))[3:6],'little')
        self.assertEqual(output(BUTTONS['GL']|BUTTONS['GR']),BUTTONS['ZL']|BUTTONS['ZR']|BUTTONS['B'])
        # Releasing the back button must keep a physical target that is still held.
        self.assertEqual(output(BUTTONS['ZL']|BUTTONS['GR']),BUTTONS['ZL']|BUTTONS['B'])
        self.assertEqual(output(0),0)
        self.assertEqual(output(BUTTONS['GR']),BUTTONS['B'])

    def test_shared_target_is_not_released_by_other_source(self):
        m={'GL':'B','GR':'B'}
        for raw in (BUTTONS['GL'],BUTTONS['GR'],BUTTONS['GL']|BUTTONS['GR']):
            self.assertEqual(remap_buttons(raw,m),BUTTONS['B'])
        self.assertEqual(remap_buttons(0,m),0)

    def test_editor_normalizes_and_rejects_unavailable_controls(self):
        self.assertEqual(parse_action(' zl + zr '),['ZL','ZR'])
        self.assertEqual(parse_action('B + B'),'B')
        self.assertEqual(format_action('NONE'),'NONE')
        for text in ('GL','GR','C','NONE + A','A + B + X + Y + ZL','', 'KEY_F1'):
            with self.assertRaises(ValueError,msg=text):parse_action(text)

class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'config.json'
        shutil.copy(Path(__file__).parent.parent/'config.example.json',self.path.parent/'config.example.json')

    def test_initial_config_and_concurrent_mapping_calibration_preserve_fields(self):
        cfg=load_config(self.path);self.assertEqual(cfg['button_mapping']['GL'],'NONE')
        errors=[]
        def write(**kwargs):
            try:update_config(self.path,**kwargs)
            except Exception as e:errors.append(e)
        threads=[threading.Thread(target=write,kwargs=dict(mappings={'GL':['A','B'],'GR':'ZL'})),
            threading.Thread(target=write,kwargs=dict(patch={'gyro_bias':[1.,2.,3.],'gyro_calibrated':True}))]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertFalse(errors)
        saved=load_config(self.path)
        self.assertEqual(saved['gyro_bias'],[1.,2.,3.]);self.assertTrue(saved['gyro_calibrated'])
        self.assertEqual(saved['button_mapping'],{'GL':['A','B'],'GR':'ZL','C':'NONE'})

    def test_rejected_edit_keeps_previous_config(self):
        original=load_config(self.path)
        for edit in ({'gyro_bias':[float('nan'),0,0]},{'rumble_strength':float('inf')},{'button_mapping':{'GL':'GL'}}):
            with self.assertRaises(ValueError):update_config(self.path,patch=edit)
            self.assertEqual(load_config(self.path),original)
