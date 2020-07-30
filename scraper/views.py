from django.shortcuts import render
from django.http import HttpResponse

from .models import Mytest, Number, Json, JsonCountyPDFLinks
from django.views.decorators.csrf import csrf_exempt

import requests #Load JSONs if necessary
import json #Str -> JSON,
import re #For senats text replacement

def index(request):
    jsons = Json.objects.all()
    if len(jsons) == 0: #Load 
        loadJSONsInDB()

    jsonsPDFLinks = JsonCountyPDFLinks.objects.all()
    if len(jsonsPDFLinks) == 0: #Load 
        loadJSONsPDFLinksInDB()

    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)
    allTOPs = []
    allSessionNumbers = list(map(lambda session: session["number"], brJSON))
    return render(request, "index.html", {"sessionNumbers": allSessionNumbers})

@csrf_exempt  #TODO Remove annotation
def update_counter(request):
    cou = Mytest()
    cou.save()

    cou.save()
    cous = Mytest.objects.all()
    message = 'update successful {}x'.format("test")
    return render(request, "mycounter.html", {"counters": cous})

def sendMethod(request):
    numbers = Number.objects.all()
    if len(numbers) == 0:
        number = Number()
        number.save()
    number = Number.objects.first() #get (maybe new) number, only one number in DB
    oldNumber = number.number

    number.number = request.POST["textfield"]
    number.save()
    return render(request, "number.html", {"oldNumber": oldNumber, "newNumber": number.number, "IO": request.POST["textfield"] })

def tef(request=None):
    pass

#TODO Calculate real votes for selected Session+TOP Pair
def showDiagram(request):
    return render(request, "diagram.html", {"yes": 10, "no": 5, "out": 3})

def getTopsAJAX(request):
    jsons = Json.objects.all() #TODO Check if any, don't load all (Multiple methods here use this)
    if len(jsons) == 0: #Load 
        loadJSONsInDB()
    sessionNumber = int(request.GET['sNumber'])
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)
    for session in brJSON:
        if int(session['number']) == sessionNumber:
            allTOPs = list(map(lambda top: {'name': top["number"]}, session["tops"]))
            allTOPs.reverse() #TOP 1 at the start afterwards
            break
    return HttpResponse(json.dumps(allTOPs), content_type='application/json') #Doesn't recognize without content_type

def loadJSONsInDB():
    counties = [
            "baden_wuerttemberg",
            "bayern",
            "berlin",
            "brandenburg", 
            "bremen",
            "hamburg",
            "hessen",
            "mecklenburg_vorpommern",
            "niedersachsen",
            "nordrhein_westfalen",
            "rheinland_pfalz",
            "saarland",
            "sachsen",
            "sachsen_anhalt",
            "schleswig_holstein",
            "thueringen",
            ]
    jsonUrl = "https://raw.githubusercontent.com/okfde/bundesrat-scraper/master/{}/session_tops.json"
    for county in counties:
        countyJsonUrl = jsonUrl.format(county)
        response = requests.get(countyJsonUrl)
        if response.status_code != 200:
            raise Exception('{} not found'.format(countyJsonUrl))
        #TODO rename county attribute
        countyDBRow = Json(county = county, json = response.content.decode()) #If not decode bytearraw, then problem when storing (bytearray) string and rereading it to json
        countyDBRow.save()
    
    #bundesrat folder with Session->TOPs mapping extra
    brUrl = "https://raw.githubusercontent.com/okfde/bundesrat-scraper/master/bundesrat/sessions.json"
    #TODO remove double code
    response = requests.get(brUrl)
    if response.status_code != 200:
        raise Exception('{} not found'.format(brUrl))
    #TODO rename county attribute
    brDBRow = Json(county = "bundesrat", json = response.content.decode()) #If not decode bytearraw, then problem when storing (bytearray) string and rereading it to json
    brDBRow.save()

#TODO Merge with loadJSONsInDB, but no bundesrat folder used here
def loadJSONsPDFLinksInDB():
    counties = [
            "baden_wuerttemberg",
            "bayern",
            "berlin",
            "brandenburg", 
            "bremen",
            "hamburg",
            "hessen",
            "mecklenburg_vorpommern",
            "niedersachsen",
            "nordrhein_westfalen",
            "rheinland_pfalz",
            "saarland",
            "sachsen",
            "sachsen_anhalt",
            "schleswig_holstein",
            "thueringen",
            ]
    jsonUrl = "https://raw.githubusercontent.com/okfde/bundesrat-scraper/master/{}/session_urls.json"
    for county in counties:
        countyJsonUrl = jsonUrl.format(county)
        response = requests.get(countyJsonUrl)
        if response.status_code != 200:
            raise Exception('{} not found'.format(countyJsonUrl))
        #TODO rename county attribute
        countyDBRow = JsonCountyPDFLinks(county = county, json = response.content.decode()) #If not decode bytearraw, then problem when storing (bytearray) string and rereading it to json
        countyDBRow.save()

