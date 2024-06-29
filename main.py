import html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import requests
import smtplib
import ssl

sender_email = "cassie.dalrymple3@gmail.com"
receiver_email = "cassie.dalrymple3@gmail.com"


def get_hot_posts_for_subreddit(subreddit_name):
    print("Getting hot posts for " + subreddit_name)
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
            print("post number " + str(posts))
        i += 1

    # # not permanent, just for caching
    # with open(f"{subreddit_name}.json", "w+") as f:
    #     json.dump(posts_data, f, indent=4)

    return {"data": posts_data, "subreddit_url": f"r/{subreddit_name}"}


def create_email(full_data):
    # grabs basic structure
    with open("email.html", "r") as f:
        soup = BeautifulSoup(f.read(), features="html.parser")

    body = soup.find("body")

    for i in range(len(full_data)):
        subreddit_data = full_data[i]["data"]

        # creates the subreddit title
        a = soup.new_tag("a", href="https://www.reddit.com/" + full_data[i]["subreddit_url"])
        a.string = full_data[i]["subreddit_url"]
        print("putting together", a.string)

        h1 = soup.new_tag("h1")
        h1.append(a)

        body.append(h1)

        # goes through each post
        for post in subreddit_data:
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
                div["style"] = "padding-left: 8em"
                body.append(contents)

            # adds image or video
            if "preview" in post:
                if "url_overridden_by_dest" in post:
                    # for some reason, reddit will sometimes give a direct link and sometimes not. this is a redirect that still seems to work
                    if "i.redd.it" in post["url_overridden_by_dest"]:
                        img = soup.new_tag("img", src=post["url_overridden_by_dest"])

                        # adds padding to fit with the text
                        if post["selftext_html"] is not None:
                            img["style"] = "padding-left: 8em"
                        body.append(img)

                    elif "v.redd.it" in post["url_overridden_by_dest"]:
                        p = soup.new_tag("p")
                        p.string = "video"

                        # adds padding to fit with the text
                        if post["selftext_html"] is not None:
                            p["style"] = "padding-left: 8em"
                        body.append(p)

                    elif "youtube.com" in post["url_overridden_by_dest"] or "youtu.be" in post["url_overridden_by_dest"]:
                        a = soup.new_tag("a", href=post["url_overridden_by_dest"])
                        img = soup.new_tag("img", src=post["secure_media"]["oembed"]["thumbnail_url"])
                        a.append(img)

                        # adds padding to fit with the text
                        if post["selftext_html"] is not None:
                            img["style"] = "padding-left: 8em"
                        body.append(a)

                    else:
                        a = soup.new_tag("a", href=post["url_overridden_by_dest"])
                        img = soup.new_tag("img", src=post["thumbnail"])
                        a.append(img)

                        # adds padding to fit with the text
                        if post["selftext_html"] is not None:
                            img["style"] = "padding-left: 8em"
                        body.append(a)

            # handles gallery posts
            if "gallery_data" in post:
                urls = get_gallery_image_urls("https://www.reddit.com" + post["permalink"])

                for url in urls:
                    img = soup.new_tag("img", src=url)

                    # adds padding to fit with the text
                    if post["selftext_html"] is not None:
                        img["style"] = "padding-left: 8em"
                    body.append(img)

            # gets the icon, colour of text and resizes it all to fit
            comments_icon = soup.new_tag("img", src="https://www.redditstatic.com/emaildigest/reddit_comment.png", width="13px")
            comments_text = soup.new_tag("p", style="color: #999999 !important;")
            num_comments = post["num_comments"]

            if num_comments != 1:
                comments_text.string = f"{num_comments} Comments"
            else:
                comments_text.string = f"{num_comments} Comment"

            comments_text.insert(0, comments_icon)
            body.append(comments_text)

    return soup.prettify()


def get_gallery_image_urls(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, features="html.parser")
    imgs = soup.find_all("img", attrs={"class": "media-lightbox-img"})

    urls = []
    for img in imgs:
        if "src" in img.attrs:
            urls.append(img["src"])
        else:
            urls.append(img["data-lazy-src"])

    return urls


def send_email(html):
    with open("password.txt", "r") as f:
        password = f.read()

    # set up the message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Reddit Roundup"
    message["From"] = "test"
    message["To"] = receiver_email
    part = MIMEText(html, "html")
    message.attach(part)

    # set up the email sender
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        print(f"Sending email to {receiver_email}")
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )


def main():
    subreddits = ["feedthebeast", "singularity", "obsidianmd"]
    full_data = []
    for subreddit in subreddits:
        full_data.append(get_hot_posts_for_subreddit(subreddit))

    email = create_email(full_data)
    send_email(email)


if __name__ == "__main__":
    main()
