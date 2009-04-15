#!/usr/bin/env python
"""Apache License 2.0, see the LICENSE file for details."""

import unittest
import minusconf
import socket
import time

class MinusconfUnitTest(unittest.TestCase):
	def setUp(self):
		try:
			self._sharp_s = unichr(223)
		except: # Python 3+
			self._sharp_s = chr(223)
		sz = self._sharp_s
		
		machineid = socket.gethostname()
		self.svc1 = minusconf.Service('-conf-test-service-strange-' + machineid, 'strangeport', 'some name')
		self.svc2 = minusconf.Service('-conf-test-service' + sz + machineid, 'strangeport', 'some name', 'some location')
		self.svc3 = minusconf.Service('-conf-test-service' + sz + machineid, 'svcp3', 'svc3: sharp s = ' + sz)
		self.svc4 = minusconf.Service('-conf-test-service' + sz + machineid, 'svcp4', 'svc4', 'Buy More basement')
		self.svc5 = minusconf.Service('-conf-test-service' + sz + machineid, 'svcp5', 'svc5')
	
	def testServiceMatching(self):
		a = minusconf.Advertiser()
		def assert_sm(stype, sname, expected):
			self.assertEquals(set(a.services_matching(stype, sname)), set(expected))
		
		assert_sm('', '', [])
		
		a.services.append(self.svc1)
		assert_sm(self.svc1.stype, self.svc1.sname, [self.svc1])
		assert_sm(self.svc1.stype, '', [self.svc1])
		
		a.services.append(self.svc2)
		assert_sm(self.svc2.stype, self.svc2.sname, [self.svc2])
		
		a.services.append(self.svc3)
		assert_sm(self.svc3.stype, self.svc3.sname, [self.svc3])
		assert_sm('', self.svc3.sname, [self.svc3])
		
		assert_sm('', '', [self.svc1, self.svc2, self.svc3])
	
	def testServiceRepresentation(self):
		svca = minusconf.ServiceAt('aaa', 'bbb', 'ccc', 'ddd', 'eee', 'fff')
		
		reprfuncs = [repr]
		try:
			if not callable(unicode):
				raise Exception
			
			reprfuncs.append(unicode)
		except:
			reprfuncs.append(str) # Python 3+: str does not step over Unicode chars anymore
		
		for reprfunc in reprfuncs:
			for svc in [self.svc1, self.svc2, self.svc3, self.svc4, svca]:
				r = reprfunc(svc)
				self.assertTrue(r.find(reprfunc(svc.stype)) >= 0)
				self.assertTrue(r.find(reprfunc(svc.port)) >= 0)
				self.assertTrue(r.find(reprfunc(svc.sname)) >= 0)
			
			r = reprfunc(svca)
			self.assertTrue(r.find(reprfunc(svca.aname)) >= 0)
			self.assertTrue(r.find(reprfunc(svca.location)) >= 0)
	
	def testSingleThreadAdvertiser(self):
		a_thread = minusconf.ThreadAdvertiser([], 'unittest.advertiser-thread-single')
		self._runSingleConcurrentAdvertiserTest(a_thread)
	
	def testSingleMultiprocessingAdvertiser(self):
		a_mp = minusconf.MultiprocessingAdvertiser([], 'unittest.advertiser-multiprocessing-single')
		self._runSingleConcurrentAdvertiserTest(a_mp)
	
	def testMultiThreadAdvertisers(self):
		a1 = minusconf.ThreadAdvertiser([], 'unittest.multitest.ThreadAdvertiser1')
		a2 = minusconf.ThreadAdvertiser([], 'unittest.multitest.ThreadAdvertiser2')
		
		self._runMultiTest([
			(a1, [self.svc1, self.svc2, self.svc3]),
			(a2, [self.svc3, self.svc4, self.svc5]),
			], self.svc2.stype)
	
	def testMultiMultiprocessingAdvertisers(self):
		a1 = minusconf.MultiprocessingAdvertiser([], 'unittest.multitest.MultiprocessingAdvertiser1')
		a2 = minusconf.MultiprocessingAdvertiser([], 'unittest.multitest.MultiprocessingAdvertiser2')
		
		self._runMultiTest([
			(a1, [self.svc1, self.svc2, self.svc3]),
			(a2, [self.svc3, self.svc4, self.svc5]),
			], self.svc2.stype)
	
	def testMultiCombinedAdvertisers(self):
		mpa1 = minusconf.MultiprocessingAdvertiser([], 'unittest.multictest.MultiprocessingAdvertiser1')
		mpa2 = minusconf.MultiprocessingAdvertiser([], 'unittest.multictest.MultiprocessingAdvertiser2')
		ta1 = minusconf.ThreadAdvertiser([], 'unittest.multictest.ThreadAdvertiser1')
		ta2 = minusconf.ThreadAdvertiser([], 'unittest.multictest.ThreadAdvertiser2')
		ta3 = minusconf.ThreadAdvertiser([], 'unittest.multictest.ThreadAdvertiser3')
		
		self._runMultiTest([
			(mpa1, [self.svc1, self.svc2, self.svc3]),
			(mpa2, [self.svc3]),
			(ta1, [self.svc2, self.svc4]),
			(ta2, [self.svc1, self.svc5]),
			(ta3, []),
			], self.svc2.stype)
	
	def testInetPton(self):
		bts = minusconf._compat_bytes
		testVals = [
			(socket.AF_INET, '1.2.3.4', bts('\x01\x02\x03\x04')),
			(socket.AF_INET, '255.254.253.252', bts('\xff\xfe\xfd\xfc')),
			(socket.AF_INET6, '::', bts('\x00')*16),
			(socket.AF_INET6, '::1', bts('\x00')*15 + bts('\x01')),
			(socket.AF_INET6, '100::', bts('\x01') + bts('\x00')*15),
			(socket.AF_INET6, '0100::', bts('\x01') + bts('\x00')*15),
			(socket.AF_INET6, '1000::', bts('\x10') + bts('\x00')*15),
			(socket.AF_INET6, 'ff25::12:2:254.232.3.4', bts('\xff\x25\x00\x00\x00\x00\x00\x00\x00\x12\x00\x02\xfe\xe8\x03\x04')),
			(socket.AF_INET6, 'ffff:2:3:4:ffff::', bts('\xff\xff\x00\x02\x00\x03\x00\x04\xff\xff') + bts('\x00') * 6),
			]
		
		invalidVals = [
			(socket.AF_INET, '1.2.3'),
        		(socket.AF_INET, '1.2.3.4.5'),
			(socket.AF_INET, '301.2.2.2'),
			(socket.AF_INET, '::1.2.2.2'),
			(socket.AF_INET6, '1:2:3:4:5:6:7'),
			(socket.AF_INET6, '1:2:3:4:5:6:7:'),
			(socket.AF_INET6, ':2:3:4:5:6:7:8'),
			(socket.AF_INET6, '1:2:3:4:5:6:7:8:9'),
			(socket.AF_INET6, '1:2:3:4:5:6:7:8:'),
			(socket.AF_INET6, '1::3:4:5:6::8'),
			(socket.AF_INET6, 'a:'),
			(socket.AF_INET6, ':'),
			(socket.AF_INET6, ':::'),
			(socket.AF_INET6, '::a:'),
			(socket.AF_INET6, ':a::'),
			(socket.AF_INET6, '1ffff::'),
			(socket.AF_INET6, '0xa::'),
			(socket.AF_INET6, '1:2:3:4:5:6:300.2.3.4'),
			(socket.AF_INET6, '1:2:3:4:5:6:1a.2.3.4'),
			(socket.AF_INET6, '1:2:3:4:5:1.2.3.4:8'),
			]
		
		for ptonf in (minusconf._inet_pton, minusconf._compat_inet_pton):
			for (family, arg, expected) in testVals:
				self.assertEquals(ptonf(family, arg), expected)
			
			for (family, arg) in invalidVals:
				self.assertRaises((ValueError, socket.error), ptonf, family, arg)
	
	def testResolveAddrs(self):
		ra = minusconf._resolve_addrs
		def testResolveTo(rares, expected_addr, fam=socket.AF_INET):
			fr = rares[0] # first result
			self.assertEquals(fam, fr[0])
			self.assertEquals(minusconf._inet_pton(fam, fr[1][0]), minusconf._inet_pton(fam, expected_addr))
		
		# Test auto conversion
		if MinusconfUnitTest._testIPv6Support():
			testResolveTo(ra(['1.2.3.4'], None, False, [socket.AF_INET6]), '::ffff:1.2.3.4', socket.AF_INET6)
		testResolveTo(ra(['1.2.3.4'], None, False, [socket.AF_INET]), '1.2.3.4')
		
		self.assertEquals(ra(['::1::2', '1.2.3.4', '::2::1'], None, True), [(socket.AF_INET, ('1.2.3.4', 0), socket.AF_INET, '1.2.3.4')])
		self.assertRaises(socket.gaierror, ra, ['::1::2'], None, False)
	
	def testNUL(self):
		optlen = 4
		for i in range(optlen):
			toptions = ['x'] * optlen
			toptions[i] = 'null\x00byte'
			
			self.assertRaises(ValueError, minusconf.Service, *toptions)
		
		optlen = 3
		for i in range(optlen):
			toptions = ['x'] * optlen
			toptions[i] = 'null\x00byte'
			
			self.assertRaises(ValueError, minusconf.Seeker, *toptions)
		
		self.assertRaises(ValueError, minusconf.Advertiser, [], 'advertiser\x00name')
	
	def testIntPort(self):
		return # TODO
		svc = minusconf.Service('stype', 42, 'sname')
		x = 'a' + self._sharp_s + str(svc) + repr(svc)
	
	def testSeekerSanity(self):
		stype = 'stype ' + self._sharp_s
		aname = 'aname ' + self._sharp_s
		sname = 'sname ' + self._sharp_s + ' (wienerlicious)'
		s = minusconf.Seeker(stype, aname, sname)
		
		self.assertEquals(s.stype, stype)
		self.assertEquals(s.aname, aname)
		self.assertEquals(s.sname, sname)
		
		s.stype = stype
		s.aname = aname
		s.sname = sname
		
		self.assertEquals(s.stype, stype)
		self.assertEquals(s.aname, aname)
		self.assertEquals(s.sname, sname)
	
	def testMalformed(self):
		return #TODO
	
	def _runSingleConcurrentAdvertiserTest(self, advertiser):
		advertiser.start_blocking()
		
		self._runTestSeek([])
		
		advertiser.services.append(self.svc1)
		self._runTestSeek([self.svc1], self.svc1.stype)
		
		advertiser.services.append(self.svc2)
		self._runTestSeek([self.svc1], self.svc1.stype)
		self._runTestSeek([self.svc2], self.svc2.stype)
		
		advertiser.services.append(self.svc3)
		self.assertEquals(self.svc2.stype, self.svc3.stype)
		self._runTestSeek([self.svc1], self.svc1.stype)
		self._runTestSeek([self.svc2, self.svc3], self.svc2.stype)
		
		advertiser.stop_blocking()
		
		self._runTestSeek([], self.svc1.stype)
		self._runTestSeek([], self.svc1.stype)
	
	def _runTestSeek(self, services, stype=None, timeouts=[0.01,0.1,0.5,1.0]):
		if stype == None:
			if len(services) > 0:
				stype = services[0].stype
			else:
				stype = ''
		
		s = minusconf.Seeker(stype)
		svc_eq = lambda svc, exp: (svc.sname == exp.sname and svc.stype == exp.stype and svc.port == exp.port)
		svc_in = lambda svc, svcs: any((svc_eq(svc, s) for s in svcs))
		def find_callback(seeker,svcat):
			if not svc_in(svcat, services):
				raise AssertionError('Got ' + repr(svcat) + ', expected one of ' + repr(services))
			self.assertTrue(svcat.aname != '')
		s.find_callback = find_callback
		s.error_callback = lambda seeker,serveraddr,errorstr: self.fail('Got error ' + repr(errorstr) + ' from ' + repr(serveraddr))
		
		# TODO special-case services == []
		for to in timeouts:
			try:
				s.timeout = to
				s.run()
				
				for svc in services:
					if not svc_in(svc, s.results):
						raise AssertionError('Missing ' + repr(svc) + ', got ' + repr(s.results))
				
				break
			except AssertionError:
				if to == max(timeouts):
					raise
		
		return s.results
	
	def _runMultiTest(self, advertiser_services, stype):
		try:
			for av,svcs in advertiser_services:
				av.start_blocking()
			
			self._runTestSeek([], stype)
			
			expected_services = set()
			for av,svcs in advertiser_services:
				av.services += svcs
				expected_services.update(filter(lambda svc: svc.stype == stype, svcs))
			
			self._runTestSeek(expected_services, stype)
			
			for av,svcs in advertiser_services:
				av.stop_blocking()
			
			self._runTestSeek([], stype)
		finally:
			for av,svcs in advertiser_services:
				try:
					av.stop_blocking()
				except:
					pass
	
	@staticmethod
	def _testIPv6Support():
		if not socket.has_ipv6:
			return False
		
		try:
			socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
		except socket.gaierror:
			return False
		
		return True

if __name__ == '__main__':
	unittest.main()
