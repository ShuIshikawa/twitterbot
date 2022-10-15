from requests_oauthlib import OAuth1Session

# https://www.d-advantage.jp/ja/gis/quote


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


# API情報を記入
API_KEY = ''
API_SECRET = ''
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''
USER_ID = 0


def create_retweet(oauth, tweet_id):

    # Making the request
    response = oauth.post(
        f'https://api.twitter.com/2/users/{USER_ID}/retweets',
        json={'tweet_id': tweet_id}
    )

    if response.status_code != 200:
        raise Exception(
            f'Request returned an error: {response.status_code} {response.text}'
        )


def like_tweet(oauth, tweet_id):

    # Making the request
    response = oauth.post(
        f'https://api.twitter.com/2/users/{USER_ID}/likes',
        json={'tweet_id': tweet_id}
    )

    if response.status_code != 200:
        raise Exception(
            f'Request returned an error: {response.status_code} {response.text}'
        )


def get_timeline(oauth):

    response = oauth.get(
        f'https://api.twitter.com/2/users/{USER_ID}/timelines/reverse_chronological',
        params={
            'tweet.fields': 'id,referenced_tweets',
        }
    )

    if response.status_code != 200:
        raise Exception(
            f'Request returned an error: {response.status_code} {response.text}'
        )

    return response.json()['data']


if __name__ == '__main__':

    while True:
        # Make the request
        oauth = OAuth1Session(
            API_KEY,
            client_secret=API_SECRET,
            resource_owner_key=ACCESS_TOKEN,
            resource_owner_secret=ACCESS_TOKEN_SECRET,
        )
        timeline = get_timeline(oauth)
        for tweet in timeline[::-1]:
            if any(map(lambda x: x in tweet['text'], KEY_WORDS)):
                if any(map(lambda x: x in tweet['text'], NG_WORDS)) or ('referenced_tweets' in tweet):
                    like_tweet(oauth, tweet['id'])
                else:
                    create_retweet(oauth, tweet['id'])
