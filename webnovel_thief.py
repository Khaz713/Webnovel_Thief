import datetime
import os
import time
import json
import re
import urllib.request
import warnings

import requests
import pydrive
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from urllib.request import urlopen
import pywin32_system32
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

with open('accounts.json', 'r', encoding='utf-8') as f:
    accounts = json.load(f)  # accounts.json has list of all emails for bot accounts

with open('list.json', 'r', encoding='utf-8') as f:
    novels = json.load(f)  # list.json has a list of novels and their current chapter

warnings.filterwarnings("ignore")


def fast_pass(driver):
    # gets a free fast pass(ticket for a chapter) for logging in
    driver.get('https://www.webnovel.com/bill/fastpass')
    while True:
        try:
            driver.find_element_by_xpath('//*[@title="Get More"]').click()
        except Exception as e:
            break
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'taskMod')))
    claim_frame = driver.find_element_by_id('taskMod')
    try:
        claim_frame.find_element_by_xpath('.//a[text()="claim"]').click()
        WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.XPATH, './/a[text()="claim"]')))
    except Exception as e:
        pass
    driver.refresh()


def energy_stone(driver):
    # get a free fast pass by voting on a new novel
    driver.get("https://www.webnovel.com/vote")
    while True:
        try:
            driver.find_element_by_xpath('//*[@title="vote"]').click()
        except Exception as e:
            break


def power_stone(driver, url):
    # gets a free fast pass by giving the current novel daily points
    driver.get(url[:-8])
    while True:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@title="Vote Power Stone"]')))
            driver.find_element_by_xpath('//*[@title="Vote Power Stone"]').click()
        except Exception as e:
            break


def sign_out(driver, account):
    # signs out from the current account
    driver.get('https://www.webnovel.com/bill/fastpass')
    account_name = account.split('@')[0]
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f'[class="g_drop_hd _hd oh br100% td300 db w40 h40"]')))
    driver.find_element_by_css_selector(f'[class="g_drop_hd _hd oh br100% td300 db w40 h40"]').click()
    sign_out = driver.find_element_by_css_selector('[title="Sign Out"]')
    driver.execute_script("arguments[0].click();", sign_out)
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'loginIfr')))
    except Exception as e:
        driver.refresh()


