#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yusuf Tokenizer - Advanced Turkish Morphological Tokenizer
Decode system that applies phonetic rules in functions
"""

import json
import re
import os
from typing import List, Dict, Tuple, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Turkish case mapping for proper capitalization
TURKISH_LOWER_MAP = {
    'İ': 'i', 'I': 'ı', 'Ş': 'ş', 'Ğ': 'ğ', 'Ü': 'ü', 'Ö': 'ö', 'Ç': 'ç'
}

TURKISH_UPPER_MAP = {
    'i': 'İ', 'ı': 'I', 'ş': 'Ş', 'ğ': 'Ğ', 'ü': 'Ü', 'ö': 'Ö', 'ç': 'Ç'
}

def turkish_lower(text: str) -> str:
    result = ""
    for char in text:
        if char in TURKISH_LOWER_MAP:
            result += TURKISH_LOWER_MAP[char]
        else:
            result += char.lower()
    return result

def turkish_upper(text: str) -> str:
    result = ""
    for char in text:
        if char in TURKISH_UPPER_MAP:
            result += TURKISH_UPPER_MAP[char]
        else:
            result += char.upper()
    return result

def turkish_capitalize(text: str) -> str:
    if not text:
        return text
    
    first_char = text[0]
    if first_char in TURKISH_UPPER_MAP:
        return TURKISH_UPPER_MAP[first_char] + text[1:]
    else:
        return first_char.upper() + text[1:]

# Load JSON files into memory
def load_json(file_path: str) -> Dict[str, int]:
    full_path = os.path.join(CURRENT_DIR, file_path)
    with open(full_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Load roots, suffixes, and BPE tokens
roots = load_json("kokler_v08.json")
suffixes = load_json("ekler_v06.json")
bpe_tokens = load_json("bpe_v08.json")

def choose_correct_form(token_candidates: List[str], next_token: str = None, context: Dict = None, token_type: str = None) -> str:
    """Choose the correct form based on Turkish morphophonemic rules"""
    if len(token_candidates) == 1:
        return token_candidates[0]
    
    # Turkish phonological sets
    vowels = set('aeiıouöü')
    back_vowels = set('aıou')
    front_vowels = set('eiöü')
    unrounded_vowels = set('aeıi')
    rounded_vowels = set('ouöü')
    
    hard_consonants = set('çfhkpsşt')
    soft_consonants = set('bccdgğjlmnrvyz')
    
    # Softening map for consonants
    softening_map = {'p': 'b', 'ç': 'c', 't': 'd', 'k': 'ğ'}
    
    def get_last_vowel(word: str) -> str:
        """Find the last vowel in word"""
        for i in range(len(word) - 1, -1, -1):
            if word[i] in vowels:
                return word[i]
        return None
    
    def apply_vowel_harmony(suffix_candidates: List[str], root: str) -> str:
        """Apply Turkish vowel harmony rules"""
        last_vowel = get_last_vowel(root)
        if not last_vowel:
            return suffix_candidates[0]
        
        # Major vowel harmony (a/e selection)
        if last_vowel in back_vowels:
            # Back vowels prefer 'a'
            a_variants = [c for c in suffix_candidates if 'a' in c and 'e' not in c]
            if a_variants:
                suffix_candidates = a_variants
        else:
            # Front vowels prefer 'e'  
            e_variants = [c for c in suffix_candidates if 'e' in c and 'a' not in c]
            if e_variants:
                suffix_candidates = e_variants
        
        # Minor vowel harmony (ı/i/u/ü selection)
        if last_vowel in {'a', 'ı'}:
            # Back unrounded -> ı
            target_variants = [c for c in suffix_candidates if 'ı' in c]
        elif last_vowel in {'o', 'u'}:
            # Back rounded -> u
            target_variants = [c for c in suffix_candidates if 'u' in c]
        elif last_vowel in {'e', 'i'}:
            # Front unrounded -> i
            target_variants = [c for c in suffix_candidates if 'i' in c and 'ü' not in c]
        elif last_vowel in {'ö', 'ü'}:
            # Front rounded -> ü
            target_variants = [c for c in suffix_candidates if 'ü' in c]
        else:
            target_variants = []
        
        return target_variants[0] if target_variants else suffix_candidates[0]
    
    def apply_consonant_assimilation(suffix_candidates: List[str], root: str) -> str:
        """Apply consonant assimilation rules"""
        if not root:
            return suffix_candidates[0]
            
        root_final = root[-1]
        
        # If root ends with hard consonant, suffix should start with hard consonant
        if root_final in hard_consonants:
            hard_variants = [c for c in suffix_candidates if c and c[0] in hard_consonants]
            if hard_variants:
                return hard_variants[0]
        
        # If root ends with soft consonant, suffix should start with soft consonant
        elif root_final in soft_consonants:
            soft_variants = [c for c in suffix_candidates if c and c[0] in soft_consonants]
            if soft_variants:
                return soft_variants[0]
        
        return suffix_candidates[0]
    
    def apply_root_softening(root_candidates: List[str], next_suffix: str) -> str:
        """Apply consonant softening for roots before vowel-initial suffixes"""
        if not next_suffix or next_suffix[0] not in vowels:
            return root_candidates[0]
        
        # Look for softened forms
        for candidate in root_candidates:
            if candidate and candidate[-1] in soft_consonants:
                # Check if this could be a softened form
                base_form = None
                for other in root_candidates:
                    if (other != candidate and 
                        len(other) == len(candidate) and
                        other[:-1] == candidate[:-1]):
                        
                        # Check if last consonant matches softening pattern
                        if other[-1] in softening_map and softening_map[other[-1]] == candidate[-1]:
                            base_form = other
                            break
                
                if base_form:
                    return candidate  # Return softened form
        
        return root_candidates[0]
    
    def apply_consonant_softening(self, root: str, suffix: str) -> str:
        """Apply consonant softening"""
        if not root or not suffix:
            return root
            
        # If the root ends with a hard consonant and the suffix starts with a vowel, softening occurs
        if (root[-1] in self.phonology.hard_consonants and 
            suffix and suffix[0] in self.phonology.vowels):
            
            # Exceptions check
            if self._is_softening_exception(root, suffix):
                return root
                
            # Apply softening
            if root[-1] in self.phonology.softening_map:
                return root[:-1] + self.phonology.softening_map[root[-1]]
                
        return root
    
    
    def apply_vowel_drop(self, root: str, suffix: str) -> str:
        """Apply vowel drop"""
        if not root or len(root) < 2:
            return root
            
        # Two-syllable roots + vowel-starting suffix
        if (self._is_two_syllable(root) and 
            suffix and suffix[0] in self.phonology.vowels and
            root[-2] in self.phonology.vowels):
            
            # Exceptions check
            if self._is_vowel_drop_exception(root):
                return root
                
            # Apply vowel drop
            return root[:-2] + root[-1]
            
        return root
    
    
    def apply_buffer_consonant(self, root: str, suffix: str) -> str:
        """Add buffer consonant"""
        if not root or not suffix:
            return suffix
            
        # If the root ends with a vowel and the suffix starts with a vowel, add buffer consonant
        if (root[-1] in self.phonology.vowels and 
            suffix[0] in self.phonology.vowels):
            
            # 3. For personal suffix, add 's'
            if suffix in ['i', 'ı', 'u', 'ü']:
                return 's' + suffix
                
            # For other cases, add 'y'
            return 'y' + suffix
            
        return suffix
    
    def _apply_major_vowel_harmony(self, suffix: str, vowel_props: Dict[str, bool]) -> str:
        """Major vowel harmony (a/e)"""
        if vowel_props['back']:
            return suffix.replace('e', 'a')
        else:
            return suffix.replace('a', 'e')
    
    def _apply_minor_vowel_harmony(self, suffix: str, vowel_props: Dict[str, bool]) -> str:
        """Minor vowel harmony (ı/i/u/ü)"""
        if vowel_props['back'] and vowel_props['unrounded']:
            # a, ı -> ı
            return suffix.replace('i', 'ı').replace('u', 'ı').replace('ü', 'ı')
        elif vowel_props['back'] and vowel_props['rounded']:
            # o, u -> u
            return suffix.replace('i', 'u').replace('ı', 'u').replace('ü', 'u')
        elif vowel_props['front'] and vowel_props['unrounded']:
            # e, i -> i
            return suffix.replace('ı', 'i').replace('u', 'i').replace('ü', 'i')
        elif vowel_props['front'] and vowel_props['rounded']:
            # ö, ü -> ü
            return suffix.replace('i', 'ü').replace('ı', 'ü').replace('u', 'ü')
            
        return suffix

    
    # Determine token type and apply appropriate rules
    is_suffix = token_type == 'suffix' or (context and 'current_root' in context and context['current_root'])
    
    if is_suffix and context and 'current_root' in context:
        current_root = context['current_root']
        
        # Apply vowel harmony first
        selected = apply_vowel_harmony(token_candidates, current_root)
        
        # Then apply consonant assimilation if needed
        candidates_for_assimilation = [c for c in token_candidates if 
                                     get_last_vowel(c) == get_last_vowel(selected) if get_last_vowel(c)]
        if not candidates_for_assimilation:
            candidates_for_assimilation = [selected]
            
        selected = apply_consonant_assimilation(candidates_for_assimilation, current_root)
        
        return selected
        
    elif not is_suffix:
        # For roots, apply softening if next token is vowel-initial
        if next_token:
            return apply_root_softening(token_candidates, next_token)
    
    # Default: return first candidate
    return token_candidates[0]

reverse_dict = {}
for key, value in roots.items():
    if value not in reverse_dict:
        reverse_dict[value] = []
    reverse_dict[value].append(key)
    
for key, value in suffixes.items():
    if value not in reverse_dict:
        reverse_dict[value] = []
    reverse_dict[value].append(key)
    
for key, value in bpe_tokens.items():
    if value not in reverse_dict:
        reverse_dict[value] = []
    reverse_dict[value].append(key)

# Special token IDs
SPECIAL_TOKENS = {
    "<uppercase>": 0, "<space>": 1, "<newline>": 2, "<tab>": 3, "<unknown>": 4
}

def tokenize(text: str) -> Dict[str, List]:
    tokens = []
    ids = []

    i = 0
    while i < len(text):
        char = text[i]
        if char == ' ':
            tokens.append("<space>")
            ids.append(SPECIAL_TOKENS["<space>"])
        elif char == '\n':
            tokens.append("<newline>")
            ids.append(SPECIAL_TOKENS["<newline>"])
        elif char == '\t':
            tokens.append("<tab>")
            ids.append(SPECIAL_TOKENS["<tab>"])
        elif char.isalnum() or char in ".,!?;:()[]{}@#$%^&*-+=_/\\'\"`":
            word_start = i
            while i < len(text) and (text[i].isalnum() or text[i] in ".,!?;:()[]{}@#$%^&*-+=_/\\'\"`"):
                i += 1
            word = text[word_start:i]
            i -= 1
            
            if any(c.isupper() for c in word):
                # Split by uppercase patterns (including Turkish characters)
                parts = []
                current_part = ""
                
                for char in word:
                    if char.isupper():
                        # If we have accumulated lowercase chars, save them
                        if current_part:
                            parts.append(current_part)
                            current_part = ""
                        # Start new uppercase part
                        current_part = char
                    else:
                        # Add to current part (either continuing uppercase word or lowercase)
                        current_part += char
                
                # Add final part
                if current_part:
                    parts.append(current_part)
                
                # Process each part
                for part in parts:
                    if part and part[0].isupper():
                        tokens.append("<uppercase>")
                        ids.append(SPECIAL_TOKENS["<uppercase>"])
                        process_word(turkish_lower(part), tokens, ids)
                    else:
                        process_word(part, tokens, ids)
            else:
                process_word(word, tokens, ids)
        else:
            # Unsupported character - check if it's in BPE
            if char in bpe_tokens:
                tokens.append(char)
                ids.append(bpe_tokens[char])
            else:
                # Really unsupported character - <unknown>
                tokens.append("<unknown>")
                ids.append(SPECIAL_TOKENS["<unknown>"])
        i += 1

    return {"tokens": tokens, "ids": ids}

def process_word(word: str, tokens: List[str], ids: List[int]):
    root, root_id, remainder = match_root(word)
    if root:
        tokens.append(root)
        ids.append(root_id)
        if remainder:
            process_remainder(remainder, tokens, ids)
    else:
        bpe_success = process_bpe(word, tokens, ids)
        if not bpe_success:
            tokens.append("<unknown>")
            ids.append(SPECIAL_TOKENS["<unknown>"])

def match_root(word: str) -> Tuple[str, int, str]:
    for i in range(len(word), 1, -1):
        if word[:i] in roots:
            return word[:i], roots[word[:i]], word[i:]
    return None, None, word

def process_remainder(remainder: str, tokens: List[str], ids: List[int]):
    suffix, suffix_id = match_suffix(remainder)
    if suffix:
        tokens.append(suffix)
        ids.append(suffix_id)
        remainder = remainder[len(suffix):]
        if remainder:
            process_remainder(remainder, tokens, ids)
    else:
        root, root_id, remainder = match_root(remainder)
        if root:
            tokens.append(root)
            ids.append(root_id)
            if remainder:
                process_remainder(remainder, tokens, ids)
        else:
            bpe_success = process_bpe(remainder, tokens, ids)
            if not bpe_success:
                tokens.append("<unknown>")
                ids.append(SPECIAL_TOKENS["<unknown>"])

def match_suffix(word: str) -> Tuple[str, int]:
    for i in range(len(word), 0, -1):
        if word[:i] in suffixes:
            return word[:i], suffixes[word[:i]]
    return None, None

def process_bpe(word: str, tokens: List[str], ids: List[int]) -> bool:
    i = 0
    found_any = False
    while i < len(word):
        found_match = False
        for j in range(len(word), i, -1):
            if word[i:j] in bpe_tokens:
                tokens.append(word[i:j])
                ids.append(bpe_tokens[word[i:j]])
                i = j
                found_match = True
                found_any = True
                break
        if not found_match:
            i += 1
    return found_any

# ===============================
# NEW MORPHOLOGICAL DECODE SYSTEM
# ===============================

class TurkishPhonology:
    """Turkish phonology and morphological rules"""
    
    def __init__(self):
        # Vowels
        self.vowels = set('aeiıouöü')
        self.back_vowels = set('aıou')
        self.front_vowels = set('eiöü')
        self.unrounded_vowels = set('aeıi')
        self.rounded_vowels = set('ouöü')
        
        # Consonants
        self.consonants = set('bcçdfgğhjklmnprsştyvz')
        self.hard_consonants = set('çfhkpsşt')
        self.soft_consonants = set('bccdgğjlmnrvyz')
        
        # Softening map
        self.softening_map = {'p': 'b', 'ç': 'c', 't': 'd', 'k': 'g'}
        self.hardening_map = {'b': 'p', 'c': 'ç', 'd': 't', 'g': 'k'}
        
    def get_last_vowel(self, word: str) -> Optional[str]:
        """Find the last vowel in the word"""
        for i in range(len(word) - 1, -1, -1):
            if word[i] in self.vowels:
                return word[i]
        return None
        
    def get_vowel_type(self, vowel: str) -> Dict[str, bool]:
        """Return the properties of the vowel"""
        return {
            'back': vowel in self.back_vowels,
            'front': vowel in self.front_vowels,
            'rounded': vowel in self.rounded_vowels,
            'unrounded': vowel in self.unrounded_vowels
        }

class MorphophoneticRules:
    """Turkish phonetic rules"""
    
    def __init__(self):
        self.phonology = TurkishPhonology()
    
    
    
    def _is_softening_exception(self, root: str, suffix: str) -> bool:
        """Softening exceptions"""
        exceptions = {'at', 'et', 'it', 'ot', 'ut', 'üt'}
        return root in exceptions
    
    def _is_vowel_drop_exception(self, root: str) -> bool:
        """Vowel drop exceptions"""
        exceptions = {'ara', 'kara', 'para', 'dere', 'göre'}
        return root in exceptions
    
    def _is_two_syllable(self, word: str) -> bool:
        """Check if the word is two-syllable"""
        vowel_count = sum(1 for char in word if char in self.phonology.vowels)
        return vowel_count == 2
class MorphologicalDecoder:
    """Morphological decoder"""
    
    def __init__(self):
        self.rules = MorphophoneticRules()
        
    def decode_text(self, token_ids: List[int]) -> str:
        """Main decode function"""
        if not token_ids:
            return ""
            
        result = ""
        context = {
            'current_root': None,
            'pending_uppercase': False,
            'morpheme_sequence': []
        }
        
        i = 0
        while i < len(token_ids):
            token_id = token_ids[i]
            
            # Check for unknown token
            if token_id not in reverse_dict:
                print(f"Warning: Unknown token ID: {token_id}")
                i += 1
                continue
                
            tokens = reverse_dict[token_id]
            if not tokens:
                i += 1
                continue
                
            # Check the next token (for form selection)
            next_token = None
            if i + 1 < len(token_ids):
                next_id = token_ids[i + 1]
                if next_id in reverse_dict and reverse_dict[next_id]:
                    next_token = reverse_dict[next_id][0]
            
            # Determine token type
            token_type = None
            if token_id in roots.values():
                token_type = 'root'
            elif token_id in suffixes.values():
                token_type = 'suffix'
            
            # Choose the correct form
            token = choose_correct_form(tokens, next_token, context, token_type)
            
            # Process special tokens
            processed_text = self._process_special_tokens(token, context)
            if processed_text is not None:
                result += processed_text
                i += 1
                continue
            
            # Morphological processing
            processed_text = self._process_morphological_token(
                token, token_id, context, token_ids, i
            )
            
            if processed_text:
                result += processed_text
                
            i += 1
            
        return result
    
    def _process_special_tokens(self, token: str, context: Dict) -> Optional[str]:
        """Process special tokens"""
        if token == "<space>":
            context['current_root'] = None
            context['morpheme_sequence'] = []
            return " "
        elif token == "<newline>":
            context['current_root'] = None
            context['morpheme_sequence'] = []
            return "\n"
        elif token == "<tab>":
            return "\t"
        elif token == "<uppercase>":
            context['pending_uppercase'] = True
            return ""
        elif token == "<unknown>":
            return ""  # Unsupported character
            
        return None
    
    def _process_morphological_token(self, token: str, token_id: int, 
                                   context: Dict, token_ids: List[int], 
                                   current_index: int) -> str:
        """Morfolojik token işleme"""
        
        # Determine token type
        if token_id in roots.values():
            return self._process_root_token(token, context)
        elif token_id in suffixes.values():
            return self._process_suffix_token(token, context, token_ids, current_index)
        else:
            return self._process_bpe_token(token, context)
    
    def _process_root_token(self, root: str, context: Dict) -> str:
        """Process root token"""
        context['current_root'] = root
        context['morpheme_sequence'] = [root]
        
        # Check for uppercase
        if context['pending_uppercase']:
            context['pending_uppercase'] = False
            return turkish_capitalize(root)
            
        return root
    
    def _process_suffix_token(self, suffix: str, context: Dict, 
                            token_ids: List[int], current_index: int) -> str:
        """Process suffix token with phonetic rules"""
        if not context['current_root']:
            return suffix
            
        root = context['current_root']
        
        # Apply Turkish phonetic rules
        processed_suffix = self._apply_phonetic_transformations(root, suffix)
        
        full_word = root + processed_suffix
        context['current_root'] = full_word
        context['morpheme_sequence'].append(processed_suffix)
        
        # Return only the processed suffix (root already added)
        return processed_suffix
    
    def _apply_phonetic_transformations(self, root: str, suffix: str) -> str:
        """Apply Turkish phonetic transformation rules"""
        if not root or not suffix:
            return suffix
        
        # Set of Turkish phonemes
        vowels = set('aeiıouöü')
        back_vowels = set('aıou')
        front_vowels = set('eiöü')
        
        def get_last_vowel(word: str) -> str:
            """Get the last vowel in word"""
            for i in range(len(word) - 1, -1, -1):
                if word[i] in vowels:
                    return word[i]
            return None
        
        def apply_vowel_harmony_to_suffix(suffix: str, root: str) -> str:
            """Apply vowel harmony rules to suffix"""
            last_vowel = get_last_vowel(root)
            if not last_vowel:
                return suffix
            
            result = suffix
            
            # Major vowel harmony (a/e)
            if last_vowel in back_vowels:
                result = result.replace('e', 'a')
            else:
                result = result.replace('a', 'e')
            
            # Minor vowel harmony (ı/i/u/ü)
            if last_vowel in {'a', 'ı'}:
                result = result.replace('i', 'ı').replace('u', 'ı').replace('ü', 'ı')
            elif last_vowel in {'o', 'u'}:
                result = result.replace('i', 'u').replace('ı', 'u').replace('ü', 'u')
            elif last_vowel in {'e', 'i'}:
                result = result.replace('ı', 'i').replace('u', 'i').replace('ü', 'i')
            elif last_vowel in {'ö', 'ü'}:
                result = result.replace('i', 'ü').replace('ı', 'ü').replace('u', 'ü')
            
            return result
        
        def add_buffer_consonant(root: str, suffix: str) -> str:
            """Add buffer consonant (y/s) between vowels"""
            if (root and suffix and 
                root[-1] in vowels and suffix[0] in vowels):
                
                # For possessive suffixes, add 's'
                if suffix in ['i', 'ı', 'u', 'ü'] and len(root) > 2:
                    return 's' + suffix
                # For other cases, add 'y'
                else:
                    return 'y' + suffix
            
            return suffix
        
        # Apply transformations in order
        transformed_suffix = suffix
        
        # 1. Add buffer consonant if needed
        transformed_suffix = add_buffer_consonant(root, transformed_suffix)
        
        # 2. Apply vowel harmony
        transformed_suffix = apply_vowel_harmony_to_suffix(transformed_suffix, root)
        
        return transformed_suffix
    
    def _process_bpe_token(self, token: str, context: Dict) -> str:
        """Process BPE token"""
        if context['pending_uppercase']:
            context['pending_uppercase'] = False
            return turkish_capitalize(token)
            
        return token
    
    def _apply_phonetic_rules(self, root: str, suffix: str, 
                            next_suffix: Optional[str] = None) -> str:
        """Apply phonetic rules sequentially"""
        
        # 1. Consonant softening
        processed_root = self.rules.apply_consonant_softening(root, suffix)
        
        # 2. Vowel drop
        processed_root = self.rules.apply_vowel_drop(processed_root, suffix)
        
        return processed_root
    
    def _apply_suffix_rules(self, root: str, suffix: str, 
                          next_suffix: Optional[str] = None) -> str:
        """Apply phonetic rules on the suffix"""
        
        # 1. Vowel harmony
        processed_suffix = self.rules.apply_vowel_harmony(root, suffix)
        
        # 2. Consonant assimilation
        processed_suffix = self.rules.apply_consonant_assimilation(root, processed_suffix)
        
        # 3. Buffer consonant
        processed_suffix = self.rules.apply_buffer_consonant(root, processed_suffix)
        
        return processed_suffix

# Main decode function
def morphological_decode(token_ids: List[int]) -> str:
    """Morphological decode"""
    decoder = MorphologicalDecoder()
    return decoder.decode_text(token_ids)