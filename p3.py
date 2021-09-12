# Import libraries
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os
import time
from time import sleep

# some global variables that need to change as we run the program
end_of_game = None  # set if the user wins or ends the game

# DEFINE THE PINS USED HERE
LED_value = [11, 13, 15]
LED_accuracy = 32
btn_submit = 16
btn_increase = 18
#buzzer = None
buzzer = 33
eeprom = ES2EEPROMUtils.ES2EEPROM()

user_guess = 0
randomized_value = 0
number_of_guesses = 0
mode = None
p = None
q = None


# Print the game banner
def welcome():
    os.system('clear')
    print("  _   _                 _                  _____ _            __  __ _")
    print("| \ | |               | |                / ____| |          / _|/ _| |")
    print("|  \| |_   _ _ __ ___ | |__   ___ _ __  | (___ | |__  _   _| |_| |_| | ___ ")
    print("| . ` | | | | '_ ` _ \| '_ \ / _ \ '__|  \___ \| '_ \| | | |  _|  _| |/ _ \\")
    print("| |\  | |_| | | | | | | |_) |  __/ |     ____) | | | | |_| | | | | | |  __/")
    print("|_| \_|\__,_|_| |_| |_|_.__/ \___|_|    |_____/|_| |_|\__,_|_| |_| |_|\___|")
    print("")
    print("Guess the number and immortalise your name in the High Score Hall of Fame!")


# Print the game menu
def menu():
    global end_of_game
    global randomized_value
    global number_of_guesses
    global user_guess
    global mode
    
    
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
        
    elif option == "P":
        os.system('clear')
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        print("Your current guess is " + user_guess)
        randomized_value = generate_number() #The number they'll try guess
        number_of_guesses = 0
        while not end_of_game:
            pass
        user_guess = 0
        number_of_guesses = 0
        end_of_game = False
        sleep(0.01)

    elif option == "Q":
        print("Come back soon!")
        exit()
        
    else:
        print("Invalid option. Please select a valid one!")


def display_scores(count, raw_data):
    # print the scores to the screen in the expected format
    print("There are {} scores. Here are the top 3!".format(count))
    # print out the scores in the required format
    for i in range(3 if count > 3 else count):
        print("{} - {} took {} guesses".format(i+1, (raw_data[i])[0], (raw_data[i])[1]))
    pass


