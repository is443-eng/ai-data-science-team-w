**Baseline to build on**
Create App V2 in a new standalone folder while copying over relevant files from "dashboard" folder and "Shiny App V1" folder. Build all improvements in this new folder. 

**Improvement actions for V2**
- Add a loading indicator to each screen while query runs 
- Change LLM model to gemma4:31b-cloud
- Take V1 API calls and turn them into an LLM Toolset, one tool for each API 
- Ensure tool calls are backwards compatible with current dashboard views
- Build a multiple agent workflow with a central agent orchestrator that manages: 
-- Agent 1 - call API tools and feed to dashboard and next agents
-- Agent 2 - Summarize data from Agent 1 for a given US state selected on a dropdown menu by the user
-- Agent 3 - Summarize data from Agent 1 for the US at a national level
-- Agent 4 - Interprete the data from Agent 1 and the summary of Agent 2 to build a "concerned parent" report for a parent in the same state as was selected for Agent 2
- Display new agent results on the "Overview" tab underneath the key metrics graphics
-- Display the agent results as soon as each one is ready, and provide a loading indicator for each one 
- Build a new documentation package that fulfills the requirements of TOOL2.md for submission
- Deploy to Posit Connect using RSConnect Python package and a provided POSIT_PUBLISHER_KEY for API key