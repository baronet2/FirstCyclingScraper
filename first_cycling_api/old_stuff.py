# Rankings ----
from .utilities import *

class Ranking:
    """
    A framework to store Ranking data.

    Attributes
    ----------
    url : str
        The url for the rankings page
    df : pd.DataFrame
        A dataframe containing the rankings from the page, or None if there is no data for that page
    """

    def __init__(self, url=None, ranking_type=1, ranking_category=1, year=2021, country=None, u23='', page_num=1):
        """
        Initialize a Ranking object.

        Arguments
        ---------
        url : str
            The URL for the rankings page. If url is provided, all other arguments are ignored.
        ranking_type : int
            The ranking type (1: 'World', 2: 'One-day race', 3: 'Stage race', 4: 'Africa Tour', 5: 'America Tour', 6: 'Europe Tour', 7: 'Asia Tour', 8: 'Oceania Tour', 99: 'Women')
        ranking_category : int
            The ranking category (1: 'Riders', 2: 'Teams', 3: 'Nations')
        year : int or str
            If int, returns ranking for that particular year, e.g. '2021'
            If str, format as "yyyy-w" with year and week, e.g. '2021-7' returns the rankings in week 7 of 2021
        country : str
            The three-letter code for the country to filter results to, e.g. 'BEL'
        u23 : int
            If 1, include results for under-23 riders only
        page_num : int
            The page number of the ranking desired
        """

        if not url: # Prepare URL with appropriate headers
            url = "https://firstcycling.com/ranking.php?"
            url += 'rank=' + str(ranking_type)
            url += '&h=' + str(ranking_category)
            url += '&y=' + str(year)
            url += ('&cnat=' + str(country)) if country else ''
            url += '&u23=' + str(u23)
            url += '&page=' + str(page_num)

        # Load webpage
        self.url = url
        page = requests.get(url)
        soup = bs4.BeautifulSoup(page.text, 'html.parser')

        # Parse rankings from page
        rankings_table = soup.find('table', {'class': 'tablesorter sort'})
        self.df = table_of_riders_to_df(rankings_table)

    def __repr__(self):
        return "Ranking(" + self.url + ")"

    def get_json(self):
        return json.dumps(self, default=ComplexHandler)

    def to_json(self):
        d = vars(self).copy()
        d['df'] = self.df.to_json() if self.df is not None else None
        return d

# rider.py --------------------------------
class Rider(FirstCyclingObject):
    """
    Framework to store information about a particular rider.
    
    Attributes
    ----------
    rider_id : int
        FirstCycling.com id for the rider used in the url
    details : RiderDetails
        Rider's basic profile information
    year_details : dict(int : RiderYearDetails)
        Dictionary mapping years to rider's details for that year
    results : dict(int : ResultsTable)
        Dictionary mapping years to rider's results for that year
    """

    def __init__(self, rider_id, name=None, nation=None):
        self.ID = rider_id
        self.year_details = {}
        self.name = None

    def get_details(self, years=None, overwrite=False):
        if not years:
            if not self.name: # First request for rider
                details = RiderYear(self.ID)
                self._get_rider_details(details.response)
                self.year_details[details.year] = details
            years = self.years_active
        
        if not overwrite: # Remove previously loaded years
            years = [year for year in years if year not in self.year_details.keys()]
        for year in years:
            self.year_details[year] = RiderYear(self.ID, year)

    def _get_rider_details(self, response):
        soup = bs4.BeautifulSoup(response, 'html.parser')

        # Add basic rider information
        self.name = soup.h1.text
        self.current_team = soup.p.text.strip()
        self.current_team = soup.p.text.strip() if self.current_team else None
        self.twitter_handle = soup.find('p', {'class': 'left'}).a['href'].split('/')[3] if soup.find('p', {'class': 'left'}).a else None
        
        # Find table with rider details on right sidebar
        details_table = soup.find('table', {'class': 'tablesorter notOddEven'})
        details_df = pd.read_html(str(details_table))[0]
        details = pd.Series(details_df.set_index(0)[1])
        
        # Load details from table into attributes
        self.nation = details['Nationality']
        self.date_of_birth = parse(details['Born'].rsplit(maxsplit=1)[0]).date() if 'Born' in details else None
        self.height = float(details['Height'].rsplit(maxsplit=1)[0]) if 'Height' in details else None
        self.WT_wins = int(details['WorldTour'].split()[0]) if 'WorldTour' in details else 0
        self.UCI_wins = int(details['UCI'].split()[0]) if 'UCI' in details else 0
        self.UCI_rank = int(details['UCI Ranking']) if 'UCI Ranking' in details else None
        self.agency = details['Agency'] if 'Agency' in details else None

        # Load rider's strengths from details table
        if 'Strengths' in details:
            tr = details_table.find_all('tr')[-1]
            td = tr.find_all('td')[1]
            self.strengths = [x.strip() for x in td if isinstance(x, bs4.element.NavigableString)]
        else:
            self.strengths = []
        
        # Get list of all years for which results available
        self.years_active = [int(o['value']) for o in soup.find('select').find_all('option') if o['value']]

    def _to_json(self):
        d = vars(self).copy()
        d['date_of_birth'] = str(d['date_of_birth'])
        return d

    def get_results_dataframe(self, expand=False):
        """ Return pd.DataFrame of all loaded result for rider, sorted in reverse chronological order """
        return pd.concat([result.to_dataframe(expand=expand) for result in self.results.values()]).sort_values('date', ascending=False)


