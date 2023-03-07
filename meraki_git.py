# =============================================================================================== #
# -*- coding: utf-8 -*-
# =============================================================================================== #

"""
    Версия Бота 0.2.9
    В версии git скрыта приватная информация.

    - последние изменения: выполнен рефакторинг

"""

# =============================================================================================== #
# Блок импортов библиотек и запуск longpoll бота

import vk_api
import random, string, json, datetime, heapq, codecs, time, traceback
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.upload import VkUpload
from json import load,dump

MAIN_TOKEN = None
vk_session  = vk_api.VkApi(token = MAIN_TOKEN)
session_api = vk_session.get_api()
longpoll    = VkBotLongPoll(vk_session, None)

# =============================================================================================== #
# Блок выгрузки json баз данных

# БД фраз бота:
with open('random_pattern/random_inserts.json', 'r', encoding="utf-8", errors='ignore') as file:
    """
        random inserts - список случайных фраз бота;
        ...
    """
    data_file = json.load(file)
    random_inserts = data_file['random_inserts'][0]['database']

# БД команд бота:
with open('random_pattern/commands.json', 'r', encoding="utf-8", errors='ignore') as file:
    """
        commands_pattern - список всезовможных триггер-команд бота
        ...
    """
    data_file = json.load(file)
    commands_pattern = data_file['commands_pattern'][0]['commands']

# БД баланса участников:
with open('rpg/balance_info.json', 'r', encoding="utf-8", errors='ignore') as file:
    """
        users_balance - словарь с балансом валют участников беседы:
            raki   - рачки;
            gold   - монеты;
            likes  - лайки;
            gems   - алмазы;
            pearls - жемчуг;
            souls  - души;
            exp    - опыт;
            raki_trap_lvl    - уровень раколовки;
            raki_per_sms_lvl - доходность рачков за сообщения
    """
    data_file = json.load(file)
    users_balance = data_file['users_balance'][0]

# БД информации об участников:
with open('rpg/user_info.json', 'r', encoding="utf-8", errors='ignore') as file:
    """
        users_info - словарь с данными об акаунте пользователя:
            f_name   - имя;
            l_name   - фамилия;
            sex      - пол;
            nickname - ник (имя и фамилия по умолчанию);
            date_appearance - дата вступления в беседу
    """
    data_file = json.load(file)
    users_info = data_file['users_info'][0]

# БД статистики участников:
with open('rpg/stats_info.json', 'r', encoding="utf-8", errors='ignore') as file:
    """
        users_stats - словарь со статистической информацией об активностях участника беседы:
            last_day_communication - последний день общения;
            all_sms   - всего написано сообщений;
            today_sms - сообщений написано за сегодня;
            bad_sms   - количество написанных сообщений, содержащих брань
            opened_boxes - количество открытых кейсов, коробок и т.п.
            doned_tasks  - количество выполненных заданий
    """
    data_file = json.load(file)
    users_stats = data_file['users_stats'][0]

# БД информации о чате:
with open('rpg/chat_info.json', 'r', encoding="utf-8", errors='ignore') as file:
    """
        chat_info - словарь с актуальными данными о беседе:
            all_sms   - всего сообщений было написано;
            sms_today - написано за сегодня;
            NFT   - количество игровых NFT;
            today - сегодняшняя дата;
            curr_day_of_week  - число дня недели;
            curr_num_of_month - номер месяца;
            raki_trap_opened  - список с id тех, кто доставал сегодня раколовку
    """
    data_file = json.load(file)
    chat_info = data_file['chat_info'][0]

# БД купонов:
with open('rpg/coupons.json', 'r', encoding="utf-8", errors='ignore') as file:
    """
        coupons - словарь с данными о купонах. Структура:
            ключ = купон
            0 элемент списка - сумма награды
            1 элемент списка - название валюты
            2 элемент списка - количство использований купона (число минус 3)
            Далее идут id тех, кто уже использовал купон
    """
    data_file = json.load(file)
    coupons   = data_file['coupons'][0]

# =============================================================================================== #
# Блок объявлений функций

def sender(text):
    ''' 
        Функция отправки ответного сообщения в беседу.
        text - ответный тект бота.
    '''
    vk_session.method("messages.send", {"chat_id" : 1, "message" : text, "random_id" : 0})

def random_msg(list_with_patterns):
    '''
        Функция отправляет случаное сообщение в беседу из входного списка.
        list_with_patterns - входной список.
    '''
    random_text = random.SystemRandom().choice(list_with_patterns)
    return random_text

def add_info_about_new_member(user_id):
    """
        Функция добавляет данные о новом пользователе по его vk-id (аргумент user_id) во все необходимые json БД
    """
    global today
    data_user = vk_session.method("users.get", {"user_ids": user_id, 'fields':'sex'})[0]

    users_balance[user_id] = {"raki":0,"gold":0,"likes":0,"gems":0,"pearls":0,"souls":0,"exp":0,"raki_trap_lvl":1,"raki_per_sms_lvl":1}    
    users_info[user_id]    = {"f_name":data_user["first_name"],"l_name":data_user["last_name"],"nickname":f'{data_user["first_name"]} {data_user["last_name"]}',"sex":data_user["sex"],"date_appearance":today}
    users_stats[user_id]   = {"last_day_communication": today, "all_sms": 1,"today_sms": 1,"bad_sms": 0,"opened_boxes": 0,"doned_tasks": 0}

def add_sms_and_raki(user_id):
    """
        Функция, которая добавляет в статистику и баланс пользователя (аргумент - его vk-id) необходимые значения.
    """
    global users_balance, users_stats, chat_info
    chat_info['all_sms'] += 1
    chat_info['sms_today'] += 1
    users_stats[user_id]['all_sms'] += 1
    users_stats[user_id]['today_sms'] += 1

    users_balance[user_id]['exp'] += 1

    if users_stats[user_id]['all_sms'] %10 == 0:
        users_balance[user_id]['raki'] += users_balance[user_id]['raki_per_sms_lvl']

