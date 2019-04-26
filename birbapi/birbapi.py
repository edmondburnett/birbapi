import requests
from urllib.parse import quote_plus
import time
import re
import logging
from ssl import SSLError
from requests_oauthlib import OAuth1
from birbapi.resource_urls import SEARCH_TWEETS, FAVORITES_CREATE, FAVORITES_DESTROY, \
    STATUSES_RETWEET, STATUSES_DESTROY, FRIENDSHIPS_CREATE, FRIENDSHIPS_DESTROY, STATUSES_UPDATE, \
    FRIENDS_IDS, FOLLOWERS_IDS, USERS_LOOKUP, USERS_SHOW, FRIENDSHIPS_SHOW, RATE_LIMIT_STATUS, \
    OAUTH_ACCESS_TOKEN, OAUTH_REQUEST_TOKEN


def timestr_to_timestamp(created_at):
    """ Convert a Twitter-supplied 'created_at' time field to a timestamp """
    regex = re.compile(r'(\+|\-)\d\d\d\d')
    match = regex.search(created_at)
    if not match:
        logging.warning('Twitter gave unsupported time string')
        return time.time()
    return time.mktime(time.strptime(created_at, '%a %b %d %H:%M:%S ' + match.group() + ' %Y'))


class TwitterError(Exception):
    def __init__(self, response):
        self.response_raw = response
        self.response    = response.json()
        self.http_code   = response.status_code
        self.error_msg   = self.get_msg()
        self.error_code  = self.get_code()

    def get_msg(self):
        error_msg = 'Unknown Twitter Error'
        if 'errors' in self.response:
            if len(self.response['errors']) > 0:
                if 'message' in self.response['errors'][0]:
                    error_msg = self.response['errors'][0]['message']
        return error_msg

    def get_code(self):
        error_code = 0
        if 'errors' in self.response:
            if len(self.response['errors']) > 0:
                if 'code' in self.response['errors'][0]:
                    error_code = self.response['errors'][0]['code']
        return error_code


class RequestsError(Exception):
    def __init__(self, msg=None):
        self.error_msg  = 'Requests Unknown/Catchall Error'
        if msg:
            self.error_msg = msg

    def __str__(self):
        return repr(self.error_msg)



