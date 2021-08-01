import nltk
import regex as re
import string
from typing import List


def clean_paper_id(paper_id: str) -> str:
    return paper_id.replace(".", "_")


def clean_venue_name(venue_name: str) -> str:
    return venue_name.replace("*", "").replace("/", "_").replace(" ", "_")


def preprocess_text(text: str, language_vocabulary, lemmatizer, stopwords):
    text = newline_hyphens(text, language_vocabulary)
    tokens = tokenize_and_lemmatize(text, lemmatizer)
    tokens = remove_stopwords(tokens, stopwords)
    return tokens


def newline_hyphens(input_: str, language_vocabulary):
    # does not remove stopwords, punctuation
    input_ = input_.lower()
    for match in re.findall(r"[\s]+(\S*-\n\S*)[\s]+", input_, overlapped=True):
        # regex: start and end with whitespace
        # arbitrary amount of chars with -\n somewhere in it
        new_match = match.replace("-\n", "")
        new_match = new_match.strip(string.punctuation)
        if new_match in language_vocabulary:
            input_ = input_.replace(match, new_match)
        else:
            input_ = input_.replace(match, match.replace("-\n", "-"))
    return input_


def tokenize_and_lemmatize(text, lemmatizer):
    tokens = nltk.word_tokenize(text)
    return [lemmatizer.lemmatize(token) for token in tokens]


def english_words():
    return set(nltk.corpus.words.words())


def stopwords_and_more():
    stops = nltk.corpus.stopwords.words('english')
    stops += [char for char in string.punctuation]
    return set(stops)


def lemmatizer():
    return nltk.stem.WordNetLemmatizer()


# TODO add download nltk corpus

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def remove_stopwords(tokens: List[str], stopwords):
    return [token for token in tokens if token not in stopwords and not is_number(token)]