def get_chapter(driver, num, max_num, account):
    # gets a chapter, using a fast pass, in a list format with every paragraph being a new element of the list
    time.sleep(1)
    try:
        while True:
            try:
                driver.find_element_by_xpath('//i[text()="{}"]'.format(num)).click()
                break
            except Exception as e:
                driver.refresh()
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, '//span[text()="Use Fast Pass"]')))
        driver.find_element_by_xpath('//span[text()="Use Fast Pass"]').click()
    except Exception as e:
        driver.refresh()
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, '//span[text()="Use Fast Pass"]')))
        driver.find_element_by_xpath('//span[text()="Use Fast Pass"]').click()
        pass
    time.sleep(2)
    chapter_name_frame = driver.find_element_by_xpath('//div[@class="oh skiptranslate"]')
    chapter_name = chapter_name_frame.find_element_by_xpath('//span[@class="j_chapName"]').text
    chapter_id = str(driver.current_url)
    chapter_id = chapter_id[chapter_id.rfind('_') + 1:]
    chapter_id = chapter_id.replace('#', '')
    chapter_frame = driver.find_element_by_xpath('//div[@data-cid="{}"]'.format(chapter_id))
    chapter_raw = chapter_frame.find_elements_by_xpath('.//div[@class="dib pr"]/p')
    if len(chapter_raw) < 1000:
        driver.refresh()
        chapter_frame = driver.find_element_by_xpath('//div[@data-cid="{}"]'.format(chapter_id))
        chapter_raw = chapter_frame.find_elements_by_xpath('.//div[@class="dib pr"]/p')
    chapter = ['# {}\n'.format('Chapter ' + str(num) + ': ' + chapter_name)]
    try:
        driver.find_element_by_xpath('//*[@title="GOT IT"]').click()
        driver.find_element_by_xpath('//*[@title="Display Options"]').click()
        driver.find_element_by_xpath('//*[@id="modalTheme"]/div[2]/form/p[2]/span[2]/label[1]/strong').click()
        driver.refresh()
        chapter_frame = driver.find_element_by_xpath('//div[@data-cid="{}"]'.format(chapter_id))
        chapter_raw = chapter_frame.find_elements_by_xpath('.//div[@class="dib pr"]/p')
    except Exception as e:
        pass
    try:
        if not accounts[account]['comments_disabled']:
            driver.find_element_by_xpath('//*[@title="Display Options"]').click()
            driver.find_element_by_xpath('//*[@id="modalTheme"]/div[2]/form/p[2]/span[2]/label[1]/strong').click()
            driver.find_element_by_xpath('//*[@id="modalTheme"]/div[2]/form/p[4]/label/strong').click()
            accounts[account]['comments_disabled'] = True
            driver.refresh()
            chapter_frame = driver.find_element_by_xpath('//div[@data-cid="{}"]'.format(chapter_id))
            chapter_raw = chapter_frame.find_elements_by_xpath('.//div[@class="dib pr"]/p')
    except Exception as e:
        pass
    i = 0
    for line in chapter_raw:
        # the website started encrypting the source of the webpage for non-free chapters, to go around it getting
        # text from screenshots was used
        i += 1
        driver.execute_script("return arguments[0].scrollIntoView(true);", line)
        driver.execute_script("window.scrollBy(0, -200);")
        line.screenshot(f'screenshots/{i}.png')
        text = pytesseract.image_to_string(Image.open(f'screenshots/{i}.png'), config='--psm 6')
        #print(text)
        chapter.append(text + '\n\n')
    print(f'{num}/{max_num} {chapter_name} DONE')
    return chapter


def get_free_chapter(driver, num, max_num):
    # gets a free chapter in a list format with every paragraph being a new element of the list
    WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, '//i[text()="{}"]'.format(num))))
    driver.find_element_by_xpath('//i[text()="{}"]'.format(num)).click()
    WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, '//div[@class="oh skiptranslate"]')))
    chapter_name_frame = driver.find_element_by_xpath('//div[@class="oh skiptranslate"]')
    chapter_name = chapter_name_frame.find_element_by_xpath('//span[@class="j_chapName"]').text
    chapter_id = str(driver.current_url)
    chapter_id = chapter_id[chapter_id.rfind('_') + 1:]
    chapter_id = chapter_id.replace('#', '')
    chapter_frame = driver.find_element_by_xpath('//div[@data-cid="{}"]'.format(chapter_id))
    chapter_raw = chapter_frame.find_elements_by_xpath('.//div[@class="dib pr"]/p')
    chapter = ['# {}\n\n'.format('Chapter ' + str(num) + ': ' + chapter_name)]
    for line in chapter_raw:
        chapter.append(line.text + '\n\n')
    print(f'{num}/{max_num} {chapter_name} DONE')
    return chapter


def get_cover(driver, url, name):
    # gets cover of the novel
    driver.get(url)
    image_ulr = driver.find_element_by_xpath("/html/body/div[1]/div[2]/div/div/div[1]/i/img[2]").get_attribute("src")
    novels[name]['cover'] = int(datetime.datetime.now().timestamp())
    urllib.request.urlretrieve(image_ulr, f'covers/{name}.jpg')
    with open('list.json', 'w', encoding='utf-8') as f:
        json.dump(novels, f)


def log_in(driver, email):
    # logs into an account
    driver.get(
        'https://passport.webnovel.com/emaillogin.html?appid=900&areaid=1&returnurl=https%3A%2F%2Fwww.webnovel.com%2Fl'
        'oginSuccess&auto=1&autotime=0&source=&ver=2&fromuid=0&target=iframe&option=&logintab=&popup=1&format=redirect'
    )
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'email')))
    driver.find_element_by_name('email').send_keys('{}'.format(email))
    #time.sleep(1)
    driver.find_element_by_name('password').send_keys('krysiak1')
    #time.sleep(1)
    driver.find_element_by_id('submit').click()
    WebDriverWait(driver, 15).until(EC.url_matches('https://www.webnovel.com'))


