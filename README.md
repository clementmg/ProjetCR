# ProjetCR

## Install

`pip install -r requirements.txt`

## Run

Run `python main.py` and follow ingame instructions.

## Documentation

### Sparql queries

The first query we use is this one to get all countries with more than 1M inhabitants, so that we can select one randomly.
```sparql
SELECT DISTINCT ?countryLabel ?country WHERE {   
                ?country wdt:P31 wd:Q3624078;
                         wdt:P1082 ?population.
                FILTER(?population > 1000000)
                SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
```

The `wdt:P31 wd:Q3624078` properties means `is a sovereign state` which is the wikidata property thqt correspond best to the meaning of country that we understand, contrary as wikidata country property.


The second query we use to query the data of a country for the questions, where country_id is the country we want to fetch its data.

```sparql
SELECT DISTINCT ?population  ?capitaleLabel ?monnaieLabel 
                (GROUP_CONCAT(DISTINCT(?langueLabel); separator = ";") AS ?langue_list)
                WHERE    
                    {country_id} wdt:P31 wd:Q3624078;
                                wdt:P1082 ?population;
                                wdt:P36 ?capitale;
                                wdt:P37 ?langue;
                                wdt:P38 ?monnaie.
                    ?langue rdfs:label ?langueLabel. FILTER(langmatches(lang(?langueLabel), 'fr')).
                    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr". }}
                
                GROUP BY ?population ?capitaleLabel ?monnaieLabel 
```

We select the population, the capital city, the currency and the languages of the country, that we get with the `wdt:P1082`, `wdt:P36`, `wdt:P38` and `wdt:P37` relations.
We use the group_concat aggregation to get the list of languages for a country as they are multiple languages for a country.
We also use the  `wikibase:label` to get the labels of the variables directly, except for the languages, where we need to specifically query the label as the label service is not working with the group_concat aggregation.


The last query we use, is the one to query the neighbours of a country. This query takes a parameter to be able to query the countries that are k-country distant from the given country. We will use this query with 2 values for k : 1 and DIFFICULTY_LEVEL. We use k=1 to query the neighbours of a country that the player can access, and we use k=DIFFICULTY_LEVEL to query a goal country which is to a given distance of the initial country (even if it can be less).
We also have a conditional filter on wether we want to select all countries or only the one with more than 1M inhabitants, as we want a goal country with at least 1M inhabitants, but we want to select every neighbour countries when the player moves from one country to another.

We also use the `skos:altLabel` relation to get all the possible aliases of a country name, to allow the a flexible experience for the player, so that the game accepts multiple responses for a country name.

The queries look like this, where `k_distant_neighbour_relation` is `wdt:P47`, the wikidata bordering relation, for k=1, or `wdt:P47/wdt:P47/wdt:P47/wdt:P47` for k=4.

```sparql
SELECT DISTINCT ?countryLabel ?country
                                (GROUP_CONCAT(DISTINCT(?altLabel); separator = ";") AS ?altLabel_list)  
                WHERE {{
                    ?country wdt:P31 wd:Q3624078;
                             wdt:P1082 ?population;
                             {k_distant_neighbour_relation} {country_id}.
                    OPTIONAL {{ ?country  skos:altLabel ?altLabel. FILTER (lang(?altLabel) = "fr") }}
                    { "FILTER(?population > 1000000)" if not filter_small else ""}
                    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr". }}
                }}
                GROUP BY ?countryLabel ?country
```