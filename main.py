import html as ht
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
import asyncio
import aiohttp
import aiosmtplib
from bs4 import BeautifulSoup, Tag
import ssl

sender_email = "cassie.dalrymple3@gmail.com"
receiver_email = "cassie.dalrymple3@gmail.com"


async def get_hot_posts_for_subreddit(session: aiohttp.ClientSession, subreddit_name: str) -> dict:
    """
    Fetches the top 10 hot posts from the specified subreddit asynchronously.
    """
    print("Getting hot posts for " + subreddit_name)
    url = f"https://www.reddit.com/r/{subreddit_name}/hot.json"
    async with session.get(url) as response:
        data = (await response.json())["data"]["children"]

    posts = 0
    i = 0
    posts_data = []
    while posts < 10 and i < len(data):
        if not data[i]["data"]["stickied"] and data[i]["data"]["link_flair_text"] != "Problem":
            posts_data.append(data[i]["data"])
            posts += 1
            print(f"post number {posts} for {subreddit_name}")
        i += 1

    return {"data": posts_data, "subreddit_url": f"r/{subreddit_name}"}


def create_image_from_post(post: dict, soup: BeautifulSoup) -> Tag:
    """
    Creates a responsive HTML img tag for a post with an image.
    """
    img = soup.new_tag("img", src=post["url_overridden_by_dest"])
    style = "max-width: 100%; height: auto; display: block;"

    if post["selftext_html"] is not None:
        style += " padding-left: 8em;"

    img["style"] = style
    return img


def create_video_placeholder_from_post(post: dict, soup: BeautifulSoup) -> Tag:
    """
    Creates a placeholder text for video posts.
    """
    p = soup.new_tag("p")
    p.string = "video"
    if post["selftext_html"] is not None:
        p["style"] = "padding-left: 8em"
    return p


def create_youtube_video_from_post(post: dict, soup: BeautifulSoup) -> Tag:
    """
    Creates a responsive anchor tag for YouTube video posts with a thumbnail image.
    """
    a = soup.new_tag("a", href=post["url_overridden_by_dest"])
    img = soup.new_tag("img", src=post["secure_media"]["oembed"]["thumbnail_url"])
    style = "max-width: 100%; height: auto; display: block;"

    if post["selftext_html"] is not None:
        style += " padding-left: 8em;"

    img["style"] = style
    a.append(img)
    return a


def create_video_from_post(post: dict, soup: BeautifulSoup) -> Tag:
    """
    Creates a responsive anchor tag for video posts with a thumbnail image.
    """
    a = soup.new_tag("a", href=post["url_overridden_by_dest"])
    img = soup.new_tag("img", src=post["thumbnail"])
    style = "max-width: 100%; height: auto; display: block;"

    if post["selftext_html"] is not None:
        style += " padding-left: 8em;"

    img["style"] = style
    a.append(img)
    return a


async def create_gallery_from_post(session: aiohttp.ClientSession, post: dict, soup: BeautifulSoup) -> list[Tag]:
    """
    Creates a list of responsive img tags for gallery posts asynchronously.
    """
    urls = await get_gallery_image_urls(session, "https://www.reddit.com" + post["permalink"])

    imgs = []
    for url in urls:
        img = soup.new_tag("img", src=url)
        style = "max-width: 100%; height: auto; display: block;"

        if post["selftext_html"] is not None:
            style += " padding-left: 8em;"

        img["style"] = style
        imgs.append(img)
    return imgs


