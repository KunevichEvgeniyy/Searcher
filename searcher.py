import uuid
import asyncio
import aiofiles
import pyshorteners
from typing import Union
from urllib.parse import quote_plus, unquote_plus
from bs4 import BeautifulSoup as Bs
import textwrap
from aiohttp import ClientSession
from aiohttp.client_exceptions import (
    ClientConnectorCertificateError,
    ClientConnectorError,
    TooManyRedirects,
)
from lxml.html import fromstring


async def get_requests_to_url(url: str) -> Union[str, None]:
    """
    Get page any found url in search system

    :param url: str
    :return: Union[str, None]
    """
    headers = {"User-Agent": "Opera/9.80 (J2ME/MIDP; Opera Mini/9.80 (S60; SymbOS; "
                             "Opera Mobi/23.334; U; id) Presto/2.5.25 Version/10.54"}
    async with ClientSession() as session:
        async with session.get(url, headers=headers, timeout=15) as resp:
            if resp.status == 200:
                return await resp.text()


async def get_page_search(search_url: str) -> Union[str, None]:
    """
    Requests to search system and get code page

    :param search_url: str
    :return: Union[str, None]
    """
    headers = {"User-Agent": "Opera/9.80 (J2ME/MIDP; Opera Mini/9.80 (S60; SymbOS; "
                             "Opera Mobi/23.334; U; id) Presto/2.5.25 Version/10.54"}
    async with ClientSession() as session:
        async with session.get(url=search_url,
                               headers=headers,
                               timeout=15) as resp:
            if resp.status == 200:
                return await resp.text()


async def search_service(search_url: str, search_string: str) -> str:
    """
    Get page in search system

    :param search_url: str
    :param search_string: str
    :return: str
    """
    return await get_page_search(search_url.format(quote_plus(search_string)))


async def find_url_check(response: str) -> list:
    """
    Get urls in search page

    :param response: str
    :return: list
    """
    soup = Bs(response, "html.parser")
    links = soup.findAll("a")
    url_sets = {unquote_plus(temp.replace('//duckduckgo.com/l/?uddg=', '')) for i in links
                if (temp := i.attrs.get("href"))}
    url_list = [i for i in url_sets if i.startswith("https")]
    if url_list:
        return list(url_list)


async def parse_page_short_view(search_string: str) -> None:
    """
    Crab page title to get short info

    Enter you`re questions >> music free

    console output:

    Search_system : [duckduckgo] Title : YouTube	 URL сайта : https://clck.ru/38pemx
    ...
    Search_system : [google] Title : Условия использования Google – Политика конфиденциальности и Условия использования – Google	 URL сайта : https://clck.ru/38pZh8
    ...
    Search_system : [yandex] Title : Law	 URL сайта : https://clck.ru/38perp
    ...
    Search_system : [bing] Title : Overview - Microsoft Advertising	 URL сайта : https://clck.ru/38pZhs

    :param search_string: str

    :return: None
    """

    search_system = {
        "duckduckgo": "https://duckduckgo.com/?q={}",
        "google": "https://www.google.com/search?q={}",
        "bing": "https://www.bing.com/search?q={}",
        "yandex": "https://yandex.ru/search?text={}",
    }
    date_from_search = []
    for search_sys, search_url in search_system.items():
        response_search_system = await search_service(search_url, search_string)
        if response_search_system:
            urls_list = await find_url_check(response_search_system)
            if urls_list:
                for url in urls_list:
                    try:
                        response = await get_requests_to_url(url)
                        res = fromstring(response)
                        string = res.findtext(".//title")
                        wrapper = textwrap.TextWrapper(width=150)
                        dedented_text = textwrap.dedent(text=string)
                        original = wrapper.fill(text=dedented_text)
                        shortened = textwrap.shorten(text=original, width=150)
                        title = wrapper.fill(text=shortened)
                        date_from_search.append(
                            f"Search_system : [{search_sys}] "
                            f"Title : {title}\t "
                            f"URL сайта : {pyshorteners.Shortener().clckru.short(url)}"
                        )
                    except (
                            TypeError,
                            ValueError,
                            TooManyRedirects,
                            ClientConnectorCertificateError,
                            ClientConnectorError,
                            TimeoutError,
                            ):
                        continue

    print('\n'.join(date_from_search))

    name_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, search_string)

    async with aiofiles.open(f'./result_search_{name_uuid}.txt', mode='w') as f:
        await f.write('\n'.join(date_from_search))


asyncio.run(parse_page_short_view(input('Enter you`re questions >> ')))
