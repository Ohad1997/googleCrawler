# whatapp messages sending, ohad baehr, python 3.6

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


def send_msg(name, driver, msg):
    try:
        message = driver.find_elements_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')[0]
        message.send_keys(msg)
        sendbutton = driver.find_elements_by_xpath('//*[@id="main"]/footer/div[1]/div[3]/button')[0]
        sendbutton.click()
    except Exception:
        print(f"failed to send message to:{name}")


def main():
    #------------------------------#

    # your name list, use: 'all' to send to all your contacts 
    # or a list of names separated by: ","
    names_list = ['name']

    #this is your message
    msg = "This is a Test Message"


    #------------------------------#
    options = webdriver.ChromeOptions()

    options.add_argument('--log-level=3') 
    options.add_argument("user-data-dir=selenium") 
    
    driver = webdriver.Chrome('chromedriver', chrome_options=options)
    wait = WebDriverWait(driver, 600)
    driver.get("https://web.whatsapp.com/")


    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.RLfQR")))
    search = driver.find_element_by_class_name("jN-F5")
    if names_list=="all" or names_list[0]=="all":
        names_list = driver.find_elements_by_class_name('_2wP_Y')
        print(f"sending messages to: {len(names_list)} peoples")
        for name in names_list:
            try:
                if name.text not in ['CHATS','MESSAGES']:
                    name_contact = name.find_element_by_class_name('_2EXPL')
                    name_contact.click()
                    send_msg(name, driver, msg)
            except Exception:
                print(f"failed to send message to:{name}")
    else:
        for name in names_list:
            try:
                search.clear()
                search.send_keys(name)
                search.send_keys(Keys.ENTER)
                send_msg(name, driver, msg)
            except Exception:
                print(f"failed to send message to:{name}")
    driver.close()

if __name__=="__main__":
    main()
