# VertiFarm — AI Agent Instructions

## 1. Project Overview

VertiFarm is a mobile-first environmental monitoring and agricultural intelligence application for precision vertical farming. The platform connects greenhouse operators with real-time environmental metrics (temperature, humidity, soil moisture, pH, TDS, light), severity-based alerts, historical trend analytics, and computer vision-assisted plant health diagnostics.

### Current System State
The project currently exists as a **client-side mobile application** built on:
- **Framework:** Expo SDK 57 (`~57.0.20`), React Native `0.86.3`, React `19.2.3`.
- **Navigation:** Expo Router v57 (`expo-router/entry`) with file-based routing.
- **Language:** TypeScript `~6.0.3` with strict domain typing.
- **Visuals:** Custom Botanical SaaS design system and SVG charts (`react-native-svg`).
- **Operational Mode:** Mock-first development. All UI components interact with an asynchronous service layer (`services/`) that returns structured mock data (`data/mock/`).
- **Authentication:** Client-side Google OAuth 2.0 via `expo-auth-session` with local session persistence and an offline email/password development fallback.

Future layers (FastAPI backend, PostgreSQL/Supabase, MQTT broker, and edge hardware) are planned and must remain strictly decoupled from the presentation layer.

---

## 2. Source of Truth

When inspecting, modifying, or reasoning about this repository, agents must adhere to the following strict order of precedence:

