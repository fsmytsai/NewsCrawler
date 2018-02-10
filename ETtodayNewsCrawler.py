import asyncio
import aiohttp
import requests
import time
from bs4 import BeautifulSoup
from xml.etree import ElementTree


class ETtodayNewsCrawler:
    base_url = 'https://game.ettoday.net/'

    def __init__(self):
        tStart = time.time()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.crawl())
        loop.close()

        tEnd = time.time()
        print('It cost %f sec' % (tEnd - tStart))

    async def crawl(self):
        async with aiohttp.ClientSession() as session:
            headers = {
                'Ocp-Apim-Subscription-Key': 'Bing Speech API Key'}
            async with session.post('https://api.cognitive.microsoft.com/sts/v1.0/issueToken', headers=headers) as response:
                self.access_token = await response.text()

            async with session.get(self.base_url) as response:
                whole_html = await response.text()
                soup = BeautifulSoup(whole_html, features='lxml')

                hot_news_a_list = soup.find(
                    'div', {'class': 'block_2 sidebar-hot-news'}).find_all('a')

                tasks = []
                for hot_news_a in hot_news_a_list:
                    task = asyncio.ensure_future(self.crawlDetail(
                        session, self.base_url + hot_news_a['href']))
                    tasks.append(task)
                await asyncio.gather(*tasks)

    async def crawlDetail(self, session, url):
        async with session.get(url) as response:
            whole_html = await response.text()
            soup = BeautifulSoup(whole_html, features='lxml')

            title = '標題：' + soup.find('h1').text

            story_p_list = soup.find(
                'div', {'class': 'story'}).find_all('p')

            if len(story_p_list[2].text) > 15:
                desc = '簡介：' + story_p_list[2].text
            else:
                desc = '簡介：' + story_p_list[3].text

            tasks = []
            tasks.append(self.downloadSpeech(session, title))
            tasks.append(self.downloadSpeech(session, desc))
            await asyncio.gather(*tasks)

    async def downloadSpeech(self, session, text):

        headers = {"Content-type": "application/ssml+xml",
                   "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
                   "Authorization": "Bearer " + self.access_token}

        body = ElementTree.Element('speak', version='1.0')
        body.set('xml:lang', 'en-us')
        voice = ElementTree.SubElement(body, 'voice')
        voice.set('xml:lang', 'en-us')
        voice.set('xml:gender', 'Female')
        voice.set(
            'name', 'Microsoft Server Speech Text to Speech Voice (zh-TW, Yating, Apollo)')
        voice.text = text

        async with session.post('https://speech.platform.bing.com/synthesize', data=ElementTree.tostring(body), headers=headers) as response:
            sound = await response.read()
            with open('./sounds/' + text[0:12] + '.wav', 'wb') as f:
                f.write(sound)


ETtodayNewsCrawler()
