# coding=utf-8

import sys
import re
import xml.etree.ElementTree
import csv
import os
import traceback
from bottle import route, run, template, post, request, HTTPResponse, static_file, redirect
from io import StringIO

# scp ~/impo.py root@138.197.223.128:/var/tmp/impo.py
# все area, floor, corpus, section, entrance с дефисом перед ним нужно преобразовать в без дефиса!

ROOT = '/var/tmp/polis/static/'
STATIC = 'var/tmp/static/'
LOCAL = 'static/'

# VARIABLE / table name # old name
ID_DDU = 'ID'  # 'ID_DDU',
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
NUM_UCHASTOK = '№ ЗУ'  # 'Num_Uchastok',
WHOLESALE = 'Кол-во купленных лотов'  # 'wholesale',
DDU_DESC = 'Название ДДУ' # 'DduDocDesc
FULL_ADDRESS = 'Объект и адрес' # full_address
CHECK_THIS = "проверить!" # check!

SOURCE_FILE = 'Объект'

PROJECT = 'Проект'
GLORAX_COMPETITOR = 'Конкурент проекта Glorax'


# all table headers in appearance order
ALL_KEYS = [
    ID_DDU,
    NUM_UCHASTOK,
    PROJECT,
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
    'Соглашение об уступке прав '
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
    'скц. ']

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
    'Договор долевого участия '
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
    'нежиллое',
]

APPARTAMENT_TYPO = [
    'аппартамент',
    'апортамент',
]


def replaceTyposInAddress(data):
    data = " " + data.replace("\n", " ").replace("  ", " ") + ";"
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
        data = data.replace(to_replace, "апартамент")
  
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
    data = " " + data.replace("\n", " ").replace("  ", " ") + " "
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


DATE_REGEXP = "[0-9]{2}\.[0-9]{2}\.[0-9]{4}"

def extractDduDocDesc(desc):
    desc = replaceTyposInDduDesc(desc)
    result = dict() # q: why not just [] ?
    # print("DESC = " + desc + "|")
    # parse ddu date
    search = re.compile("Договор участия в долевом строительстве[^;,]* oт ("+DATE_REGEXP+")").search(desc)
    search = search or re.compile("Договор.* долевого.* участия oт ("+DATE_REGEXP+")").search(desc)
    search = search or re.compile("строительстве .*многоквартирного[^;,]* oт ("+DATE_REGEXP+")").search(desc)
    search = search or re.compile("строительстве .* по адресу.* oт ("+DATE_REGEXP+")").search(desc)
    search = search or re.compile("участия в долевом строительстве[^;,]* oт ("+DATE_REGEXP+")").search(desc)
    search = search or re.compile("Дополнительное.* соглашение[^;,]* oт ("+DATE_REGEXP+")").search(desc)
    search = search or re.compile("Соглашение об уступке[^;,]* oт ("+DATE_REGEXP+")").search(desc)
    result[DDU_DOC_DESC_DATE] = search and search.groups()[0]
    # parse ddu number
    search = re.compile("Договор участия в долевом строительстве.* oт[^№]*(№.*?)[;, ]").search(desc)
    search = search or re.compile("Договор [^№]*(№.*?) .*участия").search(desc)
    search = search or re.compile("строительстве.*oт[^№]*(№.*?)[;, ]").search(desc)
    search = search or re.compile("Соглашение об уступке[^;,]* oт[^№]*(№.*?)[;, ]").search(desc)
    result[DDU_DOC_DESC_NUMBER] = search and search.groups()[0]
    checkDate = re.compile("дата регистрации ("+DATE_REGEXP+"),").search(desc)
    checkDogovor = re.compile("Договор.* участия").search(desc)
    if checkDate and checkDogovor:
        result[DDU_DATE] = checkDate.groups()[0] #q: what is .groups() ?

    desc = desc.lower()
    #
    # Type_dogovor
    # Определяем тип договора
    if "уступк" in desc:
        result[DOGOVOR_TYPE] = "Уступка"
    elif "замен" in desc:
        result[DOGOVOR_TYPE] = "Замена стороны"
    elif "растор" in desc:
        result[DOGOVOR_TYPE] = "Расторжение"
    else:
        result[DOGOVOR_TYPE] = "ДДУ"
    return result


# #TODO: check other fields before trimming area- it leads to bugs!
# def trim_area(value):
#     area = value.replace(",", ".")
#     if BOOL(lambda: float(area) > 1000):
#         return str(float(area) / 100.0).replace(".", ",")
#     else:
#         return value