# ------------------------------
class RiderResultsTable(FirstCyclingObject):
	def __init__(self, table):
		self.raw = table
		self.results = [RiderResult(row) for row in results_table.tbody.find_all('tr')] if results_table else []
        self.results = [x for x in self.results if vars(x)]


class RiderResult(FirstCyclingObject):
	def __init__(self, date, race_name, race_id, race_cat)


    def __init__(self, row):
        """
        Parameters
        ----------
        row : bs4.element.Tag
            tr from race results table
        """

        # Get tds from tr
        tds = row.find_all('td')
        if len(tds) < 7: # No data
            return
        elif len(tds) == 7: # Missing UCI points column - prior to 2018
            tds.append(None)
        date, date_alt, result, gc_standing, icon, race_td, cat, uci = tuple(tds)
        
        # Parse race date
        try:
            self.date = parse(date.text).date()
        except ParserError: # Result with uncertain date, use January/1st by default
            year, month, day = date.text.split('-')
            month = '01' if not int(month) else month
            day = '01' if not int(day) else day
            fixed_date = year + '-' + month + '-' + day
            self.date = parse(fixed_date).date()

        # Load basic result details
        self.result = int(result.text) if result.text.isnumeric() else result.text
        self.gc_standing = int(gc_standing.text) if gc_standing.text else None
        self.icon = icon.img['src'].split('/')[-1] if icon.img else None
        self.cat = cat.text
        self.uci_points = (float(uci.text) if uci.text != '-' else 0) if uci else None
        
        # Parse td containing race name
        links = race_td.find_all('a')
        self.race_id = race_link_to_race_id(links[0])
        imgs = race_td.find_all('img')
        self.race_country_code = img_to_country_code(imgs[0])
        self.full_name = race_td.text.strip().replace('\n', ' ').replace('\t', '').replace('\r', '')
        tokens = [x.strip() for x in self.full_name.split('|')]
        self.name = tokens[0]
        if len(imgs) == 2: # Championships edition
            self.edition_country_code = img_to_country_code(imgs[1])
            self.edition_city = tokens[1]
        else:
            if len(links) == 2: # Stage
                self.stage_num = race_link_to_stage_num(links[0])
            elif len(tokens) == 2: # Classification (except GC)
                self.classification = tokens[1]


    def __str__(self):
        return str(self.date.year) + ' ' + self.full_name

    def __repr__(self):
        return "RaceResult(" + self.full_name + ", " + str(self.date.year) + ")"

    def get_json(self):
        return json.dumps(self, default=ComplexHandler)

    def to_json(self):
        d = vars(self).copy()
        d['date'] = str(d['date'])
        return d


