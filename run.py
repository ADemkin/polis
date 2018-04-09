# coding=utf-8

import sys
import re
import xml.etree.ElementTree
import csv
import os
import traceback
from bottle import route, run, template, post, request, HTTPResponse, static_file, redirect
from io import StringIO
import collections

import cadastral_data as cd

from decouple import config


ROOT = '/var/tmp/polis/static/'
STATIC = 'var/tmp/static/'
LOCAL = 'static/'

STATIC_DIR = config('STATIC_DIR') or LOCAL
SETTINGS_DIR = config('SETTINGS_DIR') or LOCAL
DEBUG_MODE = config('DEBUG_MODE') or True
PORT = config('PORT') or 9999

# scp ~/impo.py root@138.197.223.128:/var/tmp/impo.py

# VARIABLE / table name # old name (same name in xml)
# id should be lowercase, this is ms excel bug
ID_DDU = 'id'  # 'ID_DDU',
CADASTRAL_NUM = '№ ЗУ'  # 'Num_Uchastok', Кадарстровый номер
DDU_DOC_DESC_DATE = 'Дата ДДУ'  # 'DduDocDesc_date',
DDU_DOC_DESC_NUMBER = '№ ДДУ'  # 'DduDocDesc_number'
DDU_DATE = 'Дата регистрации ДДУ'  # 'DduDate',
DDU_REG_NUMBER = '№ регистрации ДДУ'  # 'DduRegNo',
DOGOVOR_TYPE = 'Тип Договора'  # 'Type_dogovor',
ADRESS = 'Адрес'  # 'address',
ROOMS = 'Кол-во комнат'  # 'rooms'
AREA = 'Площадь'  # 'area'
FLOOR = 'Этаж'  # 'floor'
OBJECT_TYPE = 'Тип помещения'  # 'type_object'
OBJECT_NUMBER = '№ объекта'  # 'object'
TYPE = 'Тип_исх'  # 'type',
CORPUS = 'Корпус'  # 'corpus'
SECTION = 'Секция'  # 'section'
ENTRANCE = 'Подъезд'  # 'entrance'
OWNERS = 'ФИО'  # 'owners',
OWNER_TYPE = 'ФЛ/ЮЛ'  # 'Type_owner'
LOAN_DATE = 'Дата регистрации залога'  # 'loanDate'
LOAN_DURATION = 'Срок залога'  # 'loanDuration'
LOAN_NAME = 'Тип залога'  # 'loanName'
LOAN_NUMBER = '№ залога'  # 'loanNumber'
LOAN_OWNER_NAME = 'Банк'  # 'loanOwnerName' # Переделываем в Банк, сейчас здесь ФИО дольщика
WHOLESALE = 'Кол-во купленных лотов'  # 'wholesale',
DDU_DESC = 'Название ДДУ' # 'DduDocDesc
FULL_ADDRESS = 'Объект и адрес' # full_address
CHECK_THIS = "проверить!" # check!

SOURCE_FILE = 'Объект'

PROJECT_NAME = 'Проект'
GLORAX_COMPETITOR = 'Конкурент проекта Glorax'


# all table headers in appearance order
ALL_KEYS = [
    ID_DDU,
    CADASTRAL_NUM,
    PROJECT_NAME,
    SOURCE_FILE,
    GLORAX_COMPETITOR,
    DDU_DESC,
    DDU_DOC_DESC_DATE,
    DDU_DOC_DESC_NUMBER,
    DDU_DATE,
    DDU_REG_NUMBER,
    DOGOVOR_TYPE,
    FULL_ADDRESS,
    ADRESS,
    CORPUS,
    SECTION,
    ENTRANCE,
    OBJECT_TYPE,
    TYPE,
    ROOMS,
    AREA,
    FLOOR,
    OBJECT_NUMBER,
    OWNERS,
    OWNER_TYPE,
    WHOLESALE,
    LOAN_DATE,
    LOAN_DURATION,
    LOAN_NAME,
    LOAN_NUMBER,
    LOAN_OWNER_NAME,
    CHECK_THIS
]


def debug(*s):
    print(*s, file=sys.stderr)


USTUPKA_PRAV_TYPO = [
    'Соглашение о замене стороны ',
    'Соглашение о замене стороны в Договоре ',
    'Соглашение об уступке права требования и обязанностей ',
    'Соглашение об уступке прав требования по договору ',
    'Соглашение об уступке права требования ',
    'Соглашение об уступке прав требований ',
    'Соглашение об уступке прав требования ',
    'Соглашение об уступке права требований ',
    'Соглашение об уступке права требования ',
    'Соглашение об уступке права ',
    'Соглашение об уступке прав ',
    'Соглашение от уступке',
]


