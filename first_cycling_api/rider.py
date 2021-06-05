"""
Rider
=========

Provides a framework to load and store data on riders.

"""

from .utilities import *

# Endpoints ----
class _RiderEndpoint(Endpoint):
	_base_url = 'https://firstcycling.com/rider.php'

	def _get_years_active(self):
		soup = bs4.BeautifulSoup(self.response, 'html.parser')
		return [int(o['value']) for o in soup.find('select').find_all('option') if o['value']]

	def _get_header_details(self):
		soup = bs4.BeautifulSoup(self.response, 'html.parser')
		header_details = {}
		header_details['name'] = soup.h1.text
		header_details['current_team'] = soup.p.text.strip() if soup.p.text.strip() else None
		header_details['twitter_handle'] = soup.find('p', {'class': 'left'}).a['href'].split('/')[3] if soup.find('p', {'class': 'left'}).a else None
		return header_details
	
	def _get_sidebar_details(self):
		soup = bs4.BeautifulSoup(self.response, 'html.parser')

		# Find table with rider details on right sidebar
		details_table = soup.find('table', {'class': 'tablesorter notOddEven'})
		details_df = pd.read_html(str(details_table))[0]
		details = pd.Series(details_df.set_index(0)[1])
		
		# Load details from table into attributes
		sidebar_details = {}
		sidebar_details['nation'] = details['Nationality']
		sidebar_details['date_of_birth'] = parse_date(details['Born'].rsplit(maxsplit=1)[0]) if 'Born' in details else None
		sidebar_details['height'] = float(details['Height'].rsplit(maxsplit=1)[0]) if 'Height' in details else None
		sidebar_details['WT_wins'] = int(details['WorldTour'].split()[0]) if 'WorldTour' in details else 0
		sidebar_details['UCI_wins'] = int(details['UCI'].split()[0]) if 'UCI' in details else 0
		sidebar_details['UCI_rank'] = int(details['UCI Ranking']) if 'UCI Ranking' in details else None
		sidebar_details['agency'] = details['Agency'] if 'Agency' in details else None

		# Load rider's strengths from details table
		if 'Strengths' in details:
			tr = details_table.find_all('tr')[-1]
			td = tr.find_all('td')[1]
			sidebar_details['strengths'] = [x.strip() for x in td if isinstance(x, bs4.element.NavigableString)]
		else:
			sidebar_details['strengths'] = []

		return sidebar_details

class RiderYearResults(ParsedEndpoint, _RiderEndpoint):
	"""
	An endpoint for rider's results in a certain year. Extends ParsedEndpoint.

	Attributes
	----------
	year_details : dict
		The year-specific rider details from the page.
	results_df : pd.DataFrame
		A DataFrame containing the rider's results from the year.
	"""
	_params = {'y': current_year}

	def _parse_soup(self):
		self._get_year_details()
		self._get_year_results()

	def _get_year_details(self):
		# Find table with details
		details_table = self.soup.find('table', {'class': 'tablesorter notOddeven'})

		# Parse table with details
		if details_table:
			rider_year_details = [s.strip() for s in details_table.text.replace('\n', '|').split('|') if s.strip()]
			rider_year_details = [x.split(':') if ':' in x else ['UCI Points', x.split()[0].replace('.', '')] for x in rider_year_details]
			rider_year_details = dict(rider_year_details)
		else:
			rider_year_details = {}

		# Load attributes
		self.year_details = {}
		self.year_details['Team'] = rider_year_details['Team'].strip() if 'Team' in rider_year_details else None
		self.year_details['Division'] = rider_year_details['Division'].strip() if 'Division' in rider_year_details else None
		self.year_details['UCI Ranking'] = int(rider_year_details['UCI Ranking']) if 'UCI Ranking' in rider_year_details else None
		self.year_details['UCI Points'] = int(rider_year_details['UCI Points']) if 'UCI Points' in rider_year_details and rider_year_details['UCI Points'].strip() else 0
		self.year_details['UCI Wins'] = int(rider_year_details['UCI Wins'].replace('-', '0')) if 'UCI Wins' in rider_year_details and rider_year_details['UCI Wins'].strip() else 0
		self.year_details['Race days'] = int(rider_year_details['Race days'].replace('-', '0')) if 'Race days'in rider_year_details and rider_year_details['Race days'].strip() else 0
		self.year_details['Distance'] = int(rider_year_details['Distance'].split()[0].replace('.', '').replace('-', '0')) if 'Distance' in rider_year_details else 0

	def _get_year_results(self):
		# Find table with results
		table = self.soup.find('table', {'class': "sortTabell tablesorter"})
		self.results_df = parse_table(table)

class RiderBestResults(_RiderEndpoint):
	""" Extends Endpoint. """
	_params = {'high': 1}

class RiderVictories(_RiderEndpoint):
	""" Extends Endpoint. """
	_params = {'high': 1, 'k': 1, 'uci': 0}

class RiderMonumentResults(_RiderEndpoint):
	""" Extends Endpoint. """
	_params = {'high': 1, 'k': 3}

class RiderRaceHistory(_RiderEndpoint):
	""" Extends Endpoint. """
	_params = {'ra': None}

