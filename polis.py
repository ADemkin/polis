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

DDU_DESC_FIELD = 'DduDocDesc'
FULL_ADDRESS_FIELD = 'full_address'
CHECK_THIS_FIELD = "проверить!"


ALL_KEYS = [
    'ID_DDU',
    'DduDocDesc_date',
    'DduDocDesc_number',
    'DduDate',
    'DduRegNo',
    'Type_dogovor',
    'address',
    'rooms',
    'area',
    'floor',
    'type_object',
    'object',
    'type',
    'corpus',
    'section',
    'entrance',
    'owners',
    'Type_owner',
    'loanDate',
    'loanDuration',
    'loanName',
    'loanNumber',
    'loanOwnerName',
    DDU_DESC_FIELD,
    FULL_ADDRESS_FIELD,
    'Num_Uchastok',
    'wholesale',
    'check!'
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
    result['DduDocDesc_date'] = search and search.groups()[0]
    # parse ddu number
    search = re.compile("Договор участия в долевом строительстве.* oт[^№]*(№.*?)[;, ]").search(desc)
    search = search or re.compile("Договор [^№]*(№.*?) .*участия").search(desc)
    search = search or re.compile("строительстве.*oт[^№]*(№.*?)[;, ]").search(desc)
    search = search or re.compile("Соглашение об уступке[^;,]* oт[^№]*(№.*?)[;, ]").search(desc)
    result['DduDocDesc_number'] = search and search.groups()[0]
    checkDate = re.compile("дата регистрации ("+DATE_REGEXP+"),").search(desc)
    checkDogovor = re.compile("Договор.* участия").search(desc)
    if checkDate and checkDogovor:
        result['DduDate'] = checkDate.groups()[0] #q: what is .groups() ?

    desc = desc.lower()
    #
    # Type_dogovor
    # Определяем тип договора
    if "уступк" in desc:
        result['Type_dogovor'] = "Уступка"
    elif "замен" in desc:
        result['Type_dogovor'] = "Замена стороны"
    elif "растор" in desc:
        result['Type_dogovor'] = "Расторжение"
    else:
        result['Type_dogovor'] = "ДДУ"
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
    data['floor'] = data['floor'] or ""
    data['object'] = data['object'] or ""

    #
    area_value = data['area'].replace(",", ".")
    # type_object
    full_address = data[FULL_ADDRESS_FIELD].lower()
    if "ДОУ" in full_address:
        #
        result['type_object'] = "ДОУ"
    elif "апарт" in full_address or \
         "аппарт" in full_address or \
         "апорт" in full_address or \
         "апарт" in data['type'] or \
         "нежил" in data['type'] and "комн" in data['type'] or \
         "нежил" in data['type'] and "студ" in data['type'] or \
         "нежил" in data['type'] and "комн" in full_address:
        #
        result['type_object'] = "апартамент"
    elif "квартир" in data['type']:
        #
        result['type_object'] = "квартира"
    elif "машин" in full_address or \
         "машин" in data['type'] or \
         "стоян" in data['type'] or \
         "подвал" in data['floor'] or \
         "уров" in data['floor']:
        #
        result['type_object'] = "машиноместо"
    elif "нежил" in data['type'] and BOOL(lambda: float(data['floor']) >= 4) or \
         "нежил" in data['type'] and BOOL(lambda: float(data['floor']) >= 2) and BOOL(lambda: float(area_value) < 70):
        #
        result['type_object'] = "апартамент"

    elif "кладов" in data['type'] or \
         BOOL(lambda: float(area_value) < 11):
        #
        result['type_object'] = "кладовая"
    elif "встроен" in full_address or \
         "офис" in full_address or \
         "встроен" in data['type'] or \
         "нежил" in data['type'] and data['floor'] == "1" or \
         "н" in data['object'] and BOOL(lambda: float(data['floor']) <= 3):
        #
        result['type_object'] = "нежилое"
    elif not data['type'] and not full_address or \
         not data['type'] and not area_value:
        #
        result['type_object'] = "нд"
    else:
        result['type_object'] = CHECK_THIS_FIELD
        result['check!'] = "type_object"
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
    result["type"] = tmp and tmp.groups()[0].lower() or ""
    tmp = re.compile("номер этажа[: ]*(\d*?),").search(data)
    tmp = tmp or re.compile("номер.* этажа:[: ]+(.*?),[^\d]").search(data)
    result["floor"] = tmp and tmp.groups()[0] or ""
    tmp = re.compile("строительный номер[: ]+(.+?),").search(data)
    tmp = tmp or re.compile("номер объекта[: ]*(.+?),").search(data)
    result["object"] = tmp and wrap_data_like_value(tmp.groups()[0]) or ""
    tmp = re.compile("проектная.*планируемая.*площадь[: -]+(.*?) кв.м").search(data)
    tmp = tmp or re.compile("общая площадь[: -]+(.*?) кв.м").search(data)
    # res["area"] = "=\"" + tmp and tmp.groups()[0] + "\""
    result["area"] = tmp and trim_area(tmp.groups()[0]) or ""
    tmp = re.compile("местоположение[: ]+(.*?)[.;]*$").search(data)
    tmp = tmp or re.compile("строительный адрес[: ]+(.*?)[.;]*$").search(data)
    # tmp = tmp or re.compile("уч. (.*?),кад.").search(data)
    result["address"] = tmp and tmp.groups()[0] or ""

    tmp = re.compile("[;., ]+([\d.]+)[- ]*корпус").search(data)
    tmp = tmp or re.compile("корпус{eq}(.+?){sep}".format_map(FMTS)).search(data)
    tmp = tmp or re.compile("блок{eq}([^,; ]+?){sep}".format_map(FMTS)).search(data)
    tmp = tmp or re.compile(", (\d+?) блок{sep}".format_map(FMTS)).search(data)
    # tmp = tmp or re.compile("блок[: ]*(.+?)$").search(data)
    tmp = tmp and tmp.groups()[0] or ""
    result["corpus"] = wrap_data_like_value(tmp)

    tmp = re.compile("секция{eq}({section})[\(\s]*секция[: -]*({section}){sep}".format_map(FMTS)).search(data)
    if tmp:
        result["section"] = tmp and wrap_data_like_value("{groups[0]} ({groups[1]})".format(groups=tmp.groups()))
    if not tmp:
        tmp = re.compile("секция{eq}([а-яА-Я\d]+){sep}([а-яА-Я\d]) *,".format_map(FMTS)).search(data)
        result["section"] = tmp and wrap_data_like_value("{groups[0]}, {groups[1]}".format(groups=tmp.groups()))
    if not tmp:
        tmp = re.compile("секция{eq}({section}?){eq}\(([а-яА-Я\d]?)\){sep}".format_map(FMTS)).search(data)
        result["section"] = tmp and wrap_data_like_value("{groups[0]}{groups[1]}".format(groups=tmp.groups()))
    if not tmp:
        tmp = re.compile("секция{eq}([^;, ]+?){sep}".format_map(FMTS)).search(data)
        tmp = tmp or re.compile("секция{eq}([^;, ]+?){sep}".format_map(FMTS)).search(data)
        tmp = tmp or re.compile("[, ]+({section}?) секция{sep}".format_map(FMTS)).search(data)
        tmp = tmp and tmp.groups()[0] or ""
        result["section"] = tmp and wrap_data_like_value(tmp)

    tmp = re.compile("подъезд{eq}([^,;() ]+?){sep}".format_map(FMTS)).search(data)
    tmp = tmp or re.compile("{sep}(\d+){eq}подъезд{sep}".format_map(FMTS)).search(data)
    tmp = tmp and tmp.groups()[0] or ""
    result["entrance"] = tmp and re.sub("[.]$", "", tmp)
    # rooms
    rooms_re = re.compile("количество комнат{eq}(.+?){sep}".format_map(FMTS)).search(data)
    rooms_re = rooms_re or re.compile("тип{eq}(.+?){sep}".format_map(FMTS)).search(data)
    rooms_re = rooms_re or re.compile(", *(\d+?) *ком\.").search(data)
    if "студ" in data or "студ" in result['type']:
        result['rooms'] = "студия"
    elif "1" in result['type'] or "одно" in result['type']:
        result['rooms'] = "1"
    elif "2" in result['type'] or "дву" in result['type']:
        result['rooms'] = "2"
    elif "3" in result['type'] or "трех" in result['type']:
        result['rooms'] = "3"
    elif "4" in result['type'] or "четыре" in result['type']:
        result['rooms'] = "4"
    elif "5" in result['type'] or "пяти" in result['type']:
        result['rooms'] = "5"
    elif "6" in result['type'] or "шести" in result['type']:
        result['rooms'] = "6"
    elif "7" in result['type'] or "семи" in result['type']:
        result['rooms'] = "7"
    # восьмикомнатная квартира бывает?
    #TODO: уточнить у Полины нужно ли увеличивать количество комнат
    elif rooms_re:
        tmp = rooms_re.groups()[0]
        if tmp == "ст":
            result['rooms'] = "студия"
        elif tmp[0].isdigit():
            result['rooms'] = tmp[0]
        else:
            result['rooms'] = CHECK_THIS_FIELD
            result['check!'] = "rooms"
    else:
        result['rooms'] = CHECK_THIS_FIELD
        result['check!'] = "rooms"
    # save audit info
    result[FULL_ADDRESS_FIELD] = data
    return result


def getOwners(elem):
    owners = list()
    for t in elem.findall('Owner'):
        tag = t.find('Person') or \
              t.find('Organization') or \
              t.find('Governance')
        owners.append(tag.findtext('Content'))
    return owners


def process(inputFile, spamwriter):
    parser = xml.etree.ElementTree.XMLParser(encoding="UTF-8")
    root = xml.etree.ElementTree.parse(inputFile, parser).getroot()
    cadastralNumber = root.find('ReestrExtract'
        ).find('ExtractObjectRight'
        ).find('ExtractObject'
        ).find('ObjectRight'
        ).find('ObjectDesc'
        ).findtext('CadastralNumber').strip()
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
        res['Num_Uchastok'] = cadastralNumber

        # debug(xml.etree.ElementTree.tostring(elem, encoding="utf8").decode("utf8"))
        # return

        # debug('ID_DDU = ' + str(elem.findtext('ID_DDU')))

        # if elem.findtext('ID_DDU') == '3285443000':
        #     debug("TROLOLO:")
        #     debug(xml.etree.ElementTree.tostring(elem, encoding="utf8").decode("utf8"))

        res['ID_DDU'] = elem.findtext('ID_DDU')
        if not res['ID_DDU']:
            continue

        res[DDU_DESC_FIELD] = (elem.findtext('DduDocDesc') or "").replace("\n", " ")
        res['DduDate'] = elem.findtext('DduDate')
        res['DduRegNo'] = elem.findtext('DduRegNo')
        res.update(extractDduDocDesc(res[DDU_DESC_FIELD]))

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
        res['owners'] = ", ".join(owners)
        for owner in owners:
            if ownersCount[owner] >= 7:
                res['wholesale'] = "оптовый"
        # loan
        curr = elem.find("Encumbrance")
        if curr:
            # res['loanId'] = curr.findtext("ID_Record")
            res['loanNumber'] = curr.findtext("RegNumber")
            # res['loanType'] = curr.findtext('Type')
            res['loanName'] = curr.findtext('Name')
            res['loanDate'] = curr.findtext('RegDate')
            tmp = curr.find('Duration')
            if tmp:
                res['loanDuration'] = tmp.findtext('Term')
            curr = elem.find("Encumbrance").find("Owner")
            if curr:
                # res['loanOwnerId'] = curr.findtext('ID_Subject')
                # if curr.find('Organization'):
                    # res['loanOwnerName'] = curr.find('Organization').findtext('Name')
                    # res['loanOwnerINN'] = curr.find('Organization').findtext('INN')
                if curr.find('Person'):
                    res['loanOwnerName'] = curr.find('Person').findtext('Content')
        #
        # Type_owner
        if "'" in res['owners'] or '"' in res['owners']:
            res['Type_owner'] = "ЮЛ"
        else:
            res['Type_owner'] = "ФЛ"

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
            name, ext = os.path.splitext(upload.filename)
            # if ext not in ('.xml', ".html", ".htm"):
            #     return "<h2>Unable to upload a file: This file type is not supported.</h2>"
            #q: why this is removed? do we use non-xml files?
            process(upload.file, spamwriter)
        if len(uploads) > 1:
            name += "_multiple"
        res = output.getvalue()
        output.close()
        print("END")
        headers = dict()
        headers['Content-Type'] = "text/csv;charset=utf-8"
        headers['Content-Disposition'] = 'attachment; filename=' + name + ".csv"
        return HTTPResponse(res, **headers)
    except Exception as e:
        output = StringIO()
        traceback.print_exc(file=output)
        error_message = output.getvalue()
        output.close()
        return "<h2>" + str(e) + "</h2>" + error_message.replace("\n", "<BR />\n")


@route('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root='var/tmp/static/')


@route('/')
def index():
    return static_file("index.html", root="var/tmp/static/")
    #return "<h1>index page</h1>"


if __name__ == '__main__':
    # spamwriter = csv.DictWriter(sys.stdout, fieldnames=ALL_KEYS)
    # spamwriter.writeheader()
    # process(sys.stdin, spamwriter)
    run(host='localhost', port=9999)

