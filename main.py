import traceback
import time
import tweepy
import ccxt
from discord import Webhook, RequestsWebhookAdapter
from textblob import TextBlob

# Set up Twitter API
auth = tweepy.OAuthHandler('', '')
auth.set_access_token('',
                      '')
api = tweepy.API(auth)

try:
    api.verify_credentials()
    print("Authentication OK")
except:
    print("Error during authentication")

# Set up FTX API
ftx = ccxt.ftx({
    'apiKey': '',
    'secret': '',
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    },
})

if ftx.check_required_credentials() is not True:
    exit('Failed to connect to FTX')


def get_balance(currency):
    return ftx.fetch_balance()[currency]['free']


def get_average_price_of_order(order_id):
    return ftx.fetch_order(order_id)['average']


def get_id_of_latest_order(symbol):
    return ftx.fetch_orders(symbol, limit=2)[-1]['id']


def create_market_order(symbol, side, amount):
    return ftx.create_order(symbol, 'market', side, amount, price=None)['id']


def create_stop_loss_order(symbol, amount, limit_price, stop_price):
    return ftx.create_order(symbol, 'stop', 'sell', amount, limit_price, params={'stopPrice': stop_price})


# Filters out mentions and RTs
def from_creator(status):
    if hasattr(status, 'retweeted_status'):
        return False
    elif status.in_reply_to_status_id is not None:
        return False
    elif status.in_reply_to_screen_name is not None:
        return False
    elif status.in_reply_to_user_id is not None:
        return False
    else:
        return True


class StreamListener(tweepy.StreamListener):

    def on_status(self, status):
        print(status.text.lower())
        if from_creator(status):
            tweet = status.text.lower()
            blob = TextBlob(tweet)
            print('New tweet from Elon Musk')
            print(tweet)
            if 'doge' in tweet and blob.sentiment.polarity >= 0:
                print('Tweet is about $DOGE and is not negative')
                # Market order USD balance
                order_id = create_market_order('DOGEBULL/USD', 'buy', 999)
                time.sleep(1)
                # Place stop loss
                amount = get_balance('DOGEBULL')
                avg_price = get_average_price_of_order(order_id)
                limit_price = avg_price - avg_price * 1.5 / 100
                stop_price = limit_price + limit_price * 0.1 / 100
                create_stop_loss_order('DOGEBULL/USD', amount, limit_price, stop_price)

                # Send discord notification
                webhook = Webhook.from_url(
                    "",
                    adapter=RequestsWebhookAdapter())
                webhook.send("!!! ROCKET ALERT !!!")
                webhook.send("ELON IS SENDING DOGE TO THE MOON")
            return True

        return True

    def on_error(self, status_code):
        if status_code == 420:
            print("Error 420")
            # Returning False here disconnects the stream
            return False


while 1:
    try:
        myStreamListener = StreamListener()
        myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
        myStream.filter(follow=['44196397'])

    except Exception as e:
        traceback.print_exc()
        continue