V_OSYASH_TYPO = [
    'В осях',
    'в рсях',
    'восх ',
    'восях ',
    '. в осях ',
    '.в осях ',
    '.в  осях',
    '. восях',
    'в ос. ',
    'в оясх ',
    '. в осях',
    'в осчях ',
    'в осяхз ',
    'в осяХ:',
    'оси6',
    'в лсях ',
    'оси6 ',
    'св осях ']

STROIT_OSI_TYPO = [
    'строит. оси:',
    'строительыне оси:',
    '. строительне оси',
    '. строительные оси ']


SECTION_TYPO = [
    'Секция ',
    'секц.',
    'с екция ',
    'снекция ',
    ' сек. ',
    ' скция ',
    ' екция ',
    'секйия ',
    'мекция ',
    'сецкия ',
    '.секция',
    ' секия ',
    'секуия ',
    'чекция ',
    'сееция ',
    'cекция',
    'сеция ',
    'скц. ',
    'секции',
    'СЕКЦ.',
    'секци я',
    'секци ', # this one should be last
    ]

CORPUS_TYPOS = [
    'корпус:',
    'копрус',
    'кор.',
    'коропус ',
    'корпсу ',
    'крпус ',
    'копус ',
    'корпу ',
    'корп ',
    'корпуса ',
    'кор.',
    'корп.',
    'Корп.',
    'коопус ',
    'коорпус',
    'копрус ',
    'корупс',
    'коп.',
    'Корпус ',
    'корус',
    'корпсус',
    ' орпус',
    'корапус ',
    'КОРПУС ',
    'кропус',
    'юлок ',
    'Блок No',
    'блок No',
    'блок №',
    '№ блока',
    '№блока-',
    '№блока ',
    '№Блока-',
    ' пус -',
    '. к. ',
    ', к.',
    'корпуc',
    'корпусс',
    'Блок ',
    'в корпусе ',
    'ьлок',
    'юлок',
    'дом №',
    'доме №',
    'дома №',
    'блое',
    'КОРП.',
    'вкорпус'
    ]

DOGOVOR_UCHASTIA_TYPO = [
    'Договор участия в долевос строительстве ',
    'Договор Участия в Долевом строительстве ',
    'Договор участия в долевом стротиельстве ',
    'Договор участия в длевом строительстве ',
    'Договор участия в долевом участии ',
    'Договор участия в долевом сироительстве ',
    'Договор участия в долевом строительств ',
    'Договор участия в долевом строительства ',
    'Договор долевого участия ',
    'Договоручастия в долевом строительстве ',
    'Договор участия с долевом строительстве ',
    'Договору частия в долевом строительстве'
    
]

ROOMS_NUMBER_TYPO = [
    'Кол-во комнат ',
    'кол-во комнат',
    'Кол-во ком.',
    'кол-во ком.',
    'Количество комнат '
]

KVARTIRA_TYPO = [
    'квартирва',
    'кв-ра ',
    #'кв. ',  # cant use this one because of same notation of area!
]

# not used yet
NEJILOE_TYPO = [
    'нежиллое ',
    'Нежилое ',
]

APPARTAMENT_TYPO = [
    'аппартамент',
    'апортамент',
]