# define type here
def parseExtraFields(data):
    result = dict()
    data[FLOOR] = data[FLOOR] or ""
    data[OBJECT_NUMBER] = data[OBJECT_NUMBER] or ""

    area_value = data[AREA].replace(",", ".")
    full_address = data[FULL_ADDRESS].lower()
    if "ДОУ" in full_address:
        #
        result[OBJECT_TYPE] = "ДОУ"
    elif "апарт" in full_address or \
         "аппарт" in full_address or \
         "апорт" in full_address or \
         "апарт" in data[TYPE] or \
         "нежил" in data[TYPE] and "комн" in data[TYPE] or \
         "нежил" in data[TYPE] and "студ" in data[TYPE] or \
         "нежил" in data[TYPE] and "комн" in full_address:
        #
        result[OBJECT_TYPE] = "апартамент"
    elif "квартир" in data[TYPE]:
        #
        result[OBJECT_TYPE] = "квартира"
    elif "машин" in full_address or \
         "машин" in data[TYPE] or \
         "стоян" in data[TYPE] or \
         "подвал" in data[FLOOR] or \
         "уров" in data[FLOOR]:
        #
        result[OBJECT_TYPE] = "машиноместо"
    elif "нежил" in data[TYPE] and BOOL(lambda: float(data[FLOOR]) >= 4) or \
         "нежил" in data[TYPE] and BOOL(lambda: float(data[FLOOR]) >= 2) and BOOL(lambda: float(area_value) < 70):
        #
        result[OBJECT_TYPE] = "апартамент"

    elif "кладов" in data[TYPE] or \
         BOOL(lambda: float(area_value) < 11):
        #
        result[OBJECT_TYPE] = "кладовая"
    elif "встроен" in full_address or \
         "офис" in full_address or \
         "встроен" in data[TYPE] or \
         "нежил" in data[TYPE] and data[FLOOR] == "1" or \
         "н" in data[OBJECT_NUMBER] and BOOL(lambda: float(data[FLOOR]) <= 3):
        #
        result[OBJECT_TYPE] = "нежилое"
    elif not data[TYPE] and not full_address or \
         not data[TYPE] and not area_value:
        #
        result[OBJECT_TYPE] = "нд"
    else:
        result[OBJECT_TYPE] = CHECK_THIS
        result[CHECK_THIS] = OBJECT_TYPE
    return result
    

def wrap_data_like_value(s):
    tmp = re.sub("[.,/]$", "", s)
    return '="' + tmp + '"'


#разделитель
FMTS = dict(
    #section="[\-\d./]+", # Oleg
    section="[\-\d./]*",  # Anton
    # sep="[;,)( ]+",  # Oleg
    sep="[;,)( ]+",  # Anton
    # eq="[: №-]*"  # Oleg
    eq="[.: №К\-]*"  # Anton
)


def parseAddress(data):
    data = replaceTyposInAddress(data)
    result = dict()
    
    tmp = re.compile("Объект долевого строительства[: ]*(.*?)[,;]").search(data)
    result[TYPE] = tmp and tmp.groups()[0].lower() or ""
    
    # Floor
    re_floor = "[на урвьеотмк.]*(\-\d[,.]?\d+|\-?\d+)[-оимый]*"
    tmp = re.compile("(цоколь\w*|подвал\w*|подзем\w*)").search(data)  # Anton
    tmp = tmp or re.compile("{floor}\s*этаж[е,.;]*".format(floor=re_floor)).search(data)  # Anton
    tmp = tmp or re.compile("номер этажа[: ]*{floor}".format(floor=re_floor)).search(data)  # Anton
    result[FLOOR] = tmp and tmp.groups()[0] or ""  # Oleg
    
    
    tmp = re.compile("строительный номер[: ]+(.+?),").search(data)
    tmp = tmp or re.compile("номер объекта[: ]*(.+?),").search(data)
    result[OBJECT_NUMBER] = tmp and wrap_data_like_value(tmp.groups()[0]) or ""

    # Area
    
    # Area v2.0
    # re_area = "(\d{1,4}[,.]?\d{0,3}[,.]?\d{0,2})"
    # tmp = re.compile("проектная.*планируемая.*площадь[: -]+{area}\s*кв\.м".format(area=re_area)).search(data)
    # tmp = tmp or re.compile("общая площадь[: -]+{area}\s*кв\.м".format(area=re_area)).search(data)
    # result[AREA] = tmp and tmp.groups()[0] or ""  # Anton
    
    # area v2.1 by Anton
    re_area_type = "(?:проектная|\(?планируемая\)?|общая|примерная)"
    re_area = "(\d{1,4}[,.]?\d{0,3}[,.]?\d{0,2})\s*кв[\. ]+м"
    tmp = re.compile("{type}\s*площадь[: -]+{area}".format(area=re_area, type=re_area_type)).findall(data) or "no info"
    result[AREA] = min(tmp) or ""
    
    # Adress
    tmp = re.compile("местоположение[: ]+(.*?)[.;]*$").search(data)
    tmp = tmp or re.compile("строительный адрес[: ]+(.*?)[.;]*$").search(data)
    # tmp = tmp or re.compile("уч. (.*?),кад.").search(data)
    result[ADRESS] = tmp and tmp.groups()[0] or ""
    
    # Corpus
    tmp = re.compile("[^\d][;.,][ ]{0,3}([\d.]+)[- ]*корпус[;,.]?[\s]+[^\d]").search(data)  # Anton
    tmp = tmp or re.compile(" корпус{eq}й?([\d\./\-]+){sep}".format_map(FMTS)).search(data)  # Anton
    tmp = tmp or re.compile("[\s\(]?блоки?{eq}([\d\.]+){sep}".format_map(FMTS)).search(data)  # Anton
    tmp = tmp or re.compile(", (\d+?)[-й]* блок{sep}".format_map(FMTS)).search(data)  # Oleg
    tmp = tmp and tmp.groups()[0] or ""
    result[CORPUS] = wrap_data_like_value(tmp)

    # Section
    tmp = re.compile("секция{eq}({section})[\(\s]*секция[: -]*({section}){sep}".format_map(FMTS)).search(data)
    if tmp:
        result[SECTION] = tmp and wrap_data_like_value("{groups[0]} ({groups[1]})".format(groups=tmp.groups()))
    if not tmp:
        tmp = re.compile("секция{eq}([а-яА-Я\d]+){sep}([а-яА-Я\d]) *,".format_map(FMTS)).search(data)
        result[SECTION] = tmp and wrap_data_like_value("{groups[0]}, {groups[1]}".format(groups=tmp.groups()))
    if not tmp:
        tmp = re.compile("секция{eq}({section}?){eq}\(([а-яА-Я\d]?)\){sep}".format_map(FMTS)).search(data)
        result[SECTION] = tmp and wrap_data_like_value("{groups[0]}{groups[1]}".format(groups=tmp.groups()))
    if not tmp:
        tmp = re.compile("секция{eq}([^;, ]+?){sep}".format_map(FMTS)).search(data)
        tmp = tmp or re.compile("секция{eq}([^;, ]+?){sep}".format_map(FMTS)).search(data)
        tmp = tmp or re.compile("[, ]+({section}?) секция{sep}".format_map(FMTS)).search(data)
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
    # debug(rooms_re)
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
            #result[ROOMS] = CHECK_THIS
            #result[CHECK_THIS] = "комнаты"
            pass
            
    # else:
    #     result[ROOMS] = CHECK_THIS
    #     result[CHECK_THIS] = "комнаты"
    elif "нежил" in result[TYPE] or \
         "машин" in result[TYPE] or \
         "клад" in result[TYPE]:
        pass
    elif "квартира" in result[TYPE]:
        # If kvartira wwithout rooms
        # debug("Something wrong with {}".format(result))
        pass
    
    # save audit info
    result[FULL_ADDRESS] = data
    return result