# results.py -------------------------------
# Load information on right sidebar
info_table = soup.find('table', {'class': 'tablesorter notOddEven'})
details_df = pd.read_html(str(info_table))[0]
details = pd.Series(details_df['Information.1'].values, index=details_df['Information'])
soup_details = pd.Series(info_table.find_all('tr')[1:], index=details.index)

# Get nation and start/end cities
self.nation = img_to_country_code(soup_details['Nation' if 'Nation' in details.index else 'Where'].img)

if 'Where' in details.index:
    if ' -> ' in details['Where']:
        self.start_city, self.end_city = details['Where'].split(' -> ')
    else:
        self.start_city = self.end_city = details['Where']
else:
    self.start_city = self.end_city = None

if 'Nation' in details.index and len(soup_details['Nation'].find_all('img')) > 1: # Edge case: olympic games
    self.nation = img_to_country_code(soup_details['Nation'].find_all('img')[-1])
    self.start_city = self.end_city = soup_details['Nation'].find_all('img')[-1].next_sibling.strip()

# Get date
if 'Date' in details.index:
    if ' - ' in details['Date']:
        self.start_date, self.end_date = tuple([parse(x + ', ' + str(self.year)).date() for x in details['Date'].split(' - ')])
    else:
        self.start_date = self.end_date = parse(details['Date'] + ', ' + str(self.year)).date()
else:
    self.start_date = self.end_date = None

# Get additional race information
self.distance = float(details['Distance'].split()[0]) if 'Distance' in details.index else None
self.cat = details['CAT'] if 'CAT' in details.index else None
self.stage_num = int(''.join([x for x in details['What'] if x.isnumeric()])) if 'What' in details.index else None

if 'What' in details.index and 'Prologue' in details['What']:
    self.stage_num = 0

# Find profile information
self.profile = None
if 'Distance' in details.index:
    self.profile = img_to_profile(soup_details['Distance'].img) if soup_details['Distance'].img else None
elif 'What' in details.index:
    self.profile = img_to_profile(soup_details['What'].img) if soup_details['What'].img else None

# Classification leaders after stage
self.classification_leaders = {}
for classification in ['Leader', 'Youth', 'Points', 'Mountain', 'Combative']: # TODO Any others?
    if classification in details:
        self.classification_leaders[classification] = rider_link_to_id(soup_details[classification].a) # TODO save as Rider without loading page?

def __repr__(self):
    return "Results(" + self.race_name + ", " + str(self.year) + ")"

def get_json(self):
    return json.dumps(self, default=ComplexHandler)

def to_json(self):
    d = vars(self).copy()
    d['start_date'] = str(d['start_date'])
    d['end_date'] = str(d['end_date'])
    d['df'] = self.df.to_json() if self.df is not None else None
    d['standings'] = {k: v.to_json() for k, v in d['standings'].items()}
    return d



# Results dataframe ----
# Race type/category booleans
series['uci_race'] = self.cat in uci_categories
series['championship'] = self.cat in championships_categories
series['u23'] = self.cat in U23_categories
series['cx'] = self.name.startswith('CX -')
series['juniors'] = self.cat.startswith('J')
series['one_day'] = self.cat in one_day_categories

# Parse icon for details on race type and profile using colours and icon_map static variables
series['jersey_colour'] = None
series['profile'] = None

if self.icon:
for col in colour_icons:
    if (col + '.') in self.icon:
        series['jersey_colour'] = col.capitalize()
        break

if not series['jersey_colour']:
    if self.icon in profile_icon_map:
        series['profile'] = profile_icon_map[self.icon]

series['ttt'] = series['profile'] == 'TTT'
series['itt'] = 'ITT' in series['profile'] if series['profile'] else None
series['tt'] = series['itt'] or series['ttt']
series['mtf'] = series['profile'].endswith(' MTF') if series['profile'] else None
series['mountain'] = 'Mountain' in series['profile'] if series['profile'] else None
series['hilly'] = 'Hilly' in series['profile'] if series['profile'] else None
series['flat'] = 'Flat' in series['profile'] if series['profile'] else None
series['cobbled'] = 'Cobbles' in series['profile'] if series['profile'] else None