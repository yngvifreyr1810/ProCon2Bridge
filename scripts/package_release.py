"""GPL-3.0-or-later. Package ONLY tracked source plus two named release binaries."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import zipfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from version import __version__

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    tracked=subprocess.check_output(['git','-C',str(root),'ls-files','-z']).decode().split('\0')[:-1]
    files={p:(root/p).read_bytes() for p in tracked}
    for name in ('ProCon2Bridge.exe','drivers/USBip-0.9.8.1-x64.exe'):files[name]=(root/name).read_bytes()
    assert hashlib.sha256(files['drivers/USBip-0.9.8.1-x64.exe']).hexdigest()=='38cad6d4432b52d5bb9409d9ad03b72fdffc4ada4cd3a48fbeca1a2752a8518a'
    assert not any(Path(p).name in ('config.json','status.json') or p.endswith(('.log','.pyc')) for p in files)
    commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    files['SOURCE.txt']=f'ProCon2Bridge {__version__}\nhttps://github.com/yngvifreyr1810/ProCon2Bridge\nSource commit: {commit}\nAll corresponding bridge source is included. Third-party sources/licenses: docs/THIRD_PARTY.md.\n'.encode()
    files['CHECKSUMS-SHA256.txt']=''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name,data in sorted(files.items())).encode()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(files.items()):archive.writestr('ProCon2Bridge/'+name,data)
    print(args.output.name,len(files),'allowlisted files')
if __name__=='__main__':main()