# Setup Pins
def setup():
    global p
    global q
    
    # Setup board mode
    GPIO.setmode(GPIO.BOARD)

    # Setup regular GPIO
    for i in range(len(LED_value)):
        GPIO.setup(LED_value[i], GPIO.OUT)
        GPIO.output(LED_value[i], False)
        

    
    ## Buttons
    GPIO.setup(btn_submit, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(btn_increase, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    ## LEDs for user guess value
    GPIO.setup(LED_value, GPIO.OUT)
    GPIO.output(LED_value, GPIO.LOW)

    ## LED for accuracy of guess
    GPIO.setup(LED_accuracy, GPIO.OUT)
    #GPIO.output(LED_accuracy, GPIO.LOW)

    ## Setting up the buzzer
    GPIO.setup(buzzer, GPIO.OUT)
    #GPIO.output(buzzer, GPIO.LOW)

    # Setup PWM channels
   
    p = GPIO.PWM(LED_accuracy, 10000)
    q = GPIO.PWM(buzzer, 1)

    #p.start(0)

    #duty_cycle_buzzer = 50
    #q.ChangeDutyCycle(duty_cycle_buzzer)

    # Setup debouncing and callbacks
    #GPIO.add_event_callback(btn_submit, btn_guess_pressed, bouncetime=200)
    GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=300)
    GPIO.add_event_detect(btn_increase, GPIO.FALLING, callback=btn_increase_pressed, bouncetime=300)


    #global randomized_value

    #randomized_value = generate_number()
    #print(randomized_value)
    pass


# Load high scores
def fetch_scores():
    global eeprom
    # get however many scores there are
    score_count = eeprom.read_byte(0)
    scores = []

    if score_count > 0:
        rawData = eeprom.read_block(1,score_count*4)
        #Get scores
        for i in range(0, score_count*4, 4):
            username = ''
            # Convert to char
            for j in range(3):
                username += chr(rawData[i+j])
            # Add to array
            scores.append([username, rawData[i + 3]])
    
    # return back the results
    return score_count, scores


# Save high scores
def save_scores(username, newscore):
    global eeprom
    # fetch scores 
    s_count, ss = fetch_scores()

    # include new score
    if not([username, newscore] in ss):
        ss.append([username, newscore])
        # sort
        ss.sort(key=lambda x: x[1])
        # update total amount of scores
        s_count += 1
        eeprom.write_block(0, [4])
        # write new scores
        for a, score in enumerate(ss):
            outdata = []
            # fetch scores
            for letter in score[0]:
                outdata.append(ord(letter))
            outdata.append(score[1])
            eeprom.write_block(a+1, outdata)
    pass


# Generate guess number
def generate_number():
    return random.randint(0, pow(2, 3)-1)


# Increase button pressed
def btn_increase_pressed(channel):
    # Increase the value shown on the LEDs
    # You can choose to have a global variable store the user's current guess, 
    # or just pull the value off the LEDs when a user makes a guess

    global user_guess
    global mode
    
    if mode != 'P':
        return
    
    binary_rep = list()

    #global p

    user_guess += 1
    print("Current guess: " + user_guess)
    user_guess = user_guess % 8

    temp = user_guess
    binary_rep.append(temp%2)

    for i in range(2):

        temp = temp // 2
        binary_rep.append(temp%2)

    if binary_rep[0] == 1:

        GPIO.output(LED_value[0], GPIO.HIGH)

    else:

        GPIO.output(LED_value[0], GPIO.LOW)

    if binary_rep[1] == 1:

        GPIO.output(LED_value[1], GPIO.HIGH)

    else:

        GPIO.output(LED_value[1], GPIO.LOW)

    if binary_rep[2] == 1:

        GPIO.output(LED_value[2], GPIO.HIGH)

    else:

        GPIO.output(LED_value[2], GPIO.LOW)
        
    pass


# Guess button
def btn_guess_pressed(channel):
    # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
    # Compare the actual value with the user value displayed on the LEDs
    # Change the PWM LED
    # if it's close enough, adjust the buzzer
    # if it's an exact guess:
    # - Disable LEDs and Buzzer
    # - tell the user and prompt them for a name
    # - fetch all the scores
    # - add the new score
    # - sort the scores
    # - Store the scores back to the EEPROM, being sure to update the score count

    global user_guess
    global randomized_value
    global p
    global q
    global number_of_guesses
    global mode
    global end_of_game

    if mode != 'P':
        return

    presstimestart = time.time()
    while GPIO.input(channel) == GPIO.LOW:
        time.sleep(0.005)
    presstimeend = time.time()
    timepressed = presstimeend - presstimestart
    
    if timepressed > 2:
        end_of_game = True
        mode = ''
        os.system('clear')
        return
        
    print("You guessed " + user_guess)
    
    if user_guess == randomized_value: #CORRECT
        print('CORRECT ANSWER! YAAAAAAY!')
        username = input('Enter your name:\n')[0:3]
        
        save_scores(username, number_of_guesses)
        
        os.system('clear')
        mode =''
        end_of_game = True
    else: #INCORRECT
    accuracy_leds()
    if 1 <= abs(user_guess - randomized_value) <= 3:
        pass
        trigger_buzzer()
    
    number_of_guesses += 1
    print("Incorrect Answer Boet, Tough Luck, Try Again Next Time")
    
    sleep(2)
    p.stop()
    q.stop()
    print("Current guess is " + user_guess)
    pass

# LED Brightness
def accuracy_leds():
    # Set the brightness of the LED based on how close the guess is to the answer
    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%

    global user_guess
    global randomized_value
    global p

    if user_guess < randomized_value_value:
        close = (user_guess/randomized_value)*100
    else:
        close = ((8-user_guess)/(8-randomized_value))*100

    p.start(close)

    pass

# Sound Buzzer
def trigger_buzzer():
    # The buzzer operates differently from the LED
    # While we want the brightness of the LED to change(duty cycle), we want the frequency of the buzzer to change
    # The buzzer duty cycle should be left at 50%
    # If the user is off by an absolute value of 3, the buzzer should sound once every second
    # If the user is off by an absolute value of 2, the buzzer should sound twice every second
    # If the user is off by an absolute value of 1, the buzzer should sound 4 times a second

    global q
    global user_guess
    global randomized_value

    absolute_value = abs(user_guess - randomized_value)

    if absolute_value == 3:

        q.start(50)
        q.ChangeFrequency(1)

    elif absolute_value == 2:

        q.start(50)
        q.ChangeFrequency(2)

    elif absolute_value == 1:

        q.start(50)
        q.ChangeFrequency(4)

    else:

        q.stop()

    pass


if __name__ == "__main__":
    try:
        # Call setup function
        setup()
        welcome()
        if eeprom.read_byte(0) == 0:
            sleep(0.01)
            eeprom.clear(2048)
            sleep(0.01)
            eeprom.populate_mock_scores()
        while True:
            menu()
            pass
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
