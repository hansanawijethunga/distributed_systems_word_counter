import tweepy
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")


def authenticate_twitter():
    try:
        # Create authentication object
        auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)

        # Set access token
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

        # Create API object
        api = tweepy.API(auth)

        # Verify credentials
        api.verify_credentials()
        print("Authentication successful!")
        return api
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
        return None


# Step 6: Function to create a tweet
def create_tweet(api, message):
    try:
        # Post the tweet
        api.update_status(status=message)
        print(f"Successfully tweeted: {message}")
    except Exception as e:
        print(f"Error creating tweet: {str(e)}")


# Step 7: Main execution
if __name__ == "__main__":
    # Authenticate
    twitter_api = authenticate_twitter()

    # Check if authentication was successful
    if twitter_api:
        # Tweet message (must be 280 characters or less)
        tweet_message = "Hello World! This is my first tweet using Python and Tweepy!"

        # Create the tweet
        create_tweet(twitter_api, tweet_message)