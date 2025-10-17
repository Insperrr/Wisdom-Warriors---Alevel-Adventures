
import pygame 
import sys
import os
import sqlite3
import re
import pygame_gui.ui_manager
import button 
import pygame_gui
import random
import datetime
import math 
from collections import deque


os.chdir(os.path.dirname(os.path.abspath(__file__)))

SCREEN_WIDTH, SCREEN_HEIGHT = (1280, 720)
FPS = 60

def wrap_text(text, font, max_width):
    # Split the input text into individual words
    words = text.split(' ')
    lines = []           # List to store each line of wrapped text
    current_line = ""     # String to build the current line
    
    # Loop through each word to build lines within the max_width limit
    for word in words:
        # Add the word to the current line (with a space if necessary)
        test_line = current_line + (word if current_line == "" else " " + word)
        
        # Measure the width of the test_line
        text_width, _ = font.size(test_line)
        
        if text_width > max_width:
            # If the line is too long, add the current line to lines
            lines.append(current_line)
            current_line = word  # Start a new line with the current word
        else:
            # Otherwise, keep adding words to the current line
            current_line = test_line

    # After the loop, add any leftover text as a final line
    if current_line:
        lines.append(current_line)

    # Combine all lines into one string, separated by newline characters
    final_line = ""
    for line in lines:
        final_line = final_line + line + "\n"

    return final_line

class BaseCharacter:
    def __init__(self):
        self.health = 100
        self.character = None


class PlayerData():
    def __init__(self):
        super().__init__()  
        # Initialize basic user data attributes
        self.username = None           # Username of the player
        self.user_id = None             # Unique ID associated with the player (from database)
        
        # Structure to store player's high scores by character, subject, and topic
        self.high_score = {
            "sonic": {
                "computer_science": {
                    "fundamentals_of_data_representation": 0,
                    "fundamentals_of_computer_systems": 0
                }
            }
        }
        
        self.logged_in = False          # Boolean to check if a user is currently logged in

    def fetch_high_score(self, character, subject, topic):
        """
        Fetches the high score for a specific character, subject, and topic from the database.
        Updates the local high_score dictionary with the value.
        """
        # Connect to the local SQLite database
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()

        # Execute a query to fetch the high score
        self.cursor.execute(f'''SELECT high_score
                                FROM HighScore
                                JOIN Characters ON Characters.character_id = HighScore.character_id
                                JOIN Topic ON Topic.topic_id = HighScore.topic_id
                                WHERE user_id = ? AND character_name = ? AND topic_text = ? ''',
                                (self.user_id, character, topic))
        
        # Retrieve the result
        temp = self.cursor.fetchone()

        # If a high score exists, update it in the local dictionary
        if not(temp == None):
            self.high_score[character][subject][topic] = temp[0]
        # If no high score exists but the user is logged in, initialize to 0
        elif self.logged_in:
            self.high_score[character][subject][topic] = 0

        # Always close the connection after the operation
        self.connection.close()

        

class PlayerInstance(BaseCharacter):
    def __init__(self):
        # Initialize all player-specific attributes
        self.subject = None                 # Selected subject (e.g., "Maths", "Science")
        self.topic = None                   # Selected topic within the subject
        self.character = None               # Selected character/avatar
        self.score = 0                      # Player's current score
        self.combo = 0                      # Number of correct answers in a row
        self.new_high_score = False         # Whether the player achieved a new high score
        self.correct_questions = 0          # Total number of correct questions answered

    def reset_player_instance(self):
        """
        Fully reset all attributes related to the player,
        including subject, topic, character, and performance stats.
        """
        self.subject = None
        self.topic = None
        self.character = None
        self.score = 0
        self.combo = 0
        self.new_high_score = False
        self.correct_questions = 0

    def reset_stats(self):
        """
        Reset only the player's performance stats (score, combo, high score flag),
        but keep subject, topic, and character selection unchanged.
        """
        self.score = 0
        self.combo = 0
        self.new_high_score = False




class Player:
    def __init__(self):
        # Initialize player data (e.g., username) and game instance (e.g., selected character and topic)
        self.player_data = PlayerData()
        self.player_instance = PlayerInstance()

    def has_high_score(self):
        # Get the user ID based on the player's username
        user_id = get_user_id(self.player_data.username)

        # Use a context manager to safely handle the database connection
        with sqlite3.connect("main.db") as connection:
            cursor = connection.cursor()

            # Execute a query to count matching high score records
            cursor.execute('''
                SELECT COUNT(*) 
                FROM HighScore
                JOIN Characters ON Characters.character_id = HighScore.character_id
                JOIN Topic ON Topic.topic_id = HighScore.topic_id
                WHERE user_id = ? AND character_name = ? AND topic_text = ? 
            ''', (
                user_id,
                self.player_instance.character,
                self.player_instance.topic
            ))

            count = cursor.fetchone()[0]

        # Return True if a record exists, otherwise False
        return count > 0


class BaseScreen: 
    def __init__(self): 
        # Load the background image for the screen 
        self.background = pygame.image.load("Assets/Background.png") 
         
        # Initialize fonts for text rendering 
        self.big_font = pygame.font.Font("Assets/Font1.ttf", 96)  # Big font for headings 
        self.small_font = pygame.font.Font("Assets/Font1.ttf", 20)  # Smaller font for other text 
         
        # Create a back button with an image and a size factor of 0.25 
        self.back_button = button.Button(10, 0, pygame.image.load("Assets/back.png"), 0.25) 
        # Position the back button in the bottom-left corner of the screen 
        self.back_button.change_position(10, SCREEN_HEIGHT, "bottomleft") 
         
        # Initialize the ButtonManager to handle button logic 
        self.all_buttons = button.ButtonManager() 
 
    def handle_events(self, events, screen): 
        # This method is left empty here, meant to be overridden by subclasses for specific event handling 
        pass 
 
    def update(self, dt): 
        # This method is left empty here, meant to be overridden by subclasses for specific updates per frame 
        pass 
 
    def render(self, screen): 
        # This method is left empty here, meant to be overridden by subclasses for specific rendering logic 
        pass 

class MainMenuScreen(BaseScreen):
    def __init__(self, player):
        super().__init__()

        # Load fonts
        self.medium_font = pygame.font.Font("Assets/Font1.ttf", 60)
        self.small_font = pygame.font.Font("Assets/Font1.ttf", 30)

        # Load and position the logo
        self.logo = pygame.image.load("Assets/logo.png")
        self.logo_rect = self.logo.get_frect(topleft=(60, -20))

        # Create and set up the START button
        self.start_text = self.big_font.render("START", True, (255, 255, 255))
        self.start_button = button.Button(0, 0, self.start_text)
        self.start_button.change_position(SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + 25, "center")
        self.all_buttons.add_button(self.start_button, lambda: game.change_screen("character_select_screen"))

        # Create and set up the LOGIN and REGISTER buttons
        self.login_text = self.medium_font.render("LOGIN", True, "white")
        self.register_text = self.medium_font.render("REGISTER", True, "white")

        self.register_button = button.Button(0, 0, self.register_text, 0.8)  # Slightly smaller size
        self.login_button = button.Button(0, 0, self.login_text)

        self.register_button.change_position(SCREEN_WIDTH // 4, (SCREEN_HEIGHT // 4) * 2.7, "center")
        self.login_button.change_position((SCREEN_WIDTH // 4) * 3, (SCREEN_HEIGHT // 4) * 2.7, "center")

        self.all_buttons.add_button(self.register_button, lambda: game.change_screen("register_screen"))
        self.all_buttons.add_button(self.login_button, lambda: game.change_screen("login_screen"))

        # Store reference to the player
        self.player = player

        # Time counter for animation
        self.time_elapsed = 0

    def update(self, dt):
        # Update the elapsed time
        self.time_elapsed += dt

        # Logo floating animation using sine wave
        amplitude = 1
        frequency = 0.25
        self.logo_rect.y += (amplitude * math.sin(self.time_elapsed * frequency * 2 * math.pi))

        # If player is logged in, prepare welcome message
        if self.player.player_data.logged_in:
            self.welcome_text = self.medium_font.render(
                f"Welcome back {self.player.player_data.username}!", True, "green"
            )
            self.welcome_text_rect = self.welcome_text.get_frect(center=(SCREEN_WIDTH // 2, 700))

        # Reset player instance for fresh state
        self.player.player_instance.reset_player_instance()

    def handle_events(self, events, screen):
        # Pass all events to the button manager
        self.all_buttons.handle_input(events)

    def render(self, screen):
        # Draw the background
        screen.blit(self.background, (0, 0))

        # Draw the animated logo
        screen.blit(self.logo, self.logo_rect)

        # If logged in, draw the welcome message
        if self.player.player_data.logged_in:
            screen.blit(self.welcome_text, self.welcome_text_rect)

        # Draw all buttons
        self.all_buttons.render_buttons(screen)

class CharacterSelectScreen(BaseScreen): 
    def __init__(self, screen, player): 
        # Initialize the parent class (BaseScreen) 
        super().__init__() 
         
        # Dictionary to hold the character names and their descriptions 
        self.character_texts = { 
            "sonic": "Sonic - The Fastest Thing Alive", 
            "kirby": "Kirby - The Star Warrior" 
        } 
         
        # Fetch the character descriptions from the database 
        self.get_character_descriptions() 
         
        # Create the button for selecting Sonic, with an icon for the character 
        self.sonic_icon_button = button.Button(10, 200, pygame.image.load("Assets/sonic_icon.jpg"), 0.4) 
         
        # Add buttons for navigating back to the main menu and selecting the character 
        self.all_buttons.add_button(self.back_button, lambda: game.change_screen("main_menu")) 
        self.all_buttons.add_button(self.sonic_icon_button, 
                                    lambda: self.character_selected("sonic"), 
                                    None, lambda: self.display_text(screen, "sonic")) 
         
        # Create heading text for the character selection screen 
        self.heading_text = self.big_font.render("Choose Your Character:", True, "black") 
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH // 2, 50)) 
         
        # Initialize the current text (description) to None 
        self.current_text = None 
         
        # Store the player instance 
        self.player = player 
 
    def get_character_descriptions(self): 
        # Connect to the database to retrieve character descriptions 
        self.connection = sqlite3.connect("main.db") 
        self.cursor = self.connection.cursor() 
         
        # Fetch all character names and their descriptions from the database 
        self.cursor.execute('SELECT character_name, character_description FROM Characters') 
        self.character_descriptions = {} 
         
        # Populate the character descriptions dictionary with the results 
        for character_name, character_description in self.cursor.fetchall(): 
            self.character_descriptions[character_name] = character_description 
         
        # Close the database connection 
        self.connection.close() 
 
    def display_text(self, screen, character): 
        # Set the positions of the character description text on the screen 
        self.character_texts_positions = {"sonic": (20, 500)} 
         
        # Get the description text for the selected character and render it 
        self.current_text = self.small_font.render(self.character_texts.get(character), True, "white") 
         
        # Position the text on the screen based on the character selected 
        self.current_text_rect = self.current_text.get_rect(topleft=self.character_texts_positions[character]) 
 
    def character_selected(self, character): 
        # Set the selected character for the player 
        self.player.player_instance.character = character 
         
        # Change the screen to the subject selection screen after a character is chosen 
        game.change_screen("subject_select_screen") 
     
    def handle_events(self, events, screen): 
        # Handle input events for all buttons on the screen 
        self.all_buttons.handle_input(events) 
 
    def render(self, screen): 
        # Draw the background for the screen 
        screen.blit(self.background, (0, 0)) 
         
        # Draw the heading text for character selection 
        screen.blit(self.heading_text, self.heading_text_rect) 
         
        # Render all buttons on the screen 
        self.all_buttons.render_buttons(screen) 
         
        # If a character description is selected, render it on the screen 
        if self.current_text: 
            screen.blit(self.current_text, self.current_text_rect) 
         
        # Reset the current text to None after rendering 
        self.current_text = None 

class SubjectSelectScreen(BaseScreen): 
    def __init__(self, player): 
        super().__init__()  # Call parent constructor to set up base screen elements 
 
        # Add the back button to return to the character selection screen 
        self.all_buttons.add_button(self.back_button, lambda: game.change_screen("character_select_screen"))        
 
        # Create the text and button for selecting Computer Science 
        self.computer_science_text = self.big_font.render("Computer Science", True, "darkorange") 
        self.computer_science_button = button.Button(0, 0, self.computer_science_text, 0.8) 
 
        # Position the Computer Science button 
        self.computer_science_button.change_position(10, 110, "topleft") 
 
        # Add the Computer Science button and link it to subject selection 
        self.all_buttons.add_button(self.computer_science_button, lambda: self.subject_selected("computer_science")) 
 
        # Create and position the screen heading 
        self.heading_text = self.big_font.render("Choose Your Subject:", True, "black") 
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH //2, 50)) 
 
        self.player = player  # Reference to player object 
 
    def subject_selected(self, subject): 
        # Set the player's subject and move to the topic selection screen 
        self.player.player_instance.subject = subject 
        game.change_screen("topic_select_screen") 
 
    def handle_events(self, events, screen): 
        # Delegate event handling to button manager 
        self.all_buttons.handle_input(screen) 
 
    def render(self, screen): 
        # Draw the background, heading, and all buttons to the screen 
        screen.blit(self.background, (0, 0)) 
        screen.blit(self.heading_text, self.heading_text_rect) 
        self.all_buttons.render_buttons(screen) 


class TopicSelectScreen(BaseScreen): 
    def __init__(self, player): 
        super().__init__()  # Call the parent constructor to initialize shared screen elements 
        self.player = player  # Store reference to the player object 
 
        # Load a smaller font for topic text 
        self.small_font = pygame.font.Font("Assets/Font1.ttf", 50) 
 
        # Add the back button to return to the subject selection screen 
        self.all_buttons.add_button(self.back_button, lambda: game.change_screen("subject_select_screen")) 
 
        # Create and center the heading text for the topic selection screen 
        self.heading_text = self.big_font.render("Choose Your Topic:", True, "black") 
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH // 2, 50)) 
 
    def start_screen(self): 
        # Retrieve topic list from the database based on the selected subject 
        self.topic_list = self.fetch_topics(self.player.player_instance.subject) 
 
        # Example list of topic names (used instead of dynamically retrieved names for now) 
        self.topic_names = ["Fundementals of data representation", "Fundamentals of Computer Systems"] 
 
        # Render each topic's text in varying shades of red 
        self.topics = [self.small_font.render(x, True, f"red{i % 3 + 1}") for i, x in enumerate(self.topic_names)] 
 
        # Create a button for each rendered topic text 
        self.topic_buttons = [button.Button(150, 200, i, 0.75) for i in self.topics] 
 
        # Position and register each topic button 
        for i, b in enumerate(self.topic_buttons): 
            b.change_position(10, 110 + i * 70, "topleft") 
            self.all_buttons.add_button(b, lambda x=self.topic_list[i]: self.topic_selected(x)) 
 
    def fetch_topics(self, subject): 
        # Use a context manager to safely open and close the database connection 
        with sqlite3.connect("main.db") as connection: 
            cursor = connection.cursor() 
 
            # Execute a query to fetch topic names for the specified subject 
            cursor.execute(''' 
                SELECT topic_text 
                FROM Topic 
                JOIN Subject ON Topic.subject_id = Subject.subject_id 
                WHERE subject_name = ? 
            ''', (subject,)) 
 
            # Fetch all resulting rows from the query 
            rows = cursor.fetchall() 
 
            # Extract the topic_text from each row and store in a list 
            topics = [row[0] for row in rows] 
 
        # Return the list of topic names 
        return topics 
 
    def topic_selected(self, topic): 
        # Store selected topic in the player's data and move to the confirmation screen 
        self.player.player_instance.topic = topic 
        game.change_screen("confirm_screen") 
 
    def handle_events(self, events, screen): 
        # Handle input events for all buttons 
        self.all_buttons.handle_input(screen) 
 
    def render(self, screen): 
        # Draw background, heading, and all topic buttons to the screen 
        screen.blit(self.background, (0, 0)) 
        screen.blit(self.heading_text, self.heading_text_rect) 
        self.all_buttons.render_buttons(screen)

class ConfirmScreen(BaseScreen):
    def __init__(self, player):
        super().__init__()  # Initialize the base screen class
        # Create and position the heading text
        self.heading_text = self.big_font.render("Confirm Your selection:", True, "black")
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH // 2, 50))
        
        # Define smaller font for details
        self.smaller_font = pygame.font.Font("Assets/Font1.ttf", 50)
        
        # Add back button functionality to return to topic select screen
        self.all_buttons.add_button(self.back_button, lambda: game.change_screen("topic_select_screen"))
        
        # Store player instance
        self.player = player
        

    def handle_events(self, events, screen):
        # Fetch the player's high score from the database for the selected subject and topic
        self.player.player_data.fetch_high_score(self.player.player_instance.character, self.player.player_instance.subject, self.player.player_instance.topic)
        
        # Render the subject, topic, and high score texts
        self.subject_text = self.smaller_font.render(f"Subject:\n{self.player.player_instance.subject}", True, "orange")
        self.topic_text = self.smaller_font.render(f"Topic:\n{self.player.player_instance.topic}", True, "cyan1")
        self.high_score_text = self.smaller_font.render(f"High Score: {self.player.player_data.high_score[self.player.player_instance.character][self.player.player_instance.subject][self.player.player_instance.topic]}", True, "red")
        
        # Position the text objects
        self.high_score_text_rect = self.high_score_text.get_frect(topleft=(0, 450))
        self.subject_text_rect = self.subject_text.get_frect(topleft=(0, 150))
        self.topic_text_rect = self.topic_text.get_frect(topleft=(0, 300))
        
        # Create and position the "Begin" button
        self.start_text = self.big_font.render("Begin!", True, "chartreuse1")
        self.start_button = button.Button(0, 0, self.start_text)
        self.start_button.change_position(SCREEN_WIDTH // 2, 600, "center")
        
        # Add the start button and associate it with the "game_screen" action
        self.all_buttons.add_button(self.start_button, lambda: game.change_screen("game_screen"))
        
        # Handle any button input (e.g., clicks or hover)
        self.all_buttons.handle_input(screen)
    
    
    def render(self, screen):
        # Draw the background and all screen elements
        screen.blit(self.background, (0, 0))
        screen.blit(self.heading_text, self.heading_text_rect)
        screen.blit(self.subject_text, self.subject_text_rect)
        screen.blit(self.topic_text, self.topic_text_rect)
        screen.blit(self.high_score_text, self.high_score_text_rect)
        
        # Render all buttons on screen
        self.all_buttons.render_buttons(screen)

class Stage():
    def __init__(self):
        num = random.randint(1, 9)
        self.background = pygame.image.load(f"Assets/Stages/{num}.png")

class Question(): 
    def __init__(self): 
        # The text of the question (e.g., "What is 2 + 2?") 
        self.question_text = None 
 
        # A list to hold possible answer choices 
        self.answers = [] 
 
        # The correct answer from the list of answers 
        self.correct_answer = None 
    
class QuestionManager():
    def __init__(self, player):
        self.questions = deque()  # Initialize a queue to hold the questions
        self.player = player  # Store the player instance for fetching player-specific data

    def fetch_questions(self, no_questions):    
        # Connect to the database
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()
        
        # Fetch the topic ID and subject ID based on the player's current topic
        self.cursor.execute(
            f'''SELECT * FROM Topic WHERE topic_text = "{self.player.player_instance.topic}"'''
        )
        topic_id, subject_id, topic = self.cursor.fetchone()
        
        # Fetch random questions from the Questions table based on the topic and subject
        self.cursor.execute(
            f'''SELECT question_text, correct_answer, option_1, option_2, option_3
               FROM Questions
               WHERE topic_id = {topic_id} AND subject_id = {subject_id} 
               ORDER BY RANDOM()
               LIMIT {no_questions}'''
        )
        temp = self.cursor.fetchall()  # Get the question data
        self.connection.close()  # Close the database connection
        return temp  # Return the fetched data
    
    def create_questions(self, no_questions):
        # Fetch the questions from the database
        data = self.fetch_questions(no_questions)
        
        # Create new question objects and populate them with data
        for question in data:
            new_question = Question()
            new_question.question_text = question[0]
            new_question.answers = [question[1], question[2], question[3], question[4]]  # List of answer options
            new_question.correct_answer = question[1]  # Correct answer
            self.questions.append(new_question)  # Add the question to the queue
    
    def get_next_question(self):
        # Return the first question from the queue and remove it
        if self.questions:
            return self.questions.popleft()
        else:
            return None  # Return None if no more questions are available

    
##           
class GameInstance(BaseScreen):
    def __init__(self, player):
        super().__init__()  # Initialize parent class (BaseScreen)
        self.stage = Stage()  # Create a new stage object (handles background and other stage elements)
        self.player = player  # Store the player object
        self.player.player_instance.reset_stats()  # Reset player stats at the start of the game
        self.start_time = None  # The start time of the game
        self.elapsed_time = 0  # Track elapsed time during the game
        self.small_font = pygame.font.Font("Assets/Font1.ttf", 50)  # Set font for larger text (time/score)
        self.smaller_font = pygame.font.Font("Assets/Font1.ttf", 30)  # Set font for smaller text (questions/answers)
        self.all_buttons = button.ButtonManager()  # Initialize button manager (to manage all buttons)
        self.last_question_correct = False  # Track whether the last question was answered correctly
        self.running = False  # Track whether the game is running
        self.player.player_instance.no_questions = 20  # Set the number of questions to be asked
        self.max_question_time = 60  # Set maximum time for answering each question
        self.current_question_time = 0  # Time taken to answer the current question
        self.correct_answer_sound = pygame.mixer.Sound("Assets/Sounds/correct.mp3")  # Load correct answer sound
        self.wrong_answer_sound = pygame.mixer.Sound("Assets/Sounds/wrong.mp3")  # Load wrong answer sound
        self.correct_answer_sound.set_volume(0.6)  # Set volume for correct answer sound
        self.wrong_answer_sound.set_volume(0.8)  # Set volume for wrong answer sound


    def start_gameplay(self):
        self.running = True  # Start the game
        self.start_time = pygame.time.get_ticks()  # Record the start time
        self.question_manager = QuestionManager(self.player)  # Initialize the QuestionManager
        self.question_manager.create_questions(self.player.player_instance.no_questions)  # Create questions for the game
        self.player.player_instance.new_high_score = False  # Reset high score flag
        self.current_question_number = 0  # Initialize question number
        self.change_question()  # Change to the first question


    def change_question(self):
        self.current_question_time = pygame.time.get_ticks()  # Track the time the question is displayed
        
        # Increment question number
        self.current_question_number += 1
        
        # If no more questions are available, end the game
        if not self.question_manager.questions:
            self.end_game()
            return None
        
        # Get the next question from the question manager
        self.current_question = self.question_manager.get_next_question()
        
        # After changing the question, set up the answer buttons
        self.make_answer_buttons()
        

    def handle_events(self, events, screen):
        self.all_buttons.handle_input(screen)  # Handle user input for buttons


    def update(self, dt):
        if self.running:
            # Calculate elapsed time since game started
            if self.start_time is not None:
                self.elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000 
            
        

    def make_answer_buttons(self):
        self.all_buttons.clear_buttons()  # Clear previous answer buttons
        self.answer_button_width = 300  # Set the width for the answer buttons
        self.answer_button_height = 200  # Set the height for the answer buttons
        self.answer_button_Y = SCREEN_HEIGHT - self.answer_button_height - 10  # Set the Y position for buttons
        self.button_images = []  # List to store button images
        self.answer_buttons = []  # List to store the button objects
        random.shuffle(self.current_question.answers)  # Shuffle answers to randomize their order
        for i in range (4):
            current_answer = self.current_question.answers[i]  # Get each answer
            current_answer_text = wrap_text(current_answer, self.smaller_font, self.answer_button_width - 6)  # Wrap answer text to fit button
            current_answer_image = self.smaller_font.render(current_answer_text, True, "white")  # Render answer text
            button_image = pygame.Surface((self.answer_button_width, self.answer_button_height))  # Create button surface
            button_image.fill("darkblue")  # Fill button with color
            button_image.blit(current_answer_image, (0, 0))  # Place answer text on button surface
            self.button_images.append(button_image)  # Append to button images list
            self.answer_buttons.append(button.Button((i * (self.answer_button_width + 10)), self.answer_button_Y, self.button_images[i]))  # Create a new button and add it to the list
            # Assign function to check answer correctness for each button
            if current_answer == self.current_question.correct_answer:
                self.all_buttons.add_button(self.answer_buttons[i], lambda: self.check_answer(True))
            else:
                self.all_buttons.add_button(self.answer_buttons[i], lambda: self.check_answer(False))


    def check_answer(self, correct):
        current_time = pygame.time.get_ticks()  # Get the current time
        time_taken = (current_time - self.current_question_time) / 1000  # Calculate time taken to answer
        if correct:
            self.correct_answer_sound.play()  # Play correct answer sound
            self.last_question_correct = True  # Mark last question as correct
            self.player.player_instance.correct_questions += 1  # Increment correct question counter
        else:
            self.last_question_correct = False  # Mark last question as incorrect
            self.wrong_answer_sound.play()  # Play wrong answer sound
        self.calculate_score(time_taken)  # Calculate the score based on time taken
        self.change_question()  # Move to the next question

    def calculate_score(self, time_taken):
        self.set_combo()  # Check and update combo multiplier
        base_score = 100 + max(0, (900 * ((self.max_question_time - time_taken) / self.max_question_time)))  # Calculate base score
        if self.last_question_correct:
            self.player.player_instance.score += int(base_score * (1 + 0.05 * self.player.player_instance.combo))  # Add to score based on combo multiplier
        else:
            penalty = int(base_score * 0.3) + 50  # Apply penalty for wrong answer
            self.player.player_instance.score -= penalty
            if self.player.player_instance.score < 0:
                self.player.player_instance.score = 0  # Ensure score doesn't go below zero


    def set_combo(self):
        if self.last_question_correct:
            self.player.player_instance.combo += 1  # Increase combo if the last question was correct
        elif not self.last_question_correct:
            self.player.player_instance.combo = 0  # Reset combo if the last question was incorrect

    def render_question(self, screen):
        # Format the current question text
        current_question_text = f"Q.{self.current_question_number} " + self.current_question.question_text
        current_question_text = wrap_text(current_question_text, self.smaller_font, 700)  # Wrap question text
        current_question_text_image = self.smaller_font.render(current_question_text, True, "white")  # Render the question text
        current_question_text_rect = current_question_text_image.get_frect(topright=(1200, 20))  # Get the rectangle for positioning
        pygame.draw.rect(screen, "darkblue", current_question_text_rect.inflate(20, 30))  # Draw background for question
        screen.blit(current_question_text_image, current_question_text_rect)  # Blit question text on screen
        
    def end_game(self):
        self.player.player_instance.total_time = self.elapsed_time  # Record total time taken
        if self.player.player_instance.score > self.player.player_data.high_score[self.player.player_instance.character][self.player.player_instance.subject][self.player.player_instance.topic]:
            self.set_new_high_score()  # Set new high score if applicable
        self.running = False  # End the game
        game.change_screen("game_summary")  # Change screen to game summary

    def set_new_high_score(self):
        self.connection = sqlite3.connect("main.db")  # Connect to database
        self.cursor = self.connection.cursor()  # Create a cursor to execute queries
        if self.player.player_data.logged_in:
            self.player.player_instance.new_high_score = True  # Mark that a new high score was achieved
            if not (self.player.has_high_score()):  # Check if player already has a high score
                # Insert new high score into database
                self.cursor.execute('''
                    INSERT INTO HighScore (user_id, character_id, subject_id, topic_id, high_score)
                    SELECT ?, Characters.character_id, Subject.subject_id, Topic.topic_id, ?
                    FROM Characters
                    JOIN Subject ON Subject.subject_name = ?
                    JOIN Topic ON Topic.topic_text = ?
                    WHERE Characters.character_name = ?
                    ''', (
                    self.player.player_data.user_id,
                    self.player.player_instance.score,
                    self.player.player_instance.subject,
                    self.player.player_instance.topic,
                    self.player.player_instance.character))
            else:
                # Update the high score for the player
                self.cursor.execute('''
                    UPDATE HighScore
                    SET high_score = ?
                    WHERE user_id = ?
                    AND character_id = (SELECT character_id FROM Characters WHERE character_name = ?)
                    AND subject_id = (SELECT subject_id FROM Subject WHERE subject_name = ?)
                    AND topic_id = (SELECT topic_id FROM Topic WHERE topic_text = ?)
                ''', (
                    self.player.player_instance.score,
                    self.player.player_data.user_id,
                    self.player.player_instance.character,  # character name
                    self.player.player_instance.subject,    # subject name
                    self.player.player_instance.topic       # topic name
                ))

        self.connection.commit()  # Commit changes to the database
        self.connection.close()  # Close the database connection


    def render_game(self, screen):
        screen.blit(self.stage.background, (0, 0))  # Draw the background
        if self.start_time is not None:
            time_text_image = self.small_font.render(f"Time: {self.elapsed_time:.2f}s", True, "white")  # Display elapsed time
            time_text_rect = time_text_image.get_frect(topleft=(20, 20))  # Get rectangle for positioning
            pygame.draw.rect(screen, "darkblue", time_text_rect.inflate(20, 30))  # Draw background for time
            screen.blit(time_text_image, time_text_rect)  # Display time text
            score_text_image = self.small_font.render(f"Score: {self.player.player_instance.score}", True, "white")  # Display score
            score_text_rect = score_text_image.get_frect(topleft=(20, 100))  # Get rectangle for positioning
            pygame.draw.rect(screen, "darkblue", score_text_rect.inflate(20, 30))  # Draw background for score
            screen.blit(score_text_image, score_text_rect)  # Display score text
            combo_text_image = self.small_font.render(f"Combo: {self.player.player_instance.combo}", True, "white")  # Display combo
            combo_text_rect = combo_text_image.get_frect(topleft=(20, 180))  # Get rectangle for positioning
            pygame.draw.rect(screen, "darkblue", combo_text_rect.inflate(20, 30))  # Draw background for combo
            screen.blit(combo_text_image, combo_text_rect)  # Display combo text
            question_number_image = self.smaller_font.render(f"Question {self.current_question_number} of {self.player.player_instance.no_questions}", True, "white")  # Display question number
            questnion_number_rect = question_number_image.get_frect(topleft=(20, 240))  # Get rectangle for positioning
            pygame.draw.rect(screen, "darkblue", questnion_number_rect.inflate(20, 30))  # Draw background for question number
            screen.blit(question_number_image, questnion_number_rect)  # Display question number
        self.render_question(screen)  # Render the current question
        self.all_buttons.render_buttons(screen)  # Render answer buttons

    def render(self, screen):
        if self.running:
            self.render_game(screen)  # If the game is running, render the game screen


class GameSummary(BaseScreen):
    def __init__(self, player):
        super().__init__()  # Initialize parent class (BaseScreen)
        self.player = player  # Store player object
        
        # Create and position the game summary heading text
        self.heading_text = self.big_font.render("Game Summary", True, "antiquewhite4")  # Heading text
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH // 2, 50))  # Center the heading at the top

        self.small_font = pygame.font.Font("Assets/Font1.ttf", 50)  # Set font for stats text
        self.continue_text = self.big_font.render("Continue", True, "chartreuse1")  # Text for "Continue" button
        self.continue_button = button.Button(0, 0, self.continue_text)  # Create continue button
        self.all_buttons.add_button(self.continue_button, lambda: self.end_game_summary())  # Assign function to button
        self.continue_button.change_position(SCREEN_WIDTH // 2, 600, "center")  # Position the button at the center bottom

    def end_game_summary(self):
        game.change_screen("main_menu")  # Change the screen to the main menu when the game summary ends

    def handle_events(self, events, screen):
        self.all_buttons.handle_input(screen)  # Handle any input from the buttons

    def update(self, dt):
        # Determine the score to display (new high score if applicable, otherwise the existing high score)
        if self.player.player_instance.new_high_score:
            temp = self.player.player_instance.score  # Use the new high score
        else:
            temp = self.player.player_data.high_score[self.player.player_instance.character][self.player.player_instance.subject][self.player.player_instance.topic]  # Use existing high score
        
        # Prepare the stats text to display in the game summary
        self.stats_text = (
            f"{self.player.player_instance.correct_questions}/{self.player.player_instance.no_questions} Questions Correct\n"
            f"Score: {self.player.player_instance.score} \n"
            + f"High Score: {temp} \n"
            + f"Total Time: {self.player.player_instance.total_time} \n"
            + f"Character: {self.player.player_instance.character} \n"
            + f"Subject: {self.player.player_instance.subject} \n"
            + f"Topic: {self.player.player_instance.topic} \n"
        )

        # Render the stats text to display on the screen
        self.stats_text_surf = self.small_font.render(self.stats_text, True, "white")  # Render the stats text
        self.stats_text_rect = self.stats_text_surf.get_frect(topleft=(10, 150))  # Position the stats text in the top-left corner

    def render(self, screen):
        # Draw the background and other elements on the screen
        screen.blit(self.background, (0, 0))  # Blit the background
        screen.blit(self.heading_text, self.heading_text_rect)  # Blit the heading text
        screen.blit(self.stats_text_surf, self.stats_text_rect)  # Blit the stats text
        self.all_buttons.render_buttons(screen)  # Render the buttons (like "Continue" button)

class LoginScreen(BaseScreen):
    def __init__(self, player):
        super().__init__()  # Initialize parent class (BaseScreen)

        # Set up the heading text for the login screen
        self.heading_text = self.big_font.render("Login", True, "green")
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH // 2, 50))

        self.player = player  # Store reference to player object

        # Set up fonts for different text elements
        self.small_font = pygame.font.Font("Assets/Font1.ttf", 50)
        self.smaller_font = pygame.font.Font("Assets/Font1.ttf", 30)

        # Add a "Back" button to return to the main menu
        self.all_buttons.add_button(self.back_button, lambda: game.change_screen("main_menu"))

        # Username label
        self.username_text = self.small_font.render("Username:", True, "green")
        self.username_text_rect = self.username_text.get_frect(topleft=(10, 150))

        # Password label
        self.password_text = self.small_font.render("Password:", True, "green")
        self.password_text_rect = self.password_text.get_frect(topleft=(10, 250))

        # Set up the GUI manager with a theme
        self.UI_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), "theme.json")

        # Create text input fields for username and password
        self.username_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((10, 200), (900, 50)), manager=self.UI_manager, object_id="username_entry")
        self.password_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((10, 300), (900, 50)), manager=self.UI_manager, object_id="password_entry")

        # Create a submit button
        self.submit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 400), (100, 50)),
            text="Submit",
            manager=self.UI_manager
        )

        # Set the initial error message
        self.error_text = "Please enter your Username and Password."

        # Load and configure the login sound
        self.login_sound = pygame.mixer.Sound("Assets/Sounds/ding.mp3")
        self.login_sound.set_volume(0.5)

    def update(self, dt):
        self.UI_manager.update(dt)  # Update the UI manager

    def handle_events(self, events, screen):
        self.all_buttons.handle_input(screen)  # Handle button inputs

        for event in events:
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.submit_button:
                    # If submit button is pressed, collect input and check credentials
                    username_text = self.username_input.get_text()
                    password_text = self.password_input.get_text()
                    self.check_username_and_password(username_text, password_text)
            self.UI_manager.process_events(event)  # Pass events to the UI manager

    def check_username_and_password(self, username, password):
        # Connect to the database
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()

        # Check if username exists
        if not RegisterScreen(self.player).username_exists(username):
            self.error_text = "Username does not exist"
        
        # Validate password length
        elif len(password) >= 20 or len(password) < 5:
            self.error_text = "Password should be between 5-20 characters."
        
        else:
            # Fetch the stored hash and salt for the username
            self.cursor.execute("SELECT hash, salt FROM User WHERE username = ?", (username,))
            old_hash, old_salt = self.cursor.fetchone()
            self.connection.close()  # Close the database connection

            # Hash the entered password with the stored salt
            new_hash, new_salt = RegisterScreen(self.player).hash_password(password, old_salt)

            if new_hash == old_hash:
                # If the hashes match, log the user in
                self.log_user_in(username)
                self.username_input.clear()
                self.password_input.clear()
                game.change_screen("main_menu")  # Go to main menu
            else:
                self.error_text = "Username or Password do not match"

        self.connection.close()  # Ensure database connection is closed

    def log_user_in(self, username):
        # Set player data to logged in and store username and user ID
        self.player.player_data.logged_in = True
        self.player.player_data.username = username
        self.player.player_data.user_id = get_user_id(username)
        self.login_sound.play()  # Play login success sound

    def render_error(self, screen):
        # Wrap the error text to fit inside a box
        current_error_text = wrap_text(self.error_text, self.smaller_font, 700)
        current_error_text_image = self.smaller_font.render(current_error_text, True, "white")
        current_error_text_rect = current_error_text_image.get_frect(topleft=(200, 400))

        # Draw a background rectangle for the error message
        pygame.draw.rect(screen, "darkblue", current_error_text_rect.inflate(20, 30))
        screen.blit(current_error_text_image, current_error_text_rect)  # Blit the error text

    def render(self, screen):
        # Draw all visual elements to the screen
        screen.blit(self.background, (0, 0))  # Background
        screen.blit(self.heading_text, self.heading_text_rect)  # Heading
        screen.blit(self.username_text, self.username_text_rect)  # Username label
        screen.blit(self.password_text, self.password_text_rect)  # Password label

        # If there is an error message, display it
        if self.error_text is not None:
            self.render_error(screen)

        self.all_buttons.render_buttons(screen)  # Render buttons
        self.UI_manager.draw_ui(screen)  # Draw UI elements (input boxes, submit button)

class RegisterScreen(BaseScreen):
    def __init__(self, player):
        super().__init__()
        # Fonts for different text sizes
        self.small_font = pygame.font.Font("Assets/Font1.ttf", 50)
        self.smaller_font = pygame.font.Font("Assets/Font1.ttf", 30)
        
        # Heading Text
        self.heading_text = self.big_font.render("Register", True, "red")
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH // 2, 50))
        
        # Store player object
        self.player = player
        
        # Add back button to go to the main menu
        self.all_buttons.add_button(self.back_button, lambda: game.change_screen("main_menu"))
        
        # Username label
        self.username_text = self.small_font.render("Username:", True, "red")
        self.username_text_rect = self.username_text.get_frect(topleft=(10, 150))
        
        # Password label
        self.password_text = self.small_font.render("Password:", True, "red")
        self.password_text_rect = self.password_text.get_frect(topleft=(10, 250))
        
        # Confirm Password label
        self.confirm_password_text = self.small_font.render("Confirm Password:", True, "red")
        self.confirm_password_text_rect = self.confirm_password_text.get_frect(topleft=(10, 350))
        
        # Setup UI Manager with theme
        self.UI_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), "theme.json")
        
        # Input fields for username, password and password confirmation
        self.username_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((10, 200), (900, 50)), manager=self.UI_manager, object_id="username_entry")
        self.password_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((10, 300), (900, 50)), manager=self.UI_manager, object_id="password_entry")
        self.confirm_password_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((10, 400), (900, 50)), manager=self.UI_manager, object_id="confirm_password_entry")
        
        # Submit button
        self.submit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 450), (100, 50)), text="Submit", manager=self.UI_manager)
        
        # Default warning message about password safety
        self.error_text = "Warning: Don't use the actual passwords you use for other programs. The security for this program is not industry standard."

    def handle_events(self, events, screen):
        # Handle button input
        self.all_buttons.handle_input(screen)
        for event in events:
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.submit_button:
                    # Get input values when submit is pressed
                    username_text = self.username_input.get_text()
                    password_text = self.password_input.get_text()
                    confirm_password_text = self.confirm_password_input.get_text()
                    self.check_inputs(username_text, password_text, confirm_password_text)
            # Pass events to UI manager
            self.UI_manager.process_events(event)

    def check_inputs(self, username, password, confirm_password):
        # Validate username and password
        if len(username) >= 20 or len(username) < 5:
            self.error_text = "Username should be between 5-20 characters."
        elif len(password) >= 20 or len(password) < 5:
            self.error_text = "Password should be between 5-20 characters."
        elif username.lower() in password.lower():
            self.error_text = "Password cannot contain the username."
        elif not re.match(r"^[a-zA-Z0-9_.]+$", username):
            self.error_text = "Username can only contain letters, numbers, underscores, and dots."
        elif " " in password:
            self.error_text = "Password cannot contain spaces."
        elif password != confirm_password:
            self.error_text = "Password does not match confirm password."
        elif self.username_exists(username):
            self.error_text = "Username already exists"
        else:
            # If all checks pass, add user to database
            self.add_details_to_db(username, password)

    def add_details_to_db(self, username, password):
        # Connect to the database
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()
        
        # Hash the password with a new salt
        hashed_password, salt = self.hash_password(password, salt=None)
        
        # Get the current time
        current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert the user into the database
        self.cursor.execute('''INSERT INTO User(username, hash, salt, time_created)
                               VALUES (?, ?, ?, ?)''', (username, hashed_password, salt, current_timestamp))
        
        # Commit changes and close the database
        self.connection.commit()
        self.connection.close()
        
        # Log the user in and go back to main menu
        LoginScreen(self.player).log_user_in(username)
        game.change_screen("main_menu")

    def hash_password(self, password, salt=None):
        # Simple custom password hashing with salt
        if salt is None:
            salt = os.urandom(16)
        combined = password.encode('utf-8') + salt
        
        # Custom hash function (not industry standard, just for school project use)
        hash_value = 10061
        for byte in combined:
            hash_value = ((hash_value << 5) + hash_value) ^ byte
        
        return hex(hash_value), salt

    def username_exists(self, username):
        # Check if username already exists in the database
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()
        self.cursor.execute('''SELECT 1 FROM User WHERE username = ?''', (username,))
        temp = self.cursor.fetchone()
        self.connection.close()
        return temp is not None

    def render_error(self, screen):
        # Display the current error message
        current_error_text = wrap_text(self.error_text, self.smaller_font, 700)
        current_error_text_image = self.smaller_font.render(current_error_text, True, "white")
        current_error_text_rect = current_error_text_image.get_frect(topleft=(200, 480))
        
        # Draw a background rectangle for the error message
        pygame.draw.rect(screen, "darkblue", current_error_text_rect.inflate(20, 30))
        
        # Draw the error text
        screen.blit(current_error_text_image, current_error_text_rect)

    def update(self, dt):
        # Update the UI manager
        self.UI_manager.update(dt)

    def render(self, screen):
        # Draw the background and heading
        screen.blit(self.background, (0, 0))
        screen.blit(self.heading_text, self.heading_text_rect)
        
        # Draw form labels
        screen.blit(self.username_text, self.username_text_rect)
        screen.blit(self.password_text, self.password_text_rect)
        screen.blit(self.confirm_password_text, self.confirm_password_text_rect)
        
        # Render all buttons
        self.all_buttons.render_buttons(screen)
        
        # Render any error messages
        if self.error_text is not None:
            self.render_error(screen)
        
        # Draw the UI elements
        self.UI_manager.draw_ui(screen)

