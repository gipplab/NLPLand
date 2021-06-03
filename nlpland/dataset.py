import os
import time
import pandas as pd
import urllib.request
from tqdm import tqdm
from tika import parser
from typing import List
from nlpland.constants import COLUMN_ABSTRACT, MISSING_PAPERS, ABSTRACT_SOURCE_ANTHOLOGY, ABSTRACT_SOURCE_RULE, COLUMN_ABSTRACT_SOURCE
from nlpland.data_cleanup import clean_paper_id, clean_venue_name


def download_papers(df: pd.DataFrame, min_year: int, max_year: int) -> None:
    path_papers = os.getenv("PATH_PAPERS")
    df_missing = pd.read_csv(MISSING_PAPERS, delimiter="\t", low_memory=False, header=None)

    years = []
    for year in range(min_year, max_year+1):
        years.append(year)

    for year in years:
        print(f"Downloading papers from {year}.")
        df_year = df[df["AA year of publication"] == year]
        for i, row in tqdm(df_year.iterrows(), total=df_year.shape[0]):
            venue = clean_venue_name(row["NS venue name"])
            output_dir = f"{path_papers}/{year}/{venue}"
            os.makedirs(output_dir, exist_ok=True)
            filename = clean_paper_id(row["AA paper id"])
            full_path = f"{output_dir}/{filename}.pdf"

            if not os.path.isfile(full_path) and row["AA paper id"] not in df_missing.iloc[:, [0]].values:
                url = row["AA url"]
                if str.startswith(url, "https://www.aclweb.org/anthology/"):
                    url = f"{url}.pdf"
                elif str.startswith(url, "http://yanran.li/"):
                    # TODO
                    pass
                try:
                    urllib.request.urlretrieve(url, full_path)
                except urllib.error.HTTPError:
                    with open(MISSING_PAPERS, "a+") as f:
                        f.write(f"{row['AA paper id']}\t{url}\n")

def load_dataset(env_name: str):
    return pd.read_csv(os.getenv(env_name), delimiter="\t", low_memory=False, header=0, index_col=0)
    # df_expanded = pd.read_csv(os.getenv("PATH_DATASET_EXPANDED"), delimiter="\t", low_memory=False, header=0, index_col=0)


def save_dataset(df: pd.DataFrame):
    path_dataset_expanded = os.getenv("PATH_DATASET_EXPANDED")
    df.to_csv(path_dataset_expanded, sep="\t", na_rep="NA")


def determine_earliest_string(text: str, possible_strings: List[str]):
    earliest_string = ""
    earliest_pos = -1
    for possible_string in possible_strings:
        pos_current = text.find(possible_string)
        if pos_current != -1 and (earliest_pos == -1 or pos_current < earliest_pos):
            earliest_pos = pos_current
            earliest_string = possible_string
    return earliest_pos, earliest_string


