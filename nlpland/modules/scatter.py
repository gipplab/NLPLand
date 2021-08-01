import os
import pandas as pd


import nlpland.data.clean as clean_
from nlpland.constants import COLUMN_ABSTRACT, CURRENT_TIME
import nlpland.data.filter as filter_

CATEGORY = "category"
PARSE = "parse"


def preprocess_dfs(df1: pd.DataFrame, df2: pd.DataFrame, fast: bool):
    df1[CATEGORY] = "c1"
    df2[CATEGORY] = "c2"
    df = pd.concat([df1, df2])

    english_words = clean_.english_words()

    df_titles = df[[CATEGORY, "AA title"]]
    df_titles = df_titles.dropna(subset=["AA title"])
    df_titles = df_titles.rename(columns={"AA title": PARSE})
    df_abstracts = df[[CATEGORY, COLUMN_ABSTRACT]]
    df_abstracts = df_abstracts.dropna(subset=[COLUMN_ABSTRACT])
    df_abstracts[COLUMN_ABSTRACT] = df_abstracts[COLUMN_ABSTRACT].apply(lambda x: clean_.newline_hyphens(x, english_words))
    df_abstracts = df_abstracts.rename(columns={COLUMN_ABSTRACT: PARSE})
    df = pd.concat([df_titles, df_abstracts])

    # df[PARSE] = df[COLUMN_ABSTRACT].apply(st.whitespace_nlp)
    # the above one is even faster, but breaks if lemmatization is active
    import spacy
    if fast:
        model = "en_core_web_sm"
    else:
        model = "en_core_web_trf"
    nlp = spacy.load(name=model, disable=["ner", "textcat", "custom"])
    df[PARSE] = df[PARSE].apply(nlp)

    return df


def plot_word_counts(df1: pd.DataFrame, df2: pd.DataFrame, fast, filters):
    import scattertext as st
    df = preprocess_dfs(df1, df2, fast)
    stopwords = clean_.stopwords_and_more()

    corpus = st.CorpusFromParsedDocuments(
        df, category_col=CATEGORY, parsed_col=PARSE,
        feats_from_spacy_doc=st.FeatsFromSpacyDoc(use_lemmas=True)
    ).build().remove_terms(stopwords, ignore_absences=True).get_unigram_corpus().compact(st.AssociationCompactor(2000))

    html = st.produce_scattertext_explorer(
        corpus,
        category="c1", category_name=filter_.category_names(filters),
        not_category_name=filter_.category_names(filters, second_df=True),
        minimum_term_frequency=5, pmi_threshold_coefficient=0,
        width_in_pixels=1000,
        transform=st.Scalers.dense_rank
    )
    path = f"output/scattertext/st_{CURRENT_TIME}.html"
    open(path, 'w+', encoding="UTF-8").write(html)
    print(f"File created at {os.path.abspath(path)}")