def do_command(msg, user_id, peer_id):
    """
        Функция проверяет: является ли сообщение (msg) написавшего (user_id) командой.
        Если же некая команда должна выполняться на ком-то и присутствует peer_id, функция так же проверит корректность
        команды и желаний пользователя, перед тем как исполнять команды.
    """
    if msg in ["/кто я", "/мои раки", "/мои рачки", "/мой баланс", "/раки", "/мой профиль", "/рачки", "/баланс", "/мой кошелек", "/кошелек", "/мой кошелёк", "/кошелёк"]:
            sender_profile_info(user_id)

    elif msg in ["/инфо", "/чат инфо", "/чат", "/данные чата"]:
            sender_profile_chat()

    elif msg.split()[0] in ["/к", "/казино", "/казик", "/ставка", "/поставить"]:
        casinoGameProcess(msg, user_id)

    elif msg.split()[0] in ["/обменять", "/поменять", "/обмен", "/трансфер", "/перевод"]:
        transfer_raki_to_gold(msg, user_id)

    elif msg.split()[0] in ["/отдать", "/поделиться", "/подарить", "/подарок"] and peer_id != "None":
        give_currency(msg, user_id, peer_id)

    elif msg.split()[0] == '/купон':
        enter_coupon(msg, user_id)

    elif msg in ['/достать раколовку', '/ловить рачков', '/достать сеть', '/достать сети', '/ежедневная награда', '/получить рачков', '/получить раков','/ловить раков']:
        get_raki_from_trap(user_id)

    elif msg == '/доход +':
        raki_per_sms_lvl_up(user_id)

    elif msg == '/раколовка +':
        raki_trap_lvl_up(user_id)

    elif msg in ['/магаз','/магазин','/шоп','/покупки','/товары','/улучшения']:
        show_personal_shop(user_id)

def show_personal_shop(user_id):
    """
        Функция выводит личный магазин написавшего (user_id).
        Доступ к различным новым вещам зависит от уровня.
    """
    global users_balance, users_info

    lvl_ = get_lvl_user(users_balance[user_id]['exp'])

    seashell_info    = f'1) 🐚 Ракушка: 15💰\n'
    bighand_info     = f'2) 🧤 Мощная рука: 100💰\n'
    anchor_info      = f'3) ⚓ Якорь: 300💰\n'
    lucky_info       = f'4) 🍀 Удача: 500💰\n'
    blackhearth_info = f'5) 🖤 Черное сердце: 1000💰\n'
    hearth_info      = f'6) 💘 Сердце: 1000💰\n'
    ring_info        = f'7) 💍 Перстень: 5000💰\n'

    personal_shop = f'🏫 МАГАЗИН 🏫\n\n'
    personal_shop = personal_shop+seashell_info+bighand_info

    if lvl_ >= 5:
        personal_shop = personal_shop + anchor_info

        if lvl_ >= 10:
            personal_shop = personal_shop + lucky_info

            if lvl_ >= 15:
                personal_shop = personal_shop + blackhearth_info

                if lvl_ >= 20:
                    personal_shop = personal_shop + hearth_info 

                    if lvl_ >= 25:
                        personal_shop = personal_shop + ring_info

    personal_shop = personal_shop+f'\n❗ Для покупки введите: /купить (номер товара)\n❗ Команды других улучшений: "/доход+" и "/раколовка +"\n❗ Документация по предметам: https://vk.com/@meraki_vk-magazin'
    sender(personal_shop)

