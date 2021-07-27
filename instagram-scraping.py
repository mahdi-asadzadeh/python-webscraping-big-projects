import os
import json
import requests
import dataset
from datetime import datetime
from requests import Session
from abc import ABC, abstractmethod


# Facade
# ==========================================================================
# ==========================================================================


class InstagramScrapingManager:

    def __init__(self, **kwargs):
        self.link = link
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.login_url = kwargs['login_url']
        self.session = requests.Session()
        self.login_check()
        self.scraping_user = ScrapingUser(kwargs['data_base_file_name'], kwargs['table_name'], self.session, kwargs['tag_name'])

    def start_scraping(self):
        self.login_check()
        self.scraping_user.scraping()
        
    def login(self):
        time = int(datetime.now().timestamp())
        response = requests.get(self.link)
        csrf = response.cookies.get_dict()['ig_did']
        payload = {
            'username': self.username,
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{time}:{self.password}',
            'queryParams': {},
            'optIntoOneTap': 'false'
            }
        login_header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/login/",
            "x-csrftoken": csrf
            }
        login = self.session.post(self.login_url, data=payload, headers=login_header)
        return login

    def login_check(self):
        cookie = None
        if os.path.getsize('cookies.txt') == 0:
            login = self.login()
            login_json = json.loads(login.text)
            cookies = login.cookies
            cookie_jar = cookies.get_dict()
            cookie = cookie_jar['csrftoken']
            file_cookies = open('cookies.txt', 'w')
            file_cookies.write(cookie)
            file_cookies.close()
        else:
            cookie_file = open('cookies.txt', 'r')
            cookie = cookie_file.read()
            self.session.cookies.update({'cookies':cookie})


# Subsystems
# ==========================================================================
# ==========================================================================


class MetaSingleton(type):
    _instance = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super().__call__(*args, **kwargs)
        return cls._instance[cls]


class DataBaseConnector(metaclass=MetaSingleton):
    def __init__(self, data_base_file_name):
        self.db = dataset.connect(f'sqlite:///{data_base_file_name}.db')


class DataBaseController:

    def __init__(self, data_base_file_name):
        self.db = DataBaseConnector(data_base_file_name).db

    def processor(self, *args, **kwargs):
        self.db['mahdi'].insert(kwargs)
 

class Scraping(ABC):

    @abstractmethod
    def scraping(self):
        pass


class ScrapingUser(Scraping):
    def __init__(self, data_base_file_name: str, table_name: str, session: Session, tag_name: str):
        self.data_base_file_name = data_base_file_name
        self.session = session
        self.tag_name = tag_name
        self.table_name = table_name
        self.db = DataBaseController(self.data_base_file_name)

    def scraping(self):
        hashtag_response = self.session.get(f'https://www.instagram.com/explore/tags/{self.tag_name}/?__a=1')
        json_hashtag_response = json.loads(hashtag_response.text)
        section = json_hashtag_response['data']['recent']['sections']

        for item_section in section:
            medias = item_section['layout_content']['medias']
            for media in medias:
                user = media['media']['user']
                pk = user['pk']
                username = user['username']
                full_name = user['full_name']
                profile_pic_url = user['profile_pic_url']
                self.db.processor(self.table_name, pk=pk, username=username, full_name=full_name, profile_pic_url=profile_pic_url)


# Client
# ==========================================================================
# ==========================================================================


def client_code(scraping_manager: InstagramScrapingManager):
    scraping_manager.start_scraping()


if __name__ == '__main__':
    USERNAME = ''
    PASSWORD = ''
    link = 'https://www.instagram.com/accounts/login/'
    login_url = 'https://www.instagram.com/accounts/login/ajax/'

    client_code(InstagramScrapingManager(
        username=USERNAME, 
        password=PASSWORD, 
        link=link, 
        login_url=login_url,
        data_base_file_name='instagram',
        table_name = 'users',
        tag_name = 'tehran',
        ))