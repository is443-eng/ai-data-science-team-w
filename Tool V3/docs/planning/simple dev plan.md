Base app V3 on "TOOL V2" folder, reference "TOOL3.md" file for rubric and assignment
- Maintain all existing features 
- Add refinements for finishing touches
- Quality control and validation of AI prompts
- 1 Agentic Loop 

Agentic loop
Tim commments: 
"TOOL V3 does purposely have that line in there about an agentic loop. But, a good agentic loop doesn't need to be long! It just has a few components:

Inputs get passed to agent

Agent does N rounds of LLM queries, where the agent's choices affect how many turns it runs. (with guardrails, of course. It could feasibly be an upper limit of 3 turns and a lower limit of 2 turns, for example.) Common uses include:

Quality control + Prompt refinement (I believe App V3 asks you to add some kind of quality control anyways)

2-stage / multi-stage LLM processes, like:

User request --> LLM decides to use Tool --> Tool Call --> LLM parses Tool Response --> LLM summarizes response --> Returns Content to User

Notice here how the LLM is choosing how many rounds it needs to run, not the developer. For example, if the user request doesn't merit a Tool call, the LLM would just skip and return the response to the user.

This requirement could certainly be integrated into a chat user interface - just like how Cursor IDE has a chat-based agent interface, where the agent might take multiple turns to return content to you.

Feel free to follow up if any questions! Think of this requirement more as formalizing into a 'true' autonomous agent loop the processes (eg tool calling) that you have already built. Although you can certainly take it further if you like! It's intended to be a floor, not a ceiling!"
