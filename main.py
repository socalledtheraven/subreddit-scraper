import requests


def get_hot_posts_for_subreddit(subreddit_name):
    r = requests.get(f"https://www.reddit.com/r/{subreddit_name}/hot.json")
    data = r.json()["data"]["children"]

    posts = 0
    posts_data = []
    while posts < 10:
        print(f"Getting posts for subreddit {subreddit_name}")
        print(data[posts]["data"]["stickied"])
        if data[posts]["data"]["stickied"] is not True:
            posts_data.append(data[posts]["data"])
        posts += 1

    return posts_data


get_hot_posts_for_subreddit("feedthebeast")