def driver_element_exists(driver, css):
    try:
        driver.find_element_by_css_selector(css)
    except Exception as e:
        return False
    return True


today = datetime.datetime.today()
life_time_over = []
unavailable_accounts = []   # accounts can get free fast passes only once per day, which resets at 6pm
for email in accounts:
    account_date = datetime.datetime.fromtimestamp(accounts[email]['last_used'])
    if today.hour < 18:
        yesterday = today - datetime.timedelta(days=1)
        yesterday = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 18)
        if account_date > yesterday:
            accounts[email]['available'] = False
            unavailable_accounts.append(email)
    elif today.hour >= 18:
        today = datetime.datetime(today.year, today.month, today.day, 18)
        if account_date > today:
            accounts[email]['available'] = False
            unavailable_accounts.append(email)
    else:
        accounts[email]['available'] = True
    today = datetime.datetime.today()

gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)  # at the end novel gets sent to google drive for ease of access on mobile
print(f'Available bots:{len(accounts) - len(unavailable_accounts)}')
print('1. Select novel\n'   # select novels from the list to get
      '2. Add accounts\n'   # add accounts from "new_accounts.txt" file into "accounts.json" in correct format
      '3. Create new accounts\n'    # creates new accounts using temp email website
      '4. Show/Hide novel\n'    # disables/enables novel visibility in "select novel" option
      '5. Add novel\n'  # add new novel to the list
      '6. Beta novel')  # converts docx file into epub and uploads it into google drive
