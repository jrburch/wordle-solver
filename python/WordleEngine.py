import os
import string

class WordleEngine:
   def __init__(self):
      self.letters = string.ascii_lowercase
      self.LoadWords("words.txt")

   def LoadWords(self, filename):
      self.potential_words = []
      if not os.path.exists(filename): return
      self.potential_words = [l.strip() for l in open(filename, 'r').readlines()]
            
   def MatchPattern(self, word, pattern):
      for i, entry in enumerate(pattern):
         if entry['correct'] and word[i] != entry['letter']: return False
         if entry['included']:
            found = False
            for j, letter in enumerate(word):
               if entry['letter'] == letter and not entry['correct'] and i != j:
                  found = True
            if not found:
               return False
      return True
            
   def ParsePattern(self, patternStr):
      pattern = []
      for i, letter in enumerate(patternStr):
         pattern.append({ 'letter'   : letter.lower(),
                          'correct'  : str(letter).isupper(),
                          'included' : str(letter).isalpha() and not str(letter).isupper() })
      return pattern
 
   def TrimLetters(self, guess, pattern):
      for letter in guess:
         if letter not in [e['letter'] for e in pattern]:
            self.letters = self.letters.replace(letter,"")
            
   def TrimWords(self, pattern):
      bad_words = []
      for word in self.potential_words:
         valid = self.MatchPattern(word, pattern)
         if valid:
            for letter in word:
               if letter not in self.letters:
                  valid = False
         if not valid: 
            bad_words.append(word)
      for word in bad_words:
         self.potential_words.remove(word)
        
   def GetSuggestion(self):
      letter_heatmap = {}
      score = {}
      score_total = 0
      let_total = 0
      for word in self.potential_words:
         for i, letter in enumerate(word):
            if letter not in letter_heatmap: letter_heatmap[letter] = [0] * len(word)
            letter_heatmap[letter][i] += 1
            let_total += 1
      for let in letter_heatmap:
         for pos in range(len(letter_heatmap[let])):
            letter_heatmap[let][pos] /= let_total
      for word in self.potential_words:
         s = 0
         for i, letter in enumerate(word):
            s += letter_heatmap[letter][i] / word.count(letter)
         score[word] = s
         score_total += s
      score = [(k,v*100/score_total) for (k,v) in sorted(score.items(), key=lambda item: item[1])[::-1]]
      if len(score) > 9:
         other_score = sum([s for (sug, s) in score[9:]])
         score = score[:9]
         score.append((".....",other_score))
      else:
         score.append((".....",0.0))
      return score

   def PlayGuess(self, guess, pattern):
      pattern = self.ParsePattern(pattern)
      self.TrimLetters(guess.lower(), pattern)
      self.TrimWords(pattern)

   def Active(self):
      return len(self.potential_words) > 1
      