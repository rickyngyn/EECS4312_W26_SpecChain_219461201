# Requirement ID: FR_hybrid_1
- Description: The system shall start and play a meditation session without crashing during normal use.
- Source Persona: Reliability Focused Meditation User
- Traceability: Derived from review group H1
- Acceptance Criteria: If the user selects a meditation session and presses play, the session must begin successfully and the app must remain stable throughout playback.
- Notes: Rewritten from the automated requirement to focus on a specific, testable reliability issue supported by the review evidence.

# Requirement ID: FR_hybrid_2
- Description: The system shall maintain uninterrupted audio playback for an active meditation session unless the user pauses, stops, or loses device audio output.
- Source Persona: Reliability Focused Meditation User
- Traceability: Derived from review group H1
- Acceptance Criteria: If the user is listening to a meditation session, the audio must continue playing until the session ends unless the user intentionally interrupts playback.
- Notes: Added to address repeated review evidence about audio stopping unexpectedly.

# Requirement ID: FR_hybrid_3
- Description: The system shall provide a browsable library of guided meditations and courses that users can access from the main interface.
- Source Persona: Content Seeking Meditation Learner
- Traceability: Derived from review group H2
- Acceptance Criteria: If the user opens the content area of the app, the system must display available guided meditations or courses that can be selected for playback.
- Notes: Rewritten to remove vague language like “variety” and replace it with a directly testable content access requirement.

# Requirement ID: FR_hybrid_4
- Description: The system shall label meditation content clearly enough for users to distinguish between sessions, courses, and other available materials.
- Source Persona: Content Seeking Meditation Learner
- Traceability: Derived from review group H2
- Acceptance Criteria: If the user browses available meditation content, each selectable item must display a clear title or label that distinguishes it from other content.
- Notes: Added to support content discoverability without inventing unsupported features.

# Requirement ID: FR_hybrid_5
- Description: The system shall allow a new user to access at least some core meditation content before requiring payment or donation.
- Source Persona: Cost Sensitive First Time Evaluator
- Traceability: Derived from review group H3
- Acceptance Criteria: If a first time user installs and opens the app, they must be able to reach and play at least one meditation session before being required to pay or donate.
- Notes: Rewritten from the automated free access requirement to stay grounded in the evidence about trial access and paywall frustration.

# Requirement ID: FR_hybrid_6
- Description: The system shall present any payment or donation request with wording that makes clear whether it is optional or required.
- Source Persona: Cost Sensitive First Time Evaluator
- Traceability: Derived from review group H3
- Acceptance Criteria: If the app displays a payment or donation prompt, the prompt must clearly indicate whether the user can skip it and continue using available content.
- Notes: Added to address misleading or confusing expectations around “free” access.

# Requirement ID: FR_hybrid_7
- Description: The system shall preserve access to previously available free trial content after the user dismisses an optional payment or donation prompt.
- Source Persona: Cost Sensitive First Time Evaluator
- Traceability: Derived from review group H3
- Acceptance Criteria: If the user dismisses an optional payment or donation prompt, the app must continue to allow access to content that is designated as free or trial content.
- Notes: Makes the paywall experience testable while staying within the evidence provided by the review group.

# Requirement ID: FR_hybrid_8
- Description: The system shall support repeated session use by allowing users to start a meditation session in no more than three navigation steps from the home screen.
- Source Persona: Habit Building Meditation User
- Traceability: Derived from review group H4
- Acceptance Criteria: If the user opens the app from the home screen, they must be able to begin a meditation session within three user actions not including media playback time.
- Notes: Rewritten from the vague habit building requirement into a concrete usability condition that supports routine use.

# Requirement ID: FR_hybrid_9
- Description: The system shall display completed meditation sessions in a session history or equivalent record visible to the user.
- Source Persona: Habit Building Meditation User
- Traceability: Derived from review group H4
- Acceptance Criteria: If the user completes a meditation session, the completed session must appear in a user visible record of prior activity.
- Notes: Supports ongoing routine building without assuming unsupported reminder functionality.

# Requirement ID: FR_hybrid_10
- Description: The system shall provide a navigation structure that allows users to move between home, content browsing, and playback screens without confusion or broken paths.
- Source Persona: Simplicity Focused Meditation App User
- Traceability: Derived from review group H5
- Acceptance Criteria: If the user navigates from the home screen to browse content and then opens a session, each transition must complete successfully and the user must be able to return to the previous screen.
- Notes: Rewritten from the broad clean design requirement into a testable navigation requirement.

# Requirement ID: FR_hybrid_11
- Description: The system shall present primary actions such as play, pause, and back navigation as clearly visible controls on the relevant screen.
- Source Persona: Simplicity Focused Meditation App User
- Traceability: Derived from review group H5
- Acceptance Criteria: If the user is on a playback or content screen, the relevant primary controls must be visible without requiring hidden gestures or undiscoverable actions.
- Notes: Added to address usability and friction concerns grounded in the design focused review group.

# Requirement ID: FR_hybrid_12
- Description: The system shall use concise and readable interface labels for menu items, buttons, and major content categories.
- Source Persona: Simplicity Focused Meditation App User
- Traceability: Derived from review group H5
- Acceptance Criteria: If the user views a major navigation or content screen, visible labels for key actions and sections must be present and readable.
- Notes: Added to improve testability of usability concerns without inventing unsupported features such as cross device syncing or manual offline logging.