def raki_trap_lvl_up(user_id):
    """
        Функция, которая улучшает раколовку по команде пользователя(user_id), проверяя его текущий уровень и баланс
    """
    global users_balance, users_info

    try:
        if users_balance[user_id]['raki_trap_lvl'] == 1 and users_balance[user_id]['gold']>=100:
            users_balance[user_id]['raki_trap_lvl'] = 2
            users_balance[user_id]['gold'] -= 100
            sender(f'📈 Улучшение состоялось!\n\nТеперь у @id{user_id}(тебя) 2 уровень раколовки🎣\n🌊Можно получить от 20 до 80 🦞')

        elif users_balance[user_id]['raki_trap_lvl'] == 2 and users_balance[user_id]['gold']>=250:
            users_balance[user_id]['raki_trap_lvl'] = 3
            users_balance[user_id]['gold'] -= 250
            sender(f'📈 Улучшение состоялось!\n\nТеперь у @id{user_id}(тебя) 3 уровень раколовки🎣\n🌊Можно получить от 35 до 100 🦞')

        elif users_balance[user_id]['raki_trap_lvl'] == 3 and users_balance[user_id]['gold']>=1000:
            users_balance[user_id]['raki_trap_lvl'] = 4
            users_balance[user_id]['gold'] -= 1000
            sender(f'📈 Улучшение состоялось!\n\nТеперь у @id{user_id}(тебя) 4 уровень раколовки🎣\n🌊Можно получить от 50 до 100🦞 и от 0 до 5💰')

        elif users_balance[user_id]['raki_trap_lvl'] == 4 and users_balance[user_id]['gold']>=2500:
            users_balance[user_id]['raki_trap_lvl'] = 5
            users_balance[user_id]['gold'] -= 2500
            sender(f'📈 Улучшение состоялось!\n\nТеперь у @id{user_id}(тебя) 5 уровень раколовки🎣\n🌊Можно получить от 80 до 150🦞 и от 1 до 5💰')

        elif users_balance[user_id]['raki_trap_lvl'] == 5 and users_balance[user_id]['gold']>=5000:
            users_balance[user_id]['raki_trap_lvl'] = 6
            users_balance[user_id]['gold'] -= 5000
            sender(f'📈 Улучшение состоялось!\n\nТеперь у @id{user_id}(тебя) 6 уровень раколовки🎣\n🌊Можно получить от 100 до 200🦞 и от 2 до 6💰')

        elif users_balance[user_id]['raki_trap_lvl'] == 6 and users_balance[user_id]['gold']>=15000:
            users_balance[user_id]['raki_trap_lvl'] = 7
            users_balance[user_id]['gold'] -= 15000
            sender(f'📈 Улучшение состоялось!\n\nТеперь у @id{user_id}(тебя) 7 уровень раколовки🎣\n🌊Можно получить от 150 до 200🦞, от 3 до 10💰 и c малой вероятностью получить 1💎')

        elif users_balance[user_id]['raki_trap_lvl'] == 7 and users_balance[user_id]['gold']>=20000:
            users_balance[user_id]['raki_trap_lvl'] = 8
            users_balance[user_id]['gold'] -= 20000
            sender(f'📈 Улучшение состоялось!\n\nТеперь у @id{user_id}(тебя) 8 уровень раколовки🎣\n🌊Можно получить от 200 до 300🦞, от 5 до 15💰 и c малой вероятностью получить 1💎')

        elif users_balance[user_id]['raki_trap_lvl'] == 8 and users_balance[user_id]['gold']>=40000:
            users_balance[user_id]['raki_trap_lvl'] = 9
            users_balance[user_id]['gold'] -= 40000
            sender(f'📈 Улучшение состоялось!\n\nТеперь у @id{user_id}(тебя) 9 уровень раколовки🎣\n🌊Можно получить от 300 до 500🦞, от 10 до 20💰 и c малой вероятностью получить 1-2💎')

        elif users_balance[user_id]['raki_trap_lvl'] == 9 and users_balance[user_id]['gold']>=100000:
            users_balance[user_id]['raki_trap_lvl'] = 10
            users_balance[user_id]['gold'] -= 100000
            sender(f'📈 Улучшение состоялось!\n\nТеперь у @id{user_id}(тебя) 10 уровень раколовки🎣\n🌊Можно получить от 300 до 1000🦞, от 20 до 30💰, c малой вероятностью получить 1-3💎 и с ничтожно низким шансом получить 1🦪')

        elif users_balance[user_id]['raki_trap_lvl'] == 10:
            sender(f'📊 Улучшения больше не доступны!\n\n@id{user_id}(Твоя) раколовка🎣 имеет 10 уровень.\n🌊Можно получить от 300 до 1000🦞, от 20 до 30💰, c малой вероятностью получить 1-3💎 и с ничтожно низким шансом получить 1🦪')
        else:
            sender(f'📉 Улучшение пока недоступно. @id{user_id}(Ты) бомж!\n\nСейчас у тебя {users_balance[user_id]["raki_trap_lvl"]} уровень раколовки🎣\n\n2 🎣 = 100 💰\n3 🎣 = 250 💰\n4 🎣 = 1000 💰\n5 🎣 = 2500 💰\n6 🎣 = 5000 💰\n7 🎣 = 15000 💰\n8 🎣 = 20000 💰\n9 🎣 = 40000 💰\n10 🎣 = 100000 💰')

    except:
        pass

