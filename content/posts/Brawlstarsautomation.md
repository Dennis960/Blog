---
title: "Automated screenshots for BrawlStars"
date: 2021-08-07
author: "Dennis"
image: Robot.png
---

# Automated screenshots for BrawlStars

A bot that automatically makes screenshots of the competition winner’s map every day.

That was my goal.

## Why would I need to build something like that?

There is this website of my brother [brawltime.ninja](https://brawltime.ninja) on which you can have a look at your stats and playtime in BrawlStars. It’s a mobile game (I don’t really know what it is about as I have barely ever played it).

Fact is that there is a publicly available API to receive any statistics of a player by his in-game tag, so my brother made a website to visualize these statistics.

You can find a lot of other information about BrawlStars on his website as well such as what character you should play on what map and how you should play to have the greatest chance at winning.

In BrawlStars you play on a prebuilt map. Most maps are made by the developers of the game with one major exception. And that is the Competition Map.

It is a map that changes every day. The community of BrawlStars gets to vote which map will win the competition. As there is no way to get an image of the in-game maps via the API and there is also no way to scrape the map from the APK, someone has to take a screenshot every day and upload it.

For a while my brother did that himself for his website.

That is where this project comes into play.

## What did I do?

I connected a real Android device (an old one still lying around in our house) to a Raspberry Pi (the same that I use for my LED with telegram project).

The Raspberry Pi is connected to LAN. It runs a python script every day at 10:30 am.

All the script does is:

- Turn on the phone
- Open BrawlStars
- Click on some right buttons to navigate to the map
- Take a screenshot
- Upload the screenshot to my brother’s server
- Send a notification that the screenshot was uploaded successfully
- Restart if anything went wrong

Easy right?

## Now comes the fun part: Coding!!!

First step was to figure out how to communicate with an Android device.

I tried different emulators and websites, but they all wouldn’t run BrawlStars because of the safety precautions that the developers took. A real Android device was my only reliable option.

Looking through my project now, there is a lot to cover if I want to explain everything so be prepared for a long blog post:

### Tools Used:

- Android debug bridge (ADB) for communication with the phone.
- OpenCV for image recognition.
- Telegram bot for error communication.
- SFTP for uploading images.
- PIL python image library for resizing and cutting screenshots.

### ADB Commands:

First some imports:

```python
import subprocess
import vars
import time
import images
from my_logging import my_print as print
```

`vars` stores things like is the script running in debug mode? or what should I name the final image?

`images` will be covered later in this post.

`my_logging` is made for debugging purposes and not that important.

`subprocess` is used to run all the ADB commands:

```python
def run_adb_command(command):
    """runs an adb command."""
    return subprocess.Popen(vars.pathToAdb + command, shell=True, stdout=subprocess.PIPE)
```

Then there are some simplified versions of the standard ADB commands whose names are self-explanatory:

```python
def scroll(x1, y1, x2, y2):
    """Simulates a swipe on the phone from position x1, y1 to position x2, y2."""
    print('scrolling')
    run_adb_command('shell input swipe '+str(x1)+' '+str(y1)+' '+str(x2)+' '+str(y2))

def tap(x, y):
    """Simulates a tap on the display at the position x, y"""
    print('tapping')
    run_adb_command('shell input tap '+str(x)+' '+str(y))

def get_screenshot():
    """Saves the screenshot from the phone as screenshot.png"""
    print('taking screenshot')
    process = run_adb_command('shell screencap -p')
    data = process.stdout.read()
    if vars.isWin:
        data = data.replace(b'\r\n', b'\n')
    f = open(vars.pathToScript+vars.screenshotFilename, 'wb')
    f.write(data)
    f.close()

def is_device_on():
    """Returns True if the device is on and False if the device is off."""
    process = run_adb_command('shell dumpsys power')
    data = process.stdout.read()
    return 'state=ON' in data.decode("utf-8")

def turn_on_device():
    """Turns on the device if it is turned off"""
    print('turn on phone')
    if not is_device_on():
        run_adb_command('shell input keyevent 26')
    else:
        print('device already on')

def turn_off_device():
    """Turns off the device if the device is on. It may occur that the device holds the power button too long and doesn't turn off. In that case the script runs itself again."""
    if is_device_on():
        run_adb_command('shell input keyevent 26')
    else:
        print('device already off')
    time.sleep(3)
    if is_device_on():
        print('shutdown unsuccessful, trying again')
        turn_off_device()

def is_device_connected():
    """Returns True if a phone is connected to the PC via USB and the phone has granted access to the PC."""
    process = run_adb_command('get-state')
    data = process.stdout.read().decode("utf-8")
    return not 'error' in data and 'device' in data

def wait_for_device_connect():
    """Pauses the script until a phone is connected to the PC via USB-Cable."""
    while not is_device_connected():
        time.sleep(1)
    print('\ndevice connected')

def reset_connection():
    run_adb_command('kill-server')

def start_brawlstars():
    print('starting brawlstars')
    run_adb_command('shell monkey -p com.supercell.brawlstars -c android.intent.category.LAUNCHER 1')

def stop_brawlstars():
    print('stopping brawlstars')
    run_adb_command('shell am force-stop com.supercell.brawlstars')

def update_brawlstars():
    """Not yet implemented."""
    print('opening play store')
    run_adb_command("shell am start -a android.intent.action.VIEW -d 'market://details?id=com.supercell.brawlstars'")
```

You may have noticed that the last command is not implemented yet. That is because I was too lazy to do that, and it was easier to update the game on the phone manually every time it would be necessary.

The final method in my `adbCommand.py` file is used to wait until a specific image is visible on the screen:

```python
def wait_for_image_to_appear(imagePath):
    """Makes screenshots of the device until the specified image is recognized via cv2."""
    while True:
        image = images.load_image_from_path(vars.pathToScript + imagePath)
        get_screenshot()
        screenshot = images.load_image_from_path(vars.pathToScript+vars.screenshotFilename)
        print('searching for image', end='\r')
        if images.is_image_in_image(image, screenshot):
            break
```

This is where the `images` import comes to play:

```python
import cv2
import numpy
from my_logging import my_print as print

def is_image_in_image(smallImage, largeImage):
    """Returns true if the smallImage is found in the largeImage using cv2. Images have to be of type cv2 image you can use the 'load_image_from_path' method"""
    if smallImage is None:
        print('small image is none')
        return False
    if largeImage is None:
        print('large image is none')
        return False
    method = cv2.TM_CCOEFF_NORMED
    result = cv2.matchTemplate(smallImage, largeImage, method)
    threshold = 0.8
    loc = numpy.where(result >= threshold)
    w, h = largeImage.shape[::-1]
    for pt in zip(*loc[::-1]):  # Switch columns and rows
        cv2.rectangle(largeImage, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
        print('\nimage found!')
        return True

def load_image_from_path(path):
    """Loads an image of type .png or .jpg from a given path and returns it in the cv2 format."""
    print('converting image path to cv2 image', path)
    image = cv2.imread(path, 0)
    return image
```

The comments already explain what the methods do. With the help of `cv2` and template matching I check if an image exists in another image. That part is important to check the success of every part of my script. It is also important because clicking on a button in-game doesn’t end up in an instant action but takes time, so I need to wait until a window is fully loaded.

Just for the sake of being complete I will show my terrible solution for logging any debug and error messages:

```python
import logging
import vars
logging.basicConfig(filename=(vars.pathToScript+'notification.log'),
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
def my_print(*args, **kwargs):
    print(*args, *kwargs)
    logging.info(str(args))
```

It’s not very pretty. All it does is save the `print()` calls inside a file, so I can have a look at them if the script is run in the background.

An important part when working with so many dependencies is handling errors. There is no way at all to prevent every error when fiddling around with so many libraries and a real Android device. Having something that works once or twice in a row doesn’t guarantee that it will work consistently forever.

Some errors that occurred while testing were:

- The phone not turning on
- The app not starting
- Pop up windows suddenly blocking the view
- A notification or the voice manager popping up
- Internet problems
- Loose contact at the cable
- Screenshots not getting saved correctly
- ADB striking to start a server and a connection to the Raspberry Pi

The simplest solution would be to restart the entire script whenever something goes wrong. But how would I know if something went wrong? I am not able to predict which errors may occur.

I solved that problem by putting a timer around everything that waits for 5 minutes. If my script has not finished until the end of that timer an exception gets thrown and the entire thing restarts. So if something gets stuck it will just try again after 5 minutes.

Some code is copied from StackOverflow, but I had to change it a bit to make it work properly.

```python
import sys
import threading
import _thread as thread
import signal
import time
from my_logging import my_print as print

def start_timed_execution(function):
    '''
    returns True if ended successfully\n
    returns False if not ended in time
    '''
    try:
        function()
    except KeyboardInterrupt:
        return False
    return True

def quit_function(fn_name):
    # print to stderr, unbuffered in Python 2.
    print('Process took too long')
    sys.stderr.flush() # Python 3 stderr is likely buffered.
    thread.interrupt_main() # raises KeyboardInterrupt

def exit_after(s):
    '''
    use as decorator to exit process if
    function takes longer than s seconds
    '''
    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, quit_function, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result
        return inner
    return outer
```

Now that the basics are covered I can explain the core of the program. This one is the only file I need to change to make adjustments whenever BrawlStars has an update that changes the layout or place of the map.

I need most of the scripts I already talked about as well as `uploadScreenshot` which does exactly what it says and the `notificationManager` which is covered in the Telegram API blog post.

```python
import time
import os
import uploadScreenshot
import screenshotCutter
import images
import adbCommand as adb
import vars
import executionManager
import notificationManager
import configs
from my_logging import my_print as print
```

The following method handles everything concerning the Android phone:

- Starting BrawlStars
- Navigating to the map
- Saving the map as a screenshot
- Turning off the phone

```python
@executionManager.exit_after(120)
def get_automated_screenshot():
    """Runs the script that automatically saves the screenshot as screenshot.png. If it doesn't finish within 120 seconds it throws an error."""
    adb.turn_on_device()
    adb.stop_brawlstars()
    time.sleep(3)
    adb.start_brawlstars()
    adb.wait_for_image_to_appear('SettingsButton.png')
    print('tapping info button')
    adb.tap(1050, 1000)
    adb.wait_for_image_to_appear('Home.png')
    print('tapping community tab')
    adb.tap(1170, 1060)
    time.sleep(2)
    print('tapping info button')
    adb.tap(1040, 620)
    adb.wait_for_image_to_appear('ExitButton.png')
    print('tapping heart')
    adb.tap(1530, 330)
    time.sleep(2)
    adb.get_screenshot()
    adb.stop_brawlstars()
    adb.turn_off_device()
```

The rest of the main file is used to handle errors and upload the screenshot:

```python
config = configs.load_config()
if config.get_shouldRunScreenshotAutomation():
    startTime = time.time()

    adb.wait_for_device_connect()
    failCounter = 0
    while not executionManager.start_timed_execution(get_automated_screenshot) and failCounter < 5:
        print('starting Script')
        failCounter += 1
        pass
    if failCounter >= 5:
        print('script failed')
        notificationManager.broadcast_to_subscribers(message='script failed 5 times in a row', photoPath=vars.pathToScript+vars.screenshotFilename)
    else:
        screenshot =  images.load_image_from_path(vars.pathToScript+vars.screenshotFilename)
        backButtonImage =  images.load_image_from_path(vars.pathToScript+'Heart.png')
        if screenshot is not None and images.is_image_in_image(backButtonImage, screenshot):
            print('image correct, uploading...')
            screenshotCutter.cut(vars.pathToScript + vars.screenshotFilename, vars.pathToScript + vars.cuttedscreenshotFilename)
            uploadScreenshot.upload(vars.pathToScript, vars.cuttedscreenshotFilename)
            uploadScreenshot.upload(vars.pathToScript, vars.screenshotFilename, "_full")
            notificationManager.broadcast_to_subscribers(photoPath=vars.pathToScript + vars.cuttedscreenshotFilename, message='Screenshot uploaded')
        else:
            print('screenshot not right')
            notificationManager.broadcast_to_subscribers(message='screenshot failed', photoPath=vars.pathToScript+vars.screenshotFilename)

    print('process took', time.time()-startTime, 's')
else:
    print('process not started')
```

Some interesting files left to look at would be `screenshotCutter` and `uploadScreenshot` though the `screenshotCutter` is not that fun to look at, so I won’t even try to explain it in detail:

```python
import numpy as np
from PIL import Image
from my_logging import my_print as print

borderColor = (11, 75, 190)
pixelsToChange = []

def getLeft(image, pix):
    """Returns the most left pixel which has the border color."""
    for x in range(0, image.size[0]-1):
        for y in range(0, image.size[1]):
            if colorsMatch(pix, x, y, borderColor):
                return x

def goRight(image, pix, left):
    """Returns the most right, top and bottom pixel which has the border color."""
    topMostBorder = image.size[1]
    bottomMostBorder = 0
    for x in range(left+1, image.size[0]):
        borderFound = False
        for y in range(0, image.size[1]):
            if colorsMatch(pix, x, y, borderColor):
                if borderFound and bottomMostBorder < y:
                    bottomMostBorder = y
                elif topMostBorder > y:
                    topMostBorder = y
                borderFound = True
        if not borderFound:
            break
    return x, topMostBorder, bottomMostBorder

def markEdge(left, right, top, bottom, pix):
    """Debug. Marks all pixels that are checked and surrounds the cutted Screenshot in yellow."""
    for x in range(left, right):
        pixelsToChange.append([x, top, 200, 200, 0])
    for y in range(top, bottom):
        pixelsToChange.append([right, y, 200, 200, 0])
    for x in range(right, left, -1):
        pixelsToChange.append([x, bottom, 200, 200, 0])
    for y in range(bottom, top, -1):
        pixelsToChange.append([left, y, 200, 200, 0])
    for c in pixelsToChange: #c[x, y, r, g, b]
        prevColor = pix[c[0], c[1]]
        prevColor = [prevColor[0], prevColor[1], prevColor[2]]
        for i in range(0, 3):
            prevColor[i] += c[i+2]
            if prevColor[i] > 255:
                prevColor[i] = 255
        pix[c[0], c[1]] = (prevColor[0], prevColor[1], prevColor[2])
def cut(path, savePath):
    """Cuts the brawlstars map screenshot so that only the map is visible. Returns the name of the cutted Screenshot File."""
    image = Image.open(path).convert('RGB')
    debugImage = image.copy()
    pix = image.load()
    left = getLeft(image, pix)
    right, top, bottom = goRight(image, pix, left)
    image = image.crop((left, top, right, bottom))
    image.save(savePath)

    markEdge(left, right, top, bottom, debugImage.load())
    idx = savePath.index('.')
    savePath = savePath[:idx] + '_debug' + savePath[idx:]
    debugImage.save(savePath)

    return savePath.split('/')[-1]
def colorsMatch(pix, x, y, color2, tolerance=5):
    """Checks if two colors are similar with a given tolerance."""
    color1 = pix[x, y]
    for i in range(0, 3):
        if not abs(color1[i] - color2[i]) <= tolerance:
            pixelsToChange.append([x, y, 50, 0, 0])
            return False
    pixelsToChange.append([x, y, 0, 50, 0])
    return True
```

The screenshotCutter takes the screenshot of the map and removes everything around the map. Here is an example.

First the original screenshot:

![Original Screenshot](/images/BrawlStarsAutomation/download.jpeg)

I then find the border of the map:

![Border of the map](/images/BrawlStarsAutomation/downloadCuttedScreenshot_debug.png)

And then I cut out the map and save it:

![Map](/images/BrawlStarsAutomation/downloadCuttedScreenshot.png)

```python
import numpy as np
from PIL import Image
from my_logging import my_print as print

borderColor = (11, 75, 190)
pixelsToChange = []

def getLeft(image, pix):
    """Returns the most left pixel which has the border color."""
    for x in range(0, image.size[0]-1):
        for y in range(0, image.size[1]):
            if colorsMatch(pix, x, y, borderColor):
                return x
def goRight(image, pix, left):
    """Returns the most right, top and bottom pixel which has the border color."""
    topMostBorder = image.size[1]
    bottomMostBorder = 0
    for x in range(left+1, image.size[0]):
        borderFound = False
        for y in range(0, image.size[1]):
            if colorsMatch(pix, x, y, borderColor):
                if borderFound and bottomMostBorder < y:
                    bottomMostBorder = y
                elif topMostBorder > y:
                    topMostBorder = y
                borderFound = True
        if not borderFound:
            break
    return x, topMostBorder, bottomMostBorder

def markEdge(left, right, top, bottom, pix):
    """Debug. Marks all pixels that are checked and surrounds the cutted Screenshot in yellow."""
    for x in range(left, right):
        pixelsToChange.append([x, top, 200, 200, 0])
    for y in range(top, bottom):
        pixelsToChange.append([right, y, 200, 200, 0])
    for x in range(right, left, -1):
        pixelsToChange.append([x, bottom, 200, 200, 0])
    for y in range(bottom, top, -1):
        pixelsToChange.append([left, y, 200, 200, 0])
    for c in pixelsToChange: #c[x, y, r, g, b]
        prevColor = pix[c[0], c[1]]
        prevColor = [prevColor[0], prevColor[1], prevColor[2]]
        for i in range(0, 3):
            prevColor[i] += c[i+2]
            if prevColor[i] > 255:
                prevColor[i] = 255
        pix[c[0], c[1]] = (prevColor[0], prevColor[1], prevColor[2])
def cut(path, savePath):
    """Cuts the brawlstars map screenshot so that only the map is visible. Returns the name of the cutted Screenshot File."""
    image = Image.open(path).convert('RGB')
    debugImage = image.copy()
    pix = image.load()
    left = getLeft(image, pix)
    right, top, bottom = goRight(image, pix, left)
    image = image.crop((left, top, right, bottom))
    image.save(savePath)

    markEdge(left, right, top, bottom, debugImage.load())
    idx = savePath.index('.')
    savePath = savePath[:idx] + '_debug' + savePath[idx:]
    debugImage.save(savePath)

    return savePath.split('/')[-1]
def colorsMatch(pix, x, y, color2, tolerance=5):
    """Checks if two colors are similar with a given tolerance."""
    color1 = pix[x, y]
    for i in range(0, 3):
        if not abs(color1[i] - color2[i]) <= tolerance:
            pixelsToChange.append([x, y, 50, 0, 0])
            return False
    pixelsToChange.append([x, y, 0, 50, 0])
    return True
```

The code looks awful, but it may be one of the best solutions.

It is very unlikely that anyone will find out the bot token and use the bot, but to prevent that from happening and to save some other important settings, I created a config system.

```python
import json
import vars
from collections import namedtuple
import os
import time
from my_logging import my_print as print
```

It consists of a User where I store whether someone is currently trying to send or get a screenshot from the server as well as the rank and subscription status:

```python
class User:
    """A class that stores parameters of a user in a file named after the userId.config"""
    def __init__(self, userId, subscribed=False, waitingForScreenshot=False, waitingForScreenshotRequest=False, rank=[], waitingForDate=False, documentNames=None):
        """Initlialize the User class with a userId and optional parameters"""
        self.userId, self.subscribed, self.waitingForScreenshot, self.waitingForScreenshotRequest, self.rank, self.waitingForDate, self.documentNames = userId, subscribed, waitingForScreenshot, waitingForScreenshotRequest, rank, waitingForDate, documentNames
    def save(self):
        """Saves the configuration to a file named <userId>.config"""
        save_user_config(self, self.userId)
#------------------------------------------#
    def get_subscribed(self):
        """Returns whether the user is subscribed to broadcast messages"""
        return self.subscribed
    def set_subscribed(self, value):
        """Sets the subscription status of the user to broadcast messages to True or False. Don't forget to save() afterwards."""
        self.subscribed = value
        if value:
            load_config().add_subscriber(self.userId).save()
        else:
            load_config().remove_subscriber(self.userId).save()
        return self
#------------------------------------------#
    def get_waitingForScreenshot(self):
        """Returns whether the script is waiting to receive a screenshot as a document from the user."""
        return self.waitingForScreenshot
    def set_waitingForScreenshot(self, value):
        """Set whether the script is waiting to reveice a screenshot as a document from the user. Don't forget to save() afterwards."""
        self.waitingForScreenshot = value
        return self
#------------------------------------------#
    def get_waitingForScreenshotRequest(self):
        """Returns whether the script is waiting for a date input and sending a screenshot afterwards"""
        return self.waitingForScreenshotRequest
    def set_waitingForScreenshotRequest(self, value):
        """Set whether the script should be returning a screenshot after the user types in a date. Don't forget to save() afterwards."""
        self.waitingForScreenshotRequest = value
        return self
#------------------------------------------#
    def get_rank(self):
        """Returns the ranks of a user as an array of String."""
        return self.rank
    #Todo methods to add rank and to remove rank from the rank list
    def set_rank(self, value):
        """Sets the rank of the user. Highest rank is Admin. This script is commented out for safety purposes. Don't forget to save() afterwards."""
    #     self.rank = value
        return self
#------------------------------------------#
    def get_waitingForDate(self):
        """Returns whether the script is waiting for a user input in form of a date string as True or False."""
        return self.waitingForDate
    def set_waitingForDate(self, value):
        """Set to True to wait for the user to input a date string. Don't forget to save() afterwards."""
        self.waitingForDate = value
        return self
#------------------------------------------#
    def get_documentNames(self):
        """Returns the names of documents that are stored in vars.pathToScript."""
        return self.documentNames
    def set_documentNames(self, value):
        """Set the names of documents that are stored in vars.pathToScript. Dont't forget to save() afterwards"""
        self.documentNames = value
        return self
#------------------------------------------#
    def cancel_all(self):
        """Cancels all activities by setting all booleans to their default "False" state. Executes the save() command by itself."""
        self.set_waitingForDate(False).set_waitingForScreenshot(False).set_waitingForScreenshotRequest(False).save()
        return self
#------------------------------------------#
```

And a config file for the script that saves subscribers, and a boolean to control the execution of the script:

```python
class Config:
    """This class stores the configurations of the entire script in the config.config"""
    def __init__(self, subscribers=[], shouldRunScreenshotAutomation=False):
        self.subscribers, self.shouldRunScreenshotAutomation = subscribers, shouldRunScreenshotAutomation
    def save(self):
        save_config(self)
#------------------------------------------#
    def add_subscriber(self, sub):
        """Add a subscriber to the config. Don't forget to save() afterwards."""
        if not sub in self.subscribers:
            self.subscribers.append(sub)
        return self
    def remove_subscriber(self, sub):
        """Remove a subscriber from the config. Don't forget to save() afterwards."""
        if sub in self.subscribers:
            self.subscribers.remove(sub)
        return self
#------------------------------------------#
    def get_shouldRunScreenshotAutomation(self):
        """Returns True if the BSA script should be running every day at 10:30am or False if it shouldn't."""
        return self.shouldRunScreenshotAutomation
    def set_shouldRunScreenshotAutomation(self, value):
        """Set the boolean which determines whether the BSA script should be running every day at 10:30am or False if it shouldn't. Don't forget to save() afterwards."""
        self.shouldRunScreenshotAutomation = value
        return self
#------------------------------------------#
def save_user_config(user, userId):
    """Saves the specified user config under the userId."""
    userData = json.dumps(user.__dict__)
    open(vars.pathToScript + str(userId) + '.config', 'w+').write(userData)
def load_user_config(userId):
    """Loads the user config by a given userId = chat_id and returns it as a User class. Returns a new class if it couldn't load."""
    userDataFilename = vars.pathToScript + str(userId)
    userDataPath = userDataFilename + '.config'
    if not os.path.exists(userDataPath):
        return User(userId)
    userData = open(userDataPath, 'r').read()
    try:
        return User(**json.loads(userData))
    except Exception as e:
        print(e)
        open(userDataFilename + '_backup_' + str(time.time()), 'w+').write(userData)
        return User(userId)
#------------------------------------------#
def save_config(config):
    """Saves the general config.config."""
    configData = json.dumps(config.__dict__)
    open(vars.pathToScript + 'config.config', 'w+').write(configData)
def load_config():
    """Loads the general config.config and returns it as a Config class. Returns a new class if it couldn't load."""
    configDataFilename = vars.pathToScript + 'config'
    configDataPath = configDataFilename + '.config'
    if not os.path.exists(configDataPath):
        return Config()
    configData = open(configDataPath, 'r').read()
    try:
        return Config(**json.loads(configData))
    except Exception as e:
        print(e)
        open(configDataFilename + '_backup_' + str(time.time()), 'w+').write(configData)
        return Config()
```

The last part to cover in this post would be the uploadScreenshot part:

```python
import pysftp
from datetime import datetime
from my_logging import my_print as print

def upload(pathToScript, screenshotFilename, ext="", dateString=""):
    """Uploads a .png to the brawltime.ninja server with a given filename and a date. If the date is not set, it will use the current date."""
    print('assining date string')
    now = datetime.now()
    if not dateString:
        dateString = now.strftime("%Y-%m-%d")
    print(dateString)
    print('getting key from', pathToScript+'********************.key')
    try:
        connection = pysftp.Connection(host="schneefux.xyz", username="*********", private_key=pathToScript+'************.key')
        print('connection established')
        connection.put(pathToScript+screenshotFilename, "***********************************/"+dateString+ext+".png")
        print('image uploaded to', "*************************************/"+dateString+ext+".png")
        connection.close()
    except:
        print('trying again... Are you connected to internet?')
        upload(pathToScript, screenshotFilename, ext)
        return "something went wrong"
    return 'image uploaded to', "*************************************/competition-winners/"+dateString+ext+".png"
```

Just for safety reasons I replaced vulnerable data with stars. The script establishes a connection to the server of my brother. It uses a username and key and uploads the image via SFTP.

My Telegram API plays a big role in the communication with the user (my brother and me) so I want to cover that part as well. The groundwork is covered in my Telegram Api blog post.

The only thing left to show would be the commands I implemented:

```python
from notificationManager import send_message, send_photo, download_file
import vars
import screenshotCutter
import uploadScreenshot
from configs import User, Config
import configs
import re
from my_logging import my_print as print
import os
import urllib
import adbCommand as adb

# a dictionary of commands with layout 'command' : helpText
commandDict = {
    '/help' : "shows this information",
    '/subscribe' : "get updates on the brawlbot",
    '/unsubscribe' : "don't get any more updates",
    '/sendScreenshot' : "send a screenshot for processing",
    '/getScreenshot' : "get the screenshots for a specific date",
    '/cancel' : "cancels all operations",
    '/startAutomation' : "starts the screenshotAutomation",
    '/stopAutomation' : "stops the screenshotAutomation",
    '/shutdown' : "turns off the raspberry pi (use in emergency only)",
    '/reboot' : "reboots the raspberry pi",
    '/restartAutomation' : "restarts the screenshot Automation script",
    '/me' : "shows the personalized config",
    '/turnOffPhone' : "Turns off the phone via ADB-Command",
    '/turnOnPhone' : "Turns on the phone via ADB-Command"
}


def reply_help(update, chat_id):
    help = open(vars.pathToScript + 'brawlBotHelp', 'r').read() + '\n'
    for key in commandDict:
        help += '\n' + key + ' - ' + commandDict.get(key)
    send_message(help, chat_id)
def reply_subscribe(update, chat_id):
    user = configs.load_user_config(chat_id)
    if not user.get_subscribed():
        user.cancel_all().set_subscribed(True).save()
        send_message("Successfully subscribed to notifications. You can /unsubscribe to unsubscribe.", chat_id)
    else:
        send_message("You are already subscribed. You can /unsubscribe to unsubscribe.", chat_id)
def reply_unsubscribe(update, chat_id):
    user = configs.load_user_config(chat_id)
    if user.get_subscribed():
        user.cancel_all().set_subscribed(False).save()
        send_message("Successfully unsubscribed from notifications. You can /subscribe to subscribe again.", chat_id)
    else:
        send_message("You are already unsubscribed. You can /subscribe to subscribe.", chat_id)
def reply_sendScreenshot(update, chat_id):
    user = configs.load_user_config(chat_id)
    user.cancel_all().set_waitingForScreenshot(True).save()
    send_message("please send your screenshot now", chat_id)
def reply_getScreenshot(update, chat_id):
    user = configs.load_user_config(chat_id)
    user.cancel_all().set_waitingForDate(True).set_waitingForScreenshotRequest(True).save()
    send_message('Please send a date to this image in the following format: YYYY-mm-dd', chat_id)
def reply_cancel(update, chat_id):
    user = configs.load_user_config(chat_id)
    user.cancel_all()
    send_message('Canceled all actions successfully!', chat_id)
def reply_startAutomation(update, chat_id):
    config = configs.load_config()
    if not config.get_shouldRunScreenshotAutomation():
        config.set_shouldRunScreenshotAutomation(True).save()
        send_message('screenshotAutomation successfully started', chat_id)
    else:
        send_message('screenshotAutomation already running', chat_id)
def reply_stopAutomation(update, chat_id):
    config = configs.load_config()
    if config.get_shouldRunScreenshotAutomation():
        config.set_shouldRunScreenshotAutomation(False).save()
        send_message('screenshotAutomation successfully stopped', chat_id)
    else:
        send_message('screenshotAutomation already stopped', chat_id)
def reply_shutdown(update, chat_id):
    user = configs.load_user_config(chat_id)
    if "Admin" in user.get_rank():
        send_message('Admin recognized. Command not implemented yet.', chat_id)
    else:
        send_message('You need to be of rank Admin to run this command.', chat_id)
        return
def reply_reboot(update, chat_id):
    user = configs.load_user_config(chat_id)
    if "Admin" in user.get_rank():
        send_message('Admin recognized. Now rebooting Raspberry pi. Command not implemented yet', chat_id)
    else:
        send_message('You need to be of rank Admin to run this command.', chat_id)
        return
def reply_restartAutomation(update, chat_id):
    try:
        os.system(vars.pythonPath + vars.pathToScript + 'brawlstarsScreenshotAutomation.py')
        send_message('restarted', chat_id)
    except:
        send_message('failed', chat_id)
def reply_me(update, chat_id):
    user = configs.load_user_config(chat_id)
    userDict = user.__dict__
    userConfig = ""
    for key in userDict:
        userConfig += key + ': ' + str(userDict.get(key)) + '\n'
    send_message(userConfig, chat_id)
def reply_turnOffPhone(update, chat_id):
    adb.turn_off_device()
    send_message('Phone turned off!', chat_id)
def reply_turnOnPhone(update, chat_id):
    adb.turn_on_device()
    send_message('Phone turned on!', chat_id)
def reply__command_not_found(update, chat_id):
    send_message('command not found', chat_id)

def reply__date(update, chat_id):
    def is_date_valid(dateString):
        r = re.compile(r'([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))')
        return r.match(dateString) is not None

    dateString = update["message"]["text"]

    if not is_date_valid(dateString):
        send_message("your given format doesn't match YYYY-mm-dd", chat_id)
        return
    send_message("date successfully received", chat_id)

    user = configs.load_user_config(chat_id)
    if user.get_waitingForScreenshot():
        screenshotFilename = user.get_documentNames()[0]
        cuttedScreenshotFilename = user.get_documentNames()[1]

        upload1 = uploadScreenshot.upload(vars.pathToScript, cuttedScreenshotFilename, dateString=dateString)
        upload2 = uploadScreenshot.upload(vars.pathToScript, screenshotFilename, ext='_full', dateString=dateString)
        send_message(str(upload1) + '\n' + str(upload2), chat_id)
        user.set_documentNames([]).set_waitingForScreenshot(False).set_waitingForDate(False).save()
    elif user.get_waitingForScreenshotRequest():
        user.set_waitingForDate(False).set_waitingForScreenshotRequest(False).save()
        url = "*********************************/competition-winners/"+dateString+".png"
        send_message(url, chat_id)
def reply__text(update, chat_id):
    print('text received')

    user = configs.load_user_config(chat_id)
    if user.get_waitingForDate():
        reply__date(update, chat_id)

def reply__document(update, chat_id):
    fileType = '.' + update["message"]["document"]["mime_type"].split('/')[1]
    file_id = update["message"]["document"]["file_id"]
    user = configs.load_user_config(chat_id)
    if user.get_waitingForScreenshot() and not user.get_waitingForDate():
        screenshotFilename = 'download' + fileType
        downloadPath = vars.pathToScript + screenshotFilename
        download_file(file_id, downloadPath)

        cuttedScreenshotFilename = 'downloadCuttedScreenshot' + '.png'
        savePath = vars.pathToScript + cuttedScreenshotFilename
        send_message("Screenshot received successfully! Please wait a few seconds for the process to finish.", chat_id)
        screenshotCutter.cut(downloadPath, savePath)
        send_photo(savePath, chat_id)
        send_message('Please send a date to this image in the following format: YYYY-mm-dd', chat_id)

        user.set_documentNames([screenshotFilename, cuttedScreenshotFilename]).set_waitingForDate(True).save()

def reply__photo(update, chat_id):
    user = configs.load_user_config(chat_id)
    if user.get_waitingForScreenshot():
        send_message("Did you mean to send a screenshot? Try sending it as a document for no loss in quality.", chat_id)
```

All in all, I am very happy how this project turned out. I still need to fix errors occasionally, but it is very reliable.

Looking back on my code now makes me proud because I never thought I had documented it so well and refactored so much.

I had no problems at all understanding my code half a year later.

What did I do?

I used Telegram to control the bot. I used python to control a smartphone. I took a screenshot of the competition winners map. I uploaded the screenshot to a server.

Pretty easy!
