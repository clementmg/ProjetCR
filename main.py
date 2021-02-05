from SPARQLWrapper import SPARQLWrapper, JSON
import random
import re
import unicodedata
import numpy as np


endpoint_url = "https://query.wikidata.org/sparql"

def format_wikidata_id(id):
    wd_id = id.split("/")[-1]
    return f"wd:{wd_id}"

def country_result_mapping(country_result):
    return [{
                "id":format_wikidata_id(country["country"]["value"]),
                "label":country["countryLabel"]["value"],
                "alternative_labels":[country["countryLabel"]["value"]] + country["altLabel_list"]["value"].split(";")
            } for country in country_result ]

def sparql_query(endpoint_url, query):
    user_agent = "CountryExplorer/0.0 (https://github.com/clementmg/ProjetCR)"
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return  sparql.query().convert()["results"]["bindings"]

#pas compris le k
def get_k_neighbours(country_id,k,filter_small=False):
    k_neighbour_relation = "/".join(["wdt:P47"]*k)
    query = f"""SELECT DISTINCT ?countryLabel ?country
                                (GROUP_CONCAT(DISTINCT(?altLabel); separator = ";") AS ?altLabel_list)  
                WHERE {{
                    ?country wdt:P31 wd:Q3624078;
                             wdt:P1082 ?population;
                             {k_neighbour_relation} {country_id}.
                    OPTIONAL {{ ?country  skos:altLabel ?altLabel. FILTER (lang(?altLabel) = "fr") }}
                    { "FILTER(?population > 1000000)" if not filter_small else ""}
                    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr". }}
                }}
                GROUP BY ?countryLabel ?country
            """
    return country_result_mapping(sparql_query(endpoint_url,query))


#Mettre une min pop en paramètres
def get_random_country():
    query = """SELECT DISTINCT ?countryLabel ?country WHERE {   
                ?country wdt:P31 wd:Q3624078;
                         wdt:P1082 ?population.
                FILTER(?population > 1000000)
                SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
            }"""
    results = sparql_query(endpoint_url,query)
    country = random.choice(results)
    return{"id":format_wikidata_id(country["country"]["value"]), "label":country["countryLabel"]["value"]}

def get_country_data(country_id):
    query = f"""SELECT DISTINCT ?population  ?capitaleLabel ?monnaieLabel 
                                (GROUP_CONCAT(DISTINCT(?langueLabel); separator = ";") AS ?langue_list)
                WHERE {{   
                    {country_id} wdt:P31 wd:Q3624078;
                                wdt:P1082 ?population;
                                wdt:P36 ?capitale;
                                wdt:P37 ?langue;
                                wdt:P38 ?monnaie.
                    ?langue rdfs:label ?langueLabel. FILTER(langmatches(lang(?langueLabel), 'fr')).
                    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr". }}
                }}
                GROUP BY ?population ?capitaleLabel ?monnaieLabel 
            """
    country_data = sparql_query(endpoint_url,query)[0]
    return {
            "population":country_data["population"]["value"],
            "capitale": country_data["capitaleLabel"]["value"],
            "monnaie": country_data["monnaieLabel"]["value"],
            "langues": country_data["langue_list"]["value"].split(";"),
        }


print("Bienvenue dans notre jeu de Quizz sur les pays du monde!")

#idée: filtrer les pays avec moins de 1 millions habitants comme pays de départ, pour éviter les petites îles. 
start_country = get_random_country()


DIFFICULTY_LEVEL = 4 #sinon le jeu est trop long

#choisir un pays du même continent? si possible
possible_end_countries = get_k_neighbours(start_country["id"],DIFFICULTY_LEVEL,True)
end_country = random.choice(possible_end_countries)



print(f"Votre pays de départ est: {start_country['label']}")
print(f"Votre pays dans lequel vous devez vous rendre: {end_country['label']}\n Bonne chance!")

current_country = start_country


def normalize_string(string):
    ascii_string = unicodedata.normalize('NFD', string).encode('ascii', 'ignore').decode()
    return re.sub('[^a-zA-Z]+', '', ascii_string).lower()

#définitions de 4 fonctions permettant de comparer la réponse à la question à la requête
# def compare_pop(guess, country_data, lb=0.6, ub=1.8):
#     guess_number = int(guess)
#     if guess_number*lb < int(country_data["population"] / 1000000) < guess_number*ub:
#         print(f"Presque ! La réponse exacte était: {np.round(country_data['population'] / 1000000, 2)} millions, mais on vous l'accorde.")
#         return True
#     return False


