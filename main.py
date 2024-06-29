import html
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup, Tag
import requests
import smtplib
import ssl

sender_email = "cassie.dalrymple3@gmail.com"
receiver_email = "cassie.dalrymple3@gmail.com"


def get_hot_posts_for_subreddit(subreddit_name):
    r = requests.get(f"https://www.reddit.com/r/{subreddit_name}/hot.json")
    data = r.json()["data"]["children"]

    posts = 0
    i = 0
    posts_data = []
    while posts < 10:
        # check for pinned posts and uninteresting posts
        if data[i]["data"]["stickied"] is not True and data[i]["data"]["link_flair_text"] != "Problem":
            posts_data.append(data[i]["data"])
            # separate post count and index bc filtering posts
            posts += 1
        i += 1

    # not permanent, just for caching
    with open(f"{subreddit_name}.json", "w+") as f:
        json.dump(posts_data, f, indent=4)

    return posts_data


def create_email(posts_data):
    # grabs basic structure
    with open("email.html", "r") as f:
        soup = BeautifulSoup(f.read(), features="html.parser")

    body = soup.find("body")

    # adds each post at the time
    for post in posts_data:
        # creates link
        a = soup.new_tag("a", href="https://www.reddit.com" + post["permalink"])
        a.string = post["title"]

        # creates title
        h2 = soup.new_tag("h2")
        h2.append(a)

        body.append(h2)

        # adds text
        if post["selftext_html"] is not None:
            contents = BeautifulSoup(html.unescape(post["selftext_html"]), features="html.parser")
            div = contents.find("div")
            div["style"] = "padding-left: 4em"
            body.append(contents)

        # adds image
        if "preview" in post:
            if "https://i.redd.it" in post["url_overridden_by_dest"]:
                img = soup.new_tag("img", src=post["url_overridden_by_dest"])
                body.append(img)
            elif "https://v.redd.it" in post["url_overridden_by_dest"]:
                video = soup.new_tag("video", src=post["media"]["reddit_video"]["fallback_url"], controls="")
                body.append(video)

        # handles gallery posts
        if "gallery_data" in post:
            img = soup.new_tag("img", src=link)
            body.append(img)

    print(soup.prettify())


def get_gallery_first_image(url)
    r = requests.get(url)
    soup = BeautifulSoup(r.content, features="html.parser")

    return soup.find("img", attrs={"class": "media-lightbox-img"})


def send_email(html):
    with open("password.txt", "r") as f:
        password = f.read()

    message = MIMEMultipart("alternative")
    message["Subject"] = "Reddit Roundup"
    message["From"] = sender_email
    message["To"] = receiver_email
    part = MIMEText(html, "html")
    message.attach(part)

    print(message.as_string())

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        print(f"Sending email to {receiver_email}")
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )


def main():
    # get_hot_posts_for_subreddit("feedthebeast")
    with open("feedthebeast.json", "r") as f:
        data = json.load(f)
    create_email(data)


if __name__ == "__main__":
    main()
