import html as ht
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from bs4 import BeautifulSoup, Tag
import requests
import smtplib
import ssl

sender_email = "cassie.dalrymple3@gmail.com"
receiver_email = "cassie.dalrymple3@gmail.com"


def get_hot_posts_for_subreddit(subreddit_name: str) -> dict:
    """
    Fetches the top 10 hot posts from the specified subreddit, excluding stickied and uninteresting posts.

    Args:
        subreddit_name (str): The name of the subreddit to fetch posts from.

    Returns:
        dict: A dictionary containing the subreddit URL and a list of post data.
    """
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

    return {"data": posts_data, "subreddit_url": f"r/{subreddit_name}"}


def create_image_from_post(post: dict, soup: BeautifulSoup) -> Tag:
    """
    Creates an HTML img tag for a post with an image.

    Args:
        post (dict): The post data.
        soup (BeautifulSoup): A BeautifulSoup object to create new tags.

    Returns:
        Tag: An img tag with the post image.
    """
    img = soup.new_tag("img", src=post["url_overridden_by_dest"], width=1000)

    # adds padding to fit with the text
    if post["selftext_html"] is not None:
        img["style"] = "padding-left: 8em"

    return img


def create_video_placeholder_from_post(post: dict, soup: BeautifulSoup) -> Tag:
    """
    Creates a placeholder text for video posts.

    Args:
        post (dict): The post data.
        soup (BeautifulSoup): A BeautifulSoup object to create new tags.

    Returns:
        Tag: A paragraph tag with the placeholder text.
    """
    p = soup.new_tag("p")
    p.string = "video"

    # adds padding to fit with the text
    if post["selftext_html"] is not None:
        p["style"] = "padding-left: 8em"

    return p


def create_youtube_video_from_post(post: dict, soup: BeautifulSoup) -> Tag:
    """
    Creates an anchor tag for YouTube video posts with a thumbnail image.

    Args:
        post (dict): The post data.
        soup (BeautifulSoup): A BeautifulSoup object to create new tags.

    Returns:
        Tag: An anchor tag with the YouTube video link and thumbnail image.
    """
    a = soup.new_tag("a", href=post["url_overridden_by_dest"])
    img = soup.new_tag("img", src=post["secure_media"]["oembed"]["thumbnail_url"], width=1000)
    a.append(img)

    # adds padding to fit with the text
    if post["selftext_html"] is not None:
        img["style"] = "padding-left: 8em"

    return a


def create_video_from_post(post: dict, soup: BeautifulSoup) -> Tag:
    """
    Creates an anchor tag for video posts with a thumbnail image.

    Args:
        post (dict): The post data.
        soup (BeautifulSoup): A BeautifulSoup object to create new tags.

    Returns:
        Tag: An anchor tag with the video link and thumbnail image.
    """
    a = soup.new_tag("a", href=post["url_overridden_by_dest"])
    img = soup.new_tag("img", src=post["thumbnail"], width=1000)
    a.append(img)

    # adds padding to fit with the text
    if post["selftext_html"] is not None:
        img["style"] = "padding-left: 8em"

    return a


def create_gallery_from_post(post: dict, soup: BeautifulSoup) -> list[Tag]:
    """
    Creates a list of img tags for gallery posts.

    Args:
        post (dict): The post data.
        soup (BeautifulSoup): A BeautifulSoup object to create new tags.

    Returns:
        list[Tag]: A list of img tags for the gallery images.
    """
    urls = get_gallery_image_urls("https://www.reddit.com" + post["permalink"])

    imgs = []
    for url in urls:
        img = soup.new_tag("img", src=url, width=1000)

        # adds padding to fit with the text
        if post["selftext_html"] is not None:
            img["style"] = "padding-left: 8em"

        imgs.append(img)

    return imgs


def create_comments_text(post: dict, soup: BeautifulSoup) -> Tag:
    """
    Creates a paragraph tag displaying the number of comments on the post.

    Args:
        post (dict): The post data.
        soup (BeautifulSoup): A BeautifulSoup object to create new tags.

    Returns:
        Tag: A paragraph tag with the comments count.
    """
    # gets the icon, colour of text and resizes it all to fit inline
    comments_icon = soup.new_tag("img", src="https://www.redditstatic.com/emaildigest/reddit_comment.png", width="13px")
    comments_text = soup.new_tag("p", style="color: #999999 !important;")
    num_comments = post["num_comments"]

    if num_comments != 1:
        comments_text.string = f"{num_comments} Comments"
    else:
        comments_text.string = f"{num_comments} Comment"

    comments_text.insert(0, comments_icon)

    return comments_text


