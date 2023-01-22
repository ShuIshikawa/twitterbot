import requests
from requests_oauthlib import OAuth1Session
import datetime


BEARER_TOKEN = ''
API_KEY = ''
API_SECRET = ''
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''
USER_ID = 0

INTERVAL_MINUTE = 15

KEY_WORDS = [
    '期間限定',
    '限定商品',
    '登場',
    '発売',
    '新商品',
    '新メニュー',
    '販売開始',
    '季節限定',
]

NG_WORDS = [
    '店舗限定',
    '朝限定',
    '夜限定',
    '昼限定',
    'フォロー',
    '販売中',
    '発売中',
    'リツイート',
    '引用リツイート',
    '引用ツイート',
    'リプライ',
]


def bearer_oauth_following(r):
    '''
    Method required by bearer token authentication.
    '''

    r.headers['Authorization'] = f'Bearer {BEARER_TOKEN}'
    r.headers['User-Agent'] = 'v2FollowingLookupPython'
    return r


def bearer_oauth_search(r):
    '''
    Method required by bearer token authentication.
    '''

    r.headers['Authorization'] = f'Bearer {BEARER_TOKEN}'
    r.headers['User-Agent'] = 'v2RecentSearchPython'
    return r


def connect_to_endpoint(url, bearer_oauth, params):
    response = requests.get(url, auth=bearer_oauth, params=params)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def get_following_usernames():
    return sorted(list(
        map(lambda x: x['username'], connect_to_endpoint(
            f'https://api.twitter.com/2/users/{USER_ID}/following',
            bearer_oauth_following,
            {'user.fields': 'created_at'}
        )['data'])
    ))


def create_retweet(tweet_id):
    oauth = OAuth1Session(
        API_KEY,
        client_secret=API_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET,
    )

    # Making the request
    response = oauth.post(
        f'https://api.twitter.com/2/users/{USER_ID}/retweets',
        json={'tweet_id': tweet_id}
    )

    if response.status_code != 200:
        raise Exception(
            f'Request returned an error: {response.status_code} {response.text}'
        )


def like_tweet(tweet_id):
    oauth = OAuth1Session(
        API_KEY,
        client_secret=API_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET,
    )

    # Making the request
    response = oauth.post(
        f'https://api.twitter.com/2/users/{USER_ID}/likes',
        json={'tweet_id': tweet_id}
    )

    if response.status_code != 200:
        raise Exception(
            f'Request returned an error: {response.status_code} {response.text}'
        )


def search(query_params):
    return connect_to_endpoint(
        'https://api.twitter.com/2/tweets/search/recent',
        bearer_oauth_search,
        query_params
    )


def query_format(usernames):
    return f'({" OR ".join(KEY_WORDS)}) ({" OR from:".join(usernames)}) -is:retweet -is:reply -is:quote'


if __name__ == '__main__':

    print('-'*64)

    now = datetime.datetime.now()
    print(now)
    now = now.replace(
        minute=now.minute - now.minute % INTERVAL_MINUTE + 5,
        second=0,
        microsecond=0
    )

    following_usernames = get_following_usernames()
    print('Got following usernames')

    queries = []
    usernames = []
    for username in following_usernames:
        if len(query_format(usernames+[username])) < 512:
            usernames.append(username)
        else:
            queries.append(query_format(usernames))
            usernames = [username]
    if len(usernames) > 0:
        queries.append(query_format(usernames))

    query_params = [{
        'query': query,
        'start_time': (now - datetime.timedelta(minutes=INTERVAL_MINUTE)).isoformat()+'Z',
        'end_time': now.isoformat()+'Z',
        'tweet.fields': 'id,text,created_at,source',
    } for query in queries]

    search_results = []
    for query_param in query_params:
        search_results = search_results + search(query_param).get('data', [])
    print(f'Got {len(search_results)} search result')

    for data in search_results:
        if (text:=data.get('text', ''))!='':
            if any(map(lambda x: x in text, NG_WORDS)):
                if (id_:=data.get('id', ''))!='':
                    like_tweet(id_)
                    print(f'Liked\n{data}')
            else:
                if (id_:=data.get('id', ''))!='':
                    create_retweet(id_)
                    print(f'Retweeted\n{data}')
