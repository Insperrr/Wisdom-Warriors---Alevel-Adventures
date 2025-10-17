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

os.chdir(os.path.dirname(os.path.abspath(__file__)))

SCREEN_WIDTH, SCREEN_HEIGHT = (1280, 720)
FPS = 60

def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (word if current_line == "" else " " + word)
        text_width, _ = font.size(test_line)
        
        if text_width > max_width:
            lines.append(current_line)
            current_line = word  
        else:
            current_line = test_line

    if current_line:
        lines.append(current_line)
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
        super().__init__()  # Inherits from a base class (if applicable)

        # User identity and login status
        self.username = None          # Username of the logged-in player
        self.user_id = None           # Unique user ID from the database
        self.logged_in = False        # Tracks whether the user is logged in

        # Local cache of high scores organized by character, subject, and topic
        self.high_score = {
            "sonic": {
                "computer_science": {
                    "fundamentals_of_data_representation": 0,
                    "fundamentals_of_computer_systems": 0
                }
            }
        }

    def fetch_high_score(self, character, subject, topic):
        """
        Loads the high score for a specific character-subject-topic combination from the database.
        Updates self.high_score with the result.
        """
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()

        # Get the IDs for character, subject, and topic from utility functions
        character_id = get_character_id(character)
        subject_id = get_subject_id(subject)
        topic_id = get_topic_id(topic)

        # SQL query to fetch high score from database
        self.cursor.execute(f'''SELECT high_score
                          FROM HighScore
                          WHERE user_id = ? AND character_id = ? 
                          AND subject_id = ? AND topic_id = ?''',
                            (self.user_id, character_id, subject_id, topic_id))
        
        # Fetch result and store in local high_score dict
        temp = self.cursor.fetchone()
        if temp is not None:
            self.high_score[character][subject][topic] = temp[0]
        elif self.logged_in:
            self.high_score[character][subject][topic] = 0

        self.connection.close()
 
class PlayerInstance(BaseCharacter):
    def __init__(self):
        # Initializes session-specific player data
        self.subject = None               # Subject currently selected by the player (e.g., "Maths")
        self.topic = None                 # Specific topic within the subject (e.g., "Algebra")
        self.character = None             # Chosen character avatar or style
        self.score = 0                    # Current score in the session
        self.combo = 0                    # Current combo streak (e.g., consecutive correct answers)
        self.new_high_score = False       # Flag to indicate if a new high score has been achieved
        self.correct_questions = 0        # Count of correctly answered questions in this session

    def reset_player_instance(self):
        # Resets all session-related data, including character and chosen topics
        self.subject = None
        self.topic = None
        self.character = None
        self.score = 0
        self.combo = 0
        self.new_high_score = False
        self.correct_questions = 0

    def reset_stats(self):
        # Resets only performance-related stats — keeps subject, topic, and character intact
        self.score = 0
        self.combo = 0
        self.new_high_score = False

class Player:
    def __init__(self):
        # Initializes player-related data:
        # player_data holds persistent info (like username, user_id)
        # player_instance holds session-specific choices (character, subject, topic)
        self.player_data = PlayerData()
        self.player_instance = PlayerInstance()

    def set_player_ids(self, character, subject, topic):
        # Set IDs in player_instance using utility functions that fetch from the database
        self.player_instance.character_id = get_character_id(character)
        self.player_instance.subject_id = get_subject_id(subject)
        self.player_instance.topic_id = get_topic_id(topic)

    def has_high_score(self):
        # Checks if this player already has a high score saved for their chosen character, subject, and topic
        
        # Connect to the database
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()

        # Query the HighScore table for an existing record with matching IDs
        self.cursor.execute('''
            SELECT COUNT(*) 
            FROM HighScore 
            WHERE user_id = ? AND character_id = ? AND subject_id = ? AND topic_id = ?
        ''', (
            self.player_data.user_id, 
            self.player_instance.character_id, 
            self.player_instance.subject_id, 
            self.player_instance.topic_id
        ))

        # Check if any matching row exists (i.e., count > 0)
        exists = self.cursor.fetchone()[0] > 0
        
        # Close the connection and return the result
        self.connection.close()
        return exists

##        
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

