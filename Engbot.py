import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import logging
import time

WORD_COUNT = 10000

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logging.info("Starting the scraping process using BeautifulSoup with custom headers and timeout.")

# Define your topics (units)
topics = [
    "Preserving Our Heritage",
    "Education Options for School-Leavers",
    "Becoming Independent",
    "Social Issues",
    "The Ecosystem"
]

# Common stop words to filter out candidate words.
stop_words = {"our", "for", "the", "and", "of", "to", "in", "a", "an", "options", "becoming"}

# Hard-coded candidate words for each topic.
candidate_words = {
    "Preserving Our Heritage": [
        "old", "past", "tradition", "culture", "custom", "legacy", "memory",
        "history", "heritage", "old-fashioned", "ancestry", "roots", "folklore",
        "relic", "museum", "antique", "preservation", "conservation", "time", "story"
    ],
    "Education Options for School-Leavers": [
        "school", "college", "job", "training", "internship", "trade", "study",
        "courses", "classes", "program", "career", "skills", "diploma", "degree",
        "exam", "workshop", "tutoring", "mentorship", "online", "campus"
    ],
    "Becoming Independent": [
        "alone", "self", "free", "grown-up", "adult", "responsible", "choice",
        "decide", "self-help", "standalone", "budget", "work", "money", "planning",
        "cooking", "cleaning", "driving", "renting", "saving", "support"
    ],
    "Social Issues": [
        "poverty", "racism", "unfairness", "crime", "homeless", "health", "drugs",
        "violence", "discrimination", "rights", "hunger", "waste", "education", "family",
        "income", "gap", "abuse", "bullying", "justice", "community"
    ],
    "The Ecosystem": [
        "nature", "plants", "animals", "water", "air", "earth", "forest", "trees",
        "rivers", "pollution", "soil", "climate", "wildlife", "ocean", "grass",
        "ecosystem", "habitat", "species", "weather", "recycle"
    ]
}

used_words = set()       # To avoid duplicates.
quiz_items = []          # To store quiz question items.
thesaurus_items = []     # To store synonyms/antonyms data.
definitions_items = []   # To store definitions data.

# Set headers and timeout for all requests.
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MyScraper/1.0)"}
TIMEOUT = 10

def scrape_cambridge_info(word):
    """
    Fetches related words and definitions from Cambridge Dictionary for the given word.
    - Related words are extracted from <div> elements whose class contains "daccord_lb".
    - Definitions are extracted from <div> elements with exact class "def ddef_d db".
    Returns (related_words, definitions) as lists.
    """
    logging.info(f"Scraping Cambridge info for word: {word}")
    related = []
    definitions = []
    url = f"https://dictionary.cambridge.org/dictionary/english/{word}?q={word}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            logging.warning(f"Failed to load page for {word}: {response.status_code}")
            return related, definitions
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for {word}: {e}")
        return related, definitions

    soup = BeautifulSoup(response.text, "html.parser")

    # Fetch related words.
    container = soup.find("div", class_="daccord_lb")
    if container:
        li_elements = container.find_all("li")
        logging.debug(f"Found {len(li_elements)} <li> elements for related words of '{word}'.")
        for li in li_elements:
            a_elem = li.find("a")
            if a_elem and a_elem.has_attr("title"):
                candidate_word = a_elem["title"].strip().lower()
                if candidate_word and candidate_word not in used_words and candidate_word != word.lower():
                    related.append(candidate_word)
    else:
        logging.warning(f"No related words container found for '{word}' on Cambridge Dictionary.")

    # Fetch definitions.
    def_elements = soup.find_all("div", class_="def ddef_d db")
    logging.debug(f"Found {len(def_elements)} definition elements for '{word}'.")
    for def_elem in def_elements:
        text = def_elem.get_text(separator=" ", strip=True)
        if text:
            definitions.append(text)

    return related, definitions

def scrape_cambridge_thesaurus(word):
    """
    Fetches synonyms and antonyms from Cambridge Thesaurus for the given word.
    Uses BeautifulSoup to parse the page.
    Returns (synonyms, antonyms) as lists.
    """
    logging.info(f"Scraping Cambridge thesaurus for word: {word}")
    synonyms = []
    antonyms = []
    url = f"https://dictionary.cambridge.org/thesaurus/{word}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            logging.warning(f"Failed to load thesaurus page for {word}: {response.status_code}")
            return synonyms, antonyms
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for thesaurus {word}: {e}")
        return synonyms, antonyms

    soup = BeautifulSoup(response.text, "html.parser")

    # Fetch synonyms.
    syn_header = soup.find("h4", string=lambda s: s and "Synonyms" in s)
    syn_container = syn_header.find_next_sibling("div", class_="tlcs") if syn_header else None
    if syn_container:
        items = syn_container.find_all("div", class_="item")
        logging.debug(f"Found {len(items)} synonym items for '{word}'.")
        for item in items:
            a_elem = item.find("a")
            if a_elem:
                span_elem = a_elem.find("span")
                if span_elem:
                    candidate_word = span_elem.get_text(strip=True).lower()
                    if candidate_word and candidate_word not in synonyms:
                        synonyms.append(candidate_word)
    else:
        logging.warning(f"No synonyms container found for '{word}' on Cambridge Thesaurus.")

    # Fetch antonyms.
    ant_header = soup.find("h4", string=lambda s: s and "Antonyms" in s)
    ant_container = ant_header.find_next_sibling("div", class_="tlcs") if ant_header else None
    if ant_container:
        items = ant_container.find_all("div", class_="item")
        logging.debug(f"Found {len(items)} antonym items for '{word}'.")
        for item in items:
            a_elem = item.find("a")
            if a_elem:
                span_elem = a_elem.find("span")
                if span_elem:
                    candidate_word = span_elem.get_text(strip=True).lower()
                    if candidate_word and candidate_word not in antonyms:
                        antonyms.append(candidate_word)
    else:
        logging.warning(f"No antonyms container found for '{word}' on Cambridge Thesaurus.")

    return synonyms, antonyms

