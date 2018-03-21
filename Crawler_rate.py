#臺銀匯率
import requests
import string
from bs4 import BeautifulSoup
from time import strftime
import datetime
from send_gmail import sendmail
import os.path
import sys, time

payload = {
 'StartStation': '5f4c7bb0-c676-4e39-8d3c-f12fc188ee5f',
 'EndStation': 'f2519629-5973-4d08-913b-479cce78a356',
 'SearchDate': '2017/09/17',
 'SearchTime': '21:30',
 'SearchWay': 'DepartureInMandarin'
}

def get_web_page(url, currency):
    resp = requests.get(url + currency)
    if resp.status_code != 200:
        print('Invalid url:', resp.url)
        return None
    else:
        return resp.text



def get_rate_data(dom, currency):
    soup = BeautifulSoup(dom, 'html.parser')
    body = soup.find('tbody')
    tr = body.find_all('tr')
    CurrencyData = []  # 取得的匯率資料
    for s in tr:
        Date = s.find('td', 'text-center').find('a').text     # 日期
        Rate = s.find_all('td', 'rate-content-cash')[1].text  # 現金賣出匯率
        CurrencyData.append({
            'Type': currency,
            'Date': Date,
            'Rate': Rate
        })

    return CurrencyData


def traceback(err):
    now = time.strftime('%H:%M:%S', time.localtime(time.time()))
    traceback = sys.exc_info()[2]
    errmsg = str(err) + 'exception in line' + str(traceback.tb_lineno)
    return errmsg

if __name__ == '__main__':
    try:
        bank_url = 'http://rate.bot.com.tw/xrt/quote/l6m/'
        currency_list = ('JPY', 'USD', 'CAD','AUD')
        mail_content = ''
        today = strftime("%Y/%m/%d")
        if datetime.date.today().weekday() == 0:
            yesterday = str(datetime.date.today() - datetime.timedelta(days=3)).replace('-', '/')
        elif datetime.date.today().weekday() == 7:
            yesterday = str(datetime.date.today() - datetime.timedelta(days=2)).replace('-', '/')
        else:
            yesterday = str(datetime.date.today() - datetime.timedelta(days=1)).replace('-', '/')

        for currency in currency_list:
            time.sleep(3)
            page = get_web_page(bank_url, currency)
            if page:
                rate_list = get_rate_data(page, currency)
                # print(rate_list)
                # for dic in rate_list:
                #    # if dic['Date'] == str(yesterday).replace('-', '/'):
                #     if dic['Date'] == today:
                #         print('日期:', dic['Date'], '今天匯率', dic['Rate'], sep=' ')
                keyValList_now = [today]
                keyValList_last = [yesterday]
                matches_today = list(filter(lambda d: d['Date'] in keyValList_now, rate_list))
                matches_yesterday = list(filter(lambda d: d['Date'] in keyValList_last, rate_list))

                if len(matches_today) == 0:    # 凌晨抓不到今天匯率，匯率於早上八點開盤
                    matches_today = matches_yesterday


                max_list = max(rate_list, key=lambda x: x['Rate'])
                min_list = min(rate_list, key=lambda x: x['Rate'])
                average = sum(float(item['Rate']) for item in rate_list) / len(rate_list)
                # print('幣別:', currency)
                # print('日期:', matches_today[0]['Date'], '今天匯率', matches_today[0]['Rate'], sep=' ')
                # print('日期:', matches_yesterday[0]['Date'], '昨天匯率', matches_yesterday[0]['Rate'], sep=' ')
                # print('日期:', max_list['Date'], '半年內最糟匯率', max_list['Rate'], sep=' ')
                # print('日期:', min_list['Date'], '半年內最好匯率', min_list['Rate'], sep=' ')

                mail_content += '幣別: {0}\n' \
                                '日期: {1} 今天匯率 {2}\n' \
                                '日期: {3} 昨天匯率 {4}\n' \
                                '日期: {5} 半年內最糟匯率 {6}\n' \
                                '日期: {7} 半年內最好匯率 {8}\n' \
                                '半年內匯率平均 {9}\n' \
                                '\n'.format(currency, matches_today[0]['Date'] if len(matches_today) > 0 else '-', matches_today[0]['Rate'] if len(matches_today) > 0 else '-', matches_yesterday[0]['Date'] if len(matches_yesterday) > 0 else '-',  matches_yesterday[0]['Rate'] if len(matches_yesterday) > 0 else '-', max_list['Date'], max_list['Rate'], min_list['Date'], min_list['Rate'], "%.6f" % average )

        print(mail_content)
        sendmail(today + ' 匯率', mail_content)
        # 寫LOG

        if not os.path.exists('log.txt'):
            f = open('log.txt', 'w', encoding='UTF-8')
        with open("log.txt", "a") as myfile:
            myfile.write('Finished:' + str(datetime.datetime.now()) + '\r\n')

    except Exception as e:
        if not os.path.exists('log.txt'):
            f = open('log.txt', 'w', encoding='UTF-8')
        with open("log.txt", "a") as file:
            file.write('Error:' + str(datetime.datetime.now()) + str(traceback(e)) + '\r\n')
