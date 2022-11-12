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


def logging(text):
    with open(__file__+'.log', 'a') as f:
        print(text, file=f)


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


def bearer_oauth(r):
    '''
    Method required by bearer token authentication.
    '''

    r.headers['Authorization'] = f'Bearer {BEARER_TOKEN}'
    r.headers['User-Agent'] = 'v2FilteredStreamPython'
    return r


def get_rules():
    response = requests.get(
        'https://api.twitter.com/2/tweets/search/stream/rules', auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            'Cannot get rules (HTTP {}): {}'.format(response.status_code, response.text)
        )
    logging(json.dumps(response.json()))
    return response.json()


def delete_all_rules(rules):
    if rules is None or 'data' not in rules:
        return None

    ids = list(map(lambda rule: rule['id'], rules['data']))
    payload = {'delete': {'ids': ids}}
    response = requests.post(
        'https://api.twitter.com/2/tweets/search/stream/rules',
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            'Cannot delete rules (HTTP {}): {}'.format(
                response.status_code, response.text
            )
        )
    logging(json.dumps(response.json()))


def set_rules():
    # You can adjust the rules if needed
    sample_rules = [
        {'value': '-is:retweet @jirolian', 'tag': 'at jiolian'},
    ]
    payload = {'add': sample_rules}
    response = requests.post(
        'https://api.twitter.com/2/tweets/search/stream/rules',
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            'Cannot add rules (HTTP {}): {}'.format(response.status_code, response.text)
        )
    logging(json.dumps(response.json()))


def get_stream():
    response = requests.get(
        'https://api.twitter.com/2/tweets/search/stream?tweet.fields=entities', auth=bearer_oauth, stream=True,
    )
    logging(response.status_code)
    if response.status_code != 200:
        raise Exception(
            'Cannot get stream (HTTP {}): {}'.format(
                response.status_code, response.text
            )
        )
    for response_line in response.iter_lines():
        if response_line:
            json_response = json.loads(response_line)
            logging(json_response)
            if 'entities' in json_response['data']:
                if 'mentions' in json_response['data']['entities']:
                    if len(json_response['data']['entities']['mentions'])==1:
                        if json_response['data']['entities']['mentions'][0]['username']=='jirolian':
                            create_retweet(json_response['data']['id'])
                    elif 'urls' in json_response['data']['entities']:
                        if any([('www.swarmapp.com' in url.get('expanded_url', '')) for url in json_response['data']['entities']['urls']]):
                            create_retweet(json_response['data']['id'])


def main():
    rules = get_rules()
    delete_all_rules(rules)
    set_rules()
    while True:
        try:
            get_stream()
        except Exception as e:
            logging(datetime.datetime.now())
            logging(e)
        time.sleep(60)


if __name__ == '__main__':
    main()

# nohup python jirolian.py > jirolian.log &
