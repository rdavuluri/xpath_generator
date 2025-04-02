import streamlit as st
import openai
import re

# Define the XPath generation prompt
XPATH_GENERATION_PROMPT = """
Generate the top 5 XPath expressions to locate a target element within the provided HTML context. Prioritize accuracy, robustness, and performance. Follow these guidelines meticulously:

**Input Processing and Contextual Understanding:**

1.  **HTML Snippet Analysis:**
    * Thoroughly parse the provided HTML snippet to understand the DOM structure, including parent-child relationships, sibling relationships, and attribute values.
    * Identify potential iframe elements and adjust XPath construction accordingly.
2.  **Target Element Description:**
    * Precisely interpret the target element's description, including its text content, attributes, and expected behavior.
    * Pay close attention to any specified states (e.g., visible, enabled, expanded, selected).
3.  **Page Context Awareness:**
    * Consider the broader page structure, if available, to ensure the generated XPath expressions are not overly specific to the provided snippet.
    * Analyze surrounding elements and their attributes to identify stable locators.
4.  **Attribute Reliability Assessment:**
    * Distinguish between static and dynamic attributes.
    * Prefer static attributes (e.g., `id`, `name`, `type`, `role`, `aria-*`) for robustness.
    * Use dynamic attributes only when explicitly specified as reliable or when no other stable locators are available.
5.  **Element State Handling:**
    * Incorporate state-aware predicates (e.g., `[@aria-expanded='true']`, `[@disabled='false']`, `[contains(@class, 'visible')]`) when the target element's state is relevant.
6.  **User Ranking Preferences:**
    * If specific ranking criteria are provided (e.g., prioritize `id`, minimize use of `contains()`), strictly adhere to them.

**XPath Construction and Output Format:**

1.  **XPath Expression Generation:**
    * Construct 5 distinct XPath expressions, each offering a unique approach to locating the target element.
    * Aim for diversity in XPath axes (e.g., `//`, `/`, `ancestor::`, `descendant::`, `following-sibling::`, `preceding-sibling::`).
    * Minimize the use of index-based selectors (`[n]`) due to their fragility.
    * Favor text-based selectors (`text()`, `contains(text(), '...')`) or structural selectors when attributes are unreliable.
    * Handle iframe cases by preceding the target xpath with the iframe xpath.
2.  **Output Format for Each XPath:**
    * "XPath: [The complete XPath expression]"
    * "Advantage: [A concise explanation of the expression's key strength (e.g., robustness, simplicity, performance)]"
    * "Disadvantage: [A brief description of the expression's potential weaknesses (e.g., fragility, performance overhead)]"
    * "Explanation: [A detailed explanation of the syntax and logic used in the XPath expression, including the chosen axes, predicates, and functions.]"

**XPath Construction Best Practices:**

* **Robustness:** Prioritize XPath expressions that are resilient to minor changes in the HTML structure.
* **Performance:** Consider the performance implications of different XPath approaches. Avoid overly complex expressions or those that traverse a large portion of the DOM.
* **Maintainability:** Aim for XPath expressions that are easy to understand and maintain.
* **Clarity:** Write clear and concise explanations for each XPath expression, making it easy to understand the logic behind it.
* **Specificity vs. Generality:** Find the balance of specific and general xpaths. Too specific, and small changes break it. Too general, and it grabs the wrong element.
* **Use of contains() and starts-with():** Use these functions when dealing with dynamic text or attribute values. But use them carefully.
* **Use of normalize-space():** Use this function when dealing with text that contains whitespace.

By adhering to these guidelines, you will generate XPath expressions that are accurate, robust, and efficient for locating target elements within the provided HTML context.
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