def replaceTyposInAddress(data):
    data = " " + data.replace("  ", " ") + ";"
    # trash
    data = data.replace("номер 473 этажа: 1, ", "номер этажа: 1, номер объекта: 473, ")
    data = data.replace(": Нежилое помещение, студия, ", ": Нежилое помещение студия, ")
    data = data.replace("проектная (планиру6емая) площадь", "проектная (планируемая) площадь")
    data = data.replace(" площадь м/м:", " площадь ")
    data = data.replace(" площадь м/м ", " площадь ")
    data = data.replace(" площадь помещения ", " площадь ")
    data = data.replace(" площадь парк. места ", " площадь ")
    data = data.replace("3орпус", " 3 корпус ")
    data = data.replace("секция/Блок - 7/1,", "секция: 7, корпус: 1,")
    data = data.replace("секция объекта", " секция ")
    data = data.replace("корпус (секция", "корпус ,(секция")
    data = data.replace("подъезд/секция", "подъезд , секция")

    # patterns
    for to_replace in V_OSYASH_TYPO + STROIT_OSI_TYPO:
        data = data.replace(to_replace, " в осях: ")
    for to_replace in SECTION_TYPO:
        data = data.replace(to_replace, " секция ")
    for to_replace in CORPUS_TYPOS:
        data = data.replace(to_replace, " корпус ")
    for to_replace in ROOMS_NUMBER_TYPO:
        data = data.replace(to_replace, " количество комнат ")
    for to_replace in KVARTIRA_TYPO:
        data = data.replace(to_replace, " квартира ")
    for to_replace in APPARTAMENT_TYPO:
        data = data.replace(to_replace, "апартамент ")
  
    data = data.replace("в осях ", " в осях ")
    data = data.replace("Тип", "тип: ")
    data = data.replace("Тип:", "тип: ")
    data = data.replace("Местоположение:", "местоположение:")
    data = data.replace("Строительный адрес:", "строительный адрес:")
    data = data.replace(", условный номер ", ", номер объекта: ")
    data = data.replace(", этаж ", ", номер этажа: ")
    data = data.replace(" под. ", " подъезд ")
    data = data.replace("подънзд ", ", подъезд ")
    data = data.replace("/подъезд", ", подъезд ")

    return data


def replaceTyposInDduDesc(data):
    data = " " + data\
        .replace("  ", " ")\
        .replace("№ ","№")\
        .replace("№Договор", "")\
        .replace(" oт ", " от ") + " " # o is latin
    for to_replace in USTUPKA_PRAV_TYPO:
        data = data.replace(to_replace, "Соглашение об уступке ")
    for to_replace in DOGOVOR_UCHASTIA_TYPO:
        data = data.replace(to_replace, "Договор участия в долевом строительстве ")
    return data


def BOOL(f):
    try:
        return f()
    except Exception:
        return False



def extractDduDocDesc(desc):
    DATE_REGEXP = "[0-9]{2}\.[0-9]{2}\.[0-9]{4}"
    
    desc = replaceTyposInDduDesc(desc)
    result = dict()
    
    # Дата регистрации ДДУ
    search = re.compile(f"Договор участия в долевом строительстве[^;]* от ({DATE_REGEXP})").search(desc)
    search = search or re.compile(f"Договор.* долевого.* участия от ({DATE_REGEXP})").search(desc)
    search = search or re.compile(f"Договор участия.* от ({DATE_REGEXP})").search(desc)
    search = search or re.compile(f"Договор от ({DATE_REGEXP})").search(desc)
    search = search or re.compile(f"строительстве .*многоквартирного[^;,]* от ({DATE_REGEXP})").search(desc)
    search = search or re.compile(f"строительстве .* по адресу.* от ({DATE_REGEXP})").search(desc)
    search = search or re.compile(f"участия в долевом строительстве[^;,]* от ({DATE_REGEXP})").search(desc)
    search = search or re.compile(f"Дополнительное.* соглашение[^;,]* от ({DATE_REGEXP})").search(desc)
    search = search or re.compile(f"Соглашение об уступке[^;,]* от ({DATE_REGEXP})").search(desc)
    search = search or re.compile(f"Муниципальный контракт[^;,]* от ({DATE_REGEXP})").search(desc)
    result[DDU_DOC_DESC_DATE] = search and search.groups()[0] or ""
    
    # № ДДУ
    # todo: create additional complex regexp for ddu number (for space typos and so on)
    search = re.compile("Договор участия в долевом строительстве.* от[^№]*(№.*?)[;, ]").search(desc)
    search = search or re.compile("Договор участия в долевом строительстве.*(№.*?) от[^№]*[:, ]*").search(desc)
    search = search or re.compile("Договор участия.*(№.*?).* от[^№]*[:, ]*").search(desc)
    search = search or re.compile("Договор [^№]*(№.*?) .*участия").search(desc)
    search = search or re.compile("Договор от[^№]*(№.{2,25}?)[:, ]*").search(desc)
    search = search or re.compile("Дополнительное.* соглашение[^;,]* от[^№]*(№.{1,25}?)[:, ]*").search(desc)
    search = search or re.compile("строительстве.*от[^№]*(№.*?)[;, ]").search(desc)
    search = search or re.compile("Соглашение об уступке[^;,]* от[^№]*(№.*?)[;, ]").search(desc)
    search = search or re.compile("Муниципальный контракт[^;,]* от [^№]*(№.*?)[;, ]").search(desc)
    result[DDU_DOC_DESC_NUMBER] = search and search.groups()[0] or ""
    
    checkDate = re.compile(f"дата регистрации ({DATE_REGEXP}),").search(desc)
    checkDogovor = re.compile("Договор.* участия").search(desc)
    if checkDate and checkDogovor:
        result[DDU_DATE] = checkDate.groups()[0]

    desc = desc.lower()
    
    # Тип Договора
    if "уступ" in desc or "цесси" in desc:
        result[DOGOVOR_TYPE] = "Уступка"
    elif "замен" in desc or "перемен" in desc:
        result[DOGOVOR_TYPE] = "Замена стороны"
    elif "расторж" in desc:
        result[DOGOVOR_TYPE] = "Расторжение"
    elif "соглаш" in desc:
        result[DOGOVOR_TYPE] = "Доп. соглашение"
    elif 'муницип' in desc:
        result[DOGOVOR_TYPE] = "Муниципальный контракт"
        # todo: возможно заменить на "другое"
    else:
        result[DOGOVOR_TYPE] = "ДДУ"
        
    return result


