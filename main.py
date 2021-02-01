from SPARQLWrapper import SPARQLWrapper, JSON
import numpy as np


print("Welcome to our quizz country game")

#idée: filtrer les pays avec moins de 1 millions habitants comme pays de départ, pour éviter les petites îles. 
possible_start_countries = #SPARQL

#index compris entre 0 et la taille de la liste filtrée
start_index = np.random.randint(len(possible_start_countries))
start_country = possible_start_countries[start_index]

#déterminer le final country
#calcul, pour chaque pays possible, la taille du chemin le plus court pour y aller. Mettre ça dans un dictionnaire {k: v avec k = countries, v = taille du chemin}
countries_path_sizes = {} #SPARQL

DIFFICULTY_LEVEL = 5 #sinon le jeu est trop long
filtered_countries_path_sizes = {k: v if v =< DIFFICULTY_LEVEL and v >= 2 for k, v in countries_path_sizes.items()}

end_index = np.random.randint(len(filtered_countries_path_sizes.keys()))
end_country = list(filtered_countries_path_size.keys())[end_index]



print(f"Your initial country is: {start_country}")
print(f"You have to go to: {end_country}\n Good luck!")

current_country = start_country

#créer un dictionnaire avec {k = type de questions, v = [requetes SPARQL correspondante fonction d'un pays, fontion solution correspondante]}
questions_dict = {"population": #SPARQL, en millions, à 10 près
    "une couleur du drapeau": #SPARQL,
    "capitale": #SPARQL,
    "place au classement PIB": #SPARQL}            # a 30 prèes

#définitions de 4 fonctions permettant de comparer la réponse à la question à la requête
def compare_pop(guess, true):
    return None

def compare_pib(guess, true):
    return None

def compare_cap(guess, true):
    return None

def compare_pib(guess, true):
    return None


while current_country != end_country:
    print(f"Your current country is {current_country}")
    #find actual neighbours
    neighbour_countries = #SPARQL

    guessed_country = input("Can you find a neighbour country?\n>>").lower() #no capital letters
    tries = 0
    while guessed_country not in neighbour_countries and tries < 3:
        guessed_country = input("No, try again\n>>").lower() #no capital letters
        tries += 1

    if tries == 3:
        print("Game over, you lost")
        break

    print("Good job! To get there please answer this question:")
    rand_question = list(question_dict.keys())[np.random.randint(len(questions_dict))]
    answer = input(rand_question+"\n>>")
    true = #SPARQL
    tries = 0
    while not questions_dict[rand_question][1](anwer, true) and tries < 3:
        answer = input("No, try again\n>>")
        tries += 1

    if tries == 3:
        print("Game over, you lost")
        break
    
    print("Good job! You now advanced to the next country!")



