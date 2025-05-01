import logging
import requests
import time
import os

# logger setup
logger = logging.getLogger("Reddit client")
logger.propagate = False
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)

from dotenv import load_dotenv

# load env file
load_dotenv()

class RedditClient:
    API_BASE = "https://oauth.reddit.com/r"
    SUBREDDITS = {"anime_titties", "NeutralPolitics", "PoliticslDiscussion", "politics"}

    # OAuth2 credentials
    CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
    USER_AGENT=os.environ.get("REDDIT_USER_AGENT")
    USERNAME = os.environ.get("REDDIT_USERNAME")
    PASSWORD = os.environ.get("REDDIT_PASSWORD")
    ACCESS_TOKEN = None
    TOKEN_EXPIRATION = 0 

    def __init__(self):
        self.update_oauth2_token()

    def update_oauth2_token(self):
        current_time = time.monotonic()

        if current_time > self.TOKEN_EXPIRATION - 300:
            logger.info("Refreshing OAuth2 token...")

            # Request a new token
            auth = requests.auth.HTTPBasicAuth(self.CLIENT_ID, self.CLIENT_SECRET)
            headers = {"User-Agent": self.USER_AGENT}
            data = {
                "grant_type": "password",
                "username": self.USERNAME,
                "password": self.PASSWORD
            }
            response = requests.post("https://www.reddit.com/api/v1/access_token", auth=auth, data=data, headers=headers)

            if response.status_code == 200:
                token_data = response.json()
                self.ACCESS_TOKEN = token_data["access_token"]
                self.TOKEN_EXPIRATION = current_time + token_data["expires_in"]
                logger.info(f"OAuth2 token obtained. Expires at {self.TOKEN_EXPIRATION}")
            else:
                logger.error(f"Failed to refresh OAuth2 token: {response.status_code}")
                raise Exception(f"Failed to refresh token: {response.text}")

    def build_request(self, request_pieces):
        """Build the URL for the API call."""
        api_call = "/".join([self.API_BASE] + request_pieces)
        return api_call

    def execute_request(self, api_call):
        """Execute an HTTP GET request."""
        self.update_oauth2_token() 

        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "User-Agent": self.USER_AGENT
        }

        resp = requests.get(api_call, headers=headers)  # Include the OAuth2 token in the headers

        if resp.status_code != 200:
            logger.error(f"Request failed with status code {resp.status_code}")
            resp.raise_for_status()

        json = resp.json()
        #logger.info(f"Response JSON: {json}")
        return json

    def get_thread(self, subreddit, post_id):
        """Get the comments for a given post."""
        request_pieces = [subreddit, "comments", f"{post_id}/.json"]
        api_call = self.build_request(request_pieces)
        print(api_call)
        return self.execute_request(api_call)

    def get_catalog(self, subreddit, sort_type="new"):
        """Get a catalog of posts from a subreddit."""
        request_pieces = [subreddit, sort_type, ".json"]
        api_call = self.build_request(request_pieces)
        print(api_call)
        return self.execute_request(api_call)


if __name__ == "__main__":
    # Initialize the Reddit client
    client = RedditClient()

    # Example of fetching a thread from a subreddit
    #json = client.get_thread("politics", "1ggrjfz")
    #print(json)
    c = client.get_catalog("politics")
    print(c)
