import uuid
import asyncio
import aiofiles
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


async def get_requests_to_url(url: str) -> str:
    headers = {"User-Agent": "Opera/9.80 (J2ME/MIDP; Opera Mini/9.80 (S60; SymbOS; "
                             "Opera Mobi/23.334; U; id) Presto/2.5.25 Version/10.54"}
    async with ClientSession() as session:
        async with session.get(url, headers=headers, timeout=15) as resp:
            if resp.status == 200:
                return await resp.text()


async def get_page_search(search_url: str) -> str:
    headers = {"User-Agent": "Opera/9.80 (J2ME/MIDP; Opera Mini/9.80 (S60; SymbOS; "
                             "Opera Mobi/23.334; U; id) Presto/2.5.25 Version/10.54"}
    async with ClientSession() as session:
        async with session.get(url=search_url,
                               headers=headers,
                               timeout=15) as resp:
            if resp.status == 200:
                return await resp.text()


async def search_google(search_string: str) -> str:
    search_url = f"https://www.google.com/search?q={quote_plus(search_string)}"
    return await get_page_search(search_url)


async def search_yandex(search_string: str) -> str:
    search_url = f"https://yandex.ru/search?text={quote_plus(search_string)}"
    return await get_page_search(search_url)


async def search_bing(search_string: str) -> str:
    search_url = f"https://www.bing.com/search?q={quote_plus(search_string)}"
    return await get_page_search(search_url)


async def search_duckduckgo(search_string: str) -> str:
    search_url = f"https://duckduckgo.com/?q={quote_plus(search_string)}"
    return await get_page_search(search_url)


async def find_url_to_check(response: str) -> list:
    soup = Bs(response, "html.parser")
    links = soup.findAll("a")
    url_sets = {unquote_plus(temp.replace('//duckduckgo.com/l/?uddg=', '')) for i in links
                if (temp := i.attrs.get("href"))}
    url_list = [i for i in url_sets if i.startswith("https")]
    if url_list:
        return list(url_list)


async def parse_url_and_title(search_string: str) -> None:
    search_system = [search_duckduckgo, search_google, search_yandex, search_bing]
    date_from_search = []
    for search in search_system:
        response_search_system = await search(search_string)
        if response_search_system:
            urls_list = await find_url_to_check(response_search_system)
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
                            f"Search_system: [{search.__name__.replace('search_', '')}] "
                            f"Заголовок: {title}\t "
                            f"URL сайта: {url}"
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


asyncio.run(parse_url_and_title(input('Enter you`re questions >> ')))
