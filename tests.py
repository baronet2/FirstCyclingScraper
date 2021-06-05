import unittest
from unittest.mock import patch

import first_cycling_api


class TestRider(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.pidcock = first_cycling_api.Rider(65025)
		cls.pidcock.get_year(2020)
		
	@classmethod
	def tearDownClass(cls):
		pass

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_name(self):
		hd = self.pidcock.header_details
		self.assertEqual(hd['name'], 'Tom Pidcock')
		self.assertEqual(hd['twitter_handle'], 'Tompid')

	def test_sidebar_details(self):
		sd = self.pidcock.sidebar_details
		self.assertEqual(sd['nation'], 'Great Britain')
		self.assertEqual(str(sd['date_of_birth']), '1999-07-30')
		self.assertEqual(sd['agency'], 'Trinity Sports Management')

	def test_year_results(self):
		self.assertEqual(self.pidcock.results[2020].results_df.shape[0], 30)

if __name__ == '__main__':
	unittest.main()