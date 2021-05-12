from typing import *

WORD_DICT = {
    "fantasy": {
        "pre": ["living in", "feeling like in a"],
        "post": ["world", "feeling"],
    },
    "power": {
        "pre": ["I have", "having", "feel the"],
        "post": ["needed"],
    },
    "lazy": {
        "pre": ["l feel", "they are", "I am"],
        "post": ["after school", "homework"],
    },
    "lunatic": {
        "pre": ["he is a", "i am a", "it makes me a"],
        "post": ["under the moon", "photographer"],
    },
    "unpopular": {
        "pre": ["I am very", "people here is", "I don’t sit with"],
        "post": ["guy", "product", "people"],
    },
    "family": {
        "pre": ["happy", "desired", "it is a very large"],
        "post": ["members are loved"],
    },
    "magic": {
        "pre": ["she knows how to do", "rapid"],
        "post": ["product", "ticks for kids"],
    },
    "alive": {
        "pre": ["I feel very much", "the animals are", "the flowers are"],
        "post": ["in the water"],
    },
    "tempting": {
        "pre": ["his kisses are", "desires are"],
        "post": ["cake", "oreos"],
    },
    "strategy": {
        "pre": ["business is built on", "they have no"],
        "post": ["is key", "is what we should aim for"],
    },
    "aesthetics": {
        "pre": ["they optimize for", "their brand"],
        "post": ["are key for her art", "are not important"],
    },
    "loved": {
        "pre": ["our family is", "our friends are"],
        "post": ["is a beautiful word", "by my dogs"],
    },
    "hand": {
        "pre": ["they have nice", "eat it with your"],
        "post": ["model", "picked"],
    },
    "lifetime": {
        "pre": ["they were friends for a", "this store has been here for a"],
        "post": ["friendship", "is a very long time"],
    },
}


def get_word_list() -> List[str]:
    word_list = []
    for word in WORD_DICT.keys():
        word_list.append(word)

    return word_list


def get_word_info(word: str) -> Dict[str, List]:
    return WORD_DICT[word]