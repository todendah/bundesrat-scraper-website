from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory

from .views import index,loadJSON #Needs __init__.py in same folder, else error when executing tests
from .models import Json, JsonCountyPDFLinks
import json


class Tests(TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.currentSession = 992 #Last BR Session Number, needed for many tests

    def test_DB_setup(self):
        # Create an instance of a GET request.
        request = self.factory.get("/")
        request.user = AnonymousUser()

        # Test my_view() as if it were deployed at /customer/details
        response = index(request)

        # Check DB Tables
        self.assertEqual(Json.objects.all().count(), 16+1) #16 rows for counties, 1 for bundesrat
        self.assertEqual(JsonCountyPDFLinks.objects.all().count(), 16) 
        #Test all rows are present
        #Website would crash if some table is malformed, so only test some parts
        row = Json.objects.get(county="baden_wuerttemberg")
        rowJSON = json.loads(row.json)
        self.assertEqual(len(rowJSON), self.currentSession - 916 + 1)

        row = Json.objects.get(county="bundesrat")
        rowJSON = json.loads(row.json)
        self.assertEqual(len(rowJSON), self.currentSession -910 + 1) #992-910 + 1 = 83 different sessions

    def testIndexSite(self):
        # Create an instance of a GET request.
        request = self.factory.get("/")
        request.user = AnonymousUser()

        # Test my_view() as if it were deployed at /customer/details
        response = index(request)
        self.assertEqual(response.status_code, 200)

        indexHTML = response.content.decode()
        self.assertTrue("Suchen Sie hier nach dem konkreten Abstimmungsverhalten jedes Bundeslandes im Bundesrat" in indexHTML)
        self.assertTrue('<a href="https://www.bundesrat.de/SharedDocs/TO/{}/to-node.html">hier</a>'.format(self.currentSession) in indexHTML) #Check right link to latest session

    #TODO Nur einmal DB Init
    def testSearchResultSuccess(self):
        #TODO Test Search Bar
        request = self.factory.get("/loadJSON?sessionNumber=992&topNumber=4") #Latest TOP with 3 bars none zero and 1 bar empty
        request.user = AnonymousUser()

        # Test my_view() as if it were deployed at /customer/details
        response = loadJSON(request)
        self.assertEqual(response.status_code, 200)

        searchHTML = response.content.decode()

        #Test meta data present and correct
        self.assertTrue("TOP 992/4" in searchHTML)
        self.assertTrue("Titel: 320/20 Gesetz zur Verbesserung der Hilfen für Familien bei Adoption (Adoptionshilfe-Gesetz)" in searchHTML)
        self.assertTrue("Kategorie: Zustimmungsbedürftiges Gesetz" in searchHTML)
        self.assertTrue("Beschlusstenor im Bundesrat: Versagung der Zustimmung" in searchHTML)

        #Check some links and texts
        self.assertTrue('<a href="https://landesvertretung-brandenburg.de/wp-content/uploads/992_Abstimmungverhalten-BB.pdf">Brandenburg</a>' in searchHTML) #Check link to PDF present
        self.assertTrue('Haltung SL: Enthaltung zum Anrufungsgrund und Zustimmung zum Gesetz' in searchHTML) #Check Text present
        self.assertTrue('<th>Ablehnung</th>' in searchHTML) #Check opinion parsed correctly


