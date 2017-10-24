# coding=utf-8

import sys
import re
import xml.etree.ElementTree
import csv
import os
import traceback
from bottle import route, run, template, post, request, HTTPResponse, static_file
from io import StringIO

# scp ~/impo.py root@138.197.223.128:/var/tmp/impo.py
# все area, floor, corpus, section, entrance с дефисом перед ним нужно преобразовать в без дефиса!

ROOT = '/var/tmp/polis/static/'
STATIC = 'var/tmp/static/'

# VARIABLE / table name # old name
ID_DDU_HEADER = 'ID'  # 'ID_DDU',
DDU_DOC_DESC_DATE_HEADER = 'Дата ДДУ'  # 'DduDocDesc_date',
DDU_DOC_DESC_NUMBER_HEADER = '№ ДДУ'  # 'DduDocDesc_number'
DDU_DATE_HEADER = 'Дата регистрации ДДУ'  # 'DduDate',
DDU_REG_NUMBER_HEADER = '№ регистрации ДДУ'  # 'DduRegNo',
DOGOVOR_TYPE_HEADER = 'Тип Договора'  # 'Type_dogovor',
ADRESS_HEADER = 'Адрес'  # 'address',
ROOMS_HEADER = 'Кол-во комнат'  # 'rooms'
AREA_HEADER = 'Площадь'  # 'area'
FLOOR_HEADER = 'Этаж'  # 'floor'
OBJECT_TYPE_HEADER = 'Тип помещения'  # 'type_object'
OBJECT_HEADER = '№ объекта'  # 'object'
TYPE_HEADER = 'Тип_исх'  # 'type',
CORPUS_HEADER = 'Корпус'  # 'corpus'
SECTION_HEADER = 'Секция'  # 'section'
ENTRANCE_HEADER = 'Подъезд'  # 'entrance'
OWNERS_HEADER = 'ФИО'  # 'owners',
OWNER_TYPE_HEADER = 'ФЛ/ЮЛ'  # 'Type_owner'
LOAN_DATE_HEADER = 'Дата регистрации залога'  # 'loanDate'
LOAN_DURATION_HEADER = 'Срок залога'  # 'loanDuration'
LOAN_NAME_HEADER = 'Тип залога'  # 'loanName'
LOAN_NUMBER_HEADER = '№ залога'  # 'loanNumber'
LOAN_OWNER_NAME_HEADER = 'Банк'  # 'loanOwnerName' # Переделываем в Банк, сейчас здесь ФИО дольщика
NUM_UCHASTOK_HEADER = '№ ЗУ'  # 'Num_Uchastok',
WHOLESALE_HEADER = 'Кол-во купленных лотов'  # 'wholesale',
DDU_DESC_HEADER = 'Название ДДУ' # 'DduDocDesc
FULL_ADDRESS_HEADER = 'Объект и адрес' # full_address
CHECK_THIS_FIELD = "проверить!" # check!

SOURCE_FILE_HEADER = 'исходный файл'

PROJECT_HEADER = ''
NEW_OBJECT_HEADER = ''
GLORAX_PROJECT_COMPETITOR_HEADER = ''


# all table headers in appearance order
ALL_KEYS = [
    ID_DDU_HEADER,
    DDU_DOC_DESC_DATE_HEADER,
    DDU_DOC_DESC_NUMBER_HEADER, #'DduDocDesc_number',
    DDU_DATE_HEADER,
    DDU_REG_NUMBER_HEADER,
    DOGOVOR_TYPE_HEADER,
    ADRESS_HEADER,
    ROOMS_HEADER,
    AREA_HEADER,
    FLOOR_HEADER,
    OBJECT_TYPE_HEADER,
    OBJECT_HEADER,
    TYPE_HEADER,
    CORPUS_HEADER,
    SECTION_HEADER,
    ENTRANCE_HEADER,
    OWNERS_HEADER,
    OWNER_TYPE_HEADER,
    LOAN_DATE_HEADER,
    LOAN_DURATION_HEADER,
    LOAN_NAME_HEADER,
    LOAN_NUMBER_HEADER,
    LOAN_OWNER_NAME_HEADER,
    DDU_DESC_HEADER,
    FULL_ADDRESS_HEADER,
    NUM_UCHASTOK_HEADER,
    WHOLESALE_HEADER,
    SOURCE_FILE_HEADER,
    CHECK_THIS_FIELD

]


def debug(*s):
    print(*s, file=sys.stderr)


