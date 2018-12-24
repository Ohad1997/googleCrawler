# this script made by: Ohad Baehr,
# is designed to download 60k+ Images from google search related to the search query
# the script is originally designed to get Images of faces but you may change the search query
# and delete the part of the program designed to search for them
# you may use this program to your liking, credit will be appreciated

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as BS
import os
import json
import sys
import time
import requests
import multiprocessing as mp


# libraries imported to find faces, you can delete this part if you do not want to test for faces
import cv2
import dlib


SCALE_FACTOR = 0.6 # determines the resize amount of the image when its processed, bigger= better detection but slower

# you may delete this part if you want other kind of Images,
# note that you must also delete the function "findFaces" and the call for it in "Main"
detector = dlib.get_frontal_face_detector()


directory = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Images") # make a new folder called "Images" in the current folder
requestPool= mp.cpu_count() * 12 # determines the amount of proccesses working simultaneously for sending requests to download images


def findFaces(file):# delete this if you do not want to search for faces
    try:
        fname = os.path.join(directory,os.fsdecode(file))
        print(f"proccesing: {fname}")
        im = cv2.imread(fname, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (int(gray.shape[1] * SCALE_FACTOR),int(gray.shape[0] * SCALE_FACTOR))) 
        rects = detector(gray, 1)
        if len(rects) == 0:# no face, remove image
            os.remove(fname)   
    except Exception:
        os.remove(fname)      


def sliceSource(source):
    soup = BS(source, "lxml")
    Images=[]

    # divide the urls of the images
    for a in soup.find_all("div",{"class":"rg_meta"}):
        link , Type =json.loads(a.text)["ou"]  ,json.loads(a.text)["ity"]
        if Type=='jpg':
            findText= link.lower().find(".jpg")
            if findText !=-1:
                link= link[:findText+4]
            Images.append(link)
        elif Type=='png':
            findText= link.lower().find(".png")
            if findText !=-1:
                link= link[:findText+4]

            Images.append(link)
    return Images  


def downloadImg(link):
    print(f"downloading: {link}")
    try:
        r = requests.get(link, allow_redirects=False, timeout=10)
        fname=os.path.join(os.path.dirname(os.path.abspath(__file__)),"images",link.split('/')[-1])
        open(fname, 'wb').write(r.content)
    except Exception as e:
        print("Download failed:", e) 


def openUrl(browser,searchtext):
    url = "https://www.google.com/search?q="+searchtext+"&source=lnms&tbm=isch"
    # Open the link
    browser.get(url)
    print("Getting you a lot of images. This may take a few moments...")
    if mp.cpu_count()< 4: # set repeating time of the scroll script
        repeatAmount=200
    else:
        repeatAmount=120
    for _ in range(repeatAmount):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);") # scroll to bottom of page
        try:
            browser.find_element_by_id("smb").click() # click on "show more images"
        except Exception:
            pass

    source = browser.page_source
    return source


def extended_openUrl(browser,imgUrl):
    gImagesUrl= "https://images.google.com/"
    # Open google images
    browser.get(gImagesUrl)
    print("Getting you you more images related to your search queury...")
    browser.find_element_by_class_name("S3Wjs").click() # search by url
    time.sleep(0.5)
    inputElement = browser.find_element_by_class_name("lst") # search button
    inputElement.send_keys(imgUrl)
    time.sleep(0.5)
    inputElement.send_keys(Keys.ENTER)
    try:
        browser.find_element_by_class_name("mnr-c") # this class only shows up when google returns an error
        return -1
    except Exception:
        pass
    time.sleep(0.5)
    textElement=browser.find_element_by_class_name("gLFyf") # input text
    searchtext= textElement.get_attribute('value').replace(" ", "+")
    source=openUrl(browser,searchtext)
    return source
    

def main():
    searchtext = "face" # the search query
    sTime = time.time()
    options = webdriver.ChromeOptions()
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

    source= openUrl(browser,searchtext)

    if not os.path.exists(directory): # if "Images" doesnt exist, create it
        os.makedirs(directory)

    ActualImages=sliceSource(source) # divides the Images urls
    with mp.Pool(requestPool) as p: # workers downloading the Images simultaneously
        p.map(downloadImg, [url for url in ActualImages])

    for imgUrl in ActualImages:
        if len(imgUrl)>70: # url is too long so cut to the chase before getting an error
            continue
        source= extended_openUrl(browser,imgUrl)# get related images
        if source==-1:
            continue
        SecondaryImages=sliceSource(source)# divides the Images urls
        with mp.Pool(requestPool) as p:# workers downloading the Images simultaneously
            p.map(downloadImg, [url for url in SecondaryImages])



    # you may delete this part if you want other kind of photos
    with mp.Pool(mp.cpu_count()-1) as p:# workers finding faces and deleting photos without
        p.map(findFaces, [file for file in os.listdir(directory)])



    # speed check
    print(f"downloaded and processed: {len([name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))])} images in {time.time() - sTime} seconds")


if __name__=="__main__":
    main()
