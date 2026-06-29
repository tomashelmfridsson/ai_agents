from __future__ import annotations


DEFAULT_TITLE = "Demo: web application for login and registration"
DEFAULT_REQUIREMENTS = """The user must be able to sign in with email and password.
The system shall display a clear error message when credentials are invalid.
An administrator shall be able to view an overview of registered users.
The user shall be able to register a new account through a form."""

SAMPLE_SCENARIOS = {
    "Scenario 1": {
        "title": DEFAULT_TITLE,
        "requirements": DEFAULT_REQUIREMENTS,
    },
    "Scenario 2": {
        "title": "E-commerce checkout and order confirmation",
        "requirements": """The customer must be able to add a product to the shopping cart.
The system shall calculate the total price including tax before checkout.
The customer must be able to complete payment with a valid card.
The system shall display an order confirmation after a successful purchase.""",
    },
    "Scenario 3": {
        "title": "Password reset and account recovery",
        "requirements": """The user shall be able to request a password reset using an email address.
The system must send a reset link only to registered email addresses.
The user must be able to set a new password through the reset form.
The system shall show a clear error message when the reset token is invalid or expired.""",
    },
    "Scenario 4": {
        "title": "Support ticket creation and status tracking",
        "requirements": """The customer shall be able to create a support ticket from a form.
The system shall validate that subject and description are provided before submission.
The support agent must be able to update the ticket status.
The customer shall be able to view the current ticket status in the portal.""",
    },
    "Scenario 5": {
        "title": "Inventory management for warehouse staff",
        "requirements": """A warehouse operator must be able to register incoming stock.
The system shall prevent negative inventory values.
A manager shall be able to view a list of products below the reorder threshold.
The system shall log every stock adjustment with timestamp and user identity.""",
    },
    "Scenario 6": {
        "title": "Course enrollment in a student portal",
        "requirements": """A student must be able to browse available courses for the current term.
The student shall be able to enroll in a course with available seats.
The system must block enrollment when prerequisites are not fulfilled.
The system shall display a confirmation when enrollment succeeds.""",
    },
}

DEFAULT_SCENARIO = "Scenario 1"


def load_sample_scenario(
    selected_scenario: str, current_title: str, current_requirements: str
) -> tuple[str, str]:
    if selected_scenario == "Custom scenario":
        return current_title, current_requirements
    scenario = SAMPLE_SCENARIOS.get(selected_scenario, SAMPLE_SCENARIOS[DEFAULT_SCENARIO])
    return scenario["title"], scenario["requirements"]
