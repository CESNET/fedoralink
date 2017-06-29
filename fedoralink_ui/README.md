# Fedoralink_ui
Modul Fedoralink_ui zjednodušuje prácu so šablónami.
Využíva views (zobrazenia) založené na triedach, ktorých použitie umožnuje
Django. Navyše ale umožnuje získanie šablón, ktoré sú uložené mimo kódu
aplikácie, vo Fedore.

Pre rôzne typy dát môžu byt v repozitári uložené rôzne šablóny, pre zobrazenie,
vytvorenie alebo editáciu dokumentu. Tiež šablóny, ktoré urcujú, ako
sa má dokument zobrazit vo výpise dokumentov v rámci kolekcie alebo pri
vyhladávaní. Pre jednotlivé typy polí môžu byt taktiež vytvorené a do Fedory
uložené rôzne šablóny. Ak nie je šablóna pre daný typ dokumentu uložená
ani vo Fedore, ani priamo v kóde aplikácie, Fedoralink_ui sa pokúsi zobrazit
aspon základné informácie s využitím predvolených šablón.

## generic_urls.py
Mapovanie generických URL adries
Aby nebolo nutné do aplikácie pridávat nové pravidlá pre URL adresy pri
každom vytvorení novej kolekcie, mám vytvorené pravidlá pre všeobecné URL
adresy a kód, ktorý zabezpecí zobrazenie dokumentov v správnej šablóne.
Funkcie v rámci súboru generic_urls.py mapujú URL adresy v aplikácii na
správne casti kódu pre zobrazenie, editáciu alebo vyhladávanie. Z URL adresy
zistíme ID dokumentu alebo kolekcie vo Fedore.
Vzory využívajúce regulárne výrazy pre URL adresy:

• ’^$’ - index

• r’^(?P<collection_id>[a-fA-F0-9_/-]*)?search(?P<parameters>.*)$’ - vyhladávanie
v rámci kolekcie

• ’^(?P<id>.*)/addSubcollection$’ - pridanie novej subkolekcie

• ’^(?P<id>.*)/add$’ - vytvorenie nového dokumentu ako potomka dokumentu
s daným ID

• ’^(?P<id>.*)/edit$’ - upravenie dokumentu s daným ID

• ’^(?P<id>.*)$’ - zobrazenie dokumentu s daným ID

Tieto generické URL adresy môžu byt v prípade potreby dalej rozšírené
v niektorej casti aplikácie.

## cachovanie sablon
Fedoralink_ui taktiež obsahuje kód potrebný pre cachovanie výsledných šablón
zložených zo šablón typu dokumentu a jednotlivých polí, kedže získanie
týchto údajov z Fedory je casovo nárocné. Pre získanie výslednej šablóny je
potrebné množstvo dopytov na Elasticsearch a následne na Fedoru, pocet dopytov
záleží hlavne na komplikovanosti modelu dokumentu.

O cachovanie sa stará trieda FedoraTemplateCache.

Viac informacii <https://github.com/kosto1992/dp>