def pad_contents(post: dict) -> BeautifulSoup:
    """
    Adds padding to the contents of the post.

    Args:
        post (dict): The post data.

    Returns:
        BeautifulSoup: A BeautifulSoup object with padded contents.
    """
    contents = BeautifulSoup(ht.unescape(post["selftext_html"]), features="html.parser")
    div = contents.find("div")
    div["style"] = "padding-left: 8em"

    return contents


def create_post_title(post: dict, soup: BeautifulSoup) -> Tag:
    """
    Creates a header tag for the post title with a link to the post.

    Args:
        post (dict): The post data.
        soup (BeautifulSoup): A BeautifulSoup object to create new tags.

    Returns:
        Tag: An h2 tag with the post title.
    """
    # creates link
    a = soup.new_tag("a", href="https://www.reddit.com" + post["permalink"])
    a.string = post["title"]

    # creates title
    h2 = soup.new_tag("h2")
    h2.append(a)

    return h2


def create_subreddit_title(soup: BeautifulSoup, subreddit_url: str) -> Tag:
    """
    Creates a header tag for the subreddit title with a link to the subreddit.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object to create new tags.
        subreddit_url (str): The URL of the subreddit.

    Returns:
        Tag: An h1 tag with the subreddit title.
    """
    # creates the subreddit title
    a = soup.new_tag("a", href="https://www.reddit.com/" + subreddit_url)
    a.string = subreddit_url
    print("putting together", a.string)

    h1 = soup.new_tag("h1")
    h1.append(a)

    return h1


def create_email(full_data: list[dict]) -> str:
    """
    Creates the HTML content for the email using the subreddit post data.

    Args:
        full_data (list[dict]): A list of dictionaries containing subreddit and post data.

    Returns:
        str: The HTML content for the email.
    """
    # grabs basic structure
    with open("email.html", "r") as f:
        soup = BeautifulSoup(f.read(), features="html.parser")

    body = soup.find("body")

    for i in range(len(full_data)):
        subreddit_data = full_data[i]["data"]

        h1 = create_subreddit_title(soup, full_data[i]["subreddit_url"])
        body.append(h1)

        # goes through each post
        for post in subreddit_data:
            h2 = create_post_title(post, soup)
            body.append(h2)

            # adds text
            if post["selftext_html"] is not None:
                contents = pad_contents(post)
                body.append(contents)

            # adds image or video
            if "preview" in post:
                if "url_overridden_by_dest" in post:
                    # for some reason, reddit will sometimes give a direct link and sometimes not. this is a redirect that still seems to work
                    if "i.redd.it" in post["url_overridden_by_dest"]:
                        body.append(create_image_from_post(post, soup))
                    elif "v.redd.it" in post["url_overridden_by_dest"]:
                        body.append(create_video_placeholder_from_post(post, soup))
                    elif "youtube.com" in post["url_overridden_by_dest"] or "youtu.be" in post["url_overridden_by_dest"]:
                        body.append(create_youtube_video_from_post(post, soup))
                    else:
                        body.append(create_video_from_post(post, soup))

            # handles gallery posts
            if "gallery_data" in post:
                body.extend(create_gallery_from_post(post, soup))

            comments_text = create_comments_text(post, soup)
            body.append(comments_text)

    return soup.prettify()


def get_gallery_image_urls(url: str) -> List[str]:
    """
    Fetches the URLs of images in a gallery post.

    Args:
        url (str): The URL of the Reddit post.

    Returns:
        list[str]: A list of image URLs.
    """
    r = requests.get(url)
    soup = BeautifulSoup(r.content, features="html.parser")
    imgs = soup.find_all("img", attrs={"class": "media-lightbox-img", "width": "1000"})

    urls = []
    for img in imgs:
        if "src" in img.attrs:
            urls.append(img["src"])
        else:
            urls.append(img["data-lazy-src"])

    return urls


def create_message(html: str) -> MIMEMultipart:
    """
    Creates an email message with the given HTML content.

    Args:
        html (str): The HTML content for the email.

    Returns:
        MIMEMultipart: The email message.
    """
    # set up the message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Reddit Roundup"
    message["From"] = "test"
    message["To"] = receiver_email
    part = MIMEText(html, "html")
    message.attach(part)

    return message


def send_email(html: str):
    """
    Sends an email with the given HTML content.

    Args:
        html (str): The HTML content for the email.
    """
    with open("password.txt", "r") as f:
        password = f.read()

    message = create_message(html)

    # set up the email sender
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        print(f"Sending email to {receiver_email}")
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )


def main():
    """ Main function to fetch hot posts from subreddits, create the email content, and send the email."""
    subreddits = ["feedthebeast", "singularity", "obsidianmd"]
    full_data = [get_hot_posts_for_subreddit(subreddit) for subreddit in subreddits]

    email = create_email(full_data)
    send_email(email)


main()