def get_floor_simplified(floor):
    if floor == "" or floor == None:
        return None
    elif not floor.isdigit():
        return -1
    else:
        return int(floor)
    
def get_area_converted(area):
    area = area.replace(",", ".")
    try:
        result_area = float(area)
    except ValueError:
        result_area = None
    finally:
        return result_area

def get_initial_type(type):
    if type:
        return type.lower()
    else:
        return ""


# Object Type
def get_object_type(data, object_type = ""):
    result = dict()
    floor = get_floor_simplified(data[FLOOR])
    object_number = data[OBJECT_NUMBER].lower() or ""
    area = get_area_converted(data[AREA])
    object_and_adress = data[FULL_ADDRESS].lower()
    initial_type = get_initial_type(data[TYPE])
    possible_object_types = object_type or []
    # тип исх = initial_type
    # объект и адрес = object_and_adress
    result_type = None

    
    if initial_type == None and floor == None:
        result_type = "нд"
        
    elif "доу" in object_and_adress:
        result_type = "ДОУ"
        
    elif area and 8 <= area and area < 11:
        if "машин" in initial_type or "стоян" in initial_type:
            result_type = "машиноместо"
        else:
            result_type = "кладовая"
    
    elif area and 0 <= area and area < 8:
        result_type = "кладовая"
    
    # todo: проверить в исходных данных наличие нулевых площадей
    # нулевая площадь бывает только в крыму
    elif area and area == 0:
        if "машин" in initial_type or "стоян" in initial_type:
            result_type = "машиноместо"
        elif "кладов" in initial_type:
            result_type = "кладовая"
        else:
            result_type = "ПРОВЕРИТЬ!"
            
    elif area and area > 1000:
        result_type = "машиноместо"
        
    elif "кварт" in initial_type or "жилое" in initial_type and "нежилое" not in initial_type:
        if 'жилое' in possible_object_types:
            result_type = 'квартира'
        else:
            result_type = 'апартамент'
        
    elif "апарт" in initial_type:
        if 'апарт' in possible_object_types:
            result_type = 'апартамент'
        else:
            result_type = 'квартира'
    
    elif "комнат" in initial_type or "студ" in initial_type:
        if 'апарт' in possible_object_types and 'жилое' in possible_object_types:
            result_type = "квартира/апартамент"
        elif 'жилое' in possible_object_types:
            result_type = "квартира"
        elif 'апарт' in possible_object_types:
            result_type = "апартамент"
        else:
            result_type = "квартира/апартамент"

    elif "встроен" in initial_type or "офис" in initial_type:
        result_type = "нежилое"
        
    elif "машин" in initial_type or "стоян" in initial_type:
        if area and area > 31:
            if "-" in object_number:
                result_type = "машиноместо"
            else:
                if 'апарт' in possible_object_types:
                    result_type = "апартамент"
                else:
                    result_type = "ПРОВЕРИТЬ!"
                    
        elif area and area <= 16:
            result_type = "машиноместо"
        
        elif floor and floor < 0 or "подвал" in initial_type or "подзем" in initial_type or "цокол" in initial_type:
            result_type = "машиноместо"
        else:
            if 'апарт' in possible_object_types:
                result_type = 'апартамент'
            else:
                result_type = 'машиноместо'
            
    elif "доля" in object_and_adress or "доли" in object_and_adress:
        if area and area <= 31:
            result_type = "машиноместо"
        else:
            result_type = "ПРОВЕРИТЬ!"
    
    elif floor and floor > 9 and 'апарт' in possible_object_types:
        result_type = "апартамент"

    elif 'апартн' not in possible_object_types and "магаз" in object_and_adress or "офис" in object_and_adress:
        result_type = "нежилое"

    elif 'апарт' in possible_object_types:
        if "н" in object_number:
            result_type = "нежилое"
        elif area and area < 16:
            result_type = "машиноместо"
        elif floor and floor > 3:
            result_type = "апартамент"
        elif "апарт" in object_and_adress or "комнат" in object_and_adress or "студ" in object_and_adress:
            result_type = "апартамент"
        else:
            result_type = "ПРОВЕРИТЬ!"
            
    else:
        if area and area <= 31:
            result_type = "машиноместо"
        if "нежил" in initial_type or "помещ" in initial_type:
            if floor and floor <= 3:
                result_type = "нежилое"
            else:
                result_type = "ПРОВЕРИТЬ!"
        else:
            result_type = "ПРОВЕРИТЬ!"
            
    result[OBJECT_TYPE] = result_type
    
    return result
    

