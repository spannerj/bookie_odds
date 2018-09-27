from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json
import requests
import shutil

def send_to_slack(section, postcode):
    # Set the webhook_url to the one provided by Slack when you create the webhook at https://my.slack.com/services/new/incoming-webhook/
    webhook_url = 'https://hooks.slack.com/services/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'
    slack_data = {'text': section + ' - ' + postcode}

    response = requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )


options = Options()  
# options.add_argument("--headless")
# options.add_argument("--start-maximized")
# driver.set_window_size(1400,1000)
options.add_argument("--window-size=1300,1000")
options.add_argument('--disable-gpu')
# options.add_argument('--no-sandbox')
driver = webdriver.Chrome(options=options)

try:
    import os
    mydir = os.getcwd() + '/sshots'
    filelist = [ f for f in os.listdir(mydir) if f.endswith(".png") ]
    for f in filelist:
        os.remove(os.path.join(mydir, f))

    driver.get('https://pickmypostcode.com')

    # log in
    print('click sign in')
    driver.find_element_by_xpath('//button[text()="Sign in"]').click()
    print('entering email')
    driver.find_element_by_xpath('//*[@id="confirm-email"]').send_keys('spencer.jago.register@gmail.com')
    print('entering postcode')
    driver.find_element_by_xpath('//*[@id="confirm-ticket"]').send_keys('PL3 4PW')
    print('submit login')
    driver.find_element_by_xpath('//button[@type="submit"]').click()
    driver.save_screenshot('sshots/screenshot.png')

    # # ads
    # driver.save_screenshot('sshots/screenshot2.png')
    driver.find_element_by_xpath('//*[@id="qcCmpButtons"]/button').click()
    driver.save_screenshot('sshots/screenshot3.png')

    # # privacy
    # elem = driver.find_element_by_xpath("//*[@class='qc-cmp-button qc-cmp-save-and-exit']")
    # elem.click()

    # #  main
    main_draw_postcode = driver.find_element_by_class_name("result--postcode").text[0:7].strip()
    print(main_draw_postcode)
    send_to_slack('main_draw', main_draw_postcode)
    # driver.save_screenshot('sshots/screenshot4a.png')

    # # video
    # # driver.get('https://pickmypostcode.com/video/')
    # # elements = driver.find_elements_by_xpath("//*[contains(@id, 'bridVideoPlayer')]")
    # # elements[0].click()
    # # video_postcode = driver.find_element_by_class_name("result--postcode").text[0:8].strip()
    # # print(video_postcode)
    # # send_to_slack('video_draw', video_postcode)

    # driver.get('https://pickmypostcode.com/survey-draw/')
    # timeout = 90
    # try:
    #     import datetime
    #     print(datetime.datetime.time(datetime.datetime.now()))
    #     element_present = EC.presence_of_element_located((By.CLASS_NAME, 'btn btn-secondary btn__xs'))
    #     WebDriverWait(driver, timeout).until(element_present)
    #     print(datetime.datetime.time(datetime.datetime.now()))
    #     driver.save_screenshot('sshots/present.png')
    # except TimeoutException:
    #     print(datetime.datetime.time(datetime.datetime.now()))
    #     driver.save_screenshot('sshots/error.png')
    #     print("Timed out waiting for page to load")

    # survey
    driver.get('https://pickmypostcode.com/survey-draw/')
    driver.save_screenshot('sshots/screenshot5.png')
    elem = driver.find_element_by_xpath("//*[@class='btn btn-secondary btn__xs']")
    elem.click()
    driver.save_screenshot('sshots/screenshot6.png')
    survey_postcode = driver.find_element_by_class_name("result--postcode").text[0:7].strip()
    print(survey_postcode)
    send_to_slack('survey_draw', survey_postcode)

    # stackpot
    driver.get('https://pickmypostcode.com/stackpot/')
    stack_postcodes = driver.find_elements_by_class_name("result--postcode")  
    for stack_postcode in stack_postcodes:
        print(stack_postcode.text[0:8].strip())
        send_to_slack('stackpot', stack_postcode.text[0:7].strip())

    # # # bonus
    # # driver.get('https://pickmypostcode.com/your-bonus/')

    

finally:
    driver.quit()
    # pass