def create_comments_text(post: dict, soup: BeautifulSoup) -> Tag:
    """
    Creates a paragraph tag displaying the number of comments on the post.
    """
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
    """
    contents = BeautifulSoup(ht.unescape(post["selftext_html"]), features="html.parser")
    div = contents.find("div")
    if div:
        div["style"] = "padding-left: 8em"
    return contents


def create_post_title(post: dict, soup: BeautifulSoup) -> Tag:
    """
    Creates a header tag for the post title with a link to the post.
    """
    a = soup.new_tag("a", href="https://www.reddit.com" + post["permalink"])
    a.string = post["title"]
    h2 = soup.new_tag("h2")
    h2.append(a)
    return h2


def create_subreddit_title(soup: BeautifulSoup, subreddit_url: str) -> Tag:
    """
    Creates a header tag for the subreddit title with a link to the subreddit.
    """
    a = soup.new_tag("a", href="https://www.reddit.com/" + subreddit_url)
    a.string = subreddit_url
    print("putting together", a.string)
    h1 = soup.new_tag("h1")
    h1.append(a)
    return h1


async def create_email(full_data: list[dict]) -> str:
    """
    Creates the HTML content for the email using the subreddit post data.
    """
    with open("email.html", "r") as f:
        soup = BeautifulSoup(f.read(), features="html.parser")

    body = soup.find("body")

    async with aiohttp.ClientSession() as session:
        for i in range(len(full_data)):
            subreddit_data = full_data[i]["data"]
            h1 = create_subreddit_title(soup, full_data[i]["subreddit_url"])
            body.append(h1)

            for post in subreddit_data:
                h2 = create_post_title(post, soup)
                body.append(h2)

                if post["selftext_html"] is not None:
                    contents = pad_contents(post)
                    body.append(contents)

                if "preview" in post and "url_overridden_by_dest" in post:
                    if "i.redd.it" in post["url_overridden_by_dest"]:
                        body.append(create_image_from_post(post, soup))
                    elif "v.redd.it" in post["url_overridden_by_dest"]:
                        body.append(create_video_placeholder_from_post(post, soup))
                    elif "youtube.com" in post["url_overridden_by_dest"] or "youtu.be" in post["url_overridden_by_dest"]:
                        body.append(create_youtube_video_from_post(post, soup))
                    else:
                        body.append(create_video_from_post(post, soup))

                if "gallery_data" in post:
                    gallery_images = await create_gallery_from_post(session, post, soup)
                    body.extend(gallery_images)

                comments_text = create_comments_text(post, soup)
                body.append(comments_text)

    return soup.prettify()


async def get_gallery_image_urls(session: aiohttp.ClientSession, url: str) -> List[str]:
    """
    Fetches the URLs of images in a gallery post asynchronously.
    """
    async with session.get(url) as response:
        content = await response.text()
        soup = BeautifulSoup(content, features="html.parser")
        imgs = soup.find_all("img", attrs={"class": "media-lightbox-img"})

        urls = []
        for img in imgs:
            if "src" in img.attrs:
                urls.append(img["src"])
            elif "data-lazy-src" in img.attrs:
                urls.append(img["data-lazy-src"])
        return urls


def create_message(html: str) -> MIMEMultipart:
    """
    Creates an email message with the given HTML content.
    """
    message = MIMEMultipart("alternative")
    message["Subject"] = "Reddit Roundup"
    message["From"] = "test"
    message["To"] = receiver_email
    part = MIMEText(html, "html")
    message.attach(part)
    return message


async def send_email(html: str):
    """
    Sends an email with the given HTML content asynchronously.
    """
    with open("password.txt", "r") as f:
        password = f.read().strip()

    message = create_message(html)
    context = ssl.create_default_context()

    await aiosmtplib.send(
        message,
        hostname="smtp.gmail.com",
        port=465,
        use_tls=True,
        username=sender_email,
        password=password,
        sender=sender_email,
        recipients=[receiver_email],
    )
    print(f"Email sent to {receiver_email}")


async def main():
    """ Main function to fetch hot posts from subreddits, create the email content, and send the email asynchronously."""
    subreddits = ["feedthebeast", "obsidianmd", "amazingmarvin", "datahoarders"]
    async with aiohttp.ClientSession() as session:
        tasks = [get_hot_posts_for_subreddit(session, subreddit) for subreddit in subreddits]
        full_data = await asyncio.gather(*tasks)

    email_html = await create_email(full_data)
    await send_email(email_html)


if __name__ == "__main__":
    asyncio.run(main())