def wrap_data_like_value(s):
    tmp = re.sub("[.,/]$", "", s)
    return '="' + tmp + '"'


#разделитель
FMTS = dict(
    section="[\-\d./]*",
    sep="[;,)( ]+",
    eq="[.: №К\-]*"
)


def parseAddress(data):
    #data = data.lower()
    data = replaceTyposInAddress(data)
    result = dict()
    
    # Объект
    # это регулярка состоит из трех частей:
    # первая, необязательная, которая сожержит в основном описания.
    # вторая, обязательная, содержит непосредственно упоминание объекта.
    # третья, необязательная, работает аналогично первой и закрывает дыры, оставленные первыми двумя.
    # todo: упростить эту регулярку, переписав через оператор or
    tmp = re.compile("Объект долевого строительства[: ]*(.*?)[,;]").search(data)
    tmp = tmp and tmp.groups()[0].lower() or ""
    re_obj_pre = "((нежил|жил|.*комнат|офис|встр|\d.?к|\d|техн|служ).{0,30})"
    re_obj_body = "(квартира|помещение|апартамент|.*комнатная|.{0,30}место|студия|комнаты?)"
    re_obj_suf = "(.{0,30}(кладовая|стоянка|место|студия|нат[аы]|н[ои]е|квартира|апартаменты?))"
    tmp = re.compile(f"({re_obj_pre}?{re_obj_body}{re_obj_suf}?\)?)").search(tmp)
    result[TYPE] = tmp and tmp.groups()[0].lower() or ""
    
    # Floor
    # todo: все негативные значения привести к виду -5.5
    # todo: все буквенные значения привести к единому стандарту (заменять "цокольное" на "цокольный")
    re_floor = "[на урвьеотмк.]*(\-\d[,.]?\d+|\-?\d+)[-оимый]*"
    tmp = re.compile("(цоколь\w*|подвал\w*|подзем\w*)").search(data)
    tmp = tmp or re.compile(f"{re_floor}\s*этаж[е,.;]*").search(data)
    tmp = tmp or re.compile(f"номер этажа[: ]*{re_floor}").search(data)
    result[FLOOR] = tmp and tmp.groups()[0] or ""
    
    
    tmp = re.compile("строительный номер[: ]+(.+?),").search(data)
    tmp = tmp or re.compile("номер объекта[: ]*(.+?),").search(data)
    result[OBJECT_NUMBER] = tmp and wrap_data_like_value(tmp.groups()[0]) or ""

    # Area
    re_area_type = "(?:проектная|\(?планируемая\)?|общая|примерная)[\d]?"  # [\d]? is for typo
    re_area = "(\d{0,4}[,.]?\d{0,3}[,.]?\d{1,2})\s*кв[\. ]+м"
    tmp = re.compile(f"{re_area_type}\s*площадь[: -]+{re_area}").findall(data) or "no info"
    tmp = min(tmp)
    # typo: if area = object_number
    # object number is wrapped like this: ="{number}"
    if tmp == result[OBJECT_NUMBER][2:-1]:
        tmp = ""
    # convert ,8 to 0,8
    elif tmp.startswith(',') or tmp.startswith('.'):
        tmp = f"0{tmp}"
    # convert 2345 to 23,45 для квартира, апартамент, студия, [комнат], жилое
    elif tmp.isdigit() and float(tmp) > 1500 and (
    'квартир' in result[TYPE] or 'апарт' in result[TYPE] or
    'студ' in result[TYPE] or 'комнат' in result[TYPE] or
    'жилое' in result[TYPE]) and 'нежилое' not in result[TYPE]:
        tmp = str(float(tmp) / 100).replace(".",",") # area separator is coma
    result[AREA] = tmp or ""
    
    # Address
    tmp = re.compile("местоположение[: ]+(.*?)[.;]*$").search(data)
    tmp = tmp or re.compile("строительный адрес[: ]+(.*?)[.;]*$").search(data)
    # tmp = tmp or re.compile("уч. (.*?),кад.").search(data)
    result[ADRESS] = tmp and tmp.groups()[0] or ""
    
    # todo: разделить корпус и блок
    # todo: если корупса/блока нет, то берем дом
    # Corpus
    corpus_data = data.lower()
    tmp = re.compile("[^\d][;,]\s*([\d.]+)[- ]*корпус[;,.]?\s*[^\d]").search(corpus_data)
    tmp = tmp or re.compile("[, )\d]корпус(?!ами){eq}й?([а-я\d\./\-]+){sep}".format_map(FMTS)).search(corpus_data)
    tmp = tmp or re.compile("[\s\(]?блоки?{eq}([\d\.]+){sep}".format_map(FMTS)).search(corpus_data)
    tmp = tmp or re.compile(", (\d+?)[-й]* блок{sep}".format_map(FMTS)).search(corpus_data)
    tmp = tmp and tmp.groups()[0] or ""
    result[CORPUS] = wrap_data_like_value(tmp)

    # Секция
    section_data = data.lower()
    tmp = re.compile("секция{eq}({section})[\(\s]*секция[: -]*({section}){sep}".format_map(FMTS)).search(section_data)
    if tmp:
        result[SECTION] = tmp and wrap_data_like_value("{groups[0]} ({groups[1]})".format(groups=tmp.groups()))
    if not tmp:
        tmp = re.compile("секция{eq}([а-яА-Я\d]+){sep}([а-яА-Я\d]) *,".format_map(FMTS)).search(section_data)
        result[SECTION] = tmp and wrap_data_like_value("{groups[0]}, {groups[1]}".format(groups=tmp.groups()))
    if not tmp:
        tmp = re.compile("секция{eq}({section}?){eq}\(([а-яА-Я\d]?)\){sep}".format_map(FMTS)).search(section_data)
        result[SECTION] = tmp and wrap_data_like_value("{groups[0]}{groups[1]}".format(groups=tmp.groups()))
    if not tmp:
        tmp = re.compile("секция{eq}([^;, ]+?){sep}".format_map(FMTS)).search(section_data)
        tmp = tmp or re.compile("секция{eq}([^;, ]+?){sep}".format_map(FMTS)).search(section_data)
        tmp = tmp or re.compile("[, ]+({section}?) секция{sep}".format_map(FMTS)).search(section_data)
        tmp = tmp and tmp.groups()[0] or ""
        result[SECTION] = tmp and wrap_data_like_value(tmp)

    tmp = re.compile("подъезд{eq}([^,;() ]+?){sep}".format_map(FMTS)).search(data)
    tmp = tmp or re.compile("{sep}(\d+){eq}подъезд{sep}".format_map(FMTS)).search(data)
    tmp = tmp and tmp.groups()[0] or ""
    result[ENTRANCE] = tmp and re.sub("[.]$", "", tmp)
    
    # rooms
    rooms_re = re.compile("количество комнат{eq}(.+?){sep}".format_map(FMTS)).search(data)
    rooms_re = rooms_re or re.compile("тип{eq}(.+?){sep}".format_map(FMTS)).search(data)
    rooms_re = rooms_re or re.compile(", *(\d+?) *ком\.").search(data)
    if "студ" in data or "студ" in result[TYPE]:
        result[ROOMS] = "студия"
    elif "1" in result[TYPE] or "одно" in result[TYPE]:
        result[ROOMS] = "1"
    elif "2" in result[TYPE] or "дву" in result[TYPE]:
        result[ROOMS] = "2"
    elif "3" in result[TYPE] or "трех" in result[TYPE]:
        result[ROOMS] = "3"
    elif "4" in result[TYPE] or "четыре" in result[TYPE]:
        result[ROOMS] = "4"
    elif "5" in result[TYPE] or "пяти" in result[TYPE]:
        result[ROOMS] = "5"
    elif "6" in result[TYPE] or "шести" in result[TYPE]:
        result[ROOMS] = "6"
    elif "7" in result[TYPE] or "семи" in result[TYPE]:
        result[ROOMS] = "7"
    elif rooms_re:
        tmp = rooms_re.groups()[0]
        if tmp == "ст":
            result[ROOMS] = "студия"
        elif tmp[0].isdigit():
            result[ROOMS] = tmp[0]
        else:
            # if no rooms detected and not studio
            result[ROOMS] = ""
            #result[CHECK_THIS] = "комнаты"
    # else:
    #     result[ROOMS] = CHECK_THIS
    #     result[CHECK_THIS] = "комнаты"
    elif "нежил" in result[TYPE] or \
         "машин" in result[TYPE] or \
         "клад" in result[TYPE]:
        result[ROOMS] = ""
    elif "квартира" in result[TYPE]:
        # If kvartira without rooms
        # todo: check area and try to guess how many rooms
        result[ROOMS] = ""
    else:
        # prevent empty field, needed for later
        result[ROOMS] = ""
    
    # save audit info
    result[FULL_ADDRESS] = data
    return result




