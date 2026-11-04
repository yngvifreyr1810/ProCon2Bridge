"""GPL-3.0-or-later. Focused Windows BLE recovery, informed by Switch2Connect."""
import asyncio
import contextlib
from contextlib import asynccontextmanager
import logging
import sys
from protocol import WRITE,RESPONSE,INPUT,RUMBLE

LOG=logging.getLogger('ProCon2Bridge')
SERVICE='ab7de9be-89fe-49ad-828f-118f09df7fd0'

async def disconnect(client):
    with contextlib.suppress(Exception): await asyncio.wait_for(client.disconnect(),3)

@asynccontextmanager
async def controller_connection(device,factory,on_disconnect,cached=False):
    variants=[('fresh-filtered',[SERVICE],False),('fresh-full',None,False)]
    if cached: variants.insert(0,('cached-filtered',[SERVICE],True))
    client=None
    for index,(label,services,use_cache) in enumerate(variants):
        client=factory(device,timeout=18,services=services,winrt={'use_cached_services':use_cache},
            disconnected_callback=on_disconnect)
        try:
            await asyncio.wait_for(client.connect(),20)
            if any(client.services.get_characteristic(uuid) is None for uuid in (WRITE,RESPONSE,INPUT,RUMBLE)):
                raise RuntimeError('Required Pro Controller 2 GATT characteristics missing')
        except BaseException as error:
            await disconnect(client)
            if not isinstance(error,Exception) or index==len(variants)-1: raise
            LOG.warning('BLE %s failed (%s); retrying fresh discovery',label,error)
        else:
            LOG.info('BLE service discovery: %s',label)
            break
    try: yield client
    finally: await disconnect(client)

def release_request(request):
    if request is not None:
        close=getattr(request,'close',None)
        if callable(close):
            with contextlib.suppress(Exception): close()

async def request_throughput(client,parameters=None):
    # Win11 only; an unavailable projection/API must never block controller use.
    if parameters is None:
        if sys.platform!='win32' or sys.getwindowsversion().build<22000: return None
        from winrt.windows.devices.bluetooth import BluetoothLEPreferredConnectionParameters
        parameters=BluetoothLEPreferredConnectionParameters.throughput_optimized
    backend=getattr(client,'_backend',None)
    native=getattr(backend,'_requester',None) or getattr(backend,'_device',None) or getattr(client,'_device',None)
    if native is None: return None
    method=getattr(native,'request_preferred_connection_parameters_async',None)
    if method: request=await asyncio.wait_for(method(parameters),2)
    else:
        method=getattr(native,'request_preferred_connection_parameters',None)
        if not method: return None
        request=method(parameters)
    status=getattr(request,'status',None)
    LOG.info('Bluetooth throughput preference: %s',status)
    if status is not None and str(getattr(status,'name',status)).upper()!='SUCCESS' and status!=1:
        release_request(request);return None
    return request
