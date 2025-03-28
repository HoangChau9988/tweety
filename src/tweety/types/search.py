import time
from . import Tweet, Excel, User, deprecated


class Search(dict):
    def __init__(self, keyword, http, pages=1, filter_=None, wait_time=2, cursor=None):
        super().__init__()
        self.tweets = []
        self.users = []
        self.keyword = keyword
        self.cursor = cursor
        self.is_next_page = True
        self.http = http
        self.filter = filter_.lower().strip() if filter_ else None
        self._search(pages, wait_time)

    def __repr__(self):
        return "Search(keyword={}, count={}, filter={})".format(
            self.keyword,
            len(self.users) if self.filter == "users" else len(self.tweets),
            self.filter
        )

    def get_next_page(self):
        _tweets = []
        if self.is_next_page:
            response = self.http.perform_search(self.keyword, self.cursor, self.filter)

            thisTweets = self._parse_response(response)

            self['is_next_page'] = self.is_next_page
            self['cursor'] = self.cursor

            return thisTweets

    def _parse_response(self, response):
        thisObjects = []
        if self.filter == "users":
            for raw_user in response.json()['globalObjects']['users'].values():
                try:
                    user = User(raw_user, 2)
                    self.users.append(user)
                    thisObjects.append(user)
                except:
                    pass
            self['users'] = self.users
        else:
            users = response.json()['globalObjects']['users']
            for tweet_id, raw_tweet in response.json()['globalObjects']['tweets'].items():
                try:
                    raw_tweet['rest_id'], raw_tweet['core'] = tweet_id, users.get(str(raw_tweet['user_id']))
                    tweet = Tweet(response, raw_tweet, self.http, False, True)
                    self.tweets.append(tweet)
                    thisObjects.append(tweet)
                except:
                    pass

            self['tweets'] = self.tweets
    
        # FIXME Temporarily disable pagination as its not working
        self.is_next_page = False
        return thisObjects

    def _get_cursor(self, response):
        if self.filter == "users":
            for i in response.json()['timeline']['instructions'][-1]['addEntries']['entries']:
                if str(i['entryId']).split("-")[0] == "cursor":
                    if i['content']['operation']['cursor']['cursorType'] == "Bottom":
                        newCursor = i['content']['operation']['cursor']['value']
                        if newCursor == self.cursor:
                            return False
                        self.cursor = newCursor
                        return True
        else:
            for i in response.json()['timeline']['instructions'][0]['addEntries']['entries']:
                try:
                    if i['content']['operation']:
                        if i['content']['operation']['cursor']['cursorType'] == "Bottom":
                            newCursor = i['content']['operation']['cursor']['value']
                            if newCursor == self.cursor:
                                return False
                            self.cursor = newCursor
                            return True
                except:
                    pass
                try:
                    for j in response.json()['timeline']['instructions']:
                        for key in j.keys():
                            if key == "replaceEntry":
                                if j['replaceEntry']['entry']['content']['operation']['cursor']['cursorType'] == "Bottom":
                                    newCursor = j['replaceEntry']['entry']['content']['operation']['cursor']['value']
                                    if newCursor == self.cursor:
                                        return False
                                    self.cursor = newCursor
                                    return True
                except:
                    pass
        return False

    def _search(self, pages, wait_time):
        for page in range(1, int(pages) + 1):
            this_tweets = self.get_next_page()

            if self.is_next_page and page != pages:
                time.sleep(wait_time)

    def to_xlsx(self, filename=None):
        if self.filter == "users":
            return AttributeError("to_xlsx with 'users' filter isn't supported yet")
        return Excel(self.tweets, f"search-{self.keyword}", filename)

    @deprecated
    def to_dict(self):
        return self.tweets

    def __getitem__(self, index):
        if self.filter == "users":
            return self.users[index]
        else:
            return self.tweets[index]

    def __iter__(self):
        if self.filter == "users":
            for _user in self.users:
                yield _user
        else:
            for _tweet in self.tweets:
                yield _tweet
