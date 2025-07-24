# 🧠 Multi-Agent Collaboration Protocol (Supaermaven + Langflow)

## Objective
Establish synchronized agent collaboration with full project context awareness and mutual communication flow for the NoxPanel Suite.

---

## Agent Roles

### Supaermaven (Orchestrator)
- High-level strategist and project coordinator
- Loads and analyzes all project files recursively
- Understands architecture, coding goals, versioning, and priorities
- Coordinates project goals with Langflow’s suggestions
- Documents all actions and suggestions
- Maintains and updates the shared knowledge graph

### Langflow (Collaborator)
- Intelligent flow manager and logic transformer
- Handles flow logic, interdependency mapping, and chained operation design
- Breaks down tasks into executable units
- Offers LLM-based reasoning and highlights bottlenecks
- Suggests optimizations and refactors
- Communicates findings to Supaermaven

---

## Collaboration Workflow
1. **Initialization**
   - Supaermaven activated as orchestrator
   - Langflow linked as collaborator
   - Full scan of project folder (all file types)
   - Load documentation, architecture, audit logs, README/versioning
2. **Analysis**
   - Identify deprecated, outdated, or archived files
   - Flag duplicate/redundant functionality
   - Suggest reintegration of missing legacy features
   - List files for deletion or archiving
   - Update shared knowledge graph (`agents/project_context.json`)
3. **Optimization & Refactor**
   - Suggest real-time optimizations based on performance, redundancy, feature coverage, and architecture
   - Allow agent switching if limitations encountered
   - Log all decisions and rationale
4. **Communication**
   - Agents share findings and updates continuously
   - No changes without mutual agreement or conflict log
   - Maintain public changelog (`agents/multi_agent_changelog.md`)

---

## Communication Rules
- Continuous internal communication between agents
- Shared information pool updated dynamically
- All major changes logged with reasoning and output
- Conflict resolution logged if agents disagree

---

## Persistent Protocol
This protocol is to be used for every reboot or stage handover. Agents must treat this as the persistent collaborative workflow for all future development.

---

## Activation
- Supaermaven: Orchestrator (active)
- Langflow: Collaborator (linked)
- Begin full scan and coordination as described above