class Twitter():
    """ A wrapper interface to the Twitter API """
    def __init__(self, conkey, consec, otoken=None, osecret=None, verifier=None, timeout=10, testing=False):
        self.consumer_key = conkey
        self.consumer_secret = consec
        self.oauth_token = otoken
        self.oauth_secret = osecret
        self.verifier = verifier
        self.timeout = timeout
        self.testing = testing

        # configure OAuth1 depending on what arguments are present
        if otoken is None or osecret is None:
            self.oauth = OAuth1(conkey, client_secret=consec)
        elif verifier is not None:
            self.oauth = OAuth1(conkey, client_secret=consec,
                    resource_owner_key=otoken, resource_owner_secret=osecret,
                    verifier=verifier)
        else:
            self.oauth = OAuth1(conkey, client_secret=consec,
                    resource_owner_key=otoken, resource_owner_secret=osecret)


    def build_uri(self, args_dict):
        uri = ''
        for key, value in list(args_dict.items()):
            uri = uri + '&' + '%s=%s' % (key, value)
        return uri


    def search_tweets(self, q, **kwargs):
        """ GET search/tweets

            q: Search query string
            **kwargs: Arbitrary number of keyword arguments as specified by
                      the Twitter API, such as:
                      lang='en', result_type='popular', count=25
        """
        # TODO: implement since_id on subsequent searches to avoid dupes?

        if 'lang' in kwargs:
            if kwargs['lang'] is None:
                del kwargs['lang']

        query = quote_plus(q)
        uri = self.build_uri(kwargs)
        try:
            response = requests.get(SEARCH_TWEETS + '?q=' + query + uri,
                    auth=self.oauth, timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def favorites_create(self, id):
        """ Add favorite specified by id """
        try:
            response = requests.post(FAVORITES_CREATE,
                    data={ 'id' : id }, auth=self.oauth, timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def favorites_destroy(self, id):
        """ Remove favorite specified by id """
        try:
            response = requests.post(FAVORITES_DESTROY,
                    data={ 'id' : id }, auth=self.oauth, timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200 or response.status_code != 404:
            raise TwitterError(response)
        return response


    def retweet(self, id):
        """ Retweet the status specified by id """
        argdict = { 'trim_user' : 1 }
        uri = self.build_uri(argdict)

        try:
            response = requests.post(STATUSES_RETWEET + str(id) + '.json' + '?' + uri,
                    auth=self.oauth, timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def statuses_destroy(self, id):
        """ Destroy the status or retweet specified by id """
        argdict = { 'trim_user' : 1 }
        uri = self.build_uri(argdict)

        try:
            response = requests.post(STATUSES_DESTROY + str(id) + '.json' + '?' + uri,
                    auth=self.oauth, timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def follow_user(self, user_id):
        """ Follow the user specified by user_id """
        try:
            response = requests.post(FRIENDSHIPS_CREATE,
                    data={ 'user_id' : user_id }, auth=self.oauth, timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def unfollow_user(self, user_id):
        """ Unfollow the user specified by user_id """
        try:
            response = requests.post(FRIENDSHIPS_DESTROY,
                    data={ 'user_id' : user_id }, auth=self.oauth, timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def send_tweet(self, status, reply_to=None, trim_user=1):
        """ Send the tweets.

            status: the text of the status update
            reply_to: the ID of an existing status being replied to (optional)
            trim_user: don't return full user object if 1 or true (optional)
        """
        try:
            if reply_to is None:
                response = requests.post(STATUSES_UPDATE,
                        data={ 'status' : status, 'trim_user' : trim_user }, auth=self.oauth,
                        timeout=self.timeout)
            else:
                response = requests.post(STATUSES_UPDATE,
                        data={ 'status' : status, 'in_reply_to_status_id' : reply_to, 'trim_user' : trim_user },
                        auth=self.oauth, timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def friends_ids(self, user_id, cursor=-1):
        """ Return list of IDs of each user the specified user is following
            Should be called from get_friends_list. """
        try:
            response = requests.get(FRIENDS_IDS + '?user_id=' + user_id +
                    '&cursor=' + str(cursor), auth=self.oauth, timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def get_friends_recursive(self, twitter_id, cursor=-1, friends_list=[]):
        """ Recursive function to assemble a list of users the specified
            user is following (friends).
        """
        if int(cursor) == 0 or len(friends_list) >= 75000:
            return { 'friends' : friends_list, 'cursor' : cursor }

        response = self.friends_ids(twitter_id, cursor)

        friends_json = response.json()
        cursor = friends_json['next_cursor_str']
        for id in friends_json['ids']:
            friends_list.append(str(id))

        return self.get_friends_recursive(twitter_id, cursor, friends_list)


    def followers_ids(self, user_id, cursor=-1):
        """ Return list of IDs of each user the specified user is following.
            Should only be called from get_followers_list.
        """
        try:
            response = requests.get(FOLLOWERS_IDS + '?user_id=' + user_id +
                    '&cursor=' + str(cursor), auth=self.oauth, timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def get_followers_recursive(self, twitter_id, cursor=-1, followers_list=[]):
        """ Recursive function to assemble a list of users who follow the
            specified user.
        """
        if int(cursor) == 0 or len(followers_list) >= 75000:
            return { 'followers' : followers_list, 'cursor' : cursor }

        response = self.followers_ids(twitter_id, cursor)

        followers_json = response.json()
        cursor = followers_json['next_cursor_str']
        for id in followers_json['ids']:
            followers_list.append(str(id))

        return self.get_followers_recursive(twitter_id, cursor, followers_list)


    def oauth_request_token(self, callback_url):
        """ Step 1/3 in Twitter auth process """
        try:
            response = requests.post(url=OAUTH_REQUEST_TOKEN, auth=self.oauth,
                    data={ 'oauth_callback' : callback_url })
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            print(response.status_code)
            print(response.text)
            raise TwitterError(response)
        return response


    def oauth_access_token(self):
        """ Step 3/3 in Twitter auth process """
        try:
            response = requests.post(url=OAUTH_ACCESS_TOKEN, auth=self.oauth)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def get_rate_limit_status(self, resources):
        """ Return current rate limits for the specified resource families.
            resources: string of comma-seperated resource families """
        try:
            response = requests.get(RATE_LIMIT_STATUS + '?resources=' + resources,
                auth=self.oauth, timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def get_rate_limit_status_all(self):
        uri = quote_plus('help,users,search,statuses')
        response = requests.get(RATE_LIMIT_STATUS + '?resources=' + uri,
                auth=self.oauth, timeout=self.timeout)
        return response


    def friendships_show(self, source_id=None, target_id=None, source_name=None, target_name=None):
        """ Return info about the relationship between two users """
        if source_id and target_id:
            argdict = { 'source_id' : source_id, 'target_id': target_id }
        elif source_name and target_name:
            argdict = { 'source_screen_name' : source_name, 'target_screen_name': target_name }
        else:
            logging.error('Creating argdict failed')
            return None

        uri = self.build_uri(argdict)

        try:
            response = requests.get(FRIENDSHIPS_SHOW + '?' + uri, auth=self.oauth,
                    timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def users_show(self, user_id):
        """ Return details on a single user specified by user_id """
        try:
            response = requests.get(USERS_SHOW + '?user_id=' + str(user_id),
                    auth=self.oauth, timeout=self.timeout)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response


    def users_lookup(self, userlist, entities=False):
        """ Return fully-hydrated user objects for up to 100 users per request """
        if len(userlist) > 100:
            raise Exception("userlist length must be <= 100")

        # convert list to a CSV string
        csv_list = ','.join(userlist)
        try:
            response = requests.post(url=USERS_LOOKUP, auth=self.oauth,
                    data={'user_id' : csv_list, 'include_entities' : entities})
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects, SSLError) as e:
            raise RequestsError(str(e))
        if response.status_code != 200:
            raise TwitterError(response)
        return response