def loadJSON(request):
    jsons = Json.objects.all()
    if len(jsons) == 0: #Load 
        loadJSONsInDB()
    jsonsPDFLinks = JsonCountyPDFLinks.objects.all()
    if len(jsonsPDFLinks) == 0: #Load 
        loadJSONsPDFLinksInDB()
    sessionNumber = int(request.POST["sessionNumber"])
    topNumber = request.POST["topNumber"] #TODO Is Subpart + Number , should rename JS Parameter
    jsons = Json.objects.all()
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)
    sessionURL = ""
    allTOPs = []
    for session in brJSON:
        if int(session['number']) == sessionNumber:
            sessionURL = session['url']
            for top in session["tops"]:
                if top["number"] == topNumber:
                    topTitle = top['title']
                    topCategory = top.get('law_category', 'Ohne Kategorie')#Zustimmungsbedürftig/Einspruchsgesetz/None
                    topBeschlussTenor = top.get('beschlusstenor', 'Kein Beschlusstenor') #Zustimmung/Versagung der Zustimmung/keine Einberufung des Vermittlungsausschusses/...
            break

    countySenatTextAndOpinionAndPDFLink = {}
    allRows = Json.objects.all()
    for row in allRows:
        if row.county == "bundesrat": #TODO besser
            continue #already processed
        countyName = row.county
        countyJSON = json.loads(row.json)
        countySessionTextsJSON = countyJSON.get(str(sessionNumber), {}) #{} is default, but doesn't like keyword "default"
        countySessionTOPTextsJSON = countySessionTextsJSON.get(str(topNumber), {}) #{} is default, but doesn't like keyword "default"
        countySessionTOPSenatsText = countySessionTOPTextsJSON.get("senat", "Keinen Text in JSON gefunden")
        opinion = extractOpinionSenatsText(countySessionTOPSenatsText)

        pdfLinksAbstimmungsverhaltenRow = JsonCountyPDFLinks.objects.get(county=countyName)
        pdfLinksAbstimmungsverhaltenJSON = json.loads(pdfLinksAbstimmungsverhaltenRow.json)
        pdfLinkCountyCurrentSession = pdfLinksAbstimmungsverhaltenJSON.get(str(sessionNumber), "") #No pdf for county and session ? -> empty link

        countySenatTextAndOpinionAndPDFLink[row.county] = (countySessionTOPSenatsText, opinion, pdfLinkCountyCurrentSession)

    return render(request, "json.html", {"sessionNumber": sessionNumber, "sessionURL": sessionURL,  "top": topNumber, "topTitle" : topTitle, "topCategory": topCategory, "topTenor": topBeschlussTenor, "countiesTextsAndOpinionsAndPDFLinks": countySenatTextAndOpinionAndPDFLink})

#In: some senats text
#Out: Return YES/NO/ABSTENTION if matches keywords TODO Is there an extra/third "Anruf VA" opinion?
#Out: Else return original text
def extractOpinionSenatsText(senatsText):

    #Order important! "keine Zustimmung"(NO) before "Zustimmung" (YES)
    text = senatsText
    text = replaceStringIfSomeMatchWith(text, ["keine zustimmung", "ablehnung", "keine Unterstützung der Ausschussempfehlungen"], "NO" )
    text = replaceStringIfSomeMatchWith(text, ["enthaltung", "Kenntnisnahme der Ausschussverweisung"], "ABSTENTION" ) #"Enthaltung zur Zustimmung zum Gesetz" exists, so check before YES
    text = replaceStringIfSomeMatchWith(text, 
            [   "keine einwendungen", 
                "hat der Verordnung zugestimmt",
                "stimmte dem Gesetz zu",
                "Anrufung des Vermittlungsausschusses nicht verlangt",
                "Einer Überweisung an die Ausschüsse wird nicht widersprochen", #(BB - 949/42) -> Das ist für Gesetzes*entwürfe*, Ausschuss noch vor eigentlicher Gesetzeswahl (Ausschuss != Verfassungsausschuss)  -> YES
                "Keine Anrufung Vermittlungsausschuss", #(SA - 977/1) -> Nur bei Einspruchsgesetzen -> YES
                "Keine Anrufung des Vermittlungsausschusses",
                "Keine Anrufung VA",
                "Zu den Gesetzen einen Antrag auf Anrufung des Vermittlungsausschusses nicht zu stellen",
                "Die Einberufung des Vermittlungsausschusses wurde nicht verlangt",
                "Dem Gesetz wurde einstimmig zugestimmt",
                "einen Antrag auf Anrufung des Vermittlungsausschusses nicht zu stellen",
                "zustimmung",
                "Freie Hand", #Bremen 988 1a
                "Fassen der Entschließung nach Maßgaben unterstützt",
                "mit den Stimmen Hamburgs zugestimmt",

                "Verweisung in die Ausschüsse", #Next ones exist only for "Gesetzesentwürfe" (e.g. 981 18), not for "Gesetzesbeschlüsse", "Ausschuss" != "Vermittlungsausschuss
                "Ausschussüberweisung",
                "Überweisung an die Ausschüsse",
                "Überweisung in die Ausschüsse",
                "Ausschussüberweisung",
                "Die Vorlage wurde an die Ausschüsse zur Beratung überwiesen",

                "Einbringung", #For "Gesetzesanträge" (985 15)
            ], "YES" )

    return text

#In: String to match against (Will all be lower cased in the end)
#In: List of strings/words to match
#In: Replacement string if some match in string
#Out: replacement if match, else original
def replaceStringIfSomeMatchWith(inString, toMatchList, replacement):

    toMatchListLC = map(str.lower, toMatchList)

    #Create big regex or with from toMatchList
    regexStr = ".*(" + "|".join(toMatchListLC) + ")"
    regex = re.compile(regexStr)

    if regex.match(inString.lower()): #Find any string from toMatchListLC -> replace
        return replacement
    return inString #Nothing Found, so return original string