def raki_per_sms_lvl_up(user_id):
    """
        Функция, которая улучшает доход за сообщения по команде пользователя(user_id), проверяя его текущий уровень и баланс
    """
    global users_balance, users_info

    try: 
        if users_balance[user_id]['raki_per_sms_lvl'] == 1 and users_balance[user_id]['gold']>=200:
            users_balance[user_id]['raki_per_sms_lvl'] = 2
            users_balance[user_id]['gold'] -= 200
            sender(f'📈 Улучшение состоялось!\n\nТеперь @id{user_id}(ты) получаешь {users_balance[user_id]["raki_per_sms_lvl"]} 🦞 за 10 ✉\nУ тебя {users_balance[user_id]["gold"]} 💰')
        elif users_balance[user_id]['raki_per_sms_lvl'] == 2 and users_balance[user_id]['gold']>=400:
            users_balance[user_id]['raki_per_sms_lvl'] = 3
            users_balance[user_id]['gold'] -= 400
            sender(f'📈 Улучшение состоялось!\n\nТеперь @id{user_id}(ты) получаешь {users_balance[user_id]["raki_per_sms_lvl"]} 🦞 за 10 ✉\nУ тебя {users_balance[user_id]["gold"]} 💰')
        elif users_balance[user_id]['raki_per_sms_lvl'] == 3 and users_balance[user_id]['gold']>=600:
            users_balance[user_id]['raki_per_sms_lvl'] = 4
            users_balance[user_id]['gold'] -= 600
            sender(f'📈 Улучшение состоялось!\n\nТеперь @id{user_id}(ты) получаешь {users_balance[user_id]["raki_per_sms_lvl"]} 🦞 за 10 ✉\nУ тебя {users_balance[user_id]["gold"]} 💰')
        elif users_balance[user_id]['raki_per_sms_lvl'] == 4 and users_balance[user_id]['gold']>=800:
            users_balance[user_id]['raki_per_sms_lvl'] = 5
            users_balance[user_id]['gold'] -= 800
            sender(f'📈 Улучшение состоялось!\n\nТеперь @id{user_id}(ты) получаешь {users_balance[user_id]["raki_per_sms_lvl"]} 🦞 за 10 ✉\nУ тебя {users_balance[user_id]["gold"]} 💰')
        elif users_balance[user_id]['raki_per_sms_lvl'] == 5 and users_balance[user_id]['gold']>=1000:
            users_balance[user_id]['raki_per_sms_lvl'] = 6
            users_balance[user_id]['gold'] -= 1000
            sender(f'📈 Улучшение состоялось!\n\nТеперь @id{user_id}(ты) получаешь {users_balance[user_id]["raki_per_sms_lvl"]} 🦞 за 10 ✉\nУ тебя {users_balance[user_id]["gold"]} 💰')
        elif users_balance[user_id]['raki_per_sms_lvl'] == 6 and users_balance[user_id]['gold']>=3000:
            users_balance[user_id]['raki_per_sms_lvl'] = 7
            users_balance[user_id]['gold'] -= 3000
            sender(f'📈 Улучшение состоялось!\n\nТеперь @id{user_id}(ты) получаешь {users_balance[user_id]["raki_per_sms_lvl"]} 🦞 за 10 ✉\nУ тебя {users_balance[user_id]["gold"]} 💰')
        elif users_balance[user_id]['raki_per_sms_lvl'] == 7 and users_balance[user_id]['gold']>=5000:
            users_balance[user_id]['raki_per_sms_lvl'] = 8
            users_balance[user_id]['gold'] -= 5000
            sender(f'📈 Улучшение состоялось!\n\nТеперь @id{user_id}(ты) получаешь {users_balance[user_id]["raki_per_sms_lvl"]} 🦞 за 10 ✉\nУ тебя {users_balance[user_id]["gold"]} 💰')
        elif users_balance[user_id]['raki_per_sms_lvl'] == 8 and users_balance[user_id]['gold']>=8000:
            users_balance[user_id]['raki_per_sms_lvl'] = 9
            users_balance[user_id]['gold'] -= 8000
            sender(f'📈 Улучшение состоялось!\n\nТеперь @id{user_id}(ты) получаешь {users_balance[user_id]["raki_per_sms_lvl"]} 🦞 за 10 ✉\nУ тебя {users_balance[user_id]["gold"]} 💰')
        elif users_balance[user_id]['raki_per_sms_lvl'] == 9 and users_balance[user_id]['gold']>=1000:
            users_balance[user_id]['raki_per_sms_lvl'] = 10
            users_balance[user_id]['gold'] -= 10000
            sender(f'📈 Улучшение состоялось!\n\nТеперь @id{user_id}(ты) получаешь {users_balance[user_id]["raki_per_sms_lvl"]} 🦞 за 10 ✉\nУ тебя {users_balance[user_id]["gold"]} 💰')
        elif users_balance[user_id]['raki_per_sms_lvl'] == 10:
            sender(f'📊 Улучшения больше не доступны!\n\n@id{user_id}(Твой) доход 10 🦞 за 10 ✉')                               
        else:
            sender(f'📉 Улучшение пока недоступно. @id{user_id}(Ты) бомж!\n\nСейчас ты получаешь: {users_balance[user_id]["raki_per_sms_lvl"]} 🦞 за 10 ✉\n\n2 🦞 за 10 ✉ = 200 💰\n3 🦞 за 10 ✉ = 400 💰\n4 🦞 за 10 ✉ = 600 💰\n5 🦞 за 10 ✉ = 800 💰\n6 🦞 за 10 ✉ = 1000 💰\n7 🦞 за 10 ✉ = 3000 💰\n8 🦞 за 10 ✉ = 5000 💰\n9 🦞 за 10 ✉ = 8000 💰\n10 🦞 за 10 ✉ = 10000 💰')

    except:
        pass

def get_raki_from_trap(user_id):
    """
        Функция, которая присваивает результат "вытягивания" раколовки пользователем (user_id), занося изменения в необходимы БД
    """
    global chat_info, users_balance, users_info

    if user_id not in chat_info['raki_trap_opened']:
        chat_info['raki_trap_opened'].append(user_id)
        lvl  = users_balance[user_id]['raki_trap_lvl']
        send_info = f'🌊 {users_info[user_id]["nickname"]}, тебе удалось достать '

        # Расчет уровня раколовки и соответствующих наград:
        raki_reward_stats   = {1:[1,50],2:[20,80],3:[35,100],4:[50,100],5:[80,150],6:[100,200],7:[150,200],8:[200,300],9:[300,500],10:[300,1000]}
        gold_reward_stats   = {4:[0,5],5:[1,5],6:[2,6],7:[3,10],8:[5,15],9:[10,20],10:[20,30]}
        gems_reward_stats   = {7:[0,1],8:[0,1],9:[0,2],10:[0,3]}
        pearls_reward_stats = {10:[0,1]}

        if lvl<=3:
            get_raki = random.randint(raki_reward_stats[lvl][0],raki_reward_stats[lvl][1])
            users_balance[user_id]['raki'] += get_raki

            send_info += f'{get_raki}🦞'

        elif lvl<=6:
            get_raki = random.randint(raki_reward_stats[lvl][0],raki_reward_stats[lvl][1])
            get_gold = random.randint(gold_reward_stats[lvl][0],gold_reward_stats[lvl][1])

            users_balance[user_id]['raki'] += get_raki
            users_balance[user_id]['gold'] += get_gold

            send_info += f'{get_raki}🦞 и {get_gold}💰'

        elif lvl<= 9:
            get_raki = random.randint(raki_reward_stats[lvl][0],raki_reward_stats[lvl][1])
            get_gold = random.randint(gold_reward_stats[lvl][0],gold_reward_stats[lvl][1])

            if random.randint(0,100)>=92:
                get_gems = random.randint(gems_reward_stats[lvl][0],gems_reward_stats[lvl][1])
            else:
                get_gems = 0

            users_balance[user_id]['raki'] += get_raki
            users_balance[user_id]['gold'] += get_gold
            users_balance[user_id]['gems'] += get_gems

            send_info += f'{get_raki}🦞, {get_gold}💰 и {get_gems}💎'

        elif lvl== 10:
            get_raki = random.randint(raki_reward_stats[lvl][0],raki_reward_stats[lvl][1])
            get_gold = random.randint(gold_reward_stats[lvl][0],gold_reward_stats[lvl][1])

            if random.randint(0,100)>=90:
                get_gems = random.randint(gems_reward_stats[lvl][0],gems_reward_stats[lvl][1])
            else:
                get_gems = 0

            if random.randint(0,1000)>=995:
                get_pearls = random.randint(pearls_reward_stats[lvl][0],pearls_reward_stats[lvl][1])
            else:
                get_pearls = 0

            users_balance[user_id]['raki']   += get_raki
            users_balance[user_id]['gold']   += get_gold
            users_balance[user_id]['gems']   += get_gems
            users_balance[user_id]['pearls'] += get_pearls


            send_info += f'{get_raki}🦞, {get_gold}💰, {get_gems}💎 и {get_pearls}🦪'


        send_info += f" из раколовки.\n🎣Ты снова забрасываешь её.\n📅Посмотрим, что будет завтра..."
        sender(send_info)
    else:
        sender(f'⌚ {users_info[user_id]["nickname"]}, твоя раколовка заброшена. Проверь её завтра.')

def give_currency(msg, user_id, peer_id):
    """
        Функция осуществаляет перевод валюты между написавшим (user_id) и тем, кому пересылается (peer_id) сообщение (msg)
    """
    global users_balance, users_info

    if user_id == peer_id:
        pass

    else:
        if msg.split()[1] in ["р", "рачков", "раков", "p", "раки", "рачками", "раками", "рачки"]:
            try:
                if msg.split(" ")[-1].isnumeric() and int(msg.split(" ")[-1]) > 0:
                    give_raki = int(msg.split(" ")[-1])

                    if give_raki <= users_balance[user_id]['raki']:
                        users_balance[user_id]['raki'] -= give_raki
                        users_balance[peer_id]['raki'] += give_raki

                        sender(f"✅ Перевод выполенен!\n\n📤 {users_info[user_id]['nickname']}: {users_balance[user_id]['raki']}🦞\n📥 {users_info[peer_id]['nickname']}: {users_balance[peer_id]['raki']}🦞")

                    else:
                        sender(f'⚠Недостаточно средств\n👛 Ваш баланс: {users_balance[user_id]["raki"]}🦞')

            except:
                sender("⚠Некорректно введена команда или выбранную валюту невозможно отдать.\n📌Читайте документацию:\nhttps://vk.com/@meraki_vk-peredacha-valut-mezhdu-uchastnikami")


        elif msg.split()[1] in ["лайк", "л", "с", "сердцами", "c", "лайками", "лайки"]:
            try:
                if msg.split(" ")[-1].isnumeric() and int(msg.split(" ")[-1]) > 0:
                    give_likes = int(msg.split(" ")[-1])

                    if give_likes <= users_balance[user_id]['likes']:
                        users_balance[user_id]['likes'] -= give_likes
                        users_balance[peer_id]['likes'] += give_likes

                        sender(f"✅ Перевод выполенен!\n\n📤 {users_info[user_id]['nickname']}: {users_balance[user_id]['likes']}❤\n📥 {users_info[peer_id]['nickname']}: {users_balance[peer_id]['likes']}❤")

                    else:
                        sender(f'⚠Недостаточно средств\n👛 Ваш баланс: {users_balance[user_id]["likes"]}❤')
            except:
                sender("⚠Некорректно введена команда или выбранную валюту невозможно отдать.\n📌Читайте документацию:\nhttps://vk.com/@meraki_vk-peredacha-valut-mezhdu-uchastnikami")
        else:
            sender("⚠Некорректно введена команда или выбранную валюту невозможно отдать.\n📌Читайте документацию:\nhttps://vk.com/@meraki_vk-peredacha-valut-mezhdu-uchastnikami")

def sender_profile_chat():
    """
        Функция выводит информацию о чате.
    """
    global chat_info

    sms_   = chat_info["all_sms"]
    sms_t  = chat_info["sms_today"]
    nft_   = chat_info["NFT"]
    today_ = chat_info["today"]

    sender(f"meraki\n{today_}\n\n✉ Всего: {sms_}\n📨 Сегодня: {sms_t}\t\n💷 NFT: {nft_}\n")

def sender_profile_info(user_id):
    """
        Функция выводит информацию о профиле написавшего команду пользователя (user_id)
    """
    global users_balance , users_info, users_stats

    name = users_info[user_id]['nickname']
    date = users_info[user_id]['date_appearance']
    sms_ = users_stats[user_id]['all_sms']
    sms_t = users_stats[user_id]['today_sms']

    raki_   = users_balance[user_id]['raki']
    gold_   = users_balance[user_id]['gold']
    likes_  = users_balance[user_id]['likes']
    gems_   = users_balance[user_id]['gems']
    pearls_ = users_balance[user_id]['pearls']
    souls_  = users_balance[user_id]['souls']

    trap_lvl = users_balance[user_id]['raki_trap_lvl']
    raki_sms = users_balance[user_id]['raki_per_sms_lvl']

    lvl_ = str(get_lvl_user(users_balance[user_id]['exp']))

    sender(f"👤 {name}\n📅 Появление: {date}\t\n✉ Сообщений: {sms_} ({sms_t})\n\n🦞 Рачков: {raki_}\n💰 Монет: {gold_}\n❤ Лайков: {likes_}\n💎 Алмазов: {gems_}\n🦪 Жемчуг: {pearls_}\n👻 Души: {souls_}\n\n⚜ Уровень: {lvl_}\n🎣 Уровень раколовки: {trap_lvl}\n💹 Доход за 10 смс: {raki_sms}")