# def compare_lang(guess, country_data):
#     return normalize_string(guess) in [ normalize_string(language) for language in country_data["langues"]]


# def compare_cap(guess, country_data):
#     return normalize_string(guess) ==  normalize_string(country_data["capitale"])

# def compare_curr(guess, country_data):
#     return normalize_string(guess) ==  normalize_string(country_data["monnaie"])


def get_pop(country_data):
    return np.round((int(country_data["population"]) / 1000000), 2)


def get_lang(country_data):
    return [language for language in country_data["langues"]]


def get_cap(country_data):
    return country_data["capitale"]

def get_curr(country_data):
    return country_data["monnaie"]

def evaluate_pop(guess, answer, lb=0.6, ub=1.8):
    guess_number = int(guess)
    if guess_number*lb < answer < guess_number*ub:
        print(f"Presque ! La réponse exacte était: {answer} millions, mais on vous l'accorde.")
        return True
    return False    

def evaluate_str(guess, answer):
    return normalize_string(guess) == normalize_string(answer)


def evaluate_lang(guess, answers):
    return normalize_string(guess) in [ normalize_string(language) for language in answers]


questions_dict = {"La population du pays, en millions? ": [get_pop, evaluate_pop],
    "Une langue officielle du pays ?": [get_lang, evaluate_lang],
    "La capitale du pays ?": [get_cap, evaluate_str],
    "La monnaie officielle du pays ?": [get_curr, evaluate_str]
}


def compare_country_name(guess, countries):
    for country in countries:
        if normalize_string(guess) in [ normalize_string(label) for label in country["alternative_labels"]]:
            return country
    return False

N_count = 0
while current_country["label"] != end_country["label"]:
    N_count += 1
    print('--------')
    print(f"\nVous vous trouvez actuellement dans ce pays : {current_country['label']}")
    print('--------')
    #trouver les pays voisins
    neighbour_countries = get_k_neighbours(current_country["id"],1)

    guessed_country = input("\nPouvez vous trouver un pays voisin? Si vous avez besoin d'aide, répondez 'non'\n>>") 
    if guessed_country == "non":
        print("\nVoici la liste des pays voisins\n")
        for country in neighbour_countries:
            print(country["label"])
        guessed_country = input("\nChoisissez-en, mais le bon cette fois. Qu'on ne vous y reprenne plus:\n>>")
    tries = 0
    guessed_country_match = compare_country_name(guessed_country, neighbour_countries)
    while not guessed_country_match and tries < 3:
        guessed_country = input("\nNon, essayez encore\n>>")
        guessed_country_match = compare_country_name(guessed_country, neighbour_countries)
        if not guessed_country_match:
            tries += 1

    if tries == 3:
        print("\nGame over, C'est perdu")
        break

    current_country = guessed_country_match
    current_country_data = get_country_data(current_country["id"])

    print("\nBravo! Pour vous y rendre, répondez à cette question:")
    rand_question = random.choice(list(questions_dict.keys()))
    answer = input(rand_question+"\nSi vous souhaitez un choix multiple, répondez qcm"+"\n>>")
    correct_answer = questions_dict[rand_question][0](current_country_data)
    if answer == "qcm":
        print("\nVoici la liste des réponses possibles. On espère que cela vous aide. Alors?\n")

        possible_responses = [questions_dict[rand_question][0](get_country_data(country["id"])) for country in neighbour_countries]
        if type(possible_responses[0]) == list: #Alors il faut flatten, il s'agit des langues
            possible_responses = [val for sublist in possible_responses for val in sublist]

        possible_responses = list(set(possible_responses))
        random.shuffle(possible_responses)
        for response in possible_responses:
            print(response)

        answer = input("\n"+rand_question+"\n>>")

    tries = 0

    is_correct = questions_dict[rand_question][1](answer, correct_answer)
    while not is_correct and tries < 3:
        answer = input("\nNon, essayez encore\n>>")
        is_correct = questions_dict[rand_question][1](answer, correct_answer)
        if not is_correct:
            tries += 1

    if tries == 3:
        print("Game over, you lost")
        break
    
    print(f"\nBravo! Vous avancez donc d'une case!")

if current_country["label"] != end_country["label"]:
    print(f"Félicitations! Vous avez atteint votre destination en {N_count} coups")



