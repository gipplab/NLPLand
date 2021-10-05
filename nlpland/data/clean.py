import string
from typing import List, Set

import nltk
import regex as re


def clean_paper_id(paper_id: str) -> str:
    return paper_id.replace(".", "_")


def clean_venue_name(venue_name: str) -> str:
    return venue_name.replace("*", "").replace("/", "_").replace(" ", "_")


def preprocess_text(text: str, language_vocabulary: Set[str], lemmatizer: nltk.WordNetLemmatizer, stopwords: Set[str]) -> List[str]:
    text = newline_hyphens(text, language_vocabulary)
    tokens = tokenize_and_lemmatize(text, lemmatizer)
    tokens = remove_stopwords(tokens, stopwords)
    return tokens


def newline_hyphens(input_: str, language_vocabulary: Set[str]) -> str:
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


def tokenize_and_lemmatize(text: str, lemmatizer: nltk.WordNetLemmatizer) -> List[str]:
    nltk_resource("tokenizers/punkt")
    nltk_resource("corpora/wordnet")
    tokens = nltk.word_tokenize(text)
    return [lemmatizer.lemmatize(token) for token in tokens]


def english_words() -> Set[str]:
    nltk_resource("corpora/words")
    return set(nltk.corpus.words.words())


def stopwords_and_more() -> Set[str]:
    nltk_resource("corpora/stopwords")
    stops = nltk.corpus.stopwords.words('english')
    stops += list(string.punctuation)
    return set(stops)


def lemmatizer() -> nltk.WordNetLemmatizer:
    return nltk.stem.WordNetLemmatizer()


def is_number(word: str) -> bool:
    try:
        float(word)
        return True
    except ValueError:
        return False


def remove_stopwords(tokens: List[str], stopwords: Set[str]) -> List[str]:
    return [token for token in tokens if token not in stopwords and not is_number(token)]


def nltk_resource(name: str) -> None:
    try:
        nltk.data.find(name)
    except LookupError:
        nltk.download(name.split("/")[-1])