def is_person(owner):
    # check if owner is ФЛ or ЮЛ
    if "'" in owner or '"' in owner or 'акционерное' in owner or 'общество' in owner:
        return False
    return True


def getOwners(elem):
    owners = list()
    for t in elem.findall('Owner'):
        tag = t.find('Person') or \
              t.find('Organization') or \
              t.find('Governance')
        name = tag.findtext('Content')
        owners.append(name)
    persons = [owner for owner in owners if is_person(owner)]
    organisations = [owner for owner in owners if not is_person(owner)]
    result = persons or organisations
    return result


def has_no_data(root):
    notice = root.find('ReestrExtract').find('NoticelObj')
    if notice:
        return True
    return False


def first_pass_process(input_file, csv_writer):
    inputFile = input_file.file.read().decode().replace("\n", " ")
    filename = os.path.splitext(input_file.raw_filename)[0]
    
    parser = xml.etree.ElementTree.XMLParser(encoding="UTF-8")
    root = xml.etree.ElementTree.fromstring(inputFile, parser)
    
    if has_no_data(root):
        debug('{} has no data to parse'.format(filename))
        return
    
    cadastralNumber = root.find('ReestrExtract') \
                          .find('ExtractObjectRight') \
                          .find('ExtractObject') \
                          .find('ObjectRight') \
                          .find('ObjectDesc') \
                          .findtext('CadastralNumber') \
                          .strip()
    res1 = root.find('ReestrExtract').find('ExtractObjectRight')
    res2 = res1.find('ExtractObject').find('ObjectRight')
    elems = res2.findall('ShareHolding')
    
    object_custom_data = cd.get_data_by_cadastral_number(cadastralNumber)
    # debug("###")
    # debug(custom_data)

    ownersCount = dict()
    for elem in elems:
        for owner in getOwners(elem):
            ownersCount[owner] = ownersCount.get(owner, 0) + 1

    for elem in elems:
        
        res = dict()
        res[CADASTRAL_NUM] = cadastralNumber
        res[ID_DDU] = elem.findtext('ID_DDU')
        if not res[ID_DDU]:
            continue

        res[DDU_DESC] = (elem.findtext('DduDocDesc') or "")#.replace("\n", " ")
        res[DDU_DATE] = elem.findtext('DduDate')
        res[DDU_REG_NUMBER] = elem.findtext('DduRegNo')
        
        res.update(extractDduDocDesc(res[DDU_DESC]))

        data = None
        if len(elem.find('ShareHolding')) == 2:
            data = " ".join(elem.find('ShareHolding')[1].itertext())
        elif len(elem.find('ShareHolding').find('ShareObjects')) == 0:
            data = elem.find('ShareHolding').findtext('ShareObjects')
        else:
            data = " ".join(elem.find('ShareHolding').findtext('ShareObjects'))

        res.update(parseAddress(data))
        
        # owners
        owners = getOwners(elem)
        res[OWNERS] = ", ".join(owners)
        for owner in owners:
            res[WHOLESALE] = ownersCount[owner]
        
        # loan
        curr = elem.find("Encumbrance")
        if curr:
            res[LOAN_NUMBER] = curr.findtext("RegNumber")
            res[LOAN_NAME] = curr.findtext('Name')
            res[LOAN_DATE] = curr.findtext('RegDate')
            tmp = curr.find('Duration')
            if tmp:
                res[LOAN_DURATION] = tmp.findtext('Term')
            curr = elem.find("Encumbrance").find("Owner")
            if curr:
                if curr.find('Organization'):
                    res[LOAN_OWNER_NAME]= curr.find('Organization').findtext('Name')
        
        # Type_owner
        # if "'" in res[OWNERS] or '"' in res[OWNERS]:
        #     res[OWNER_TYPE] = "ЮЛ"
        # else:
        #     res[OWNER_TYPE] = "ФЛ"
        #debug(res[OWNERS])
        if is_person(res[OWNERS]):
            res[OWNER_TYPE] = "ФЛ"
        else:
            res[OWNER_TYPE] = "ЮЛ"
        
        res[SOURCE_FILE] = filename
        
        # set extra fields
        if 'object_type' in object_custom_data:
            possible_object_types = object_custom_data['object_type']
        else:
            possible_object_types = ""
            
        res.update(get_object_type(res, possible_object_types))
        
        # write custom data from xlsx
        if 'project_glorax_competitor' in object_custom_data:
            res[GLORAX_COMPETITOR] = object_custom_data['project_glorax_competitor']
        if 'project_name' in object_custom_data:
            res[PROJECT_NAME] = object_custom_data['project_name']
        
        # output all fields as csv row
        #csv_writer.writerow(res)
        
        csv_writer.append(res)
        

