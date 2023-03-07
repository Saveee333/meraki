# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
import pandas as pd
import json
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from pandas.plotting import table
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
"""
	Функции, для удобного и быстрого считывания json данных в
	приемлемого вида датафреймы.

"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def get_balance_info_df(path):
    """
        Функция возвращает датафрейм с данными о балансе пользователей беседы.
        path - путь к файлу, включая его имя с расширением.
        Функция не универсальная и работает с конкретным шаблоном json файла.
    """

    with open(path, 'r', encoding="utf-8", errors='ignore') as file:
        data_file = json.load(file)

    df_json = []
    for ids in data_file['users_balance'][0]:
        raki = data_file['users_balance'][0][ids]["raki"]
        gold = data_file['users_balance'][0][ids]["gold"]
        likes = data_file['users_balance'][0][ids]["likes"]
        pearls = data_file['users_balance'][0][ids]["pearls"]
        souls = data_file['users_balance'][0][ids]["souls"]
        exp = data_file['users_balance'][0][ids]["exp"]
        raki_trap_lvl = data_file['users_balance'][0][ids]["raki_trap_lvl"]
        raki_per_sms_lvl = data_file['users_balance'][0][ids]["raki_per_sms_lvl"]
    
        df_json.append({"id":str(ids), "raki":raki, "gold":gold, "likes":likes, "pearls":pearls, "souls":souls,
                        "exp":exp, "raki_trap_lvl":raki_trap_lvl, "raki_per_sms_lvl":raki_per_sms_lvl})
    
    return pd.json_normalize(df_json)

def get_user_info_df(path):
    """
        Функция возвращает датафрейм с данными о пользователях беседы.
        path - путь к файлу, включая его имя с расширением.
        Функция не универсальная и работает с конкретным шаблоном json файла.
    """

    with open(path, 'r', encoding="utf-8", errors='ignore') as file:
        data_file = json.load(file)

    df_json = []
    for ids in data_file['users_info'][0]:
        f_name = data_file['users_info'][0][ids]["f_name"]
        l_name = data_file['users_info'][0][ids]["l_name"]
        nickname = data_file['users_info'][0][ids]["nickname"]
        sex = data_file['users_info'][0][ids]["sex"]
        date_appearance = data_file['users_info'][0][ids]["date_appearance"]
    
        df_json.append({"id":str(ids), "f_name":f_name, "l_name":l_name, "nickname":nickname, "sex":sex,
                        "date_appearance":date_appearance})
    
    return pd.json_normalize(df_json)

def get_stats_info_df(path):
    """
        Функция возвращает датафрейм с данными о статистике пользователей беседы.
        path - путь к файлу, включая его имя с расширением.
        Функция не универсальная и работает с конкретным шаблоном json файла.
    """

    with open(path, 'r', encoding="utf-8", errors='ignore') as file:
        data_file = json.load(file)

    df_json = []
    for ids in data_file['users_stats'][0]:
        last_day_communication = data_file['users_stats'][0][ids]["last_day_communication"]
        all_sms = data_file['users_stats'][0][ids]["all_sms"]
        today_sms = data_file['users_stats'][0][ids]["today_sms"]
        bad_sms = data_file['users_stats'][0][ids]["bad_sms"]
        opened_boxes = data_file['users_stats'][0][ids]["opened_boxes"]
        doned_tasks = data_file['users_stats'][0][ids]["doned_tasks"]
    
        df_json.append({"id":str(ids), "last_day_communication":last_day_communication, "all_sms":all_sms,
                        "today_sms":today_sms, "bad_sms":bad_sms, "opened_boxes":opened_boxes, "doned_tasks":doned_tasks})
    
    return pd.json_normalize(df_json)

def get_allSms_todaySms(path):
    """
        Функция возвращает словарь с данными о написанных сообщениях в беседе.
        path - путь к файлу, включая его имя с расширением.
        Функция не универсальная и работает с конкретным шаблоном json файла.
    """

    with open(path, 'r', encoding="utf-8", errors='ignore') as file:
        data_file = json.load(file)
    
    return {"all":data_file['chat_info'][0]["all_sms"] ,"today":data_file['chat_info'][0]["today"], 'day':data_file['chat_info'][0]["sms_today"]}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def daily_info():
    """
        Функция выгружающая дневную информацию.
    """
    
    # Указание путей и считывание датафрейсов:
    path_bi = 'rpg/balance_info.json'
    path_ui = 'rpg/user_info.json'
    path_si = 'rpg/stats_info.json'
    path_dy = 'rpg/chat_info.json'
    
    df_bi = get_balance_info_df(path_bi)
    df_ui = get_user_info_df(path_ui)
    df_si = get_stats_info_df(path_si)
    extra_df = df_bi.merge(df_ui, how="inner", on="id")
    full_df  = extra_df.merge(df_si, how="inner", on="id")
    day_info = get_allSms_todaySms(path_dy)
    
    # Небольшая реконструкция итогового датафрейма:
    full_df = full_df.query('today_sms > 0') \
                     .rename(columns={'id':'vk-id','raki':'Рачки','gold':'Монеты','likes':'Лайки','pearls':'Жемчуг',
                                      'souls':'Души','exp':'Опыт','raki_trap_lvl':'Уровень раколовки',
                                      'raki_per_sms_lvl':'Уровень дохода','nickname':'Имя','sex':'Пол',
                                      'date_appearance':'Дата вступления','last_day_communication':'Последний день общения',
                                      'all_sms':'Всего сообщений','today_sms':'Сообщений сегодня','bad_sms':'Плохих сообщений',
                                      'opened_boxes':'Открыто коробок','doned_tasks':'Выполнено заданий'}) \
                      .drop(columns=['f_name','l_name']) \
                      .sort_values('Сообщений сегодня', ascending=False)
    full_df["Пол"] = np.where(full_df['Пол'] == 1, "жен", "муж")
    
    # Сохранение картинки - датафрейма
    plt.figure(figsize=(50, 130))
    ax = plt.subplot(111, frame_on=False)
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False) 
    table(ax, full_df, loc='center') 
    plt.savefig(f'reports/{day_info["today"]}.png')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #