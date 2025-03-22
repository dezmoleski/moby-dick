#!/usr/bin/python3
# 
# The sole purpose of this script is to split the Project Gutenberg
# plain text file of Moby-Dick into chapters and sentences. Output
# is plain text also in a simple format for downstream processing.
# 
# The script is tuned to work with a specially (hopefully slightly)
# modified version of the plain text edition #2701 from Project
# Gutenberg, which is archived with the script here:
# 
#   https://github.com/dezmoleski/moby-dick
# 
# This script is Copyright (C) 2025 Dez Moleski dez@moleski.com
# MIT License: All uses allowed with attribution.
# 
# The output of this script is in the public domain.
# 
import sys
import re
from dataclasses import dataclass
from dataclasses import field

MOBY_STR = ''

@dataclass()
class Chapter:
    number: int
    title: str
    title_offset: int
    text_offset: int
    end_offset: int = 0
    
    def __len__(self) -> int:
        if self.end_offset > self.text_offset:
            return self.end_offset -  self.text_offset
        return 0

    def __repr__(self) -> str:
        return f'Ch. {self.number} "{self.title}" {self.text_offset} - {self.end_offset}'
    
    def text(self) -> str:
        if len(self) > 0:
            return MOBY_STR[self.text_offset:self.end_offset]
        return ''
    
def split_moby_dick(filepath: str):
    global MOBY_STR
    
    with open(filepath, 'rt') as f:
        MOBY_STR = f.read()
    print("# Split Moby-Dick into chapters, paragraphs, and sentences from file:", filepath, " len:", len(MOBY_STR))
    print("# The contents of this file are in the public domain.")
    
    ##########################
    # PHASE I - Find chapters
    ##########################
    contents = dict() # {<chapter number>:"Chapter Title", ...}
    chapters = list() # of Chapter instances
    
    # We have a couple special cases right off the bat: the ETYMOLOGY and EXTRACTS.
    # My interest here is to catalog the sentences that are original to Melville,
    # so the sections other than the intro paragraphs are not part of the main
    # index. The plan though is to keep all the text of the book in the output, so
    # there is going to be some **TBD** markup for pre-formatted sections that are
    # not included in the chapter/paragraph/sentence index.
    etymology_re = r'^ETYMOLOGY .+\.$'
    re_etymology = re.compile(etymology_re, re.MULTILINE)
    etym = None
    ETYM_INDEX = -1
    for etym_match in re_etymology.finditer(MOBY_STR):
        title = etym_match.group()[0:-1] # Take the whole matching string minus the period.
        if contents.get(ETYM_INDEX) is None:
            contents[ETYM_INDEX] = title
        else:
            etym = Chapter(ETYM_INDEX,
                           title,
                           etym_match.start(),
                           etym_match.end()+2) # Skip two newlines to reach chapter text offset
            chapters.append(etym)
    
    extracts_re = r'^EXTRACTS .+\.$'
    re_extracts = re.compile(extracts_re, re.MULTILINE)
    extr = None
    EXTR_INDEX = 0
    for extr_match in re_extracts.finditer(MOBY_STR):
        title = extr_match.group()[0:-1] # Take the whole matching string minus the period.
        if contents.get(EXTR_INDEX) is None:
            contents[EXTR_INDEX] = title
        else:
            extr = Chapter(EXTR_INDEX,
                           title,
                           extr_match.start(),
                           extr_match.end()+2) # Skip two newlines to reach chapter text offset
            etym.end_offset = extr.title_offset - 1
            chapters.append(extr)
    
    # The main chapters 1-135 can be chopped up with this regex:
    chapter_re = r'^CHAPTER (?P<ch_num>\d+)\. (?P<ch_title>.+)(?P<title_terminator>[\.\!\?])$'
    re_chapter = re.compile(chapter_re, re.MULTILINE)
    prev_chapter = extr
    for ch_match in re_chapter.finditer(MOBY_STR):
        ch_num = int(ch_match['ch_num'])
        ch_title = ch_match['ch_title']
        terminator = ch_match['title_terminator']
        if terminator == '!' or terminator == '?':
            ch_title += terminator

        # The chapter regex matches twice: once for the contents entry and once for the chapter.
        # So make an entry in contents() the first time a chapter is seen and in chapters() next time.
        if contents.get(ch_num) is None:
            contents[ch_num] = ch_title
        else:
            ch = Chapter(ch_num,
                         ch_title,
                         ch_match.start(),
                         ch_match.end()+2) # Skip two newlines to reach chapter text offset
            if prev_chapter is not None:
                prev_chapter.end_offset = ch.title_offset - 1
            chapters.append(ch)
            prev_chapter = ch
    
    # Fix up the Epilogue and the end offset of chapter 135 just before it.
    re_epilogue = re.compile(r'^Epilogue$', re.MULTILINE)
    ep = None
    for ep_match in re_epilogue.finditer(MOBY_STR):
        if contents.get(136) is None:
            contents[136] = "Epilogue"
        else:
            ep = Chapter(136,
                         "Epilogue",
                         ep_match.start(),
                         ep_match.end()+2) # Skip two newlines to reach chapter text offset
            prev_chapter.end_offset = ep.title_offset - 1
            chapters.append(ep)
            
    # Find the end of the epilogue using the Project Gutenberg end marker
    re_end = re.compile(r'\*\*\* END')
    end_match = re_end.search(MOBY_STR)
    ep.end_offset = end_match.start() - 1
    
    # Debug output
    for chap in chapters:
        print(chap)
        print(chap.text())

    print("N chapters:", len(chapters))
    
if __name__ == "__main__":
    split_moby_dick("pg2701-modified.txt")
    
