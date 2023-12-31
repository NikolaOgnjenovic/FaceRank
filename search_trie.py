class Node:
    def __init__(self, letter):
        self.letter = letter
        self.children = {}
        self.counter = 0  # Indicates how many times the sentence has been inserted (parent -> child -> child)
        self.status_ids: set[str] = set()
        self.is_terminal: bool = False


# Leaves only lowercase letters and spaces inside a string. Replaces all other characters with spaces.
def filter_status_characters(status: str, to_lower: bool) -> str:
    filtered_status = ''
    if to_lower:
        status = status.lower()
    for char in status:
        if (not to_lower and (65 <= ord(char) <= 90)) or (97 <= ord(char) <= 122) or char == ' ' or char.isnumeric():
            filtered_status += char
        else:
            filtered_status += ' '

    return filtered_status


# A pattern searching function that uses Bad Character Heuristic of Boyer Moore Algorithm
def has_phrase(text: str, pattern: str) -> bool:
    text_len = len(text)
    pattern_len = len(pattern)
    if pattern_len == 0:
        return True

    last = {}
    for k in range(pattern_len):
        last[pattern[k]] = k

    i = pattern_len - 1
    k = pattern_len - 1
    while i < text_len:
        if text[i] == pattern[k]:
            if k == 0:
                return True
            else:
                i -= 1
                k -= 1
        else:
            j = last.get(text[i], -1)
            i += pattern_len - min(k, j + 1)
            k = pattern_len - 1
    return False


class Trie(object):
    def __init__(self):
        """
        The root node does not store a letter
        """
        self.root = Node('')

    def insert(self, status, status_id):
        """Inserts a status into the trie"""
        # Loop through each word in the sentence
        status = filter_status_characters(status, True)
        words = status.split(' ')
        for word in words:
            node = self.root
            for i in range(0, len(word)):
                # If the letter is found, break out of the word loop
                if word[i] in node.children.keys():
                    node = node.children[word[i]]
                # If the letter is not found, create a new node in the trie
                else:
                    new_node = Node(word[i])
                    node.children[word[i]] = new_node
                    node = new_node

                node.status_ids.add(status_id)
                node.counter += 1  # Increase the times the node has been stored in the trie

            node.is_terminal = True  # Mark the last node in the word as terminal (used for autocompletion)

    def dfs(self, letters: str, letter_counter: int, node: Node) -> set[str]:
        # Base case: if all letters have been found, return the ids of the node
        if letter_counter == len(letters):
            return node.status_ids

        ids = set()
        # If the node's children contain the given letter, iterate deeper and update the ids set
        letter = letters[letter_counter]
        if letter in node.children:
            node_ids = self.dfs(letters, letter_counter + 1, node.children[letter])
            if node_ids:
                ids.update(node_ids)

        return ids

    # Returns a set of status ids that hold the given search term
    def query(self, search_term: str) -> set[str]:
        # join(filter MAG#$! A) == join(MAG    A) == MAGA
        letters = ''.join(filter_status_characters(search_term, True).split(" "))
        if len(letters) == 0:
            return set()

        # If the first letter is not in the letter hash map, return an empty set
        ids = set()

        # Iterate through every node in list of the first letter hash
        nodes = self.root.children
        for letter, node in nodes.items():
            if letters[0] == letter:
                node_ids = self.dfs(letters, 1, node)
            else:
                node_ids = self.dfs(letters, 0, node)
            if node_ids:
                ids.update(node_ids)
        return ids

    # Returns a list of autocompleted search terms
    def autocomplete(self, prefix):
        prefix = filter_status_characters(prefix, True).replace(' ', '')
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]

        # Sort the words-occurrence pair list by the occurrence descending
        words = self.get_words_from_prefix(node, prefix)
        words.sort(key=lambda w: w[1], reverse=True)
        return words

    # Returns a list of pairs (word, occurrences in trie) that contain the given prefix
    def get_words_from_prefix(self, node, prefix) -> list[(str, int)]:
        words = []
        # If the node marks the end of a word, add a space to the prefix and add it the word list
        if node.is_terminal:
            words.append((prefix, node.counter))
        # For each child, add the child's character to the prefix and iterate deeper
        for char, child in node.children.items():
            words.extend(self.get_words_from_prefix(child, prefix + char))
        return words

    # Returns status ids that contain all words in the given phrase (case-sensitive!)
    def search_phrase(self, phrase, statuses):
        phrase = phrase[1:-1]  # Remove " from the beginning and end of the phrase
        phrase = filter_status_characters(phrase, False)  # Filter the characters, but leave uppercase characters
        status_ids = self.search_intersection_case_insensitive(phrase)  # Do a case-insensitive search of the phrase

        filtered_ids = []
        for status_id in status_ids:
            if has_phrase(statuses[status_id]['status_message'], phrase + ' '):
                filtered_ids.append(status_id)

        return filtered_ids

    # Performs a case-insensitive intersection search for the given phrase
    def search_intersection_case_insensitive(self, phrase):
        phrase_words = phrase.split(' ')
        status_ids = self.query(phrase_words[0])
        for i in range(1, len(phrase_words)):
            status_ids = status_ids.intersection(self.query(phrase_words[i]))

        return status_ids

    # Returns a dictionary which maps a status id to the number of words in the phrase that are in the status
    def search_union_case_insensitive(self, phrase) -> dict:
        phrase_words = phrase.split(' ')
        status_ids: dict = {}
        for word in phrase_words:
            word_status_ids = list(self.query(word))
            for status_id in word_status_ids:
                if status_id in status_ids:
                    status_ids[status_id] = status_ids[status_id] + 1
                else:
                    status_ids.update({status_id: 1})

        return status_ids