select = int(input())
print('====================================================')
if select == 1:
    os.system('cls')
    print(
        f'Available bots:{len(accounts) - len(unavailable_accounts)} Limit:{(len(accounts) - len(unavailable_accounts)) * 3} ')
    print('====================================================')
    i = 0
    novels_list = []
    accounts_to_delete = []
    for novel in novels:
        if novels[novel]['visible']:
            i += 1
            novels_list.append(novel)
            while True:
                try:
                    f = urlopen(novels[novel]['url'] + '/catalog')
                    myfile = f.read()
                    break
                except Exception as e:
                    pass
            newest_chapter = str(myfile).count('fl fs16 lh24 c_l _num mr4 tal')
            new = ""
            if novels[novel]['current_chapter'] < int(newest_chapter):
                new = f'<---NEW {newest_chapter - novels[novel]["current_chapter"]}!'
            print(f'{i}. {novel} {novels[novel]["current_chapter"]}/{newest_chapter} {new}')
    selects = []
    print('====================================================')
    print('CHOOSE NOVELS, 0 TO START:')
    while True:
        selects.append([int(x) for x in input().split()])
        if selects[-1][0] == 0:
            break
    os.system('cls')
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument('window-size=1000,1000')
    driver = webdriver.Chrome(options=options)
    driver.delete_all_cookies()
    for select_2 in selects:
        if select_2[0] == 0:
            print('ALL DONE')
            break
        novel_name = novels_list[select_2[0] - 1]
        novel_url = novels[novel_name]['url'] + '/catalog'
        novel_chap_num = novels[novel_name]['current_chapter'] + 1
        chapters = []
        while True:
            try:
                f = urlopen(novel_url)
                myfile = f.read()
                break
            except Exception as e:
                pass
        if len(select_2) > 1:
            latest_num = select_2[1]
        else:
            latest_num = int(str(myfile).count('fl fs16 lh24 c_l _num mr4 tal'))
        current_num = novel_chap_num
        print('====================================================')
        print(novel_name)
        print(f'LATEST CHAPTER: {latest_num}')
        # testing = False
        for account in accounts:
            try:
                if account not in life_time_over and account not in unavailable_accounts and current_num <= latest_num:
                    print(f'CURRENT CHAPTER: {current_num}')
                    print(account)
                    fast_passes = 0
                    log_in(driver, account)
                    fast_pass(driver)
                    fast_passes += 1
                    if latest_num - current_num >= 1:
                        energy_stone(driver)
                        fast_passes += 1
                    if latest_num - current_num >= 2:
                        power_stone(driver, novel_url)
                        fast_passes += 1

                    if not novels[novel_name]['cover'] \
                            or int(datetime.datetime.now().timestamp()) > novels[novel_name]['cover'] + 2592000:
                        get_cover(driver, novels[novel_name]['url'], novel_name)

                    while current_num <= novels[novel_name]['free_chapters']:
                        driver.get(novel_url)
                        chapters.extend(get_free_chapter(driver, current_num, latest_num))
                        current_num += 1
                    if current_num >= latest_num and latest_num <= novels[novel_name]['free_chapters']:
                        break
                    while fast_passes > 0:
                        driver.get(novel_url)
                        chapters.extend(get_chapter(driver, current_num, latest_num, account))
                        current_num += 1
                        fast_passes -= 1
                    with open('accounts.json', 'w', encoding='utf-8') as f:
                        json.dump(accounts, f)
                    sign_out(driver, account)
                    driver.delete_all_cookies()
                    accounts[account]['last_used'] = int(datetime.datetime.now().timestamp())
                    accounts[account]['strikes'] = 0
                    unavailable_accounts.append(account)
            except Exception as e:
                # sometimes account stops working, it could be temporary or permanent, every time it does not work it
                # gets a strike, 3 in the row and the account is removed from the list
                print(e)
                accounts[account]['last_used'] = int(datetime.datetime.now().timestamp())
                if not 'strikes' in accounts[account]:
                    accounts[account]['strikes'] = 1
                else:
                    accounts[account]['strikes'] += 1
                print(f'\nSTRIKES: {accounts[account]["strikes"]}!!!\n')
                if accounts[account]['strikes'] >= 3:
                    accounts_to_delete.append(account)
                    print('ACCOUNT DELETED')
                unavailable_accounts.append(account)
                try:
                    sign_out(driver, account)
                except Exception as ex:
                    print(e)
                driver.delete_all_cookies()

        for account in accounts_to_delete:
            accounts.pop(account, 0)
        if len(chapters) > 0:
            name = "" + novel_name
            name = name.replace(" ", '_')
            if novel_chap_num == current_num - 1:
                name += "_" + str(novel_chap_num)
            else:
                name += "_" + str(novel_chap_num) + '-' + str(current_num - 1)
            novels[novel_name]['current_chapter'] = current_num - 1
            chapters.insert(0, f'%![ ](covers/{novel_name}.jpg)\n')

            with open('list.json', 'w', encoding='utf-8') as f:
                json.dump(novels, f)

            with open('accounts.json', 'w', encoding='utf-8') as f:
                json.dump(accounts, f)

            with open('novels/' + name + '.txt', 'w', encoding='utf-8') as f:
                first = True
                for line in chapters:
                    # replacing some symbols for css escape sequence
                    if not first:
                        line = line.replace('|', 'I')
                        line = line.replace('<', '\\<')
                        line = line.replace('>', '\\>')
                        line = line.replace('[', '\\[')
                        line = line.replace(']', '\\]')
                        line = line.replace('~', '\\~')
                        line = line.replace('…', '...')
                        line = line.replace('-----', ' ')
                        line = line.replace('----', ' ')
                        line = line.replace('---', ' ')
                    else:
                        first = False
                    f.write(line)

            os.system(f'pandoc novels/{name}.txt -o novels/{name}.epub --quiet')
            # using pandoc to convert txt into epub, there is a lib in python for that but it was not working

            upload = drive.CreateFile({"mimeType": "application/epub+zip",
                                       "parents": [
                                           {"kind": "drive#fileLink", "id": '1HpRyxpnQvoCFaciexNbpGq-ylhhQ3zTZ', }],
                                       "title": "{}.epub".format(name)})
            # uploads the epub file into private google drive
            upload.SetContentFile("novels/{}.epub".format(name))
            upload.Upload()
            print(f'UPLOAD {name} DONE')
    driver.quit()

