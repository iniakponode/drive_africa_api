import random

def player1():
  target_num=random.randint(-100, 100)
  print("Target number: ", target_num)

def player1():
    target_number=random.randint(-100, 100)
    print(target_number)
    #return target_number


def player2():
    
    guess_number=int(input("Please guess the number: "))
    print(guess_number)
    return guess_number


def check_guess(guess_number, target_number):
    
    if guess_number<target_number:
      print("Higher")
      return "higher"
    elif guess_number>target_number:
      print("Lower")
      return "lower"
    else:
      print("Correct")
      return "correct"

def main():
  target_number=player1()
  guess_number=0
  round=5

  for num in range(5):
      guess_number=player2(guess_number=int(input("Please guess the number: ")))
      #guess_count +=1

    #result=check_guess(guess_number, target_number)
      if result=="correct":
        print(f"You have guessed the correct number in: {num} attempts. ")
        break
  else:
    print(f"Player2 failed the guess number in: {num} rounds attempt, try again")