def is_person(owner):
    if "'" in owner or '"' in owner:
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


def process(input_file, spamwriter):
    inputFile = input_file.file
    filename = os.path.splitext(input_file.raw_filename)[0]
    
    parser = xml.etree.ElementTree.XMLParser(encoding="UTF-8")
    root = xml.etree.ElementTree.parse(inputFile, parser).getroot()
    
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

    ownersCount = dict()
    for elem in elems:
        for owner in getOwners(elem):
            ownersCount[owner] = ownersCount.get(owner, 0) + 1

    for elem in elems:
        res = dict()
        res[NUM_UCHASTOK] = cadastralNumber
        res[ID_DDU] = elem.findtext('ID_DDU')
        if not res[ID_DDU]:
            continue

        res[DDU_DESC] = (elem.findtext('DduDocDesc') or "").replace("\n", " ")
        res[DDU_DATE] = elem.findtext('DduDate')
        res[DDU_REG_NUMBER] = elem.findtext('DduRegNo')
        res.update(extractDduDocDesc(res[DDU_DESC]))

        data = None
        if len(elem.find('ShareHolding')) == 2:
            # res['regNum'] = elem.find('ShareHolding').findtext('ShareObjects')
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
        if "'" in res[OWNERS] or '"' in res[OWNERS]:
            res[OWNER_TYPE] = "ЮЛ"
        else:
            res[OWNER_TYPE] = "ФЛ"
        
        res[SOURCE_FILE] = filename
        
        # set extra fields
        res.update(parseExtraFields(res))
        
        # output all fields as csv row
        spamwriter.writerow(res)



@route('/upload', method='POST')
def do_upload():
    try:
        print("BEGIN")
        output = StringIO()
        spamwriter = csv.DictWriter(output, fieldnames=ALL_KEYS)
        spamwriter.writeheader()
        uploads = request.files.getall('upload')
        if len(uploads) == 0:
            return "<h4>nothing to upload</h4></br><a href='/'>go back</a>"
        for upload in uploads:
            # todo: make a workaround about raw_filename and encode it correctly (utf-8 i think)
            name, ext = os.path.splitext(upload.filename)
            # if ext not in ('.xml', ".html", ".htm"):
            #     return "<h2>Unable to upload a file: This file type is not supported.</h2>"
            #q: why this is removed? do we use non-xml files?
            process(upload, spamwriter)
            debug("{} processed".format(upload.raw_filename))
            #debug(upload.filename) #working, but cyrillic filenames is not working
        if len(uploads) > 1:
            name += "_multiple"
        result_csv = output.getvalue()
        output.close()
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
    return static_file(filename, root=LOCAL)


@route('/')
def index():
    # use ROOT on deploy. Use LOCAL on development
    return static_file("index.html", root=LOCAL)


if __name__ == '__main__':
    run(host='localhost', port=9999, reloader=True, debug=True)  # TODO: remove reloader on release