elif select == 2:
    os.system('cls')
    with open('new_accounts.txt', 'r') as f:
        _list = f.read().splitlines()
        for line in _list:
            print(line)
            accounts[line] = {}
            accounts[line]['last_used'] = 0
            accounts[line]['available'] = True
            accounts[line]['strikes'] = 0
        with open('accounts.json', 'w', encoding='utf-8') as f:
            json.dump(accounts, f)

    print('ALL DONE')

elif select == 3:
    num = int(input("How many: "))
    os.system('cls')
    options = webdriver.ChromeOptions()
    options.add_argument("--mute-audio")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(options=options)
    driver.get('https://passport.webnovel.com/register.html?appid=900&areaid=1&returnurl='
               'https%3A%2F%2Fwww.webnovel.com%2FloginSuccess&auto=1&autotime=0&source=&v'
               'er=2&fromuid=0&target=iframe&option=&logintab=&popup=1&format=redirect%27')
    sing_up_window = driver.current_window_handle
    driver.execute_script('''window.open("https://mail.tm/en/","_blank");''')
    mail_window = driver.window_handles[-1]
    driver.execute_script('''window.open("https://speech-to-text-demo.ng.bluemix.net/","_blank");''')
    audio_text_converter = driver.window_handles[-1]
    driver.switch_to.window(mail_window)
    for i in range(0, num):
        time.sleep(4)
        driver.find_element_by_id('address').click()
        win32clipboard.OpenClipboard()
        email = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        driver.switch_to.window(sing_up_window)
        time.sleep(1)
        driver.find_element_by_name('email').send_keys(email)
        time.sleep(1)
        driver.find_element_by_name('password').send_keys('krysiak1')
        time.sleep(1)
        driver.find_element_by_id('submit').click()
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it(
            (By.CSS_SELECTOR, "iframe[name^='a-'][src^='https://www.google.com/recaptcha/api2/anchor?']")))
        time.sleep(1)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@id='recaptcha-anchor']"))).click()
        driver.switch_to.default_content()

        while driver_element_exists(driver, "iframe[title='recaptcha challenge']"):
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title='recaptcha challenge']")))
            time.sleep(2)
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#recaptcha-audio-button"))).click()
            time.sleep(1)
            href = driver.find_element_by_id('audio-source').get_attribute('src')
            audio_file = requests.get(href, stream=True) # using audio to solve captcha
            with open('audio_captcha.mp3', "wb") as f:
                for data in audio_file.iter_content():
                    f.write(data)
            audio_file_path = os.getcwd().replace('\\', '/') + '/audio_captcha.mp3'
            time.sleep(1)
            driver.switch_to.window(audio_text_converter)
            btn = driver.find_element(By.XPATH, '//*[@id="root"]/div/input')
            btn.send_keys(audio_file_path)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div[7]/div/div/div/span')))
            result = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[7]/div/div/div/span').text
            driver.refresh()
            driver.switch_to.window(sing_up_window)
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title='recaptcha challenge']")))
            audio_input = driver.find_element_by_id('audio-response')
            audio_input.send_keys(result)
            audio_input.send_keys(Keys.ENTER)

            time.sleep(2)

        driver.switch_to.default_content()
        driver.find_element_by_id('submit').click()
        time.sleep(3)
        driver.get('https://passport.webnovel.com/register.html?appid=900&areaid=1&returnurl='
                   'https%3A%2F%2Fwww.webnovel.com%2FloginSuccess&auto=1&autotime=0&source=&v'
                   'er=2&fromuid=0&target=iframe&option=&logintab=&popup=1&format=redirect%27')
        driver.switch_to.window(mail_window)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="__layout"]/div/div[2]/main/div/div[2]/ul/li/a/div')))
        driver.find_element_by_xpath('//*[@id="__layout"]/div/div[2]/main/div/div[2]/ul/li/a/div').click()
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it(
            (By.XPATH, '//*[@id="iFrameResizer0"]')))
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, 'Activate Account')))
        driver.find_element_by_link_text('Activate Account').click()
        time.sleep(1)
        driver.close()
        driver.switch_to.default_content()
        driver.find_element_by_id('logout').click()
        driver.delete_all_cookies()
        print(email)
        accounts[email] = {}
        accounts[email]['last_used'] = 0
        accounts[email]['available'] = True
        accounts[email]['cookies'] = []
        with open('accounts.json', 'w', encoding='utf-8') as f:
            json.dump(accounts, f)
    print('ALL DONE')
    driver.quit()

