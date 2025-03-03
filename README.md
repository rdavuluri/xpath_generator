# XPath Generator

A Streamlit-based web application that generates robust XPath expressions for web automation using OpenAI's GPT models. This tool helps automation engineers create reliable XPaths by analyzing HTML snippets and optional contextual details.

## Features
- Generate the top 5 XPath expressions for a target element.
- Analyze HTML snippets and element descriptions.
- Customize XPath generation with dynamic attribute flags, element states, and ranking preferences.
- View results with advantages, disadvantages, and testing guidance.
- Copy generated XPaths easily for use in automation frameworks like Selenium or Cypress.

## Installation

Follow these steps to set up the project locally:

### Prerequisites
- Python 3.8 or higher
- An OpenAI API key (sign up at [OpenAI](https://platform.openai.com/) to get one)

### Steps
1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/xpath-generator.git
   cd xpath-generator
   
2. **Install the required dependencies**
   ```bash
   pip install -r requirements.txt

3. **Run the Application**
    ```bash
   streamlit run xpath_generator_agent.py