def get_lvl_user(exp):
    """
        Функция возвращает уровень пользователя, по его опыту (exp)
    """
    levels_inf = {
        1:[0,30],
        2:[31,100],
        3:[101,300],
        4:[301,560],
        5:[561,899],
        6:[900,1300],
        7:[1300,1750],
        8:[1751,2299],
        9:[2300,3000],
        10:[3001,3500],
        11:[3501,4009],
        12:[4010,4700],
        13:[4701,5309],
        14:[5310,5990],
        15:[5991,6999],
        16:[7000,7999],
        17:[8000,8999],
        18:[9000,9999],
        19:[10000,10999],
        20:[11000,13000],
        21:[13001,15000],
        22:[15001,17000],
        23:[17001,19000],
        24:[19001,21000],
        25:[21001,23000],
        26:[23001,25000],
        27:[25001,27000],
        28:[27001,30000],
        29:[30001,34599],
        30:[34600,39999],
        31:[40000,45000],
        32:[45001,49999],
        33:[50000,60000],
        34:[60001,74999],
        35:[75000,80000],
        36:[80001,89999],
        37:[90000,99999],
        38:[100000,120000],
        39:[120001,149999],
        40:[150000,199999],
        41:[200000,299999],
        42:[300000,999999],
        43:[1000000,999999999]
    }

    for lvl in levels_inf:
        min_exp = levels_inf[lvl][0]
        max_exp = levels_inf[lvl][1]

        if (exp >= min_exp) and (exp <= max_exp):
            return lvl

def set_today():
    """
        Функция обновляет данные о текущей дате: день, неделя, месяц
    """
    global chat_info, users_stats

    datetime_ = datetime.datetime.now()

    today = datetime_.strftime("%d-%m-%Y")
    week  = str(datetime_.weekday())
    month = datetime_.strftime("%m")

    if chat_info['today'] != today:
        chat_info['today']     = today
        chat_info['sms_today'] = 0
        chat_info['raki_trap_opened'] = []

        for user in users_stats:
            users_stats[user]['today_sms'] = 0

        if chat_info['curr_day_of_week'] != week:
            chat_info['curr_day_of_week'] = week

        if chat_info['curr_num_of_month'] != month:
            chat_info['curr_num_of_month'] = month

