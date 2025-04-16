import streamlit as st
import openai
import re

# Define the XPath generation prompt
XPATH_GENERATION_PROMPT = """
You are an expert XPath Generator for Selenium automation and web scraping. Generate the top 5 XPath expressions to locate the target element within the provided HTML context, prioritizing accuracy, robustness, performance, and cross-browser compatibility (Chrome, Firefox, Edge). Follow these guidelines meticulously:

**Input Processing and Contextual Understanding:**
1. **HTML Snippet Analysis**:
   - Thoroughly parse the provided HTML snippet to understand the DOM structure, including parent-child relationships, sibling relationships, and attribute values.
   - Identify potential iframe or shadow DOM elements and adjust XPath construction accordingly.
   - If shadow DOM is present, provide methods for traversal using Selenium's `execute_script` or `shadowRoot`.
2. **Target Element Description**:
   - Interpret the target element's description (e.g., tag, attributes, text content, states like visible or enabled).
   - Default to the element specified in the description or HTML (e.g., a `div` with `data-test='target-element'` if not specified).
3. **Page Context Awareness**:
   - Use provided page context to ensure XPaths are not overly specific to the snippet.
   - Analyze surrounding elements to identify stable locators (e.g., `id`, `data-test`, `role`).
4. **Attribute Reliability**:
   - Prefer static attributes (e.g., `id`, `name`, `data-test`, `aria-*`) over dynamic ones (e.g., auto-generated `class`).
   - Use dynamic attributes only when explicitly marked as reliable in the 'Dynamic Attributes Flag'.
5. **Element State Handling**:
   - Incorporate state-aware predicates (e.g., `[@aria-expanded='true']`, `[@disabled='false']`) if specified in 'Element State'.
6. **User Ranking Preferences**:
   - Adhere to ranking preferences (e.g., prioritize `id`, avoid `contains()`) if provided.

**XPath Construction and Output Format:**
1. **XPath Expression Generation**:
   - Construct 5 distinct XPath expressions using diverse axes (e.g., `/`, `//`, `ancestor::`, `descendant::`).
   - Minimize index-based selectors (`[n]`) due to fragility.
   - Use text-based selectors (`text()`, `contains(text(), '...')`) or `normalize-space()` only when attributes are unreliable.
   - For iframes, prepend the iframe's XPath (e.g., `//iframe[@id='frame']`).
   - For shadow DOM, provide Selenium code to access the element.
2. **Output Format for Each XPath**:
   - **XPath**: `[The complete XPath expression]`
   - **Advantage**: `[Key strength, e.g., robustness, performance]`
   - **Disadvantage**: `[Potential weakness, e.g., fragility, performance overhead]`
   - **Explanation**: `[Detailed explanation of syntax, axes, predicates, and logic]`
   - **Selenium (Python)**: `[Python code snippet with comments and try-catch]`
   - **Selenium (Java)**: `[Java code snippet with comments and try-catch]`
   - **Edge Case Handling**: `[Scenarios like dynamic loading, missing attributes, localization, and mitigations]`
   - **Architectural Notes**: `[Broader considerations, e.g., pipeline integration, reusability]`
3. **Ranking**:
   - Rank the 5 XPaths by prioritizing High stability, Excellent performance, and maintainability.

**XPath Construction Best Practices:**
- **Robustness**: Ensure resilience to minor DOM changes (e.g., added classes).
- **Performance**: Use efficient axes:
  - **Excellent**: O(1) complexity, direct axes (e.g., `/[@id='app']`).
  - **Good**: O(log n), relative paths with minimal `//`.
  - **Fair**: O(n), limited `//` with unique attributes.
  - **Poor**: O(n^2), text-based or complex predicates.
- **Maintainability**: Balance specificity and generality to avoid brittle or overly broad XPaths.
- **Clarity**: Write clear explanations for team collaboration.
- **Cross-Browser Compatibility**: Ensure XPaths work in Chrome, Firefox, and Edge, noting quirks (e.g., Firefox’s shadow DOM limitations).
- **Dynamic Attributes**: Use parent stability or semantic attributes if dynamic attributes are specified.
- **Localization**: Avoid `text()` for text that may change due to language settings.
- **Validation**: Recommend testing XPaths with `document.evaluate` or Selenium’s `findElements`.

**Testing Guidance**:
- Provide a markdown table comparing the 5 XPaths (columns: XPath, Stability, Performance, Use Case).
- Suggest testing in browser DevTools (`$x()`) and Selenium to verify uniqueness and robustness.

By adhering to these guidelines, generate XPath expressions that are accurate, robust, efficient, and suitable for production-grade Selenium automation.
"""