##
class MainMenuScreen(BaseScreen):
    def __init__(self, player):
        super().__init__()

        # Load medium-sized font and game logo
        self.medium_font = pygame.font.Font("Assets/Font1.ttf", 60)
        self.logo = pygame.image.load("Assets/logo.png")
        self.logo_rect = self.logo.get_frect(topleft=(60, -20))             

        # Create and center the START button
        self.start_text = self.big_font.render("START", True, (255, 255, 255))
        self.start_button = button.Button(0, 0, self.start_text)
        self.start_button.change_position(SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + 25, "center")
        self.all_buttons.add_button(self.start_button, lambda: game.change_screen("character_select_screen"))

        # Create LOGIN and REGISTER text surfaces
        self.login_text = self.medium_font.render("LOGIN", True, "white")
        self.register_text = self.medium_font.render("REGISTER", True, "white")

        # Create and position LOGIN and REGISTER buttons
        self.register_button = button.Button(0, 0, self.register_text, 0.8)
        self.login_button = button.Button(0, 0, self.login_text)
        self.register_button.change_position(SCREEN_WIDTH // 4, (SCREEN_HEIGHT // 4) * 2.7, "center")
        self.login_button.change_position((SCREEN_WIDTH // 4) * 3, (SCREEN_HEIGHT // 4) * 2.7, "center")

        # Add button actions to change screens
        self.all_buttons.add_button(self.register_button, lambda: game.change_screen("register_screen"))
        self.all_buttons.add_button(self.login_button, lambda: game.change_screen("login_screen"))

        # Additional setup
        self.small_font = pygame.font.Font("Assets/Font1.ttf", 30)
        self.player = player
        self.time_elapsed = 0

    def update(self, dt):
        # Track time for animation
        self.time_elapsed += dt
        amplitude = 1
        frequency = 0.25

        # Display welcome message if user is logged in
        if self.player.player_data.logged_in:
            self.welcome_text = self.medium_font.render(f"Welcome back {self.player.player_data.username}!", True, "green")
            self.welcome_text_rect = self.welcome_text.get_frect(center=(SCREEN_WIDTH // 2, 700))

        # Animate logo using sine wave
        self.logo_rect.y += (amplitude * math.sin(self.time_elapsed * frequency * 2 * math.pi))

        # Reset player instance for a clean start
        self.player.player_instance.reset_player_instance()

    def handle_events(self, events, screen):
        # Pass events to button handler
        self.all_buttons.handle_input(events)

    def render(self, screen):
        # Draw background and logo
        screen.blit(self.background, (0, 0))
        screen.blit(self.logo, self.logo_rect)

        # Draw welcome text if user is logged in
        if self.player.player_data.logged_in:
            screen.blit(self.welcome_text, self.welcome_text_rect)

        # Render all buttons
        self.all_buttons.render_buttons(screen)

##
class CharacterSelectScreen(BaseScreen):
    def __init__(self, screen, player):
        super().__init__()
        self.character_texts = {"sonic": "Sonic - The Fastest Thing Alive",
                                "kirby": "Kirby - The Star Warrior"
                                }
        self.get_character_descriptions()
        self.sonic_icon_button = button.Button(10, 200, pygame.image.load("Assets/sonic_icon.jpg"), 0.4)
        self.all_buttons.add_button(self.back_button, lambda: game.change_screen("main_menu"))
        self.all_buttons.add_button(self.sonic_icon_button,
                                    lambda: self.character_selected("sonic"),
                                    None, lambda: self.display_text(screen, "sonic"))
        self.heading_text = self.big_font.render("Choose Your Character:", True, "black")
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH //2, 50))
        self.current_text = None
        self.player = player


    def get_character_descriptions(self):
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()
        self.cursor.execute('SELECT character_name, character_description FROM Characters')
        self.character_descriptions = {}
        for character_name, character_description in self.cursor.fetchall():
            self.character_descriptions[character_name] = character_description
        self.connection.close()


    def display_text(self, screen, character):
        self.character_texts_positions = {"sonic": (20, 500)}
        self.current_text = self.small_font.render(self.character_texts.get(character), True, "white")
        self.current_text_rect = self.current_text.get_rect(topleft=self.character_texts_positions[character])

    def character_selected(self, character):
        self.player.player_instance.character = character
        game.change_screen("subject_select_screen")
    
    def handle_events(self, events, screen):
        self.all_buttons.handle_input(screen)

    def render(self, screen):
        screen.blit(self.background, (0, 0))
        screen.blit(self.heading_text, self.heading_text_rect)
        self.all_buttons.render_buttons(screen)
        if self.current_text:
            screen.blit(self.current_text, self.current_text_rect)
        self.current_text = None

##
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

##
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
        # Connect to the database and get topics matching the selected subject
        connection = sqlite3.connect("main.db")
        cursor = connection.cursor()

        # Get the subject ID to use in query
        subject_id = get_subject_id(subject)

        # Fetch topic names from the database
        cursor.execute('''SELECT topic_text
                          FROM Topic
                          WHERE subject_id = ?''', (subject_id,))
        rows = cursor.fetchall()

        # Extract topic names from query result
        topics = [row[0] for row in rows]

        # Close the connection (note: fix missing parentheses)
        connection.close()

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

##
class ConfirmScreen(BaseScreen):
    def __init__(self, player):
        super().__init__()  # Initialize shared screen elements from BaseScreen

        # Create and position heading text
        self.heading_text = self.big_font.render("Confirm Your selection:", True, "black")
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH // 2, 50))

        # Load a smaller font for the subject, topic, and score text
        self.smaller_font = pygame.font.Font("Assets/Font1.ttf", 50)

        # Add the back button to return to the topic selection screen
        self.all_buttons.add_button(self.back_button, lambda: game.change_screen("topic_select_screen"))

        # Store reference to the player object
        self.player = player

    def handle_events(self, events, screen):
        # Fetch and store the player's high score for their current character, subject, and topic
        self.player.player_data.fetch_high_score(
            self.player.player_instance.character,
            self.player.player_instance.subject,
            self.player.player_instance.topic
        )

        # Set player IDs internally for tracking in the database
        self.player.set_player_ids(
            self.player.player_instance.character,
            self.player.player_instance.subject,
            self.player.player_instance.topic
        )

        # Render subject, topic, and high score as text surfaces
        self.subject_text = self.smaller_font.render(
            f"Subject:\n{self.player.player_instance.subject}", True, "orange"
        )
        self.topic_text = self.smaller_font.render(
            f"Topic:\n{self.player.player_instance.topic}", True, "cyan1"
        )
        self.high_score_text = self.smaller_font.render(
            f"High Score: {self.player.player_data.high_score[self.player.player_instance.character][self.player.player_instance.subject][self.player.player_instance.topic]}",
            True,
            "red"
        )

        # Get rects for layout positioning
        self.high_score_text_rect = self.high_score_text.get_frect(topleft=(0, 450))
        self.subject_text_rect = self.subject_text.get_frect(topleft=(0, 150))
        self.topic_text_rect = self.topic_text.get_frect(topleft=(0, 300))

        # Create and position the start button
        self.start_text = self.big_font.render("Begin!", True, "chartreuse1")
        self.start_button = button.Button(0, 0, self.start_text)
        self.start_button.change_position(SCREEN_WIDTH // 2, 600, "center")

        # Add the start button to proceed to the game screen
        self.all_buttons.add_button(self.start_button, lambda: game.change_screen("game_screen"))

        # Handle button input
        self.all_buttons.handle_input(screen)

    def render(self, screen):
        # Draw all UI elements to the screen
        screen.blit(self.background, (0, 0))
        screen.blit(self.heading_text, self.heading_text_rect)
        screen.blit(self.subject_text, self.subject_text_rect)
        screen.blit(self.topic_text, self.topic_text_rect)
        screen.blit(self.high_score_text, self.high_score_text_rect)
        self.all_buttons.render_buttons(screen)

class Stage():
    def __init__(self):
        # Randomly select a number between 1 and 9 to choose a stage background
        num = random.randint(1, 9)

        # Load the corresponding stage background image
        self.background = pygame.image.load(f"Assets/Stages/{num}.png")

class Question():
    def __init__(self):
        self.question_text = None
        self.answers = []
        self.correct_answer = None
    
class QuestionManager():
    def __init__(self, player):
        # List to store all generated Question objects
        self.questions = []

        # Reference to the current player instance to access selected topic/subject
        self.player = player

    def fetch_questions(self, no_questions):    
        # Connect to the SQLite database
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()

        # Fetch topic_id and subject_id based on the selected topic
        self.cursor.execute(
            f'''Select * from Topic where topic_text = "{self.player.player_instance.topic}"'''
        )
        topic_id, subject_id, topic = self.cursor.fetchone()

        # Fetch a random set of questions that match the topic and subject
        self.cursor.execute(
            f'''Select question_text, correct_answer, option_1, option_2, option_3
               From Questions
               Where topic_id = {topic_id} AND subject_id = {subject_id} ORDER BY RANDOM()
               Limit {no_questions}'''
        )

        # Get the results and close the connection
        temp = self.cursor.fetchall()
        self.connection.close()
        return temp

    def create_questions(self, no_questions):
        # Fetch raw question data from the database
        data = self.fetch_questions(no_questions)

        # Convert raw data into Question objects
        for question in data:
            new_question = Question()
            new_question.question_text = question[0]  # Set the question text
            new_question.answers = [question[1], question[2], question[3], question[4]]  # Add answer options
            new_question.correct_answer = question[1]  # Set the correct answer
            self.questions.append(new_question)  # Add to the list of questions

class GameInstance(BaseScreen):
    def __init__(self, player):
        super().__init__()
        self.stage = Stage()  # Random background stage
        self.player = player
        self.player.player_instance.reset_stats()  # Reset stats for a new game
        self.start_time = None  
        self.elapsed_time = 0  # Time passed since start of gameplay
        self.small_font = pygame.font.Font("Assets/Font1.ttf", 50)
        self.smaller_font = pygame.font.Font("Assets/Font1.ttf", 30)
        self.all_buttons = button.ButtonManager()  # Manages on-screen buttons
        self.last_question_correct = False
        self.running = False  # Indicates if game is actively running
        self.player.player_instance.no_questions = 20  # Total number of questions in a game
        self.max_question_time = 60  # Time allocated per question (for score scaling)
        self.current_question_time = 0
        # Load sounds for feedback
        self.correct_answer_sound = pygame.mixer.Sound("Assets/Sounds/correct.mp3")
        self.wrong_answer_sound = pygame.mixer.Sound("Assets/Sounds/wrong.mp3")
        self.correct_answer_sound.set_volume(0.6)
        self.wrong_answer_sound.set_volume(0.8)

    def start_gameplay(self):
        self.running = True
        self.start_time = pygame.time.get_ticks()
        self.question_manager = QuestionManager(self.player)
        self.question_manager.create_questions(self.player.player_instance.no_questions)
        self.player.player_instance.new_high_score = False
        self.change_question(1)

    def change_question(self, number=None):
        # Update time for new question
        self.current_question_time = pygame.time.get_ticks()
        # If specific question number is provided
        if number:
            self.current_question_number = number
        else:
            self.current_question_number += 1

        # Check if game is over
        if self.current_question_number >= self.player.player_instance.no_questions + 1:
            self.end_game()
            return None

        # Load the current question and generate its answer buttons
        self.current_question = self.question_manager.questions[self.current_question_number - 1]
        self.make_answer_buttons()

    def handle_events(self, events, screen):
        self.all_buttons.handle_input(screen)

    def update(self, dt):
        # Update elapsed time and current question if game is running
        if self.running:
            if self.start_time is not None:
                self.elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000 
            self.current_question = self.question_manager.questions[self.current_question_number - 1]

    def make_answer_buttons(self):
        # Generate 4 answer buttons with randomized positions
        self.all_buttons.clear_buttons()
        self.answer_button_width = 300
        self.answer_button_height = 200
        self.answer_button_Y = SCREEN_HEIGHT - self.answer_button_height - 10
        self.button_images = []
        self.answer_buttons = []
        random.shuffle(self.current_question.answers)

        for i in range(4):
            current_answer = self.current_question.answers[i]
            current_answer_text = wrap_text(current_answer, self.smaller_font, self.answer_button_width - 6)
            current_answer_image = self.smaller_font.render(current_answer_text, True, "white")
            button_image = pygame.Surface((self.answer_button_width, self.answer_button_height))
            button_image.fill("darkblue")
            button_image.blit(current_answer_image, (0, 0))
            self.button_images.append(button_image)
            self.answer_buttons.append(button.Button((i * (self.answer_button_width + 10)), self.answer_button_Y, self.button_images[i]))
            
            # Link button to correct/wrong check
            if current_answer == self.current_question.correct_answer:
                self.all_buttons.add_button(self.answer_buttons[i], lambda: self.check_answer(True))
            else:
                self.all_buttons.add_button(self.answer_buttons[i], lambda: self.check_answer(False))

    def check_answer(self, correct):
        # Calculate time taken for question
        current_time = pygame.time.get_ticks()
        time_taken = (current_time - self.current_question_time) / 1000

        if correct:
            self.correct_answer_sound.play()
            self.last_question_correct = True
            self.player.player_instance.correct_questions += 1
        else:
            self.last_question_correct = False
            self.wrong_answer_sound.play()

        self.calculate_score(time_taken)
        self.change_question()

    def calculate_score(self, time_taken):
        self.set_combo()
        # Score based on time, accuracy, and combo multiplier
        base_score = 100 + max(0, (900 * ((self.max_question_time - time_taken) / self.max_question_time)))
        if self.last_question_correct:
            self.player.player_instance.score += int(base_score * (1 + 0.05 * self.player.player_instance.combo))
        else:
            penalty = int(base_score * 0.3) + 50
            self.player.player_instance.score -= penalty
            if self.player.player_instance.score < 0:
                self.player.player_instance.score = 0

    def set_combo(self):
        # Update combo count based on correctness
        if self.last_question_correct:
            self.player.player_instance.combo += 1
        else:
            self.player.player_instance.combo = 0

    def render_question(self, screen):
        # Display current question text in top right
        current_question_text = f"Q.{self.current_question_number} " + self.question_manager.questions[self.current_question_number - 1].question_text
        current_question_text = wrap_text(current_question_text, self.smaller_font, 700)
        current_question_text_image = self.smaller_font.render(current_question_text, True, "white")
        current_question_text_rect = current_question_text_image.get_frect(topright=(1200, 20))
        pygame.draw.rect(screen, "darkblue", current_question_text_rect.inflate(20, 30))
        screen.blit(current_question_text_image, current_question_text_rect)

    def end_game(self):
        # Save final stats and return to summary screen
        self.player.player_instance.total_time = self.elapsed_time
        if self.player.player_instance.score > self.player.player_data.high_score[self.player.player_instance.character][self.player.player_instance.subject][self.player.player_instance.topic]:
            self.set_new_high_score()
        self.running = False
        game.change_screen("game_summary")

    def set_new_high_score(self):
        # Update the database with a new high score if necessary
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()

        if self.player.player_data.logged_in:
            character_id = get_character_id(self.player.player_instance.character)
            subject_id = get_subject_id(self.player.player_instance.subject)
            topic_id = get_topic_id(self.player.player_instance.topic)
            self.player.player_instance.new_high_score = True

            if not self.player.has_high_score():
                # Insert new high score if one doesn't exist
                self.cursor.execute('''INSERT INTO HighScore (user_id, character_id, subject_id, topic_id, high_score)
                                       VALUES (?,?,?,?,?)''',
                                    (self.player.player_data.user_id, character_id, subject_id, topic_id, self.player.player_instance.score))
            else:
                # Update existing high score
                self.cursor.execute('''UPDATE HighScore
                                       SET high_score = ?
                                       WHERE user_id = ? AND character_id = ? AND subject_id = ? AND topic_id = ?''',
                                    (self.player.player_instance.score, self.player.player_data.user_id, character_id, subject_id, topic_id))
        
        self.connection.commit()
        self.connection.close()

    def render_game(self, screen):
        # Render gameplay visuals and HUD
        screen.blit(self.stage.background, (0, 0))

        if self.start_time is not None:
            # Render time, score, combo, and question counter
            time_text_image = self.small_font.render(f"Time: {self.elapsed_time:.2f}s", True, "white")
            time_text_rect = time_text_image.get_frect(topleft=(20, 20))
            pygame.draw.rect(screen, "darkblue", time_text_rect.inflate(20, 30))
            screen.blit(time_text_image, time_text_rect)

            score_text_image = self.small_font.render(f"Score: {self.player.player_instance.score}", True, "white")
            score_text_rect = score_text_image.get_frect(topleft=(20, 100))
            pygame.draw.rect(screen, "darkblue", score_text_rect.inflate(20, 30))
            screen.blit(score_text_image, score_text_rect)

            combo_text_image = self.small_font.render(f"Combo: {self.player.player_instance.combo}", True, "white")
            combo_text_rect = combo_text_image.get_frect(topleft=(20, 180))
            pygame.draw.rect(screen, "darkblue", combo_text_rect.inflate(20, 30))
            screen.blit(combo_text_image, combo_text_rect)

            question_number_image = self.smaller_font.render(f"Question {self.current_question_number} of {self.player.player_instance.no_questions}", True, "white")
            questnion_number_rect = question_number_image.get_frect(topleft=(20, 240))
            pygame.draw.rect(screen, "darkblue", questnion_number_rect.inflate(20, 30))
            screen.blit(question_number_image, questnion_number_rect)

        self.render_question(screen)
        self.all_buttons.render_buttons(screen)

    def render(self, screen):
        if self.running:
            self.render_game(screen)

class GameSummary(BaseScreen):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.heading_text = self.big_font.render("Game Summary", True, "antiquewhite4")
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH //2, 50))
        self.small_font = pygame.font.Font("Assets/Font1.ttf", 50)
        self.continue_text = self.big_font.render("Continue", True, "chartreuse1")
        self.continue_button = button.Button(0, 0, self.continue_text)
        self.all_buttons.add_button(self.continue_button, lambda: self.end_game_instance())
        self.continue_button.change_position(SCREEN_WIDTH //2, 600, "center")
    

    def end_game_instance(self):

        game.change_screen("main_menu")
    
    
    def handle_events(self, events, screen):
        self.all_buttons.handle_input(screen)

    def update(self, dt):
        if self.player.player_instance.new_high_score:
            temp = self.player.player_instance.score
        else:
            temp = self.player.player_data.high_score[self.player.player_instance.character][self.player.player_instance.subject][self.player.player_instance.topic]
        self.stats_text = (f"{self.player.player_instance.correct_questions}/{self.player.player_instance.no_questions} Questions Correct\n"+
                           f"Score: {self.player.player_instance.score} \n"
                           + f"High Score: {temp} \n"
                           + f"Total Time: {self.player.player_instance.total_time} \n"
                           + f"Character: {self.player.player_instance.character} \n"
                            + f"Subject: {self.player.player_instance.subject} \n"
                            + f"Topic: {self.player.player_instance.topic} \n"
                            )


        self.stats_text_surf = self.small_font.render(self.stats_text, True, "white")
        self.stats_text_rect = self.stats_text_surf.get_frect(topleft=(10, 150))


    def render(self, screen):
        screen.blit(self.background, (0, 0))
        screen.blit(self.heading_text, self.heading_text_rect)
        screen.blit(self.stats_text_surf, self.stats_text_rect)
        self.all_buttons.render_buttons(screen)

##
class GameSummary(BaseScreen):


    def __init__(self, player):
        super().__init__()
        self.player = player

        # Render heading text for the summary screen
        self.heading_text = self.big_font.render("Game Summary", True, "antiquewhite4")
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH // 2, 50))

        # Load smaller font for the stats text
        self.small_font = pygame.font.Font("Assets/Font1.ttf", 50)

        # Create the "Continue" button
        self.continue_text = self.big_font.render("Continue", True, "chartreuse1")
        self.continue_button = button.Button(0, 0, self.continue_text)

        # Add the button and bind its click to end_game_instance()
        self.all_buttons.add_button(self.continue_button, lambda: self.end_game_instance())

        # Position the "Continue" button at the bottom center
        self.continue_button.change_position(SCREEN_WIDTH // 2, 600, "center")
    
    def end_game_instance(self):
        # Change screen back to main menu when continue button is pressed
        game.change_screen("main_menu")
    
    def handle_events(self, events, screen):
        # Delegate event handling to the button manager
        self.all_buttons.handle_input(screen)

    def update(self, dt):
        # Determine the appropriate high score to display
        if self.player.player_instance.new_high_score:
            temp = self.player.player_instance.score
        else:
            temp = self.player.player_data.high_score[
                self.player.player_instance.character
            ][self.player.player_instance.subject][self.player.player_instance.topic]

        # Format the game stats text
        self.stats_text = (
            f"{self.player.player_instance.correct_questions}/{self.player.player_instance.no_questions} Questions Correct\n"
            f"Score: {self.player.player_instance.score} \n"
            f"High Score: {temp} \n"
            f"Total Time: {self.player.player_instance.total_time} \n"
            f"Character: {self.player.player_instance.character} \n"
            f"Subject: {self.player.player_instance.subject} \n"
            f"Topic: {self.player.player_instance.topic} \n"
        )

        # Render the stats text to a surface
        self.stats_text_surf = self.small_font.render(self.stats_text, True, "white")
        self.stats_text_rect = self.stats_text_surf.get_frect(topleft=(10, 150))

    def render(self, screen):
        # Draw the background, heading, stats, and buttons
        screen.blit(self.background, (0, 0))
        screen.blit(self.heading_text, self.heading_text_rect)
        screen.blit(self.stats_text_surf, self.stats_text_rect)
        self.all_buttons.render_buttons(screen)


class LoginScreen(BaseScreen):
    def __init__(self, player):
        super().__init__()
        # Heading text for the login screen
        self.heading_text = self.big_font.render("Login", True, "green")
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH // 2, 50))
        
        # Player instance
        self.player = player
        
        # Fonts for text rendering
        self.small_font = pygame.font.Font("Assets/Font1.ttf", 50)
        self.smaller_font = pygame.font.Font("Assets/Font1.ttf", 30)
        
        # Add the back button to go to the main menu
        self.all_buttons.add_button(self.back_button, lambda: game.change_screen("main_menu"))
        
        # Labels and input fields for username and password
        self.username_text = self.small_font.render("Username:", True, "green")
        self.username_text_rect = self.username_text.get_frect(topleft=(10, 150))
        self.password_text = self.small_font.render("Password:", True, "green")
        self.password_text_rect = self.password_text.get_frect(topleft=(10, 250))
        
        # Initialize the UI manager for text entry
        self.UI_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), "theme.json")    
        
        # Input fields for username and password
        self.username_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((10, 200), (900, 50)), manager=self.UI_manager, object_id="username_entry"
        )
        self.password_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((10, 300), (900, 50)), manager=self.UI_manager, object_id="password_entry"
        )
        
        # Submit button
        self.submit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 400), (100, 50)), text="Submit", manager=self.UI_manager
        )
        
        # Default error text
        self.error_text = "Please enter your Username and Password."
        
        # Sound to play when login succeeds
        self.login_sound = pygame.mixer.Sound("Assets/Sounds/ding.mp3")
        self.login_sound.set_volume(0.5)

    def update(self, dt):
        # Update UI manager (required for pygame_gui elements)
        self.UI_manager.update(dt)

    def handle_events(self, events, screen):
        # Handle input events for buttons and text fields
        self.all_buttons.handle_input(screen)
        for event in events:
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.submit_button:
                    username_text = self.username_input.get_text()
                    password_text = self.password_input.get_text()
                    self.check_username_and_password(username_text, password_text)
            self.UI_manager.process_events(event)

    def check_username_and_password(self, username, password):
        # Check username and password from the database
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()
        
        # Check if username exists
        if not RegisterScreen(self.player).username_exists(username):
            self.error_text = "Username does not exist"
        # Validate password length
        elif len(password) >= 20 or len(password) < 5:
            self.error_text = "Password should be between 5-20 characters."
        else:
            # Fetch hashed password and salt from the database
            self.cursor.execute("SELECT hash, salt FROM User WHERE username = ?", (username,))
            old_hash, old_salt = self.cursor.fetchone()
            self.connection.close()
            
            # Hash the entered password with the salt and check for match
            new_hash, new_salt = RegisterScreen(self.player).hash_password(password, old_salt)
            if new_hash == old_hash:
                # If password matches, log the user in
                self.log_user_in(username)
                self.username_input.clear()
                self.password_input.clear()
                game.change_screen("main_menu")
            else:
                self.error_text = "Username or Password do not match"
        self.connection.close()

    def log_user_in(self, username):
        # Log the user in and update their player data
        self.player.player_data.logged_in = True
        self.player.player_data.username = username
        self.player.player_data.user_id = get_user_id(username)
        self.login_sound.play()

    def render_error(self, screen):
        # Render error text if any error occurs
        current_error_text = wrap_text(self.error_text, self.smaller_font, 700)
        current_error_text_image = self.smaller_font.render(current_error_text, True, "white")
        current_error_text_rect = current_error_text_image.get_frect(topleft=(200, 400))
        
        # Draw a background rectangle for the error message
        pygame.draw.rect(screen, "darkblue", current_error_text_rect.inflate(20, 30))
        screen.blit(current_error_text_image, current_error_text_rect)
        
    def render(self, screen):
        # Render the background and UI elements
        screen.blit(self.background, (0, 0))
        screen.blit(self.heading_text, self.heading_text_rect)
        screen.blit(self.username_text, self.username_text_rect)
        screen.blit(self.password_text, self.password_text_rect)
        
        # Render the error message if there is one
        if self.error_text != None:
            self.render_error(screen)
        
        # Render buttons and other UI elements
        self.all_buttons.render_buttons(screen)
        self.UI_manager.draw_ui(screen)


class RegisterScreen(BaseScreen):
    def __init__(self, player):
        super().__init__()

        # Fonts
        self.small_font = pygame.font.Font("Assets/Font1.ttf", 50)
        self.smaller_font = pygame.font.Font("Assets/Font1.ttf", 30)

        # Title heading
        self.heading_text = self.big_font.render("Register", True, "red")
        self.heading_text_rect = self.heading_text.get_frect(center=(SCREEN_WIDTH // 2, 50))

        # Player instance reference
        self.player = player

        # Back button setup
        self.all_buttons.add_button(self.back_button, lambda: game.change_screen("main_menu"))

        # Labels for inputs
        self.username_text = self.small_font.render("Username:", True, "red")
        self.username_text_rect = self.username_text.get_frect(topleft=(10, 150))

        self.password_text = self.small_font.render("Password:", True, "red")
        self.password_text_rect = self.password_text.get_frect(topleft=(10, 250))

        self.confirm_password_text = self.small_font.render("Confirm Password:", True, "red")
        self.confirm_password_text_rect = self.confirm_password_text.get_frect(topleft=(10, 350))

        # UI manager for handling text fields and buttons
        self.UI_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), "theme.json")

        # Input fields
        self.username_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((10, 200), (900, 50)),
            manager=self.UI_manager,
            object_id="username_entry"
        )

        self.password_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((10, 300), (900, 50)),
            manager=self.UI_manager,
            object_id="password_entry"
        )

        self.confirm_password_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((10, 400), (900, 50)),
            manager=self.UI_manager,
            object_id="confirm_password_entry"
        )

        # Submit button
        self.submit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 450), (100, 50)),
            text="Submit",
            manager=self.UI_manager
        )

        # Default error message
        self.error_text = "Warning: Don't use the actual passwords you use for other programs. The security for this program is not industry standard."

    def handle_events(self, events, screen):
        """
        Handles button presses and passes events to UI manager.
        """
        self.all_buttons.handle_input(screen)
        for event in events:
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.submit_button:
                    # Retrieve input text
                    username_text = self.username_input.get_text()
                    password_text = self.password_input.get_text()
                    confirm_password_text = self.confirm_password_input.get_text()

                    # Validate inputs
                    self.check_inputs(username_text, password_text, confirm_password_text)

            # Pass event to UI manager
            self.UI_manager.process_events(event)

    def check_inputs(self, username, password, confirm_password):
        """
        Validates registration fields and triggers registration if valid.
        """
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
            self.error_text = "Username already exists."
        else:
            # If all checks pass, insert into database
            self.add_details_to_db(username, password)

    def add_details_to_db(self, username, password):
        """
        Hashes and stores new user details into the database.
        """
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()

        # Hash the password with a generated salt
        hashed_password, salt = self.hash_password(password)

        # Get current time
        current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Store user details in DB
        self.cursor.execute('''INSERT INTO User(username, hash, salt, time_created)
                               VALUES (?, ?, ?, ?)''', 
                               (username, hashed_password, salt, current_timestamp))

        self.connection.commit()
        self.connection.close()

        # Log in user and change screen
        LoginScreen(self.player).log_user_in(username)
        game.change_screen("main_menu")

    def hash_password(self, password, salt=None):
        """
        Custom password hashing function with salt (not industry-standard).
        """
        if salt is None:
            salt = os.urandom(16)

        combined = password.encode('utf-8') + salt
        hash_value = 10061

        # Basic (non-secure) custom hash algorithm
        for byte in combined:
            hash_value = ((hash_value << 5) + hash_value) ^ byte

        return hex(hash_value), salt

    def username_exists(self, username):
        """
        Checks if a username already exists in the database.
        """
        self.connection = sqlite3.connect("main.db")
        self.cursor = self.connection.cursor()
        self.cursor.execute('''SELECT 1 FROM User WHERE username = ?''', (username,))
        temp = self.cursor.fetchone()
        self.connection.close()
        return temp is not None

    def render_error(self, screen):
        """
        Draws error message on screen with background.
        """
        current_error_text = wrap_text(self.error_text, self.smaller_font, 700)
        current_error_text_image = self.smaller_font.render(current_error_text, True, "white")
        current_error_text_rect = current_error_text_image.get_frect(topleft=(200, 480))
        pygame.draw.rect(screen, "darkblue", current_error_text_rect.inflate(20, 30))
        screen.blit(current_error_text_image, current_error_text_rect)

    def update(self, dt):
        """
        Updates UI manager.
        """
        self.UI_manager.update(dt)

    def render(self, screen):
        """
        Renders all UI components and error message.
        """
        screen.blit(self.background, (0, 0))
        screen.blit(self.heading_text, self.heading_text_rect)
        screen.blit(self.username_text, self.username_text_rect)
        screen.blit(self.password_text, self.password_text_rect)
        screen.blit(self.confirm_password_text, self.confirm_password_text_rect)
        self.all_buttons.render_buttons(screen)

        if self.error_text:
            self.render_error(screen)

        self.UI_manager.draw_ui(screen)

