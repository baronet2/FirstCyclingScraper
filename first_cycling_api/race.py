"""
Race
=========

Provides a framework to load and store data on races and race editions.

"""

from .utilities import *

# Race Endpoints ----
class _RaceEndpoint(Endpoint):
	_base_url = 'https://firstcycling.com/race.php'

	def _get_header_details(self):
		soup = bs4.BeautifulSoup(self.response, 'html.parser')
		header_details = {}
		header_details['name'] = soup.h1.text.rsplit(' - ', maxsplit=1)[0] # Get race name, excluding year
		header_details['links'] = {a.img['src'].rsplit('/', maxsplit=1)[1][:-7]: a['href'] for a in soup.h1.parent.find_all('a')}
		if 'www' in header_details['links']:
			header_details['links']['website'] = header_details['links'].pop('www')
		return header_details

	def _get_editions(self):
		soup = bs4.BeautifulSoup(self.response, 'html.parser')
		return [int(o['value']) for o in soup.find('select', {'name': 'y'}).find_all('option') if o['value']]

class RaceOverview(_RaceEndpoint):
	""" Extends Endpoint. """
	_params = {'k': 0}

class RaceYearByYear(_RaceEndpoint):
	""" Extends Endpoint. """
	_params = {'k': 'X', 'j': 0}

class RaceVictoryTable(ParsedEndpoint, _RaceEndpoint):
	"""
	An endpoint for a race's victory table. Extends ParsedEndpoint.

	Attributes
	----------
	table : pd.DataFrame
		A DataFrame containing the victory table.
	"""
	_params = {'k': 'W'}

	def _parse_soup(self):
		self._get_victory_table()

	def _get_victory_table(self):
		victory_table = self.soup.find('table', {'class': 'tablesorter'})
		self.table = parse_table(victory_table)

class RaceStageVictories(ParsedEndpoint, _RaceEndpoint):
	"""
	An endpoint for a race's stage victories table. Extends ParsedEndpoint.

	Attributes
	----------
	table : pd.DataFrame
		A DataFrame containing the victory table.
	"""
	_params = {'k': 'Z'}

	def _parse_soup(self):
		self._get_stage_victory_table()

	def _get_stage_victory_table(self):
		victory_table = self.soup.find('table', {'class': 'test tablesorter'}) # TODO test
		self.table = parse_table(victory_table)

class RaceYoungestOldestWinners(_RaceEndpoint):
	""" Extends Endpoint. """
	_params = {'k': 'Y'}

# Race Edition Endpoints ----
class RaceEditionInformation(_RaceEndpoint):
	""" Extends Endpoint. """
	_params = {'k': 2}

class RaceEditionResults(ParsedEndpoint, _RaceEndpoint):
	"""
	An endpoint for a race edition's results. Extends ParsedEndpoint.

	Attributes
	----------
	results_table : pd.DataFrame
		A DataFrame containing the victory table.
	standings : dict {str : pd.DataFrame}
		For stage races, maps classification names to a DataFrame with the appropriate standings after the stage.
	"""
	_params = {'l': None, 'e': None}

	def _parse_soup(self):
		self._get_results_table()
		self._get_sidebar_information()

	def _get_results_table(self):
		results_table = self.soup.find('table', {'class': 'sortTabell tablesorter'})
		if not results_table:
			results_table = self.soup.find('table', {'class': 'sortTabell2 tablesorter'})
		self.results_table = parse_table(results_table)

		# Load all classification standings after stage
		divs = self.soup.find_all('div', {'class': "tab-content dummy"})
		self.standings = {div['id']: parse_table(div.table) for div in divs}

	def _get_sidebar_information(self): # TODO
		return

class RaceEditionStageProfiles(_RaceEndpoint):
	""" Extends Endpoint. """
	_params = {'e': 'all'}

class RaceEditionStartlistNormal(_RaceEndpoint):
	""" Extends Endpoint. """
	_params = {'k': 8}

class RaceEditionStartlistExtended(_RaceEndpoint):
	""" Extends Endpoint. """
	_params = {'k': 9}