def casinoGameProcess(msg, user_id):
    """
        Функция мини-игры казино.
    """
    global users_balance, users_info

    try:
        gamer_rate = int(msg.split(" ")[-1])

        if gamer_rate > 0 and users_balance[user_id]["gold"] >= gamer_rate:

            # Сбор необходимых данных для игры
            gamer_name  = f"Игрок: {users_info[user_id]['nickname']}\n\n"
            random_game = random.randint(0,36)
            name_game   = msg.split(" ")[-2]
            casino = {
                "1-12": [i for i in range(1,13)],
                "13-24": [i for i in range(13,25)],
                "25-36": [i for i in range(25,37)],
                "1-18": [i for i in range(1, 19)],
                "19-36": [i for i in range(19,37)],
                "чет": [i for i in range(1,37) if i%2 == 0],
                "нечет": [i for i in range(1,37) if i%2 == 1],
                "1": [1,4,7,10,13,16,19,22,25,28,31,34],
                "2": [2,5,8,11,14,17,20,23,26,29,32,35],
                "3": [3,6,9,12,15,18,21,24,27,30,33,36]
            }

            # Корректна ли команда пользователя? (msg)
            if name_game in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18',
                             '19','20','21','22','23','24','25','26','27','28','29','30','31','32','33','34',
                             '35','36', '1-12','13-24','25-36','1-18','19-36','чт','четное', 'even', 'чет', 
                             'четн','нчт', 'нечетное', 'odd', 'нечет', 'нечетн', 'нч', "столб1", "1столб", 
                             "столбец1", "1столбец", "1c", "c1", "столб2", "2столб", "столбец2", "2столбец",
                             "2c", "c2", "столб3", "3столб", "столбец3", "3столбец", "3c", "c3"]:
                game_info = f'{gamer_name}🚩 Ставка: {gamer_rate}\n🎰 Ожидание: {name_game}\n🎲 На рулетке: {random_game}\n\n'

                # Отправка сообщения о результате игры и обновление БД
                if (name_game == '1-12') and (random_game in casino["1-12"]):
                    users_balance[user_id]['gold'] += ((int(gamer_rate*3))-gamer_rate)
                    win_info = f'✅Ты выиграл {((int(gamer_rate*3))-gamer_rate)} 💰 \n\n'
                    sender(game_info+win_info+ f'💰Твой баланс: {users_balance[user_id]["gold"]}')

                elif (name_game == '13-24') and (random_game in casino["13-24"]):
                    users_balance[user_id]['gold'] += ((int(gamer_rate*3))-gamer_rate)
                    win_info = f'✅Ты выиграл {((int(gamer_rate*3))-gamer_rate)} 💰 \n\n'
                    sender(game_info+win_info+ f'💰Твой баланс: {users_balance[user_id]["gold"]}')
                
                elif (name_game == '25-36') and (random_game in casino["25-36"]):
                    users_balance[user_id]['gold'] += ((int(gamer_rate*3))-gamer_rate)
                    win_info = f'✅Ты выиграл {((int(gamer_rate*3))-gamer_rate)} 💰 \n\n'
                    sender(game_info+win_info+ f'💰Твой баланс: {users_balance[user_id]["gold"]}')
                
                elif (name_game in ['чт','четное', 'even', 'чет', 'четн']) and (random_game in casino["чет"]):
                    users_balance[user_id]['gold'] += ((int(gamer_rate*2))-gamer_rate)
                    win_info = f'✅Ты выиграл {((int(gamer_rate*2))-gamer_rate)} 💰 \n\n'
                    sender(game_info+win_info+ f'💰Твой баланс: {users_balance[user_id]["gold"]}')

                elif (name_game in ['нчт', 'нечетное', 'odd', 'нечет', 'нечетн', 'нч']) and (random_game in casino["нечет"]):
                    users_balance[user_id]['gold'] += ((int(gamer_rate*2))-gamer_rate)
                    win_info = f'✅Ты выиграл {((int(gamer_rate*2))-gamer_rate)} 💰 \n\n'
                    sender(game_info+win_info+ f'💰Твой баланс: {users_balance[user_id]["gold"]}')

                elif (name_game in ["столб1", "1столб","столбец1", "1столбец", "1с", "с1"]) and (random_game in casino["1"]):
                    users_balance[user_id]['gold'] += ((int(gamer_rate*3))-gamer_rate)
                    win_info = f'✅Ты выиграл {((int(gamer_rate*3))-gamer_rate)} 💰 \n\n'
                    sender(game_info+win_info+ f'💰Твой баланс: {users_balance[user_id]["gold"]}')

                elif (name_game in ["столб2", "2столб", "столбец2", "2столбец","2с", "с2"]) and (random_game in casino["2"]):
                    users_balance[user_id]['gold'] += ((int(gamer_rate*3))-gamer_rate)
                    win_info = f'✅Ты выиграл {((int(gamer_rate*3))-gamer_rate)} 💰 \n\n'
                    sender(game_info+win_info+ f'💰Твой баланс: {users_balance[user_id]["gold"]}')

                elif (name_game in ["столб3", "3столб", "столбец3", "3столбец", "3с", "с3"]) and (random_game in casino["3"]):
                    users_balance[user_id]['gold'] += ((int(gamer_rate*3))-gamer_rate)
                    win_info = f'✅Ты выиграл {((int(gamer_rate*3))-gamer_rate)} 💰 \n\n'
                    sender(game_info+win_info+ f'💰Твой баланс: {users_balance[user_id]["gold"]}')

                elif (name_game in [i for i in range(1,37)]) and (random_game == name_game):
                    users_balance[user_id]['gold'] += ((int(gamer_rate*36))-gamer_rate)
                    win_info = f'✅Ты выиграл {((int(gamer_rate*36))-gamer_rate)} 💰 \n\n'
                    sender(game_info+win_info+ f'💰Твой баланс: {users_balance[user_id]["gold"]}')

                elif (name_game == '1-18') and (random_game in casino["1-18"]):
                    users_balance[user_id]['gold'] += ((int(gamer_rate*2))-gamer_rate)
                    win_info = f'✅Ты выиграл {((int(gamer_rate*2))-gamer_rate)} 💰 \n\n'
                    sender(game_info+win_info+ f'💰Твой баланс: {users_balance[user_id]["gold"]}')

                elif (name_game == "19-36") and (random_game in casino["19-36"]):
                    users_balance[user_id]['gold'] += ((int(gamer_rate*2))-gamer_rate)
                    win_info = f'✅Ты выиграл {((int(gamer_rate*2))-gamer_rate)} 💰 \n\n'
                    sender(game_info+win_info+ f'💰Твой баланс: {users_balance[user_id]["gold"]}')

                else:
                    users_balance[user_id]['gold'] -= gamer_rate
                    sender(game_info + '❌Ты проиграл!\n\n' + f'💰Твой баланс: {users_balance[user_id]["gold"]}')

            else:
                sender("⚠Некорректная ставка.\n📌Читайте документацию:\nhttps://vk.com/@meraki_vk-kazino")
        else:
            sender("⚠Недостаточно денег или некорректная ставка.\n📌Читайте документацию:\nhttps://vk.com/@meraki_vk-kazino")
    except:
        sender("⚠Некорректно введена команда.\n📌Читайте документацию:\nhttps://vk.com/@meraki_vk-kazino")
        print(f"Кто-то неправильно стал юзать казино! {users_info[user_id]['nickname']}")