1. **Existing Codebase:** Active files under `app/`, `components/`, `constants/`, `services/`, `types/`, and `data/` represent ground truth. Always inspect implementation before assuming behavior.
2. **[ARCHITECTURE.md](file:///d:/farm-app/ARCHITECTURE.md):** The comprehensive technical reference for system architecture, component hierarchies, data contracts, and navigation relationships.
3. **[CLAUDE.md](file:///d:/farm-app/CLAUDE.md):** Agent entry pointer referencing these instructions.
4. **[README.md](file:///d:/farm-app/README.md):** High-level product overview, setup guides, and project mission.
5. **PRD & Design Reference (`VertiFarm_PRD_v1.0.docx`, `design-reference.png`):** Product requirements and visual targets to explain system boundaries and target aesthetics.

> [!IMPORTANT]
> **Expo SDK 57 Documentation:** Expo has undergone significant architectural changes. Always consult the versioned Expo documentation at https://docs.expo.dev/versions/v57.0.0/ before introducing or modifying Expo APIs.

---

## 3. Core Development Rules

- **Do Not Recreate Functionality:** Check existing implementations in `components/`, `services/`, and `constants/` before authoring new primitives or utilities.
- **Prefer Modifying Existing Code:** Extend or adapt existing services and components rather than creating parallel implementations.
- **Enforce Strict Typing:** All domain entities, component props, and service returns must be strictly typed using contracts defined in [types/index.ts](file:///d:/farm-app/types/index.ts). Avoid `any`, loose object types, or unvalidated type assertions.
- **Follow Existing Design Tokens:** Use centralized design tokens from `constants/` (`colors.ts`, `typography.ts`, `spacing.ts`, `radii.ts`, `config.ts`). Never hardcode raw hex colors, margins, or padding values.
- **Reuse Existing Components:** Build UI with established primitives: [Button.tsx](file:///d:/farm-app/components/ui/Button.tsx), [Card.tsx](file:///d:/farm-app/components/ui/Card.tsx), [Badge.tsx](file:///d:/farm-app/components/ui/Badge.tsx), [CustomText.tsx](file:///d:/farm-app/components/ui/CustomText.tsx), [ScreenContainer.tsx](file:///d:/farm-app/components/ui/ScreenContainer.tsx), and SVG chart primitives.
- **Make Minimal, Targeted Changes:** Only touch files directly required by the user's task. Avoid extraneous refactoring.
- **Avoid Unnecessary Dependencies:** Do not add third-party libraries (e.g., Redux, MobX, alternative charting suites) unless explicitly instructed.
- **Preserve Expo Router Architecture:** Maintain file-based routing patterns, layout files (`_layout.tsx`), route grouping conventions, and navigation guards.
- **Maintain Separation of Concerns:** Keep presentation, business logic, data simulation, and type definitions strictly segregated.

---

## 4. UI/UX Rules

- **Visual Source of Truth:** `design-reference.png` defines the target visual standard.
- **Botanical SaaS Aesthetic:** Preserve the established visual language:
  - Deep Forest Green primary (`#1B3B2B`) and Vibrant Leaf Green accent (`#34A853`).
  - Warm cream background (`#F8F9F6`) with pure white card surfaces (`#FFFFFF`).
  - Multidimensional status coloring (background, border, text, and label) ensuring status is never conveyed by color alone.
- **No Unauthorized Redesigns:** Do not change screen layouts, color schemes, or component structures without explicit user instruction.
- **Responsive Mobile Layouts:** Ensure all screens accommodate mobile viewports with proper safe-area insets (`SafeAreaProvider`, `ScreenContainer`), keyboard handling, and scroll wrappers where content exceeds viewport height.
- **Reuse Primitives:** Style screens using semantic aliases (`radii.card`, `spacing.screenPadding`, `typography.fontSize.screenTitle`).

---

## 5. Architecture Rules

The VertiFarm application follows a unidirectional 5-layer architecture:

```
Routes / Screens (app/)
       ↓
Reusable Components (components/)
       ↓
Services Layer (services/)
       ↓
Data / Backend Abstraction (data/mock/ → Future REST/WS)
       ↓
Domain Types (types/)
```

### Layer Responsibilities
1. **Routes & Screens (`app/`):** View controllers that bind route parameters, orchestrate service calls, and assemble UI components. Screens do not directly fetch remote URLs or read raw data files.
2. **Components (`components/`):** Reusable, presentation-focused UI widgets and custom SVG data visualizations.
3. **Services (`services/`):** Encapsulated async APIs for telemetry, alerts, farms, scans, and authentication. All methods return Promises typed by domain models.
4. **Data Layer (`data/mock/`):** Seed datasets that simulate backend responses. When connecting to a live backend, only service internals are swapped.
5. **Domain Types (`types/index.ts`):** Single source of truth for entity interfaces (`Farm`, `Zone`, `SensorDevice`, `TelemetrySummary`, `AlertItem`, `AIScan`, `AuthUser`, etc.).

### Current vs. Planned Systems
- **Current (Implemented):** Client UI, Expo Router navigation, mock data services, custom SVG charting, client-side Google OAuth with local session storage.
- **Planned (Do NOT simulate as active):** FastAPI backend, PostgreSQL/Supabase database, MQTT broker ingestion, physical STM32/ESP32 edge communication, server-side PyTorch/OpenCV AI inference, push notifications.

---

## 6. Authentication & Security

- **Never Commit Secrets:** API keys, client secrets, database URIs, and private credentials must never be committed to Git.
- **Environment Variables:** All client-accessible environment variables must be defined in [.env.example](file:///d:/farm-app/.env.example) and prefixed with `EXPO_PUBLIC_`.
- **Public OAuth Clients Only:** Mobile Google OAuth relies on public client IDs (`EXPO_PUBLIC_GOOGLE_*_CLIENT_ID`) with PKCE or custom URL schemes (`vertifarm://`). Never embed OAuth client secrets in the mobile client.
- **Preserve Service Abstraction:** Maintain the session methods in [services/authService.ts](file:///d:/farm-app/services/authService.ts) (`restoreSession`, `saveSession`, `getCurrentUser`, `isAuthenticated`, `logout`).
- **Respect Route Guards:** Do not bypass or disable authentication routing logic in [app/_layout.tsx](file:///d:/farm-app/app/_layout.tsx) or [app/index.tsx](file:///d:/farm-app/app/index.tsx).
- **No Premature Backend Assumptions:** Do not introduce server session validation, refresh token rotators, or external auth cookies until the backend infrastructure is formally implemented.

---

## 7. Dependency Rules

- **Minimal Dependency Policy:** Only install a dependency when the task cannot be accomplished using the existing platform tools or React Native primitives.
- **Use Expo CLI for Installation:** Always install packages via:
  ```bash
  npx expo install <package-name>
  ```
  This guarantees compatibility with Expo SDK 57.
- **Verify Version Compatibility:** Ensure new libraries support React Native `0.86.3` and React `19.2.3`.
- **No Destructive Upgrades:** Never run `npm audit fix --force`, `npm update`, or major version package upgrades unless explicitly directed by the repository owner.
- **Consult Versioned Documentation:** Check the exact Expo SDK 57 docs at https://docs.expo.dev/versions/v57.0.0/.

---

## 8. File Modification Rules

Before modifying any file:
1. **Inspect Target Files:** Read the exact lines to modify using workspace viewing tools.
2. **Inspect Associated Context:** Check corresponding types in `types/`, services in `services/`, and design tokens in `constants/`.
3. **Identify Reusable Patterns:** Match existing formatting, naming conventions, and component styles.
4. **Confine Edits:** Only edit files directly related to the user request. Never modify unrelated application code, configuration files, or scripts.

---

## 9. Validation Rules

Before declaring any task complete, the agent must run the following validation suite:

1. **TypeScript Compilation:**
   ```bash
   npx tsc --noEmit
   ```
   Must pass with **0 errors**.
2. **Git Diff Hygiene Check:**
   ```bash
   git diff --check
   ```
   Must produce **zero whitespace or newline warnings** in newly authored or modified files.
3. **Expo Runtime Verification:**
   When working on UI or configuration changes, verify that the application compiles cleanly for Expo Web or mobile targets:
   ```bash
   npx expo start --web
   ```
   *(Run as a non-blocking or preview step where relevant).*

---

## 10. Git Rules

> [!CAUTION]
> **Strict Git Policy:** AI agents must **NEVER** execute `git commit`, `git push`, `git reset`, `git rebase`, `git checkout -b`, or `git branch -D` unless the user explicitly instructs you to perform that specific Git command.

- All commits and pushes are executed manually by the repository owner.
- Agents may only run non-mutating Git inspection commands: `git status`, `git diff`, `git log`, and `git diff --check`.

---

## 11. Token Efficiency

- **Be Direct and Precise:** Provide concise, high-density explanations. Avoid conversational filler.
- **Avoid Redundant File Reads:** Inspect only the files necessary to complete the task. Do not re-read unchanged files.
- **No Unrequested Documentation:** Do not create ancillary markdown summaries, scratch documents, or duplicate reports unless explicitly requested.
- **Smallest Correct Change:** Target the minimal set of line edits required to fulfill the specification.
- **Stop Immediately:** Once the requested change is implemented, validated, and reported, terminate execution without proposing unsolicited tasks.

---

## 12. Current Development Stages

The VertiFarm project progresses through 10 structured engineering stages:

| Stage | Domain | Status | Description |
|---|---|---|---|
| **Stage 1** | Foundation | ✅ **COMPLETE** | Project initialization, Expo SDK 57 setup, Expo Router navigation tree, TypeScript domain models, mock data layer, design tokens, and base UI primitives. |
| **Stage 2** | UI/UX | ✅ **COMPLETE** | 17 routable screens, custom SVG charts (`SingleMetricChart`, `MultiMetricChart`), botanical design language, card layouts, and responsive screens. |
| **Stage 3** | OAuth / Authentication | ✅ **COMPLETE** | Production Google OAuth 2.0 (`expo-auth-session`), JWT/userinfo decoding, persistent local auth session, auth route guards, and offline mock fallback. |
| **Stage 4** | Backend & Database | ✅ **COMPLETE** | FastAPI REST server, PostgreSQL / Supabase schema, JWT verification, domain models, and mobile API adapter layer (`services/apiClient.ts`). |
| **Stage 5** | IoT & Realtime Telemetry | ✅ **COMPLETE** | MQTT ingestion pipeline (`mqtt_service.py`), 6-metric validation, deduplication, time-series persistence, WebSockets (`/telemetry/ws`), and mobile real-time adapter. |
| **Stage 6** | Alerts & Notifications | 📋 **PLANNED** | Dynamic threshold evaluation, debounce engine, and push notifications via Expo Push Notification Service (FCM/APNs). |

| **Stage 7** | AI Plant Health & Camera | 📋 **PLANNED** | ESP32-CAM optical capture pipeline, server-side PyTorch/OpenCV plant disease inference model, and diagnostic reporting. |
| **Stage 8** | Analytics & Recommendations | 📋 **PLANNED** | Time-series historical data aggregations, yield correlation metrics, and agronomic rule-based guidance engine. |
| **Stage 9** | Testing & Hardening | 📋 **PLANNED** | End-to-end integration tests, unit test suites, security penetration review, and native secure storage (`expo-secure-store`). |
| **Stage 10**| Deployment & Release | 📋 **PLANNED** | EAS Build pipelines, app store listings (Google Play & Apple App Store), and production telemetry monitoring. |

---

## 13. Explicit Prohibitions

AI agents working on VertiFarm are strictly forbidden from:
1. Recreating or re-scaffolding the project structure.
2. Deleting or breaking existing working screens or components.
3. Altering application architecture without explicit instructions.
4. Inventing unapproved API contracts or backend endpoints.
5. Inventing unapproved database schemas or ORM models.
6. Claiming planned functionality (FastAPI, MQTT, AI inference, Supabase) is currently operational.
7. Committing or pushing Git changes automatically.
8. Installing unvetted or unnecessary third-party packages.
9. Committing or logging secrets, API keys, or private credentials.
10. Modifying files outside the explicit scope of the assigned task.

---

## 14. Completion Protocol

Every completed implementation task must conclude with a standardized completion report containing:
1. **Summary of Changes:** Concise explanation of what was added or modified.
2. **Files Changed:** Clickable markdown list of modified and created files.
3. **Validation Results:** Exact outputs and exit codes of `npx tsc --noEmit` and `git diff --check`.
4. **Remaining Blockers:** Any technical constraints, missing environment variables, or dependencies requiring user action.
5. **STOP:** Terminate response cleanly without soliciting unrelated work.