class Game:
    def __init__(self):
        # Sets up the initial game state, initializes Pygame and loads all screens and the player
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.player = Player()
        self.screens = {
            "main_menu": MainMenuScreen(self.player),
            "game_screen": None, 
            "character_select_screen": CharacterSelectScreen(self.screen, self.player),
            "subject_select_screen": SubjectSelectScreen(self.player),
            "topic_select_screen": TopicSelectScreen(self.player),
            "confirm_screen": ConfirmScreen(self.player),
            "game_summary": GameSummary(self.player),
            "register_screen": RegisterScreen(self.player),
            "login_screen" : LoginScreen(self.player)
        }
        self.current_screen = "main_menu"

    def change_screen(self, screen):
        # Switches the current screen to another one, and triggers any necessary screen-specific setup
        self.current_screen = screen
        if screen == "game_screen":
            self.screens[screen] = GameInstance(self.player)
            game_screen = self.screens[screen]
            game_screen.start_gameplay() 
        if screen == "login_screen":
            login_screen = self.screens[screen]
            login_screen.error_text = "Please enter your Username and Password"
        if screen == "register_screen":
            register_screen = self.screens[screen]
            register_screen.error_text = "Warning: Don't use the actual passwords you use for other programs. The security for this program is not industry standard."
        if screen == "topic_select_screen":
            topic_select_screen = self.screens[screen]
            topic_select_screen.start_screen()

    def run(self):
        # Main game loop: handles events, updates, renders the current screen, and manages quitting
        while self.running:
            dt = self.clock.tick(FPS) / 1000  
            events = pygame.event.get()
            pygame.display.set_caption(f"{self.current_screen}")
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            # Get the current screen instance
            screen_instance = self.screens[self.current_screen]
            screen_instance.handle_events(events, self.screen)
            screen_instance.update(dt)
            screen_instance.render(self.screen)

            pygame.display.flip()

        pygame.quit()


def get_character_id(character):
    connection = sqlite3.connect("main.db")
    cursor = connection.cursor()
    cursor.execute(f'''SELECT character_id
                        FROM Characters
                        WHERE character_name = ?''', (character,))
    temp = cursor.fetchone()
    connection.close()
    return temp[0]

def get_subject_id(subject):
    connection = sqlite3.connect("main.db")
    cursor = connection.cursor()
    cursor.execute(f'''SELECT subject_id
                        FROM Subject
                        WHERE subject_name = ?''', (subject,))
    temp = cursor.fetchone()
    connection.close()
    return temp[0]

def get_topic_id(topic):
    connection = sqlite3.connect("main.db")
    cursor = connection.cursor()
    cursor.execute(f'''SELECT topic_id
                        FROM Topic
                        WHERE topic_text = ?''', (topic,))
    temp = cursor.fetchone()
    connection.close()
    return temp[0]

def get_user_id(username):
    connection = sqlite3.connect("main.db")
    cursor = connection.cursor()
    cursor.execute(f'''SELECT user_id
                        FROM User
                        WHERE username = ?''', (username,))
    temp = cursor.fetchone()
    connection.close()
    return temp[0]

if __name__ == "__main__":
    game = Game()
    game.run()

