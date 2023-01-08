import requests
from requests_oauthlib import OAuth1Session
import json
import datetime
import time


BEARER_TOKEN = ''
API_KEY = ''
API_SECRET = ''
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''
USER_ID = 0


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


def connect_to_endpoint(url, params):
    response = requests.request(
        'GET',
        url,
        auth=bearer_oauth_following,
        params=params
    )
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            'Request returned an error: {} {}'.format(
                response.status_code, response.text
            )
        )
    return response.json()


def get_following_usernames():
    url = f'https://api.twitter.com/2/users/{USER_ID}/following'
    params = {'user.fields': 'created_at'}
    following_usernames = [user['username'] for user in connect_to_endpoint(url, params)['data']]
    return sorted(following_usernames)


def make_rules(following_ids):
    rules = [''] * 5
    for username in following_ids:
        for i in range(5):
            if len(rules[i]+' OR from:'+username) + 30 < 512:
                rules[i] += (' OR from:' + username)
                break
    return [{'value': f'-is:retweet -is:reply -is:quote ({rule[4:]})', 'tag': f'rule {i}'} for i, rule in enumerate(rules) if rule != '']


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


def bearer_oauth_stream(r):
    '''
    Method required by bearer token authentication.
    '''

    r.headers['Authorization'] = f'Bearer {BEARER_TOKEN}'
    r.headers['User-Agent'] = 'v2FilteredStreamPython'
    return r


def get_rules():
    response = requests.get(
        'https://api.twitter.com/2/tweets/search/stream/rules', auth=bearer_oauth_stream
    )
    if response.status_code != 200:
        raise Exception(
            'Cannot get rules (HTTP {}): {}'.format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()


def delete_all_rules(rules):
    if rules is None or 'data' not in rules:
        return None

    ids = list(map(lambda rule: rule['id'], rules['data']))
    payload = {'delete': {'ids': ids}}
    response = requests.post(
        'https://api.twitter.com/2/tweets/search/stream/rules',
        auth=bearer_oauth_stream,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            'Cannot delete rules (HTTP {}): {}'.format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))


def set_rules(rules):
    payload = {'add': rules}
    response = requests.post(
        'https://api.twitter.com/2/tweets/search/stream/rules',
        auth=bearer_oauth_stream,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            'Cannot add rules (HTTP {}): {}'.format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))


def get_stream():
    response = requests.get(
        'https://api.twitter.com/2/tweets/search/stream',
        auth=bearer_oauth_stream,
        stream=True,
    )
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            'Cannot get stream (HTTP {}): {}'.format(
                response.status_code, response.text
            )
        )
    for response_line in response.iter_lines():
        if response_line:
            json_response = json.loads(response_line)
            print(datetime.datetime.now())
            print(json_response)
            if 'errors' in json_response:
                time.sleep(60)
                continue
            elif 'data' in json_response:
                if any(map(lambda x: x in json_response['data']['text'], KEY_WORDS)):
                    if any(map(lambda x: x in json_response['data']['text'], NG_WORDS)):
                        like_tweet(json_response['data']['id'])
                    else:
                        create_retweet(json_response['data']['id'])


if __name__ == '__main__':
    rules = get_rules()
    delete_all_rules(rules)
    following_usernames = get_following_usernames()
    rules = make_rules(following_usernames)
    set_rules(rules)
    while True:
        try:
            get_stream()
        except Exception as e:
            print(datetime.datetime.now())
            print(e)
        time.sleep(60)

# nohup python gentei.py >> gentei.log &