elif select == 4:
    os.system('cls')
    while True:
        _list_ = []
        i = 1
        for novel in novels:
            _list_.append(novel)
            if novels[novel]['visible']:
                visible = True
            else:
                visible = False
            print(f'{i}. {novel} [{visible}]')
            i += 1

        print('====================================================')
        print('CHOOSE NOVELS, 0 TO END:')
        select_2 = int(input())
        if select_2 == 0:
            break
        else:
            if novels[_list_[select_2 - 1]]['visible']:
                novels[_list_[select_2 - 1]]['visible'] = False
            else:
                novels[_list_[select_2 - 1]]['visible'] = True

            with open('list.json', 'w', encoding='utf-8') as f:
                json.dump(novels, f)
            os.system('cls')

elif select == 5:
    os.system('cls')
    new_name = input('Name: ')
    new_url = input('Url: ')
    new_free_chapter = int(input('Free chapters: '))
    new_current_chapter = int(input('Current chapter: '))
    novels[new_name] = {}
    novels[new_name]['url'] = new_url
    novels[new_name]['current_chapter'] = new_current_chapter
    novels[new_name]['cover'] = 0
    novels[new_name]['visible'] = True
    novels[new_name]['free_chapters'] = new_free_chapter
    with open('list.json', 'w', encoding='utf-8') as f:
        json.dump(novels, f)
    print(f'{new_name} ADDED')

elif select == 6:
    os.system('cls')
    novel_name = input('Name: ')
    num_list = [int(s[8:-5]) for s in os.listdir('beta')]
    num_list.sort()
    for num in num_list:
        os.system(f'pandoc beta/Chapter_{num}.docx -o beta/{novel_name.replace(" ", "_")}_{num}.txt --quiet')
        print(f'{num}/{num_list[-1]}')

    with open('novels/' + novel_name.replace(" ", "_") + '_' + str(num_list[0]) + '-' + str(num_list[-1]) + '.txt', 'w',
              encoding='utf-8') as f:
        f.write(f'% {novel_name} {num_list[0]}-{num_list[-1]}\n')
        for num in num_list:
            with open(f'beta/{novel_name.replace(" ", "_")}_{num}.txt', 'r') as f2:
                _list = f2.read().splitlines()
                _list.insert(0, f'# Chapter {num}\n')
                for line in _list:
                    f.write(line + '\n')
                f.write('\n\n')

    name = novel_name.replace(" ", "_") + '_' + str(num_list[0]) + '-' + str(num_list[-1])
    os.system(f'pandoc novels/{name}.txt -o novels/{name}.epub --quiet')

    upload = drive.CreateFile({"mimeType": "application/epub+zip",
                               "parents": [
                                   {"kind": "drive#fileLink", "id": 'XXX', }],
                               "title": "{}.epub".format(name)})
    upload.SetContentFile("novels/{}.epub".format(name))
    upload.Upload()
    print('DONE')

elif select == 7:
    for account in accounts:
        accounts[account]['comments_disabled'] = False
    with open('accounts.json', 'w', encoding='utf-8') as f:
        json.dump(accounts, f)

input()
exit(0)
