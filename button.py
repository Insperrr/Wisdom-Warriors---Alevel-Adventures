import pygame

class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, image, scale=1):
        super().__init__()
        if isinstance(image, pygame.Rect):
            self.width = image.width
            self.height = image.height
        else:
            self.width, self.height = image.get_width(), image.get_height()
        self.image = pygame.transform.scale(image, (int((self.width * scale)), int(self.height * scale)))
        self.rect = self.image.get_frect(topleft=(x, y))
        self.clicked = False

    def change_position(self, x, y, axis="topleft"):
        if hasattr(self.rect, axis):   # type: ignore
            setattr(self.rect, axis, (x, y))  # type: ignore
        else:
            raise ValueError(f"Invalid axis '{axis}'. Must be a valid Rect attribute like 'topleft' or 'center'.")

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def is_hovered(self, mouse_position):
        return self.rect.collidepoint(mouse_position)

class ButtonManager:
    def __init__(self):
        self.buttons = []

    def add_button(self, button, left_click_action=None, right_click_action=None, touching_action=None):
        self.buttons.append({
            "button": button,
            "left_click_action": left_click_action,
            "right_click_action": right_click_action,
            "touching_action": touching_action,
        })

    def render_buttons(self, screen):
        buttons = [buttons["button"] for buttons in self.buttons]
        for button in buttons:
            button.draw(screen)


    def handle_input(self, screen):
        mouse_position = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_just_pressed()
        click_handled = False
        if mouse_pressed[0] == 0:
            click_handled = False
        for button_data in self.buttons:
            button = button_data["button"]
            if button.is_hovered(mouse_position):
                if mouse_pressed[0] == 1 and not click_handled:  # Mouse press event
                    if button_data["left_click_action"]:
                        button_data["left_click_action"]()
                    click_handled = True
                elif mouse_pressed[2] == 1 and not click_handled:  # Right mouse press event
                    if button_data["right_click_action"]:
                        button_data["right_click_action"]()
                    click_handled = True
                elif not click_handled:
                    if button_data["touching_action"]:
                        button_data["touching_action"]()

    def clear_buttons(self):
        self.buttons = []