class Game:
    def __init__(self):
        # Initializes Pygame modules and game assets
        pygame.init()
        pygame.mixer.init()

        # Sets up the game window and frame rate control
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Creates the Player object
        self.player = Player()

        # Dictionary storing all the different screens of the game
        self.screens = {
            "main_menu": MainMenuScreen(self.player),
            "game_screen": None,  # Will be created when gameplay starts
            "character_select_screen": CharacterSelectScreen(self.screen, self.player),
            "subject_select_screen": SubjectSelectScreen(self.player),
            "topic_select_screen": TopicSelectScreen(self.player),
            "confirm_screen": ConfirmScreen(self.player),
            "game_summary": GameSummary(self.player),
            "register_screen": RegisterScreen(self.player),
            "login_screen": LoginScreen(self.player)
        }

        # Sets the initial screen to the main menu
        self.current_screen = "main_menu"

    def change_screen(self, screen):
        # Changes the current active screen
        self.current_screen = screen

        # If moving to the gameplay screen, initialize it
        if screen == "game_screen":
            self.screens[screen] = GameInstance(self.player)
            game_screen = self.screens[screen]
            game_screen.start_gameplay()

        # If moving to the login screen, set initial error text
        if screen == "login_screen":
            login_screen = self.screens[screen]
            login_screen.error_text = "Please enter your Username and Password"

        # If moving to the register screen, set a warning message
        if screen == "register_screen":
            register_screen = self.screens[screen]
            register_screen.error_text = (
                "Warning: Don't use the actual passwords you use for other programs. "
                "The security for this program is not industry standard."
            )

        # If moving to the topic selection screen, prepare it
        if screen == "topic_select_screen":
            topic_select_screen = self.screens[screen]
            topic_select_screen.start_screen()

    def run(self):
        # Main game loop
        while self.running:
            # Controls the frame rate and calculates time delta
            dt = self.clock.tick(FPS) / 1000

            # Handles all events like keypresses, mouse clicks, etc.
            events = pygame.event.get()

            # Updates the window title to the current screen name
            pygame.display.set_caption(f"{self.current_screen}")

            for event in events:
                if event.type == pygame.QUIT:
                    # If the user closes the window, stop the game loop
                    self.running = False

            # Get the instance of the currently active screen
            screen_instance = self.screens[self.current_screen]

            # Let the screen handle input, update its state, and draw itself
            screen_instance.handle_events(events, self.screen)
            screen_instance.update(dt)
            screen_instance.render(self.screen)

            # Update the full display surface to the screen
            pygame.display.flip()

        # Clean up and close Pygame when done
        pygame.quit()


def get_user_id(username):
    # Connect to the SQLite database
    connection = sqlite3.connect("main.db")
    cursor = connection.cursor()
    
    # Execute a SQL query to fetch the user_id where the username matches
    cursor.execute(f'''SELECT user_id
                        FROM User
                        WHERE username = ?''', (username,))
    
    # Fetch the first matching result
    temp = cursor.fetchone()
    
    # Close the database connection
    connection.close()
    
    # Return the user_id from the fetched result
    return temp[0]


if __name__ == "__main__":
    game = Game()
    game.run()

