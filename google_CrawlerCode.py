from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as BS
import os
import json
import sys
import time
import requests
import multiprocessing as mp
import cv2
import dlib


SCALE_FACTOR = 0.6
detector = dlib.get_frontal_face_detector()
directory = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Images")
requestPool= mp.cpu_count() * 12


def findFaces(file):
    try:
        fname = os.path.join(directory,os.fsdecode(file))
        print(f"proccesing: {fname}")
        im = cv2.imread(fname, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (int(gray.shape[1] * SCALE_FACTOR),int(gray.shape[0] * SCALE_FACTOR))) 
        rects = detector(gray, 1)
        if len(rects) == 0:
            os.remove(fname)   
    except Exception:
        os.remove(fname)      


def sliceSource(source):
    soup = BS(source, "lxml")
    Images=[]
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
    browser.get(url)
    print("Getting you a lot of images. This may take a few moments...")
    if mp.cpu_count()< 4:
        repeatAmount=200
    else:
        repeatAmount=120
    for _ in range(repeatAmount):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            browser.find_element_by_id("smb").click()
        except Exception:
            pass

    source = browser.page_source
    return source


def extended_openUrl(browser,imgUrl):
    gImagesUrl= "https://images.google.com/"
    browser.get(gImagesUrl)
    print("Getting you you more images related to your search queury...")
    browser.find_element_by_class_name("S3Wjs").click()
    time.sleep(0.5)
    inputElement = browser.find_element_by_class_name("lst")
    inputElement.send_keys(imgUrl)
    time.sleep(0.5)
    inputElement.send_keys(Keys.ENTER)
    try:
        browser.find_element_by_class_name("mnr-c")
        return -1
    except Exception:
        pass
    time.sleep(0.5)
    textElement=browser.find_element_by_class_name("gLFyf")
    searchtext= textElement.get_attribute('value').replace(" ", "+")
    source=openUrl(browser,searchtext)
    return source
    

def main():
    searchtext = "face"
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

    if not os.path.exists(directory):
        os.makedirs(directory)

    ActualImages=sliceSource(source)
    with mp.Pool(requestPool) as p:
        p.map(downloadImg, [url for url in ActualImages])

    for imgUrl in ActualImages:
        if len(imgUrl)>70:
            continue
        source= extended_openUrl(browser,imgUrl)
        if source==-1:
            continue
        SecondaryImages=sliceSource(source)
        with mp.Pool(requestPool) as p:
            p.map(downloadImg, [url for url in SecondaryImages])


    with mp.Pool(mp.cpu_count()-1) as p:
        p.map(findFaces, [file for file in os.listdir(directory)])


    print(f"downloaded and processed: {len([name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))])} images in {time.time() - sTime} seconds")


if __name__=="__main__":
    main()