def transfer_raki_to_gold(msg, user_id):
    """
        Функция переводит одну валюту в другую (раки в монеты)
    """
    global users_balance, users_info

    try:
        name = f"{users_info[user_id]['f_name']}"
        want_to_transfer = msg.split()[-1]

        if want_to_transfer in ["р", "рачков", "раков", "раки", "p", "рак"]:
            need_change_raki = int(msg.split()[-2])

            if users_balance[user_id]['raki'] >= need_change_raki:
                users_balance[user_id]['raki'] -= int(need_change_raki)
                users_balance[user_id]['gold'] += int(need_change_raki//5.5)
                sender(f"{name}, обмен выполнен!\n🦞 Рачков: {users_balance[user_id]['raki']}\n💰 Монет: {users_balance[user_id]['gold']}")

            else:
                sender(f"⚠Недостаточно средств\nНеобходимо: {int(need_change_raki)} 🦞")

        elif want_to_transfer in ["золото", "золота", "з", "г", "голды", "голд", "монет", "монеты", "м"]:
            need_add_gold = int(msg.split()[-2])

            if users_balance[user_id]['raki'] >= int(need_add_gold*5.5):
                users_balance[user_id]['raki'] -= int(need_add_gold*5.5)
                users_balance[user_id]['gold'] += int(need_add_gold)
                sender(f"{name}, обмен выполнен!\n🦞 Рачков: {users_balance[user_id]['raki']}\n💰 Монет: {users_balance[user_id]['gold']}")

            else:
                sender(f"⚠Недостаточно средств\nНеобходимо: {int(need_add_gold*5.5)} 🦞")

        else:
            sender("⚠Некорректно введена команда.\nЧитайте документацию перевода валюты:\nhttps://vk.com/@meraki_vk-obmen-valut")    

    except:
        sender("⚠Некорректно введена команда.\nЧитайте документацию перевода валюты:\nhttps://vk.com/@meraki_vk-obmen-valut")
        print(f"Кто-то неправильно стал юзать трансфер! {users_info[user_id]['nickname']}")

def generate_coupon(reward, currency, times):
    """
        Функция генерации купона, занесение его в данных и оповещения участников беседы
    """
    global coupons

    part_coupon1 = ''.join(random.choice(string.ascii_lowercase) for x in range(4))
    part_coupon2 = ''.join(random.choice(string.ascii_lowercase) for x in range(4))
    part_coupon3 = ''.join(random.choice(string.ascii_lowercase) for x in range(4))
    part_coupon4 = ''.join(random.choice(string.ascii_lowercase) for x in range(4))
    coupon = f'{part_coupon1}-{part_coupon2}-{part_coupon3}-{part_coupon4}'

    coupons[coupon] = [reward, currency, int(times)+3]
    sender(f'📢 @all\n💥НОВЫЙ КУПОН💥\n{coupon}')

def enter_coupon(msg, user_id):
    """
        Функция проверки работоспособности введенного купона для конкретного пользователя (user_id)
    """
    global coupons, users_balance, users_info

    curr_coupon = msg.split()[-1]

    if curr_coupon in coupons:
        if len(coupons[curr_coupon]) < coupons[curr_coupon][2]:
            if user_id not in coupons[curr_coupon]:

                coupons[curr_coupon].append(user_id)
                users_balance[user_id][coupons[curr_coupon][1]] += coupons[curr_coupon][0]

                sender(f'✅{users_info[user_id]["nickname"]}, купон успешно использован!')

            else:
                sender("⚠Повторное использование купона невозможно.")

        else:
            sender("⚠Данный купон уже нельзя активировать.")    

    else:
        sender("⚠Купон не найден.")

# =============================================================================================== #
# Блок с начальными действиями (выполнение функций, создание констант, переменных и т.д.):

set_today()

# =============================================================================================== #
# Блок обрабоки longpoll:

while True:
    try:
        for event in longpoll.listen():

            # Если новая запись в сообществе:
            if event.type == VkBotEventType.WALL_POST_NEW:
                sender('📢 @all\n\n🆕Новая запись на стене сообщества!🆕')

            # Если новое сообщение в беседе:
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.from_chat:

                    # Сбор начльной необходимой информации:
                    today   = datetime.datetime.now().strftime("%d-%m-%Y")
                    user_id = str(event.object.message['from_id'])
                    msg     = event.object.message['text'].lower()

                    # Проверка на корректную дату:
                    if today != chat_info['today']:
                        set_today()

                    # Проверка на нового пользователя:
                    if user_id not in users_balance:
                        add_info_about_new_member(user_id)

                    # Проверка на использование команды:
                    if msg.startswith("/"):
                        try:
                            peer_id = str(event.object.message["reply_message"]['from_id'])
                        except:
                            peer_id = "None"
                        do_command(msg, user_id, peer_id)

                    # Иначе, с неким шансом пусть бот отправит случайную фразу:
                    elif random.randint(0,100)>92:
                        sender(random_msg(random_inserts))

                    # Генерация купонов, в зависимости от количества написанных за день сообщений:
                    if chat_info["sms_today"] == 50:
                        generate_coupon(30, "raki", 5)
                    elif chat_info["sms_today"] == 200:
                        generate_coupon(100, "raki", 5)
                    elif chat_info["sms_today"] == 500:
                        generate_coupon(300, "raki", 3)
                    elif chat_info["sms_today"] == 1000:
                        generate_coupon(500, "raki", 1)

# =============================================================================================== #
# Блок команд, которые всегда будут выполняться без условий при любом сообщении:

                    add_sms_and_raki(user_id)

# =============================================================================================== #
# Блок обновления и сохраненеия изменений json БД

                    save_users_balance = {"users_balance":[users_balance]}
                    save_users_info    = {"users_info":[users_info]}
                    save_users_stats   = {"users_stats":[users_stats]}
                    save_chat_info     = {"chat_info":[chat_info]}
                    save_coupons       = {"coupons": [coupons]}

                    with open('rpg/balance_info.json', 'w', encoding="utf-8", errors='ignore') as file:
                        json.dump(save_users_balance, file, indent=2, ensure_ascii=False)

                    with open('rpg/stats_info.json', 'w', encoding="utf-8", errors='ignore') as file:
                        json.dump(save_users_stats, file, indent=2, ensure_ascii=False)

                    with open('rpg/user_info.json', 'w', encoding="utf-8", errors='ignore') as file:
                        json.dump(save_users_info, file, indent=2, ensure_ascii=False)

                    with open('rpg/chat_info.json', 'w', encoding="utf-8", errors='ignore') as file:
                        json.dump(save_chat_info, file, indent=2, ensure_ascii=False)

                    with open('rpg/coupons.json', 'w', encoding="utf-8", errors='ignore') as file:
                        json.dump(save_coupons, file, indent=2, ensure_ascii=False)

# =============================================================================================== #
# Блок авто-перезапуска бота:

    except Exception as e:
        print('\n\nОшибка:\n', traceback.format_exc())
        print("\n Переподключение к серверам ВК \n")

        time.sleep(3)

# =============================================================================================== #