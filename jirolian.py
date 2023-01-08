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


def bearer_oauth_following(r):
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
    following_usernames = {
        user['username'] for user in connect_to_endpoint(url, params)['data']
    }
    return following_usernames


def create_retweet(tweet_id):
    oauth = OAuth1Session(
        API_KEY,
        client_secret=API_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET,
    )

    response = oauth.post(
        f'https://api.twitter.com/2/users/{USER_ID}/retweets',
        json={'tweet_id': tweet_id}
    )

    if response.status_code != 200:
        raise Exception(
            f'Request returned an error: {response.status_code} {response.text}'
        )


def bearer_oauth_filtered_stream(r):
    r.headers['Authorization'] = f'Bearer {BEARER_TOKEN}'
    r.headers['User-Agent'] = 'v2FilteredStreamPython'
    return r


def get_rules():
    response = requests.get(
        'https://api.twitter.com/2/tweets/search/stream/rules',
        auth=bearer_oauth_filtered_stream,
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
        auth=bearer_oauth_filtered_stream,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            'Cannot delete rules (HTTP {}): {}'.format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))


def set_rules():
    new_rules = [
        {'value': '-is:retweet @jirolian', 'tag': 'at jiolian'},
    ]
    payload = {'add': new_rules}
    response = requests.post(
        'https://api.twitter.com/2/tweets/search/stream/rules',
        auth=bearer_oauth_filtered_stream,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            'Cannot add rules (HTTP {}): {}'.format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))


def get_stream(usernames):
    response = requests.get(
        'https://api.twitter.com/2/tweets/search/stream?tweet.fields=entities',
        auth=bearer_oauth_filtered_stream,
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
                if 'entities' in json_response['data']:
                    if 'mentions' in json_response['data']['entities']:
                        mentions = set(map(
                            lambda x: x['username'],
                            json_response['data']['entities']['mentions']
                        ))
                        if len(mentions-usernames) == 0:
                            create_retweet(json_response['data']['id'])


def main():
    usernames = get_following_usernames()
    print('Following Usernames')
    print(usernames)
    rules = get_rules()
    delete_all_rules(rules)
    set_rules()
    while True:
        try:
            get_stream(usernames)
        except Exception as e:
            print(datetime.datetime.now())
            print(e)
        time.sleep(60)


if __name__ == '__main__':
    main()

# nohup python jirolian.py >> jirolian.log &