def get_rooms_for_same_area(data, cadastral_num, area):
    # same_cadastral_num = filter(lambda row: row[CADASTRAL_NUM] == cadastral_num, data)
    # same_area = filter(lambda row: row[AREA] == area, same_cadastral_num)
    same_cadastral_num = [row for row in data if row[CADASTRAL_NUM] == cadastral_num]
    same_area = [row for row in same_cadastral_num if row[AREA] == area]
    rooms_for_same_area = [i[ROOMS] for i in same_area]
    rooms_number = collections.Counter(rooms_for_same_area).most_common()
    if rooms_number:
        return rooms_number[0][0]


def second_pass_process(data):
    for row in data:
        if row[ROOMS] == '':
            #debug(f"empty rooms found in {row[ID_DDU]} in {row[SOURCE_FILE]}")
            rooms = get_rooms_for_same_area(data, row[CADASTRAL_NUM], row[AREA])
            if rooms:
                row[ROOMS] = rooms
                #debug(f"{row[ID_DDU]} in {row[SOURCE_FILE]} has {rooms} rooms\n\n")
    
    return data
    
def export_data_as_csv(main_data):
    output = StringIO()
    csv_writer = csv.DictWriter(output, fieldnames=ALL_KEYS)
    csv_writer.writeheader()
    if main_data:
        csv_writer.writerows(main_data)
    result_csv = output.getvalue()
    output.close()
    return result_csv