def extract_abstracts_rulebased(df: pd.DataFrame, min_year: int = 1965, max_year: int = 2020, venues: List[str] = None, overwrite_abstracts: bool = False) -> None:
    # TODO startup tika server
    start = time.time()
    iterated = 0
    searched = 0
    skipped = 0
    index = 0
    nones = 0
    # unicode = 0
    no_file = 0
    path_papers = os.getenv("PATH_PAPERS")

    # df_create_cols(df)

    df_select = df[(min_year <= df["AA year of publication"]) & (df["AA year of publication"] <= max_year)]
    if venues is not None:
        df_select = df_select[df_select["NS venue name"].isin(venues)]

    for i, row in tqdm(df_select.iterrows(), total=df_select.shape[0]):
        iterated += 1
        if overwrite_abstracts or pd.isnull(row[COLUMN_ABSTRACT]):
            paper_id = clean_paper_id(row["AA paper id"])
            venue = clean_venue_name(row["NS venue name"])
            year = row["AA year of publication"]
            full_path = f"{path_papers}/{year}/{venue}/{paper_id}.pdf"
            if os.path.isfile(full_path):
                searched += 1

                raw = parser.from_file(full_path)
                text = raw["content"]

                if text is None:
                    nones += 1
                else:
                    start_strings = ["Abstract", "ABSTRACT", "A b s t r a c t"]
                    start_pos, start_string = determine_earliest_string(text, start_strings)
                    start_pos += len(start_string)

                    end_strings_1 = ["\n\nTITLE AND ABSTRACT IN ", "\n\nTitle and Abstract in ", "KEYWORDS:", "Keywords:"]
                    end_pos, end_string = determine_earliest_string(text, end_strings_1)
                    if end_pos == -1:
                        end_strings_2 = ["\n\n1 Introduction", "\n\n1. Introduction",
                                         "\n\n1 Task Description", "\n\n1. Task Description",
                                         "\n\nIntroduction\n\n", "\n\n1 "]
                        for end_string in end_strings_2:
                            end_pos = text.find(end_string, start_pos)
                            if end_pos != -1:
                                break

                    # if row["NS venue name"] == "CL":
                    #     end_string = "\n\n1. Introduction"
                    #     end_pos = text.find(end_string)
                    #     start_string = "\n\n"
                    #     start_pos = text.rfind("\n\n", 0, end_pos)

                    if end_pos == -1 or start_pos == -1:
                        index += 1
                    else:
                        abstract = text[start_pos:end_pos]
                        df.at[i, COLUMN_ABSTRACT] = abstract
                        df.at[i, COLUMN_ABSTRACT_SOURCE] = ABSTRACT_SOURCE_RULE
                        # if "�" in abstract:
                        #     df.at[i, UNICODE_COLUMN] = True
                        #     unicode += 1
                        # else:
                        #     df.at[i, UNICODE_COLUMN] = False
            else:
                no_file += 1
        else:
            skipped += 1
        if i % 1000 == 0 and i > 0:
            save_dataset(df)
    save_dataset(df)
    print(f"Papers iterated: {iterated} matching year+venue")
    print(f"Abstracts searched: {searched} abstracts searched")
    print(f"Abstracts skipped: {skipped} already existed")
    print(f"none: {nones} texts of papers are None")
    print(f"index: {index} abstracts not found")
    # print(f"�: {unicode} new abstracts with �")
    print(f"no_file: {no_file} papers not downloaded")
    duration = time.gmtime(time.time()-start)
    print(f"This took {time.strftime('%Mm %Ss', duration)}.")


def extract_abstracts_anthology(df: pd.DataFrame):
    # always overwrites

    # print(os.getenv("PYTHONPATH"))
    # os.environ["PYTHONPATH"]+=":E:/workspaces/python-git/acl-anthology/bin"
    # print(os.getenv("PYTHONPATH"), os.getenv("ACLANTHOLOGY"))
    #
    # import sys
    # sys.path.append(os.path.abspath("E:/workspaces/python-git/acl-anthology/bin"))
    # # install requirements.txt in bin/
    #
    # from anthology import Anthology
    #
    # anthology = Anthology(importdir='E:/workspaces/python-git/acl-anthology/data')
    # for id_, paper in anthology.papers.items():
    #     print(paper.anthology_id, paper.get_title('text'))

    # todo setup df
    # df_create_cols()

    from lxml import etree
    start = time.time()
    abstracts = 0
    path_anthology = os.getenv("PATH_ANTHOLOGY")
    for file in tqdm(os.listdir(path_anthology), total=len(os.listdir(path_anthology))):
        if file.endswith(".xml"):
            tree = etree.parse(f"{path_anthology}/{file}")
            for element in tree.iter("paper"):
                children = element.getchildren()
                id = None
                abstract = None
                for child in children:
                    if child.tag == "url":
                        id = child.text
                    if child.tag == "abstract":
                        if child.text is not None:
                            abstract = child.xpath("string()")
                if id is not None and abstract is not None:
                    df.at[id, COLUMN_ABSTRACT] = abstract
                    df.at[id, COLUMN_ABSTRACT_SOURCE] = ABSTRACT_SOURCE_ANTHOLOGY
                    abstracts += 1
                    # TODO only add when in id
                    # TODO lrec id = url, not id
    save_dataset(df)
    print(f"Abstracts added/overwritten: {abstracts}")
    duration = time.gmtime(time.time() - start)
    print(f"This took {time.strftime('%Mm %Ss', duration)}.")