from SPARQLWrapper import SPARQLWrapper, JSON
import random
import re
import unicodedata


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


print("Welcome to our quizz country game")

#idée: filtrer les pays avec moins de 1 millions habitants comme pays de départ, pour éviter les petites îles. 
start_country = get_random_country()


DIFFICULTY_LEVEL = 5 #sinon le jeu est trop long

possible_end_countries = get_k_neighbours(start_country["id"],DIFFICULTY_LEVEL,True)
end_country = random.choice(possible_end_countries)



print(f"Your initial country is: {start_country['label']}")
print(f"You have to go to: {end_country['label']}\n Good luck!")

current_country = start_country


def normalize_string(string):
    ascii_string = unicodedata.normalize('NFD', string).encode('ascii', 'ignore').decode()
    return re.sub('[^a-zA-Z]+', '', ascii_string).lower()

#définitions de 4 fonctions permettant de comparer la réponse à la question à la requête
def compare_pop(guess, country_data):
    guess_number = int(guess)
    if guess_number*0.5 < int(country_data["population"]) < guess_number*2:
        print(f"Close enough ! The exact response was {country_data['population']}")
        return True
    return False

def compare_lang(guess, country_data):
    return normalize_string(guess) in [ normalize_string(language) for language in country_data["langues"]]


def compare_cap(guess, country_data):
    return normalize_string(guess) ==  normalize_string(country_data["capitale"])

def compare_curr(guess, country_data):
    return normalize_string(guess) ==  normalize_string(country_data["monnaie"])

questions_dict = {"La population du pays ": compare_pop, 
    "Une langue officielle du pays ?": compare_lang,
    "La capitale du pays ?": compare_cap,
    "La monnaie officielle du pays ?": compare_curr
}


def compare_country_name(guess,countries):
    for country in countries:
        if normalize_string(guess) in [ normalize_string(label) for label in country["alternative_labels"]]:
            return country
    return False

while current_country != end_country:
    print(f"Your current country is {current_country['label']}")
    #find neighbours
    neighbour_countries = get_k_neighbours(current_country["id"],1)

    guessed_country = input("Can you find a neighbour country?\n>>") #no capital letters
    tries = 0
    guessed_country_match = compare_country_name(guessed_country, neighbour_countries)
    while not guessed_country_match and tries < 3:
        guessed_country = input("No, try again\n>>")
        guessed_country_match = compare_country_name(guessed_country, neighbour_countries)
        tries += 1

    if tries == 3:
        print("Game over, you lost")
        break

    current_country = guessed_country_match
    current_country_data = get_country_data(current_country["id"])

    print("Good job! To get there please answer this question:")
    rand_question = random.choice(list(questions_dict.keys()))
    answer = input(rand_question+"\n>>")
    tries = 0
    is_correct = questions_dict[rand_question](answer, current_country_data)
    while not is_correct and tries < 3:
        answer =input("No, try again\n>>")
        is_correct = questions_dict[rand_question](answer, current_country_data)
        tries += 1

    if tries == 3:
        print("Game over, you lost")
        break
    
    print(f"Good job! You now advanced to the next country!")
print(f"Well done! You reached your destination")



