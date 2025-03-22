#!/usr/bin/python3
# 
# The sole purpose of this script is to split the Project Gutenberg
# plain text file of Moby-Dick into chapters and sentences. Output
# is plain text also in a simple format for downstream processing.
# 
# Copyright (C) 2025 Dez Moleski dez@moleski.com
# MIT License: All uses allowed with attribution.
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
    
    def guts(self) -> str:
        if len(self) > 0:
            return MOBY_STR[self.text_offset:self.end_offset]
        return ''
    
def split_moby_dick(filepath: str):
    global MOBY_STR
    
    with open(filepath, 'rt') as f:
        MOBY_STR = f.read()
    print("# Split Moby-Dick from file=", filepath, " len(file.read())=", len(MOBY_STR))

    ##########################
    # PHASE I - Find chapters
    # 
    chapter_re = r'^CHAPTER (?P<ch_num>\d+)\. (?P<ch_title>.+)(?P<title_terminator>[\.\!\?])$'
    re_chapter = re.compile(chapter_re, re.MULTILINE)
    contents = dict()
    chapters = list()
    prev_chapter = None
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
                         ch_match.end()+2) # Skip two newlines to reach chapter guts offset
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
                         ep_match.end()+2) # Skip two newlines to reach chapter guts offset
            prev_chapter.end_offset = ep.title_offset - 1
            chapters.append(ep)
            
    # Find the end of the epilogue using the Project Gutenberg end marker
    re_end = re.compile(r'\*\*\* END')
    end_match = re_end.search(MOBY_STR)
    ep.end_offset = end_match.start() - 1
    
    # Debug output
    for chap in chapters:
        print(chap)

    print("N chapters:", len(chapters))
    
if __name__ == "__main__":
    split_moby_dick("pg2701-modified.txt")
    