class RiderTeamAndRanking(_RiderEndpoint):
	""" Extends Endpoint. """
	_params = {'stats': 1}

class RiderRaceHistory(_RiderEndpoint):
	""" Extends Endpoint. """
	_params = {'stats': 1, 'k': 1}

class RiderOneDayRaces(_RiderEndpoint):
	""" Extends Endpoint. """
	_params = {'stats': 1, 'k': 2}

class RiderStageRaces(_RiderEndpoint):
	""" Extends Endpoint. """
	_params = {'stats': 1, 'k': 3}

class RiderTeams(_RiderEndpoint):
	""" Extends Endpoint. """
	_params = {'teams': 1}


# Rider ----
class Rider(FirstCyclingObject):
	"""
	A wrapper class to load and store information on riders.

	Attributes
	----------
	ID : int
		The firstycling.com ID for the rider (can be found in the URL for their profile page).
	header_details : dict
		A dictionary listing information from the header of rider profile pages.
	sidebar_details : pd.Series
		A series listing information from the right sidebar of rider profile pages.
	years_active : list of int
		A list of the years in which the rider was active.
	results : dict {int: RiderYearResults}
		The rider's results for each year.
	race_history : dict {int: RiderRaceHistory}
		The rider's history at the race with the given ID.
	"""

	def __init__(self, rider_id):
		""" Initialize a Rider.

		Parameters
		----------
		rider_id : int
			The firstycling.com ID for the rider (can be found in the URL for their profile page)
		"""
		self.ID = rider_id
		self.header_details = None
		self.sidebar_details = None
		self.years_active = None
		self.results = {}
		self.race_history = {}

	def _get_general_info(self, endpoint):
		if not self.header_details:
			self.header_details = endpoint._get_header_details()
			self.sidebar_details = endpoint._get_sidebar_details()
			self.years_active = endpoint._get_years_active()

	def _prepare_endpoint_params(self, kwargs):
		kwargs['r'] = self.ID
		return kwargs

	def get_years(self, years=None):
		"""
		Get rider details and results for given years.

		Parameters
		----------
		years : list of int
			List of years for which to collect information.
			If None, collects information for all years in which rider was active.

		Returns
		-------
		results : dict {int: RiderYearResults}
			Results for selected years.
		"""
		if years is None:
			if not self.years_active: # Get first unloaded year
				self.get_year()
			years = [year for year in self.years_active if year not in self.results]
		return {y: self.get_year(year) for y in years}

	def get_year(self, year=None):
		"""
		Get rider details and results for given year.

		Parameters
		----------
		year : int
			Year for which to collect information.
			If None, collects information for latest unloaded year in which rider was active,
			or if all years already loaded returns latest year.

		Returns
		-------
		RiderYearResults
		"""
		if year:
			return self._get_endpoint(RiderYearResults, 'results', year, y=year)
		elif self.years_active:
			unloaded_years = [year for year in self.years_active if year not in self.results]
			if unloaded_years: # Load first unloaded year
				year = unloaded_years[0]
				return self._get_endpoint(RiderYearResults, 'results', year, y=year)
			else: # Load most recent year
				return self.results[max(self.years_active)]
		else: # Determine year after request
			year_results = RiderYearResults(self.ID)
			self.results[year_results.year] = year_results
			self._get_general_info(year_results)
			return year_results

	def get_best_results(self):
		""" Get the rider's best results.

		Returns
		-------
		RiderBestResults
		"""
		return self._get_endpoint(RiderBestResults, 'best_results')

	def get_victories(self):
		""" Get the rider's victories. 

		Returns
		-------
		RiderVictories
		"""
		return self._get_endpoint(RiderVictories, 'victories')

	def get_uci_victories(self):
		""" Get the rider's UCI victories. 

		Returns
		-------
		RiderVictories
		"""
		return self._get_endpoint(RiderVictories, 'uci_victories', uci=1)

	def get_monument_results(self):
		""" Get the rider's results in monuments. 

		Returns
		-------
		RiderMonumentResults
		"""
		return self._get_endpoint(RiderMonumentResults, 'monument_results')

	def get_race_history(self, race_id):
		"""
		Get the rider's history at a certain race.

		Parameters
		----------
		race_id : int
			The firstcycling.com ID for the desired race, from the race profile URL.

		Returns
		-------
		RiderRaceHistory
		"""
		return self._get_endpoint(RiderRaceHistory, 'race_history', race_id, ra=race_id)

	def get_team_and_ranking(self):
		""" Get the rider's historical teams and rankings. 

		Returns
		-------
		RiderTeamAndRanking
		"""
		return self._get_endpoint(RiderTeamAndRanking, 'team_and_ranking')

	def get_one_day_races(self):
		""" Get the rider's results at major one-day races. 

		Returns
		-------
		RiderOneDayRaces
		"""
		return self._get_endpoint(RiderOneDayRaces, 'one_day_races')

	def get_stage_races(self):
		""" Get the rider's results at major stage races. 

		Returns
		-------
		RiderStageRaces
		"""
		return self._get_endpoint(RiderStageRaces, 'stage_races')

	def get_teams(self):
		""" Get the rider's historical teams. 

		Returns
		-------
		RiderTeams
		"""
		return self._get_endpoint(RiderTeams, 'teams')