USTUPKA_PRAV = [
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


V_OSYASH = [
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


STROIT_OSI = [
 'строит. оси:',
 'строительыне оси:',
 '. строительне оси',
 '. строительные оси ']


SECTION = [
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

CORPUS = [
    'корпус:',
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
    'коопус ',
    'копрус ',
    'коп.',
    'Корпус ',
    'корапус ',
    'КОРПУС ',
    'юлок ',
    'Блок No',
    'блок No',
    'блок №',
    '№ блока',
    '№блока-',
    '№блока ',
    ' пус -',
    '. к. ',
    'корпуc',
    'корпусс',
    'Блок ',
    'в корпусе ']

DOGOVOR_UCHASTIA = [
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

ROOMS_NUMBER = [
    'Кол-во комнат ',
    'кол-во комнат',
    'Кол-во ком.',
    'кол-во ком.',
    'Количество комнат '
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
    for to_replace in V_OSYASH + STROIT_OSI:
        data = data.replace(to_replace, " в осях: ")
    for to_replace in SECTION:
        data = data.replace(to_replace, " секция ")
    for to_replace in CORPUS:
        data = data.replace(to_replace, " корпус ")
    for to_replace in ROOMS_NUMBER:
        data = data.replace(to_replace, " количество комнат ")
  
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
    for to_replace in USTUPKA_PRAV:
        data = data.replace(to_replace, "Соглашение об уступке ")
    for to_replace in DOGOVOR_UCHASTIA:
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
    result[DDU_DOC_DESC_DATE_HEADER] = search and search.groups()[0]
    # parse ddu number
    search = re.compile("Договор участия в долевом строительстве.* oт[^№]*(№.*?)[;, ]").search(desc)
    search = search or re.compile("Договор [^№]*(№.*?) .*участия").search(desc)
    search = search or re.compile("строительстве.*oт[^№]*(№.*?)[;, ]").search(desc)
    search = search or re.compile("Соглашение об уступке[^;,]* oт[^№]*(№.*?)[;, ]").search(desc)
    result[DDU_DOC_DESC_NUMBER_HEADER] = search and search.groups()[0]
    checkDate = re.compile("дата регистрации ("+DATE_REGEXP+"),").search(desc)
    checkDogovor = re.compile("Договор.* участия").search(desc)
    if checkDate and checkDogovor:
        result[DDU_DATE_HEADER] = checkDate.groups()[0] #q: what is .groups() ?

    desc = desc.lower()
    #
    # Type_dogovor
    # Определяем тип договора
    if "уступк" in desc:
        result[DOGOVOR_TYPE_HEADER] = "Уступка"
    elif "замен" in desc:
        result[DOGOVOR_TYPE_HEADER] = "Замена стороны"
    elif "растор" in desc:
        result[DOGOVOR_TYPE_HEADER] = "Расторжение"
    else:
        result[DOGOVOR_TYPE_HEADER] = "ДДУ"
    return result


#TODO: check other fields before trimming area- it leads to bugs!
#362 line
def trim_area(value):
    area = value.replace(",", ".")
    if BOOL(lambda: float(area) > 1000):
        return str(float(area) / 100.0).replace(".", ",")
    else:
        return value


# main parse function
def parseExtraFields(data):
    result = dict()
    data[FLOOR_HEADER] = data[FLOOR_HEADER] or ""
    data[OBJECT_HEADER] = data[OBJECT_HEADER] or ""

    #
    area_value = data[AREA_HEADER].replace(",", ".")
    # type_object
    full_address = data[FULL_ADDRESS_HEADER].lower()
    if "ДОУ" in full_address:
        #
        result[OBJECT_TYPE_HEADER] = "ДОУ"
    elif "апарт" in full_address or \
         "аппарт" in full_address or \
         "апорт" in full_address or \
         "апарт" in data[TYPE_HEADER] or \
         "нежил" in data[TYPE_HEADER] and "комн" in data[TYPE_HEADER] or \
         "нежил" in data[TYPE_HEADER] and "студ" in data[TYPE_HEADER] or \
         "нежил" in data[TYPE_HEADER] and "комн" in full_address:
        #
        result[OBJECT_TYPE_HEADER] = "апартамент"
    elif "квартир" in data[TYPE_HEADER]:
        #
        result[OBJECT_TYPE_HEADER] = "квартира"
    elif "машин" in full_address or \
         "машин" in data[TYPE_HEADER] or \
         "стоян" in data[TYPE_HEADER] or \
         "подвал" in data[FLOOR_HEADER] or \
         "уров" in data[FLOOR_HEADER]:
        #
        result[OBJECT_TYPE_HEADER] = "машиноместо"
    elif "нежил" in data[TYPE_HEADER] and BOOL(lambda: float(data[FLOOR_HEADER]) >= 4) or \
         "нежил" in data[TYPE_HEADER] and BOOL(lambda: float(data[FLOOR_HEADER]) >= 2) and BOOL(lambda: float(area_value) <
                    70):
        #
        result[OBJECT_TYPE_HEADER] = "апартамент"

    elif "кладов" in data[TYPE_HEADER] or \
         BOOL(lambda: float(area_value) < 11):
        #
        result[OBJECT_TYPE_HEADER] = "кладовая"
    elif "встроен" in full_address or \
         "офис" in full_address or \
         "встроен" in data[TYPE_HEADER] or \
         "нежил" in data[TYPE_HEADER] and data[FLOOR_HEADER] == "1" or \
         "н" in data[OBJECT_HEADER] and BOOL(lambda: float(data[FLOOR_HEADER]) <= 3):
        #
        result[OBJECT_TYPE_HEADER] = "нежилое"
    elif not data[TYPE_HEADER] and not full_address or \
         not data[TYPE_HEADER] and not area_value:
        #
        result[OBJECT_TYPE_HEADER] = "нд"
    else:
        result[OBJECT_TYPE_HEADER] = CHECK_THIS_FIELD
        result[CHECK_THIS_FIELD] = "тип объекта"
    return result
    

def wrap_data_like_value(s):
    tmp = re.sub("[.,/]$", "", s)
    return '="' + tmp + '"'

#q: что это такое?
#разделитель
FMTS = dict(
    section="[\-\d./]+",
    sep="[;,)( ]+",
    eq="[: №-]*"
)


def parseAddress(data):
    data = replaceTyposInAddress(data)
    result = dict()
    
    tmp = re.compile("Объект долевого строительства[: ]*(.*?)[,;]").search(data)
    result[TYPE_HEADER] = tmp and tmp.groups()[0].lower() or ""
    
    tmp = re.compile("номер этажа[: ]*(\d*?),").search(data)
    tmp = tmp or re.compile("номер.* этажа:[: ]+(.*?),[^\d]").search(data)
    result[FLOOR_HEADER] = tmp and tmp.groups()[0] or ""
    
    tmp = re.compile("строительный номер[: ]+(.+?),").search(data)
    tmp = tmp or re.compile("номер объекта[: ]*(.+?),").search(data)
    result[OBJECT_HEADER] = tmp and wrap_data_like_value(tmp.groups()[0]) or ""
    
    tmp = re.compile("проектная.*планируемая.*площадь[: -]+(.*?) кв.м").search(data)
    tmp = tmp or re.compile("общая площадь[: -]+(.*?) кв.м").search(data)
    # res[AREA] = "=\"" + tmp and tmp.groups()[0] + "\""
    result[AREA_HEADER] = tmp and trim_area(tmp.groups()[0]) or ""
    
    tmp = re.compile("местоположение[: ]+(.*?)[.;]*$").search(data)
    tmp = tmp or re.compile("строительный адрес[: ]+(.*?)[.;]*$").search(data)
    # tmp = tmp or re.compile("уч. (.*?),кад.").search(data)
    result[ADRESS_HEADER] = tmp and tmp.groups()[0] or ""

    tmp = re.compile("[;., ]+([\d.]+)[- ]*корпус").search(data)
    tmp = tmp or re.compile("корпус{eq}(.+?){sep}".format_map(FMTS)).search(data)
    tmp = tmp or re.compile("блок{eq}([^,; ]+?){sep}".format_map(FMTS)).search(data)
    tmp = tmp or re.compile(", (\d+?) блок{sep}".format_map(FMTS)).search(data)
    # tmp = tmp or re.compile("блок[: ]*(.+?)$").search(data)
    tmp = tmp and tmp.groups()[0] or ""
    #debug(tmp)
    result[CORPUS_HEADER] = wrap_data_like_value(tmp)

    tmp = re.compile("секция{eq}({section})[\(\s]*секция[: -]*({section}){sep}".format_map(FMTS)).search(data)
    if tmp:
        result[SECTION_HEADER] = tmp and wrap_data_like_value("{groups[0]} ({groups[1]})".format(groups=tmp.groups()))
    if not tmp:
        tmp = re.compile("секция{eq}([а-яА-Я\d]+){sep}([а-яА-Я\d]) *,".format_map(FMTS)).search(data)
        result[SECTION_HEADER] = tmp and wrap_data_like_value("{groups[0]}, {groups[1]}".format(groups=tmp.groups()))
    if not tmp:
        tmp = re.compile("секция{eq}({section}?){eq}\(([а-яА-Я\d]?)\){sep}".format_map(FMTS)).search(data)
        result[SECTION_HEADER] = tmp and wrap_data_like_value("{groups[0]}{groups[1]}".format(groups=tmp.groups()))
    if not tmp:
        tmp = re.compile("секция{eq}([^;, ]+?){sep}".format_map(FMTS)).search(data)
        tmp = tmp or re.compile("секция{eq}([^;, ]+?){sep}".format_map(FMTS)).search(data)
        tmp = tmp or re.compile("[, ]+({section}?) секция{sep}".format_map(FMTS)).search(data)
        tmp = tmp and tmp.groups()[0] or ""
        result[SECTION_HEADER] = tmp and wrap_data_like_value(tmp)

    tmp = re.compile("подъезд{eq}([^,;() ]+?){sep}".format_map(FMTS)).search(data)
    tmp = tmp or re.compile("{sep}(\d+){eq}подъезд{sep}".format_map(FMTS)).search(data)
    tmp = tmp and tmp.groups()[0] or ""
    result[ENTRANCE_HEADER] = tmp and re.sub("[.]$", "", tmp)
    # rooms
    rooms_re = re.compile("количество комнат{eq}(.+?){sep}".format_map(FMTS)).search(data)
    rooms_re = rooms_re or re.compile("тип{eq}(.+?){sep}".format_map(FMTS)).search(data)
    rooms_re = rooms_re or re.compile(", *(\d+?) *ком\.").search(data)
    if "студ" in data or "студ" in result[TYPE_HEADER]:
        result[ROOMS_HEADER] = "студия"
    elif "1" in result[TYPE_HEADER] or "одно" in result[TYPE_HEADER]:
        result[ROOMS_HEADER] = "1"
    elif "2" in result[TYPE_HEADER] or "дву" in result[TYPE_HEADER]:
        result[ROOMS_HEADER] = "2"
    elif "3" in result[TYPE_HEADER] or "трех" in result[TYPE_HEADER]:
        result[ROOMS_HEADER] = "3"
    elif "4" in result[TYPE_HEADER] or "четыре" in result[TYPE_HEADER]:
        result[ROOMS_HEADER] = "4"
    elif "5" in result[TYPE_HEADER] or "пяти" in result[TYPE_HEADER]:
        result[ROOMS_HEADER] = "5"
    elif "6" in result[TYPE_HEADER] or "шести" in result[TYPE_HEADER]:
        result[ROOMS_HEADER] = "6"
    elif "7" in result[TYPE_HEADER] or "семи" in result[TYPE_HEADER]:
        result[ROOMS_HEADER] = "7"
    # восьмикомнатная квартира бывает?
    # TODO: уточнить у Полины нужно ли увеличивать количество комнат
    elif rooms_re:
        tmp = rooms_re.groups()[0]
        if tmp == "ст":
            result[ROOMS_HEADER] = "студия"
        elif tmp[0].isdigit():
            result[ROOMS_HEADER] = tmp[0]
        else:
            result[ROOMS_HEADER] = CHECK_THIS_FIELD
            result[CHECK_THIS_FIELD] = "комнаты"
    else:
        result[ROOMS_HEADER] = CHECK_THIS_FIELD
        result[CHECK_THIS_FIELD] = "комнаты"
    # save audit info
    result[FULL_ADDRESS_HEADER] = data
    return result




def check_if_owner_is_a_person(owner):
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
    # Bug workaround
    persons = [owner for owner in owners if check_if_owner_is_a_person(owner)]
    organisations = [owner for owner in owners if not check_if_owner_is_a_person(owner)]
    result = persons or organisations
    return result


def check_if_root_does_not_contain_data(root):

    notice = root.find('ReestrExtract').find('NoticelObj')
    if notice:
        return True
    return False
    
    
    

def process(input_file, spamwriter):
    
    inputFile = input_file.file
    filename = input_file.raw_filename

    parser = xml.etree.ElementTree.XMLParser(encoding="UTF-8")
    root = xml.etree.ElementTree.parse(inputFile, parser).getroot()
    
    #TODO: Добавить проверку, что в файле есть данные в прицнипе, например как в Покровский к 2

    if check_if_root_does_not_contain_data(root):
        debug('{} contain no data to parse'.format(filename))
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
    # elems = list(x for x in elems if x.findtext('ID_DDU') == '12511551035')

    ownersCount = dict()
    for elem in elems:
        for owner in getOwners(elem):
            ownersCount[owner] = ownersCount.get(owner, 0) + 1

    for elem in elems:
        res = dict()
        res[NUM_UCHASTOK_HEADER] = cadastralNumber

        # debug(xml.etree.ElementTree.tostring(elem, encoding="utf8").decode("utf8"))
        # return

        # debug('ID_DDU = ' + str(elem.findtext('ID_DDU')))

        # if elem.findtext('ID_DDU') == '3285443000':
        #     debug("TROLOLO:")
        #     debug(xml.etree.ElementTree.tostring(elem, encoding="utf8").decode("utf8"))

        # res['ID_DDU'] = elem.findtext('ID_DDU')
        # if not res['ID_DDU']:
        #     continue
        
        res[ID_DDU_HEADER] = elem.findtext('ID_DDU')
        if not res[ID_DDU_HEADER]:
            continue

        res[DDU_DESC_HEADER] = (elem.findtext('DduDocDesc') or "").replace("\n", " ")
        res[DDU_DATE_HEADER] = elem.findtext('DduDate')
        res[DDU_REG_NUMBER_HEADER] = elem.findtext('DduRegNo')
        res.update(extractDduDocDesc(res[DDU_DESC_HEADER]))

        data = None
        if len(elem.find('ShareHolding')) == 2:
            # res['regNum'] = elem.find('ShareHolding').findtext('ShareObjects')
            data = " ".join(elem.find('ShareHolding')[1].itertext())
        elif len(elem.find('ShareHolding').find('ShareObjects')) == 0:
            data = elem.find('ShareHolding').findtext('ShareObjects')
        else:
            data = " ".join(elem.find('ShareHolding').findtext('ShareObjects'))

        # debug("------")
        # ee = elem.find('Encumbrance').find("Owner")
        # tmp = xml.etree.ElementTree.tostring(ee, encoding="utf8").decode("utf8")
        # debug(tmp)
        # debug("----------")

        res.update(parseAddress(data))
        
        # owners
        owners = getOwners(elem)
        res[OWNERS_HEADER] = ", ".join(owners)
        for owner in owners:
            if ownersCount[owner] >= 7:
                # res[WHOLESALE_HEADER] = "оптовый"
                res[WHOLESALE_HEADER] = ownersCount[owner]
        
        # loan
        curr = elem.find("Encumbrance")
        if curr:
            # res['loanId'] = curr.findtext("ID_Record")
            res[LOAN_NUMBER_HEADER] = curr.findtext("RegNumber")
            # res['loanType'] = curr.findtext('Type')
            res[LOAN_NAME_HEADER] = curr.findtext('Name')
            res[LOAN_DATE_HEADER] = curr.findtext('RegDate')
            tmp = curr.find('Duration')
            if tmp:
                res[LOAN_DURATION_HEADER] = tmp.findtext('Term')
            curr = elem.find("Encumbrance").find("Owner")
            if curr:
                # res['loanOwnerId'] = curr.findtext('ID_Subject')
                # if curr.find('Organization'):
                    # res['loanOwnerName'] = curr.find('Organization').findtext('Name')
                    # res['loanOwnerINN'] = curr.find('Organization').findtext('INN')
                # change person to bank
                # if curr.find('Person'):
                #     res[LOAN_OWNER_NAME_HEADER] = curr.find('Person').findtext('Content')
                if curr.find('Organization'):
                    res[LOAN_OWNER_NAME_HEADER]= curr.find('Organization').findtext('Name')
        #
        # Type_owner
        if "'" in res[OWNERS_HEADER] or '"' in res[OWNERS_HEADER]:
            res[OWNER_TYPE_HEADER] = "ЮЛ"
        else:
            res[OWNER_TYPE_HEADER] = "ФЛ"
        
        res[SOURCE_FILE_HEADER] = filename
        
        # set extra fields
        res.update(parseExtraFields(res))
        # output all fields as csv row
        spamwriter.writerow(res)

        # if elem.findtext('ID_DDU') == '11085187031':
        #     debug("RESULT:")
        #     debug(res['address'])
        #     return


@route('/upload', method='POST')
def do_upload():
    try:
        print("BEGIN")
        output = StringIO()
        spamwriter = csv.DictWriter(output, fieldnames=ALL_KEYS)
        spamwriter.writeheader()
        uploads = request.files.getall('upload')
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
    return static_file(filename, root='static/') # TODO: change root to STATIC


@route('/')
def index():
    return static_file("index.html", root="static/") # TODO: change root to ROOT


if __name__ == '__main__':
    # spamwriter = csv.DictWriter(sys.stdout, fieldnames=ALL_KEYS)
    # spamwriter.writeheader()
    # process(sys.stdin, spamwriter)
    run(host='localhost', port=9999, reloader=True, debug=True)  # TODO: remove reloader on release

