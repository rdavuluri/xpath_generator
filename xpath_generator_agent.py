import streamlit as st
import openai
import re

# Define the XPath generation prompt
XPATH_GENERATION_PROMPT = """
Generate the top 5 XPath expressions to locate a target element on a webpage. Follow these guidelines:

**Input Processing:**
- HTML Snippet: Analyze the provided HTML structure
- Element Description: Understand the target element characteristics
- Page Context: Consider the broader page structure when relevant
- Dynamic Attributes: Respect flags about reliable vs dynamic attributes
- Element State: Account for visible/enabled/expanded states if specified
- Ranking Preferences: Apply user's ranking criteria if provided

**XPath Construction Guidelines:**
- Avoid dynamic attributes unless specified as reliable
- Prefer stable attributes (id, name, type, role, aria-*)
- Use text-based or structural selectors when attributes are unreliable
- Create diverse expressions using different XPath axes
- Consider performance implications of different approaches
- Handle iframe scenarios when applicable
- Include state-aware predicates when needed
- Be cautious with index-based selectors

For each XPath, provide:
1. The complete XPath expression
2. One key advantage
3. One key disadvantage
4. Brief explanation of the syntax and logic
"""

class XPathGeneratorAgent:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.system_prompt = f"""
        You are an expert XPath Generator for web automation.
        Always format XPath expressions with proper syntax highlighting using markdown code blocks.
        When given HTML, analyze it thoroughly to identify optimal XPath patterns.
        Use markdown tables to compare different XPath strategies.
        Always include testing guidance with your XPath recommendations.
        {XPATH_GENERATION_PROMPT}
        """

    def generate_xpaths(self,
                        html_snippet: str,
                        element_description: str = None,
                        page_context: str = None,
                        dynamic_attributes: str = None,
                        element_state: str = None,
                        ranking_preferences: str = None) -> str:
        """
        Generate XPath expressions based on the provided inputs.
        """
        # Construct the user message
        user_message = f"Please generate XPath expressions for the following:\n\n[HTML Snippet] = {html_snippet}"

        if element_description:
            user_message += f"\n[Element Description] = {element_description}"
        if page_context:
            user_message += f"\n[Page Context] = {page_context}"
        if dynamic_attributes:
            user_message += f"\n[Dynamic Attributes Flag] = {dynamic_attributes}"
        if element_state:
            user_message += f"\n[Element State] = {element_state}"
        if ranking_preferences:
            user_message += f"\n[Ranking Preferences] = {ranking_preferences}"

        # Call the OpenAI API
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",  # Replace with gpt-4.5-turbo when available
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=2500
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating XPaths: {str(e)}"

# Streamlit app
st.set_page_config(page_title="XPath Generator", page_icon="🔍", layout="wide")
st.title("XPath Generator")

# API key configuration in sidebar
with st.sidebar:
    st.header("API Configuration")
    api_key = st.text_input("OpenAI API Key", type="password")
    st.caption("Your API key is not stored and is only used for this session.")

    st.header("About")
    st.info("""
    This XPath Generator helps automation engineers create robust XPath expressions
    for web elements. Provide HTML snippets and element details to get optimized XPaths.
    """)

# Main content area
tab1, tab2 = st.tabs(["Generate XPaths", "Documentation"])

with tab1:
    # Input form
    with st.form("xpath_input_form"):
        html_snippet = st.text_area("HTML Snippet", height=200,
                                    placeholder="<div class=\"login-form\"><button type=\"submit\">Login</button></div>")

        col1, col2 = st.columns(2)
        with col1:
            element_description = st.text_input("Element Description (Optional)",
                                                placeholder="A button labeled 'Login' with type='submit'")
            page_context = st.text_input("Page Context (Optional)",
                                         placeholder="This appears in a login form in the main content area")

        with col2:
            dynamic_attributes = st.text_input("Dynamic Attributes Flag (Optional)",
                                               placeholder="The 'id' attribute is reliable, but 'class' is dynamic")
            element_state = st.text_input("Element State (Optional)",
                                          placeholder="Element must be visible and enabled")

        ranking_preferences = st.text_input("Ranking Preferences (Optional)",
                                            placeholder="Prioritize id-based selectors and structural paths")

        submit_button = st.form_submit_button("Generate XPaths")

    # Process when form is submitted
    if submit_button:
        if not api_key:
            st.error("Please enter your OpenAI API key in the sidebar.")
        elif not html_snippet:
            st.warning("Please provide an HTML snippet to generate XPaths.")
        else:
            with st.spinner("Generating XPath expressions..."):
                try:
                    # Create agent and generate XPaths
                    agent = XPathGeneratorAgent(api_key=api_key)
                    response = agent.generate_xpaths(
                        html_snippet=html_snippet,
                        element_description=element_description,
                        page_context=page_context,
                        dynamic_attributes=dynamic_attributes,
                        element_state=element_state,
                        ranking_preferences=ranking_preferences
                    )

                    # Display response
                    st.markdown("## Generated XPath Expressions")
                    st.markdown(response)

                    # Extract XPath expressions for easy copying
                    xpath_pattern = r'```[^\n]*\n(//[^`]+)'
                    xpaths = re.findall(xpath_pattern, response)

                    if xpaths:
                        st.subheader("Quick Copy")
                        for i, xpath in enumerate(xpaths[:5], 1):
                            xpath = xpath.strip()
                            st.code(xpath, language="xpath")

                    st.success("XPath expressions generated successfully!")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

with tab2:
    st.header("XPath Generator Documentation")

    st.subheader("How to Use")
    st.markdown("""
    1. Enter your OpenAI API key in the sidebar
    2. Provide an HTML snippet containing your target element
    3. Fill in optional fields to refine the XPath generation:
       - Element Description: What element you're trying to locate
       - Page Context: Where this element appears on the page
       - Dynamic Attributes: Which attributes are reliable vs dynamic
       - Element State: Any state requirements (visible, enabled, etc.)
       - Ranking Preferences: How you want the XPaths to be prioritized
    4. Click "Generate XPaths" to get your results
    """)

    st.subheader("XPath Best Practices")
    st.markdown("""
    - **Reliability**: Use stable attributes like ID, name, and ARIA attributes
    - **Maintainability**: Shorter paths are generally easier to maintain
    - **Performance**: ID-based selectors are typically the fastest
    - **Robustness**: Avoid relying on specific text that might change due to localization
    - **Testing**: Always validate your XPaths in the browser before using in automation
    """)

    st.subheader("Testing Your XPaths")
    st.code("""
# In Chrome/Firefox DevTools Console:
$x("//your/xpath/here")

# In Selenium (Python):
driver.find_element(By.XPATH, "//your/xpath/here")

# In Cypress:
cy.xpath("//your/xpath/here")
    """, language="javascript")

if __name__ == "__main__":
    # This is only needed when running the script directly, not when using streamlit run
    pass
