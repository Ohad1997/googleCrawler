# Image collecting script, Ohad Baehr, Python 3.6

# Import Libraries
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import os
import json
import sys
import requests
import numpy as np
import multiprocessing as mp
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import time

# Libraries imported to find faces
import cv2
import dlib

SCALE_FACTOR = 0.6 # Determines the resize amount of the image when its processed, bigger= better detection but slower
detector = dlib.get_frontal_face_detector()
directory = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Images") # Make a new folder called "Images" in the current folder
requestPool= mp.cpu_count() * 3 # Determines the amount of proccesses working simultaneously for sending requests to download images
session = requests.Session() # new session of requests

def findFaces(link):
    try:
        r=session.get(link, allow_redirects=False, timeout=4).content
        nparr = np.fromstring(r, np.uint8) 
        gray = cv2.imdecode(nparr, 0)
        if isinstance(gray,np.ndarray):
            gray = cv2.resize(gray, (int(gray.shape[1] * SCALE_FACTOR),int(gray.shape[0] * SCALE_FACTOR))) 
            rects = detector(gray, 1)
            if rects:
                fname = os.path.join(directory, link.split('/')[-1])
                with open(fname, 'wb') as f:
                    f.write(r)
                    return link
        return None
    except Exception as e:
        print(e)
        return None
        
def sliceSource(browser):
    res = [value for value in (imtype(a) for a in browser.find_elements_by_class_name("rg_meta"))  if value]
    with mp.Pool(requestPool) as p: # Workers downloading the Images simultaneously
        return p.map(findFaces, [url for url in res if url])

def imtype(a):
    ja=json.loads(a.get_attribute("innerHTML"))
    legal_types=["png","jpg"]
    link, ftype = ja["ou"]  ,ja["ity"]
    if any(t in ftype for t in legal_types):
        findText= link.lower().find(f".{ftype}")
        if findText !=-1:
            link = link[:findText+4]
        return link
    return None

def openUrl(browser,searchtext):
    url = "https://www.google.com/search?q="+searchtext+"&source=lnms&tbm=isch"
    # Open the link
    browser.get(url)
    print("Getting you a lot of images. This may take a few moments...")
    repeatAmount=120 # A safe range to get a minimum of 600 images
    counter=0
    while True:
        try:
            browser.find_element_by_xpath(f'//div[@data-ri="{counter}"]')
        except Exception:
            break
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scroll to bottom of page
        try:
            browser.find_element_by_id("smb").click() # Click on "show more images" button
        except Exception:
            pass
        counter+=8


def extended_openUrl(browser,imgUrl):
    print("Getting you you more images related to your search queury...")
    browser.find_element_by_class_name("S3Wjs").click() # Search by url
    inputElement = browser.find_element_by_class_name("lst") # Search button
    inputElement.send_keys(imgUrl)
    inputElement.send_keys(Keys.ENTER)
    try:
        browser.find_element_by_class_name("mnr-c") # This class only shows up when google returns an error
        return None
    except Exception: 
        pass
    textElement=browser.find_element_by_class_name("gLFyf") # Input text
    searchtext= textElement.get_attribute('value').replace(" ", "+")
    openUrl(browser,searchtext)
    return True
    
    
#------------- Main Program -------------#
def main():
    searchtext = "face" # The search query
    sTime = time.time()
    options = webdriver.ChromeOptions()
    
    #Options for better performance
    options.add_argument('--no-sandbox')
    # options.add_argument("--headless")
    options.add_argument('--log-level=3')

    #session options
    retry = Retry(connect=2, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)


    try:
        browser = webdriver.Chrome('chromedriver', chrome_options=options)
    except Exception as e:
        print("Looks like google chrome webdriver is not "
                "installed on your machine (exception: %s)" % e)
        sys.exit()

    openUrl(browser,searchtext) # Get page source

    if not os.path.exists(directory): # If folder "Images" doesnt exist, create it
        os.makedirs(directory)

    actualImages=sliceSource(browser) # Divides the Images urls
    img_total=len(actualImages)

    for imgUrl in actualImages:
        if not imgUrl:
            continue
        if len(imgUrl)>70: # Url is too long so cut to the chase before getting an error
            continue
        success=extended_openUrl(browser,imgUrl)# Get related images
        if not success:
            continue
        secondaryImages=sliceSource(browser)# Divides the image urls
        img_total+=len(secondaryImages)
        #copy paste this part to loop as many times as u want



    # Speed check
    print(f"downloaded and processed: {img_total} images in {time.time() - sTime} seconds")


if __name__=="__main__":
    main()