# Race ----
class Race(FirstCyclingObject):
	"""
	A wrapper class to load and store information on races.

	Attributes
	----------
	ID : int
		The firstcycling.com ID for the race, as seen in the URL of the race page.
	header_details : dict
		A dictionary listing information from the header of race pages.
	edition_years : list of int
		A list of the years in which race editions took place.
	editions : dict {int: RaceEdition}
		The race editions for each year.
	overview : dict {int: RaceOverview}
		The race editions for each year.
	"""

	def __init__(self, race_id):
		""" Initialize a Race.

		Parameters
		----------
		race_id : int
			The firstycling.com ID for the rider (can be found in the URL for their profile page)
		"""
		self.ID = race_id
		self.header_details = None
		self.edition_years = None
		self.editions = {}
		self.overview = {}

	def _get_general_info(self, endpoint):
		if not self.header_details:
			self.header_details = endpoint._get_header_details()
			self.edition_years = endpoint._get_editions()

	def _prepare_endpoint_params(self, kwargs):
		kwargs['r'] = self.ID
		return kwargs

	def get_overviews(self, classifications=[0]):
		"""
		Get race overview for given classifications.

		Parameters
		----------
		classifications : list of int, default [0]
			List of classifications for which to collect information.
			See utilities.Classifications for possible numbers.

		Returns
		-------
		results : dict {int: RaceOverview}
			Overviews for selected classifications.
		"""
		return {c: self.get_overview(c) for c in classifications}

	def get_overview(self, classification):
		"""
		Get race overview for given classifications.

		Parameters
		----------
		classification : int
			Classification for which to collect information.
			See utilities.Classifications for possible inputs.

		Returns
		-------
		RaceOverview
		"""
		return self._get_endpoint(RaceOverview, 'overview', classification, k=classification)

	def get_year_by_years(self, classifications=[0]):
		"""
		Get year-by-year race statistics for given classifications.

		Parameters
		----------
		classifications : list of int, default [0]
			List of classifications for which to collect information.
			See utilities.Classifications for possible numbers.

		Returns
		-------
		results : dict {int: RaceOverview}
			Overviews for selected classifications.
		"""
		return {c: self.get_year_by_year(c) for c in classifications}

	def get_year_by_year(self, classification):
		"""
		Get year-by-year race statistics for given classification.

		Parameters
		----------
		classification : int
			Classification for which to collect information.
			See utilities.Classifications for possible inputs.

		Returns
		-------
		RaceOverview
		"""
		return self._get_endpoint(RaceYearByYear, 'year_by_year', classification, j=classification)

	def get_victory_table(self):
		"""
		Get race all-time victory table.

		Returns
		-------
		RaceVictoryTable
		"""
		return self._get_endpoint(RaceVictoryTable, 'victory_table')

	def get_stage_victories(self):
		"""
		Get race all-time stage victories.

		Returns
		-------
		RaceStageVictories
		"""
		return self._get_endpoint(RaceStageVictories, 'stage_victories')

	def get_youngest_oldest_winners(self):
		"""
		Get race all-time victory table.

		Returns
		-------
		RaceYoungestOldestWinners
		"""
		return self._get_endpoint(RaceYoungestOldestWinners, 'youngest_oldest_winners')

	def _get_edition_endpoint(self, year, method, **kwargs):
		""" Generalized method to load endpoints for race edition """
		if year not in self.editions:
			self.editions[year] = RaceEdition(self.ID, year)
		return method(self.editions[year], **kwargs)

	def get_edition_information(self, year):
		"""
		Get race edition information.

		Parameters
		----------
		year : int
			Year for which to obtain edition information.

		Returns
		-------
		RaceEditionInformation
		"""
		return self._get_edition_endpoint(year, RaceEdition.get_information)

	def get_edition_results(self, year, classification_num=None, stage_num=None):
		"""
		Get race edition results for given classification or stage.

		Parameters
		----------
		year : int
			Year for which to obtain edition information.
		classification_num : int
			Classification for which to collect information.
			See utilities.Classifications for possible inputs.
		stage_num : int
			Stage number for which to collect results, if applicable.
			Input 0 for prologue.

		Returns
		-------
		RaceEditionResults
		"""
		return self._get_edition_endpoint(year, RaceEdition.get_results, classification_num=classification_num, stage_num=stage_num)

	def get_edition_stage_profiles(self, year):
		"""
		Get race edition stage profiles.

		Parameters
		----------
		year : int
			Year for which to obtain edition information.

		Returns
		-------
		RaceEditionStageProfiles
		"""
		return self._get_edition_endpoint(year, RaceEdition.get_stage_profiles)

	def get_edition_startlist_normal(self, year):
		"""
		Get race edition startlist in normal mode.

		Parameters
		----------
		year : int
			Year for which to obtain edition information.

		Returns
		-------
		RaceEditionStartlistNormal
		"""
		return self._get_edition_endpoint(year, RaceEdition.get_startlist_normal)

	def get_edition_startlist_extended(self, year):
		"""
		Get race edition startlist in extended mode.

		Parameters
		----------
		year : int
			Year for which to obtain edition information.

		Returns
		-------
		RaceEditionStartlistExtended
		"""
		return self._get_edition_endpoint(year, RaceEdition.get_startlist_extended)


# RaceEdition ----
class RaceEdition(FirstCyclingObject):
	def __init__(self, race_id, year):
		self.ID = race_id
		self.year = year

	def _prepare_endpoint_params(self, kwargs):
		kwargs['r'] = self.ID
		kwargs['y'] = self.year
		return kwargs

	def get_information(self):
		return self._get_endpoint(RaceEditionInformation, 'information')

	def get_results(self, classification_num=None, stage_num=None): 
		key = 'results' + ('_' + classifications[classification_num] if classification_num else ('_stage_' + str(stage_num) if stage_num else ''))
		return self._get_endpoint(RaceEditionResults, key, l=classification_num, e=stage_num) # TODO update sidebar information if missing

	def get_stage_profiles(self):
		self._get_endpoint(RaceEditionStageProfiles, 'stage_profiles')

	def get_startlist_normal(self):
		self._get_endpoint(RaceEditionStartlistNormal, 'startlist_normal')

	def get_startlist_extended(self):
		self._get_endpoint(RaceEditionStartlistExtended, 'startlist_extended')