class XPathGeneratorAgent:
    def __init__(self, api_key: str):
        try:
            # Initialize OpenAI client.  We no longer try to set proxies here.
            self.client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            st.error(f"Failed to initialize OpenAI client: {str(e)}")
            st.stop()

        self.system_prompt = f"""
        You are an expert XPath Generator for Selenium automation and web scraping.
        Always format XPath expressions with proper syntax highlighting using markdown code blocks.
        When given HTML, analyze it thoroughly to identify optimal XPath patterns.
        Use markdown tables to compare different XPath strategies.
        Always include testing guidance with your XPath recommendations.
        {XPATH_GENERATION_PROMPT}
        """

    def generate_xpaths(
            self,
            html_snippet: str,
            element_description: str = None,
            page_context: str = None,
            dynamic_attributes: str = None,
            element_state: str = None,
            ranking_preferences: str = None,
    ) -> str:
        user_message = (
            f"Please generate XPath expressions for the following:\n\n[HTML Snippet] = {html_snippet}"
        )

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

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.2,
                max_tokens=3000,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating XPaths: {str(e)}"


# Streamlit app
st.set_page_config(page_title="XPath Generator", page_icon="🔍", layout="wide")
st.title("XPath Generator")

with st.sidebar:
    st.header("API Configuration")
    api_key = st.text_input("OpenAI API Key", type="password")
    st.caption("Your API key is not stored and is only used for this session.")

    st.header("About")
    st.info(
        """
    This XPath Generator helps automation engineers create robust XPath expressions
    for web elements. Provide HTML snippets and element details to get optimized XPaths
    with Selenium code snippets for Python and Java.
    """
    )

tab1, tab2 = st.tabs(["Generate XPaths", "Documentation"])

with tab1:
    with st.form("xpath_input_form"):
        html_snippet = st.text_area(
            "HTML Snippet",
            height=200,
            placeholder="<div id='app'><section class='content'><custom-component><div class='inner'><div data-test='target-element'>Target</div></div></custom-component></section></div>",
        )

        col1, col2 = st.columns(2)
        with col1:
            element_description = st.text_input(
                "Element Description (Optional)",
                placeholder="A div with data-test='target-element'",
            )
            page_context = st.text_input(
                "Page Context (Optional)",
                placeholder="This appears in a main content area with shadow DOM",
            )

        with col2:
            dynamic_attributes = st.text_input(
                "Dynamic Attributes Flag (Optional)",
                placeholder="The 'data-test' attribute is reliable, but 'class' is dynamic",
            )
            element_state = st.text_input(
                "Element State (Optional)", placeholder="Element must be visible"
            )

        ranking_preferences = st.text_input(
            "Ranking Preferences (Optional)",
            placeholder="Prioritize id-based selectors and structural paths",
        )

        submit_button = st.form_submit_button("Generate XPaths")

    if submit_button:
        if not api_key:
            st.error("Please enter your OpenAI API key in the sidebar.")
        elif not html_snippet:
            st.warning("Please provide an HTML snippet to generate XPaths.")
        else:
            with st.spinner("Generating XPath expressions..."):
                try:
                    agent = XPathGeneratorAgent(api_key=api_key)
                    response = agent.generate_xpaths(
                        html_snippet=html_snippet,
                        element_description=element_description,
                        page_context=page_context,
                        dynamic_attributes=dynamic_attributes,
                        element_state=element_state,
                        ranking_preferences=ranking_preferences,
                    )

                    st.markdown("## Generated XPath Expressions")
                    st.markdown(response)

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
    st.markdown(
        """
    1. Enter your OpenAI API key in the sidebar.
    2. Provide an HTML snippet containing your target element.
    3. Fill in optional fields to refine the XPath generation:
       - Element Description: What element you're trying to locate.
       - Page Context: Where this element appears on the page.
       - Dynamic Attributes: Which attributes are reliable vs dynamic.
       - Element State: Any state requirements (visible, enabled, etc.).
       - Ranking Preferences: How you want the XPaths to be prioritized.
    4. Click "Generate XPaths" to get your results, including Selenium code for Python and Java.
    """
    )
    st.subheader("XPath Best Practices")
    st.markdown(
        """
    - **Reliability**: Use stable attributes like `id`, `data-test`, and `aria-*`.
    - **Maintainability**: Prefer concise XPaths with clear explanations.
    - **Performance**: Use direct axes (`/`) and unique attributes for faster queries.
    - **Robustness**: Avoid text-based selectors for localized content.
    - **Cross-Browser**: Test XPaths in Chrome, Firefox, and Edge.
    """
    )
    st.subheader("Testing Your XPaths")
    st.code(
        """
# In Chrome/Firefox DevTools Console:
$x("//your/xpath/here")
# In Selenium (Python):
from selenium.webdriver.common.by import By
try:
    driver.find_element(By.XPATH, "//your/xpath/here")
except NoSuchElementException:
    print("Element not found")
# In Selenium (Java):
try {
    driver.findElement(By.xpath("//your/xpath/here"));
} catch (NoSuchElementException e) {
    System.out.println("Element not found");
}
    """,
        language="javascript",
    )


if __name__ == "__main__":
    # This is only needed when running the script directly, not when using streamlit run
    pass
