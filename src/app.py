from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from pathlib import Path
from fastai.vision import (
    load_learner,
)

import sys
import uvicorn
import twitter
import os

api = twitter.Api(consumer_key=os.environ.get('CONSUMER_KEY'),
                  consumer_secret=os.environ.get('CONSUMER_SECRET'),
                  access_token_key=os.environ.get('ACCESS_TOKEN'),
                  access_token_secret=os.environ.get('ACCESS_TOKEN_SECRET'))

path = Path(__file__).parent

app = Starlette()

# load statics
app.mount('/statics', StaticFiles(directory=str(path)+'/statics'), name='statics')

# load html templates
templates = Jinja2Templates(directory=str(path)+'/templates')

# load exported learner
learner = load_learner(str(path)+'/../exports', 'tweet-sentiment.pkl')

def predict_tweet_sentiment(user):
    tweets = api.GetUserTimeline(screen_name=user)
    sentiment = []
    total_sentiment = 0
    for tweet in tweets:
        pred_class, pred_idx, outputs = learner.predict(tweet.text)
        sentiment.append({
            "tweet": tweet.text,
            "class": int(str(pred_class))
        })
        total_sentiment += int(str(pred_class))

    return {
        "items": sentiment,
        "total": len(tweets) > 0 and total_sentiment/len(tweets) or 0
    }

@app.route("/", methods=["GET"], include_in_schema=False)
async def user(request):
    context = {'request': request}

    if 'screen_name' in request.query_params:
        try:
            context.update({'screen_name': request.query_params['screen_name'],
                            'sentiment': predict_tweet_sentiment(request.query_params['screen_name'])
            })
        except twitter.error.TwitterError as err:
            context.update({'errors': err.message})

    return templates.TemplateResponse('index.html', context)

if __name__ == '__main__':
    assert sys.argv[-1] in ("server", "schema"), "Usage: app.py [server|schema]"

    if sys.argv[-1] == "server":
        uvicorn.run(app, host="0.0.0.0", port=8000)
