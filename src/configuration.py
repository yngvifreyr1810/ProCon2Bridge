"""GPL-3.0-or-later. Validated config and atomic, serialized read/modify/write."""
import contextlib
import json
import math
import os
from pathlib import Path
import tempfile
from protocol import BUTTONS, mapping_targets

def load_config(path):
    path=Path(path)
    if not path.exists():
        defaults=json.loads((path.parent/'config.example.json').read_text(encoding='utf-8-sig'))
        update_config(path,defaults)
    return validate_config(json.loads(path.read_text(encoding='utf-8-sig')))

def validate_config(cfg):
    if not isinstance(cfg,dict): raise ValueError('Configuration must be an object')
    for key,low,high in (('deadzone',0,.4),('gyro_scale',.1,4),('rumble_strength',0,1)):
        v=cfg.get(key)
        if type(v) not in (int,float) or not math.isfinite(v) or not low<=v<=high:
            raise ValueError(f'{key} must be {low}..{high}')
    bias=cfg.get('gyro_bias')
    if not isinstance(bias,list) or len(bias)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>32768 for v in bias):
        raise ValueError('gyro_bias must contain three finite sensor values')
    mappings=cfg.get('button_mapping')
    if not isinstance(mappings,dict): raise ValueError('button_mapping must be an object')
    for source,target in mappings.items():
        if source not in BUTTONS: raise ValueError('Unknown mapping source')
        mapping_targets(target)
    for key in ('dsu_port','usbip_port'):
        if type(cfg.get(key)) is not int or not 1024<=cfg[key]<=65535: raise ValueError(f'{key} must be 1024..65535')
    if not isinstance(cfg.get('device_address'),str): raise ValueError('device_address must be text')
    host=cfg.get('host_mac')
    if host!='auto':
        try: number=int(host.replace(':','').replace('-',''),16) if isinstance(host,str) else host
        except ValueError: raise ValueError('host_mac must be auto or a Bluetooth adapter address') from None
        if type(number) is not int or not 0<=number<1<<48: raise ValueError('Invalid host_mac')
    return cfg

@contextlib.contextmanager
def _writer_lock(path):
    # OS releases this lock even if the settings window or bridge crashes.
    with path.with_suffix('.lock').open('a+b') as handle:
        handle.seek(0,2)
        if handle.tell()==0: handle.write(b'\0');handle.flush()
        handle.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(handle.fileno(),msvcrt.LK_LOCK,1)
        else:
            import fcntl
            fcntl.flock(handle,fcntl.LOCK_EX)
        try: yield
        finally:
            handle.seek(0)
            if os.name=='nt': msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
            else: fcntl.flock(handle,fcntl.LOCK_UN)

def update_config(path,patch=None,mappings=None):
    path=Path(path)
    with _writer_lock(path):
        cfg=json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}
        if patch: cfg.update(patch)
        if mappings is not None:
            cfg['button_mapping']={**cfg.get('button_mapping',{}),**mappings}
        validate_config(cfg)
        fd,name=tempfile.mkstemp(prefix='config-',suffix='.tmp',dir=path.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as file:
                json.dump(cfg,file,ensure_ascii=False,indent=2);file.flush();os.fsync(file.fileno())
            os.replace(name,path)
        finally:
            with contextlib.suppress(FileNotFoundError): os.unlink(name)
    return cfg