def create_quiz_item(topic, candidate_word, related_synonyms):
    """
    Creates a multiple-choice quiz item using the related words.
    The question is: "Which of the following is a synonym for '<candidate_word>'?"
    The first related word is used as the correct answer.
    """
    logging.info(f"Creating quiz item for word: {candidate_word} under topic: {topic}")
    if not related_synonyms:
        logging.debug("No related synonyms available, skipping quiz item.")
        return None
    correct = related_synonyms[0]
    options = related_synonyms[:5]
    while len(options) < 5:
        options.append("")

    question_text = f"Which of the following is a synonym for '{candidate_word}'?"
    return {
        "Question Text": question_text,
        "Question Type": "Multiple Choice",
        "Option 1": options[0],
        "Option 2": options[1],
        "Option 3": options[2],
        "Option 4": options[3],
        "Option 5": options[4],
        "Correct Answer": "1",
        "Time in seconds": "30",
        "Image Link": "",
        "Answer explanation": f"The word '{correct}' is a synonym for '{candidate_word}' (Topic: {topic})."
    }

# Set up a progress bar for unique words processed (goal: WORD_COUNT words).
pbar = tqdm(total=WORD_COUNT, desc="Unique words processed", unit="word")
start_time = time.time()

# Process each topic using a BFS (queue) until used_words count exceeds WORD_COUNT.
for topic in topics:
    logging.info(f"Processing topic: {topic}")
    queue = candidate_words.get(topic, []).copy()
    topic_used_words = 0  # Reset counter for each topic

    while queue and topic_used_words < (WORD_COUNT/5):
        candidate = queue.pop(0)
        if candidate in used_words:
            continue
        logging.info(f"Processing candidate word: '{candidate}' for topic: {topic}")

        # Process candidate...
        used_words.add(candidate)
        topic_used_words += 1

        # Scrape related words and definitions.
        related_words, definitions = scrape_cambridge_info(candidate)
        new_related = [w for w in related_words if w not in used_words]

        # Mark candidate as processed and add new related words.
        used_words.add(candidate)
        queue.extend(new_related)

        # Create a quiz item.
        quiz_item = create_quiz_item(topic, candidate, new_related)
        if quiz_item:
            quiz_items.append(quiz_item)

        # Scrape synonyms and antonyms.
        syns, ants = scrape_cambridge_thesaurus(candidate)
        if syns or ants:
            thesaurus_items.append({
                "Word": candidate,
                "Topic": topic,
                "Synonyms": ", ".join(syns),
                "Antonyms": ", ".join(ants)
            })

        # Save definitions.
        if definitions:
            definitions_text = " | ".join(definitions)
            definitions_items.append({
                "Word": candidate,
                "Topic": topic,
                "Definition": definitions_text
            })

        pbar.n = len(used_words)
        pbar.refresh()

pbar.close()
elapsed_time = time.time() - start_time
logging.info(f"Processing complete in {elapsed_time:.2f} seconds.")

# Export Quizizz quiz items to an Excel file.
quiz_columns = ["Question Text", "Question Type", "Option 1", "Option 2", "Option 3",
                "Option 4", "Option 5", "Correct Answer", "Time in seconds", "Image Link", "Answer explanation"]
df_quiz = pd.DataFrame(quiz_items, columns=quiz_columns)
output_excel = "quizizz_questions.xlsx"
df_quiz.to_excel(output_excel, index=False)
logging.info(f"Excel file '{output_excel}' created with {len(df_quiz)} quiz questions.")

# Export thesaurus data to a CSV file.
df_thesaurus = pd.DataFrame(thesaurus_items, columns=["Word", "Topic", "Synonyms", "Antonyms"])
output_csv_thesaurus = "cambridge_thesaurus.csv"
df_thesaurus.to_csv(output_csv_thesaurus, index=False)
logging.info(f"CSV file '{output_csv_thesaurus}' created with thesaurus data for {len(df_thesaurus)} words.")

# Export definitions data to a CSV file.
df_definitions = pd.DataFrame(definitions_items, columns=["Word", "Topic", "Definition"])
output_csv_definitions = "cambridge_definitions.csv"
df_definitions.to_csv(output_csv_definitions, index=False)
logging.info(f"CSV file '{output_csv_definitions}' created with definitions for {len(df_definitions)} words.")

logging.info("Scraping process completed successfully.")