@route('/upload', method='POST')
def do_upload():
    try:
        print("BEGIN")

        uploads = request.files.getall('upload')
        
        if len(uploads) == 0:
            return "<h4>nothing to upload</h4></br><a href='/'>go back</a>"
        
        files_to_process = []
        main_data = []
        
        for upload in uploads:
            # todo: make a workaround about raw_filename and encode it correctly (utf-8 i think)
            # todo: transliterate filename to ascii
            name, ext = os.path.splitext(upload.filename)
            if ext == '.xlsx':
                cd.store_json_data(cd.load_xlsx_data(upload.file))
                debug(f'created new config from {upload.raw_filename}')
            else:
                files_to_process.append(upload)
                
        for file in files_to_process:
            first_pass_process(file, main_data)
            debug(f"file processed: {file.raw_filename}")

        main_data = second_pass_process(main_data)

        result_csv = export_data_as_csv(main_data)
        
        if len(files_to_process) > 1:
            name += "_multiple"
        
        print("END")
        headers = dict()
        headers['Content-Type'] = "text/csv;charset=utf-8"
        headers['Content-Disposition'] = 'attachment; filename=' + name + ".csv"
        return HTTPResponse(result_csv, **headers)
    except Exception as e:
        output = StringIO()
        traceback.print_exc(file=output)
        error_message = output.getvalue()
        output.close()
        return "<h2>" + str(e) + "</h2>" + error_message.replace("\n", "<BR />\n")


@route('/static/<filename:path>')
def send_static(filename):
    # use STATIC on deploy. Use LOCAL on development
    return static_file(filename, root=STATIC_DIR)


@route('/')
def index():
    # use ROOT on deploy. Use LOCAL on development
    return static_file("index.html", root=SETTINGS_DIR)


if __name__ == '__main__':
    run(host='localhost', port=PORT, reloader=True, debug=DEBUG_MODE)  # TODO: remove reloader on release

