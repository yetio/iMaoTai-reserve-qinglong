import datetime
import logging
import sys

import config
import login
import process
import privateCrypt

'''
cron: 5 18 * * *
new Env("i茅台预约结果")
'''

DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
TODAY = datetime.date.today().strftime("%Y%m%d")
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s',  # 定义输出log的格式
                    stream=sys.stdout,
                    datefmt=DATE_FORMAT)

print(r'''
**************************************
    欢迎使用i茅台结果查询工具
    由yetio进行编写 https://github.com/yetio
**************************************
''')

process.get_current_session_id()

# 校验配置文件是否存在
configs = login.config
if len(configs.sections()) == 0:
    logging.error("配置文件未找到配置")
    sys.exit(1)

aes_key = privateCrypt.get_aes_key()

s_title = '茅台结果查询成功'
s_content = ""



for section in configs.sections():
    if (configs.get(section, 'enddate') != 9) and (TODAY > configs.get(section, 'enddate')):
        continue

    mobile = privateCrypt.decrypt_aes_ecb(section, aes_key)
    province = configs.get(section, 'province')
    city = configs.get(section, 'city')
    token = configs.get(section, 'token')
    userId = privateCrypt.decrypt_aes_ecb(configs.get(section, 'userid'), aes_key)
    lat = configs.get(section, 'lat')
    lng = configs.get(section, 'lng')
    
    process.UserId = userId
    process.TOKEN = token
    process.init_headers(user_id=userId, token=token, lng=lng, lat=lat)
    
    # 根据配置中，要预约的商品ID，城市 进行自动预约
    try:
        ret = process.getReservationResult(mobile)
        if ret:
           s_content += '\n==========[' + mobile + '] '  + '==============' 
           for reservation in ret['data']['reservationItemVOS']:
                if datetime.datetime.fromtimestamp(reservation['reservationTime']/1000).strftime("%Y-%m-%d") != datetime.datetime.now().strftime("%Y-%m-%d"):
                    continue
                if reservation['status']==1:
                    s_content += '\n--预约失败-- '
                else:
                    s_content += '\n**预约成功** '

                s_content +=  datetime.datetime.fromtimestamp(reservation['reservationTime']/1000).strftime("%Y-%m-%d %H:%M:%S") + '  ' + reservation['itemName'] + ' ' 
        else:
            s_content += "获取预约结果出错\n"
    except BaseException as e:
        print(e)
        logging.error(e)


#logging.info(s_content)
# 推送消息
process.send_msg(s_title, s_content)
