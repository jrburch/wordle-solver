import os
import sys
import tkinter as tk
import tkinter.font as tkfont
import tkinter.simpledialog as tkdialog
import WordleEngine

def clone_widget(widget, master=None):
    """
    Create a cloned version of a widget

    Parameters
    ----------
    widget : tkinter widget
        tkinter widget that shall be cloned.
    master : tkinter widget, optional
        Master widget onto which cloned widget shall be placed. If None, same master of input widget will be used. The
        default is None.

    Returns
    -------
    cloned : tkinter widget
        Clone of input widget onto master widget.

    """
    # Get main info
    parent = master if master else widget.master
    cls = widget.__class__

    # Clone the widget configuration
    cfg = {key: widget.cget(key) for key in widget.configure()}
    cloned = cls(parent, **cfg)

    # Clone the widget's children
    for child in widget.winfo_children():
        child_cloned = clone_widget(child, master=cloned)
        if child.grid_info():
            grid_info = {k: v for k, v in child.grid_info().items() if k not in {'in'}}
            child_cloned.grid(**grid_info)
        elif child.place_info():
            place_info = {k: v for k, v in child.place_info().items() if k not in {'in'}}
            child_cloned.place(**place_info)
        else:
            pack_info = {k: v for k, v in child.pack_info().items() if k not in {'in'}}
            child_cloned.pack(**pack_info)

    return cloned
   

class Word:
   STATE_COLOR   = { 'correct'     : "green",
                     'wrong_place' : "yellow",
                     'incorrect'   : "gray" }
   STATE_PATTERN = { 'correct'     : lambda c: c.upper(),
                     'wrong_place' : lambda c: c.lower(),
                     'incorrect'   : lambda c: '.' }

   def __init__(self, parent, root_frame):
      self.parent = parent    
      
      self.letters_frame = tk.Frame(root_frame)
      self.letters_frame.pack(side="top", fill="x")
      
      self.letters = []
      for i in range(5):
         b = tk.Button(self.letters_frame, text='.',
                       font=self.parent.parent.font, command=lambda i=i: self.OnLetterSelect(i))
         b.pack(side="left")
         self.letters.append({'button': b, 'state': ''})      

   def SetWord(self, word):
      # Update letters
      for i, c in enumerate(word.upper()):
         self.letters[i]['button']["text"] = c            
         self.SetLetterState(i, 'incorrect')

      # Enable/disablesubmit_button based on validty
      state = "normal" if self.Valid() else "disabled"
      for b in self.letters: b['button']['state'] = state

   def OnLetterSelect(self, i):
      if self.letters[i]['state'] == 'incorrect':
         state = 'wrong_place'
      elif self.letters[i]['state'] == 'wrong_place':
         state = 'correct'
      else:
         state = 'incorrect'
      self.SetLetterState(i, state)

   def SetLetterState(self, i, state):
      self.letters[i]['state'] = state
      self.letters[i]['button']['bg'] = self.STATE_COLOR[state]
      self.letters[i]['button']['activebackground'] = self.letters[i]['button']['bg']

   def Valid(self):
      return self.GetWord().isalpha()

   def GetWord(self):
      return ''.join([l['button']['text'] for l in self.letters])

   def GetPattern(self):
      str = ''
      for l in self.letters:
         str += self.STATE_PATTERN[l['state']](l['button']['text'])
      return str

   def Enable(self, enable):
      for l in self.letters:
         l['button']['state'] = "normal" if enable else "disabled"
      

class Guess:
   
   def __init__(self, parent, root_frame):
      self.parent = parent    
      
      self.CreateWord(root_frame)
      self.CreatSubmitButton(root_frame)
      self.CreateResetButton(root_frame)
      
   def CreateWord(self, root_frame):
      self.word_frame = tk.Frame(root_frame)
      self.word_frame.pack(side="top", fill="x")
      
      self.word = Word(self, self.word_frame)

   def CreatSubmitButton(self, root_frame):
      self.submit_frame = tk.Frame(root_frame)
      self.submit_frame.pack(side="top", fill="x")
      
      b = tk.Button(self.submit_frame, text='SUBMIT', font=self.parent.font, command=self.OnSubmit)
      b.pack(side="bottom", fill="x")
      self.submit_button = b

   def CreateResetButton(self, root_frame):
      self.reset_frame = tk.Frame(root_frame)
      self.reset_frame.pack(side="bottom", fill="x")

      b = tk.Button(self.reset_frame, text='RESET', activebackground="red", font=self.parent.font, command=self.OnReset)
      b.pack(side="bottom", fill="x")
      self.reset_button = b

   def SetGuess(self, word):
      self.word.SetWord(word)

      # Update submit button
      self.submit_button['bg'] = "#90EE90" if self.word.Valid() else "#707070"
      self.submit_button['activebackground'] = self.submit_button['bg']
      self.submit_button['state'] = state = "normal" if self.word.Valid() else "disabled"

   def OnSubmit(self):
      self.word.Enable(False)
      self.parent.OnSubmitGuess(self.word)
      self.word.Enable(True)

   def OnReset(self):
      self.parent.OnReset()

   def GuessValid(self):
      return self.word.Valid()

