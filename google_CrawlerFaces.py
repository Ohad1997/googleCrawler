# Image collecting script, Ohad Baehr, Python 3.6

# Import Libraries
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as BS
import os
import json
import sys
import time
import requests
import numpy as np
import multiprocessing as mp


# Libraries imported to find faces
import cv2
import dlib

SCALE_FACTOR = 0.6 # Determines the resize amount of the image when its processed, bigger= better detection but slower
detector = dlib.get_frontal_face_detector()



directory = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Images") # Make a new folder called "Images" in the current folder
requestPool= mp.cpu_count() * 4 # Determines the amount of proccesses working simultaneously for sending requests to download images


def findFaces(link):
    try:
        r = requests.get(link, allow_redirects=False, timeout=10)
        nparr = np.fromstring(r.content, np.uint8)
        im = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (int(gray.shape[1] * SCALE_FACTOR),int(gray.shape[0] * SCALE_FACTOR))) 
        rects = detector(gray, 1)
        if rects:
            fname = os.path.join(directory, link.split('/')[-1])
            with open(fname, 'wb') as f:
                f.write(r.content)
    except Exception as e:
        print("Download failed:", e)  


def sliceSource(source):
    soup = BS(source, "lxml")
    return [imtype(a) for a in soup.find_all("div",{"class":"rg_meta"})] 


def downloadImg(link):
    print(f"downloading: {link}")
    try:
        r = requests.get(link, allow_redirects=False, timeout=10)
        fname=os.path.join(os.path.dirname(os.path.abspath(__file__)),"images",link.split('/')[-1])
        open(fname, 'wb').write(r.content)
    except Exception as e:
        print("Download failed:", e) 

def imtype(a):
    ja=json.loads(a.text)
    link, ftype = ja["ou"]  ,ja["ity"]
    findText= link.lower().find(f".{ftype}")
    if findText !=-1:
        link = link[:findText+4]
    return link

def openUrl(browser,searchtext):
    url = "https://www.google.com/search?q="+searchtext+"&source=lnms&tbm=isch"
    # Open the link
    browser.get(url)
    print("Getting you a lot of images. This may take a few moments...")
    repeatAmount=120 # A safe range to get a minimum of 600 images
    for _ in range(repeatAmount):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scroll to bottom of page
        try:
            browser.find_element_by_id("smb").click() # Click on "show more images" button
        except Exception:
            pass

    source = browser.page_source
    return source


def extended_openUrl(browser,imgUrl):
    gImagesUrl= "https://images.google.com/"
    # Open google images
    browser.get(gImagesUrl)
    print("Getting you you more images related to your search queury...")
    browser.find_element_by_class_name("S3Wjs").click() # Search by url
    time.sleep(0.5)
    inputElement = browser.find_element_by_class_name("lst") # Search button
    inputElement.send_keys(imgUrl)
    time.sleep(0.5)
    inputElement.send_keys(Keys.ENTER)
    try:
        browser.find_element_by_class_name("mnr-c") # This class only shows up when google returns an error
        return None
    except Exception: 
        pass
    time.sleep(0.5)
    textElement=browser.find_element_by_class_name("gLFyf") # Input text
    searchtext= textElement.get_attribute('value').replace(" ", "+")
    source=openUrl(browser,searchtext)
    return source
    
    
    
#------------- Main Program -------------#
def main():
    searchtext = "face" # The search query
    sTime = time.time()
    options = webdriver.ChromeOptions()
    
    #Options for better performance
    options.add_argument('--no-sandbox')
    options.add_argument("--headless")
    options.add_argument('--log-level=3')

    try:
        browser = webdriver.Chrome('chromedriver', chrome_options=options)
    except Exception as e:
        print("Looks like we cannot locate the path the 'chromedriver' (use the '--chromedriver' "
                "argument to specify the path to the executable.) or google chrome browser is not "
                "installed on your machine (exception: %s)" % e)
        sys.exit()

    source= openUrl(browser,searchtext) # Get page source

    if not os.path.exists(directory): # If folder "Images" doesnt exist, create it
        os.makedirs(directory)

    ActualImages=sliceSource(source) # Divides the Images urls
    with mp.Pool(requestPool) as p: # Workers downloading the Images simultaneously
        p.map(findFaces, [url for url in ActualImages])

    for imgUrl in ActualImages:
        if len(imgUrl)>70: # Url is too long so cut to the chase before getting an error
            continue
        source= extended_openUrl(browser,imgUrl)# Get related images
        if not source:
            continue
        SecondaryImages=sliceSource(source)# Divides the image urls
        with mp.Pool(requestPool) as p:# Workers downloading the images simultaneously
            p.map(findFaces, [url for url in SecondaryImages])



    # Speed check
    print(f"downloaded and processed: {len([name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))])} images in {time.time() - sTime} seconds")


if __name__=="__main__":
    main()
