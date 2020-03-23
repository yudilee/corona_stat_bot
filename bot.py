"""
This is a echo bot.
It echoes any incoming text messages.
"""

import logging

from aiogram import Bot, Dispatcher, executor, types, filters
from aiogram.types import ParseMode
from aiogram.utils.emoji import emojize
from aiogram.utils.markdown import bold, code, italic, text
from crawler import Crawler
import pycountry

API_TOKEN = ''
URL = "https://api.coronatracker.com/v2/stats?countryCode=%s"
LIST = "https://api.coronatracker.com/v2/stats/top?limit=1000"
NEWS = "https://api.coronatracker.com/news/trending?limit=9&offset=0&countryCode=&country=&language=en"
TA = "https://api.coronatracker.com/v1/travel-alert"
WORLDOMETER = "https://www.worldometers.info/coronavirus/"

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)



@dp.message_handler(regexp='(^stat[s]?$|start|global)')
async def stat(message: types.Message):
    crawler = Crawler()
    response = crawler.get_response(URL % '')
    data = response.json()
    print(message.from_user.full_name)
    print(message.text)
    await message.answer(
        'Here is the latest stat crawled at : %s \n'
        '- Confirmed : %s \n'
        '- Deaths : %s \n'
        '- Recovered : %s \n' % (data["created"], data["confirmed"], data["deaths"], data["recovered"])
    )

@dp.message_handler(regexp='(list)')
async def stat(message: types.Message):
    await types.ChatActions.typing()
    crawler = Crawler()
    response = crawler.get_response(LIST)
    data = response.json()
    print(message.from_user.full_name)
    print(message.text)
    country_list = []
    country_list.append("`| CODE | COUNTRY | Confirmed | Deaths | Recovered |`")
    country_list.append("`| ---- | ------- | --------- | ------ | --------- |`")
    for country in data:
        country_list.append("`| :%s: | %s | %s | %s | %s |`" % (country["countryCode"].lower(), country["countryName"], country["confirmed"], country["deaths"], country["recovered"]))
    await message.answer(emojize(text(*country_list, sep='\n')), parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(regexp='(news)')
async def stat(message: types.Message):
    await types.ChatActions.typing()
    crawler = Crawler()
    response = crawler.get_response(NEWS)
    print(message.from_user.full_name)
    print(message.text)
    data = response.json()['items']
    news_list = []
    for news in data:
        await message.answer(text("[%s](%s)" % (news["title"], news["url"])), parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=['travel_alert_([a-zA-Z]{2,})']))
async def send_welcome(message: types.Message, regexp_command):
    country_id = f"{regexp_command.group(1)}"
    if pycountry.countries.get(alpha_2=country_id.upper()):
            crawler = Crawler()
            response = crawler.get_response(TA)
            data = response.json()
            travel_alert = {}
            for country in data:
                if country['countryCode'] == country_id.upper():
                    travel_alert = country
            await message.answer(
                'Here is the travel alert for %s crawled at : %s \n'
                '%s' % (travel_alert["countryName"], travel_alert["publishedDate"], travel_alert["alertMessage"].replace("|",''))
            )
    else:
        await message.answer("Country code not known")
    print(message.from_user.full_name)
    print(message.text)
#    await message.reply(f"You have requested an item with id <code>{regexp_command.group(1)}</code>")
    

@dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=['country_([a-zA-Z]{2,})']))
async def send_welcome(message: types.Message, regexp_command):
    country_id = f"{regexp_command.group(1)}"
    if pycountry.countries.get(alpha_2=country_id.upper()):
            crawler = Crawler()
            response = crawler.get_response(URL % country_id.upper())
            data = response.json()
            await message.answer(
                'Here is the latest stat for %s crawled at : %s \n'
                '- Confirmed : %s \n'
                '- Deaths : %s \n'
                '- Recovered : %s \n' % (data["countryName"], data["created"], data["confirmed"], data["deaths"], data["recovered"])
            )
    else:
        await message.answer("Country code not known")
    print(message.from_user.full_name)
    print(message.text)
#    await message.reply(f"You have requested an item with id <code>{regexp_command.group(1)}</code>")


@dp.message_handler()
async def echo(message: types.Message):
    # old style:
    # await bot.send_message(message.chat.id, message.text)
    crawler = Crawler()
    soup = crawler.get_soup(WORLDOMETER)
    data = []
    table = soup.select_one('table#main_table_countries_today')
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for table_row in table_body.find_all('tr'):
        columns = table_row.findAll('td')
        output_row = []
        for column in columns:
            output_row.append(column.text.strip().lower())
        data.append(output_row)

    print(message.from_user.full_name)
    print(message.text)

    try: 
        result = data[index_2d(data,message.text)[0]]
        await message.answer(
            'Latest Stat from WORLDOMETER for country %s \n'
            'Total Cases : %s \n' 
            'New Cases : %s \n' 
            'Total Deaths : %s \n'
            'New Deaths : %s \n'
            'Total Recovered : %s \n'
            'Active Cases : %s \n'
            'Serious : %s \n'
            'Total Case per 1M Population : %s \n' % (result[0],result[1],result[2],result[3],result[4],result[5],result[6],result[7],result[8])
            )
        #await message.answer('\n'.join(data[index_2d(data,message.text)[0]]))
    except:
        await message.answer('please try other command or type country you want to get info')


    


def index_2d(data, search):
    for i, e in enumerate(data):
        try:
            return i, e.index(search.lower())
        except ValueError:
            pass
    raise ValueError("{} is not in list".format(repr(search)))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