class History:
   def __init__(self, parent, root_frame):
      self.parent = parent
      self.root_frame = root_frame

      self.CreateHistory()
   
   def CreateHistory(self):
      self.history_frame = tk.Frame(self.root_frame)
      self.history_frame.pack(side="left", fill="both")

   def AddGuess(self, guess):
      cloned_word = clone_widget(guess.letters_frame, self.history_frame) 
      cloned_word.pack()

   def Reset(self):
      self.history_frame.destroy()
      self.CreateHistory()

class WordList:
   def __init__(self, parent, root_frame):
      self.parent = parent
      self.root_frame = root_frame
      self.wordlist = tk.Listbox(root_frame)
      self.wordlist.bind('<<ListboxSelect>>', self.OnSuggestionSelect)
      self.wordlist.configure(font = parent.font)
      self.wordlist.pack(fill="both", expand=True)

   def SetSuggestions(self, suggestions):
      self.wordlist.delete(0,tk.END)
      for i, (sug, prob) in enumerate(suggestions):
         self.wordlist.insert(i+1, "{} ({:.4f}%)".format(sug.upper(), prob))
      

   def OnSuggestionSelect(self, evt):
      # Note here that Tkinter passes an event object to onselect()
      w = evt.widget
      index = int(w.curselection()[0])
      value = w.get(index)
      word = value[:5]

      if word == '.....':
         word = tkdialog.askstring(title="", prompt="Word:")

      if len(word) == 5 and word.isalpha():
         self.parent.OnSuggestionSelect(word.upper())
                                       

class WordleGUI:
   def __init__(self):
      self.CreateGUI()
      self.OnReset()

   def CreateGUI(self):
      self.CreateFrame()
      
      self.CreateWordList()
      self.CreateHistory()
      self.CreateGuessBox()

   def CreateFrame(self):
      self.root = tk.Tk()
      self.root.wm_title("Wordle cheater")

      # Word list
      self.word_list_frame = tk.Frame(self.root)
      self.word_list_frame.pack(side="left", fill="both", expand=True)

      # History
      self.history_frame = tk.Frame(self.root)
      self.history_frame.configure(borderwidth=2)
      self.history_frame.pack(side="top")

      # Guess
      self.guess_frame = tk.Frame(self.root)
      self.guess_frame.pack(side="bottom")

      # Creat font
      self.font = tkfont.Font(family="Courier", size=20)
   
   def CreateWordList(self):
      self.word_list = WordList(self, self.word_list_frame)

   def CreateHistory(self):
      self.history = History(self, self.history_frame)

   def CreateGuessBox(self):
      self.guess = Guess(self, self.guess_frame)

   def OnSuggestionSelect(self, word):
      self.guess.SetGuess(word)

   def OnSubmitGuess(self, guess):
      self.history.AddGuess(guess)
      self.PlayGuess(guess.GetWord(), guess.GetPattern())

   def OnReset(self):
      self.engine = WordleEngine.WordleEngine()
      self.history.Reset()
      self.PrintSuggestions()

   def PrintSuggestions(self):
      # GUI
      suggestions = self.engine.GetSuggestion()
      self.word_list.SetSuggestions(suggestions)
      self.guess.SetGuess(suggestions[0][0])

      # Command line
      for (sug, prob) in self.engine.GetSuggestion():
         print("  {} ({:.4f}%)".format(sug.upper(), prob))

   def PlayGuess(self, guess, pattern):
      self.engine.PlayGuess(guess, pattern)
      self.PrintSuggestions()
      
   def Play(self):
      self.root.mainloop()
      
