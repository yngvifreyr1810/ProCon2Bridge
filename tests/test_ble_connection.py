import asyncio
from types import SimpleNamespace
import unittest
from ble_connection import controller_connection,request_throughput,release_request

class FakeClient:
    def __init__(self,mode='ok'):
        self.mode=mode;self.closed=0
        self.services=SimpleNamespace(get_characteristic=lambda _:None if mode=='missing' else object())
    async def connect(self):
        if self.mode=='fail':raise OSError('stale Windows GATT cache')
    async def disconnect(self):self.closed+=1

class BLETests(unittest.IsolatedAsyncioTestCase):
    async def test_stale_cache_and_filtered_discovery_fall_back_to_fresh_full(self):
        clients=[FakeClient('missing'),FakeClient('fail'),FakeClient()];calls=[]
        def factory(device,**kwargs):calls.append(kwargs);return clients[len(calls)-1]
        async with controller_connection('device',factory,lambda _:None,cached=True) as client:
            self.assertIs(client,clients[-1])
            self.assertEqual([c.closed for c in clients],[1,1,0])
        self.assertEqual([c.closed for c in clients],[1,1,1])
        self.assertEqual([k['winrt']['use_cached_services'] for k in calls],[True,False,False])
        self.assertIsNone(calls[-1]['services'])

    async def test_body_failure_does_not_silently_retry_a_new_session(self):
        clients=[]
        def factory(*args,**kwargs):c=FakeClient();clients.append(c);return c
        with self.assertRaisesRegex(RuntimeError,'initialization'):
            async with controller_connection('device',factory,lambda _:None):raise RuntimeError('initialization')
        self.assertEqual(len(clients),1);self.assertEqual(clients[0].closed,1)

    async def test_cancellation_does_not_start_new_connection(self):
        client=FakeClient()
        async def cancel():raise asyncio.CancelledError()
        client.connect=cancel
        with self.assertRaises(asyncio.CancelledError):
            async with controller_connection('device',lambda *a,**k:client,lambda _:None):pass
        self.assertEqual(client.closed,1)

    async def test_sync_async_throughput_requests_and_explicit_disposal(self):
        for asynchronous in (False,True):
            request=SimpleNamespace(status=1,closed=False)
            request.close=lambda:setattr(request,'closed',True)
            async def create(_):return request
            native=SimpleNamespace(**{'request_preferred_connection_parameters_async' if asynchronous else 'request_preferred_connection_parameters':create if asynchronous else lambda _:request})
            client=SimpleNamespace(_backend=SimpleNamespace(_requester=native))
            self.assertIs(await request_throughput(client,parameters=object()),request)
            self.assertFalse(request.closed);release_request(request);self.assertTrue(request.closed)
