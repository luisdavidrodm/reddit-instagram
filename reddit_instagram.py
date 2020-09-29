import urllib.request
import datetime
import time
import praw
import sys
import os
import moviepy.editor as mp
from instabot import Bot
from PIL import Image


################## OPTIONS ###################
folderpath = r"C:/Users/memes/"  # folder where images will be stored
caption_text = "Follow for more content"
caption_tags = "#memes"
top_type = "day"  # "hour, day, week, month..."
num_rounds = 50  # number of posts, should be less than 100
post_frequency = 400  # hour posts in seconds

print(f"Current image folder: {folderpath}\n")


################# INSTABOT ###################
bot = Bot()
bot.login(username="instagram_username", password="instagram_password")


################### PRAW #####################
reddit = praw.Reddit(
    client_id="id of reddit",
    client_secret="from reddit",
    username="reddit_username",
    password="password",
    user_agent="name of the project",
)


subreddit = reddit.subreddit("dankmemes")


# submissions = subreddit.hot(limit=100)
# submissions = subreddit.rising(limit=100)
# submissions = subreddit.new(limit=100)
submissions = subreddit.top(top_type, limit=100)


############## SUB-ROUTINES ##################
def reporthook(count, block_size, total_size):
    """This function is used for informing the progress of downloads"""
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * (int(duration) + 1)))
    percent = min(int(count * block_size * 100 / total_size), 100)
    sys.stdout.write(
        "\r...%d%%, %d MB, %d KB/s, %d seconds passed"
        % (percent, progress_size / (1024 * 1024), speed, duration)
    )
    sys.stdout.flush()


def DLsubmission(url, folderpath, name, extension):
    """This function is used for downloading submissions"""
    filepath = folderpath + name + extension
    urllib.request.urlretrieve(url, filepath, reporthook=reporthook)
    print("\n-> Downloaded successfully.")
    if extension == ".gif":
        print("-> Converting gif to mp4 and resizing.")
        clip = mp.VideoFileClip(filepath)
        clip = clip.resize(height=1000)
        clip.write_videofile(filepath.replace(".gif", ".mp4"))
        filepath = filepath.replace(".gif", ".mp4")
        print("-> Converted successfully.")
        extension = ".mp4"
    return filepath, extension


def printandlog(string):
    """This function is used for printing to console and logging to urllog.txt"""
    urllog = open("urllog.txt", "a")
    urllog.write(f"{string}\n")
    urllog.close
    print(string)


def renamefile(filepath):
    """This function renames the file after uploaded back to its original name"""
    try:
        os.rename(filepath + ".REMOVE_ME", filepath)
    except Exception as e:
        print("-> {}. Exception while renaming the file.".format(str(e)))


################# MAIN ROUTINE ###################
printandlog(
    "\n---------- SUBMISSIONS ------------\nBOT INITIATED: {}\nNumber of posts: {}".format(
        datetime.datetime.today().isoformat(), num_rounds
    )
)
x = 0
for submission in submissions:
    found = False
    printandlog("\nPOST NUMBER: {}".format(x + 1))
    if (
        submission.is_self == False and submission.stickied == False
    ):  # see if it is text, stickied or none.
        try:
            ################ INFO GATHERING #################
            title = submission.title
            author = submission.author
            name = submission.name
            url = submission.url
            caption = f"{caption_text}\nOriginal title: {title}\nCreated by redditor: {author}.\n{caption_tags}"
            submission_info = "Title:{}, Name:{}, Author:{},\nurl:{}".format(
                title, name, author, url
            )
            printandlog(submission_info)  # print info
            urllogsearch = open("urllog.txt", "r")
            for line in urllogsearch:
                if f"-> Submission:{name} attempted to upload." in line:
                    urllogsearch.close()
                    found = True
                    printandlog(
                        f"-> urllog.txt states that Submission:{name} was attempted to upload before. Skipping."
                    )
                    break
            if found == True:
                continue
            urllogsearch.close()
            if url.split(".").pop() == "gifv":
                url = url.replace(".gifv", ".mp4")
            extension = "." + url.split(".").pop()
            ################ URLLIB DOWNLOAD #################
            print("-> Extension when downloaded: {}".format(extension))
            filepath, extension = DLsubmission(url, folderpath, name, extension)
        except Exception as e:
            printandlog("-> {}. Skipping submission.".format(str(e)))
            continue
        print("-> Attempting to upload.")
        ################ VIDEO UPLOAD #################
        if extension == ".mp4":
            printandlog(f"-> Submission:{name} attempted to upload.")
            printandlog(f"-> But video/gif upload is not supported. Skipping.")
            continue
        ################ IMAGE UPLOAD #################
        else:
            img = Image.open(filepath)
            img = img.resize((1000, 1000), Image.NEAREST)  # resize
            img = img.convert("RGB")
            new_filepath = folderpath + name + ".jpg"
            img.save(new_filepath, "JPEG")
            if filepath != new_filepath:
                os.remove(filepath)
            printandlog(f"-> Submission:{name} attempted to upload.")
            try:
                bot.upload_photo(new_filepath, caption=caption)
            except Exception as e:
                printandlog("-> {}.".format(str(e)))
            renamefile(new_filepath)
        x += 1
        print(
            f"-> Post number {x} uploaded successfully unless stated otherwise above."
        )
        if x == num_rounds:
            break
        else:
            print("-> Current time: {}".format(datetime.datetime.today().isoformat()))
            print(f"-> Now waiting: {post_frequency} seconds until next post.")
            time.sleep(post_frequency)
    else:
        printandlog("-> Submission was stickied or just text. Skipping.")
        continue
print("\n-> END.")
